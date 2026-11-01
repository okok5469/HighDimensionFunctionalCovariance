"""Task5 deployment, measured resource gates and finite Slurm orchestration."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location('task5_' + name, ROOT / ('cluster/task5/' + name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def package(directory):
    archive = directory / 'package.zip'
    payload = {'中文/模型.py': b'example', 'source.py': b'source'}
    payload['manifest.json'] = json.dumps({'files': {k: hashlib.sha256(v).hexdigest() for k, v in payload.items()}}).encode()
    payload['SHA256SUMS'] = ''.join(hashlib.sha256(v).hexdigest() + '  ' + k + '\n' for k, v in payload.items()).encode()
    with zipfile.ZipFile(archive, 'w') as output:
        for key, value in payload.items(): output.writestr(key, value)
    archive.with_suffix('.zip.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + '  package.zip\n')
    return archive, payload


class Task5ClusterTests(unittest.TestCase):
    def config(self):
        config = json.loads((ROOT / 'cluster_config_task5.example.json').read_text())
        config.update(bootstrap_memory_mb=10000, bootstrap_time_minutes=120,
                      control_memory_mb=1000, control_time_minutes=20,
                      worker_memory_limit_mb=10000, worker_time_limit_minutes=120)
        return config

    def measurements(self):
        return {'small': False, 'implementation_hash': 'identity', 'measurements': [
            dict(n=n, p=p, B=500, seconds=seconds, peak_memory_mb=200)
            for n, p, seconds in [(200, 20, 1), (400, 20, 2), (800, 20, 4), (800, 50, 10)] for _ in range(2)]}

    def test_deploy_verifies_all_bytes_before_creating_missing_members(self):
        deploy = module('deploy')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); archive, payload = package(root); release = root / 'release'
            deploy.deploy(archive, archive.with_suffix('.zip.sha256'), release)
            self.assertEqual((release / '中文/模型.py').read_bytes(), b'example')
            (release / 'source.py').unlink()
            deploy.deploy(archive, archive.with_suffix('.zip.sha256'), release)
            self.assertEqual((release / 'source.py').read_bytes(), b'source')
            (release / 'source.py').unlink()
            (release / '中文/模型.py').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'differs'):
                deploy.deploy(archive, archive.with_suffix('.zip.sha256'), release)
            self.assertFalse((release / 'source.py').exists())

    def test_config_unknowns_and_dryrun_never_contact_cluster(self):
        transfer = module('transfer')
        result = transfer.execute(ROOT / 'cluster_config_task5.example.json', dry_run=True,
                                  runner=lambda argv: self.fail('network'))
        self.assertIn('ssh.host', result['missing'])
        self.assertIn('bootstrap_memory_mb', result['missing'])
        self.assertIn('8 production benchmarks B500', result['stages'])
        self.assertNotIn('nohup', (ROOT / 'cluster/task5/transfer.py').read_text())

    def test_full_b500_measurements_required_and_separate_shape_estimates(self):
        c = module('controller'); measurements = self.measurements()
        values = c.measurement_table(measurements, 'identity')
        self.assertEqual(values[(800, 50)]['seconds'], 10)
        for bad in [dict(measurements, small=True), dict(measurements, measurements=measurements['measurements'][:-1]),
                    dict(measurements, implementation_hash='other')]:
            with self.assertRaises(ValueError): c.measurement_table(bad, 'identity')
        measurements['measurements'][0]['B'] = 3
        with self.assertRaises(ValueError): c.measurement_table(measurements, 'identity')

    def test_resource_overrun_blocks_without_shrinking_statistical_plan(self):
        c = module('controller'); config = self.config()
        values = c.measurement_table(self.measurements(), 'identity')
        plan = {'implementation_hash': 'identity', 'scenarios': [
            {'scenario': {'n': 800, 'p': 50}, 'repeats': 2},
            {'scenario': {'n': 200, 'p': 20}, 'repeats': 3}]}
        estimate = c.resource_estimate(plan, values, config)
        self.assertAlmostEqual(estimate['worker_hours'], 23 / 3600)
        config['worker_memory_limit_mb'] = 100
        with self.assertRaisesRegex(ValueError, 'memory'): c.resource_estimate(plan, values, config)
        config = self.config(); values[(800, 50)]['seconds'] = 5000
        with self.assertRaisesRegex(ValueError, 'time'): c.resource_estimate(plan, values, config)

    def test_scheduler_uses_afterany_and_compute_environment(self):
        c = module('controller'); config = self.config()
        args = c.sbatch_args(config, Path('/release'), Path('/out'), 'advance', dependency='123')
        self.assertIn('--dependency=afterany:123', args)
        self.assertIn(str(Path('/release') / 'cluster/task5/run.slurm'), args)
        args = c.sbatch_args(config, Path('/release'), Path('/out'), 'worker',
                             mapping={'memory_mb': 1000, 'minutes': 20, 'workers': [[0], [1]]})
        self.assertIn('--array=0-1%8', args)
        self.assertNotIn(b'\r', (ROOT / 'cluster/task5/run.slurm').read_bytes())
        script = (ROOT / 'cluster/task5/run.slurm').read_text()
        self.assertIn('3, 9, 25', script)
        self.assertIn('2.0.2', script)
        self.assertIn('1.13.1', script)

    def test_scheduler_expired_jobs_and_unknown_states(self):
        c = module('controller')
        def query(argv):
            return '' if argv[0] == 'squeue' else '123_0|COMPLETED|0:0\n123_1|COMPLETED|0:0'
        self.assertEqual(c.job_state('123', query), 'COMPLETED')
        with self.assertRaises(ValueError): c.job_state('123', lambda argv: '')

    def test_finite_graph_multiple_waves_failure_resume_and_done_is_idempotent(self):
        from contextlib import nullcontext
        from types import SimpleNamespace
        from unittest.mock import patch
        from simulation import task3_io as io
        c = module('controller')
        config = self.config(); config['seconds_per_chunk'] = 1
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); release = root / 'release'; release.mkdir()
            (release / 'manifest.json').write_text(json.dumps({'files': {}}))
            output = root / 'results'
            environment = {'python': 'test'}; fingerprint = io.digest(environment)
            measurements = self.measurements()
            measurements['environment_hash'] = fingerprint
            for row in measurements['measurements']: row['environment_hash'] = fingerprint
            plans = {phase: dict(phase=phase, run_id=phase, implementation_hash='identity', scenarios=[
                dict(scenario={'n': 200, 'p': 20}, scenario_id=phase, repeats=repeats)])
                for phase, repeats in [('pilot', 513), ('confirm', 2)]}
            submissions = []; jobs = {}; attempted = []; benchmarks = []
            def tasklist(plan):
                return [(plan['scenarios'][0], index) for index in range(plan['scenarios'][0]['repeats'])]
            def record_path(directory, phase, entry, replicate):
                return directory / phase / ('r%s.json' % replicate)
            def worker(directory, phase, index, chunk_size, retry_failures):
                attempted.append((phase, index, retry_failures))
                io.atomic_json(record_path(directory, phase, {}, index),
                               dict(complete=(retry_failures or phase != 'pilot' or index != 0)))
            def initialize(directory):
                io.write_sealed(directory / 'pilot_plan.json', plans['pilot'])
            def benchmark(directory):
                benchmarks.append(True); io.write_sealed(directory / 'benchmark/production.json', measurements)
            def decide(directory):
                io.write_sealed(directory / 'confirm_plan.json', plans['confirm'])
            fake_io = SimpleNamespace(write_sealed=io.write_sealed, read_sealed=io.read_sealed,
                                      digest=io.digest, environment=lambda: environment)
            work = SimpleNamespace(io=fake_io, tasks_for=tasklist, record_path=record_path,
                validate_record=lambda record, *args: record, run_worker=worker,
                load_plan=lambda directory, phase: io.read_sealed(directory / (phase + '_plan.json')),
                initialize=initialize, run_smoke=lambda directory: None, benchmark=benchmark,
                collect=lambda directory, phase: {'complete': not c.pending(work, directory, phase, plans[phase])},
                decide=decide, write_report=lambda directory: None)
            def scheduler(argv):
                if argv[0] == 'sbatch':
                    job = str(100 + len(submissions)); stage = argv[-1]
                    submissions.append((job, stage)); jobs[job] = 'COMPLETED'
                    return job
                if argv[0] == 'squeue': return ''
                job = next(arg.split('=', 1)[1] for arg in argv if arg.startswith('--jobs='))
                return job + '|' + jobs[job] + ('|0:0' if jobs[job] == 'COMPLETED' else '|1:0')
            with patch.object(c, 'lock', side_effect=lambda path: nullcontext()), \
                    patch.object(c, 'workflow', return_value=work), patch.object(c, 'command', side_effect=scheduler):
                c.start(config, release, output)
                state = c.read(output / 'controller_state.json')
                with patch.dict('os.environ', SLURM_JOB_ID=state['job_id']):
                    c.execute_stage(release, output, 'bootstrap')
                with patch.dict('os.environ', SLURM_JOB_ID=state['advance_job_id']):
                    c.execute_stage(release, output, 'advance')
                state = c.read(output / 'controller_state.json')
                with patch.dict('os.environ', SLURM_JOB_ID=state['job_id'], SLURM_ARRAY_JOB_ID=state['job_id'], SLURM_ARRAY_TASK_ID='0'):
                    with self.assertRaisesRegex(RuntimeError, 'method failure'):
                        c.execute_stage(release, output, 'worker')
                jobs[state['job_id']] = 'FAILED'
                with patch.dict('os.environ', SLURM_JOB_ID=state['advance_job_id']):
                    with self.assertRaisesRegex(RuntimeError, 'predecessor'):
                        c.execute_stage(release, output, 'advance')
                self.assertEqual(c.read(output / 'controller_state.json')['stage'], 'BLOCKED')
                self.assertFalse((output / 'confirm_plan.json').exists())
                c.start(config, release, output, resume=True)
                waves = 0
                while c.read(output / 'controller_state.json')['stage'] != 'DONE':
                    state = c.read(output / 'controller_state.json'); waves += 1
                    mapping = io.read_sealed(output / state['wave_file'])
                    for index in range(len(mapping['workers'])):
                        with patch.dict('os.environ', SLURM_JOB_ID=state['job_id'], SLURM_ARRAY_JOB_ID=state['job_id'], SLURM_ARRAY_TASK_ID=str(index)):
                            c.execute_stage(release, output, 'worker')
                    with patch.dict('os.environ', SLURM_JOB_ID=state['advance_job_id']):
                        c.execute_stage(release, output, 'advance')
                self.assertEqual(waves, 3)
                count = len(submissions)
                c.start(config, release, output, resume=True)
                self.assertEqual(len(submissions), count)
                self.assertEqual(len(benchmarks), 1)
                self.assertTrue((output / 'DONE.json').exists())
                self.assertEqual(sum(phase == 'pilot' and index == 0 for phase, index, retry in attempted), 2)
                self.assertTrue(any('--dependency=afterany:' in value for value in
                    c.read(output / 'controller_state.json')['history'][1]['argv']))

    def test_cached_measurements_cannot_cross_runtime_environment(self):
        c = module('controller'); measurements = self.measurements()
        measurements['environment_hash'] = 'old'
        with self.assertRaisesRegex(ValueError, 'environment'):
            c.measurement_table(measurements, 'identity', 'current')

    def test_bash_and_powershell_parameter_contract(self):
        import shutil
        shell = ROOT / 'dist/task5_submit.sh'
        self.assertNotIn(b'\r', shell.read_bytes())
        bash = Path('C:/Program Files/Git/bin/bash.exe')
        executable = str(bash) if bash.is_file() else shutil.which('bash')
        if executable:
            subprocess.run([executable, '-n', str(shell)], check=True, capture_output=True)
        if not shutil.which('powershell'): return
        result = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
            str(ROOT / 'dist/submit_task5.ps1'), '-Config', str(ROOT / 'cluster_config_task5.example.json'), '-DryRun'],
            text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)['dry_run'])


if __name__ == '__main__': unittest.main()
