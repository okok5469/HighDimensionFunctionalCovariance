"""Verify complete Task5 ZIP before repairing only absent immutable files."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verified_members(archive, checksum):
    archive = Path(archive)
    if sha(archive.read_bytes()) != Path(checksum).read_text(encoding='ascii').split()[0]:
        raise ValueError('ZIP SHA256 mismatch')
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(set(names)) != len(names):
            raise ValueError('duplicate ZIP member')
        for info in bundle.infolist():
            name = info.filename
            if (not name or name.startswith('/') or '..' in PurePosixPath(name).parts
                    or '\\' in name or ':' in name or info.is_dir()
                    or (info.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError('unsafe ZIP member: ' + name)
        data = {name: bundle.read(name) for name in names}
    sums = {}
    for line in data['SHA256SUMS'].decode('utf-8').splitlines():
        digest, name = line.split('  ', 1)
        if name in sums:
            raise ValueError('duplicate checksum entry')
        sums[name] = digest
    if set(sums) != set(data) - {'SHA256SUMS'}:
        raise ValueError('checksums do not cover all ZIP members')
    for name, digest in sums.items():
        if sha(data[name]) != digest:
            raise ValueError('ZIP member differs: ' + name)
    manifest = json.loads(data['manifest.json'].decode('utf-8'))
    if set(manifest['files']) != set(data) - {'manifest.json', 'SHA256SUMS'}:
        raise ValueError('manifest does not cover complete payload')
    for name, digest in manifest['files'].items():
        if sha(data[name]) != digest:
            raise ValueError('manifest member differs: ' + name)
    return data


def deploy(archive, checksum, release):
    data = verified_members(archive, checksum)
    release = Path(release).absolute()
    # Complete preflight first: conflicts never leave a partially repaired release.
    for name, content in data.items():
        target = release / name
        for path in [target, *target.parents]:
            if path.is_symlink():
                raise ValueError('release path contains symlink: ' + str(path))
        if target.exists() and (not target.is_file() or sha(target.read_bytes()) != sha(content)):
            raise ValueError('existing immutable release differs: ' + name)
    created = []
    for name, content in data.items():
        target = release / name
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write(content)
        created.append(name)
    return {'release': str(release), 'created': created, 'verified_members': len(data)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', required=True, type=Path)
    parser.add_argument('--checksum', required=True, type=Path)
    parser.add_argument('--release', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(deploy(args.package, args.checksum, args.release), ensure_ascii=True))


if __name__ == '__main__': main()
