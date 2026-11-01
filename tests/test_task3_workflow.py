"""Task3 provenance, immutable plans and actual shared-input execution."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np

from simulation import task3_experiments as workflow
from simulation import task3_io as storage


class WorkflowTests(unittest.TestCase):
    def test_eight_workers_wait_for_shared_environment_lock(self):
        """Cluster regression: initialization contention must not drop chunks."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = workflow.create_plan('smoke')
            plan['scenarios'] = plan['scenarios'][:1]
            plan['scenarios'][0]['repeats'] = 8
            plan['B'] = 3
            plan = workflow.seal_plan(plan)
            workflow.save_plan(root, plan)
            script = '\n'.join([
                'import sys', 'from pathlib import Path',
                'from simulation.task3_experiments import run_worker',
                'Path(sys.argv[3]).write_text("ready")',
                'run_worker(sys.argv[1], "smoke", int(sys.argv[2]), chunk_size=1)',
            ])
            environment = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
                               MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', BLIS_NUM_THREADS='1')
            children = []
            try:
                with storage.record_lock(root/'environment.lock'):
                    for index in range(8):
                        children.append(subprocess.Popen(
                            [sys.executable, '-c', script, str(root), str(index), str(root/('ready%d' % index))],
                            cwd=Path(__file__).resolve().parents[1], env=environment,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
                    deadline = time.monotonic() + 25
                    while len(list(root.glob('ready*'))) < 8 and time.monotonic() < deadline:
                        time.sleep(.05)
                    self.assertEqual(len(list(root.glob('ready*'))), 8)
                    time.sleep(.3)
                    self.assertTrue(all(child.poll() is None for child in children),
                                    'environment lock contention killed a worker before any computation')
                for child in children:
                    stdout, stderr = child.communicate(timeout=30)
                    self.assertEqual(child.returncode, 0, stdout + stderr)
                records = list((root/'smoke'/'replicates').glob('*.json'))
                self.assertEqual(len(records), 8)
            finally:
                for child in children:
                    if child.poll() is None:
                        child.kill()
                    child.communicate()

    def test_worker_budget_scales_to_slow_complete_repetition(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = workflow.create_plan('pilot', skip_dimension_extension=True)
            workflow.save_plan(tmp, plan)
            storage.write_sealed(Path(tmp)/'benchmark'/'production.json',
                                 dict(small=False, implementation_hash=plan['implementation_hash'],
                                      measurements=[dict(n=200, p=20, M=64, B=500,
                                                         seconds=1200., peak_memory_mb=100.)]))
            mapping = workflow.plan_workers(tmp, 'pilot', seconds_per_chunk=1800)
            self.assertEqual(mapping['chunk_size'], 1)
            self.assertEqual(mapping['seconds_per_chunk'], 2400)
            self.assertEqual(mapping['chunks'], 1250)
            self.assertAlmostEqual(mapping['worker_hours_estimate'], 1250*1200/3600)

    def test_resource_measurement_returns_actual_process_peak(self):
        self.assertGreater(workflow.peak_memory_mb(), 0.)

    def test_collection_reports_changed_implementation_as_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = workflow.create_plan('smoke')
            plan['scenarios'] = plan['scenarios'][:1]
            plan['scenarios'][0]['repeats'] = 1
            plan = workflow.seal_plan(plan)
            workflow.save_plan(tmp, plan)
            with patch.object(storage, 'source_manifest', return_value={'changed': 'bytes'}):
                integrity = workflow.collect(tmp, 'smoke')
            self.assertFalse(integrity['complete'])
            self.assertIn('source_manifest_mismatch', [f['reason'] for f in integrity['failures']])

    def test_generation_failure_is_a_failed_repeat_with_stable_key(self):
        from simulation.task3_generators import make_scenario, data_key
        scenario = make_scenario('band_head', .3, n=12, p=4)
        with patch('simulation.task3_generators.generate', side_effect=ValueError('bad innovations')):
            record = workflow.run_replicate(scenario, 'smoke', 2, B=3)
        self.assertFalse(record['complete'])
        self.assertEqual(record['data_id'], storage.digest(data_key(scenario, 'smoke', 2)))
        self.assertEqual(set(record['methods']), {'ours', 'xue_s5', 'xue_s11', 'xue_s21'})
        self.assertTrue(all(m['reject'] is None for m in record['methods'].values()))

    def test_complete_record_requires_all_four_real_methods(self):
        plan = workflow.create_plan('smoke')
        entry = plan['scenarios'][0]
        from simulation.task3_generators import data_key
        broken = dict(run_id=plan['run_id'], implementation_hash=plan['implementation_hash'],
                      methods_config=plan['methods'], phase='smoke', replicate=0,
                      scenario_id=entry['scenario_id'], scenario=entry['scenario'],
                      data_id=storage.digest(data_key(entry['scenario'], 'smoke', 0)),
                      data_sha256='a', gamma0_sha256='b', methods={}, complete=True)
        broken['record_sha256'] = storage.digest(broken)
        with self.assertRaises(ValueError):
            workflow.validate_record(broken, plan, entry, 0)

    def test_os_lock_is_exclusive_and_released_after_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / 'record.lock'
            with self.assertRaises(RuntimeError):
                with storage.record_lock(lock):
                    with self.assertRaises((OSError, BlockingIOError)):
                        with storage.record_lock(lock):
                            self.fail('concurrent writer acquired the same record')
                    raise RuntimeError('interrupted operation')
            with storage.record_lock(lock):
                pass

    def test_method_failure_keeps_other_methods_and_never_fabricates_decision(self):
        from simulation.task3_generators import make_scenario
        with patch.object(workflow, 'covariance_one_sample', side_effect=ValueError('audit failure')):
            record = workflow.run_replicate(make_scenario('local_fejer', 0., n=12, p=4),
                                            'smoke', 0, B=3)
        self.assertFalse(record['complete'])
        self.assertIsNone(record['methods']['ours']['reject'])
        self.assertEqual(record['methods']['xue_s21']['status'], 'ok')

    def test_pilot_matrix_and_separate_ids(self):
        plan = workflow.create_plan('pilot')
        self.assertEqual(len(plan['scenarios']), 25)
        self.assertEqual(sum(x['repeats'] for x in plan['scenarios']), 1250)
        self.assertEqual(plan['methods']['xue_s'], [5, 11, 21])
        self.assertEqual(plan['B'], 500)
        nulls = [x for x in plan['scenarios'] if x['scenario']['tau'] == 0]
        self.assertEqual(len(nulls), 5)

    def test_sealed_plan_and_record_detect_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'plan.json'
            storage.write_sealed(path, {'a': 1})
            storage.write_sealed(path, {'a': 1})
            with self.assertRaises(ValueError):
                storage.write_sealed(path, {'a': 2})
            path.write_text('{"a":2}', encoding='utf-8')
            with self.assertRaises(ValueError):
                storage.read_sealed(path)

    def test_actual_shared_input_and_replay(self):
        from simulation.task3_generators import make_scenario
        scenario = make_scenario('band_tail', .15, n=12, p=4)
        first = workflow.run_replicate(scenario, 'smoke', 0, B=3)
        second = workflow.run_replicate(scenario, 'smoke', 0, B=3,
                                         method_order=('xue_s21', 'xue_s5', 'ours', 'xue_s11'))
        self.assertTrue(first['complete'])
        self.assertEqual(first['data_id'], second['data_id'])
        for method in first['methods']:
            self.assertEqual(first['methods'][method]['data_sha256'], first['data_sha256'])
            self.assertEqual(first['methods'][method]['gamma0_sha256'], first['gamma0_sha256'])
            self.assertEqual(first['methods'][method]['reject'], second['methods'][method]['reject'])
        np.testing.assert_allclose(first['methods']['ours']['bootstrap_statistics'],
                                   second['methods']['ours']['bootstrap_statistics'], atol=0, rtol=0)
        self.assertEqual(len(first['methods']['ours']['bootstrap_statistics']), 3)
        self.assertNotEqual(first['data_id'], workflow.run_replicate(scenario, 'pilot', 0, B=3)['data_id'])

    def test_resume_and_missing_records_are_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = workflow.create_plan('smoke')
            plan['scenarios'] = plan['scenarios'][:1]
            plan['scenarios'][0]['repeats'] = 1
            plan['B'] = 3
            plan = workflow.seal_plan(plan)
            root = Path(tmp)
            workflow.save_plan(root, plan)
            self.assertFalse(workflow.collect(root, 'smoke')['complete'])
            workflow.run_worker(root, 'smoke', 0, chunk_size=1)
            self.assertTrue(workflow.collect(root, 'smoke')['complete'])
            record_path = next((root / 'smoke' / 'replicates').glob('*.json'))
            before = record_path.read_bytes()
            workflow.run_worker(root, 'smoke', 0, chunk_size=1)
            self.assertEqual(before, record_path.read_bytes())
            record = json.loads(before)
            record['implementation_hash'] = 'corrupt'
            record_path.write_text(json.dumps(record), encoding='utf-8')
            with self.assertRaises(ValueError):
                workflow.run_worker(root, 'smoke', 0, chunk_size=1)


if __name__ == '__main__':
    unittest.main()
