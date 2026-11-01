"""Build a reviewed source package from current bytes, including dirty changes."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def files_for(root):
    allowed=[]
    extensions={'common':{'.py'},'simulation':{'.py','.json'},
                'cluster/task4':{'.py','.json','.sh','.slurm'},
                'cluster/task3':{'.py','.json','.sh','.slurm'},'docs':{'.md'}}
    for folder,suffixes in extensions.items():
        for path in (root/folder).rglob('*'):
            parts=path.relative_to(root).parts
            if (path.is_file() and path.suffix in suffixes and not
                any(part.startswith('.') or part in ('__pycache__','venv','cache','results') for part in parts)
                and path.name not in ('cluster_config.json',)):
                allowed.append(path)
    allowed.extend(path for path in (root/'tests').glob('test_task4*.py') if path.is_file())
    allowed.extend(path for path in (root/'tests').glob('test_task3*.py') if path.is_file())
    roots=['README.md','AGENTS.md','CLUSTER_GUIDE.md','TASK4_README.md',
           'TASK4_DGP_AND_SEARCH_SPEC.md','TASK4_IMPLEMENTATION_REPORT.md',
           'requirements.txt','requirements-optional.txt','tests/__init__.py',
           'tools/build_task4_package.py','dist/submit_task4.ps1',
           'cluster_config_task4.example.json','doc/task4_frozen_before.json',
           'doc/task4_smoke_final.json','doc/task4_tests_final.log',
           'TASK3_README.md','TASK3_DGP_SPEC.md','TASK3_RESOURCE_PLAN.md',
           'TASK3_IMPLEMENTATION_REPORT.md','tools/build_task3_package.py',
           'dist/submit_task3.ps1','dist/cluster_config.example.json',
           'tools/task3_serial_recovery.py','dist/task3_serial_recovery.py',
           'dist/TASK3_SERIAL_RECOVERY.md','dist/cluster_config.lockfix.example.json']
    allowed.extend(root/relative for relative in roots if (root/relative).is_file())
    return sorted(set(allowed))


def git_state(root):
    def git(*args):
        return subprocess.run(['git','-C',str(root),*args],check=True,text=True,
                              capture_output=True,encoding='utf-8').stdout.strip()
    return {'head':git('rev-parse','HEAD'),'status_porcelain':git('status','--porcelain=v1','--untracked-files=normal')}


def build(root, output, git_info=None):
    root,output=Path(root).resolve(),Path(output).resolve()
    if output.exists() or output.with_suffix(output.suffix+'.sha256').exists():
        raise FileExistsError('package is immutable; choose a new output name')
    files=files_for(root)
    data={path.relative_to(root).as_posix():path.read_bytes() for path in files}
    for relative,content in data.items():
        if relative.endswith('.py'):
            ast.parse(content.decode('utf-8-sig'),filename=relative,feature_version=(3,9))
    hashes={relative:hashlib.sha256(content).hexdigest() for relative,content in data.items()}
    # Exact same identity boundary as task4_experiments.source_manifest().
    sources={relative:checksum for relative,checksum in hashes.items()
             if (relative.startswith('common/') and Path(relative).suffix=='.py')
             or (relative.startswith('simulation/') and len(Path(relative).parts)==2 and Path(relative).suffix=='.py')
             or (relative.startswith('simulation/configs/task4/') and Path(relative).suffix=='.json')
             or (relative.startswith('cluster/task4/') and Path(relative).suffix in ('.py','.slurm'))}
    implementation_hash=hashlib.sha256(json.dumps(sources,sort_keys=True,ensure_ascii=True,
                                      separators=(',',':')).encode('utf-8')).hexdigest()
    manifest={'study':'task4_fixed_methods_v1','files':hashes,'source_manifest':sources,
              'implementation_hash':implementation_hash,'git':git_info if git_info is not None else git_state(root),
              'target_environment':{'python':'3.9.25','numpy':'2.0.2','scipy':'1.13.1',
                                    'conda':'myenv','policy':'use existing environment; never install requirements.txt'},
              'verification':'Python 3.9 grammar checked; target runtime verification required on compute node'}
    data['manifest.json']=(json.dumps(manifest,ensure_ascii=True,indent=2)+'\n').encode('utf-8')
    data['SHA256SUMS']=''.join(hashlib.sha256(content).hexdigest()+'  '+relative+'\n'
                             for relative,content in sorted(data.items())).encode('utf-8')
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for relative,content in sorted(data.items()):
            entry=zipfile.ZipInfo(relative,date_time=(2026,10,23,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED
            entry.external_attr=(0o755 if relative.endswith(('.sh','.slurm')) else 0o644)<<16
            archive.writestr(entry,content)
    checksum=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix+'.sha256').write_text(checksum+'  '+output.name+'\n',encoding='ascii')
    return {'zip':str(output),'sha256':checksum,'files':len(data),'implementation_hash':implementation_hash}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output',type=Path,default=Path('dist/covariance_task4_fixed_methods_v1_20261023.zip'))
    args=parser.parse_args(argv)
    print(json.dumps(build(args.root,args.output),indent=2))


if __name__=='__main__':
    main()
