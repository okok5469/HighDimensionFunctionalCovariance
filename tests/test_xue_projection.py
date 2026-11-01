"""Fixed-map data/target alignment tests, with explicit independent formulas."""
import unittest

import numpy as np

from common import xue_helper as helper


class XueProjectionTests(unittest.TestCase):
    def setUp(self):
        self.Y = np.random.default_rng(721).normal(size=(9, 2, 4))

    def test_legacy_projection_is_preserved_exactly_and_operator_matches(self):
        u = np.linspace(0., 1., 4)
        B = np.column_stack((np.ones(4), np.sqrt(2)*np.sin(2*np.pi*u),
                             np.sqrt(2)*np.cos(2*np.pi*u)))
        expected = np.einsum('npm,ms->nps', self.Y, B) / 4
        np.testing.assert_array_equal(helper.project_to_fourier_basis(self.Y, 3), expected)
        L = helper.projection_operator(2, 4, 3)
        np.testing.assert_array_equal(L, np.kron(np.eye(2), B.T/4))
        np.testing.assert_allclose(self.Y.reshape(9, 8) @ L.T, expected.reshape(9, 6), atol=1e-15)

    def test_nontrivial_operator_transforms_both_data_and_full_noisy_target(self):
        rng = np.random.default_rng(11)
        L = rng.normal(size=(6, 8))
        B = rng.normal(size=(8, 8))
        latent = B @ B.T
        gamma_flat = latent + .0025*np.eye(8)
        gamma = gamma_flat.reshape(2, 4, 2, 4).transpose(0, 2, 1, 3)
        original = self.Y.copy()
        result = helper.run_xue_one_sample(self.Y, gamma, s=3, operator=L)
        A = np.empty((9, 6))
        for i in range(9):
            for a in range(6):
                A[i, a] = sum(L[a, j*4+t] * self.Y[i, j, t]
                              for j in range(2) for t in range(4))
        target = np.empty((6, 6))
        for a in range(6):
            for b in range(6):
                target[a, b] = sum(L[a, j*4+t] * gamma[j, k, t, v] * L[b, k*4+v]
                                   for j in range(2) for k in range(2)
                                   for t in range(4) for v in range(4))
        centered = A - A.mean(axis=0)
        np.testing.assert_allclose(result['S'], centered.T @ centered / 9, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(result['sigma0'], target, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(result['sigma0'] - L@latent@L.T,
                                   .0025*L@L.T, rtol=1e-10, atol=1e-10)
        self.assertFalse(np.allclose(result['sigma0'], gamma_flat[:6, :6]))
        self.assertEqual(result['test_scope'], 'all')
        self.assertEqual(result['method'], 'Xue-1S-EV')
        self.assertEqual(result['source_target_type'], 'known_grid_covariance')
        self.assertEqual(result['projection_id'], 'provided_fixed_linear_operator')
        np.testing.assert_array_equal(self.Y, original)

    def test_coefficient_target_is_used_directly_and_rng_untouched(self):
        sigma = np.eye(6) + .1*np.ones((6, 6))
        state = np.random.get_state()
        result = helper.run_xue_one_sample(self.Y, sigma0=sigma, s=3)
        np.testing.assert_array_equal(result['sigma0'], sigma)
        A = helper.project_to_fourier_basis(self.Y, 3)
        direct = helper.run_xue_one_sample(A, sigma0=sigma, input_type='coefficients', s=3)
        self.assertAlmostEqual(result['Q'], direct['Q'], places=12)
        after = np.random.get_state()
        for old, new in zip(state, after):
            np.testing.assert_equal(old, new)
        self.assertEqual(result['basis_id'], 'fixed_fourier_phi_0_to_s_minus_1')
        self.assertIn('not_author_spline_or_automatic_order', result['projection_convention'])

    def test_invalid_or_missing_target_and_projection_are_explicit(self):
        sigma = np.eye(6)
        for kwargs in ({}, {'gamma0':np.eye(8)}, {'sigma0':np.eye(4)},
                       {'gamma0':np.zeros((2, 2, 4, 4)), 'sigma0':sigma},
                       {'sigma0':sigma, 'operator':np.ones((5, 8))},
                       {'sigma0':sigma, 'operator':np.full((6, 8), np.nan)},
                       {'sigma0':sigma, 'target_type':'estimated_from_current_data'},
                       {'sigma0':sigma, 'grid':np.arange(3)}):
            with self.subTest(kwargs=tuple(kwargs)), self.assertRaises(ValueError):
                helper.run_xue_one_sample(self.Y, s=3, **kwargs)
        bad = np.eye(8); bad[0, 0] = -1
        bad4 = bad.reshape(2, 4, 2, 4).transpose(0, 2, 1, 3)
        with self.assertRaises(ValueError):
            helper.run_xue_one_sample(self.Y, bad4, s=3)

    def test_degeneracy_has_no_pseudodecision_and_cross_route_is_named(self):
        Y = np.ones((9, 2, 4))
        result = helper.run_xue_one_sample(Y, sigma0=np.eye(6), s=3)
        self.assertEqual(result['status'], 'degenerate_product_variance')
        self.assertIsNone(result['reject'])
        self.assertIsNone(result['p_value'])
        with self.assertRaisesRegex(ValueError, 'degenerate'):
            helper.run_xue_test(Y, s=3)
        cross = helper.run_xue_cross_test(self.Y, s=3)
        self.assertEqual(cross['method'], 'Xue-1S-EV-cross-zero')
        self.assertEqual(cross['test_scope'], 'cross')
        self.assertEqual(cross['status'], 'ok')

    def test_complex_inputs_are_rejected_without_discarding_imaginary_parts(self):
        complex_Y = self.Y.astype(complex) + 1j
        gamma = np.eye(8).reshape(2, 4, 2, 4).transpose(0, 2, 1, 3).astype(complex)
        cases = (
            lambda: helper.project_to_fourier_basis(complex_Y, 3),
            lambda: helper.projection_operator(2, 4, 3, np.linspace(0, 1, 4)+1j),
            lambda: helper.run_xue_one_sample(self.Y, gamma+1j, s=3),
            lambda: helper.run_xue_one_sample(self.Y, sigma0=np.eye(6), s=3,
                                              operator=np.ones((6, 8))+1j),
            lambda: helper.run_xue_one_sample(np.ones((9, 2, 3))+1j,
                                              sigma0=np.eye(6), s=3,
                                              input_type='coefficients'),
        )
        for case in cases:
            with self.assertRaisesRegex(ValueError, 'real'):
                case()


if __name__ == '__main__':
    unittest.main()
