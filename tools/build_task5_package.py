"""Build an immutable, checksummed Task5 release from reviewed working-tree bytes."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
import zipfile

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.build_task4_package import git_state


def files_for(root):
    """Explicit source/configuration scopes; results and personal configs excluded."""
    root = Path(root)
    candidates = list((root/'common').rglob('*.py'))
    candidates += list((root/'simulation').glob('*.py'))
    for task in ('task3', 'task4', 'task5'):
        candidates += list((root/'simulation/configs'/task).rglob('*.json'))
        candidates += [p for p in (root/'cluster'/task).rglob('*')
                       if p.suffix in ('.py', '.sh', '.slurm')]
        candidates += list((root/'tests').glob('test_'+task+'*.py'))
    candidates += list((root/'docs').rglob('*.md'))
    roots = [
        'README.md', 'AGENTS.md', 'CLUSTER_GUIDE.md',
        'requirements.txt', 'requirements-optional.txt', 'tests/__init__.py',
        'TASK5_README.md', 'TASK5_UNIFIED_DGP_SPEC.md',
        'TASK5_DESIGN_AND_RESOURCE_PLAN.md', 'TASK5_IMPLEMENTATION_REPORT.md',
        'TASK4_README.md', 'TASK4_DGP_AND_SEARCH_SPEC.md', 'TASK4_IMPLEMENTATION_REPORT.md',
        'TASK3_README.md', 'TASK3_DGP_SPEC.md', 'TASK3_RESOURCE_PLAN.md',
        'TASK3_IMPLEMENTATION_REPORT.md',
        'tools/build_task3_package.py', 'tools/build_task4_package.py',
        'tools/build_task5_package.py', 'tools/task3_serial_recovery.py',
        'dist/task3_serial_recovery.py', 'dist/TASK3_SERIAL_RECOVERY.md',
        'dist/submit_task3.ps1', 'dist/submit_task4.ps1',
        'dist/submit_task5.ps1', 'dist/task5_submit.sh',
        'cluster_config_task3.example.json', 'cluster_config_task4.example.json',
        'cluster_config_task5.example.json', 'dist/cluster_config.example.json',
        'dist/cluster_config.lockfix.example.json',
        'doc/task5_frozen_before.json', 'doc/task5_smoke_final.json',
        'doc/task5_tests_final.log', 'dist/task5_validation_20261024.json',
    ]
    candidates += [root/name for name in roots]
    excluded = {'__pycache__', 'venv', 'cache', 'results'}
    private_names = {'cluster_config.json', 'cluster_config_task5.json', 'credentials.json'}
    return sorted({p for p in candidates if p.is_file() and not any(
        part.startswith('.') or part in excluded for part in p.relative_to(root).parts)
        and p.name.lower() not in private_names})


def build(root, output, git_info=None):
    """Seal all members and the exact workflow source identity, never overwrite."""
    root, output = Path(root).resolve(), Path(output).resolve()
    checksum_path = output.with_suffix(output.suffix+'.sha256')
    if output.exists() or checksum_path.exists():
        raise FileExistsError('package is immutable; choose a new output name')
    data = {p.relative_to(root).as_posix(): p.read_bytes() for p in files_for(root)}
    for relative, content in data.items():
        if relative.endswith('.py'):
            ast.parse(content.decode('utf-8-sig'), filename=relative, feature_version=(3, 9))
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in data.items()}
    from simulation.task5_experiments import source_manifest
    sources = source_manifest()
    mismatched = [name for name, checksum in sources.items() if hashes.get(name) != checksum]
    if mismatched:
        raise ValueError('package source snapshot differs from workflow: '+', '.join(mismatched))
    implementation_hash = hashlib.sha256(json.dumps(sources, sort_keys=True, ensure_ascii=True,
        separators=(',', ':')).encode('utf-8')).hexdigest()
    manifest = dict(manifest_version=1, study='task5_unified_v1', files=hashes,
        source_manifest=sources, implementation_hash=implementation_hash,
        git=git_info if git_info is not None else git_state(root),
        target_environment=dict(python='3.9.25', numpy='2.0.2', scipy='1.13.1',
            conda='myenv', policy='use existing environment; never install requirements.txt'),
        verification='Python 3.9 grammar checked; target runtime verification required on compute node')
    data['manifest.json'] = (json.dumps(manifest, ensure_ascii=True, indent=2)+'\n').encode('utf-8')
    data['SHA256SUMS'] = ''.join(hashlib.sha256(content).hexdigest()+'  '+name+'\n'
        for name, content in sorted(data.items())).encode('utf-8')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for relative, content in sorted(data.items()):
            entry = zipfile.ZipInfo(relative, date_time=(2026, 10, 24, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = (0o755 if relative.endswith(('.sh', '.slurm')) else 0o644)<<16
            archive.writestr(entry, content)
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    with checksum_path.open('x', encoding='ascii') as handle:
        handle.write(checksum+'  '+output.name+'\n')
    return dict(zip=str(output), sha256=checksum, files=len(data), implementation_hash=implementation_hash)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path,
        default=Path('dist/covariance_task5_unified_v1_20261024.zip'))
    args = parser.parse_args(argv)
    print(json.dumps(build(args.root, args.output), indent=2))


if __name__ == '__main__':
    main()
