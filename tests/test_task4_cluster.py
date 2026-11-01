import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class Task4ClusterTests(unittest.TestCase):
    def test_scheduler_legacy_array_and_expired_job(self):
        c = module('task4_controller', 'cluster/task4/controller.py')
        calls = []
        def query(argv):
            calls.append(argv)
            return '4|RUNNING' if argv[0] == 'squeue' else '38349_0|COMPLETED|0:0\n38349_1|COMPLETED|0:0'
        self.assertEqual(c.job_state('38349', query), 'COMPLETED')
        self.assertNotIn('--array', calls[1])
        self.assertFalse(any(v.startswith('--jobs=') for v in calls[0]))
        self.assertEqual(c.job_state('4', query), 'RUNNING')
        with self.assertRaises(ValueError):
            c.job_state('38349', lambda argv: '')

    def test_finite_decision_transitions_and_seal(self):
        c = module('task4_controller', 'cluster/task4/controller.py')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root/'search_decision.json'
            for action, expected in [('fallback','plan_fallback'),('confirm','plan_confirm'),('done_no_eligible_candidates','done')]:
                payload = (json.dumps({'action': action})+'\n').encode()
                path.write_bytes(payload)
                import hashlib
                path.with_suffix('.json.sha256').write_text(hashlib.sha256(payload).hexdigest())
                self.assertEqual(c.decision_stage(root), expected)
            path.write_text('{}')
            with self.assertRaises(ValueError): c.decision_stage(root)
        self.assertEqual(c.NEXT['fallback_collect'], 'decision')

    def test_task4_routes_and_package(self):
        c = module('task4_controller', 'cluster/task4/controller.py')
        config = json.loads((ROOT/'cluster_config_task4.example.json').read_text())
        config.update(control_memory_mb=1000, control_time_minutes=30, worker_memory_limit_mb=1000, worker_time_limit_minutes=30)
        argv = c.sbatch_args(config, ROOT, Path('out'), 'worker', 'fallback',
                             {'memory_mb': 1, 'seconds_per_chunk': 60, 'array': '0-3%8'})
        self.assertIn(str(ROOT/'cluster/task4/run.slurm'), argv)
        self.assertIn('--array=0-3%8', argv)
        builder = module('task4_builder', 'tools/build_task4_package.py')
        names = {p.relative_to(ROOT).as_posix() for p in builder.files_for(ROOT)}
        self.assertIn('simulation/task4_experiments.py', names)
        self.assertIn('doc/task4_frozen_before.json', names)
        self.assertFalse(any('simulation/results/' in n for n in names))

    def test_fake_slurm_complete_fallback_resume_and_no_candidate(self):
        import hashlib
        from contextlib import nullcontext
        from unittest.mock import patch
        for fallback, confirm in [(False,True),(True,True),(True,False)]:
            with self.subTest(fallback=fallback,confirm=confirm), tempfile.TemporaryDirectory() as tmp:
                c=module('task4_controller','cluster/task4/controller.py')
                release=Path(tmp)/'release'; release.mkdir()
                (release/'manifest.json').write_text(json.dumps({'files':{}}))
                output=Path(tmp)/'results'; output.mkdir()
                config=dict(remote_project_dir='/project',account='xjh',partition='CMO_HPC',
                    bootstrap_memory_mb=1000,bootstrap_time_minutes=30,control_memory_mb=1000,
                    control_time_minutes=30,worker_memory_limit_mb=1000,worker_time_limit_minutes=30,
                    run_name='task4',poll_seconds=0)
                def sealed(name,value):
                    path=output/name; path.write_text(json.dumps(value))
                    path.with_suffix(path.suffix+'.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest())
                for phase in ('pilot','fallback','confirm'):
                    sealed(phase+'_workers.json',dict(array='0-1%8',memory_mb=10,seconds_per_chunk=60))
                submissions=[]; jobs={}; fail_once=[True]; decisions=[0]
                def fake(argv):
                    if argv[0]=='sbatch':
                        pos=argv.index(str(release/'cluster/task4/run.slurm'))
                        stage,phase=argv[pos+3:pos+5]
                        job=str(100+len(submissions)); submissions.append((stage,phase)); jobs[job]=(stage,phase)
                        if stage=='decision':
                            decisions[0]+=1
                            if fallback and decisions[0]==1:
                                sealed('fallback_trigger.json',dict(selection=dict(fallback_required=True)))
                            else:
                                sealed('search_decision.json',dict(action='confirm' if confirm else 'done_no_eligible_candidates'))
                        return job
                    if argv[0]=='squeue': return ''
                    job=next(v.split('=',1)[1] for v in argv if v.startswith('--jobs='))
                    stage,phase=jobs[job]
                    failed=stage=='collect' and phase=='pilot' and fail_once[0]
                    if failed: fail_once[0]=False
                    if stage=='collect' and not failed: sealed(phase+'_integrity.json',dict(complete=True))
                    return job+('|FAILED|2:0' if failed else '|COMPLETED|0:0')
                with patch.object(c,'controller_lock',side_effect=lambda path:nullcontext()), patch.object(c,'command',side_effect=fake):
                    with self.assertRaisesRegex(ValueError,'stage failed'):
                        c.run_controller(config,release,output)
                    self.assertNotIn(('decision','pilot'),submissions)
                    state=c.run_controller(config,release,output,resume=True)
                    self.assertEqual(state['stage'],'done')
                    count=len(submissions)
                    c.run_controller(config,release,output,resume=True)
                    self.assertEqual(len(submissions),count)
                self.assertEqual(submissions.count(('benchmark','pilot')),1)
                self.assertEqual(submissions.count(('worker','pilot')),2)
                self.assertEqual(submissions.count(('worker','fallback')),int(fallback))
                self.assertEqual(submissions.count(('worker','confirm')),int(confirm))
                state['submission_intent']={'stage':'worker'}
                with self.assertRaisesRegex(ValueError,'acknowledgement'):
                    c.validate_resume(state,config)

    def test_transfer_dryrun_and_slurm_lf(self):
        t=module('task4_transfer','cluster/task4/transfer.py')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'config.json'
            path.write_bytes((ROOT/'cluster_config_task4.example.json').read_bytes())
            result=t.execute(path,dry_run=True,runner=lambda *a:self.fail('network'))
            self.assertIn('ssh.host',result['missing'])
        self.assertNotIn(b'\r',(ROOT/'cluster/task4/run.slurm').read_bytes())

    def test_standalone_powershell_dryrun(self):
        import hashlib
        import shutil
        import subprocess
        import zipfile
        if not shutil.which('powershell'): self.skipTest('Windows PowerShell required')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            shutil.copy2(ROOT/'dist/submit_task4.ps1',root/'submit_task4.ps1')
            config=json.loads((ROOT/'cluster_config_task4.example.json').read_text())
            config['package_file']='package.zip'
            (root/'config.json').write_text(json.dumps(config))
            package=root/'package.zip'
            with zipfile.ZipFile(package,'w') as archive:
                archive.write(ROOT/'cluster/task4/transfer.py','cluster/task4/transfer.py')
            package.with_suffix('.zip.sha256').write_text(hashlib.sha256(package.read_bytes()).hexdigest())
            result=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',
                str(root/'submit_task4.ps1'),'-Config',str(root/'config.json'),'-DryRun'],
                text=True,capture_output=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue(json.loads(result.stdout)['dry_run'])

    def test_package_and_workflow_identical_implementation_identity(self):
        import zipfile
        from simulation.task4_experiments import source_manifest
        builder=module('task4_builder','tools/build_task4_package.py')
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/'task4.zip'
            builder.build(ROOT,package,git_info={'head':'offline','status_porcelain':'offline'})
            with zipfile.ZipFile(package) as archive:
                manifest=json.loads(archive.read('manifest.json'))
            self.assertEqual(manifest['source_manifest'],source_manifest())


if __name__ == '__main__': unittest.main()
