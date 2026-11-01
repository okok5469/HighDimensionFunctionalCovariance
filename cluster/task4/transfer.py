"""PowerShell launcher backend: upload, verify, start/resume, status, download."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import tempfile


DEPLOY = r"""
import hashlib,json,os,pathlib,sys,zipfile
archive,checksum,release=sys.argv[1:]
archive=pathlib.Path(archive); release=pathlib.Path(release)
expected=pathlib.Path(checksum).read_text().split()[0]
if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:
    raise ValueError('uploaded ZIP SHA-256 mismatch')
with zipfile.ZipFile(archive) as bundle:
    names=bundle.namelist()
    if len(names)!=len(set(names)):
        raise ValueError('duplicate archive member')
    for name in names:
        parts=pathlib.PurePosixPath(name).parts
        if name.startswith('/') or '..' in parts or chr(92) in name or ':' in name:
            raise ValueError('unsafe archive member: '+name)
    sums=dict(line.split('  ',1)[::-1] for line in bundle.read('SHA256SUMS').decode().splitlines())
    if set(sums)!=set(names)-{'SHA256SUMS'}:
        raise ValueError('checksum file does not cover full ZIP')
    for name,expected_file in sums.items():
        if hashlib.sha256(bundle.read(name)).hexdigest()!=expected_file:
            raise ValueError('archive member mismatch: '+name)
    if release.exists():
        for name,expected_file in sums.items():
            if hashlib.sha256((release/name).read_bytes()).hexdigest()!=expected_file:
                raise ValueError('existing immutable release differs: '+name)
    else:
        partial=release.with_name(release.name+'.partial')
        partial.mkdir(parents=True,exist_ok=False)
        bundle.extractall(partial)
        partial.rename(release)
print(str(release))
"""


def run(argv):
    return subprocess.run([str(x) for x in argv],check=True,text=True,capture_output=True).stdout.strip()


def configuration_missing(config):
    missing=[]
    for key in ('host','port','user','authentication'):
        if not config.get('ssh',{}).get(key):
            missing.append('ssh.'+key)
    if config.get('ssh',{}).get('authentication')=='identity_file' and not config['ssh'].get('identity_file'):
        missing.append('ssh.identity_file')
    for key in ('bootstrap_memory_mb','bootstrap_time_minutes','control_memory_mb',
                'control_time_minutes','worker_memory_limit_mb','worker_time_limit_minutes'):
        if not config.get(key):
            missing.append(key)
    return missing


def connection(config):
    ssh=config['ssh']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+',ssh['host']) or not re.fullmatch(r'[A-Za-z0-9_.-]+',ssh['user']):
        raise ValueError('host/user must contain only letters, digits, dot, underscore or dash')
    if not isinstance(ssh['port'],int) or not 1<=ssh['port']<=65535:
        raise ValueError('ssh.port must be an explicit integer in 1..65535')
    if ssh['authentication'] not in ('agent','identity_file'):
        raise ValueError('ssh.authentication must be agent or identity_file')
    common=['-o','BatchMode=yes','-o','StrictHostKeyChecking=yes']
    if ssh['authentication']=='identity_file':
        identity=Path(ssh['identity_file']).expanduser().resolve()
        if not identity.is_file():
            raise ValueError('identity_file does not exist; private key is never uploaded')
        common += ['-i',str(identity)]
    target=ssh['user']+'@'+ssh['host']
    return ['ssh','-p',str(ssh['port']),*common,target],['scp','-P',str(ssh['port']),*common],target


def remote_environment(command):
    body='module load anaconda3 && conda activate myenv && '+command
    return 'bash -lc '+shlex.quote(body)


def execute(config_path,action='start',dry_run=False,runner=run,package_override=None):
    config_path=Path(config_path).resolve()
    config=json.loads(config_path.read_text(encoding='utf-8-sig'))
    missing=configuration_missing(config)
    package=Path(package_override or config['package_file'])
    if not package.is_absolute():
        package=config_path.parent/package
    plan={'dry_run':bool(dry_run),'action':action,'missing':missing,
          'package':str(package),'remote_project_dir':config['remote_project_dir'],
          'run_name':config['run_name'],'stages':['upload/checksum/unpack','smoke','production benchmark B=500',
          'pilot 600 array <=8','conditional fallback <=150','afterany collect','immutable confirmation lock','confirm array <=8','afterany collect/report']}
    if dry_run:
        return plan
    if missing:
        raise ValueError('fill centralized cluster config: '+', '.join(missing))
    for key in ('remote_project_dir','run_name'):
        if not re.fullmatch(r'[A-Za-z0-9_./-]+',config[key]):
            raise ValueError('simple POSIX path/name required: '+key)
    if not config['remote_project_dir'].startswith('/') or '/' in config['run_name'] or config['run_name'] in ('.','..'):
        raise ValueError('absolute project directory and single run_name required')
    ssh,scp,target=connection(config)
    package=package.resolve()
    expected=package.with_suffix(package.suffix+'.sha256').read_text(encoding='ascii').split()[0]
    if hashlib.sha256(package.read_bytes()).hexdigest()!=expected:
        raise ValueError('local ZIP SHA-256 mismatch')
    base=config['remote_project_dir'].rstrip('/')
    upload=base+'/.task4_upload/'+expected
    release=base+'/releases/'+expected
    remote_config=upload+'/'+config['run_name']+'.config.json'
    output=base+'/results/task4_fixed_methods_v1/'+config['run_name']
    if action=='download':
        destination=Path(config.get('download_dir','./task4_download'))
        if not destination.is_absolute():
            destination=config_path.parent/destination
        destination.mkdir(parents=True,exist_ok=True)
        runner([*scp,'-r',target+':'+output,str(destination.resolve())])
        return {'downloaded':str(destination.resolve())}
    if action=='start':
        runner([*ssh,'mkdir -p -- '+shlex.quote(upload)])
        remote_package=upload+'/package.zip'
        remote_sum=upload+'/package.zip.sha256'
        runner([*scp,str(package),target+':'+remote_package])
        runner([*scp,str(package.with_suffix(package.suffix+'.sha256')),target+':'+remote_sum])
        sanitized={key:value for key,value in config.items() if key!='ssh'}
        with tempfile.TemporaryDirectory(prefix='task4_config_') as temporary:
            path=Path(temporary)/'runtime.json'
            path.write_text(json.dumps(sanitized,indent=2)+'\n',encoding='utf-8')
            runner([*scp,str(path),target+':'+remote_config])
        encoded=base64.b64encode(DEPLOY.encode()).decode('ascii')
        code='import base64;exec(base64.b64decode('+repr(encoded)+'))'
        deployment='python -c '+shlex.quote(code)+' '+shlex.quote(remote_package)+' '+shlex.quote(remote_sum)+' '+shlex.quote(release)
        runner([*ssh,remote_environment(deployment)])
    cli='python '+shlex.quote(release+'/cluster/task4/controller.py')+' '+action+' --config '+shlex.quote(remote_config)
    if action in ('start','resume'):
        log=upload+'/'+config['run_name']+'.controller.log'
        body='module load anaconda3 && conda activate myenv && exec '+cli
        launch='nohup bash -lc '+shlex.quote(body)+' > '+shlex.quote(log)+' 2>&1 < /dev/null & echo $!'
        pid=runner([*ssh,launch])
        return {'controller_pid':pid,'controller_log':log,'results':output,
                'note':'launch acknowledged; use status and controller log to verify actual stages'}
    return {'status':runner([*ssh,remote_environment(cli)])}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True,type=Path)
    parser.add_argument('--action',choices=('start','resume','status','download'),default='start')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--package',type=Path)
    args=parser.parse_args(argv)
    print(json.dumps(execute(args.config,args.action,args.dry_run,package_override=args.package),indent=2))


if __name__=='__main__':
    main()
