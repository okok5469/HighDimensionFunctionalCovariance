"""Fixed task5 matrix, complete-data integer screening and confirmation lock."""
import json
from pathlib import Path

from simulation.task3_io import digest
from simulation.task5_generators import MAIN_MODELS, STUDY, make_scenario

METHODS = ('ours', 'xue_s5', 'xue_s11', 'xue_s21')


def _policy_path():
    return Path(__file__).with_name('configs') / 'task5' / 'search_policy.json'


def load_policy(path=None):
    """Reject policy drift rather than silently changing this study's rules."""
    policy = json.loads((Path(path) if path is not None else _policy_path()).read_text(encoding='utf-8'))
    expected = dict(study=STUDY, B=500, alpha=.05, M=64, noise_sd=.05,
        main_models=list(MAIN_MODELS), supplementary_models=['local_fejer', 'spectrum_fast_b4'],
        shapes=[[200, 20], [400, 20], [800, 20], [800, 50]], anchor=[800, 20],
        ranking_shapes=[[400, 20], [800, 20], [800, 50]],
        pilot_strengths=[.15, .30, .45, .60], null_repeats=500, alternative_repeats=50,
        pilot_null_scenarios=13, pilot_alternative_scenarios=56, pilot_datasets=9300,
        anchor_null_minimum_rejections=15, anchor_null_maximum_rejections=35,
        anchor_power_minimum_rejections=40,
        confirmation_strengths=[.15, .30, .60], confirmation_null_repeats=1000,
        confirmation_alternative_repeats=300, mandatory_confirmation_datasets=5700,
        maximum_confirmation_datasets=9500, minimum_formal_datasets=15000,
        maximum_formal_datasets=18800, epsilon=.05, level_band=[.03, .07],
        multiplicity='Bonferroni_over_all_locked_alternative_pairs')
    if policy != expected:
        raise ValueError('task5 search_policy.json differs from the frozen study design')
    return policy


def _entry(spec, tau, repeats, n, p):
    scenario = make_scenario(spec, tau, n=n, p=p)
    return dict(scenario=scenario, scenario_id=digest(scenario)[:20],
                repeats=repeats, role='alternative' if tau else 'null')


def pilot_entries():
    policy = load_policy()
    shapes = policy['shapes']
    nulls = [_entry(spec, 0., 500, n, p)
             for spec in (*MAIN_MODELS[:2], 'spectrum_flat_b0') for n, p in shapes]
    nulls.append(_entry('spectrum_fast_b4', 0., 500, 800, 20))
    main = [_entry(spec, tau, 50, n, p) for spec in MAIN_MODELS for n, p in shapes
            for tau in policy['pilot_strengths']]
    supplementary = [_entry(spec, tau, 50, 800, 20)
                     for spec in policy['supplementary_models'] for tau in policy['pilot_strengths']]
    return nulls + main + supplementary


def _complete_rows(rows, entries):
    expected = {(e['scenario_id'], method): e for e in entries for method in METHODS}
    indexed = {}
    for row in rows:
        key = row.get('scenario_id'), row.get('method')
        if key not in expected or key in indexed:
            raise ValueError('duplicate or unexpected scenario/method in task5 screening')
        entry = expected[key]
        count = entry['repeats']
        required = ('planned', 'completed', 'valid', 'common_valid')
        if (any(row.get(name) != count for name in required) or row.get('failed') != 0
                or row.get('missing') != 0 or row.get('complete') is not True):
            raise ValueError('all planned task5 paired data must be complete before selection')
        for name in ('rejections', 'common_rejections'):
            value = row.get(name)
            if type(value) is not int or not 0 <= value <= count:
                raise ValueError('task5 screening requires integer rejection counts')
        if row['rejections'] != row['common_rejections']:
            raise ValueError('paired and marginal counts disagree')
        for name in ('spec_id', 'tau', 'n', 'p', 'null_group_id'):
            if row.get(name) != entry['scenario'][name]:
                raise ValueError('task5 screening metadata disagrees with planned distribution')
        indexed[key] = row
    if set(indexed) != set(expected):
        raise ValueError('task5 screening input is incomplete')
    return indexed


def select_extension(summary_rows, integrity_complete=True):
    """Choose at most one main model; statistical alerts never cancel anchors.

    All ranks use integer counts: common denominators are 500 for H0 and
    50 for H1, so count distance and count sum exactly order the stated rates.
    Record-level distribution, target and source integrity is checked by caller.
    """
    policy = load_policy()
    if integrity_complete is not True:
        raise ValueError('identity and target integrity must pass before task5 selection')
    entries = pilot_entries()
    indexed = _complete_rows(summary_rows, entries)
    lookup = {(e['scenario']['spec_id'], e['scenario']['tau'], e['scenario']['n'], e['scenario']['p']): e
              for e in entries}

    def counts(spec, tau, n, p):
        entry = lookup[spec, tau, n, p]
        return {method: indexed[entry['scenario_id'], method]['rejections'] for method in METHODS}

    calibration = [dict(scenario_id=e['scenario_id'],
                       **{k: e['scenario'][k] for k in ('spec_id', 'null_group_id', 'n', 'p')},
                       rejections=counts(e['scenario']['spec_id'], 0., e['scenario']['n'], e['scenario']['p']),
                       planned=500) for e in entries if not e['scenario']['tau']]
    ranking = []
    for spec in MAIN_MODELS:
        null_spec = 'spectrum_flat_b0' if spec == 'coherent_all' else spec
        anchor_null = counts(null_spec, 0., 800, 20)
        anchor_power = counts(spec, .60, 800, 20)
        null_counts_L = [counts(null_spec, 0., n, p) for n, p in policy['ranking_shapes']]
        power_counts_L = [counts(spec, .30, n, p) for n, p in policy['ranking_shapes']]
        null_L = [counts['ours'] for counts in null_counts_L]
        power_L = [counts['ours'] for counts in power_counts_L]
        reasons = []
        if not 15 <= anchor_null['ours'] <= 35:
            reasons.append('anchor_level_point_outside_target_band')
        if anchor_power['ours'] < 40:
            reasons.append('anchor_power_below_0.80')
        ranking.append(dict(spec_id=spec, eligible=not reasons, exclusion_reasons=reasons,
            anchor_null_rejections=anchor_null['ours'], anchor_power_rejections=anchor_power['ours'],
            anchor_null_point_in_band={m: 15 <= k <= 35 for m, k in anchor_null.items()},
            anchor_power_rejection_differences={m: anchor_power['ours']-anchor_power[m] for m in METHODS[1:]},
            band_cells_in_L=sum(15 <= k <= 35 for k in null_L),
            max_null_count_distance_in_L=max(abs(k - 25) for k in null_L),
            power_rejections_sum_in_L=sum(power_L), null_rejections_in_L=null_L,
            power_rejections_in_L=power_L, calibration=dict(anchor_null=anchor_null,
                anchor_power=anchor_power, null_in_L=null_counts_L, power_in_L=power_counts_L), selected=False))
    ranking.sort(key=lambda row: (not row['eligible'], -row['band_cells_in_L'],
        row['max_null_count_distance_in_L'], -row['power_rejections_sum_in_L'], MAIN_MODELS.index(row['spec_id'])))
    selected = next((row['spec_id'] for row in ranking if row['eligible']), None)
    for rank, row in enumerate(ranking, 1):
        row['rank'] = rank
        row['selected'] = row['spec_id'] == selected
        row['not_selected_reason'] = (None if row['selected'] else
            ';'.join(row['exclusion_reasons']) or 'lower_fixed_rank')
    return dict(study=STUDY, selected_model=selected, ranking=ranking, calibration=calibration,
        exploration_datasets=9300,
        decision='confirm_anchor_and_extension' if selected else 'confirm_anchor_only',
        thresholds=dict(anchor_null_rejections=[15, 35], anchor_power_minimum_rejections=40,
                        nominal_alpha=.05, level_band=[.03, .07]))


def confirmation_entries(selection):
    policy = load_policy()
    selected = selection['selected_model']
    if selected is not None and selected not in MAIN_MODELS:
        raise ValueError('task5 extension must be a main model or None')
    units = [(spec, 800, 20) for spec in MAIN_MODELS]
    if selected is not None:
        units.extend((selected, n, p) for n, p in ((400, 20), (800, 50)))
    entries = []
    for spec, n, p in units:
        entries.append(_entry(spec, 0., 1000, n, p))
        entries.extend(_entry(spec, tau, 300, n, p) for tau in policy['confirmation_strengths'])
    return entries


def lock_spec(selection, implementation_hash, methods):
    """Full family is fixed before confirmation, irrespective of later labels."""
    entries = confirmation_entries(selection)
    comparisons = [dict(scenario_id=entry['scenario_id'], ours='ours', comparator=method)
                   for entry in entries if entry['scenario']['tau'] for method in METHODS[1:]]
    return dict(study=STUDY, phase='confirm', selection=selection, scenarios=entries,
        B=500, alpha=.05, methods=methods, implementation_hash=implementation_hash,
        comparisons=comparisons, planned_datasets=sum(e['repeats'] for e in entries),
        seed_namespace=STUDY+'/confirm', epsilon=.05, confidence=.95,
        seed_namespaces={'H0': STUDY+'/confirm_h0', 'H1': STUDY+'/confirm_h1'},
        calibration_rule='two_sided_95_CP_fully_inside_0.03_0.07_per_cell',
        multiple_testing='Bonferroni_over_all_locked_alternative_pairs',
        familywise_declarations=len(comparisons))
