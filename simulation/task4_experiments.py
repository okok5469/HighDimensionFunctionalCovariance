"""Task4 isolated, immutable fixed-method search workflow (Python 3.9+)."""
import argparse
import csv
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
from simulation.task3_experiments import method_config, seal_plan


def data_phase(phase):
    return 'pilot' if phase == 'fallback' else phase


def source_manifest():
    root = Path(__file__).resolve().parents[1]
    paths = list((root/'common').rglob('*.py')) + list((root/'simulation').glob('*.py'))
    paths += [root/'simulation'/name for name in ('task3_io.py','task3_summary.py',
        'task3_experiments.py','task3_generators.py','task4_generators.py',
        'task4_design.py','task4_experiments.py','covariance_experiments.py')]
    paths += list((root/'simulation/configs/task4').glob('*.json'))
    paths += list((root/'cluster/task4').glob('*.py')) + list((root/'cluster/task4').glob('*.slurm'))
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(paths))}


def create_plan(phase='pilot'):
    from simulation.task4_design import pilot_entries, fallback_entries
    entries = fallback_entries() if phase == 'fallback' else pilot_entries()
    if phase not in ('pilot','fallback','smoke'):
        raise ValueError('invalid initial plan phase')
    if phase == 'smoke':
        entries = [dict(e, repeats=1) for e in entries[:1]]
    sources = source_manifest()
    return seal_plan(dict(study='task4_fixed_methods_v1', phase=phase,
        B=3 if phase == 'smoke' else 500, alpha=.05, methods=method_config(),
        scenarios=entries, implementation_hash=io.digest(sources), source_manifest=sources))


def save_plan(root, plan):
    io.write_sealed(Path(root)/(plan['phase']+'_plan.json'),plan)


def load_plan(root, phase, check_sources=True):
    plan = io.read_sealed(Path(root)/(phase+'_plan.json'))
    if plan['study'] != 'task4_fixed_methods_v1' or seal_plan(plan)['run_id'] != plan['run_id']:
        raise ValueError('task4 plan identity mismatch')
    if plan['methods'] != method_config() or plan['alpha'] != .05:
        raise ValueError('frozen method configuration mismatch')
    if check_sources and io.digest(source_manifest()) != plan['implementation_hash']:
        raise ValueError('source/configuration hashes changed')
    return plan


def save_diagnostics(root, plan):
    from simulation.task4_generators import diagnostics
    for entry in plan['scenarios']:
        io.write_sealed(Path(root)/'scenario_diagnostics'/(entry['scenario_id']+'.json'), diagnostics(entry['scenario']))


def initialize(root):
    plan = create_plan()
    save_plan(root,plan)
    io.write_sealed(Path(root)/'implementation_manifest.json',plan['source_manifest'])
    save_diagnostics(root,plan)
    return plan


def _compact(result):
    # Deterministic operators and targets have content references; samples and
    # dense coefficient statistic matrices are never repeated in JSON.
    return {key: value for key, value in result.items() if key not in
            ('S', 'm', 'q', 'operator', 'sigma0', 'channel_pairs', 'grid')}


def run_replicate(scenario, phase, replicate, B=500, alpha=.05,
                  method_order=('ours', 'xue_s5', 'xue_s11', 'xue_s21')):
    from simulation.task4_generators import generate, rng, data_key
    expected = {'ours', 'xue_s5', 'xue_s11', 'xue_s21'}
    if len(method_order) != 4 or set(method_order) != expected:
        raise ValueError('execute each fixed method exactly once')
    start = time.perf_counter()
    try:
        generated = generate(scenario, data_phase(phase), replicate)
    except (ValueError, FloatingPointError, MemoryError, np.linalg.LinAlgError) as error:
        failed = dict(status='failed', reject=None, pvalue=None,
                      failure_reason='generation: ' + type(error).__name__ + ': ' + str(error), seconds=0.)
        return dict(study='task4_fixed_methods_v1', phase=phase, replicate=replicate, scenario=scenario,
                    scenario_id=io.digest(scenario)[:20], data_id=io.digest(data_key(scenario, data_phase(phase), replicate)),
                    data_sha256=None, gamma0_sha256=None, methods={name: dict(failed) for name in method_order},
                    truth_metadata=dict(data_key=data_key(scenario, data_phase(phase), replicate)),
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
                    rng=rng(scenario, data_phase(phase), replicate, 'bootstrap'), grid=grid,
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
    return io.plain(dict(study='task4_fixed_methods_v1', phase=phase, replicate=replicate,
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
    from simulation.task4_generators import data_key
    sealed = dict(record)
    checksum = sealed.pop('record_sha256', None)
    expected_id = io.digest(data_key(entry['scenario'], data_phase(plan['phase']), replicate))
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

def collect(root, phase):
    from simulation.task3_summary import summarize_records, _report, _write_csv
    root=Path(root)
    plan=load_plan(root,phase)
    records, failures, expected, seen = [], [], set(), set()
    env_path=root/'runtime_environment.json'
    fingerprint=io.read_sealed(env_path)['fingerprint'] if env_path.exists() else None
    for entry, replicate in tasks_for(plan):
        path=record_path(root,phase,entry,replicate)
        expected.add(path.name)
        if not path.exists():
            failures.append(dict(scenario_id=entry['scenario_id'],replicate=replicate,reason='missing'))
            continue
        try:
            record=validate_record(json.loads(path.read_text(encoding='utf-8')),plan,entry,replicate)
            if fingerprint is None or record.get('environment_hash') != fingerprint:
                raise ValueError('runtime environment mismatch')
            if record['data_id'] in seen: raise ValueError('duplicate data_id')
            seen.add(record['data_id'])
            records.append(record)
            if not record['complete']:
                failures.append(dict(scenario_id=entry['scenario_id'],replicate=replicate,reason='method_failure'))
        except (ValueError,KeyError,TypeError) as error:
            failures.append(dict(scenario_id=entry['scenario_id'],replicate=replicate,reason=str(error)))
    for path in (root/phase/'replicates').glob('*.json'):
        if path.name not in expected: failures.append(dict(scenario_id=path.stem,reason='unexpected_record'))
    integrity=dict(phase=phase,run_id=plan['run_id'],complete=not failures and len(records)==len(tasks_for(plan)),
                   requested=len(tasks_for(plan)),completed=len(records),failures=failures)
    io.atomic_json(root/(phase+'_integrity.json'),integrity)
    result=summarize_records(plan,records,failures)
    for key,name in [('summary','summary'),('paired','paired_comparisons'),('failures','failures'),('runtime','runtime_summary')]:
        _write_csv(root/(phase+'_'+name+'.csv'),result[key])
    detail=export_details(root,plan,records)
    (root/(phase+'_RESULTS_REPORT.md')).write_text(_report(plan,result).replace('Task3','Task4')+detail,encoding='utf-8')
    write_report(root)
    return integrity


def write_report(root):
    root=Path(root)
    sections=['# Task4 fixed-method model search','',
        'Smoke and benchmark validate execution only. No scientific claim precedes complete independent confirmation.',
        'All four fixed methods share each observed input and complete noisy null target.',
        'Exploratory closeness tolerance: 10 percentage points; formal noninferiority margin: 5 percentage points.',
        'Saturated strong-signal results must be distinguished from evidence about coherent peak geometry.','']
    for phase in ('pilot','fallback'):
        path=root/(phase+'_RESULTS_REPORT.md')
        if path.exists(): sections.append(path.read_text(encoding='utf-8'))
    for filename in ('search_decision.json','confirm_locked.json'):
        path=root/filename
        if path.exists():
            value=io.read_sealed(path)
            sections += ['## '+filename,'',decision_table(value) if filename=='search_decision.json' else '\n'.join('- %s: tau=%s, repeats=%s' % (e['scenario']['spec_id'],e['scenario']['tau'],e['repeats']) for e in value['scenarios'])]
    path=root/'confirm_RESULTS_REPORT.md'
    if path.exists(): sections.append(path.read_text(encoding='utf-8'))
    (root/'TASK4_RESULTS_REPORT.md').write_text('\n\n'.join(sections),encoding='utf-8')
    return {'report':str(root/'TASK4_RESULTS_REPORT.md')}


def _completed_records(root, phase):
    plan=load_plan(root,phase)
    integrity=collect(root,phase)
    if not integrity['complete']: raise ValueError(phase+' incomplete; selection prohibited')
    return plan,[json.loads(record_path(root,phase,e,r).read_text(encoding='utf-8')) for e,r in tasks_for(plan)]


def decide(root):
    from simulation.task4_design import select_candidates, confirmation_entries, lock_spec
    from simulation.task3_summary import summarize_records, _write_csv
    root=Path(root)
    # A persisted final decision is immutable; resume verifies sources and returns it.
    final=root/'search_decision.json'
    if final.exists():
        load_plan(root,'pilot')
        return io.read_sealed(final)
    plan,records=_completed_records(root,'pilot')
    combined=dict(plan,scenarios=list(plan['scenarios']))
    fallback_complete=False
    initial=select_candidates(summarize_records(plan,records)['summary'])
    if initial['fallback_required']:
        fallback=create_plan('fallback')
        save_plan(root,fallback)
        save_diagnostics(root,fallback)
        io.write_sealed(root/'fallback_trigger.json',dict(pilot_run_id=plan['run_id'],selection=initial))
        # A newly triggered branch must run its workers before any final selection.
        if not (root/'fallback_integrity.json').exists():
            return dict(action='fallback',phase='fallback',selection=initial)
        fallback,extra=_completed_records(root,'fallback')
        combined['scenarios'] += fallback['scenarios']
        records += extra
        fallback_complete=True
    selection=select_candidates(summarize_records(combined,records)['summary'],fallback_complete=fallback_complete)
    entries=confirmation_entries(selection)
    action='confirm' if entries else 'done_no_eligible_candidates'
    decision=dict(action=action,selection=selection,pilot_run_id=plan['run_id'],
        fallback_triggered=fallback_complete,implementation_hash=plan['implementation_hash'])
    if entries:
        locked=lock_spec(selection,plan['implementation_hash'],method_config())
        locked.update(pilot_run_id=plan['run_id'], source_manifest=plan['source_manifest'])
        locked=seal_plan(locked)
        io.write_sealed(root/'confirm_locked.json',locked)
        save_plan(root,locked)
        save_diagnostics(root,locked)
    _write_csv(root/'candidate_selection.csv',selection['ranking'])
    io.write_sealed(final,decision)
    write_report(root)
    return decision


def benchmark(root,small=False):
    from simulation.task4_generators import make_scenario
    root=Path(root)
    path=root/'benchmark'/('small.json' if small else 'production.json')
    implementation=io.digest(source_manifest())
    if path.exists():
        value=io.read_sealed(path)
        if value['implementation_hash'] != implementation: raise ValueError('benchmark source mismatch')
        return value
    scenario=make_scenario('coherent_all',.30,n=24 if small else 200,p=6 if small else 20)
    record=run_replicate(scenario,'benchmark',0,B=3 if small else 500)
    if not record['complete']: raise ValueError('benchmark method failed')
    value=dict(small=small,implementation_hash=implementation,environment=io.environment(),
        measurements=[dict(n=scenario['n'],p=scenario['p'],M=64,B=3 if small else 500,
            seconds=record['seconds'],generation_seconds=record['generation_seconds'],
            method_seconds={k:v['seconds'] for k,v in record['methods'].items()},peak_memory_mb=peak_memory_mb())])
    io.write_sealed(path,value)
    return value


def run_smoke(root):
    root=Path(root)
    plan=create_plan('smoke')
    save_plan(root,plan)
    save_diagnostics(root,plan)
    run_worker(root,'smoke',0,1)
    # Verify restart skips the same sealed record.
    run_worker(root,'smoke',0,1)
    result=collect(root,'smoke')
    if not result['complete']: raise ValueError('smoke incomplete')
    return result



def decision_table(decision):
    selection=decision['selection']
    lines=['Action: '+decision['action']+'. Fallback triggered: '+str(decision['fallback_triggered'])+'.',
        '', '| Model | tau | ours power | worst paired difference | usable | high power | saturated | exclusions |',
        '|---|---:|---:|---:|---|---|---|---|']
    for r in selection['ranking']:
        lines.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (r['spec_id'],r['tau'],r['power_ours'],r['delta_min'],r['useful'],r['high_power'],r['saturated'],','.join(r['exclusion_reasons'])))
    lines += ['', 'Calibration screening by null background: '+json.dumps(selection['calibration'],sort_keys=True),
        '', 'High power and exploratory closeness are point estimates. Formal noninferiority requires the locked adjusted interval above -0.05 and accepted matched null calibration.']
    return '\n'.join(lines)


def export_details(root,plan,records):
    from simulation.task4_generators import diagnostics
    from simulation.task3_summary import _write_csv
    rows=[]
    lines=['', '## Signal geometry and statistic summaries', '',
        '| Scenario | peak | weighted energy norm | rho | min white eigenvalue | method | T median | critical median |',
        '|---|---:|---:|---:|---:|---|---:|---:|']
    for entry in plan['scenarios']:
        d=diagnostics(entry['scenario'])
        matches=[r for r in records if r['scenario_id']==entry['scenario_id']]
        for method in ('ours','xue_s5','xue_s11','xue_s21'):
            item=dict(scenario_id=entry['scenario_id'],spec_id=entry['scenario']['spec_id'],tau=entry['scenario']['tau'],method=method,
                time_peak_effect=d['time_peak_effect'],weighted_frobenius_effect=d['weighted_frobenius_effect'],
                rho=d['rho'],minimum_whitened_eigenvalue=d['minimum_whitened_eigenvalue'],signal_cov_shape_frobenius=d['signal_cov_shape_frobenius'])
            for key in ('statistic','critical_value'):
                values=[r['methods'][method].get(key) for r in matches if r['methods'][method]['status']=='ok']
                values=[v for v in values if isinstance(v,(float,int)) and math.isfinite(v)]
                for label,fun in [('median',np.median),('mean',np.mean),('min',min),('max',max)]:
                    item[key+'_'+label]=float(fun(values)) if values else None
            rows.append(item)
            lines.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (entry['scenario_id'],d['time_peak_effect'],d['weighted_frobenius_effect'],d['rho'],d['minimum_whitened_eigenvalue'],method,item['statistic_median'],item['critical_value_median']))
    _write_csv(Path(root)/(plan['phase']+'_diagnostic_summary.csv'),rows)
    lines += ['', 'Energy is a grid-weighted Frobenius norm; two peaks increase energy by sqrt(2) at equal tau. It is not equal energy to the single peak.',
        'Independent confirmation is required to separate high point-estimate power and closeness from formal noninferiority or advantage.']
    return '\n'.join(lines)+'\n'

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('init','smoke','benchmark','plan-workers','worker','collect','decision','lock','report','status'))
    parser.add_argument('--output',type=Path,default=Path('results/task4_fixed_methods_v1'))
    parser.add_argument('--phase',choices=('pilot','fallback','confirm','smoke'),default='pilot')
    parser.add_argument('--chunk-id',type=int,default=0)
    parser.add_argument('--chunk-size',type=int)
    parser.add_argument('--seconds-per-chunk',type=int,default=1800)
    parser.add_argument('--small',action='store_true')
    parser.add_argument('--retry-failures',action='store_true')
    args=parser.parse_args(argv)
    actions={'init':lambda:initialize(args.output),'smoke':lambda:run_smoke(args.output),
        'benchmark':lambda:benchmark(args.output,args.small),
        'plan-workers':lambda:plan_workers(args.output,args.phase,args.seconds_per_chunk),
        'worker':lambda:run_worker(args.output,args.phase,args.chunk_id,args.chunk_size,args.retry_failures),
        'collect':lambda:collect(args.output,args.phase),'decision':lambda:decide(args.output),
        'lock':lambda:decide(args.output),'report':lambda:write_report(args.output),
        'status':lambda:{p:json.loads(f.read_text(encoding='utf-8')) for p in ('pilot','fallback','confirm','smoke')
                         for f in [args.output/(p+'_integrity.json')] if f.exists()}}
    result=actions[args.command]()
    print(json.dumps(io.plain(result),ensure_ascii=True))
    if args.command=='collect' and not result['complete']: raise SystemExit(2)
    return result


if __name__=='__main__': main()
