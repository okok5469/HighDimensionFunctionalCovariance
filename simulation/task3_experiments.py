"""Task3 full-known-target experiments, immutable plans and worker CLI.

No large experiment is run on import. The legacy cross driver is unchanged.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time

import numpy as np

from common.statistic_calculator_517 import covariance_one_sample
from common.xue_helper import run_xue_one_sample
from simulation import task3_io as io


def method_config():
    return dict(ours='covariance_one_sample/v1.1/full_known_gamma0',
                xue='Xue-1S-EV-full/xue-audit-v1/fixed-Fourier',
                xue_s=[5, 11, 21], mean_mode='estimate', test_scope='all')


def seal_plan(plan):
    plan = dict(plan)
    plan.pop('run_id', None)
    plan['run_id'] = io.digest(plan)
    return plan


def create_plan(phase='pilot', skip_dimension_extension=False):
    from simulation.task3_generators import make_scenario, spec_ids
    if phase not in ('pilot', 'smoke'):
        raise ValueError('create_plan expects pilot or smoke')
    config_path = Path(__file__).with_name('configs') / 'task3' / (phase + '.json')
    config = json.loads(config_path.read_text(encoding='utf-8'))
    n, p, repeats, B = (config[key] for key in ('n', 'p', 'repeats', 'B'))
    if config['xue_s'] != [5, 11, 21] or config['alpha'] != .05:
        raise ValueError('task3 method settings are frozen')
    null_specs = ['spectrum_fast_b4', 'spectrum_slow_b1', 'spectrum_flat_b0',
                  'legacy_M1_full_reference', 'legacy_M2_full_reference']
    entries = []
    for spec in null_specs:
        entries.append(dict(scenario=make_scenario(spec, 0., n=n, p=p), repeats=repeats, role='null'))
    for spec in list(spec_ids()):
        for tau in config.get('alternative_taus', [.15, .30]):
            entries.append(dict(scenario=make_scenario(spec, tau, n=n, p=p), repeats=repeats, role='alternative'))
    for entry in entries:
        entry['scenario_id'] = io.digest(entry['scenario'])[:20]
    if len(entries) != config['actual_scenarios'] or sum(e['repeats'] for e in entries) != config['data_sets']:
        raise ValueError('physical scenario or repetition counts disagree with configuration')
    sources = io.source_manifest()
    return seal_plan(dict(study='task3_v1', phase=phase, B=B, alpha=.05,
                          methods=method_config(), scenarios=entries,
                          skip_dimension_extension=bool(skip_dimension_extension),
                          implementation_hash=io.digest(sources), source_manifest=sources))


def save_plan(root, plan):
    root = Path(root)
    io.write_sealed(root / (plan['phase'] + '_plan.json'), plan)


def load_plan(root, phase, check_sources=True):
    plan = io.read_sealed(Path(root) / (phase + '_plan.json'))
    if seal_plan(plan)['run_id'] != plan.get('run_id'):
        raise ValueError('plan run_id mismatch')
    if plan['methods'] != method_config():
        raise ValueError('method identity mismatch')
    if check_sources and io.digest(io.source_manifest()) != plan['implementation_hash']:
        raise ValueError('source/configuration hashes changed; do not combine implementations')
    return plan


def initialize(root, skip_dimension_extension=False):
    from simulation.task3_generators import diagnostics
    root = Path(root)
    plan = create_plan('pilot', skip_dimension_extension)
    save_plan(root, plan)
    policy_path = Path(__file__).with_name('configs') / 'task3' / 'confirmation_policy.json'
    policy = json.loads(policy_path.read_text(encoding='utf-8'))
    io.write_sealed(root / 'confirmation_policy.json', policy)
    io.write_sealed(root / 'implementation_manifest.json', plan['source_manifest'])
    # Each deterministic scenario is persisted once, never in each replicate.
    for entry in plan['scenarios']:
        io.write_sealed(root / 'scenario_diagnostics' / (entry['scenario_id'] + '.json'),
                        diagnostics(entry['scenario']))
    import pandas as pd
    pd.DataFrame([dict(scenario_id=e['scenario_id'], **e['scenario'], repeats=e['repeats'])
                  for e in plan['scenarios']]).to_csv(root / 'scenario_catalog.csv', index=False)
    return plan


def _compact(result):
    # Deterministic operators and targets have content references; samples and
    # dense coefficient statistic matrices are never repeated in JSON.
    return {key: value for key, value in result.items() if key not in
            ('S', 'm', 'q', 'operator', 'sigma0', 'channel_pairs', 'grid')}


def run_replicate(scenario, phase, replicate, B=500, alpha=.05,
                  method_order=('ours', 'xue_s5', 'xue_s11', 'xue_s21')):
    from simulation.task3_generators import generate, rng, data_key
    expected = {'ours', 'xue_s5', 'xue_s11', 'xue_s21'}
    if len(method_order) != 4 or set(method_order) != expected:
        raise ValueError('execute each fixed method exactly once')
    start = time.perf_counter()
    try:
        generated = generate(scenario, phase, replicate)
    except (ValueError, FloatingPointError, MemoryError, np.linalg.LinAlgError) as error:
        failed = dict(status='failed', reject=None, pvalue=None,
                      failure_reason='generation: ' + type(error).__name__ + ': ' + str(error), seconds=0.)
        return dict(study='task3_v1', phase=phase, replicate=replicate, scenario=scenario,
                    scenario_id=io.digest(scenario)[:20], data_id=io.digest(data_key(scenario, phase, replicate)),
                    data_sha256=None, gamma0_sha256=None, methods={name: dict(failed) for name in method_order},
                    truth_metadata=dict(data_key=data_key(scenario, phase, replicate)),
                    complete=False, generation_seconds=time.perf_counter()-start, seconds=time.perf_counter()-start)
    Y, grid, target = generated['Y'], generated['grid'], generated['gamma0']
    generation_seconds = time.perf_counter() - start
    data_hash, target_hash = io.array_digest(Y), io.array_digest(target)
    methods = {}
    for name in method_order:
        method_start = time.perf_counter()
        try:
            if name == 'ours':
                result = covariance_one_sample(Y, target, B=B, alpha=alpha,
                    rng=rng(scenario, phase, replicate, 'bootstrap'), grid=grid,
                    config_id=generated['data_id'])
                result.update(status='ok')
            else:
                s = int(name.split('s')[-1])
                result = run_xue_one_sample(Y, gamma0=target, s=s, alpha=alpha, grid=grid)
                result.update(identity='Xue-1S-EV-full / xue-audit-v1 / fixed-Fourier-s' + str(s),
                              implementation_version='xue-audit-v1',
                              operator_sha256=io.array_digest(result['operator']),
                              sigma0_sha256=io.array_digest(result['sigma0']))
            result = _compact(result)
        except (ValueError, FloatingPointError, MemoryError, np.linalg.LinAlgError) as error:
            result = dict(status='failed', reject=None, pvalue=None,
                          failure_reason=type(error).__name__ + ': ' + str(error))
        result.update(data_id=generated['data_id'], data_sha256=data_hash,
                      gamma0_sha256=target_hash, seconds=time.perf_counter()-method_start)
        methods[name] = result
    return io.plain(dict(study='task3_v1', phase=phase, replicate=replicate,
        scenario=scenario, scenario_id=io.digest(scenario)[:20], data_id=generated['data_id'],
        data_sha256=data_hash, gamma0_sha256=target_hash, methods=methods,
        truth_metadata=generated['truth_metadata'], grid=grid,
        complete=all(m['status'] == 'ok' and isinstance(m['reject'], (bool, np.bool_)) for m in methods.values()),
        generation_seconds=generation_seconds, seconds=time.perf_counter()-start))


def tasks_for(plan):
    return [(entry, replicate) for entry in plan['scenarios'] for replicate in range(entry['repeats'])]


def record_path(root, phase, entry, replicate):
    return Path(root) / phase / 'replicates' / ('%s_%04d.json' % (entry['scenario_id'], replicate))


def validate_record(record, plan, entry, replicate):
    from simulation.task3_generators import data_key
    sealed = dict(record)
    checksum = sealed.pop('record_sha256', None)
    expected_id = io.digest(data_key(entry['scenario'], plan['phase'], replicate))
    valid = (checksum == io.digest(sealed) and record.get('run_id') == plan['run_id']
             and record.get('implementation_hash') == plan['implementation_hash']
             and record.get('phase') == plan['phase'] and record.get('replicate') == replicate
             and record.get('scenario_id') == entry['scenario_id']
             and record.get('data_id') == expected_id and record.get('methods_config') == plan['methods']
             and record.get('scenario') == entry['scenario'])
    if not valid:
        raise ValueError('invalid record provenance: ' + entry['scenario_id'] + '/' + str(replicate))
    methods = record.get('methods', {})
    if set(methods) != {'ours', 'xue_s5', 'xue_s11', 'xue_s21'}:
        raise ValueError('checkpoint must contain all four fixed methods')
    derived_complete = all(method.get('status') == 'ok' for method in methods.values())
    if record.get('complete') is not derived_complete:
        raise ValueError('checkpoint complete flag disagrees with method results')
    for name, method in methods.items():
        if method['status'] != 'ok':
            if method.get('reject') is not None or not method.get('failure_reason'):
                raise ValueError('failure must preserve its reason and have no decision')
            continue
        if not isinstance(method.get('reject'), bool) or method.get('data_sha256') != record['data_sha256']:
            raise ValueError('invalid shared input or decision')
        if method.get('gamma0_sha256') != record['gamma0_sha256']:
            raise ValueError('target mismatch')
        if method.get('data_id') != expected_id or method.get('alpha') != plan['alpha']:
            raise ValueError('method data or significance level mismatch')
        if method.get('mean_mode', 'estimate') != 'estimate' or method.get('test_scope', 'all') != 'all':
            raise ValueError('checkpoint changes the tested problem')
        pvalue = method.get('pvalue')
        if not isinstance(pvalue, (float, int)) or not math.isfinite(pvalue) or not 0 <= pvalue <= 1:
            raise ValueError('invalid checkpoint pvalue')
        if method['reject'] != (pvalue < plan['alpha']):
            raise ValueError('checkpoint decision and pvalue disagree')
        if not isinstance(method.get('statistic'), (float, int)) or not math.isfinite(method['statistic']):
            raise ValueError('invalid checkpoint statistic')
        if name == 'ours':
            boot = method.get('bootstrap_statistics', [])
            if len(boot) != plan['B'] or not np.isfinite(boot).all() or method.get('method_version') != 'v1.1':
                raise ValueError('bootstrap checkpoint identity or values mismatch')
        elif method.get('s') != int(name.split('s')[-1]) or method.get('implementation_version') != 'xue-audit-v1':
            raise ValueError('Xue checkpoint identity mismatch')
    return record


def run_worker(root, phase, chunk_id, chunk_size=None, retry_failures=False):
    plan = load_plan(root, phase)
    current_environment = io.environment()
    fingerprint = io.digest({key: value for key, value in current_environment.items()
                             if key not in ('executable', 'platform')})
    with io.record_lock(Path(root) / 'environment.lock', blocking=True):
        io.write_sealed(Path(root) / 'runtime_environment.json',
                        dict(fingerprint=fingerprint, details=current_environment))
    mapping_path = Path(root) / (phase + '_workers.json')
    if mapping_path.exists():
        mapping = io.read_sealed(mapping_path)
        if mapping['run_id'] != plan['run_id']:
            raise ValueError('worker mapping run mismatch')
        chunk_size = mapping['chunk_size']
    if chunk_size is None:
        raise ValueError('run plan-workers first, or supply an explicit chunk size')
    if chunk_size < 1 or chunk_id < 0:
        raise ValueError('invalid chunk size or index')
    tasks = tasks_for(plan)
    batch = tasks[chunk_id*chunk_size:(chunk_id+1)*chunk_size]
    if not batch:
        raise ValueError('chunk_id outside plan')
    failed = []
    for entry, replicate in batch:
        path = record_path(root, phase, entry, replicate)
        path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = path.with_suffix('.lock')
        with io.record_lock(lock_path):
            if path.exists():
                previous = validate_record(json.loads(path.read_text(encoding='utf-8')), plan, entry, replicate)
                if previous['complete']:
                    continue
                if not retry_failures:
                    failed.append(str(path))
                    continue
                # Preserve each failed attempt without changing its data key.
                attempt_dir = path.parent.parent / 'failed_attempts'
                attempt_dir.mkdir(exist_ok=True)
                backup = attempt_dir / (path.stem + '_' + previous['record_sha256'][:16] + '.json')
                io.write_sealed(backup, previous)
            record = run_replicate(entry['scenario'], phase, replicate, B=plan['B'], alpha=plan['alpha'])
            record.update(run_id=plan['run_id'], implementation_hash=plan['implementation_hash'],
                          methods_config=plan['methods'], environment_hash=fingerprint)
            record['record_sha256'] = io.digest(record)
            io.atomic_json(path, record)
            if not record['complete']:
                failed.append(str(path))
    if failed:
        raise ValueError('failed method records retained: ' + ', '.join(failed))
    return len(batch)


def collect(root, phase):
    import pandas as pd
    plan = load_plan(root, phase, check_sources=False)
    records, failures = [], []
    if io.digest(io.source_manifest()) != plan['implementation_hash']:
        failures.append(dict(scenario_id='all', replicate=None, reason='source_manifest_mismatch'))
    environment_path = Path(root) / 'runtime_environment.json'
    environment_hash = io.read_sealed(environment_path)['fingerprint'] if environment_path.exists() else None
    expected = set()
    seen_data = set()
    for entry, replicate in tasks_for(plan):
        path = record_path(root, phase, entry, replicate)
        expected.add(path.name)
        if not path.exists():
            failures.append(dict(scenario_id=entry['scenario_id'], replicate=replicate, reason='missing'))
            continue
        try:
            record = validate_record(json.loads(path.read_text(encoding='utf-8')), plan, entry, replicate)
            if environment_hash is None or record.get('environment_hash') != environment_hash:
                raise ValueError('record runtime environment mismatch')
            if record['data_id'] in seen_data:
                raise ValueError('duplicate data_id')
            seen_data.add(record['data_id'])
            records.append(record)
            if not record['complete']:
                failures.append(dict(scenario_id=entry['scenario_id'], replicate=replicate, reason='method_failure'))
        except (ValueError, KeyError, TypeError) as error:
            failures.append(dict(scenario_id=entry['scenario_id'], replicate=replicate, reason=str(error)))
    for path in (Path(root) / phase / 'replicates').glob('*.json'):
        if path.name not in expected:
            failures.append(dict(scenario_id=path.stem, replicate=None, reason='unexpected_record'))
    complete = not failures and len(records) == len(tasks_for(plan))
    integrity = dict(phase=phase, run_id=plan['run_id'], complete=complete,
                     requested=len(tasks_for(plan)), completed=len(records), failures=failures)
    io.atomic_json(Path(root) / (phase + '_integrity.json'), integrity)
    Path(root).mkdir(parents=True, exist_ok=True)
    pd.DataFrame(failures, columns=['scenario_id', 'replicate', 'reason']).to_csv(Path(root) / (phase + '_failures.csv'), index=False)
    from simulation.task3_summary import write_reports
    write_reports(plan, records, root, phase=phase, failures=failures)
    return integrity


def lock_confirmation(root):
    from simulation.task3_summary import select_candidates, confirmation_scenarios
    import pandas as pd
    root = Path(root)
    plan = load_plan(root, 'pilot')
    integrity = collect(root, 'pilot')
    if not integrity['complete']:
        raise ValueError('pilot incomplete; confirmation is prohibited')
    from simulation.task3_summary import summarize_records
    records = [json.loads(record_path(root, 'pilot', e, r).read_text(encoding='utf-8')) for e, r in tasks_for(plan)]
    rows = summarize_records(plan, records)['summary']
    policy = io.read_sealed(root / 'confirmation_policy.json')
    selection = select_candidates(rows, policy)
    entries = confirmation_scenarios(selection, plan['skip_dimension_extension'])
    for entry in entries:
        entry['scenario_id'] = io.digest(entry['scenario'])[:20]
    locked = dict(study='task3_v1', pilot_run_id=plan['run_id'], selection=selection,
                  confirmation_policy=policy, scenarios=entries, methods=plan['methods'],
                  B=500, alpha=.05, implementation_hash=plan['implementation_hash'],
                  source_manifest=plan['source_manifest'], phase='confirm')
    locked = seal_plan(locked)
    io.write_sealed(root / 'confirm_locked.json', locked)
    save_plan(root, locked)
    pd.DataFrame(selection['ranking']).to_csv(root / 'candidate_selection.csv', index=False)
    from simulation.task3_generators import diagnostics
    for entry in entries:
        io.write_sealed(root / 'scenario_diagnostics' / (entry['scenario_id'] + '.json'), diagnostics(entry['scenario']))
    return locked


def peak_memory_mb():
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
                'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
                'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
        info = Counters()
        info.cb = ctypes.sizeof(info)
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        psapi = ctypes.WinDLL('psapi', use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        process = kernel.GetCurrentProcess()
        if not psapi.GetProcessMemoryInfo(process, ctypes.byref(info), info.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return info.PeakWorkingSetSize / 2**20
    import resource
    import sys
    scale = 2**20 if sys.platform == 'darwin' else 1024
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / scale


def benchmark(root, small=False, skip_dimension_extension=False):
    from simulation.task3_generators import make_scenario
    root = Path(root)
    shapes = [(24, 6)] if small else [(200, 20)]
    if not small and not skip_dimension_extension:
        shapes += [(400, 20), (200, 50)]
    path = root / 'benchmark' / ('small.json' if small else 'production.json')
    if path.exists():
        previous = io.read_sealed(path)
        actual_shapes = [(m['n'], m['p']) for m in previous['measurements']]
        if previous['implementation_hash'] != io.digest(io.source_manifest()) or actual_shapes != shapes:
            raise ValueError('benchmark implementation or requested shapes changed')
        return previous
    measured = []
    for n, p in shapes:
        record = run_replicate(make_scenario('spectrum_flat_b0', .30, n=n, p=p),
                               'benchmark', 0, B=3 if small else 500)
        if not record['complete']:
            io.atomic_json(path.with_name('failure.json'), record)
            raise ValueError('benchmark numerical failure')
        measured.append(dict(n=n, p=p, M=64, B=3 if small else 500,
            generation_seconds=record['generation_seconds'], seconds=record['seconds'],
            method_seconds={k: v['seconds'] for k, v in record['methods'].items()},
            peak_memory_mb=peak_memory_mb(), data_id=record['data_id']))
    result = dict(small=small, measurements=measured, environment=io.environment(),
                  implementation_hash=io.digest(io.source_manifest()),
                  memory_scope='process high-water mark, conservative across benchmark shapes')
    io.write_sealed(path, result)
    return result


def plan_workers(root, phase, seconds_per_chunk=1800):
    root = Path(root)
    plan = load_plan(root, phase)
    measured = io.read_sealed(root / 'benchmark' / 'production.json')
    if measured['small'] or measured['implementation_hash'] != plan['implementation_hash']:
        raise ValueError('production benchmark source mismatch')
    worst = max(item['seconds'] for item in measured['measurements'])
    # Budget safety factor accounts for family and queue variation.
    chunk_size = max(1, min(10, int(seconds_per_chunk / (2*worst))))
    count = math.ceil(len(tasks_for(plan))/chunk_size)
    memory_mb = math.ceil(max(item['peak_memory_mb'] for item in measured['measurements'])*2)
    allocated_seconds = max(seconds_per_chunk, math.ceil(2*worst*chunk_size))
    mapping = dict(run_id=plan['run_id'], chunk_size=chunk_size, chunks=count,
                   array='0-%d%%8' % (count-1), concurrency=8,
                   memory_mb=memory_mb, seconds_per_chunk=allocated_seconds,
                   assumptions='Same-(n,p) M64 flat timings extrapolated to all families and legacy M30; family and queue variation require a 2x scheduling safety factor; ideal wall time excludes queue wait.',
                   worker_hours_estimate=sum(item['repeats'] * next(
                       measurement['seconds'] for measurement in measured['measurements']
                       if (measurement['n'], measurement['p']) == (item['scenario']['n'], item['scenario']['p']))
                       for item in plan['scenarios']) / 3600)
    mapping['wall_hours_estimate_at_8'] = mapping['worker_hours_estimate']/8
    io.write_sealed(root / (phase + '_workers.json'), mapping)
    return mapping


def run_smoke(root):
    root = Path(root)
    plan = create_plan('smoke')
    save_plan(root, plan)
    from simulation.task3_generators import diagnostics
    for entry in plan['scenarios']:
        io.write_sealed(root / 'scenario_diagnostics' / (entry['scenario_id'] + '.json'), diagnostics(entry['scenario']))
    for chunk_id in range(len(tasks_for(plan))):
        run_worker(root, 'smoke', chunk_id, chunk_size=1)
    result = collect(root, 'smoke')
    if not result['complete']:
        raise ValueError('smoke incomplete')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('init', 'smoke', 'benchmark', 'plan-workers', 'worker',
                                          'collect', 'lock', 'report', 'status', 'legacy'))
    parser.add_argument('--output', type=Path, default=Path('results/task3_v1'))
    parser.add_argument('--phase', choices=('pilot', 'confirm', 'smoke'), default='pilot')
    parser.add_argument('--chunk-id', type=int, default=0)
    parser.add_argument('--chunk-size', type=int)
    parser.add_argument('--seconds-per-chunk', type=int, default=1800)
    parser.add_argument('--small', action='store_true')
    parser.add_argument('--skip-dimension-extension', action='store_true')
    parser.add_argument('--retry-failures', action='store_true')
    args, extra = parser.parse_known_args(argv)
    if args.command != 'legacy' and extra:
        parser.error('unknown arguments: ' + ' '.join(extra))
    if args.command == 'legacy':
        from simulation.covariance_experiments import main as legacy
        return legacy(['--profile', 'formal', '--output', str(args.output)] + extra)
    actions = {
        'init': lambda: initialize(args.output, args.skip_dimension_extension),
        'smoke': lambda: run_smoke(args.output),
        'benchmark': lambda: benchmark(args.output, args.small, args.skip_dimension_extension),
        'plan-workers': lambda: plan_workers(args.output, args.phase, args.seconds_per_chunk),
        'worker': lambda: run_worker(args.output, args.phase, args.chunk_id, args.chunk_size, args.retry_failures),
        'collect': lambda: collect(args.output, args.phase),
        'report': lambda: collect(args.output, args.phase),
        'lock': lambda: lock_confirmation(args.output),
        'status': lambda: {phase: json.loads(path.read_text(encoding='utf-8'))
                           for phase in ('pilot', 'confirm', 'smoke')
                           for path in [args.output / (phase + '_integrity.json')] if path.exists()},
    }
    result = actions[args.command]()
    print(json.dumps(io.plain(result), ensure_ascii=True))
    if args.command in ('collect', 'report') and not result['complete']:
        raise SystemExit(2)
    return result


if __name__ == '__main__':
    main()
