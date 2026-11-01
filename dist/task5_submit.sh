#!/bin/bash -l
# Upload this file, the ZIP, its .sha256 and centralized config together.
set -eo pipefail
here=$(cd -- "$(dirname -- "$0")" && pwd)
action=${1:-start}
if [ "$#" -gt 0 ]; then shift; fi
config="$here/cluster_config_task5.json"
package=""
dry=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --config) config=$2; shift 2 ;;
        --package) package=$2; shift 2 ;;
        --dry-run) dry=1; shift ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done
case "$action" in start|resume|status|download) ;; *) echo "Expected start, resume, status or download" >&2; exit 2 ;; esac
if [ "$dry" != 1 ]; then
    module load anaconda3
    conda activate myenv
fi
set -u
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1
export MPLBACKEND=Agg PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
python -B - "$action" "$config" "$package" "$dry" <<'PY'
import hashlib,json,pathlib,runpy,subprocess,sys,zipfile
action,config_arg,package_arg,dry=sys.argv[1:]
config_path=pathlib.Path(config_arg).resolve()
config=json.loads(config_path.read_text(encoding='utf-8-sig'))
missing=[k for k in ('bootstrap_memory_mb','bootstrap_time_minutes','control_memory_mb','control_time_minutes','worker_memory_limit_mb','worker_time_limit_minutes') if not config.get(k)]
if dry=='1':
    print(json.dumps(dict(dry_run=True,action=action,missing=missing,stages=['8 production benchmarks B500','pilot arrays','afterany collect/lock','confirm arrays','report/DONE']),indent=2))
    sys.exit(0)
if missing: raise ValueError('fill centralized configuration: '+', '.join(missing))
package=pathlib.Path(package_arg or config['package_file'])
if not package.is_absolute(): package=config_path.parent/package
checksum=package.with_suffix(package.suffix+'.sha256')
if hashlib.sha256(package.read_bytes()).hexdigest()!=checksum.read_text(encoding='ascii').split()[0]:
    raise ValueError('ZIP SHA256 mismatch')
with zipfile.ZipFile(package) as bundle:
    names=bundle.namelist()
    if len(names)!=len(set(names)): raise ValueError('duplicate ZIP member')
    sums={}
    for line in bundle.read('SHA256SUMS').decode('utf-8').splitlines():
        digest,name=line.split('  ',1)
        if name in sums: raise ValueError('duplicate checksum entry')
        sums[name]=digest
    if set(sums)!=set(names)-{'SHA256SUMS'}: raise ValueError('incomplete ZIP checksums')
    for name,digest in sums.items():
        if hashlib.sha256(bundle.read(name)).hexdigest()!=digest: raise ValueError('ZIP member differs: '+name)
    manifest=json.loads(bundle.read('manifest.json'))
    if set(manifest['files'])!=set(names)-{'SHA256SUMS','manifest.json'}: raise ValueError('incomplete manifest')
    for name,digest in manifest['files'].items():
        if hashlib.sha256(bundle.read(name)).hexdigest()!=digest: raise ValueError('manifest differs: '+name)
    source=bundle.read('cluster/task5/deploy.py')
namespace={'__name__':'task5_verified_deployer'}
exec(compile(source,'cluster/task5/deploy.py','exec'),namespace)
release=pathlib.Path(config['remote_project_dir'])/'releases'/config['run_name']
namespace['deploy'](package,checksum,release)
subprocess.run([sys.executable,'-B',str(release/'cluster/task5/controller.py'),action,'--config',str(config_path),'--release',str(release)],check=True)
PY
