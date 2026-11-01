"""Deterministic checks of task5 study budgets and integer selection rules."""
import copy
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


def summary_rows(design, null=25, power=40):
    result = []
    for entry in design.pilot_entries():
        scenario, count = entry['scenario'], entry['repeats']
        for method in design.METHODS:
            k = power if scenario['tau'] else null
            result.append(dict(scenario_id=entry['scenario_id'], method=method,
                **{key: scenario[key] for key in ('spec_id', 'tau', 'n', 'p', 'null_group_id')},
                planned=count, completed=count, valid=count, common_valid=count,
                failed=0, missing=0, rejections=k, common_rejections=k, complete=True))
    return result


def replace_count(rows, spec, tau, count, n=800, p=20, method='ours'):
    for row in rows:
        if (row['spec_id'], row['tau'], row['n'], row['p'], row['method']) == (spec, tau, n, p, method):
            row['rejections'] = row['common_rejections'] = count


class Task5DesignTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('simulation.task5_design'),
                             'task5 fixed design is not implemented')
        self.d = importlib.import_module('simulation.task5_design')

    def test_pilot_budget_shapes_strengths_and_unique_physical_nulls(self):
        entries = self.d.pilot_entries()
        self.assertEqual((len(entries), sum(e['repeats'] for e in entries)), (69, 9300))
        nulls = [e for e in entries if not e['scenario']['tau']]
        self.assertEqual(len(nulls), 13)
        self.assertEqual(len({e['scenario_id'] for e in entries}), 69)
        self.assertEqual(len({(e['scenario']['null_group_id'], e['scenario']['n'], e['scenario']['p']) for e in nulls}), 13)
        self.assertEqual({e['scenario']['tau'] for e in entries}, {0., .15, .30, .45, .60})
        self.assertEqual({(e['scenario']['n'], e['scenario']['p']) for e in entries},
                         {(200, 20), (400, 20), (800, 20), (800, 50)})
        self.assertFalse(any(e['scenario']['spec_id'] == 'local_fejer' for e in nulls))

    def test_anchor_gate_uses_inclusive_integer_counts(self):
        for count, eligible in ((14, False), (15, True), (35, True), (36, False)):
            rows = summary_rows(self.d)
            replace_count(rows, 'm1_fourier5_peak1', 0., count)
            selected = self.d.select_extension(rows)
            row = next(r for r in selected['ranking'] if r['spec_id'] == 'm1_fourier5_peak1')
            self.assertEqual(row['eligible'], eligible)
        rows = summary_rows(self.d)
        replace_count(rows, 'm1_fourier5_peak1', .60, 39)
        self.assertNotEqual(self.d.select_extension(rows)['selected_model'], 'm1_fourier5_peak1')
        replace_count(rows, 'm1_fourier5_peak1', .60, 40)
        self.assertEqual(self.d.select_extension(rows)['selected_model'], 'm1_fourier5_peak1')

    def test_xue_calibration_and_power_do_not_change_ours_eligibility(self):
        rows = summary_rows(self.d)
        for row in rows:
            if row['method'].startswith('xue_'):
                row['rejections'] = row['common_rejections'] = row['planned']
        selection = self.d.select_extension(rows)
        self.assertEqual(selection['selected_model'], 'm1_fourier5_peak1')
        self.assertTrue(all(row['eligible'] for row in selection['ranking']))
        self.assertEqual(len(selection['calibration']), 13)
        row = selection['ranking'][0]
        self.assertFalse(row['anchor_null_point_in_band']['xue_s21'])
        self.assertEqual(row['anchor_power_rejection_differences']['xue_s21'], -10)
        self.assertEqual(len(row['calibration']['null_in_L']), 3)

    def test_band_count_precedes_distance_when_criteria_disagree(self):
        rows = summary_rows(self.d)
        replace_count(rows, 'm1_fourier5_peak1', 0., 500, n=400)
        replace_count(rows, 'm2_brownian_peak1', 0., 14, n=400)
        replace_count(rows, 'm2_brownian_peak1', 0., 14, p=50)
        replace_count(rows, 'coherent_all', .60, 0)
        self.assertEqual(self.d.select_extension(rows)['selected_model'], 'm1_fourier5_peak1')

    def test_ranking_uses_band_cells_before_distance_before_power(self):
        rows = summary_rows(self.d)
        replace_count(rows, 'm1_fourier5_peak1', 0., 14, n=400)
        replace_count(rows, 'm2_brownian_peak1', 0., 35, n=400)
        self.assertEqual(self.d.select_extension(rows)['selected_model'], 'coherent_all')
        replace_count(rows, 'm1_fourier5_peak1', 0., 25, n=400)
        replace_count(rows, 'm2_brownian_peak1', 0., 25, n=400)
        replace_count(rows, 'm2_brownian_peak1', .30, 41, n=400)
        self.assertEqual(self.d.select_extension(rows)['selected_model'], 'm2_brownian_peak1')
        replace_count(rows, 'm2_brownian_peak1', .30, 40, n=400)
        self.assertEqual(self.d.select_extension(rows)['selected_model'], 'm1_fourier5_peak1')

    def test_ranking_excludes_n200_and_retains_all_three_models(self):
        rows = summary_rows(self.d)
        replace_count(rows, 'm1_fourier5_peak1', 0., 500, n=200)
        replace_count(rows, 'm1_fourier5_peak1', .30, 0, n=200)
        selection = self.d.select_extension(rows)
        self.assertEqual(selection['selected_model'], 'm1_fourier5_peak1')
        self.assertEqual(len(selection['ranking']), 3)
        self.assertEqual([r['rank'] for r in selection['ranking']], [1, 2, 3])
        self.assertEqual(sum(r['selected'] for r in selection['ranking']), 1)

    def test_incomplete_duplicate_unexpected_and_invalid_rows_fail(self):
        rows = summary_rows(self.d)
        invalid = [rows[:-1], rows + [rows[0]], rows + [dict(rows[0], scenario_id='other')]]
        for field, value in (('rejections', 25.0), ('common_rejections', True),
                             ('common_rejections', 24), ('valid', 499), ('failed', 1),
                             ('complete', False), ('tau', .15), ('null_group_id', 'other')):
            changed = copy.deepcopy(rows)
            changed[0][field] = value
            invalid.append(changed)
        for value in invalid:
            with self.subTest(value=value[-1]), self.assertRaises(ValueError):
                self.d.select_extension(value)
        with self.assertRaises(ValueError):
            self.d.select_extension(rows, integrity_complete=False)

    def test_no_candidate_still_confirms_every_main_anchor(self):
        selection = self.d.select_extension(summary_rows(self.d, null=0, power=0))
        self.assertIsNone(selection['selected_model'])
        entries = self.d.confirmation_entries(selection)
        self.assertEqual((len(entries), sum(e['repeats'] for e in entries)), (12, 5700))
        self.assertEqual({(e['scenario']['n'], e['scenario']['p']) for e in entries}, {(800, 20)})
        self.assertEqual({e['scenario']['spec_id'] for e in entries},
                         {'m1_fourier5_peak1', 'm2_brownian_peak1', 'coherent_all'})

    def test_extension_confirms_five_units_with_fixed_strengths(self):
        selection = self.d.select_extension(summary_rows(self.d))
        entries = self.d.confirmation_entries(selection)
        self.assertEqual((len(entries), sum(e['repeats'] for e in entries)), (20, 9500))
        self.assertEqual({e['scenario']['tau'] for e in entries}, {0., .15, .30, .60})
        self.assertEqual(len({e['scenario_id'] for e in entries}), 20)
        self.assertEqual(sum(e['role'] == 'null' for e in entries), 5)
        self.assertTrue(all(e['repeats'] == (300 if e['scenario']['tau'] else 1000) for e in entries))
        with self.assertRaises(ValueError):
            self.d.confirmation_entries(dict(selection, selected_model='local_fejer'))

    def test_lock_includes_all_alternative_comparisons_and_fixed_family_size(self):
        for null, comparisons, budget in ((0, 27, 5700), (25, 45, 9500)):
            selection = self.d.select_extension(summary_rows(self.d, null=null))
            lock = self.d.lock_spec(selection, 'source-sha', {'fixed': True})
            self.assertEqual((lock['familywise_declarations'], len(lock['comparisons'])), (comparisons, comparisons))
            self.assertEqual(lock['planned_datasets'], budget)
            self.assertEqual(lock['multiple_testing'], 'Bonferroni_over_all_locked_alternative_pairs')
            self.assertEqual(lock['epsilon'], .05)
            self.assertEqual((lock['B'], lock['alpha']), (500, .05))
            self.assertEqual(lock['implementation_hash'], 'source-sha')
            self.assertEqual(lock['seed_namespaces'], {'H0': 'task5_unified_v1/confirm_h0',
                                                      'H1': 'task5_unified_v1/confirm_h1'})
            self.assertEqual(len({(r['scenario_id'], r['comparator']) for r in lock['comparisons']}), comparisons)

    def test_frozen_policy_cannot_be_changed_using_json_overrides(self):
        policy = self.d.load_policy()
        self.assertEqual(policy['maximum_formal_datasets'], 18800)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'policy.json'
            policy['anchor_null_minimum_rejections'] = 14
            path.write_text(json.dumps(policy), encoding='utf-8')
            with self.assertRaises(ValueError):
                self.d.load_policy(path)


if __name__ == '__main__':
    unittest.main()
