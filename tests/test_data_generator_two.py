import unittest
from unittest.mock import patch

from scipy.linalg import sqrtm as scipy_sqrtm

from simulation.data_generator_two import create_dataset_M1


class CreateDatasetM1RefactorTests(unittest.TestCase):
    def test_h1_branch_only_computes_matrix_square_root_once(self):
        with patch('simulation.data_generator_two.sqrtm', wraps=scipy_sqrtm) as mock_sqrtm:
            create_dataset_M1(
                n=4,
                p=4,
                M=6,
                h0=False,
                s0=2,
                signal_strength=0.2,
                seed=123,
            )

        self.assertEqual(mock_sqrtm.call_count, 1)


if __name__ == '__main__':
    unittest.main()
