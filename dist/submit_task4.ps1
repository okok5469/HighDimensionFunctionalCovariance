[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Config,
    [ValidateSet("start", "resume", "status", "download")][string]$Action = "start",
    [switch]$DryRun,
    [string]$Package
)
$ErrorActionPreference = "Stop"
$launcher = Join-Path $PSScriptRoot "../cluster/task4/transfer.py"
$arguments = @("--config", $Config, "--action", $Action)
if ($DryRun) { $arguments += "--dry-run" }
if ($Package) { $arguments += @("--package", $Package) }
if (Test-Path -LiteralPath $launcher -PathType Leaf) {
    & python $launcher @arguments
} else {
    # Standalone delivery: execute only the verified launcher from the ZIP.
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
if hashlib.sha256(package.read_bytes()).hexdigest()!=expected:
    raise ValueError('local ZIP SHA-256 mismatch')
with tempfile.TemporaryDirectory(prefix='task4_launcher_') as tmp:
    launcher=pathlib.Path(tmp)/'transfer.py'
    with zipfile.ZipFile(package) as bundle:
        launcher.write_bytes(bundle.read('cluster/task4/transfer.py'))
    sys.argv[0]=str(launcher)
    runpy.run_path(str(launcher),run_name='__main__')
'@
    & python -c $bootstrap @arguments
}
if ($LASTEXITCODE -ne 0) { throw "Task 4 launcher failed with exit code $LASTEXITCODE" }
