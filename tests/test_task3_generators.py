"""Independent algebra and stream checks for the task3 DGP."""
import hashlib
import importlib
import importlib.util
import json
import unittest

import numpy as np


class Task3GenerationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("simulation.task3_generators"),
                             "task3 generator module is required")
        self.dgp = importlib.import_module("simulation.task3_generators")

    def test_eight_specifications_have_required_scale_and_projection(self):
        expected = {
            "spectrum_fast_b4": [0.98194462, 0.99844307, 1],
            "spectrum_slow_b1": [0.51212573, 0.77956916, 1],
            "spectrum_flat_b0": [.2, .5, 1], "band_head": [.5, 1, 1],
            "band_tail": [0, 0, 1], "coherent_all": [.04, .25, 1],
            "coherent_tail": [0, 0, 1],
            "local_fejer": [.11933884, .52892562, 1],
        }
        norms = [1, 1, 1, 2.5, 2.5, 1, 2.5, 14/11]
        self.assertEqual(len(self.dgp.spec_ids()), 10)
        for (spec, ratios), norm in zip(expected.items(), norms):
            scenario = self.dgp.make_scenario(spec, .3, n=7, p=6)
            diag = self.dgp.diagnostics(scenario)
            phi = np.asarray(diag["basis"])
            np.testing.assert_allclose(phi.T @ phi / 64, np.eye(20), atol=4e-15)
            np.testing.assert_allclose(phi.mean(axis=0), 0, atol=1e-15)
            np.testing.assert_allclose(diag["latent_point_variance"], 1, atol=1e-14)
            self.assertAlmostEqual(diag["time_peak_effect"], .3)
            self.assertAlmostEqual(diag["whitened_signal_operator_norm"], norm)
            self.assertAlmostEqual(diag["rho"], .3 * norm)
            np.testing.assert_allclose([diag["projections"][str(s)]["reconstructed_peak_ratio"]
                                       for s in (5, 11, 21)], ratios, atol=6e-9)

    def test_matching_transform_and_noise_against_fixed_innovations(self):
        scenario = self.dgp.make_scenario("coherent_all", .3, n=7, p=6)
        result = self.dgp.generate(scenario, "smoke", 2)
        diag = self.dgp.diagnostics(scenario)
        lam = np.diag(diag["lambda_diagonal"])
        shape = np.asarray(diag["signal_cov_shape"])
        z = self.dgp.rng(scenario, "smoke", 2, "signal").standard_normal((7, 6, 20))
        coeff = z @ np.diag(np.sqrt(np.diag(lam)))
        edges = result["truth_metadata"]["edges_zero_based"]
        self.assertEqual(len(set(vertex for edge in edges for vertex in edge)), 4)
        for j, k in edges:
            plus = z[:, j] @ np.linalg.cholesky(lam + .3 * shape).T
            minus = z[:, k] @ np.linalg.cholesky(lam - .3 * shape).T
            coeff[:, j], coeff[:, k] = (plus + minus)/np.sqrt(2), (plus-minus)/np.sqrt(2)
        noise = self.dgp.rng(scenario, "smoke", 2, "noise").normal(0, .05, (7, 6, 64))
        expected = coeff @ np.asarray(diag["basis"]).T + noise
        np.testing.assert_allclose(result["Y"], expected, atol=1e-14)
        phi = np.asarray(diag["basis"])
        target = phi @ lam @ phi.T + .0025 * np.eye(64)
        np.testing.assert_allclose(result["gamma0"][0, 0], target)
        np.testing.assert_array_equal(result["gamma0"][0, 1], 0)
        self.assertEqual(result["Y"].shape, (7, 6, 64))

    def test_canonical_null_keys_and_independent_phase_streams(self):
        first = self.dgp.make_scenario("band_tail", 0, n=7, p=6)
        second = self.dgp.make_scenario("local_fejer", 0, n=7, p=6)
        self.assertEqual(self.dgp.data_key(first, "pilot", 1),
                         self.dgp.data_key(second, "pilot", 1))
        a = self.dgp.generate(first, "pilot", 1)
        b = self.dgp.generate(second, "pilot", 1)
        np.testing.assert_array_equal(a["Y"], b["Y"])
        self.assertEqual(a["data_id"], b["data_id"])
        changed = dict(first, workers=8, output="other", methods=[21, 5], repetitions=80)
        self.assertEqual(self.dgp.data_key(first, "pilot", 1),
                         self.dgp.data_key(changed, "pilot", 1))
        self.assertNotEqual(a["data_id"], self.dgp.generate(first, "confirm", 1)["data_id"])
        self.assertNotEqual(a["data_id"], self.dgp.generate(first, "pilot", 2)["data_id"])
        self.assertNotEqual(self.dgp.rng(first, "pilot", 1, "noise").random(),
                            self.dgp.rng(first, "pilot", 1, "signal").random())
        key = self.dgp.data_key(first, "pilot", 1)
        payload = json.dumps(key, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("utf-8")
        seed = (20261021 + int.from_bytes(hashlib.sha256(payload).digest()[:8], "little") + 13579) % (2**64)
        reference = np.random.default_rng(np.random.SeedSequence([seed & 0xffffffff, seed >> 32, 2, 0]))
        np.testing.assert_array_equal(self.dgp.rng(first, "pilot", 1, "signal").normal(size=5),
                                      reference.normal(size=5))
        state = np.random.get_state()
        self.dgp.generate(first, "pilot", 1)
        for before, after in zip(state, np.random.get_state()):
            np.testing.assert_equal(before, after)

    def test_legacy_references_reuse_original_generator_and_complete_target(self):
        from simulation.data_generation import sample_curves, sparse_correlation, make_rng
        for model in ("M1", "M2"):
            scenario = self.dgp.make_scenario("legacy_" + model + "_full_reference", .3, n=7, p=6)
            result = self.dgp.generate(scenario, "smoke", 1)
            task = result["truth_metadata"]["legacy_task"]
            C, edges = sparse_correlation(6, 4, scenario["legacy_delta"], make_rng(task, 1, "support"))
            observed, grid, kernel = sample_curves(task, 1, 7, C)
            np.testing.assert_array_equal(result["Y"], observed)
            self.assertEqual(result["truth_metadata"]["edges_zero_based"], edges)
            np.testing.assert_allclose(result["gamma0"][0, 0], kernel + .0025*np.eye(30))
            self.assertAlmostEqual(scenario["legacy_delta"] * scenario["kappa"], .3)
            self.assertEqual(len(grid), 30)

    def test_actual_projection_target_and_null_ratios(self):
        from common.xue_helper import projection_operator
        scenario = self.dgp.make_scenario("band_tail", .15, n=7, p=6)
        diag = self.dgp.diagnostics(scenario)
        generated = self.dgp.generate(scenario, "smoke", 1)
        for s in (5, 11, 21):
            projection = diag["projections"][str(s)]
            L = projection_operator(6, 64, s, grid=generated["grid"])
            flat = generated["gamma0"].transpose(0, 2, 1, 3).reshape(384, 384)
            expected = L @ flat @ L.T
            np.testing.assert_allclose(expected, np.kron(np.eye(6), projection["null_coefficient_covariance"]), atol=1e-15)
        null_diag = self.dgp.diagnostics(self.dgp.make_scenario("band_tail", 0, n=7, p=6))
        self.assertIsNone(null_diag["projections"]["5"]["reconstructed_peak_ratio"])

    def test_invalid_inputs_fail_without_covariance_repair(self):
        for args in (("unknown", .3, 7, 6), ("band_tail", -.1, 7, 6),
                     ("band_tail", .5, 7, 6), ("band_tail", .3, 1, 6),
                     ("band_tail", .3, 7, 3)):
            with self.assertRaises(ValueError):
                self.dgp.make_scenario(*args)
        scenario = self.dgp.make_scenario("band_tail", .3, n=7, p=6)
        for phase, rep in (("unknown", 1), ("pilot", -1), ("pilot", True)):
            with self.assertRaises(ValueError):
                self.dgp.generate(scenario, phase, rep)


if __name__ == "__main__":
    unittest.main()
