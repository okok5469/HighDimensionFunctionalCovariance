import unittest

import numpy as np

from simulation.data_generator_two import create_dataset_M1


class CreateDatasetM1RefactorTests(unittest.TestCase):
    def test_brownian_compatibility_entry_uses_the_frozen_task(self):
        from simulation.data_generation import simulate_one

        task = {
            'experiment': 2, 'model': 'M2', 'n': 4, 'p': 4, 'M': 6,
            's0': 2, 'delta': 0.2, 'sigma_noise': 0.05,
            'grid': 'closed_0_1', 'basis': 'phi_1_to_phi_5',
            'q': 5, 'c': 1.0, 'beta': 2.0,
            'support_policy': 'redraw_each_replicate_allow_shared_vertices',
        }
        expected = simulate_one(task, replicate=3)
        actual = create_dataset_M1(n=4, p=4, M=6, task=task, replicate=3)
        np.testing.assert_array_equal(actual['Y'], expected['Y'])
        np.testing.assert_array_equal(actual['Sigma_star'], expected['C'])
        np.testing.assert_array_equal(actual['X_true'][:, :, 0], 0.0)
        self.assertFalse(actual['is_h0'])


if __name__ == '__main__':
    unittest.main()
