"""Unified Task5 workflow; frozen scientific calls, sealed records and finite plans."""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
from common.statistic_calculator_517 import covariance_one_sample
from common.xue_helper import run_xue_one_sample
from simulation import task3_io as io
from simulation.task3_experiments import method_config, seal_plan


def data_phase(phase, scenario):
    return ('confirm_h1' if scenario['tau'] else 'confirm_h0') if phase == 'confirm' else phase


def source_manifest():
    root = Path(__file__).resolve().parents[1]
    paths = list((root/'common').rglob('*.py')) + list((root/'simulation').glob('*.py'))
    paths += list((root/'simulation/configs/task5').glob('*.json'))
    paths += [p for p in (root/'cluster/task5').glob('*') if p.suffix in ('.py','.sh','.slurm')]
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(paths))}


def create_plan(phase='pilot'):
    from simulation.task5_design import pilot_entries
    from simulation.task5_generators import spec_ids, make_scenario
    if phase not in ('pilot','smoke'):
        raise ValueError('initial plan phase must be pilot or smoke')
    entries = pilot_entries()
    if phase == 'smoke':
        entries = []
        for spec in spec_ids():
            scenario=make_scenario(spec,.30,n=12,p=4)
            entries.append(dict(scenario=scenario,scenario_id=io.digest(scenario)[:20],repeats=1,role='smoke'))
    sources=source_manifest()
    return seal_plan(dict(study='task5_unified_v1',phase=phase,B=3 if phase=='smoke' else 500,
        alpha=.05,methods=method_config(),scenarios=entries,
        implementation_hash=io.digest(sources),source_manifest=sources))


def save_plan(root,plan):
    io.write_sealed(Path(root)/(plan['phase']+'_plan.json'),plan)


def load_plan(root,phase,check_sources=True):
    plan=io.read_sealed(Path(root)/(phase+'_plan.json'))
    if plan['study']!='task5_unified_v1' or seal_plan(plan)['run_id']!=plan['run_id']:
        raise ValueError('task5 plan identity mismatch')
    if plan['methods']!=method_config() or plan['alpha']!=.05 or plan['B']!=(3 if phase=='smoke' else 500):
        raise ValueError('frozen method configuration mismatch')
    if check_sources and io.digest(source_manifest())!=plan['implementation_hash']:
        raise ValueError('source/configuration hashes changed')
    return plan


def save_diagnostics(root,plan):
    from simulation.task5_generators import diagnostics
    from simulation.task3_summary import _write_csv
    rows=[]
    for e in plan['scenarios']:
        io.write_sealed(Path(root)/'normalization_and_projection_diagnostics'/(e['scenario_id']+'.json'),diagnostics(e['scenario']))
        rows.append(dict(phase=plan['phase'],scenario_id=e['scenario_id'],repeats=e['repeats'],role=e['role'],
            **{k:e['scenario'].get(k) for k in ('spec_id','n','p','M','tau','null_group_id','sigma_noise')}))
    _write_csv(Path(root)/(plan['phase']+'_scenario_catalog.csv'),rows)
    catalog=[]
    for phase in ('pilot','confirm'):
        path=Path(root)/(phase+'_scenario_catalog.csv')
        if path.exists():
            with path.open(encoding='utf-8-sig',newline='') as f:catalog.extend(csv.DictReader(f))
    _write_csv(Path(root)/'scenario_catalog.csv',catalog or rows)


def initialize(root):
    plan=create_plan()
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
    from simulation.task5_generators import generate, rng, data_key
    expected = {'ours', 'xue_s5', 'xue_s11', 'xue_s21'}
    if len(method_order) != 4 or set(method_order) != expected:
        raise ValueError('execute each fixed method exactly once')
    start = time.perf_counter()
    try:
        generated = generate(scenario, data_phase(phase, scenario), replicate)
    except (ValueError, FloatingPointError, MemoryError, np.linalg.LinAlgError) as error:
        failed = dict(status='failed', reject=None, pvalue=None,
                      failure_reason='generation: ' + type(error).__name__ + ': ' + str(error), seconds=0.)
        return dict(study='task5_unified_v1', phase=phase, replicate=replicate, scenario=scenario,
                    scenario_id=io.digest(scenario)[:20], data_id=io.digest(data_key(scenario, data_phase(phase, scenario), replicate)),
                    data_sha256=None, gamma0_sha256=None, methods={name: dict(failed) for name in method_order},
                    truth_metadata=dict(data_key=data_key(scenario, data_phase(phase, scenario), replicate)),
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
                    rng=rng(scenario, data_phase(phase, scenario), replicate, 'bootstrap'), grid=grid,
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
    return io.plain(dict(study='task5_unified_v1', phase=phase, replicate=replicate,
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
    from simulation.task5_generators import data_key
    sealed = dict(record)
    checksum = sealed.pop('record_sha256', None)
    expected_id = io.digest(data_key(entry['scenario'], data_phase(plan['phase'], entry['scenario']), replicate))
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
        environment_path=Path(root)/'runtime_environment.json'
        if environment_path.exists():
            if io.read_sealed(environment_path)['fingerprint']!=fingerprint:
                raise ValueError('scientific runtime environment differs')
        else:
            io.write_sealed(environment_path,dict(fingerprint=fingerprint,details=current_environment))
        io.write_sealed(Path(root)/'environment_observations'/(io.digest(current_environment)+'.json'),
                        dict(fingerprint=fingerprint,details=current_environment))
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


def collect(root, phase):
    from simulation.task5_summary import export
    root = Path(root)
    plan = load_plan(root, phase)
    records, failures, expected, seen = [], [], set(), set()
    env_path = root/'runtime_environment.json'
    fingerprint = io.read_sealed(env_path)['fingerprint'] if env_path.exists() else None
    for entry, replicate in tasks_for(plan):
        path = record_path(root, phase, entry, replicate)
        expected.add(path.name)
        if not path.exists():
            failures.append(dict(scenario_id=entry['scenario_id'], replicate=replicate, reason='missing'))
            continue
        try:
            record = validate_record(json.loads(path.read_text(encoding='utf-8')), plan, entry, replicate)
            if fingerprint is None or record.get('environment_hash') != fingerprint:
                raise ValueError('runtime environment mismatch')
            if record['data_id'] in seen:
                raise ValueError('duplicate data_id')
            seen.add(record['data_id'])
            records.append(record)
            if not record['complete']:
                failures.append(dict(scenario_id=entry['scenario_id'],replicate=replicate,reason='method_failure'))
        except (ValueError, KeyError, TypeError) as error:
            failures.append(dict(scenario_id=entry['scenario_id'],replicate=replicate,reason=str(error)))
    for path in (root/phase/'replicates').glob('*.json'):
        if path.name not in expected:
            failures.append(dict(scenario_id=path.stem,reason='unexpected_record'))
    integrity = dict(phase=phase, run_id=plan['run_id'], requested=len(tasks_for(plan)),completed=len(records),
                     complete=not failures and len(records)==len(tasks_for(plan)),failures=failures)
    directory=root/'integrity_and_failures'
    directory.mkdir(exist_ok=True)
    io.atomic_json(directory/(phase+'_integrity.json'),integrity)
    io.atomic_json(root/(phase+'_integrity.json'),integrity)
    export(root,plan,records,failures)
    write_report(root)
    return integrity


def decide(root):
    from simulation.task5_design import select_extension, lock_spec
    from simulation.task5_summary import summarize
    from simulation.task3_summary import _write_csv
    root=Path(root)
    plan=load_plan(root,'pilot')
    final=root/'search_decision.json'
    if final.exists():
        decision=io.read_sealed(final)
        locked=load_plan(root,'confirm')
        if locked['pilot_run_id']!=plan['run_id'] or decision['confirm_run_id']!=locked['run_id']:
            raise ValueError('locked decision provenance mismatch')
        return decision
    if not collect(root,'pilot')['complete']:
        raise ValueError('pilot incomplete; extension selection prohibited')
    records=[json.loads(record_path(root,'pilot',e,r).read_text(encoding='utf-8')) for e,r in tasks_for(plan)]
    selection=select_extension(summarize(plan,records)['summary'])
    locked=lock_spec(selection,plan['implementation_hash'],method_config())
    locked.update(pilot_run_id=plan['run_id'],source_manifest=plan['source_manifest'])
    locked=seal_plan(locked)
    # Write the scientific lock before the decision; a crash can only replay the
    # same deterministic selection and immutable bytes, never resample a model.
    io.write_sealed(root/'confirm_locked.json',locked)
    save_plan(root,locked)
    save_diagnostics(root,locked)
    _write_csv(root/'extension_selection.csv',selection['ranking'])
    decision=dict(action='confirm',selection=selection,pilot_run_id=plan['run_id'],
                  confirm_run_id=locked['run_id'],implementation_hash=plan['implementation_hash'])
    io.write_sealed(final,decision)
    write_report(root)
    return decision


def benchmark_one(root, n, p, replicate, small=False):
    from simulation.task5_generators import make_scenario
    if not small and not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('production benchmark requires a Slurm allocation')
    root=Path(root)
    path=root/'benchmark'/('%s_n%s_p%s_r%s.json' % ('small' if small else 'production',n,p,replicate))
    implementation=io.digest(source_manifest())
    environment=io.environment()
    fingerprint=io.digest({k:v for k,v in environment.items() if k not in ('executable','platform')})
    if path.exists():
        value=io.read_sealed(path)
        if value['implementation_hash']!=implementation or value.get('environment_hash')!=fingerprint:
            raise ValueError('benchmark source/environment mismatch')
        return value
    scenario=make_scenario('coherent_all',.30,n=n,p=p)
    record=run_replicate(scenario,'small_benchmark' if small else 'benchmark',replicate,B=3 if small else 500)
    if not record['complete']:
        raise ValueError('benchmark method failure: '+repr(record['methods']))
    value=dict(n=n,p=p,M=64,B=3 if small else 500,replicate=replicate,small=small,
               implementation_hash=implementation,seconds=record['seconds'],peak_memory_mb=peak_memory_mb(),
               method_seconds={k:v['seconds'] for k,v in record['methods'].items()},
               data_id=record['data_id'],data_sha256=record['data_sha256'],environment=environment,
               environment_hash=fingerprint)
    io.write_sealed(path,value)
    return value


def benchmark(root, small=False):
    if not small and not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('production benchmark requires a Slurm allocation')
    root=Path(root)
    path=root/'benchmark'/('small.json' if small else 'production.json')
    implementation=io.digest(source_manifest())
    environment=io.environment()
    fingerprint=io.digest({k:v for k,v in environment.items() if k not in ('executable','platform')})
    if path.exists():
        value=io.read_sealed(path)
        if (value['implementation_hash']!=implementation or value['small']!=small
                or value.get('environment_hash')!=fingerprint):
            raise ValueError('benchmark source/configuration/environment mismatch')
        return value
    measurements=[]
    shapes=[(12,4)] if small else [(200,20),(400,20),(800,20),(800,50)]
    # A fresh process for each replicate measures its own peak RSS, not the
    # monotonically increasing peak of preceding shapes. Completed parts persist.
    for n,p in shapes:
        for replicate in range(2):
            argv=[sys.executable,'-B','-m','simulation.task5_experiments','benchmark-one',
                  '--root',str(root.resolve()),'--n',str(n),'--p',str(p),'--replicate',str(replicate)]
            if small:
                argv.append('--small')
            result=subprocess.run(argv,text=True,capture_output=True,cwd=Path(__file__).resolve().parents[1])
            if result.returncode:
                raise RuntimeError('benchmark failed: '+result.stdout+'\n'+result.stderr)
            part=root/'benchmark'/('%s_n%s_p%s_r%s.json' % ('small' if small else 'production',n,p,replicate))
            measurements.append(io.read_sealed(part))
    if any(row['environment_hash']!=fingerprint for row in measurements):
        raise ValueError('benchmark subprocess environment mismatch')
    value=dict(small=small,implementation_hash=implementation,environment_hash=fingerprint,measurements=measurements,
               assumptions='Two B500 replicates per actual shape; per-shape maximum with 2x scheduling safety factor; family variation and queue time remain uncertain.')
    if not small:
        from simulation.task5_design import pilot_entries, confirmation_entries
        timings={(n,p):max(x['seconds'] for x in measurements if (x['n'],x['p'])==(n,p)) for n,p in shapes}
        def hours(entries):
            return sum(e['repeats']*timings[e['scenario']['n'],e['scenario']['p']] for e in entries)/3600
        anchors=confirmation_entries(dict(selected_model=None))
        extension=confirmation_entries(dict(selected_model='coherent_all'))
        value['worker_hours_estimate']=dict(pilot=hours(pilot_entries()),anchor=hours(anchors),
            optional_extension=hours(extension)-hours(anchors))
        value['scheduling_safety_factor']=2
    io.write_sealed(path,value)
    return value


def run_smoke(root):
    plan=create_plan('smoke')
    save_plan(root,plan)
    save_diagnostics(root,plan)
    for i,_ in enumerate(tasks_for(plan)):
        run_worker(root,'smoke',i,1)
        run_worker(root,'smoke',i,1)
    result=collect(root,'smoke')
    if not result['complete']:
        raise ValueError('smoke incomplete')
    return result


def write_report(root):
    from simulation.task3_summary import _write_csv
    from simulation.task5_summary import figures, findings
    root=Path(root)
    lines=['# Task5 unified study','',
        'Pilot and confirmation are independent; legacy/task3/task4 data are excluded.',
        'Fixed B500, alpha=.05, all channel pairs and double-time coordinates. Smoke B3 is workflow validation only.',
        'Level band [.03,.07]: point estimates for pilot; two-sided exact 95% intervals for confirmation.',
        'Each level interval is pointwise, not a simultaneous or combined calibration/power guarantee.',
        'Paired intervals use Bonferroni over every locked H1 pair, including comparisons with calibration warnings.',
        'Near-nominal/nominal rejection-probability differences are distinct; unresolved is not a technical failure.','']
    all_pairs,all_runtime=[],[]
    for phase in ('smoke','pilot','confirm'):
        integrity_path=root/(phase+'_integrity.json')
        if not integrity_path.exists():
            continue
        integrity=json.loads(integrity_path.read_text(encoding='utf-8'))
        lines+=['## '+phase,'','Complete: %s; completed %s / planned %s.' % (
            integrity['complete'],integrity['completed'],integrity['requested']),'']
        rows=[]
        for suffix,target in [('summary',rows),('paired_comparisons',all_pairs),('runtime_summary',all_runtime)]:
            with (root/(phase+'_'+suffix+'.csv')).open(encoding='utf-8-sig',newline='') as f:
                target.extend(csv.DictReader(f))
        lines+=['| Model | n | p | tau | Method | Reject / valid | Rate | 95% interval | Level status |',
                '|---|---:|---:|---:|---|---:|---:|---|---|']
        numeric=[]
        for row in rows:
            lines.append('| %s | %s | %s | %s | %s | %s / %s | %s | [%s, %s] | %s |' % tuple(
                row[k] for k in ('spec_id','n','p','tau','method','rejections','valid','rate','ci_low','ci_high','level_status')))
            if integrity['complete']:
                converted=dict(row)
                for k in ('n','p'):converted[k]=int(row[k])
                for k in ('tau','rate','ci_low','ci_high'):converted[k]=float(row[k])
                numeric.append(converted)
        if integrity['complete']:
            lines.append(findings(phase,numeric))
            figures(root,phase,numeric)
    _write_csv(root/'paired_comparisons.csv',all_pairs)
    _write_csv(root/'runtime_summary.csv',all_runtime)
    if all_pairs:
        lines+=['','## All fixed paired comparisons','',
            '| Phase | Model | n | p | tau | Comparator | Difference | Adjusted interval | Ours / comparator level | Label | Interpretation |',
            '|---|---|---:|---:|---:|---|---:|---|---|---|---|']
        for pair in all_pairs:
            lines.append('| %s | %s | %s | %s | %s | %s | %s | [%s, %s] | %s / %s | %s | %s |' % tuple(
                pair[k] for k in ('phase','spec_id','n','p','tau','comparator','difference',
                    'adjusted_ci_low','adjusted_ci_high','ours_level_status','comparator_level_status','label','interpretation')))
    path=root/'search_decision.json'
    if path.exists():
        decision=io.read_sealed(path)
        lines+=['','## Locked selection','',
                'Extension model: '+str(decision['selection']['selected_model'])+'. All three mandatory anchors retained.']
    lines+=['','## Evidence limits','',
        'M1 s5 omits the fifth latent basis; s11/s21 cover it. s21 covers q20 latent Fourier signals, but not rank63 Brownian or all measurement noise.',
        'Coherent/local share the same flat H0 only within the same shape and phase; repeated references are not independent H0 evidence.',
        'Only complete independent confirmation supports confirmatory rejection-probability labels. Calibration warnings restrict interpretation, not locked computation.',
        'Without full confirmation, whether the research target is met remains unresolved; all failures and unfinished cells are retained.']
    (root/'TASK5_RESULTS_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return dict(report=str(root/'TASK5_RESULTS_REPORT.md'))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('init','smoke','worker','collect','decide','benchmark','benchmark-one','report'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--phase',default='pilot',choices=('smoke','pilot','confirm'))
    parser.add_argument('--chunk-id',type=int,default=0)
    parser.add_argument('--chunk-size',type=int,default=1)
    parser.add_argument('--retry-failures',action='store_true')
    parser.add_argument('--small',action='store_true')
    parser.add_argument('--n',type=int,default=200)
    parser.add_argument('--p',type=int,default=20)
    parser.add_argument('--replicate',type=int,default=0)
    args=parser.parse_args(argv)
    actions={'init':lambda:initialize(args.root),'smoke':lambda:run_smoke(args.root),
        'worker':lambda:run_worker(args.root,args.phase,args.chunk_id,args.chunk_size,args.retry_failures),
        'collect':lambda:collect(args.root,args.phase),'decide':lambda:decide(args.root),
        'benchmark':lambda:benchmark(args.root,args.small),
        'benchmark-one':lambda:benchmark_one(args.root,args.n,args.p,args.replicate,args.small),
        'report':lambda:write_report(args.root)}
    print(json.dumps(io.plain(actions[args.action]()),ensure_ascii=True))


if __name__=='__main__':
    main()


