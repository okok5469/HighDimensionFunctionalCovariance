"""Independent explicit-outer-product reference; float64 tolerance is 1e-10."""
import unittest
import numpy as np

from common import statistic_calculator_517 as core


def reference(data):
    n, p, M = data.shape
    residual = data - np.mean(data, axis=0)
    outer = np.empty((n, p, p, M, M))
    for r in range(n):
        for j in range(p):
            for k in range(p):
                outer[r, j, k] = np.outer(residual[r, j], residual[r, k])
    return outer.sum(axis=0) / (n - 1), outer - outer.mean(axis=0), outer.mean(axis=0)


class CovarianceV11Tests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(20261021)
        self.x = rng.normal(size=(7, 3, 4)) + np.arange(12).reshape(3, 4)
        self.y = rng.normal(size=(11, 3, 4)) - 3 * np.arange(12).reshape(3, 4)
        self.target = rng.normal(size=(3, 3, 4, 4))
        self.xi = rng.normal(size=(9, 7)) + 2
        self.eta = rng.normal(size=(9, 11)) - 1

    def test_independent_references_and_mean_shifts(self):
        cov, h, qbar = reference(self.x)
        cov_y, hy, _ = reference(self.y)
        np.testing.assert_allclose(core.calculate_u_statistic_matrices(self.x), cov, atol=1e-10, rtol=1e-10)
        np.testing.assert_allclose(qbar, 6 * cov / 7, atol=1e-10)
        np.testing.assert_allclose(h.sum(axis=0), 0, atol=1e-10)
        for pairs in (None, ~np.eye(3, dtype=bool), np.eye(3, dtype=bool)[[1, 0, 2]]):
            mask = np.ones((3, 3), dtype=bool) if pairs is None else pairs
            expected_single = np.array([np.max(np.abs(np.sqrt(7) / 6 * np.einsum('r,rjkst->jkst', w, h))[mask]) for w in self.xi])
            scale = np.sqrt(7 * 11 / 18)
            expected_two = np.array([np.max(np.abs(scale * (np.einsum('r,rjkst->jkst', w, h) / 6 - np.einsum('r,rjkst->jkst', v, hy) / 10))[mask]) for w, v in zip(self.xi, self.eta)])
            one = core.covariance_one_sample(self.x, self.target, pairs, B=9, multipliers=self.xi)
            two = core.covariance_two_sample(self.x, self.y, pairs, B=9, multipliers=(self.xi, self.eta))
            np.testing.assert_allclose(one['statistic'], np.sqrt(7) * np.max(np.abs(cov - self.target)[mask]), atol=1e-10)
            np.testing.assert_allclose(two['statistic'], scale * np.max(np.abs(cov - cov_y)[mask]), atol=1e-10)
            np.testing.assert_allclose(one['bootstrap_statistics'], expected_single, atol=1e-10, rtol=1e-10)
            np.testing.assert_allclose(two['bootstrap_statistics'], expected_two, atol=1e-10, rtol=1e-10)
            shifted = core.covariance_two_sample(self.x + 7, self.y - 9, pairs, B=9, multipliers=(self.xi, self.eta))
            shifted_one = core.covariance_one_sample(self.x + 7, self.target, pairs, B=9, multipliers=self.xi)
            for field in ('statistic', 'bootstrap_statistics'):
                np.testing.assert_allclose(shifted[field], two[field], atol=1e-10, rtol=1e-10)
                np.testing.assert_allclose(shifted_one[field], one[field], atol=1e-10, rtol=1e-10)

    def test_raw_multipliers_unchanged_and_global_random_state(self):
        old_xi, old_eta = self.xi.copy(), self.eta.copy()
        self.xi.setflags(write=False)
        self.eta.setflags(write=False)
        core.covariance_two_sample(self.x, self.y, B=9, multipliers=(self.xi, self.eta))
        np.testing.assert_array_equal(self.xi, old_xi)
        np.testing.assert_array_equal(self.eta, old_eta)
        np.random.seed(123)
        before = np.random.get_state()
        first = core.covariance_test(self.x, B=9, seed=42)
        second = core.covariance_test(self.x, B=9, seed=np.random.default_rng(42))
        self.assertEqual(first, second)
        after = np.random.get_state()
        np.testing.assert_array_equal(before[1], after[1])
        self.assertEqual(before[2:], after[2:])

    def test_finite_B_ties_and_float_boundary(self):
        for boot, alpha in ((np.arange(500.), .05), (np.array([0., 1., 1., 2., 3., 4., 5., 6., 7.]), .8), (np.zeros(9), .05)):
            for observed in np.concatenate((boot, np.nextafter(boot, np.inf), [1000.])):
                result = core._decision(observed, boot, alpha)
                expected_p = (1 + sum(float(b) >= observed for b in boot)) / (len(boot) + 1)
                self.assertEqual(result['pvalue'], expected_p)
                self.assertEqual(result['reject'], observed > result['critical_value'])
        self.assertEqual(core._decision(0, np.arange(500.), .05)['critical_value'], 475.)
        self.assertEqual(core._decision(0, np.arange(9.), .8)['critical_value'], 2.)

    def test_all_double_times_and_whole_channel_blocks(self):
        data = np.zeros((7, 2, 3))
        data[:, 0, 0] = np.arange(7)
        data[:, 1, 2] = np.arange(7)
        result = core.covariance_one_sample(data, np.zeros((2, 2, 3, 3)), ~np.eye(2, dtype=bool), B=3, seed=1)
        self.assertAlmostEqual(result['statistic'], np.sqrt(7) * np.var(np.arange(7), ddof=1))
        data[:, 1, 2] = 0
        self.assertEqual(core.covariance_test(data, B=3, seed=1)[0], 0.)

    def test_invalid_inputs_and_high_dimension(self):
        target = np.zeros((3, 3, 4, 4))
        for data in (self.x[:1], self.x[0], self.x * np.nan, self.x * np.inf, np.empty((7, 0, 4))):
            with self.assertRaises(ValueError):
                core.covariance_one_sample(data, target, B=3)
        for kwargs in ({'B': 0}, {'B': True}, {'B': 1.5}, {'alpha': 1}, {'alpha': np.nan}, {'channel_pairs': np.zeros((3, 3), bool)}, {'channel_pairs': np.ones((2, 2), bool)}, {'grid': [0, 1]}, {'grid': [0, 1, np.nan, 3]}, {'multipliers': np.ones((3, 6))}):
            with self.assertRaises(ValueError):
                core.covariance_one_sample(self.x, target, **kwargs)
        for wrong in (target[..., :2], target * np.nan):
            with self.assertRaises(ValueError):
                core.covariance_one_sample(self.x, wrong, B=3)
        with self.assertRaises(ValueError):
            core.covariance_two_sample(self.x, self.y[:, :, :3], B=3)
        with self.assertRaises(ValueError):
            core.covariance_two_sample(self.x, self.y, B=3, grid=[0, 1, 2, 3], grid_y=[0, 1, 2, 4])
        high = np.random.default_rng(3).normal(size=(4, 9, 3))
        statistic, critical, pvalue = core.covariance_test(high, B=3, seed=2)
        self.assertTrue(np.isfinite([statistic, pvalue]).all())
        self.assertEqual(critical, np.inf)  # B=3 cannot reject at alpha=.05.


if __name__ == '__main__':
    unittest.main()
