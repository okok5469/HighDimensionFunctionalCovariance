"""Caller identity and fail-fast regression for the restricted Xue baseline."""
import unittest
import warnings
from unittest.mock import patch

import numpy as np


class XueCallerTests(unittest.TestCase):
    def test_har_subsample_labels_and_degenerate_failure(self):
        from empirical import Main_HAR_empirical as har
        data = np.random.default_rng(321).normal(size=(10, 3, 8))
        result = har.one_subsample_test(data, 8, [0, 1, 2], 3, 42)
        self.assertEqual(result['xue_method'], 'Xue-1S-EV-cross-zero')
        self.assertEqual(result['xue_version'], 'xue-audit-v1')
        self.assertEqual((result['xue_n'], result['xue_p'], result['xue_s'], result['xue_d']),
                         (8, 3, har.Q_SMOOTH, 3*har.Q_SMOOTH))
        self.assertEqual(result['xue_covariance_denominator'], 'n')
        self.assertIn('xue-audit-v1', str(har.RESULTS_DIR))
        with self.assertRaisesRegex(ValueError, 'degener|variance'):
            har.repeat_subsample(np.ones((8, 3, 8)), 8, [0, 1, 2], 2, 3, 42)

    def test_archive_routes_shared_core_and_rejects_degeneracy(self):
        from archive.stock_empirical.xue_test import xue_test
        from common.statistic_calculator_xue import xue_cross_zero
        data = np.random.default_rng(432).normal(size=(9, 3, 4))
        expected = xue_cross_zero(data, s=4)
        actual = xue_test(data)
        self.assertEqual(actual['method'], 'Xue-1S-EV-cross-zero')
        self.assertEqual(actual['version'], 'xue-audit-v1')
        self.assertEqual(actual['Tn'], expected['T'])
        self.assertEqual(actual['p_value'], expected['p_value'])
        self.assertEqual(actual['T_max_raw'], expected['Q'])
        with self.assertRaisesRegex(ValueError, 'degener|variance'):
            xue_test(np.ones((8, 3, 4)))

    def test_third_model_labels_and_does_not_swallow_xue_failure(self):
        from simulation import Main_three as main
        task = dict(main.create_experiment_tasks()[0])
        task.update(n=8, p=3, M=8, B=3, n_repeats=1)
        result = main.execute_single_task(task)
        self.assertEqual(result['xue_method'], 'Xue-1S-EV-cross-zero')
        self.assertEqual(result['xue_version'], 'xue-audit-v1')
        self.assertIn('xue-audit-v1', str(main.OUTPUT_DIR))
        self.assertEqual(result['xue_tail_arithmetic'], 'stable_expm1')
        with patch.object(main, 'run_xue_cross_test', side_effect=ValueError('degenerate variance')):
            with self.assertRaisesRegex(ValueError, 'degenerate variance'):
                main.execute_single_task(task)


    def test_archive_public_calibration_uses_stable_shared_functions(self):
        from archive.stock_empirical.xue_test import xue_pvalue, xue_critical_value
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            self.assertEqual(xue_pvalue(-1e308), 1.0)
            self.assertEqual(xue_pvalue(1e308), 0.0)
            self.assertTrue(np.isfinite(xue_critical_value(np.nextafter(0., 1.))))


if __name__ == '__main__':
    unittest.main()
