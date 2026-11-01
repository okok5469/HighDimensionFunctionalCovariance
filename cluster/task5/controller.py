"""Finite, checkpointed Slurm dependency graph; no resident controller."""
import argparse
from collections import Counter
from contextlib import contextmanager
import getpass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

SHAPES = {(200, 20), (400, 20), (800, 20), (800, 50)}
ACTIVE = {'PENDING', 'RUNNING', 'CONFIGURING', 'COMPLETING', 'SUSPENDED', 'RESIZING',
          'REQUEUED', 'REQUEUE_FED', 'REQUEUE_HOLD', 'SIGNALING', 'STAGE_OUT'}
TERMINAL = {'COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY', 'NODE_FAIL',
            'PREEMPTED', 'BOOT_FAIL', 'DEADLINE', 'REVOKED'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def atomic(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def command(argv):
    result = subprocess.run(list(map(str, argv)), text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError('command failed: %s\n%s\n%s' % (' '.join(map(str, argv)), result.stdout, result.stderr))
    return result.stdout.strip()


def digest(config):
    values = {k: v for k, v in config.items() if k not in ('ssh', 'package_file', 'download_dir')}
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def validate_config(config):
    required = ('bootstrap_memory_mb', 'bootstrap_time_minutes', 'control_memory_mb',
                'control_time_minutes', 'worker_memory_limit_mb', 'worker_time_limit_minutes')
    missing = [key for key in required if config.get(key) is None]
    if missing:
        raise ValueError('fill centralized configuration: ' + ', '.join(missing))
    for key in (*required, 'seconds_per_chunk', 'array_concurrency'):
        if type(config.get(key)) is not int or config[key] <= 0:
            raise ValueError('positive integer required: ' + key)
    if config['array_concurrency'] > 8:
        raise ValueError('array_concurrency must be at most 8')
    if config.get('module') != 'anaconda3' or config.get('conda_env') != 'myenv':
        raise ValueError('existing environment anaconda3/myenv required')
    for key in ('account', 'partition', 'run_name'):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', config.get(key, '')) or config[key] in ('.', '..'):
            raise ValueError('simple nonempty name required: ' + key)
    if not re.fullmatch(r'/[A-Za-z0-9_./-]+', config.get('remote_project_dir', '')):
        raise ValueError('absolute POSIX remote_project_dir required')
    return config


def measurement_table(benchmark, implementation_hash, environment_hash=None):
    rows = benchmark.get('measurements', [])
    counts = Counter((row['n'], row['p']) for row in rows)
    if benchmark.get('small') is not False or benchmark.get('implementation_hash') != implementation_hash:
        raise ValueError('production benchmark source/scale mismatch')
    if set(counts) != SHAPES or any(value != 2 for value in counts.values()):
        raise ValueError('exactly 8 benchmarks, two for each planned shape, required before statistical jobs')
    if environment_hash is not None and (benchmark.get('environment_hash') != environment_hash
            or any(row.get('environment_hash') != environment_hash for row in rows)):
        raise ValueError('production benchmark runtime environment differs')
    table = {}
    for row in rows:
        if row.get('B') != 500 or row.get('M', 64) != 64:
            raise ValueError('benchmark requires M64/B500')
        if not all(math.isfinite(row[key]) and row[key] > 0 for key in ('seconds', 'peak_memory_mb')):
            raise ValueError('positive finite measured resources required')
        shape = (row['n'], row['p'])
        current = table.setdefault(shape, {'seconds': 0, 'peak_memory_mb': 0})
        for key in current:
            current[key] = max(current[key], row[key])
    return table


def resource_estimate(plan, measurements, config):
    shapes = {(item['scenario']['n'], item['scenario']['p']) for item in plan['scenarios']}
    for shape in shapes:
        row = measurements[shape]
        memory = math.ceil(2 * row['peak_memory_mb'])
        seconds = math.ceil(2 * row['seconds']) + 60
        if memory > config['worker_memory_limit_mb']:
            raise ValueError('measured %s memory requirement %s MB exceeds budget %s MB (gap %s MB)' %
                             (shape, memory, config['worker_memory_limit_mb'], memory - config['worker_memory_limit_mb']))
        limit = config['worker_time_limit_minutes'] * 60
        if seconds > limit:
            raise ValueError('measured %s time requirement %s s exceeds budget %s s (gap %s s)' %
                             (shape, seconds, limit, seconds - limit))
    hours = sum(item['repeats'] * measurements[(item['scenario']['n'], item['scenario']['p'])]['seconds']
                for item in plan['scenarios']) / 3600
    return dict(worker_hours=hours, ideal_wall_hours=hours / config['array_concurrency'],
                concurrent_workers=config['array_concurrency'],
                shapes=[dict(n=n, p=p, **measurements[(n, p)]) for n, p in sorted(shapes)],
                assumptions='Per-shape maximum of two B500 measurements; 2x scheduling safety factor. '
                'Worker hours exclude queue delay; family runtime differences remain uncertain.')


def job_state(job_id, runner=None):
    runner = command if runner is None else runner
    queue = runner(['squeue', '--noheader', '--array', '--user=' + getpass.getuser(), '--format=%F|%T'])
    statuses = [line.split('|')[1].strip().split()[0] for line in queue.splitlines()
                if len(line.split('|')) >= 2 and line.split('|')[0].strip() == str(job_id)]
    if any(status not in ACTIVE | TERMINAL for status in statuses):
        raise ValueError('unknown scheduler state')
    if any(status in ACTIVE for status in statuses):
        return 'RUNNING'
    accounting = runner(['sacct', '--noheader', '--parsable2', '--allocations', '--jobs=' + str(job_id),
                         '--format=JobID%64,State%40,ExitCode'])
    rows = []
    for line in accounting.splitlines():
        fields = [field.strip() for field in line.split('|')]
        if len(fields) < 3 or not re.fullmatch(re.escape(str(job_id)) + r'(?:_\d+)?', fields[0]):
            continue
        status = fields[1].split()[0].rstrip('+')
        if status not in ACTIVE | TERMINAL:
            raise ValueError('unknown scheduler state: ' + status)
        rows.append((status, fields[2]))
    if not rows:
        raise ValueError('job absent from squeue and sacct: ' + str(job_id))
    if any(status in ACTIVE for status, _ in rows):
        return 'RUNNING'
    return 'COMPLETED' if all(status == 'COMPLETED' and code == '0:0' for status, code in rows) else 'FAILED'


def sbatch_args(config, release, output, stage, mapping=None, dependency=None):
    memory, minutes = config['control_memory_mb'], config['control_time_minutes']
    if stage == 'bootstrap':
        memory, minutes = config['bootstrap_memory_mb'], config['bootstrap_time_minutes']
    if stage == 'worker':
        memory, minutes = mapping['memory_mb'], mapping['minutes']
        if memory > config['worker_memory_limit_mb'] or minutes > config['worker_time_limit_minutes']:
            raise ValueError('worker resource request exceeds configured budget')
    argv = ['sbatch', '--parsable', '--account=' + config['account'], '--partition=' + config['partition'],
            '--nodes=1', '--ntasks=1', '--cpus-per-task=1', '--no-requeue', '--mem=%sM' % memory,
            '--time=%s' % minutes, '--job-name=t5-' + stage, '--chdir=' + str(release),
            '--output=' + str(output / ('logs/' + stage + '-%A_%a.out')),
            '--error=' + str(output / ('logs/' + stage + '-%A_%a.err'))]
    if dependency:
        argv.append('--dependency=afterany:' + dependency)
    if stage == 'worker':
        argv.append('--array=0-%s%%%s' % (len(mapping['workers']) - 1, config['array_concurrency']))
    return argv + [str(release / 'cluster/task5/run.slurm'), str(release), str(output), stage]


@contextmanager
def lock(path):
    import fcntl
    with Path(path).open('a') as handle:
        deadline = time.monotonic() + 20
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise RuntimeError('another Task5 controller holds the lock')
                time.sleep(.1)
        yield


def source_check(release, state):
    manifest = read(release / 'manifest.json')
    for relative, expected in manifest['files'].items():
        path = (release / relative).resolve()
        path.relative_to(release.resolve())
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('release file differs: ' + relative)
    identity = hashlib.sha256((release / 'manifest.json').read_bytes()).hexdigest()
    if state.get('release_manifest_sha256', identity) != identity:
        raise ValueError('release manifest identity differs')
    return identity


def workflow(release):
    sys.path.insert(0, str(release))
    from simulation import task5_experiments
    return task5_experiments


def pending(work, output, phase, plan, allow_failed=False):
    result = []
    for index, (entry, replicate) in enumerate(work.tasks_for(plan)):
        path = work.record_path(output, phase, entry, replicate)
        if not path.exists():
            result.append(index)
            continue
        record = work.validate_record(read(path), plan, entry, replicate)
        if not record['complete']:
            if not allow_failed:
                raise RuntimeError('failed method record retained; inspect then resume: ' + str(path))
            result.append(index)
    return result


def make_wave(work, output, phase, plan, measurements, config, allow_failed=False):
    tasks = work.tasks_for(plan)
    indices = pending(work, output, phase, plan, allow_failed)
    groups = {}
    for index in indices:
        scenario = tasks[index][0]['scenario']
        groups.setdefault((scenario['n'], scenario['p']), []).append(index)
    workers = []
    estimates = []
    memory = 0
    for shape, indexes in sorted(groups.items()):
        seconds = 2 * measurements[shape]['seconds']
        target = min(config['seconds_per_chunk'], config['worker_time_limit_minutes'] * 60 - 60)
        size = max(1, int(target / seconds))
        for offset in range(0, len(indexes), size):
            batch = indexes[offset:offset + size]
            workers.append(batch)
            estimates.append(seconds * len(batch) + 60)
            memory = max(memory, math.ceil(2 * measurements[shape]['peak_memory_mb']))
            if len(workers) >= 512:
                return dict(phase=phase, workers=workers, memory_mb=memory,
                            minutes=math.ceil(max(estimates) / 60), retry_failures=allow_failed)
    return dict(phase=phase, workers=workers, memory_mb=memory,
                minutes=math.ceil(max(estimates, default=60) / 60), retry_failures=allow_failed)


def submit_pair(config, release, output, state, stage, mapping=None):
    state_path = output / 'controller_state.json'
    def submit(argv, slot):
        state['submission_intent'] = argv
        atomic(state_path, state)
        job = command(argv).split(';')[0]
        if not job.isdigit():
            raise ValueError('unrecognized sbatch acknowledgement: ' + job)
        state.pop('submission_intent')
        state[slot] = job
        state['history'].append(dict(stage=stage, job_id=job, argv=argv))
        atomic(state_path, state)
        return job
    state['stage'] = stage
    state['advance_job_id'] = None
    state.pop('blocked_stage', None)
    state.pop('error', None)
    if mapping is not None:
        work = workflow(release)
        state['wave_number'] = state.get('wave_number', 0) + 1
        state['wave_file'] = 'worker_waves/%06d.json' % state['wave_number']
        mapping.update(run_id=work.load_plan(output, mapping['phase'])['run_id'])
        work.io.write_sealed(output / state['wave_file'], mapping)
    submit(sbatch_args(config, release, output, stage, mapping), 'job_id')
    submit(sbatch_args(config, release, output, 'advance', dependency=state['job_id']), 'advance_job_id')
    return state


def guard(state, config, release):
    if state.get('config_hash') != digest(config):
        raise ValueError('resume configuration differs; preserve original settings')
    if state.get('submission_intent'):
        raise ValueError('interrupted sbatch acknowledgement; reconcile squeue/sacct before resume')
    source_check(release, state)


def continue_phase(config, release, output, state, work, allow_failed=False):
    phase = state['phase']
    plan = work.load_plan(output, phase)
    benchmark = work.io.read_sealed(output / 'benchmark/production.json')
    environment = work.io.environment()
    fingerprint = work.io.digest({key: value for key, value in environment.items() if key not in ('executable', 'platform')})
    env_path = output / 'runtime_environment.json'
    if env_path.exists() and work.io.read_sealed(env_path)['fingerprint'] != fingerprint:
        raise ValueError('runtime environment fingerprint differs')
    measurements = measurement_table(benchmark, plan['implementation_hash'], fingerprint)
    estimate = resource_estimate(plan, measurements, config)
    work.io.write_sealed(output / (phase + '_resource_estimate.json'), estimate)
    mapping = make_wave(work, output, phase, plan, measurements, config, allow_failed)
    if mapping['workers']:
        return submit_pair(config, release, output, state, 'worker', mapping)
    result = work.collect(output, phase)
    if isinstance(result, dict) and result.get('complete') is False:
        raise RuntimeError('collection incomplete: ' + phase)
    if phase == 'pilot':
        work.decide(output)
        work.load_plan(output, 'confirm')  # Requires the immutable confirmation lock.
        state['phase'] = 'confirm'
        return continue_phase(config, release, output, state, work)
    work.write_report(output)
    state.update(stage='DONE', job_id=None, advance_job_id=None)
    atomic(output / 'controller_state.json', state)
    atomic(output / 'DONE.json', {'status': 'complete', 'phase': 'confirm', 'config_hash': digest(config)})
    return state


def start(config, release, output, resume=False, dry_run=False):
    validate_config(config)
    if dry_run:
        return dict(dry_run=True, stages=['bootstrap smoke/init/8 B500 benchmarks', 'pilot arrays',
                    'afterany collect/immutable decision', 'mandatory confirm arrays', 'report/DONE'],
                    command=sbatch_args(config, release, output, 'bootstrap'))
    output.mkdir(parents=True, exist_ok=True)
    (output / 'logs').mkdir(exist_ok=True)
    path = output / 'controller_state.json'
    with lock(output / 'controller.lock'):
        if not resume:
            if path.exists():
                raise ValueError('run exists: use resume')
            runtime = {key: value for key, value in config.items() if key != 'ssh'}
            atomic(output / 'runtime_config.json', runtime)
            state = dict(config_hash=digest(config), release_manifest_sha256=source_check(release, {}),
                         phase='pilot', stage='bootstrap', history=[])
            return submit_pair(config, release, output, state, 'bootstrap')
        state = read(path)
        guard(state, config, release)
        if state['stage'] == 'DONE':
            return state
        for key in ('job_id', 'advance_job_id'):
            if state.get(key) and job_state(state[key]) == 'RUNNING':
                raise RuntimeError('existing Task5 job active: ' + state[key])
        stage = state.get('blocked_stage', state['stage'])
        if stage == 'bootstrap':
            return submit_pair(config, release, output, state, 'bootstrap')
        return continue_phase(config, release, output, state, workflow(release), allow_failed=True)


def execute_stage(release, output, stage):
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('scientific work requires Slurm compute allocation')
    config = validate_config(read(output / 'runtime_config.json'))
    # sbatch may dispatch before its caller persists the acknowledged job ID.
    with lock(output / 'controller.lock'):
        state = read(output / 'controller_state.json')
        guard(state, config, release)
    work = workflow(release)
    if stage == 'bootstrap':
        work.run_smoke(output)
        if (output / 'pilot_plan.json').exists():
            work.load_plan(output, 'pilot')
        else:
            work.initialize(output)
        work.benchmark(output)
        return
    if stage == 'worker':
        mapping = work.io.read_sealed(output / state['wave_file'])
        phase = mapping['phase']
        plan = work.load_plan(output, phase)
        if mapping['run_id'] != plan['run_id'] or os.environ.get('SLURM_ARRAY_JOB_ID') != state['job_id']:
            raise ValueError('worker mapping/job identity differs')
        benchmark = work.io.read_sealed(output / 'benchmark/production.json')
        environment = work.io.environment()
        fingerprint = work.io.digest({key: value for key, value in environment.items() if key not in ('executable', 'platform')})
        measurements = measurement_table(benchmark, plan['implementation_hash'], fingerprint)
        tasks = work.tasks_for(plan)
        deadline = time.monotonic() + mapping['minutes'] * 60 - 30
        for index in mapping['workers'][int(os.environ['SLURM_ARRAY_TASK_ID'])]:
            entry, replicate = tasks[index]
            scenario = entry['scenario']
            required = 2 * measurements[(scenario['n'], scenario['p'])]['seconds']
            if time.monotonic() + required > deadline:
                raise RuntimeError('PAUSED: worker time budget exhausted; inspect then resume')
            work.run_worker(output, phase, index, chunk_size=1, retry_failures=mapping['retry_failures'])
            record = work.validate_record(read(work.record_path(output, phase, entry, replicate)), plan, entry, replicate)
            if not record['complete']:
                raise RuntimeError('method failure; checkpoint retained for explicit resume')
        return
    with lock(output / 'controller.lock'):
        state = read(output / 'controller_state.json')
        guard(state, config, release)
        try:
            status = job_state(state['job_id'])
            if status != 'COMPLETED':
                raise RuntimeError('predecessor ' + state['job_id'] + ': ' + status + '; inspect logs then resume')
            return continue_phase(config, release, output, state, work)
        except Exception as error:
            state.update(blocked_stage=state['stage'], stage='BLOCKED', error=str(error))
            atomic(output / 'controller_state.json', state)
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('start', 'resume', 'status', 'download', 'bootstrap', 'worker', 'advance'))
    parser.add_argument('--config', type=Path)
    parser.add_argument('--release', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    release = args.release or Path(__file__).resolve().parents[2]
    if args.action in ('bootstrap', 'worker', 'advance'):
        result = execute_stage(release, args.output, args.action)
    else:
        config = read(args.config)
        output = Path(config['remote_project_dir']) / 'results/task5_unified_v1' / config['run_name']
        if args.action == 'status':
            result = read(output / 'controller_state.json')
        elif args.action == 'download':
            import tarfile
            destination = args.destination or Path(config.get('download_dir', './task5_download'))
            destination.mkdir(parents=True, exist_ok=True)
            archive = destination / (config['run_name'] + '.tar.gz')
            with tarfile.open(archive, 'x:gz') as bundle:
                bundle.add(output, arcname=config['run_name'])
            result = {'download_archive': str(archive.resolve())}
        else:
            result = start(config, release, output, args.action == 'resume', args.dry_run)
    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__': main()
