"""Independent confidence-interval, completeness and locked-selection checks."""
import importlib
import importlib.util
import csv
import tempfile
from pathlib import Path
import unittest

import numpy as np
from scipy.stats import beta


class Task3SummaryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('simulation.task3_summary'),
                             'task3 summary module is required')
        self.summary = importlib.import_module('simulation.task3_summary')

    def test_binomial_exact_interval_and_incomplete_denominator(self):
        row = self.summary.binomial_summary([True, False, None], 5)
        self.assertEqual((row['planned'], row['completed'], row['valid'], row['failed']), (5, 3, 2, 1))
        self.assertEqual(row['missing'], 2)
        self.assertFalse(row['complete'])
        self.assertEqual(row['rejections'], 1)
        self.assertEqual(row['rate'], .5)
        self.assertAlmostEqual(row['ci_low'], beta.ppf(.025, 1, 2))
        self.assertAlmostEqual(row['upper_one_sided_95'], beta.ppf(.95, 2, 1))
        zero = self.summary.binomial_summary([False] * 500, 500)
        self.assertGreater(zero['ci_high'], 0)
        self.assertTrue(zero['calibration_upper_pass'])
        self.assertTrue(zero['conservative'])

    def test_paired_interval_has_uncertainty_when_no_discordance(self):
        row = self.summary.paired_summary([True, False] * 25, [True, False] * 25)
        self.assertEqual(row['difference'], 0)
        self.assertEqual(row['mcse'], 0)
        self.assertLess(row['ci_low'], 0)
        self.assertGreater(row['ci_high'], 0)
        a = [True, True, False, False, None]
        b = [True, False, True, False, False]
        row = self.summary.paired_summary(a, b)
        self.assertEqual([row[k] for k in ('both_reject', 'only_a', 'only_b', 'neither')], [1, 1, 1, 1])
        self.assertEqual(row['common_valid'], 4)
        self.assertAlmostEqual(row['mcse'], np.std([0, 1, -1, 0], ddof=1) / 2)
        self.assertAlmostEqual(row['ci_low'], beta.ppf(.0125, 1, 4) - beta.ppf(.9875, 2, 3))

    def test_selection_keeps_references_and_prefers_distinct_family(self):
        rows = self._pilot_rows()
        selection = self.summary.select_candidates(rows)
        self.assertEqual(selection['selected_candidates'], ['band_tail', 'coherent_all'])
        self.assertEqual(selection['references'], ['spectrum_fast_b4', 'legacy_M2_full_reference'])
        self.assertEqual(len(selection['specifications']), 4)
        scenarios = self.summary.confirmation_scenarios(selection)
        self.assertLessEqual(sum(x['repeats'] for x in scenarios), 6000)
        self.assertLessEqual(len(scenarios), 16)
        self.assertEqual({(x['scenario']['n'], x['scenario']['p']) for x in scenarios},
                         {(200, 20), (400, 20), (200, 50)})
        no_extension = self.summary.confirmation_scenarios(selection, True)
        self.assertLessEqual(sum(x['repeats'] for x in no_extension), 4400)
        nulls = [x for x in scenarios if x['scenario']['tau'] == 0]
        self.assertEqual(len(nulls), 5)

    def test_failed_or_badly_calibrated_candidates_never_win(self):
        rows = self._pilot_rows()
        for row in rows:
            if row['spec_id'] == 'band_tail':
                row['failed'] = 1
            if row['spec_id'] == 'coherent_all' and row['tau'] == 0 and row['method'] == 'ours':
                row['rate'] = .14
        selected = self.summary.select_candidates(rows)
        self.assertEqual(selected['selected_candidates'], [])
        self.assertIn('calibration_suspect', [x['status'] for x in selected['ranking']])
        rows = self._pilot_rows()
        for row in rows:
            if row['spec_id'] == 'band_tail' and row['tau'] > 0:
                row['failed'] = 1
        self.assertEqual(self.summary.select_candidates(rows)['selected_candidates'],
                         ['band_head', 'coherent_all'])
        all_negative = self.summary.select_candidates(self._pilot_rows(ours=.1))
        self.assertEqual(all_negative['status'], 'no_advantage_evidence')
        self.assertEqual(len(all_negative['selected_candidates']), 2)

    def test_summary_preserves_failures_common_subset_and_bonferroni(self):
        methods = ('ours', 'xue_s5', 'xue_s11', 'xue_s21')
        plan = {'phase': 'confirm', 'scenarios': [
            {'scenario_id': 'null', 'scenario': {'spec_id': 'band_tail', 'tau': 0, 'n': 200,
             'p': 20, 'null_group_id': 'flat'}, 'repeats': 500},
            {'scenario_id': 'alt', 'scenario': {'spec_id': 'band_tail', 'tau': .3, 'n': 200,
             'p': 20, 'null_group_id': 'flat'}, 'repeats': 3}]}
        records = []
        for replicate in range(500):
            records.append({'scenario_id': 'null', 'replicate': replicate,
                            'methods': {m: {'status': 'ok', 'reject': False} for m in methods}})
        records.append({'scenario_id': 'alt', 'replicate': 0,
                        'methods': {m: {'status': 'ok', 'reject': True} for m in methods}})
        records.append({'scenario_id': 'alt', 'replicate': 1,
                        'methods': dict({m: {'status': 'ok', 'reject': False} for m in methods},
                                        xue_s5={'status': 'failed', 'reject': None})})
        result = self.summary.summarize_records(plan, records)
        self.assertFalse(result['complete'])
        alt = [x for x in result['summary'] if x['scenario_id'] == 'alt']
        self.assertEqual([x['planned'] for x in alt], [3] * 4)
        self.assertEqual([x['common_valid'] for x in alt], [1] * 4)
        self.assertEqual([x['failed'] for x in alt], [0, 1, 0, 0])
        pair = next(x for x in result['paired'] if x['comparator'] == 'xue_s5')
        self.assertAlmostEqual(pair['adjusted_confidence'], 1 - .05 / 3)
        self.assertEqual(pair['label'], 'incomplete')
        with self.assertRaises(ValueError):
            self.summary.select_candidates([], {'pilot_calibration_max': .2})
        with tempfile.TemporaryDirectory() as tmp:
            self.summary.write_reports(dict(plan, phase='pilot'), records, tmp)
            self.summary.write_reports(plan, records, tmp)
            for name in ('confirm_summary.csv', 'paired_comparisons.csv', 'failures.csv',
                         'runtime_summary.csv', 'TASK3_RESULTS_REPORT.md'):
                self.assertTrue((Path(tmp) / name).exists())
            with (Path(tmp) / 'paired_comparisons.csv').open(encoding='utf-8-sig', newline='') as stream:
                self.assertEqual({x['phase'] for x in csv.DictReader(stream)}, {'pilot', 'confirm'})
        with self.assertRaises(ValueError):
            self.summary.summarize_records(plan, records + records[:1])

    def test_formal_label_requires_full_plan_integrity_and_calibration(self):
        methods = ('ours', 'xue_s5', 'xue_s11', 'xue_s21')
        plan = {'phase': 'confirm', 'scenarios': [
            {'scenario_id': name, 'scenario': {'spec_id': 'band_tail', 'family': 'task3_band',
             'tau': tau, 'n': 200, 'p': 20, 'null_group_id': 'flat'}, 'repeats': 500}
            for name, tau in [('null', 0), ('alt', .3)]]}
        records = []
        for scenario in plan['scenarios']:
            for replicate in range(500):
                records.append({'scenario_id': scenario['scenario_id'], 'replicate': replicate,
                    'methods': {m: {'status': 'ok', 'reject': scenario['scenario']['tau'] > 0 and m == 'ours'}
                                for m in methods}})
        result = self.summary.summarize_records(plan, records)
        self.assertTrue(result['complete'])
        self.assertEqual({x['label'] for x in result['paired']}, {'advantage'})
        self.assertTrue(all(x['adjusted_ci_low'] < x['ci_low'] for x in result['paired']))
        failure = [{'failure_reason': 'unexpected provenance record'}]
        result = self.summary.summarize_records(plan, records, failure)
        self.assertEqual({x['label'] for x in result['paired']}, {'incomplete'})
        for row in records[:100]:
            row['methods']['ours']['reject'] = True
        result = self.summary.summarize_records(plan, records)
        self.assertEqual({x['label'] for x in result['paired']}, {'calibration_not_accepted'})

    def test_report_preserves_all_null_power_rows_and_limits_interpretation(self):
        result = {'complete': True, 'summary': [], 'paired': []}
        for spec, family in [('coherent_all', 'task3_coherent'),
                             ('legacy_M2_full_reference', 'legacy')]:
            for tau in (0, .15, .30):
                for method in ('ours', 'xue_s5', 'xue_s11', 'xue_s21'):
                    result['summary'].append(dict(scenario_id='%s_%s' % (spec, tau),
                        spec_id=spec, family=family, tau=tau, n=200, p=20,
                        method=method, null_group_id=spec, rejections=0, planned=500,
                        completed=500, valid=500, failed=0, missing=0, rate=0,
                        mcse=0, ci_low=0, ci_high=.0074, upper_one_sided_95=.006,
                        conservative=True, calibration_upper_pass=True, common_valid=500))
            result['paired'].append(dict(spec_id=spec, family=family, n=200, p=20, tau=.30,
                scenario_id=spec+'_0.3', comparator='xue_s21', difference=.25,
                ci_low=.1, ci_high=.4, adjusted_ci_low=.05, adjusted_ci_high=.45,
                label='advantage'))
        text = self.summary._report({'phase': 'confirm'}, result)
        self.assertIn('robust advantage with s=21', text)
        self.assertIn('fixed-s21 advantage with possible truncation', text)
        self.assertIn('Null calibration', text)
        self.assertIn('All physical null and alternative rows', text)
        self.assertIn('planned/completed/valid/failed/missing', text)
        for row in result['summary']:
            self.assertIn('%s | %s' % (row['scenario_id'], row['method']), text)
        smoke = self.summary._report({'phase': 'smoke'}, result)
        self.assertIn('Smoke execution validates the pipeline only; it supports no scientific conclusion.', smoke)
        self.assertNotIn('robust advantage with s=21', smoke)
        self.assertNotIn('fixed-s21 advantage', smoke)

    def _pilot_rows(self, ours=.8):
        rows = []
        for spec, family, advantage in [('band_tail', 'task3_band', .0),
                                         ('band_head', 'task3_band', -.02),
                                         ('coherent_all', 'task3_coherent', -.04)]:
            for tau in (0, .15, .30):
                for method in ('ours', 'xue_s5', 'xue_s11', 'xue_s21'):
                    rows.append({'spec_id': spec, 'family': family, 'tau': tau, 'n': 200, 'p': 20,
                                 'method': method, 'rate': .04 if tau == 0 else
                                 (ours + advantage if method == 'ours' else .4),
                                 'planned': 50, 'valid': 50, 'completed': 50, 'failed': 0,
                                 'complete': True, 'null_group_id': 'flat'})
        return rows


if __name__ == '__main__':
    unittest.main()
