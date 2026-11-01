"""Versioned task-card-1 experiments, using the shared v1.1 numerical core."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import time

import numpy as np
import pandas as pd

from common.statistic_calculator_517 import covariance_one_sample, covariance_two_sample
from common.xue_helper import run_xue_cross_test, run_xue_one_sample
from common.statistic_calculator_xue import xue_one_sample
from simulation.data_generation import make_rng, sample_curves, simulate_one, sparse_correlation


def load_config(profile):
    path = Path(profile)
    if not path.is_file():
        path = Path(__file__).with_name('configs') / (profile + '.json')
    return json.loads(path.read_text(encoding='utf-8'))


def canonical(task):
    return json.dumps(task, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False)


def scenario_id(task):
    return hashlib.sha256(canonical(task).encode('utf-8')).hexdigest()[:16]


def normalize_task(task, model=None):
    """Convert historical task field names once at the entry boundary."""
    normalized = dict(task)
    h0 = normalized.get('h0', normalized.get('s0', 0) == 0)
    normalized.setdefault('model', model)
    normalized.setdefault('s0', 0 if h0 else 4)
    normalized.setdefault('delta', 0.0 if h0 else normalized.get('signal_strength', .215))
    normalized.setdefault('h0', h0)
    normalized.setdefault('signal_strength', normalized['delta'])
    defaults = dict(grid='closed_0_1', basis='phi_1_to_phi_5', q=5, c=1.0,
                    beta=2.0, support_policy='redraw_each_replicate_allow_shared_vertices',
                    test_kind='one_sample', test_scope='cross', alpha=.05,
                    method_version='v1.1', with_xue=False,
                    xue_basis='phi_0_to_phi_4', xue_s=5,
                    xue_version='existing_legacy_not_audited_in_task1')
    for key, value in defaults.items():
        normalized.setdefault(key, value)
    if normalized['model'] not in ('M1', 'M2'):
        raise ValueError('task model must be M1 or M2')
    if normalized['test_scope'] != 'cross' or normalized['method_version'] != 'v1.1':
        raise ValueError('these simulations implement v1.1 cross-channel tests')
    if bool(normalized['h0']) != (normalized['s0'] == 0) or normalized['delta'] != normalized['signal_strength']:
        raise ValueError('inconsistent h0/s0/delta/signal_strength configuration')
    if normalized['with_xue'] and normalized['test_kind'] != 'one_sample':
        raise ValueError('the retained Xue comparator is single-sample only')
    for key in ('B', 'n_repeats'):
        if not isinstance(normalized[key], int) or normalized[key] < 1:
            raise ValueError(key + ' must be a positive integer')
    return normalized


def run_replicate(task, replicate):
    start = time.perf_counter()
    p = task['p']
    pairs = ~np.eye(p, dtype=bool)
    identifier = scenario_id(task)
    if task['test_kind'] == 'one_sample':
        data = simulate_one(task, replicate)
        generated = time.perf_counter()
        result = covariance_one_sample(
            data['Y'], np.zeros((p, p, task['M'], task['M'])),
            channel_pairs=pairs, B=task['B'], alpha=task['alpha'],
            seed=make_rng(task, replicate, 'bootstrap'), grid=data['grid'],
            config_id=identifier)
    elif task['test_kind'] == 'independent_two_sample':
        C, edges = sparse_correlation(p, task['s0'], task['delta'],
                                     make_rng(task, replicate, 'support', 'Y'))
        X, grid, K = sample_curves(task, replicate, task['n_X'], np.eye(p), 'X')
        Y, grid_y, _ = sample_curves(task, replicate, task['n_Y'], C, 'Y')
        data = dict(C=C, edges_zero_based=edges, grid=grid, latent_time_kernel=K)
        generated = time.perf_counter()
        xi = make_rng(task, replicate, 'bootstrap', 'X').standard_normal((task['B'], task['n_X']))
        eta = make_rng(task, replicate, 'bootstrap', 'Y').standard_normal((task['B'], task['n_Y']))
        result = covariance_two_sample(
            X, Y, channel_pairs=pairs, B=task['B'], alpha=task['alpha'],
            multipliers=(xi, eta), grid=grid, grid_y=grid_y, config_id=identifier)
    else:
        raise ValueError('unknown test_kind')
    tested = time.perf_counter()
    record = dict(task=task, replicate=replicate, scenario_id=identifier,
                  method_version='v1.1', test_kind=task['test_kind'], test_scope='cross',
                  statistic=result['statistic'], pvalue=result['pvalue'],
                  critical_value=result['critical_value'], reject=result['reject'],
                  bootstrap_statistics=result['bootstrap_statistics'].tolist(),
                  denominator=result['denominator'],
                  critical_rule='rank from (1+exceedances)/(B+1) < alpha; null means +infinity',
                  grid=data['grid'].tolist(), C=data['C'].tolist(),
                  edges_zero_based=data['edges_zero_based'],
                  min_eigenvalue=float(np.linalg.eigvalsh(data['C'])[0]),
                  noise_variance=task['sigma_noise'] ** 2,
                  base_seed=20261021,
                  seed_rule='canonical JSON SHA256 first8 little-endian + base + replicate*13579 mod 2^64; SeedSequence stream/group IDs',
                  numpy_version=np.__version__, python_version=platform.python_version(),
                  platform=platform.platform(), cpu_count=os.cpu_count(),
                  thread_environment={k: os.environ.get(k) for k in
                                      ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS')},
                  generation_seconds=generated-start, test_seconds=tested-generated,
                  failure=False)
    if task['with_xue']:
        x0 = time.perf_counter()
        xue = run_xue_cross_test(data['Y'], s=task['xue_s'], alpha=task['alpha'])
        require_xue_success(xue)
        record['xue'] = compact_xue_result(xue)
        record['xue'].update(seconds=time.perf_counter()-x0,
                             version='xue-audit-v1', implementation_version='xue-audit-v1',
                             basis=task['xue_basis'])
    if not np.isfinite(record['critical_value']):
        record['critical_value'] = None
    return record


def summarize(task, records):
    rate = float(np.mean([r['reject'] for r in records]))
    result = dict(experiment=task['experiment'], model=task['model'],
                  n=task['n'], p=task['p'], M=task['M'], s0=task['s0'],
                  signal_strength=task['delta'], reject_rate=rate, power=rate,
                  mcse=float(np.sqrt(rate*(1-rate)/len(records))),
                  n_repeats=len(records), B=task['B'], method_version='v1.1',
                  scenario_id=scenario_id(task), configuration=canonical(task),
                  time_ours=sum(r['test_seconds'] for r in records))
    if task['test_kind'] == 'independent_two_sample':
        result.update(n_X=task['n_X'], n_Y=task['n_Y'])
    if task['with_xue']:
        for record in records:
            require_xue_success(record['xue'])
        xrate = float(np.mean([r['xue']['reject'] for r in records]))
        result.update(reject_rate_xue=xrate, power_xue=xrate,
                      time_xue=sum(r['xue']['seconds'] for r in records),
                      xue_method='Xue-1S-EV-cross-zero', xue_version='xue-audit-v1',
                      n_valid_xue=len(records), n_failed_xue=0, n_common_valid=len(records),
                      n_requested=task['n_repeats'], n_completed=len(records))
    return result


def execute_single_task(task, model=None):
    task = normalize_task(task, model)
    return summarize(task, [run_replicate(task, r) for r in range(task['n_repeats'])])


def save_partial_results(results, experiment_num, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([r for r in results if r['experiment'] == experiment_num]).to_csv(
        output / f'experiment{experiment_num}_partial.csv', index=False)


def validate_checkpoint(record, task, path):
    """Reject incomplete or inconsistent inference rather than repairing it."""
    try:
        boot = np.asarray(record['bootstrap_statistics'], dtype=float)
        statistic = float(record['statistic'])
        pvalue = (1 + np.count_nonzero(boot >= statistic)) / (task['B'] + 1)
        allowed = np.arange(task['B'] + 1)
        allowed = allowed[(1 + allowed) / (task['B'] + 1) < task['alpha']]
        rank = task['B'] - int(allowed[-1]) if allowed.size else task['B'] + 1
        critical = float(np.sort(boot)[rank-1]) if rank <= task['B'] else None
        valid = (boot.shape == (task['B'],) and np.isfinite(boot).all()
                 and np.isfinite(statistic) and record['pvalue'] == pvalue
                 and record['reject'] == (pvalue < task['alpha'])
                 and record['critical_value'] == critical
                 and record['test_kind'] == task['test_kind']
                 and record['scenario_id'] == scenario_id(task)
                 and np.isfinite(record['test_seconds'])
                 and np.isfinite(record['generation_seconds']))
        if task['with_xue']:
            valid = (valid and np.isfinite(record['xue']['seconds'])
                     and record['xue'].get('method') == 'Xue-1S-EV-cross-zero'
                     and record['xue'].get('implementation_version') == 'xue-audit-v1'
                     and record['xue'].get('status') == 'ok'
                     and 0 <= record['xue']['pvalue'] <= 1)
        if not valid:
            raise ValueError('inconsistent checkpoint values')
    except (KeyError, TypeError, ValueError, IndexError) as error:
        raise ValueError(f'invalid checkpoint: {path}') from error


def run_tasks(tasks, output, resume=False):
    tasks = [normalize_task(t) for t in tasks]
    if not tasks:
        raise ValueError('tasks must be non-empty')
    output = Path(output)
    summaries = []
    for task in tasks:
        folder = output / scenario_id(task)
        folder.mkdir(parents=True, exist_ok=True)
        records = []
        for replicate in range(task['n_repeats']):
            path = folder / f'replicate_{replicate:03d}.json'
            if path.exists() and not resume:
                raise FileExistsError(f'{path} exists; use --resume or a new output directory')
            if path.exists():
                record = json.loads(path.read_text(encoding='utf-8'))
                if (record.get('task') != task or record.get('replicate') != replicate
                        or record.get('method_version') != 'v1.1'
                        or record.get('failure') is not False
                        or len(record.get('bootstrap_statistics', [])) != task['B']):
                    raise ValueError(f'invalid checkpoint: {path}')
                validate_checkpoint(record, task, path)
            else:
                try:
                    record = run_replicate(task, replicate)
                except Exception as error:
                    (folder / f'failure_{replicate:03d}.json').write_text(
                        json.dumps(dict(task=task, replicate=replicate, failure=True,
                                        error=repr(error), n_requested=task['n_repeats'],
                                        n_completed=replicate, n_failed=1),
                                   ensure_ascii=True, indent=2), encoding='utf-8')
                    raise
                temporary = path.with_suffix('.tmp')
                temporary.write_text(json.dumps(record, ensure_ascii=True, indent=2,
                                                allow_nan=False, default=json_value), encoding='utf-8')
                temporary.replace(path)
            records.append(record)
        summaries.append(summarize(task, records))
        save_partial_results(summaries, task['experiment'], output)
    frame = pd.DataFrame(summaries)
    frame.to_csv(output / 'all_experiments_results.csv', index=False)
    for experiment in sorted({t['experiment'] for t in tasks}):
        frame[frame['experiment'] == experiment].to_csv(
            output / f'experiment{experiment}_results.csv', index=False)
    summary = dict(all_results=frame)
    for experiment in (1, 2, 3):
        rows = [r for r in summaries if r['experiment'] == experiment]
        summary[f'experiment{experiment}_ours'] = float(np.mean([r['reject_rate'] for r in rows])) if rows else 0.0
        xrows = [r for r in rows if 'reject_rate_xue' in r]
        summary[f'experiment{experiment}_xue'] = float(np.mean([r['reject_rate_xue'] for r in xrows])) if xrows else 0.0
    return summary


def require_xue_success(result):
    if result.get('status') != 'ok':
        raise ValueError(f"{result.get('status', 'invalid_xue_result')}: {result.get('failure_reason')}")


def compact_xue_result(result):
    # Dense audit matrices remain in the numerical API. Untested q coordinates
    # are undefined; records retain the tested maximum and argmax.
    return {key: value for key, value in result.items() if key not in ('S', 'm', 'q')}


def json_value(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f'unsupported result type: {type(value).__name__}')


def run_xue_input(source, output, s=5, alpha=.05):
    """Explicit NPZ scores+sigma0 or Y+(gamma0 or sigma0), with optional L/grid.

    No target is fitted from this sample and no extra sample is generated.
    """
    source, output = Path(source), Path(output)
    path = output / 'xue_result.json'
    if path.exists():
        raise FileExistsError(f'{path} exists; choose a new output directory')
    with np.load(source, allow_pickle=False) as data:
        supplied = {key: data[key] for key in data.files}
    if ('scores' in supplied) == ('Y' in supplied):
        raise ValueError('input must contain exactly one of scores or Y')
    if ('sigma0' in supplied) == ('gamma0' in supplied):
        raise ValueError('input must contain exactly one known target: sigma0 or gamma0')
    actual_s = supplied['s'].item() if 's' in supplied else s
    if 'scores' in supplied and supplied['scores'].ndim == 3 and 's' not in supplied:
        actual_s = supplied['scores'].shape[2]
    if 'scores' in supplied:
        if 'sigma0' not in supplied:
            raise ValueError('coefficient input requires sigma0 in the same representation')
        p = supplied['p'].item() if 'p' in supplied else None
        result = xue_one_sample(supplied['scores'], supplied['sigma0'], p=p, s=actual_s,
                                alpha=alpha, target_type='known_coefficient_covariance')
    else:
        result = run_xue_one_sample(supplied['Y'], gamma0=supplied.get('gamma0'),
                                    sigma0=supplied.get('sigma0'), s=actual_s, alpha=alpha,
                                    operator=supplied.get('operator'), grid=supplied.get('grid'))
    record = compact_xue_result(result)
    if 'Y' in supplied and 'gamma0' in supplied and result['status'] == 'ok':
        # Both methods receive the same explicitly supplied full target and Y.
        B = supplied['B'].item() if 'B' in supplied else 500
        seed = supplied['bootstrap_seed'].item() if 'bootstrap_seed' in supplied else 20261021
        ours = covariance_one_sample(supplied['Y'], supplied['gamma0'], B=B, seed=seed,
                                     alpha=alpha, grid=supplied.get('grid'))
        ours.update(test_scope='all', target_source='same_explicit_grid_target',
                    bootstrap_seed=seed)
        if not np.isfinite(ours['critical_value']):
            ours['critical_value'] = None
        record['ours'] = ours
    record.update(input_path=str(source.resolve()),
                  input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  implementation_version='xue-audit-v1', numpy_version=np.__version__,
                  target_source='explicit_known_target_in_input_file')
    output.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(record, default=json_value, ensure_ascii=True,
                                    allow_nan=False, indent=2), encoding='utf-8')
    temporary.replace(path)
    valid = record['status'] == 'ok'
    pd.DataFrame([dict(method=record['method'], status=record['status'],
                       n_total=1, n_valid=int(valid), n_failed=int(not valid),
                       reject=record.get('reject'), p_value=record.get('p_value'),
                       Q=record.get('Q'), T=record.get('T'))]).to_csv(output / 'xue_summary.csv', index=False)
    require_xue_success(record)
    return record


def main(argv=None, model=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('formal', 'smoke', 'two_sample_smoke'), default='smoke')
    parser.add_argument('--config', type=Path)
    parser.add_argument('--model', choices=('M1', 'M2'), default=model)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--with-xue', action='store_true', help='audited cross-zero EV variant, preserving the configured cross null')
    parser.add_argument('--xue-input', type=Path, help='NPZ observations with an explicit known target; complete Xue-1S-EV')
    parser.add_argument('--xue-s', type=int, default=5)
    parser.add_argument('--alpha', type=float, default=.05, help='nominal level for explicit Xue input')
    args = parser.parse_args(argv)
    if args.xue_input is not None:
        output = args.output or Path(__file__).resolve().parents[1] / 'results' / 'xue_audit_v1_20261021' / args.xue_input.stem
        result = run_xue_input(args.xue_input, output, s=args.xue_s, alpha=args.alpha)
        print(f'{result["method"]}: {result["status"]}; results: {output}')
        return result
    config = load_config(str(args.config) if args.config else args.profile)
    tasks = [t for t in config['tasks'] if args.model is None or t['model'] == args.model]
    if args.with_xue:
        tasks = [dict(t, with_xue=True) for t in tasks]
    root = 'xue_audit_v1_20261021' if any(t['with_xue'] for t in tasks) else 'validation_v1.1_20261021'
    default_output = Path(__file__).resolve().parents[1] / 'results' / root / args.profile
    if args.model is not None:
        default_output /= args.model
    if args.with_xue:
        default_output /= 'with_xue'
    output = args.output or default_output
    result = run_tasks(tasks, output, resume=args.resume)
    print(f'Completed {len(result["all_results"])} scenarios; results: {output}')
    return result


if __name__ == '__main__':
    main()
