"""Offline cluster orchestration and deployment safety contracts."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    path = ROOT / relative
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClusterTests(unittest.TestCase):
    def controller(self):
        module = load('task3_controller', 'cluster/task3/controller.py')
        self.assertIsNotNone(module, 'cluster controller must exist')
        return module

    def test_afterany_collection_and_success_gate(self):
        c = self.controller()
        config = dict(remote_project_dir='/project', account='xjh', partition='CMO_HPC',
                      bootstrap_memory_mb=8192, bootstrap_time_minutes=120,
                      control_memory_mb=2048, control_time_minutes=30,
                      skip_dimension_extension=False, worker_memory_limit_mb=8192, worker_time_limit_minutes=120)
        with tempfile.TemporaryDirectory() as tmp:
            commands=[]
            def submit(argv):
                commands.append(argv)
                return str(100+len(commands))
            c.submit_phase(config, Path('/release'), Path(tmp), 'pilot',
                           dict(array='0-124%8', memory_mb=1024, seconds_per_chunk=1800), submit)
            self.assertIn('--array=0-124%8', commands[0])
            self.assertIn('--dependency=afterany:101', commands[1])
            self.assertEqual(commands[1][-1], 'pilot')
            self.assertEqual(c.next_stage('pilot_collect', 'FAILED'), 'blocked')
            self.assertEqual(c.next_stage('pilot_collect', 'COMPLETED'), 'lock')
            self.assertEqual(c.next_stage('confirm_collect', 'COMPLETED'), 'done')

    def test_unknown_scheduler_state_and_missing_resource_fail_closed(self):
        c = self.controller()
        with self.assertRaises(ValueError):
            c.next_stage('pilot_collect', 'DISAPPEARED')
        with self.assertRaises(ValueError):
            c.validate_config(dict(remote_project_dir='/project', account='xjh', partition='CMO_HPC'))

    def test_controller_rejects_parent_directory_run_name(self):
        c=self.controller()
        config=dict(remote_project_dir='/project',account='xjh',partition='CMO_HPC',
                    bootstrap_memory_mb=8192,bootstrap_time_minutes=120,
                    control_memory_mb=2048,control_time_minutes=30,
                    worker_memory_limit_mb=8192,worker_time_limit_minutes=120,run_name='..')
        with self.assertRaises(ValueError):
            c.validate_config(config)

    def test_resume_validates_config_and_does_not_resubmit_live_job(self):
        c = self.controller()
        state=dict(config_hash='old', stage='benchmark', job_id='123')
        with self.assertRaises(ValueError):
            c.validate_resume(state, dict(account='changed'))
        self.assertFalse(c.finished('RUNNING'))
        self.assertTrue(c.finished('OUT_OF_MEMORY'))

    def test_package_hashes_actual_dirty_source_and_excludes_secrets(self):
        builder = load('task3_builder', 'tools/build_task3_package.py')
        self.assertIsNotNone(builder, 'package builder must exist')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source'; root.mkdir()
            for relative, data in [('common/a.py','changed = True'),
                                   ('simulation/configs/x.json','{}'),
                                   ('cluster/task3/run.slurm','#!/bin/bash'),
                                   ('common/__pycache__/x.py','no'),
                                   ('results/leak.json','no'),
                                   ('.ssh/id_rsa','secret'),
                                   ('cluster/task3/cluster_config.json','secret')]:
                path=root/relative; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(data)
            package=Path(tmp)/'p.zip'
            builder.build(root, package, git_info={'head':'abc','status_porcelain':' M common/a.py'})
            with zipfile.ZipFile(package) as archive:
                names=archive.namelist()
                self.assertIn('manifest.json',names); self.assertIn('SHA256SUMS',names)
                self.assertNotIn('.ssh/id_rsa',names); self.assertNotIn('results/leak.json',names)
                self.assertNotIn('common/__pycache__/x.py',names)
                self.assertNotIn('cluster/task3/cluster_config.json',names)
                manifest=json.loads(archive.read('manifest.json'))
                self.assertEqual(manifest['git']['status_porcelain'],' M common/a.py')
                self.assertIn('common/a.py',manifest['files'])
            self.assertTrue(package.with_suffix('.zip.sha256').exists())

    def test_controller_runs_full_pipeline_and_retains_failed_collection(self):
        from unittest.mock import patch
        from contextlib import nullcontext
        import hashlib
        c=self.controller()
        config=dict(remote_project_dir='/project',account='xjh',partition='CMO_HPC',
                    bootstrap_memory_mb=8192,bootstrap_time_minutes=120,
                    control_memory_mb=2048,control_time_minutes=30,
                    worker_memory_limit_mb=8192,worker_time_limit_minutes=120,
                    run_name='test',poll_seconds=0)
        with tempfile.TemporaryDirectory() as tmp:
            release=Path(tmp)/'release'; release.mkdir()
            (release/'manifest.json').write_text(json.dumps({'files':{}}))
            output=Path(tmp)/'results'; output.mkdir()
            for phase in ('pilot','confirm'):
                path=output/(phase+'_workers.json')
                path.write_text(json.dumps(dict(array='0-1%8',memory_mb=1024,seconds_per_chunk=1800)))
                path.with_suffix('.json.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest())
            submitted=[]; jobs={}; failed_once=[True]
            def fake(argv):
                if argv[0]=='sbatch':
                    job=str(100+len(submitted)); submitted.append(argv)
                    stage=argv[argv.index(str(release/'cluster/task3/run.slurm'))+3]
                    phase=argv[argv.index(str(release/'cluster/task3/run.slurm'))+4]
                    jobs[job]=(stage,phase)
                    return job
                if argv[0]=='squeue': return ''
                job=next(x.split('=',1)[1] for x in argv if x.startswith('--jobs='))
                stage,phase=jobs[job]
                fail=stage=='collect' and phase=='pilot' and failed_once[0]
                if fail: failed_once[0]=False
                return job+'|'+('FAILED|2:0' if fail else 'COMPLETED|0:0')
            with patch.object(c,'controller_lock',side_effect=lambda path:nullcontext()), patch.object(c,'command',side_effect=fake):
                with self.assertRaisesRegex(ValueError,'stage failed'):
                    c.run_controller(config,release,output)
                stages=[args[args.index(str(release/'cluster/task3/run.slurm'))+3] for args in submitted]
                self.assertNotIn('lock',stages)
                count=len(submitted)
                result=c.run_controller(config,release,output,resume=True)
            self.assertEqual(result['stage'],'done')
            self.assertGreater(len(submitted),count)
            self.assertEqual(sum(args.count('benchmark') for args in submitted),1)
            self.assertEqual(sum(args.count('lock') for args in submitted),1)

    def test_transfer_dryrun_never_calls_network(self):
        transfer=load('task3_transfer','cluster/task3/transfer.py')
        self.assertIsNotNone(transfer,'upload launcher must exist')
        config=json.loads((ROOT/'dist/cluster_config.example.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'config.json'; path.write_text(json.dumps(config))
            result=transfer.execute(path,'start',dry_run=True,runner=lambda *a,**k:self.fail('network called'))
            self.assertTrue(result['dry_run'])
            self.assertIn('ssh.host',result['missing'])

    @unittest.skipUnless(__import__('shutil').which('powershell'), 'Windows PowerShell required')
    def test_four_file_standalone_powershell_dryrun(self):
        import hashlib
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            script=directory/'submit_task3.ps1'
            shutil.copy2(ROOT/'dist/submit_task3.ps1',script)
            config=json.loads((ROOT/'dist/cluster_config.example.json').read_text())
            config['package_file']='package.zip'
            path=directory/'cluster_config.json'; path.write_text(json.dumps(config))
            package=directory/'package.zip'
            with zipfile.ZipFile(package,'w') as archive:
                archive.write(ROOT/'cluster/task3/transfer.py','cluster/task3/transfer.py')
            package.with_suffix('.zip.sha256').write_text(hashlib.sha256(package.read_bytes()).hexdigest())
            result=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),'-Config',str(path),'-DryRun'],
                                  text=True,capture_output=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue(json.loads(result.stdout)['dry_run'])
            invalid=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),'-Config',str(path),'-Action','nonsense'],
                                   text=True,capture_output=True,timeout=30)
            self.assertNotEqual(invalid.returncode,0)

    def test_slurm_script_lf_and_python39_syntax(self):
        import ast
        for folder in ('cluster/task3','tools'):
            for path in (ROOT/folder).glob('*.py'):
                ast.parse(path.read_text(encoding='utf-8'),feature_version=(3,9))
        run=ROOT/'cluster/task3/run.slurm'
        self.assertTrue(run.exists())
        self.assertNotIn(b'\r',run.read_bytes())
        self.assertIn('SLURM_ARRAY_TASK_ID',run.read_text())


if __name__ == '__main__':
    unittest.main()
