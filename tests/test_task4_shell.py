import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'dist/task4_batch.py'

class Task4ShellTests(unittest.TestCase):
    def test_startup_wait_releases_submit_lock_without_skipping_guard(self):
        h = self.helper()
        fake = SimpleNamespace(LOCK_EX=1, LOCK_NB=2,
            flock=__import__('unittest.mock', fromlist=['Mock']).Mock(side_effect=[BlockingIOError(), None]))
        with tempfile.TemporaryDirectory() as d, patch.dict('sys.modules', {'fcntl': fake}), patch.object(h.time, 'sleep'):
            with h.lock(Path(d)/'controller.lock', wait_seconds=10):
                pass
        self.assertEqual(fake.flock.call_count, 2)

    def test_status_includes_original_controller_error_without_network(self):
        h = self.helper()
        import io
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/'cluster_config.json').write_text(json.dumps({'remote_project_dir': d, 'run_name': 'test'}))
            (root/'controller.log').write_text('original controller failure')
            captured = io.StringIO()
            with patch('sys.stdout', captured), patch.object(h, 'command', side_effect=AssertionError('network')):
                h.status(root)
            self.assertIn('original controller failure', captured.getvalue())

    def helper(self):
        self.assertTrue(PATH.exists(), 'standalone batch helper missing')
        spec = importlib.util.spec_from_file_location('task4_batch_test', PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_budget_uses_existing_worker_ceiling(self):
        h=self.helper()
        self.assertEqual(h.budget(dict(worker_time_limit_minutes=30,worker_memory_limit_mb=4096)),(30,4096))

    def test_conflict_active_array_blocks(self):
        h=self.helper()
        with self.assertRaisesRegex(RuntimeError,'active'):
            h.check_jobs({'history':[{'job_id':'123'}]}, '123|RUNNING\n', '')

    def test_unknown_submission_blocks(self):
        h=self.helper()
        with self.assertRaisesRegex(RuntimeError,'unacknowledged'):
            h.check_jobs({'submission_intent':{'stage':'worker'}}, '', '')

    def test_terminal_old_job_needs_no_accounting(self):
        h=self.helper()
        h.check_jobs({'history':[{'job_id':'123'}]}, '124|RUNNING\n', '')

    def test_budget_pauses_and_rejects_unfit_chunk(self):
        h=self.helper()
        with self.assertRaisesRegex(RuntimeError,'budget'):
            h.can_start(200,100,120)
        self.assertFalse(h.can_start(50,40,120))
        self.assertTrue(h.can_start(90,100,120))

    def test_checkpoint_progress_skips_complete_chunks(self):
        h=self.helper()
        class F:
            @staticmethod
            def tasks_for(plan): return [({'scenario_id':'x'},0),({'scenario_id':'x'},1)]
            @staticmethod
            def record_path(root,phase,e,r): return root / ('%s.json'%r)
            @staticmethod
            def validate_record(record,*args): return record
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'0.json').write_text(json.dumps({'complete':True}))
            self.assertEqual(h.pending_chunks(F,root,'pilot',{},1),[1])

    def test_runner_fallback_confirm_and_resume(self):
        h=self.helper()
        calls=[]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'pilot_plan.json').write_text('{}')
            def worker(output,phase,chunk):
                calls.append((phase,chunk))
                (root/('%s_%s.json'%(phase,chunk))).write_text('{"complete":true}')
            def decision(output):
                phase='confirm' if (root/'fallback_0.json').exists() else 'fallback'
                return {'action':phase}
            w=SimpleNamespace(run_smoke=lambda r:None,
                load_plan=lambda r,p:{},benchmark=lambda r:{'measurements':[{'seconds':1,'peak_memory_mb':1}]},
                plan_workers=lambda *a:{'chunk_size':1},tasks_for=lambda p:[({'scenario_id':'x'},0)],
                record_path=lambda r,p,e,i:r/('%s_%s.json'%(p,i)),validate_record=lambda r,*a:r,
                run_worker=worker,collect=lambda r,p:{'complete':True},decide=decision,write_report=lambda r:None)
            modules={'simulation':SimpleNamespace(task4_experiments=w),'numpy':SimpleNamespace(__version__='2.0.2'),
                     'scipy':SimpleNamespace(__version__='1.13.1')}
            config={'worker_time_limit_minutes':30,'worker_memory_limit_mb':4096}
            with patch.object(h,'setup',return_value=(config,root,root,None)),patch.object(h,'lock',side_effect=lambda *a,**k:nullcontext()),patch.object(h,'guard'),patch.dict('os.environ',{'SLURM_JOB_ID':'123'}),patch.dict('sys.modules',modules),patch.object(h.sys,'version_info',(3,9,25)):
                h.execute(root)
                h.execute(root)
            self.assertEqual(calls,[('pilot',0),('fallback',0),('confirm',0)])
            self.assertEqual(json.loads((root/'batch_state.json').read_text())['stage'],'DONE')

    def test_malformed_queue_is_not_success(self):
        h=self.helper()
        with self.assertRaisesRegex(RuntimeError,'unrecognized'):
            h.check_jobs({},'not a queue row','')

    def test_spooled_sbatch_preserves_incoming_directory(self):
        h=self.helper()
        commands=[]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            config={'worker_time_limit_minutes':30,'worker_memory_limit_mb':4096,'account':'xjh','partition':'CMO_HPC'}
            with patch.object(h,'setup',return_value=(config,root,root,None)),patch.object(h,'lock',side_effect=lambda *a,**k:nullcontext()),patch.object(h,'guard'),patch.object(h,'command',side_effect=lambda argv:commands.append(argv) or '123'):
                h.submit(root)
            self.assertEqual(commands[0][-2:],['--run',str(root)])
            self.assertIn('--time=30',commands[0])
            self.assertNotIn('submission_intent',json.loads((root/'batch_state.json').read_text()))
