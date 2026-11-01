[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Config,
    [ValidateSet("start", "resume", "status", "download")][string]$Action = "start",
    [switch]$DryRun,
    [string]$Package
)
$ErrorActionPreference = "Stop"
$launcher = Join-Path $PSScriptRoot "../cluster/task5/transfer.py"
$arguments = @("--config", $Config, "--action", $Action)
if ($DryRun) { $arguments += "--dry-run" }
if ($Package) { $arguments += @("--package", $Package) }
if (Test-Path -LiteralPath $launcher -PathType Leaf) {
    & python $launcher @arguments
} else {
    $bootstrap = @'
import argparse,hashlib,json,pathlib,runpy,sys,tempfile,zipfile
parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('--config',required=True,type=pathlib.Path)
parser.add_argument('--package',type=pathlib.Path)
args,_=parser.parse_known_args()
config=json.loads(args.config.read_text(encoding='utf-8-sig'))
package=args.package or pathlib.Path(config['package_file'])
if not package.is_absolute(): package=args.config.resolve().parent/package
expected=package.with_suffix(package.suffix+'.sha256').read_text(encoding='ascii').split()[0]
if hashlib.sha256(package.read_bytes()).hexdigest()!=expected: raise ValueError('ZIP SHA256 mismatch')
with zipfile.ZipFile(package) as bundle:
    names=bundle.namelist()
    if len(names)!=len(set(names)): raise ValueError('duplicate archive member')
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
    deploy_source=bundle.read('cluster/task5/deploy.py')
namespace={'__name__':'task5_verified_deployer'}
exec(compile(deploy_source,'cluster/task5/deploy.py','exec'),namespace)
with tempfile.TemporaryDirectory(prefix='task5_launcher_') as tmp:
    namespace['deploy'](package,package.with_suffix(package.suffix+'.sha256'),pathlib.Path(tmp)/'release')
    launcher=pathlib.Path(tmp)/'release/cluster/task5/transfer.py'
    sys.argv[0]=str(launcher)
    runpy.run_path(str(launcher),run_name='__main__')
'@
    & python -c $bootstrap @arguments
}
if ($LASTEXITCODE -ne 0) { throw "Task 5 launcher failed with exit code $LASTEXITCODE" }
