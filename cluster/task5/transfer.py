"""Optional SSH/SCP launcher; Bash on the cluster is the default entry."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import tempfile


def run(argv):
    result = subprocess.run(list(map(str, argv)), check=True, text=True, capture_output=True)
    return result.stdout.strip()


def configuration_missing(config):
    keys = ['ssh.' + key for key in ('host', 'port', 'user', 'authentication') if not config.get('ssh', {}).get(key)]
    if config.get('ssh', {}).get('authentication') == 'identity_file' and not config['ssh'].get('identity_file'):
        keys.append('ssh.identity_file')
    keys += [key for key in ('bootstrap_memory_mb', 'bootstrap_time_minutes', 'control_memory_mb',
             'control_time_minutes', 'worker_memory_limit_mb', 'worker_time_limit_minutes') if not config.get(key)]
    return keys


def connection(config):
    ssh = config['ssh']
    for key in ('host', 'user'):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', ssh[key]):
            raise ValueError('invalid SSH ' + key)
    if type(ssh['port']) is not int or not 1 <= ssh['port'] <= 65535:
        raise ValueError('SSH port must be an explicit integer')
    if ssh['authentication'] not in ('agent', 'identity_file'):
        raise ValueError('SSH authentication must be agent or identity_file')
    common = ['-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes']
    if ssh['authentication'] == 'identity_file':
        identity = Path(ssh['identity_file']).expanduser().resolve()
        if not identity.is_file():
            raise ValueError('identity_file does not exist')
        common += ['-i', str(identity)]
    target = ssh['user'] + '@' + ssh['host']
    return ['ssh', '-p', str(ssh['port']), *common, target], ['scp', '-P', str(ssh['port']), *common], target


def environment(body):
    return 'bash -lc ' + shlex.quote('module load anaconda3 && conda activate myenv && ' + body)


def execute(config_path, action='start', dry_run=False, runner=run, package_override=None):
    config_path = Path(config_path).resolve()
    config = json.loads(config_path.read_text(encoding='utf-8-sig'))
    missing = configuration_missing(config)
    plan = dict(dry_run=bool(dry_run), action=action, missing=missing,
                stages=['verify/upload missing bytes', '8 production benchmarks B500', 'pilot arrays',
                        'afterany collect/immutable lock', 'mandatory confirm arrays', 'report/DONE'],
                run_name=config['run_name'], remote_project_dir=config['remote_project_dir'])
    if dry_run:
        return plan
    if missing:
        raise ValueError('fill centralized configuration: ' + ', '.join(missing))
    for key in ('remote_project_dir', 'run_name'):
        if not re.fullmatch(r'[A-Za-z0-9_./-]+', config[key]) or '..' in Path(config[key]).parts:
            raise ValueError('simple POSIX path/name required: ' + key)
    if not config['remote_project_dir'].startswith('/') or '/' in config['run_name']:
        raise ValueError('absolute project path and single run_name required')
    ssh, scp, target = connection(config)
    base = config['remote_project_dir'].rstrip('/')
    release = base + '/releases/' + config['run_name']
    output = base + '/results/task5_unified_v1/' + config['run_name']
    upload = base + '/.task5_upload/' + config['run_name']
    remote_config = upload + '/runtime.json'
    if action == 'download':
        destination = Path(config.get('download_dir', './task5_download'))
        if not destination.is_absolute():
            destination = config_path.parent / destination
        destination.mkdir(parents=True, exist_ok=True)
        runner([*scp, '-r', target + ':' + output, str(destination.resolve())])
        return {'downloaded': str(destination.resolve()), 'results': output}
    if action == 'start':
        package = Path(package_override or config['package_file'])
        if not package.is_absolute():
            package = config_path.parent / package
        checksum = package.with_suffix(package.suffix + '.sha256')
        from importlib.util import spec_from_file_location, module_from_spec
        spec = spec_from_file_location('task5_deploy', Path(__file__).with_name('deploy.py'))
        deploy = module_from_spec(spec); spec.loader.exec_module(deploy)
        deploy.verified_members(package, checksum)
        runner([*ssh, 'mkdir -p -- ' + shlex.quote(upload)])
        def upload_absent(local, remote):
            digest = hashlib.sha256(Path(local).read_bytes()).hexdigest()
            code = ('import pathlib,hashlib; p=pathlib.Path(' + repr(remote) + '); '
                    'print("missing" if not p.exists() else '
                    '("same" if hashlib.sha256(p.read_bytes()).hexdigest()==' + repr(digest) + ' else "differs"))')
            result = runner([*ssh, environment('python -c ' + shlex.quote(code))])
            result = result.splitlines()[-1]
            if result == 'differs':
                raise ValueError('existing remote immutable upload differs: ' + remote)
            if result == 'missing':
                runner([*scp, str(local), target + ':' + remote])
            elif result != 'same':
                raise ValueError('unrecognized remote byte verification: ' + result)
        remote_package, remote_sum = upload + '/package.zip', upload + '/package.zip.sha256'
        upload_absent(package, remote_package)
        upload_absent(checksum, remote_sum)
        sanitized = {key: value for key, value in config.items() if key != 'ssh'}
        with tempfile.TemporaryDirectory(prefix='task5_config_') as temporary:
            path = Path(temporary) / 'runtime.json'
            path.write_text(json.dumps(sanitized, indent=2) + '\n', encoding='utf-8')
            upload_absent(path, remote_config)
        encoded = base64.b64encode(Path(__file__).with_name('deploy.py').read_bytes()).decode('ascii')
        code = 'import base64;exec(base64.b64decode(' + repr(encoded) + '))'
        deploy_command = 'python -c ' + shlex.quote(code) + ' --package ' + shlex.quote(remote_package)
        deploy_command += ' --checksum ' + shlex.quote(remote_sum) + ' --release ' + shlex.quote(release)
        runner([*ssh, environment(deploy_command)])
    cli = 'python -B ' + shlex.quote(release + '/cluster/task5/controller.py') + ' ' + action
    cli += ' --config ' + shlex.quote(remote_config) + ' --release ' + shlex.quote(release)
    acknowledgement = runner([*ssh, environment(cli)])
    return dict(acknowledgement=acknowledgement, results=output, logs=output + '/logs',
                completion_marker=output + '/DONE.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--action', choices=('start', 'resume', 'status', 'download'), default='start')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--package', type=Path)
    args = parser.parse_args()
    print(json.dumps(execute(args.config, args.action, args.dry_run, package_override=args.package), indent=2))


if __name__ == '__main__': main()
