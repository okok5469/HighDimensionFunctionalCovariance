"""Exact Monte Carlo uncertainty, frozen selection, and task3 result exports.

All rates with failures are explicitly valid-subset estimates.  Planned,
completed, valid, failed and missing counts remain separate.  Formal labels
require every planned comparison to finish and matched null calibration.
"""
import csv
from pathlib import Path

import numpy as np
from scipy.stats import beta


def _methods():
    return ('ours', 'xue_s5', 'xue_s11', 'xue_s21')


def _cp(successes, total, confidence):
    if total == 0:
        return None, None
    tail = (1 - confidence) / 2
    lower = 0. if successes == 0 else float(beta.ppf(tail, successes, total-successes+1))
    upper = 1. if successes == total else float(beta.ppf(1-tail, successes+1, total-successes))
    return lower, upper


def _indicators(values):
    result = list(values)
    if any(x is not None and not isinstance(x, (bool, np.bool_)) for x in result):
        raise ValueError('rejection indicators must be boolean or None')
    return result


def binomial_summary(rejects, requested, confidence=.95):
    """Clopper-Pearson interval on valid observations; retain every denominator."""
    values = _indicators(rejects)
    if not isinstance(requested, int) or requested < len(values) or not 0 < confidence < 1:
        raise ValueError('invalid requested count or confidence')
    valid = [bool(x) for x in values if x is not None]
    total, successes = len(valid), sum(valid)
    rate = successes / total if total else None
    low, high = _cp(successes, total, confidence)
    upper = None if total == 0 else (1. if successes == total else
                                    float(beta.ppf(.95, successes+1, total-successes)))
    return dict(planned=requested, completed=len(values), valid=total,
                failed=len(values)-total, missing=requested-len(values), rejections=successes,
                rate=rate, mcse=None if rate is None else float(np.sqrt(rate*(1-rate)/total)),
                ci_low=low, ci_high=high, confidence=confidence,
                interval_method='Clopper-Pearson', upper_one_sided_95=upper,
                calibration_upper_pass=upper is not None and upper <= .08,
                conservative=high is not None and high < .05,
                complete=total == requested, denominator='valid_subset')


def paired_summary(a, b, confidence=.95):
    """Conservative paired difference via Bonferroni discordant-probability CIs."""
    a, b = _indicators(a), _indicators(b)
    if len(a) != len(b) or not 0 < confidence < 1:
        raise ValueError('paired observations must have equal length and valid confidence')
    pairs = [(bool(x), bool(y)) for x, y in zip(a, b) if x is not None and y is not None]
    count = len(pairs)
    cells = [sum(x == i and y == j for x, y in pairs) for i, j in
             ((True, True), (True, False), (False, True), (False, False))]
    diff = np.asarray([int(x)-int(y) for x, y in pairs], dtype=float)
    low_a, high_a = _cp(cells[1], count, 1-(1-confidence)/2)
    low_b, high_b = _cp(cells[2], count, 1-(1-confidence)/2)
    return dict(common_valid=count, paired_completed=len(a), both_reject=cells[0],
                only_a=cells[1], only_b=cells[2], neither=cells[3],
                difference=float(diff.mean()) if count else None,
                mcse=float(diff.std(ddof=1)/np.sqrt(count)) if count > 1 else None,
                ci_low=low_a-high_b if count else None,
                ci_high=high_a-low_b if count else None, confidence=confidence,
                interval_method='paired_Bonferroni_Clopper-Pearson')


def _metadata(item):
    scenario = item['scenario']
    return {name: scenario.get(name) for name in
            ('spec_id', 'family', 'tau', 'n', 'p', 'M', 'null_group_id')}


def _valid_indicator(record, method):
    result = record.get('methods', {}).get(method, {})
    indicator = result.get('reject')
    return bool(indicator) if result.get('status') == 'ok' and isinstance(indicator, (bool, np.bool_)) else None


def _null_key(row):
    return row.get('null_group_id'), row.get('n'), row.get('p'), row.get('method')


def _label(pair, calibrated, complete):
    if not complete:
        return 'incomplete'
    if not calibrated:
        return 'calibration_not_accepted'
    if pair['ci_low'] > 0:
        return 'advantage'
    if pair['ci_low'] >= -.05 and pair['ci_high'] <= .05:
        return 'approximately_equal'
    if pair['ci_low'] > -.05:
        return 'noninferior'
    return 'insufficient_evidence'


def summarize_records(plan, records, failures=None):
    """Summarize planned physical scenarios, without treating failed fits as zero."""
    rows, paired, runtime = [], [], []
    failure_rows = [dict(x) for x in (failures or [])]
    entries = {x['scenario_id']: x for x in plan['scenarios']}
    grouped = {key: [] for key in entries}
    seen = set()
    for record in records:
        key = record['scenario_id'], record['replicate']
        if key in seen:
            raise ValueError('duplicate scenario/replicate record: %s' % (key,))
        if key[0] not in entries or not 0 <= key[1] < entries[key[0]]['repeats']:
            raise ValueError('record is outside the locked plan')
        seen.add(key)
        grouped[key[0]].append(record)
    declarations = 3 * sum(x['scenario']['tau'] > 0 for x in entries.values())
    adjusted = 1-.05/max(1, declarations)
    for scenario_id, item in entries.items():
        observations = sorted(grouped[scenario_id], key=lambda x: x['replicate'])
        metadata = dict(_metadata(item), scenario_id=scenario_id, phase=plan['phase'],
                        run_id=plan.get('run_id', ''))
        indicators = {method: [_valid_indicator(x, method) for x in observations] for method in _methods()}
        common = [all(indicators[m][i] is not None for m in _methods()) for i in range(len(observations))]
        for method in _methods():
            summary = binomial_summary(indicators[method], item['repeats'])
            common_values = [x for x, valid in zip(indicators[method], common) if valid]
            rows.append(dict(metadata, method=method, common_valid=sum(common),
                             common_rejections=sum(common_values),
                             common_rate=sum(common_values)/sum(common) if sum(common) else None, **summary))
            seconds = [x.get('methods', {}).get(method, {}).get('seconds') for x in observations]
            seconds = [float(x) for x in seconds if x is not None and np.isfinite(x)]
            runtime.append(dict(metadata, method=method, timed=len(seconds),
                                total_seconds=sum(seconds),
                                mean_seconds=float(np.mean(seconds)) if seconds else None,
                                median_seconds=float(np.median(seconds)) if seconds else None,
                                max_seconds=max(seconds) if seconds else None))
            for record, indicator in zip(observations, indicators[method]):
                if indicator is None:
                    result = record.get('methods', {}).get(method, {})
                    failure_rows.append(dict(metadata, method=method, replicate=record['replicate'],
                                             failure_reason=result.get('failure_reason', 'invalid_or_missing_method_result')))
        missing = sorted(set(range(item['repeats']))-{x['replicate'] for x in observations})
        for replicate in missing:
            failure_rows.append(dict(metadata, method='all', replicate=replicate, failure_reason='missing_record'))
        if item['scenario']['tau'] == 0:
            continue
        for method in _methods()[1:]:
            pointwise = paired_summary(indicators['ours'], indicators[method])
            formal = paired_summary(indicators['ours'], indicators[method], adjusted)
            paired.append(dict(metadata, comparator=method, planned=item['repeats'],
                               complete=formal['common_valid'] == item['repeats'],
                               adjusted_confidence=adjusted, familywise_declarations=declarations,
                               adjusted_ci_low=formal['ci_low'], adjusted_ci_high=formal['ci_high'],
                               **pointwise))
    nulls = {_null_key(row): row for row in rows if row['tau'] == 0}
    for pair in paired:
        matched = [nulls.get((pair['null_group_id'], pair['n'], pair['p'], method))
                   for method in ('ours', pair['comparator'])]
        calibrated = all(row is not None and row['complete'] and row['calibration_upper_pass'] for row in matched)
        pair['calibration_accepted'] = calibrated
        pair['null_conservative'] = any(row is not None and row['conservative'] for row in matched)
        pair['null_rate_difference'] = abs(matched[0]['rate']-matched[1]['rate']) if all(matched) and all(x['rate'] is not None for x in matched) else None
        pair['label'] = _label(dict(ci_low=pair['adjusted_ci_low'], ci_high=pair['adjusted_ci_high']),
                               calibrated, pair['complete'] and all(x['complete'] for x in rows) and not failure_rows)
        if plan['phase'] != 'confirm':
            pair['label'] = 'exploratory_only'
    return dict(summary=rows, paired=paired, failures=failure_rows, runtime=runtime,
                complete=all(row['complete'] for row in rows) and not failure_rows)


def select_candidates(pilot_rows, policy=None):
    """Apply the task-card fixed screening and family-diverse ranking rule."""
    policy = policy or {}
    references = ['spectrum_fast_b4', 'legacy_M2_full_reference']
    expected = dict(pilot_calibration_max=.12, confirmation_calibration_upper=.08,
                    alpha=.05, confidence=.95, epsilon=.05, max_candidates=2,
                    max_specifications=4, references=references,
                    selection_score='mean_over_tau(power_ours-max_fixed_xue_power)',
                    seed_base=20261021, main_shape=[200, 20], alternative_taus=[.15, .30],
                    null_repeats=500, alternative_repeats=300,
                    dimension_shapes=[[400, 20], [200, 50]], dimension_tau=.30,
                    multiple_testing='Bonferroni_over_all_locked_alternative_pairs')
    if any(policy.get(key, value) != value for key, value in expected.items()):
        raise ValueError('task3_v1 selection thresholds are frozen')
    allowed = ('spectrum_slow_b1', 'spectrum_flat_b0', 'band_head', 'band_tail',
               'coherent_all', 'coherent_tail', 'local_fejer')
    physical = [x for x in pilot_rows if x.get('n') == 200 and x.get('p') == 20]
    nulls = {_null_key(x): x for x in physical if x['tau'] == 0}
    ranking = []
    for spec in allowed:
        alternatives = [x for x in physical if x['spec_id'] == spec and x['tau'] > 0]
        if not alternatives:
            continue
        metadata = alternatives[0]
        matched = [nulls.get((metadata['null_group_id'], 200, 20, method)) for method in _methods()]
        required = alternatives + [x for x in matched if x is not None]
        complete = len(alternatives) == 8 and all(x is not None for x in matched) and all(
            x.get('complete', False) and x.get('failed', 0) == 0 and x.get('rate') is not None for x in required)
        suspect = any(x is not None and x.get('rate') is not None and x['rate'] > .12 for x in matched)
        score = None
        if complete:
            by_key = {(x['tau'], x['method']): x['rate'] for x in alternatives}
            if set(x['tau'] for x in alternatives) != {.15, .30}:
                raise ValueError('pilot strengths must be .15 and .30')
            score = sum(by_key[(tau, 'ours')]-max(by_key[(tau, m)] for m in _methods()[1:]) for tau in (.15, .30))/2
        status = 'incomplete' if not complete else ('calibration_suspect' if suspect else 'eligible')
        ranking.append(dict(spec_id=spec, family=metadata['family'], score=score, status=status))
    ranking.sort(key=lambda x: (x['status'] != 'eligible', -(x['score'] if x['score'] is not None else -float('inf')), x['spec_id']))
    eligible = [x for x in ranking if x['status'] == 'eligible']
    chosen = eligible[:1]
    if chosen:
        remainder = [x for x in eligible[1:] if x['family'] != chosen[0]['family']] or eligible[1:]
        chosen += remainder[:1]
    selected = [x['spec_id'] for x in chosen]
    status = 'no_eligible_candidates' if not chosen else ('no_advantage_evidence' if all(x['score'] <= 0 for x in eligible) else 'exploratory_ranking_only')
    return dict(selected_candidates=selected, references=references, policy=expected,
                specifications=references+selected, ranking=ranking, status=status,
                pilot_calibration_limit=.12, noninferiority_margin=.05,
                confirm_null_upper_limit=.08, strengths=[.15, .30],
                methods=list(_methods()), multiplicity='Bonferroni_all_locked_alternative_pairs')


def confirmation_scenarios(selection, skip_dimension_extension=False):
    """Build at most 6000 physical datasets with explicitly shared nulls."""
    from simulation.task3_generators import make_scenario
    entries, seen_nulls = [], set()
    selected = selection['selected_candidates']
    if (len(selected) > 2 or len(set(selected)) != len(selected)
            or selection['references'] != ['spectrum_fast_b4', 'legacy_M2_full_reference']
            or selection['specifications'] != selection['references']+selected):
        raise ValueError('confirmation must retain the two fixed references and at most two candidates')
    shapes = [(spec, 200, 20, (.15, .30), 'reference' if spec in selection['references'] else 'candidate')
              for spec in selection['specifications']]
    if selected and not skip_dimension_extension:
        shapes += [(selected[0], n, p, (.30,), 'dimension_extension') for n, p in ((400, 20), (200, 50))]
    for spec, n, p, strengths, role in shapes:
        for tau in (0.,)+strengths:
            scenario = make_scenario(spec, tau, n=n, p=p)
            key = scenario['null_group_id'], n, p
            if tau == 0 and key in seen_nulls:
                continue
            if tau == 0:
                seen_nulls.add(key)
            entries.append(dict(scenario=scenario, repeats=500 if tau == 0 else 300, role=role))
    if len(entries) > 16 or sum(x['repeats'] for x in entries) > 6000:
        raise ValueError('confirmation exceeds predeclared budget')
    return entries


def _write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row)) or ['status']
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_reports(plan, records, output, phase=None, failures=None):
    """Export complete tables and descriptive plots for every observed scenario."""
    result = summarize_records(plan, records, failures)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    phase = phase or plan['phase']
    _write_csv(output/(phase+'_summary.csv'), result['summary'])
    for name, rows in (('paired_comparisons.csv', result['paired']),
                       ('failures.csv', result['failures']), ('runtime_summary.csv', result['runtime'])):
        _phase_csv(output, phase, name, [dict(x, phase=phase) for x in rows])
    catalog = [dict(_metadata(x), phase=phase, scenario_id=x['scenario_id'], repeats=x['repeats'], role=x.get('role', ''))
               for x in plan['scenarios']]
    _phase_csv(output, phase, 'scenario_catalog.csv', catalog)
    retention = _signal_retention(plan)
    _phase_csv(output, phase, 'signal_retention.csv', [dict(x, phase=phase) for x in retention])
    _figures(result, output/'figures', phase, retention)
    phase_report = _report(plan, result)
    (output/(phase+'_RESULTS_REPORT.md')).write_text(phase_report, encoding='utf-8')
    sections = []
    for report_phase in ('pilot', 'confirm', 'smoke', 'benchmark'):
        path = output/(report_phase+'_RESULTS_REPORT.md')
        if path.exists():
            sections.append(path.read_text(encoding='utf-8'))
    (output/'TASK3_RESULTS_REPORT.md').write_text('\n\n'.join(sections), encoding='utf-8')
    return result


def _phase_csv(output, phase, name, rows):
    """Preserve pilot evidence when independent confirmation is collected."""
    _write_csv(output/(phase+'_'+name), rows)
    combined = []
    for known_phase in ('pilot', 'confirm', 'smoke', 'benchmark'):
        path = output/(known_phase+'_'+name)
        if path.exists():
            with path.open(encoding='utf-8-sig', newline='') as stream:
                combined.extend(csv.DictReader(stream))
    _write_csv(output/name, combined)


def _report(plan, result):
    lines = ['# Task3 %s results' % plan['phase'], '',
             'Completeness: %s. All rates use the explicitly reported valid subset.' % result['complete'],
             'Missing records and failed methods remain separate from non-rejections.',
             'Null rows are physical distributions identified by null_group_id; shared nulls are reused once.',
             '95% binomial intervals: exact Clopper-Pearson. Calibration: one-sided 95% upper bound <= 0.08.',
             'This is the predeclared calibration tolerance; it does not establish exact 5% size.',
             'Formal labels use Bonferroni over all locked alternative/comparator declarations.',
             'Conservative size or appreciable null-rate differences require separate interpretation.', '']
    if plan['phase'] == 'smoke':
        lines += ['Smoke execution validates the pipeline only; it supports no scientific conclusion.', '']
    if plan['phase'] == 'benchmark':
        lines += ['Benchmark measurements assess resources only; they support no scientific conclusion.', '']
    lines += ['All physical null and alternative rows (shared nulls appear only once per method):', '',
              '| Scenario | Method | tau | n/p | Rejections | planned/completed/valid/failed/missing | Rate | MCSE | 95% CI | Common valid |',
              '|---|---|---:|---|---:|---|---:|---:|---|---:|']
    for row in result['summary']:
        counts = '/'.join(str(row[key]) for key in ('planned', 'completed', 'valid', 'failed', 'missing'))
        lines.append('| %s | %s | %s | %s/%s | %s | %s | %s | %s | [%s, %s] | %s |' %
                     (row['scenario_id'], row['method'], row['tau'], row['n'], row['p'],
                      row['rejections'], counts, row['rate'], row['mcse'], row['ci_low'],
                      row['ci_high'], row['common_valid']))
    lines += ['', 'Null calibration (one physical result per null_group_id and shape):', '',
              '| Null group | n/p | Method | Rate | One-sided 95% upper | Upper <= 0.08 | Conservative |',
              '|---|---|---|---:|---:|---|---|']
    for row in result['summary']:
        if row['tau'] == 0:
            lines.append('| %s | %s/%s | %s | %s | %s | %s | %s |' %
                         tuple(row[key] for key in ('null_group_id', 'n', 'p', 'method', 'rate',
                                                   'upper_one_sided_95', 'calibration_upper_pass', 'conservative')))
    lines += ['', 'Paired comparisons:', '',
             '| Scenario | Comparator | Difference | 95% CI | Adjusted CI | Label |',
             '|---|---|---:|---|---|---|']
    for row in result['paired']:
        lines.append('| %s | %s | %s | [%s, %s] | [%s, %s] | %s |' %
                     tuple(row[x] for x in ('scenario_id', 'comparator', 'difference', 'ci_low', 'ci_high',
                                            'adjusted_ci_low', 'adjusted_ci_high', 'label')))
    if plan['phase'] in ('smoke', 'benchmark'):
        return '\n'.join(lines+['', 'Scientific interpretation awaits complete independent confirmation.', ''])
    lines += ['', 'Interpretation by signal structure (all strengths and shapes retained):']
    grouped = {}
    for row in result['paired']:
        key = row['spec_id'], row['n'], row['p'], row['tau']
        grouped.setdefault(key, {})[row['comparator']] = row
    for key, by_method in grouped.items():
        low, full = by_method.get('xue_s5', {}), by_method.get('xue_s21', {})
        low_win, full_win = low.get('label') == 'advantage', full.get('label') == 'advantage'
        if full_win:
            new_specs = {'spectrum_fast_b4', 'spectrum_slow_b1', 'spectrum_flat_b0',
                         'band_head', 'band_tail', 'coherent_all', 'coherent_tail', 'local_fejer'}
            interpretation = ('robust advantage with s=21' if key[0] in new_specs else
                              'fixed-s21 advantage with possible truncation')
        else:
            interpretation = ('truncation-related advantage' if low_win else
                              'no established advantage; inspect noninferiority and uncertainty')
        lines.append('- %s, n=%s, p=%s, tau=%s: %s.' % (key+(interpretation,)))
    lines += ['', 'Legacy cross-zero results are outside this full-known-target report.', '']
    return '\n'.join(lines)


def _signal_retention(plan):
    from simulation.task3_generators import diagnostics
    rows = []
    for item in plan['scenarios']:
        scenario = item['scenario']
        if scenario['tau'] == 0 or 'grid' not in scenario:
            continue
        diag = diagnostics(scenario)
        for s, projection in diag['projections'].items():
            rows.append(dict(_metadata(item), scenario_id=item['scenario_id'], s=int(s),
                             reconstructed_peak_ratio=projection['reconstructed_peak_ratio'],
                             orthogonal_frobenius_ratio=projection['orthogonal_frobenius_ratio'],
                             energy_ratio=projection['energy_ratio'],
                             standardized_null_effect=projection['standardized_null_effect'],
                             coefficient_max_difference=projection['coefficient_max_difference'],
                             time_peak_effect=diag['time_peak_effect'],
                             weighted_frobenius_effect=diag['weighted_frobenius_effect']))
    return rows


def _figures(result, output, phase, retention):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    matplotlib.rcParams.update({'svg.fonttype': 'none', 'pdf.fonttype': 42,
                                 'axes.spines.right': False, 'axes.spines.top': False,
                                 'legend.frameon': False})
    colors = {'ours': '#222222', 'xue_s5': '#0072B2',
              'xue_s11': '#D55E00', 'xue_s21': '#009E73'}
    output.mkdir(parents=True, exist_ok=True)
    for tau in (0, .15, .30):
        rows = [x for x in result['summary'] if x['tau'] == tau and x['rate'] is not None]
        if not rows:
            continue
        scenarios = list(dict.fromkeys(x['scenario_id'] for x in rows))
        figure, axis = plt.subplots(figsize=(max(7, len(scenarios)*.65), 4))
        for j, method in enumerate(_methods()):
            points = [(scenarios.index(x['scenario_id'])+(j-1.5)*.15, x) for x in rows if x['method'] == method]
            axis.errorbar([i for i, x in points], [x['rate'] for i, x in points],
                          yerr=[[x['rate']-x['ci_low'] for i, x in points],
                                [x['ci_high']-x['rate'] for i, x in points]],
                          marker='o', linestyle='none', capsize=2, label=method,
                          color=colors[method])
        axis.set_xticks(range(len(scenarios)))
        labels = {x['scenario_id']: '%s\n%s/%s' % (x['spec_id'], x['n'], x['p']) for x in rows}
        axis.set_xticklabels([labels[x] for x in scenarios], rotation=90, fontsize=6)
        axis.set_ylabel('Null rejection rate' if tau == 0 else 'Power (valid subset)')
        axis.set_title('%s, tau=%s; null_group_id reuse in CSV' % (phase, tau))
        axis.set_ylim(-.03, 1.03)
        if tau == 0:
            axis.axhline(.05, color='black', linestyle=':', linewidth=1)
            axis.axhline(.08, color='grey', linestyle='--', linewidth=1)
        axis.legend(fontsize=7, bbox_to_anchor=(1.02, 1), loc='upper left')
        figure.tight_layout()
        figure.savefig(output/('%s_rates_tau_%s.png' % (phase, tau)), dpi=180)
        figure.savefig(output/('%s_rates_tau_%s.pdf' % (phase, tau)))
        plt.close(figure)
    rows = [x for x in result['paired'] if x['difference'] is not None]
    if rows:
        figure, axis = plt.subplots(figsize=(8, max(4, .22*len(rows))))
        for i, row in enumerate(rows):
            color = colors[row['comparator']]
            axis.plot([row['ci_low'], row['ci_high']], [i, i], color='grey', linewidth=3, alpha=.5)
            axis.plot([row['adjusted_ci_low'], row['adjusted_ci_high']], [i, i], color=color, linewidth=1)
            axis.plot(row['difference'], i, 'o', color=color, markersize=3)
        for comparator in _methods()[1:]:
            axis.plot([], [], 'o', color=colors[comparator], markersize=3, label=comparator)
        axis.set_yticks(range(len(rows)))
        axis.set_yticklabels(['%s/%s/%s/%s: %s' % (x['spec_id'], x['n'], x['p'], x['tau'], x['comparator']) for x in rows], fontsize=6)
        axis.axvline(0, color='grey', linestyle=':')
        axis.axvline(-.05, color='grey', linestyle='--')
        axis.set_xlabel('Paired power difference; grey 95%, colored Bonferroni')
        axis.legend(fontsize=7, bbox_to_anchor=(1.02, 1), loc='upper left')
        figure.tight_layout()
        figure.savefig(output/(phase+'_paired.png'), dpi=180)
        figure.savefig(output/(phase+'_paired.pdf'))
        plt.close(figure)
    rows = [x for x in result['runtime'] if x['mean_seconds'] is not None]
    if rows:
        figure, axis = plt.subplots(figsize=(max(7, len(rows)*.12), 4))
        axis.bar(np.arange(len(rows)), [x['mean_seconds'] for x in rows])
        axis.set_xticks(range(len(rows)))
        axis.set_xticklabels(['%s/%s' % (x['scenario_id'], x['method']) for x in rows], rotation=90, fontsize=5)
        axis.set_ylabel('Mean seconds per recorded method')
        figure.tight_layout()
        figure.savefig(output/(phase+'_runtime.png'), dpi=180)
        figure.savefig(output/(phase+'_runtime.pdf'))
        plt.close(figure)
    if retention:
        figure, axis = plt.subplots(figsize=(7, 4))
        unique = {}
        for row in retention:
            unique.setdefault(row['spec_id'], {})[row['s']] = row['reconstructed_peak_ratio']
        for spec, values in unique.items():
            axis.plot(sorted(values), [values[s] for s in sorted(values)], marker='o', label=spec)
        axis.set_xticks([5, 11, 21])
        axis.set_xlabel('Fixed Fourier truncation s')
        axis.set_ylabel('Reconstructed time-domain peak ratio')
        axis.set_ylim(-.02, max(1.05, max(x['reconstructed_peak_ratio'] for x in retention)+.05))
        axis.legend(fontsize=7, bbox_to_anchor=(1.02, 1), loc='upper left')
        figure.tight_layout()
        figure.savefig(output/(phase+'_signal_retention.png'), dpi=180)
        figure.savefig(output/(phase+'_signal_retention.pdf'))
        plt.close(figure)
