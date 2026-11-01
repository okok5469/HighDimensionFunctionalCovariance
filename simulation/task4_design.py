"""Bounded task4 scenario design and integer-count candidate screening."""
import json
from pathlib import Path
from simulation.task3_io import digest
from simulation.task4_generators import make_scenario, STUDY

METHODS = ('ours','xue_s5','xue_s11','xue_s21')


def _policy_path():
    return Path(__file__).with_name('configs')/'task4'/'search_policy.json'


def load_policy(path=None):
    """Validate the deployed policy against this fixed study, without overrides.

    Changing a threshold requires a reviewed new study implementation; editing
    a packaged JSON file alone must never silently change or bypass the design.
    """
    policy=json.loads((Path(path) if path is not None else _policy_path()).read_text(encoding='utf-8'))
    expected=dict(study=STUDY,B=500,alpha=.05,n=200,p=20,q=20,M=64,
        pilot_strengths=dict(coherent_all=[.30,.45,.60],local_fejer=[.30,.45,.60],spectrum_fast_b4=[.45,.60]),
        alternative_repeats=50,null_repeats=100,null_groups=['spectrum_flat_b0','spectrum_fast_b4'],
        fallback_spec='coherent_two_peaks',fallback_strengths=[.30,.45,.60],
        minimum_ours_rejections=30,preferred_ours_rejections=40,maximum_rejection_gap=5,
        null_suspect_above_rejections=10,confirmation_null_repeats=500,
        confirmation_alternative_repeats=300,maximum_confirmation_datasets=2200,
        maximum_formal_datasets=2950,epsilon=.05,multiplicity='Bonferroni_over_all_locked_alternative_pairs')
    if policy != expected:
        raise ValueError('task4 search_policy.json differs from the frozen study design')
    return policy


def _entry(spec,tau,repeats):
    scenario = make_scenario(spec,tau)
    return dict(scenario=scenario,scenario_id=digest(scenario)[:20],
                repeats=repeats,role='alternative' if tau else 'null')


def pilot_entries():
    load_policy()
    entries = [_entry('spectrum_flat_b0',0.,100),_entry('spectrum_fast_b4',0.,100)]
    entries += [_entry(spec,tau,50) for spec in ('coherent_all','local_fejer') for tau in (.30,.45,.60)]
    return entries+[_entry('spectrum_fast_b4',tau,50) for tau in (.45,.60)]


def fallback_entries():
    load_policy()
    return [_entry('coherent_two_peaks',tau,50) for tau in (.30,.45,.60)]


def _complete_rows(rows, fallback_complete):
    expected = {(e['scenario_id'],m):e for e in pilot_entries()+(fallback_entries() if fallback_complete else []) for m in METHODS}
    indexed = {}
    for row in rows:
        key = row['scenario_id'],row['method']
        if key not in expected or key in indexed:
            raise ValueError('duplicate or unexpected scenario/method in screening input')
        entry = expected[key]
        n = entry['repeats']
        required_counts = ('planned','completed','valid','common_valid')
        if any(row.get(k) != n for k in required_counts) or row.get('failed') != 0 or row.get('missing') != 0 or row.get('complete') is not True:
            raise ValueError('all planned paired data must be complete before screening')
        for name in ('rejections','common_rejections'):
            value = row.get(name)
            if isinstance(value,bool) or not isinstance(value,int) or not 0 <= value <= n:
                raise ValueError('screening requires integer rejection counts')
        if row['rejections'] != row['common_rejections']:
            raise ValueError('paired and marginal counts disagree')
        for name in ('spec_id','tau','n','p','null_group_id'):
            if row.get(name) != entry['scenario'][name]:
                raise ValueError('screening metadata disagrees with planned distribution')
        indexed[key] = row
    if set(indexed) != set(expected):
        raise ValueError('screening input is incomplete')
    return indexed


def select_candidates(summary_rows, integrity_complete=True, fallback_complete=False):
    """Gate the complete 600/750 data sets; never select on incomplete records.

    The caller additionally verifies record-level identity/target/source integrity.
    Every decision and rank is retained, including failed calibration gates.
    """
    load_policy()
    if integrity_complete is not True:
        raise ValueError('identity and target integrity must pass before screening')
    entries = pilot_entries()+(fallback_entries() if fallback_complete else [])
    indexed = _complete_rows(summary_rows,fallback_complete)
    calibration = {}
    for entry in entries:
        scenario = entry['scenario']
        if scenario['tau']:
            continue
        suspect = [m for m in METHODS if indexed[entry['scenario_id'],m]['rejections'] > 10]
        calibration[scenario['null_group_id']] = dict(suspect_methods=suspect,
            calibration_suspect=bool(suspect),primary_suspect=any(m in suspect for m in ('ours','xue_s21')),
            rejections={m:indexed[entry['scenario_id'],m]['rejections'] for m in METHODS},
            planned=100)
    ranking = []
    for entry in entries:
        scenario = entry['scenario']
        if not scenario['tau']:
            continue
        counts = {m:indexed[entry['scenario_id'],m]['rejections'] for m in METHODS}
        ours,best = counts['ours'],max(counts[m] for m in METHODS[1:])
        gate = calibration[scenario['null_group_id']]
        reasons = []
        if ours < 30: reasons.append('power_below_0.60')
        if best-ours > 5: reasons.append('gap_exceeds_0.10')
        if gate['primary_suspect']: reasons.append('primary_calibration_suspect')
        ranking.append(dict(spec_id=scenario['spec_id'],tau=scenario['tau'],scenario_id=entry['scenario_id'],
            null_group_id=scenario['null_group_id'],rejections=counts,power_ours=ours/50,
            differences={m:(ours-counts[m])/50 for m in METHODS[1:]},delta_min=(ours-best)/50,
            useful=not reasons,high_power=ours>=40,saturated=all(v>=49 for v in counts.values()),
            calibration_suspect_methods=gate['suspect_methods'],exclusion_reasons=reasons))
    ranking.sort(key=lambda r:(not r['high_power'],-r['delta_min'],-r['power_ours'],r['tau'],r['spec_id']))
    for rank,row in enumerate(ranking,1): row['rank'] = rank
    models = [r for r in ranking if r['useful'] and r['spec_id'] != 'spectrum_fast_b4']
    references = [r for r in ranking if r['useful'] and r['spec_id'] == 'spectrum_fast_b4']
    chosen = {r['scenario_id'] for r in models[:1]+references[:1]}
    for row in ranking:
        row['selected'] = row['scenario_id'] in chosen
        row['not_selected_reason'] = (None if row['selected'] else
            (';'.join(row['exclusion_reasons']) or 'lower_fixed_rank_in_selection_pool'))
    # No reference-only signal can suppress the prescribed coherent/local fallback.
    fallback_required = not models and not fallback_complete and not calibration['spectrum_flat_b0']['primary_suspect']
    return dict(study=STUDY,ranking=ranking,calibration=calibration,
        selected_model=models[0] if models else None,selected_reference=references[0] if references else None,
        fallback_required=fallback_required,fallback_complete=bool(fallback_complete),
        exploration_datasets=750 if fallback_complete else 600,
        decision='fallback_required' if fallback_required else ('confirm' if models or references else 'no_eligible_interval'),
        thresholds=dict(minimum_power=.60,preferred_power=.80,maximum_gap=.10,
                        calibration_suspect_above=.10,formal_epsilon=.05))


def confirmation_entries(selection):
    load_policy()
    if selection['fallback_required']:
        return []
    entries = []
    for key in ('selected_model','selected_reference'):
        candidate = selection[key]
        if candidate is None:
            continue
        spec,tau = candidate['spec_id'],candidate['tau']
        if spec == 'spectrum_fast_b4':
            null_spec,taus = spec,(.45,.60)
        else:
            null_spec = 'spectrum_flat_b0'
            tested = [.30,.45,.60]
            i = tested.index(tau)
            taus = sorted([tau,tested[i-1] if i else tested[1]])
        entries.append(_entry(null_spec,0.,500))
        entries.extend(_entry(spec,t,300) for t in taus)
    if len(entries)>6 or sum(e['repeats'] for e in entries)>2200:
        raise ValueError('confirmation budget exceeded')
    return entries


def lock_spec(selection, implementation_hash, methods):
    entries = confirmation_entries(selection)
    if selection['fallback_required']:
        raise ValueError('cannot lock before the prescribed fallback completes')
    comparisons = [dict(scenario_id=e['scenario_id'],ours='ours',comparator=m)
                   for e in entries if e['scenario']['tau'] for m in METHODS[1:]]
    return dict(study=STUDY,phase='confirm',selection=selection,scenarios=entries,
        B=500,alpha=.05,methods=methods,implementation_hash=implementation_hash,
        comparisons=comparisons,planned_datasets=sum(e['repeats'] for e in entries),
        seed_namespace=STUDY+'/confirm',epsilon=.05,confidence=.95,
        calibration_rule='one_sided_95_upper_at_most_0.08',
        multiple_testing='Bonferroni_over_all_locked_alternative_pairs',
        familywise_declarations=len(comparisons))
