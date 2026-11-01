"""Offline recovery contracts; no cluster or numerical work is performed."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import nullcontext
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


class SerialRecoveryTests(unittest.TestCase):
    def test_expired_job_is_checked_without_squeue_job_filter(self):
        m = self.module()
        controller = m.load_controller(ROOT)
        calls = []
        def query(argv):
            calls.append(argv)
            if argv[0] == 'squeue':
                self.assertFalse(any(arg.startswith('--jobs') for arg in argv))
                return '99999|RUNNING\n'
            self.assertIn('JobID', ' '.join(argv))
            self.assertNotIn('JobIDRaw', ' '.join(argv))
            self.assertNotIn('--array', argv, 'older sacct does not support this option')
            return '38349_0|COMPLETED|0:0\n38349_1|FAILED|1:0\n'
        self.assertEqual(m.scheduler_state('38349', controller, query), 'FAILED')
        self.assertEqual([argv[0] for argv in calls], ['squeue', 'sacct'])

    def test_live_array_prevents_accounting_completion(self):
        m = self.module()
        controller = m.load_controller(ROOT)
        def query(argv):
            self.assertEqual(argv[0], 'squeue')
            return '38349|RUNNING\n38349|PENDING\n'
        self.assertEqual(m.scheduler_state('38349', controller, query), 'RUNNING')

    def test_scheduler_query_error_preserves_stderr_and_stops(self):
        m = self.module()
        with patch.object(m.subprocess, 'run', return_value=SimpleNamespace(
                returncode=1, stdout='', stderr='Slurm controller unavailable')):
            with self.assertRaisesRegex(RuntimeError, 'Slurm controller unavailable'):
                m.scheduler_query(['squeue', '--noheader'])

    def test_missing_accounting_never_assumes_finished(self):
        m = self.module()
        controller = m.load_controller(ROOT)
        with self.assertRaisesRegex(ValueError, 'accounting'):
            m.scheduler_state('38349', controller, lambda argv: '')

    def module(self):
        path = ROOT / 'tools/task3_serial_recovery.py'
        self.assertTrue(path.exists(), 'standalone recovery tool must exist')
        spec = importlib.util.spec_from_file_location('serial_recovery', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self, tmp):
        release = Path(tmp) / 'release'
        path = release / 'cluster/task3/controller.py'
        path.parent.mkdir(parents=True)
        path.write_bytes((ROOT / 'cluster/task3/controller.py').read_bytes())
        files = {'cluster/task3/controller.py': hashlib.sha256(path.read_bytes()).hexdigest()}
        (release / 'manifest.json').write_text(json.dumps({'files': files}))
        config = dict(remote_project_dir=str(Path(tmp).as_posix()), run_name='test',
                      account='xjh', partition='CMO_HPC', bootstrap_memory_mb=100,
                      bootstrap_time_minutes=10, control_memory_mb=100,
                      control_time_minutes=10, worker_memory_limit_mb=100,
                      worker_time_limit_minutes=60, array_concurrency=8)
        # Slurm configuration requires a POSIX absolute project path on Windows too.
        module = self.module()
        c = module.load_controller(release)
        module.scheduler_state = lambda job_id, controller: controller.job_state(job_id)
        c.validate_config = lambda value: value
        c.controller_lock = lambda path: nullcontext()
        config_path = Path(tmp) / 'config.json'
        config_path.write_text(json.dumps(config))
        output = Path(config['remote_project_dir']) / 'results/task3_v1/test'
        output.mkdir(parents=True)
        state = dict(stage='blocked', blocked_stage='pilot_workers',
                     release_manifest_sha256=hashlib.sha256((release/'manifest.json').read_bytes()).hexdigest(),
                     config_hash=c.config_hash(config), history=[dict(stage='pilot_workers',job_id='7'),
                                                               dict(stage='pilot_collect',job_id='8')])
        (output / 'controller_state.json').write_text(json.dumps(state))
        mapping = dict(run_id='old', array='0-124%8', chunk_size=10,
                       memory_mb=100, seconds_per_chunk=1800)
        for phase in ('pilot', 'confirm'):
            target = output / (phase + '_workers.json')
            target.write_text(json.dumps(mapping))
            target.with_suffix('.json.sha256').write_text(hashlib.sha256(target.read_bytes()).hexdigest())
        return module, c, release, config_path, output

    def test_dry_run_submits_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            m,c,r,p,o = self.fixture(tmp)
            c.command = lambda argv: self.fail('dry run submitted')
            before = {x.name: x.read_bytes() for x in o.iterdir()}
            result = m.recover(r,p,dry_run=True,controller=c)
            self.assertEqual(result['scheduling_override'], {'array_concurrency':1})
            self.assertEqual(before,{x.name:x.read_bytes() for x in o.iterdir()})

    def test_success_uses_serial_arrays_and_preserves_originals(self):
        with tempfile.TemporaryDirectory() as tmp:
            m,c,r,p,o = self.fixture(tmp)
            original = (p.read_bytes(),(o/'controller_state.json').read_bytes())
            commands=[]
            def submit(argv):
                commands.append(argv)
                return str(100+len(commands))
            c.command=submit
            c.job_state=lambda job:'COMPLETED'
            result=m.recover(r,p,controller=c,pause=lambda seconds:None)
            self.assertEqual(result['stage'],'done')
            arrays=[a for argv in commands for a in argv if a.startswith('--array=')]
            self.assertEqual(arrays,['--array=0-124%1','--array=0-124%1'])
            self.assertIn('--dependency=afterany:101',commands[1])
            self.assertIn('--dependency=afterany:105',commands[5])
            self.assertEqual(original,(p.read_bytes(),(o/'controller_state.json').read_bytes()))

    def test_failed_collect_never_locks_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            m,c,r,p,o=self.fixture(tmp)
            commands=[]
            def submit(argv):
                commands.append(argv)
                return str(100+len(commands))
            c.command=submit
            c.job_state=lambda job:'FAILED' if job=='102' else 'COMPLETED'
            with self.assertRaisesRegex(ValueError,'pilot_collect'):
                m.recover(r,p,controller=c,pause=lambda seconds:None)
            self.assertEqual(len(commands),2)
            state=json.loads((o/'serial_recovery_state.json').read_text())
            self.assertEqual(state['stage'],'blocked')

    def test_uncertain_acknowledgement_stops_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            m,c,r,p,o=self.fixture(tmp)
            c.job_state=lambda job:'COMPLETED'
            def interrupted(argv):
                raise RuntimeError('lost acknowledgement')
            c.command=interrupted
            with self.assertRaises(RuntimeError):
                m.recover(r,p,controller=c)
            with self.assertRaisesRegex(ValueError,'acknowledgement'):
                m.recover(r,p,resume=True,controller=c)

    def test_live_old_worker_prevents_submission(self):
        with tempfile.TemporaryDirectory() as tmp:
            m,c,r,p,o=self.fixture(tmp)
            c.job_state=lambda job:'RUNNING'
            c.command=lambda argv:self.fail('submitted while old worker active')
            with self.assertRaisesRegex(ValueError,'active'):
                m.recover(r,p,controller=c)
            self.assertFalse((o/'serial_recovery_state.json').exists())

    def test_resume_keeps_acknowledged_collect_and_does_not_duplicate_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            m,c,r,p,o=self.fixture(tmp)
            commands=[]
            def submit(argv):
                commands.append(argv)
                return str(100+len(commands))
            c.command=submit
            c.job_state=lambda job:'RUNNING' if job=='102' else 'COMPLETED'
            def interrupted_wait(seconds):
                raise RuntimeError('controller stopped')
            with self.assertRaises(RuntimeError):
                m.recover(r,p,controller=c,pause=interrupted_wait)
            self.assertEqual(len(commands),2)
            c.job_state=lambda job:'COMPLETED'
            result=m.recover(r,p,resume=True,controller=c,pause=lambda seconds:None)
            self.assertEqual(result['stage'],'done')
            self.assertEqual(len(commands),6)

    def test_changed_frozen_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            m,c,r,p,o=self.fixture(tmp)
            path=r/'cluster/task3/controller.py'
            path.write_bytes(path.read_bytes()+b'\n# changed\n')
            with self.assertRaisesRegex(ValueError,'release file differs'):
                m.recover(r,p,dry_run=True,controller=c)


if __name__=='__main__':
    unittest.main()
