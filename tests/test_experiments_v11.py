"""Configuration and persisted end-to-end contracts for task card 1."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


class ExperimentContracts(unittest.TestCase):
    def runner(self):
        self.assertIsNotNone(importlib.util.find_spec('simulation.covariance_experiments'),
                             'the production experiment driver must exist')
        from simulation import covariance_experiments
        return covariance_experiments

    def test_formal_grid_is_frozen_and_separate_from_smoke(self):
        runner = self.runner()
        formal = runner.load_config('formal')
        smoke = runner.load_config('smoke')
        self.assertEqual(len(formal['tasks']), 20)
        self.assertEqual(len(smoke['tasks']), 4)
        actual = {(t['model'], t['experiment'], t['n'], t['p'], t['s0'], t['delta'])
                  for t in formal['tasks']}
        expected = set()
        for model in ('M1', 'M2'):
            expected.update((model, 1, n, p, 0, 0.0)
                            for n in (500, 1000) for p in (10, 50))
            expected.update((model, 2, 500, 50, s, d)
                            for s in (4, 8) for d in (.205, .215))
            expected.update((model, 3, 500, p, 4, .235) for p in (50, 100))
        self.assertEqual(actual, expected)
        for t in formal['tasks']:
            self.assertEqual((t['M'], t['B'], t['n_repeats'], t['alpha']),
                             (30, 500, 100, .05))

    def test_saved_results_are_reproducible_and_resume_checks_configuration(self):
        runner = self.runner()
        task = dict(runner.load_config('smoke')['tasks'][0])
        with tempfile.TemporaryDirectory() as directory:
            first = runner.run_tasks([task], directory)
            files = list(Path(directory).glob('*/replicate_*.json'))
            self.assertEqual(len(files), 2)
            before = [p.read_bytes() for p in sorted(files)]
            again = runner.run_tasks([task], directory, resume=True)
            self.assertEqual(before, [p.read_bytes() for p in sorted(files)])
            self.assertEqual(first['all_results']['reject_rate'].tolist(),
                             again['all_results']['reject_rate'].tolist())
            record = json.loads(files[0].read_text(encoding='utf-8'))
            self.assertEqual(record['reject'], record['pvalue'] < task['alpha'])
            self.assertEqual(record['reject'], record['statistic'] > record['critical_value'])
            self.assertEqual(len(record['bootstrap_statistics']), task['B'])
            self.assertEqual(len(record['grid']), task['M'])
            self.assertEqual(record['task'], task)
            with self.assertRaises(FileExistsError):
                runner.run_tasks([task], directory)
            broken = dict(record, pvalue=.123456)
            files[0].write_text(json.dumps(broken), encoding='utf-8')
            with self.assertRaises(ValueError):
                runner.run_tasks([task], directory, resume=True)
            files[0].write_text('{}', encoding='utf-8')
            with self.assertRaises(ValueError):
                runner.run_tasks([task], directory, resume=True)

    def test_independent_two_sample_smoke_persists_unequal_group_sizes(self):
        runner = self.runner()
        tasks = runner.load_config('two_sample_smoke')['tasks']
        with tempfile.TemporaryDirectory() as directory:
            result = runner.run_tasks(tasks, directory)
            self.assertEqual(len(result['all_results']), len(tasks))
            self.assertEqual(result['all_results']['n_X'].tolist(), [20]*len(tasks))
            self.assertEqual(result['all_results']['n_Y'].tolist(), [28]*len(tasks))
            records = list(Path(directory).glob('*/replicate_*.json'))
            self.assertEqual(len(records), sum(t['n_repeats'] for t in tasks))
            record = json.loads(records[0].read_text(encoding='utf-8'))
            self.assertEqual((record['task']['n_X'], record['task']['n_Y']), (20, 28))
            self.assertEqual(record['test_kind'], 'independent_two_sample')

    def test_empty_selection_has_explicit_error_without_outputs(self):
        runner = self.runner()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'non-empty'):
                runner.run_tasks([], directory)
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
