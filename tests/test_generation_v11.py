"""Deterministic DGP checks against independently expressed v1.1 formulae."""
import hashlib
import json
import unittest

import numpy as np

from simulation import data_generation as dgp


def task_for(model="M1"):
    return dict(experiment="unit", model=model, n=7, p=3, M=4, s0=4,
                delta=0.215, sigma_noise=0.05, grid="closed_0_1",
                basis="phi_1_to_phi_5", q=5, c=1.0, beta=2.0,
                support_policy="redraw_each_replicate_allow_shared_vertices")


def reference_rng(task, replicate, stream_id, group_id=0):
    payload = json.dumps(task, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("utf-8")
    digest = int.from_bytes(hashlib.sha256(payload).digest()[:8], "little")
    seed = (20261021 + digest + replicate * 13579) % (2 ** 64)
    return np.random.default_rng(np.random.SeedSequence(
        [seed & 0xffffffff, seed >> 32, stream_id, group_id]))


class GenerationTests(unittest.TestCase):
    def test_legacy_wrappers_reuse_frozen_dgp_without_global_rng_changes(self):
        from simulation.data_generator_one import create_dataset, generate_fourier_basis
        from simulation.data_generator_two import create_dataset_M1
        for model, create in (("M1", create_dataset), ("M2", create_dataset_M1)):
            task = task_for(model)
            state = np.random.get_state()
            result = create(n=7, p=3, M=4, task=task, replicate=2)
            np.testing.assert_array_equal(result["Y"], dgp.simulate_one(task, 2)["Y"])
            np.testing.assert_array_equal(result["Sigma_star"], result["C"])
            self.assertEqual(len(result["signal_indices"]), 4)
            after = np.random.get_state()
            for old, new in zip(state, after):
                np.testing.assert_equal(old, new)
        np.testing.assert_array_equal(generate_fourier_basis(4, 5)[:, 0], np.ones(4))
        with self.assertRaises(ValueError):
            create_dataset(7, 3, 4, q=4)

    def test_exact_fourier_and_brownian_with_independent_noise_reference(self):
        for model in ("M1", "M2"):
            task = task_for(model)
            result = dgp.simulate_one(task, 2)
            C = result["C"]
            self.assertEqual(np.count_nonzero(C - np.eye(3)), 4)
            self.assertEqual(len(result["edges_zero_based"]), 2)
            self.assertGreater(np.linalg.eigvalsh(C)[0], 0)
            values, vectors = np.linalg.eigh(C)
            L = vectors @ np.diag(np.sqrt(values)) @ vectors.T
            u = np.arange(4) / 3
            rng = reference_rng(task, 2, 2)
            if model == "M1":
                phi = np.array([np.sqrt(2) * (np.sin(2*np.pi*((k+1)//2)*u)
                    if k % 2 else np.cos(2*np.pi*(k//2)*u)) for k in range(1, 6)])
                np.testing.assert_allclose(dgp.fourier_literal_basis(u), phi)
                z = rng.standard_normal((7, 3, 5))
                signal = np.empty((7, 3, 4))
                for a in range(7):
                    signal[a] = sum((L @ z[a, :, k])[:, None] *
                                    phi[k][None, :] / (k+1) for k in range(5))
                K = sum(np.outer(phi[k], phi[k]) / (k+1)**2 for k in range(5))
            else:
                increments = rng.standard_normal((7, 3, 3)) / np.sqrt(3)
                brownian = np.concatenate((np.zeros((7, 3, 1)),
                                            np.cumsum(increments, axis=2)), axis=2)
                signal = np.array([L @ curve for curve in brownian])
                self.assertTrue(np.array_equal(signal[:, :, 0], np.zeros((7, 3))))
                K = np.minimum.outer(u, u)
            noise = reference_rng(task, 2, 3).normal(0, .05, (7, 3, 4))
            np.testing.assert_allclose(result["X_true"], signal, rtol=1e-12, atol=1e-12)
            np.testing.assert_allclose(result["Y"], signal + noise, rtol=1e-12, atol=1e-12)
            np.testing.assert_allclose(result["latent_time_kernel"], K)
            self.assertEqual(result["noise_variance"], .05**2)
            np.testing.assert_array_equal(result["Y"], dgp.simulate_one(task, 2)["Y"])
            self.assertTrue(np.isfinite(result["Y"]).all())

    def test_stable_hash_and_independent_streams_groups_and_support(self):
        task = task_for()
        expected = reference_rng(task, 5, 4, 2).standard_normal(8)
        np.testing.assert_array_equal(dgp.make_rng(task, 5, "bootstrap", "Y").standard_normal(8), expected)
        before = dgp.simulate_one(task, 0)["Y"]
        dgp.make_rng(task, 0, "bootstrap").standard_normal(1000)
        np.testing.assert_array_equal(before, dgp.simulate_one(task, 0)["Y"])
        x, _, _ = dgp.sample_curves(task, 0, 7, np.eye(3), "X")
        y, _, _ = dgp.sample_curves(task, 0, 7, np.eye(3), "Y")
        self.assertFalse(np.array_equal(x, y))
        C, edges = dgp.sparse_correlation(3, 6, .2, np.random.default_rng(1))
        self.assertEqual(len(edges), 3)  # Necessarily shares endpoints.
        np.testing.assert_array_equal(C - np.eye(3), (1-np.eye(3))*.2)
        C, edges = dgp.sparse_correlation(3, 0, 0, np.random.default_rng(1))
        np.testing.assert_array_equal(C, np.eye(3))
        self.assertEqual(edges, [])

    def test_invalid_inputs_fail_without_repair(self):
        for s0, delta in [(3, .2), (8, .2), (0, .2), (2, 0), (2, 1), (2, np.nan)]:
            with self.subTest(s0=s0, delta=delta), self.assertRaises(ValueError):
                dgp.sparse_correlation(3, s0, delta, np.random.default_rng(1))
        for key, value in [("n", 1), ("p", 2.5), ("M", 1), ("q", 4),
                           ("sigma_noise", -1), ("sigma_noise", np.inf),
                           ("grid", "open"), ("basis", "constant"), ("model", "M3"),
                           ("support_policy", "fixed_for_scenario")]:
            task = task_for(); task[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                dgp.simulate_one(task, 0)
        for replicate in (-1, .5):
            with self.assertRaises(ValueError):
                dgp.make_rng(task_for(), replicate, "signal")
        for C in (np.ones((3, 3)), np.full((3, 3), np.nan), np.eye(2),
                  np.array([[1, .1, 0], [0, 1, 0], [0, 0, 1]])):
            with self.assertRaises(ValueError):
                dgp.sample_curves(task_for(), 0, 7, C)


if __name__ == "__main__":
    unittest.main()
