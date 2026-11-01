"""Xue method identities, failure propagation and actual file-input workflow."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from simulation import covariance_experiments as runner


class XueWorkflowTests(unittest.TestCase):
    def test_cross_comparison_retains_data_hypothesis_and_labels_actual_version(self):
        task = dict(runner.load_config('smoke')['tasks'][0], with_xue=True)
        record = runner.run_replicate(task, 0)
        self.assertEqual(record['xue'].get('method'), 'Xue-1S-EV-cross-zero')
        self.assertEqual(record['xue']['status'], 'ok')
        self.assertEqual(record['xue']['implementation_version'], 'xue-audit-v1')
        self.assertEqual(record['xue']['test_scope'], 'cross')
        row = runner.summarize(task, [record])
        self.assertEqual((row['n_valid_xue'], row['n_failed_xue'], row['n_common_valid']), (1, 0, 1))
        # Enabling another consumer cannot affect our bootstrap on this fixed task.
        from common.statistic_calculator_517 import covariance_test
        from simulation.data_generation import simulate_one, make_rng
        data = simulate_one(task, 0)
        expected = covariance_test(data['Y'], B=task['B'], seed=make_rng(task, 0, 'bootstrap'))
        self.assertEqual((record['statistic'], record['critical_value'], record['pvalue']), expected)

    def test_missing_target_is_not_filled_from_sample_and_known_target_reaches_saved_output(self):
        self.assertTrue(hasattr(runner, 'run_xue_input'), 'complete Xue file input must be connected')
        scores = np.array([[0., 1.], [1., 3.], [2., 0.], [4., 2.]])
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'known.npz'
            np.savez(source, scores=scores, sigma0=np.eye(2), p=1, s=2)
            out = Path(folder) / 'output'
            result = runner.run_xue_input(source, out)
            self.assertEqual(result['method'], 'Xue-1S-EV')
            self.assertAlmostEqual(result['Q'], 361/259)
            self.assertFalse(result['reject'])
            saved = json.loads((out / 'xue_result.json').read_text(encoding='utf-8'))
            self.assertAlmostEqual(saved['p_value'], .379592195050727)
            self.assertEqual(saved['status'], 'ok')
            self.assertTrue((out / 'xue_summary.csv').is_file())
            with self.assertRaises(FileExistsError):
                runner.run_xue_input(source, out)
            missing = Path(folder) / 'missing.npz'
            np.savez(missing, scores=scores, p=1, s=2)
            with self.assertRaisesRegex(ValueError, 'target|sigma0'):
                runner.run_xue_input(missing, Path(folder) / 'missing_out')

    def test_failed_cross_test_is_saved_as_failure_and_never_counted_as_valid(self):
        task = dict(runner.load_config('smoke')['tasks'][0], with_xue=True)
        self.assertTrue(hasattr(runner, 'run_xue_cross_test'), 'audited cross entry must be used')
        failure = dict(method='Xue-1S-EV-cross-zero', status='degenerate_product_variance',
                       failure_reason='zero product variance at (0, 5)', reject=None,
                       p_value=None, pvalue=None)
        with tempfile.TemporaryDirectory() as folder, patch.object(runner, 'run_xue_cross_test', return_value=failure):
            with self.assertRaisesRegex(ValueError, 'degenerate_product_variance'):
                runner.run_tasks([task], folder)
            paths = list(Path(folder).glob('*/failure_*.json'))
            self.assertEqual(len(paths), 1)
            self.assertIn('zero product variance', paths[0].read_text())
            self.assertFalse((Path(folder) / 'all_experiments_results.csv').exists())

    def test_grid_target_is_shared_by_full_comparison_including_noise(self):
        from simulation.data_generation import simulate_one
        self.assertTrue(hasattr(runner, 'run_xue_input'))
        task = runner.load_config('smoke')['tasks'][0]
        data = simulate_one(task, 0)
        p, M = task['p'], task['M']
        gamma0 = np.einsum('jk,lh->jklh', np.eye(p), data['latent_time_kernel'])
        gamma0 += task['sigma_noise']**2 * np.einsum('jk,lh->jklh', np.eye(p), np.eye(M))
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'curves.npz'
            np.savez(source, Y=data['Y'], gamma0=gamma0, s=5,
                     grid=data['grid'], B=39)
            record = runner.run_xue_input(source, Path(folder) / 'out')
            self.assertEqual(record['method'], 'Xue-1S-EV')
            self.assertEqual(record['ours']['test_scope'], 'all')
            residual = data['Y'] - data['Y'].mean(axis=0)
            cov = np.einsum('rjl,rkh->jklh', residual, residual)/(task['n']-1)
            expected = np.sqrt(task['n'])*np.max(np.abs(cov-gamma0))
            self.assertAlmostEqual(record['ours']['statistic'], expected)


if __name__ == '__main__':
    unittest.main()
