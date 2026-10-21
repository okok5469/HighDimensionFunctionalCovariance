"""Check relocated experiments against the pre-cleanup code backup."""
import importlib
from contextlib import chdir
import multiprocessing
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / '.planning/project-cleanup/original_code.zip'


def old_module(path, aliases=None):
    with zipfile.ZipFile(BACKUP) as backup:
        source = backup.read(path).decode('utf-8-sig')
    module = types.ModuleType('original_reference')
    with patch.dict(sys.modules, aliases or {}):
        exec(compile(source, path, 'exec'), module.__dict__)
    return module


class ProjectStructureTests(unittest.TestCase):
    def module(self, name):
        self.assertTrue((ROOT / name.split('.')[0] / '__init__.py').is_file(),
                        f'Missing experiment package: {name}')
        return importlib.import_module(name)

    def test_shared_statistics_match_original_fixed_seed_calculations(self):
        new = self.module('common.statistic_calculator_517')
        old = old_module('数值模拟/statistic_calculator_517.py')
        Y = np.random.default_rng(321).normal(size=(12, 4, 8))
        np.testing.assert_array_equal(new.covariance_test(Y, B=9, seed=123),
                                      old.covariance_test(Y, B=9, seed=123))

    def test_xue_preserves_har_and_simulation_probability_conventions(self):
        new = self.module('common.statistic_calculator_xue')
        helper = self.module('common.xue_helper')
        old_har = old_module('实证分析/statistic_calculator_xue.py')
        old_sim = old_module('数值模拟/statistic_calculator_xue.py')
        old_helper = old_module('数值模拟/xue_helper.py',
                                {'statistic_calculator_xue': old_sim})
        Y = np.random.default_rng(321).normal(size=(12, 4, 8))
        np.testing.assert_array_equal(helper.run_xue_test(Y, s=3),
                                      old_helper.run_xue_test(Y, s=3))
        coefficients = helper.project_to_fourier_basis(Y, 3)
        self.assertEqual(new.compute_Tn_xue(coefficients, s=3),
                         old_har.compute_Tn_xue(coefficients, s=3))
        for Tn in [-100.0, 0.0, 30.0, 100.0]:
            self.assertEqual(new.xue_pvalue(Tn), old_har.xue_pvalue(Tn))
            self.assertEqual(new.xue_pvalue(Tn, legacy=True), old_sim.xue_pvalue(Tn))

    def test_three_generators_keep_original_datasets(self):
        for suffix, function in [('one', 'create_dataset'),
                                 ('two', 'create_dataset_M1'),
                                 ('three', 'create_dataset_M3')]:
            with self.subTest(model=suffix):
                new = self.module(f'simulation.data_generator_{suffix}')
                old = old_module(f'数值模拟/data_generator_{suffix}.py')
                for h0 in [True, False]:
                    args = dict(n=8, p=4, M=8, h0=h0, s0=2,
                                signal_strength=0.2, seed=123)
                    if suffix == 'one':
                        args['q'] = 3
                    a, b = getattr(new, function)(**args), getattr(old, function)(**args)
                    np.testing.assert_array_equal(a['Y'], b['Y'])

    def test_har_reads_data_and_subsamples_from_unrelated_working_directory(self):
        main = self.module('empirical.Main_HAR_empirical')
        loader = self.module('empirical.har_data_loader')
        old = old_module('实证分析/har_data_loader.py')
        previous = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as directory, chdir(directory):
                for path in [main.CSV_PATH_H0, main.CSV_PATH_H1]:
                    frame = loader.load_har_static(path, verbose=False)
                    if 'subject' not in frame:
                        frame = frame.rename(columns={'sample_id': 'subject'})
                    # A real subject segment is enough to verify preprocessing.
                    subset = frame[frame['subject'] == frame['subject'].iloc[0]].head(80)
                    Y = loader.build_windows(subset, M=12, stride=12, q_smooth=3,
                                             verbose=False)
                    expected = old.build_windows(subset, M=12, stride=12, q_smooth=3,
                                                 verbose=False)
                    np.testing.assert_array_equal(Y, expected)
                    result = main.one_subsample_test(Y, n=4, p_indices=[0, 1, 2],
                                                     B=5, seed=42)
                    self.assertTrue(np.isfinite(result['Tn_boot']))
                    self.assertTrue(0 <= result['pval_xue'] <= 1)
                self.assertFalse(list(Path(directory).iterdir()))
        finally:
            os.chdir(previous)

    def test_simulation_saves_outside_working_directory(self):
        previous = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as directory, chdir(directory):
                for suffix in ['one', 'two', 'three']:
                    main = self.module(f'simulation.Main_{suffix}')
                    with patch.object(main, 'OUTPUT_DIR', Path(directory) / suffix):
                        main.save_partial_results([{'experiment': 1, 'n': 8}], 1)
                        self.assertTrue((Path(directory) / suffix /
                                         'experiment1_partial.csv').is_file())
                    self.assertTrue(main.__name__.startswith('simulation.'))
        finally:
            os.chdir(previous)

    def test_all_models_execute_small_tasks_under_windows_spawn(self):
        functions = []
        tasks = []
        for suffix in ['one', 'two', 'three']:
            main = self.module(f'simulation.Main_{suffix}')
            task = dict(main.create_experiment_tasks()[0])
            task.update(n=8, p=4, M=8, B=5, n_repeats=1)
            functions.append(main.execute_single_task)
            tasks.append(task)
        with multiprocessing.get_context('spawn').Pool(1) as pool:
            for function, task in zip(functions, tasks):
                result = pool.apply(function, (task,))
                self.assertNotIn('error', result)
                self.assertTrue(0 <= result['reject_rate'] <= 1)
                self.assertTrue(0 <= result['reject_rate_xue'] <= 1)

    def test_complete_simulation_workflows_write_all_three_experiments(self):
        with tempfile.TemporaryDirectory() as directory:
            for suffix in ['one', 'two', 'three']:
                main = self.module(f'simulation.Main_{suffix}')
                selected = {}
                for task in main.create_experiment_tasks():
                    small = dict(task)
                    small.update(n=8, p=4, M=8, B=5, n_repeats=1,
                                 s0=2, signal_strength=0.2)
                    if suffix == 'one':
                        small['q'] = 3
                    selected.setdefault(task['experiment'], small)
                output = Path(directory) / suffix
                with patch.object(main, 'OUTPUT_DIR', output), \
                     patch.object(main, 'USE_PARALLEL', False), \
                     patch.object(main, 'create_experiment_tasks',
                                  return_value=list(selected.values())):
                    summary = main.run_experiment()
                self.assertEqual(len(summary['all_results']), 3)
                self.assertTrue((output / 'all_experiments_results.csv').is_file())
                for number in [1, 2, 3]:
                    self.assertTrue((output / f'experiment{number}_results.csv').is_file())
                    self.assertTrue((output / f'experiment{number}_partial.csv').is_file())


if __name__ == '__main__':
    unittest.main()
