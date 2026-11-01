"""Checkpointed single-job Task4 launcher; frozen release is read-only."""
import argparse
from contextlib import contextmanager
import getpass
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def atomic(path, value):
    path = Path(path)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def command(argv):
    result = subprocess.run(list(map(str, argv)), text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError('command failed: %s\n%s\n%s' % (' '.join(map(str, argv)), result.stdout, result.stderr))
    return result.stdout.strip()


def budget(config):
    values = [config[k] for k in ('worker_time_limit_minutes', 'worker_memory_limit_mb')]
    if any(type(v) is not int or v <= 0 for v in values):
        raise ValueError('existing worker time/memory budget must be positive integers')
    return tuple(values)


def check_jobs(state, queue, own_job):
    if state.get('submission_intent'):
        raise RuntimeError('unacknowledged sbatch submission; reconcile its job before proceeding')
    jobs = {str(v) for k, v in state.items() if k in ('job_id', 'worker_job_id') and v}
    jobs.update(str(item['job_id']) for item in state.get('history', []) if item.get('job_id'))
    for line in queue.splitlines():
        fields = line.split('|')
        if len(fields) != 2 or not fields[0].strip().isdigit() or not fields[1].strip():
            raise RuntimeError('unrecognized squeue row: ' + line)
        job = fields[0].strip()
        if job in jobs and job != own_job:
            raise RuntimeError('active prior task4 job ' + job + '; wait for it to finish; do not submit concurrently')


def can_start(required, remaining, capacity):
    if required > capacity:
        raise RuntimeError('measured chunk exceeds existing job budget: requires %.0fs, usable %.0fs; increase an approved worker budget or use original smaller chunks' % (required, capacity))
    return remaining >= required


def pending_chunks(workflow, output, phase, plan, size):
    tasks = workflow.tasks_for(plan)
    pending = set()
    for index, (entry, replicate) in enumerate(tasks):
        path = workflow.record_path(output, phase, entry, replicate)
        if not path.exists():
            pending.add(index // size)
            continue
        record = workflow.validate_record(read(path), plan, entry, replicate)
        if not record['complete']:
            raise RuntimeError('failed method checkpoint retained; inspect ' + str(path))
    return sorted(pending)


@contextmanager
def lock(path, wait_seconds=0):
    import fcntl
    with Path(path).open('a') as handle:
        deadline = time.monotonic() + wait_seconds
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise RuntimeError('old controller or another batch holds controller.lock; inspect it before switching')
                time.sleep(.1)
        yield


def setup(directory):
    config = read(directory / 'cluster_config.json')
    base = Path(config['remote_project_dir'])
    release = base / 'releases' / config['run_name']
    output = base / 'results/task4_fixed_methods_v1' / config['run_name']
    manifest = read(release / 'manifest.json')
    for relative, expected in manifest['files'].items():
        target = (release / relative).resolve()
        target.relative_to(release.resolve())
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise RuntimeError('frozen release differs: ' + relative)
    spec = importlib.util.spec_from_file_location('frozen_task4_controller', release / 'cluster/task4/controller.py')
    controller = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(controller)
    controller.validate_config(config)
    return config, release, output, controller


def guard(output, controller, config, own_job):
    queue = command(['squeue', '--noheader', '--array', '--user=' + getpass.getuser(), '--format=%F|%T'])
    for name in ('controller_state.json', 'batch_state.json'):
        path = output / name
        if path.exists():
            state = read(path)
            if name == 'controller_state.json':
                controller.validate_resume(state, config)
                release = Path(config['remote_project_dir']) / 'releases' / config['run_name']
                controller.source_check(release, state)
            check_jobs(state, queue, own_job)


def status(directory):
    config = read(directory / 'cluster_config.json')
    output = Path(config['remote_project_dir']) / 'results/task4_fixed_methods_v1' / config['run_name']
    print('RESULTS ' + str(output), flush=True)
    original_log = directory / 'controller.log'
    if original_log.exists():
        print('ORIGINAL CONTROLLER LOG ' + str(original_log))
        print('\n'.join(original_log.read_text(errors='replace').splitlines()[-35:]))
    for name in ('controller_state.json', 'batch_state.json'):
        path = output / name
        if path.exists():
            state = read(path)
            print('%s: stage=%s job=%s' % (name, state.get('stage'), state.get('job_id')))
    for phase in ('smoke', 'pilot', 'fallback', 'confirm'):
        count = len(list((output / phase / 'replicates').glob('*.json')))
        print('%s: %s saved records' % (phase, count))
    logs = sorted((output / 'logs').glob('batch-*.log'), key=lambda p: p.stat().st_mtime, reverse=True)
    if logs:
        print('LATEST LOG ' + str(logs[0]))
        print('\n'.join(logs[0].read_text(errors='replace').splitlines()[-35:]))
    for path in sorted((output / 'logs').glob('*.err'), key=lambda p: p.stat().st_mtime, reverse=True)[:2]:
        print('ERROR LOG ' + str(path))
        print('\n'.join(path.read_text(errors='replace').splitlines()[-15:]))


def submit(directory):
    config, release, output, controller = setup(directory)
    minutes, memory = budget(config)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'logs').mkdir(exist_ok=True)
    path = output / 'batch_state.json'
    with lock(output / 'controller.lock'):
        guard(output, controller, config, '')
        state = read(path) if path.exists() else {}
        if state.get('stage') == 'DONE':
            print('Already DONE: ' + str(output)); return
        argv = ['sbatch', '--parsable', '--account=' + config['account'], '--partition=' + config['partition'],
                '--nodes=1', '--ntasks=1', '--cpus-per-task=1', '--no-requeue', '--job-name=t4-batch',
                '--mem=%sM' % memory, '--time=%s' % minutes, '--chdir=' + str(release),
                '--output=' + str(output / 'logs/batch-%j.log'), '--error=' + str(output / 'logs/batch-%j.err'),
                str(directory / 'task4_submit.sh'), '--run', str(directory)]
        state.update(stage='SUBMITTING', submission_intent=argv)
        atomic(path, state)
        job = command(argv).split(';')[0]
        if not job.isdigit():
            raise RuntimeError('unrecognized sbatch acknowledgement: ' + job)
        state.pop('submission_intent')
        state.update(stage='QUEUED', job_id=job)
        atomic(path, state)
    print('Submitted job ' + job)
    print('LOG ' + str(output / ('logs/batch-' + job + '.log')))
    print('RESULTS ' + str(output))


def execute(directory):
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('computation requires a Slurm allocation')
    config, release, output, controller = setup(directory)
    minutes, memory = budget(config)
    own_job = os.environ['SLURM_JOB_ID']
    # An immediately scheduled job can start before its submitting process has
    # released the same lock. Wait briefly for that acknowledgement transaction;
    # the full old-job/source guard still runs after acquiring it.
    with lock(output / 'controller.lock', wait_seconds=10):
        guard(output, controller, config, own_job)
        sys.path.insert(0, str(release))
        from simulation import task4_experiments as w
        import numpy
        import scipy
        if sys.version_info[:3] != (3, 9, 25) or numpy.__version__ != '2.0.2' or scipy.__version__ != '1.13.1':
            raise RuntimeError('requires original myenv: Python3.9.25 NumPy2.0.2 SciPy1.13.1')
        start = time.monotonic()
        reserve = max(60, minutes * 6)
        capacity = minutes * 60 - reserve
        state_path = output / 'batch_state.json'
        def progress(stage):
            atomic(state_path, dict(stage=stage, job_id=own_job, elapsed_seconds=time.monotonic()-start))
            print(time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + stage, flush=True)
        def room(seconds):
            if not can_start(seconds, capacity - (time.monotonic()-start), capacity):
                progress('PAUSED'); return False
            return True
        try:
            progress('SMOKE')
            w.run_smoke(output)
            progress('INIT')
            if (output / 'pilot_plan.json').exists(): w.load_plan(output, 'pilot')
            else: w.initialize(output)
            progress('BENCHMARK B500: first production record may take time')
            measured = w.benchmark(output)
            worst = max(item['seconds'] for item in measured['measurements'])
            required_memory = math.ceil(2 * max(item['peak_memory_mb'] for item in measured['measurements']))
            if required_memory > memory:
                raise RuntimeError('measured memory %sMB exceeds configured worker budget %sMB' % (required_memory, memory))
            phase = 'pilot'
            while True:
                plan = w.load_plan(output, phase)
                mapping_path = output / (phase + '_workers.json')
                mapping = w.io.read_sealed(mapping_path) if mapping_path.exists() else w.plan_workers(output, phase, max(1, math.ceil(2*worst)))
                size = mapping['chunk_size']
                pending = pending_chunks(w, output, phase, plan, size)
                for chunk in pending:
                    count = min(size, len(w.tasks_for(plan)) - chunk*size)
                    if not room(2*worst*count): return
                    progress('%s CHUNK %s START (%s records)' % (phase, chunk, count))
                    w.run_worker(output, phase, chunk)
                    progress('%s CHUNK %s SAVED' % (phase, chunk))
                if not room(60): return
                progress(phase + ' COLLECT')
                integrity = w.collect(output, phase)
                if not integrity['complete']:
                    raise RuntimeError('incomplete ' + phase + '; inspect integrity/failures')
                if phase == 'confirm':
                    w.write_report(output); progress('DONE'); return
                decision = w.decide(output)
                if decision['action'] == 'done_no_eligible_candidates':
                    progress('DONE'); return
                phase = {'fallback': 'fallback', 'confirm': 'confirm'}[decision['action']]
        except Exception:
            progress('FAILED')
            raise


def main():
    # Keep shell interface as switches without argparse option ambiguity.
    argv = sys.argv[1:]
    if argv and argv[0] in ('--submit','--run','--status','--diagnose'):
        argv[0] = argv[0][2:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('submit','run','status','diagnose'))
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args(argv)
    {'submit': submit, 'run': execute, 'status': status, 'diagnose': status}[args.action](args.directory.resolve())


if __name__ == '__main__':
    main()
