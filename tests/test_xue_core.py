"""Xue single-sample definition checks; float64 tolerance 1e-12."""
import unittest
import warnings
import numpy as np
from common import statistic_calculator_xue as xue


class XueCoreTests(unittest.TestCase):
    def setUp(self):
        self.A = np.array([[0., 1.], [1., 3.], [2., 0.], [4., 2.]])

    def test_task_card_exact_reference(self):
        r = xue.xue_one_sample(self.A, np.eye(2), p=1, s=2)
        np.testing.assert_allclose(r['S'], [[35/16, 1/8], [1/8, 5/4]], atol=1e-12)
        np.testing.assert_allclose(r['m'], [[259/64, 27/32], [27/32, 1]], atol=1e-12)
        np.testing.assert_allclose(r['q'][np.triu_indices(2)], [361/259, 2/27, 1/4], atol=1e-12)
        self.assertAlmostEqual(r['Q'], 361/259, places=12)
        self.assertAlmostEqual(r['T'], -1.745279248999052, places=12)
        self.assertAlmostEqual(r['p_value'], .379592195050727, places=12)
        self.assertEqual(r['argmax'], (0, 0))
        self.assertEqual(r['status'], 'ok')
        self.assertFalse(r['reject'])

    def test_known_mean_and_flat_metadata(self):
        mean = np.array([.5, -.25])
        r = xue.xue_one_sample(self.A[:, None, :], np.eye(2), mean_mode='known', known_mean=mean)
        z = self.A - mean
        expected_S = np.empty((2, 2)); expected_m = np.empty((2, 2))
        for a in range(2):
            for b in range(2):
                products = np.array([row[a]*row[b] for row in z])
                expected_S[a, b] = sum(products) / 4
                expected_m[a, b] = sum((products - expected_S[a,b])**2) / 4
        np.testing.assert_allclose(r['S'], expected_S, atol=1e-12)
        np.testing.assert_allclose(r['m'], expected_m, atol=1e-12)
        self.assertEqual((r['p'], r['s'], r['d']), (1, 2, 2))
        self.assertEqual(r['metadata']['mean_mode'], 'known')

    def test_invalid_target_dimension_and_mean(self):
        for target in (np.array([[1., 1.], [0., 1.]]), np.diag([-1., 1.]), np.ones((3,3)), np.full((2,2), np.nan), np.eye(2).astype(complex)):
            with self.assertRaises(ValueError):
                xue.xue_one_sample(self.A, target, p=1, s=2)
        for kwargs in ({}, {'p':2,'s':2}, {'p':1,'s':2,'mean_mode':'known'}, {'p':1,'s':2,'mean_mode':'estimate','known_mean':[0,0]}, {'p':1,'s':2,'ordering':'basis_then_channel'}, {'p':1,'s':2,'target_type':'estimated'}, {'p':1,'s':2,'alpha':0}):
            with self.assertRaises(ValueError):
                xue.xue_one_sample(self.A, np.eye(2), **kwargs)
        with self.assertRaises(ValueError):
            xue.xue_one_sample(np.ones((4,1,1)), np.eye(1))
        with self.assertRaises(ValueError):
            xue.xue_one_sample(self.A[:2], np.eye(2), p=1, s=2)
        with self.assertRaises(ValueError):
            xue.xue_one_sample(self.A[:,None,:], np.eye(2), s=3)

    def test_degenerate_structured_failure_and_cross(self):
        r = xue.xue_one_sample(np.ones((4,2,1)), np.eye(2))
        self.assertEqual(r['status'], 'degenerate_product_variance')
        for key in ('reject','p_value','pvalue','Q','T'):
            self.assertIsNone(r[key])
        self.assertIn((0,0), r['failed_coordinates'])
        cross = xue.xue_cross_zero(self.A.reshape(4,2,1))
        self.assertEqual(cross['method'], 'Xue-1S-EV-cross-zero')
        self.assertEqual(cross['argmax'], (0,1))
        self.assertAlmostEqual(cross['Q'], 2/27)
        with self.assertRaises(ValueError):
            xue.compute_Tn_xue(self.A.reshape(4,2,1), eps=.01)
        with self.assertRaises(ValueError):
            xue.compute_Tn_xue(np.ones((4,2,1)))

    def test_extreme_tail_and_threshold_without_warnings(self):
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            for t, expected in ((-np.inf,1.),(-1e308,1.),(1e308,0.),(np.inf,0.)):
                self.assertEqual(xue.xue_pvalue(t), expected)
            for alpha in (np.nextafter(0.,1.), .05, np.nextafter(1.,0.)):
                tau = xue.xue_critical_value(alpha)
                self.assertTrue(np.isfinite(tau))
                self.assertAlmostEqual(xue.xue_pvalue(tau), alpha, places=12)
        self.assertAlmostEqual(xue.xue_critical_value(.05), 2.71621907057574)


if __name__ == '__main__':
    unittest.main()
