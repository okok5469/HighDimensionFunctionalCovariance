"""Task5 release membership, immutable bytes, and workflow identity."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from simulation.task5_experiments import source_manifest

try:
    from tools import build_task5_package as builder
except ImportError:
    builder = None

ROOT = Path(__file__).resolve().parents[1]


class Task5PackageTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(builder, 'task5 immutable package builder must exist')

    def test_membership_includes_deliverables_but_excludes_private_and_results(self):
        expected = [
            'common/core.py', 'simulation/task5_generators.py',
            'simulation/configs/task3/a.json', 'simulation/configs/task4/a.json',
            'simulation/configs/task5/a.json', 'cluster/task3/run.slurm',
            'cluster/task4/controller.py', 'cluster/task5/submit.sh',
            'tests/test_task3_a.py', 'tests/test_task4_a.py', 'tests/test_task5_a.py',
            'TASK5_README.md', 'TASK5_UNIFIED_DGP_SPEC.md',
            'TASK5_DESIGN_AND_RESOURCE_PLAN.md', 'TASK5_IMPLEMENTATION_REPORT.md',
            'TASK3_DGP_SPEC.md', 'TASK4_DGP_AND_SEARCH_SPEC.md', 'TASK3_README.md',
            'TASK4_README.md', 'docs/任务卡5_统一模拟模型与水平功效验证.md',
            'AGENTS.md', 'requirements.txt', 'requirements-optional.txt',
            'dist/submit_task5.ps1', 'dist/task5_submit.sh',
            'cluster_config_task5.example.json', 'doc/task5_frozen_before.json',
            'doc/task5_smoke_final.json', 'doc/task5_tests_final.log',
            'dist/task5_validation_20261024.json']
        excluded = ['cluster_config_task5.json', 'simulation/results/task3/result.json',
                    'simulation/credentials.json', 'simulation/configs/private.json',
                    'common/__pycache__/secret.py', 'docs/.private/note.md',
                    'cluster/task5/credentials.json', 'doc/progress.md',
                    'dist/old_results.zip', 'simulation/configs/task5/credentials.json',
                    'simulation/configs/task5/cluster_config_task5.json',
                    'dist/submit_task5.sh', 'submit_task5.ps1', 'submit_task5.sh']
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in expected+excluded:
                path = root/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('example', encoding='utf-8')
            names = {p.relative_to(root).as_posix() for p in builder.files_for(root)}
            self.assertTrue(set(expected).issubset(names), sorted(set(expected)-names))
            self.assertFalse(set(excluded)&names)

    def test_real_source_package_hashes_python39_and_exact_workflow_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp)/'task5.zip'
            result = builder.build(ROOT,package,git_info={'head':'test','status_porcelain':'offline'})
            checksum = hashlib.sha256(package.read_bytes()).hexdigest()
            self.assertEqual(result['sha256'],checksum)
            self.assertEqual(package.with_suffix('.zip.sha256').read_text().split()[0],checksum)
            with zipfile.ZipFile(package) as archive:
                data = {name:archive.read(name) for name in archive.namelist()}
            manifest = json.loads(data['manifest.json'])
            self.assertEqual(manifest['study'],'task5_unified_v1')
            self.assertEqual(manifest['manifest_version'],1)
            self.assertEqual(manifest['source_manifest'],source_manifest())
            canonical = json.dumps(source_manifest(),sort_keys=True,ensure_ascii=True,separators=(',',':'))
            self.assertEqual(manifest['implementation_hash'],hashlib.sha256(canonical.encode()).hexdigest())
            self.assertEqual(set(manifest['files']),set(data)-{'manifest.json','SHA256SUMS'})
            sums = dict((name,sha) for sha,name in (
                line.split('  ',1) for line in data['SHA256SUMS'].decode().splitlines()))
            self.assertEqual(set(sums),set(data)-{'SHA256SUMS'})
            for name,content in data.items():
                digest = hashlib.sha256(content).hexdigest()
                if name in manifest['files']:
                    self.assertEqual(manifest['files'][name],digest)
                if name != 'SHA256SUMS':
                    self.assertEqual(sums[name],digest)
                if name.endswith('.py'):
                    ast.parse(content.decode('utf-8-sig'),filename=name,feature_version=(3,9))
            self.assertFalse(any('/results/' in name for name in data))
            self.assertTrue(any('任务卡5' in name for name in data))
            before = package.read_bytes()
            with self.assertRaises(FileExistsError):
                builder.build(ROOT,package,git_info={})
            self.assertEqual(package.read_bytes(),before)

    def test_existing_checksum_alone_prevents_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/'task5.zip'
            package.with_suffix('.zip.sha256').write_text('reserved')
            with self.assertRaises(FileExistsError):
                builder.build(ROOT,package,git_info={})
            self.assertFalse(package.exists())


if __name__ == '__main__':
    unittest.main()
