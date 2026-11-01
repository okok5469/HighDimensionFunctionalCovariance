"""Strict content provenance and atomic storage for task3_v1 (Python 3.9+)."""
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import uuid
from contextlib import contextmanager

import numpy as np


def plain(value):
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return plain(value.item())
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def canonical(value):
    return json.dumps(plain(value), ensure_ascii=True, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def array_digest(value):
    data = np.ascontiguousarray(value)
    return hashlib.sha256((str(data.dtype) + repr(data.shape)).encode('ascii') + data.tobytes()).hexdigest()


@contextmanager
def record_lock(path, *, blocking=False):
    """Native advisory lock, automatically released on process exit.

    The inode stays in place: unlinking a locked file permits a second inode
    and defeats exclusion. No PID heuristics or stale-lock deletion is used.
    Shared initialization waits; duplicate record writers fail immediately.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        if os.name == 'nt':
            import msvcrt
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b'0')
                handle.flush()
            handle.seek(0)
            mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
            msvcrt.locking(handle.fileno(), mode, 1)
        else:
            import fcntl
            mode = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
            fcntl.flock(handle.fileno(), mode)
        try:
            yield
        finally:
            if os.name == 'nt':
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(json.dumps(plain(value), ensure_ascii=True, indent=2, allow_nan=False))
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temporary), str(path))
    finally:
        if temporary.exists():
            temporary.unlink()


def write_sealed(path, value):
    path = Path(path)
    content = canonical(value)
    if path.exists():
        if canonical(read_sealed(path)) != content:
            raise ValueError('immutable file differs: ' + str(path))
        return
    atomic_json(path, value)
    path.with_suffix(path.suffix + '.sha256').write_text(
        hashlib.sha256(path.read_bytes()).hexdigest() + '\n', encoding='ascii')


def read_sealed(path):
    path = Path(path)
    checksum = path.with_suffix(path.suffix + '.sha256')
    if not checksum.exists() or checksum.read_text(encoding='ascii').strip() != hashlib.sha256(path.read_bytes()).hexdigest():
        raise ValueError('missing or invalid seal: ' + str(path))
    return json.loads(path.read_text(encoding='utf-8-sig'))


def source_manifest(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    paths = []
    for directory in ('common', 'simulation', 'cluster/task3'):
        for path in (root / directory).rglob('*'):
            if path.is_file() and path.suffix in ('.py', '.json', '.sh', '.slurm'):
                paths.append(path)
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def environment():
    import scipy
    import pandas
    import matplotlib
    import tqdm
    import io
    from contextlib import redirect_stdout
    details = io.StringIO()
    with redirect_stdout(details):
        np.show_config()
    return dict(python=platform.python_version(), executable=sys.executable,
                platform=platform.platform(), numpy=np.__version__, scipy=scipy.__version__,
                pandas=pandas.__version__, matplotlib=matplotlib.__version__, tqdm=tqdm.__version__,
                blas_config=details.getvalue(), threads={key: os.environ.get(key) for key in
                ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS',
                 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS')})
