import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from simulation import task3_io as io
from simulation import task5_experiments as w
from simulation import task5_summary as summary


class WorkflowTests(unittest.TestCase):
    def test_plan_counts_namespaces_and_source_drift(self):
        plan = w.create_plan()
        self.assertEqual(len(plan['scenarios']), 69)
        self.assertEqual(len(w.tasks_for(plan)), 9300)
        self.assertEqual(plan['B'], 500)
        with tempfile.TemporaryDirectory() as tmp:
            w.save_plan(tmp, plan)
            self.assertEqual(w.load_plan(tmp, 'pilot'), plan)
            with patch.object(w, 'source_manifest', return_value={}):
                with self.assertRaisesRegex(ValueError, 'source'):
                    w.load_plan(tmp, 'pilot')

    def test_smoke_records_resume_and_missing_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = w.create_plan('smoke')
            self.assertEqual(plan['B'], 3)
            w.save_plan(tmp, plan)
            self.assertFalse(w.collect(tmp, 'smoke')['complete'])
            for i, (entry, replicate) in enumerate(w.tasks_for(plan)):
                w.run_worker(tmp, 'smoke', i, 1)
                path = w.record_path(tmp, 'smoke', entry, replicate)
                before = path.read_bytes()
                with patch.object(w, 'run_replicate', side_effect=AssertionError('recomputed')):
                    w.run_worker(tmp, 'smoke', i, 1)
                self.assertEqual(path.read_bytes(), before)
                record = json.loads(before)
                self.assertEqual(len({m['data_sha256'] for m in record['methods'].values()}), 1)
                self.assertEqual(len({m['gamma0_sha256'] for m in record['methods'].values()}), 1)
                self.assertTrue(record['complete'])
            self.assertTrue(w.collect(tmp, 'smoke')['complete'])

    def test_production_benchmark_requires_allocation(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict('os.environ', {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'Slurm'):
                w.benchmark(tmp)

    def test_resume_accepts_node_paths_but_rejects_scientific_environment_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan=w.create_plan('smoke')
            w.save_plan(tmp,plan)
            w.run_worker(tmp,'smoke',0,1)
            environment=w.io.environment()
            with patch.object(w.io,'environment',return_value=dict(environment,executable='/another/node/python',platform='another-node')):
                w.run_worker(tmp,'smoke',0,1)
            with patch.object(w.io,'environment',return_value=dict(environment,numpy='changed')):
                with self.assertRaisesRegex(ValueError,'environment'):
                    w.run_worker(tmp,'smoke',0,1)

    def test_confirmation_namespaces_and_fixed_shared_input_order(self):
        from simulation.task5_generators import make_scenario, data_key
        alt=make_scenario('coherent_all', .3, n=8, p=4)
        null=make_scenario('coherent_all', 0, n=8, p=4)
        self.assertEqual(w.data_phase('confirm', null), 'confirm_h0')
        self.assertEqual(w.data_phase('confirm', alt), 'confirm_h1')
        self.assertNotEqual(data_key(alt,'pilot',0),data_key(alt,'confirm_h1',0))
        first=w.run_replicate(alt,'confirm',0,B=3)
        second=w.run_replicate(alt,'confirm',0,B=3,
            method_order=('xue_s21','ours','xue_s5','xue_s11'))
        self.assertTrue(first['complete'])
        self.assertEqual(first['data_id'],second['data_id'])
        self.assertEqual(first['data_sha256'],second['data_sha256'])
        self.assertEqual(first['methods']['ours']['bootstrap_statistics'],
                         second['methods']['ours']['bootstrap_statistics'])

    def test_incomplete_pilot_cannot_select(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan=w.create_plan()
            w.save_plan(tmp,plan)
            with patch.object(w,'collect',return_value={'complete':False}):
                with self.assertRaisesRegex(ValueError,'incomplete'):
                    w.decide(tmp)
            self.assertFalse((Path(tmp)/'confirm_locked.json').exists())

    def test_no_extension_lock_is_immutable_and_resume_never_reselects(self):
        from simulation import task5_design as design
        from tests.test_task5_design import summary_rows
        rows=summary_rows(design,null=0,power=0)
        with tempfile.TemporaryDirectory() as tmp:
            w.save_plan(tmp,w.create_plan())
            with patch.object(w,'collect',return_value={'complete':True}), \
                 patch.object(w,'tasks_for',return_value=[]), \
                 patch.object(w,'save_diagnostics'), patch.object(w,'write_report'), \
                 patch('simulation.task5_summary.summarize',return_value={'summary':rows}):
                decision=w.decide(tmp)
            locked=w.load_plan(tmp,'confirm')
            self.assertEqual(locked['planned_datasets'],5700)
            self.assertEqual(locked['familywise_declarations'],27)
            before=(Path(tmp)/'confirm_locked.json').read_bytes()
            with patch.object(design,'select_extension',side_effect=AssertionError('reselected')), \
                 patch.object(w,'collect',side_effect=AssertionError('recollected')):
                self.assertEqual(w.decide(tmp),decision)
            self.assertEqual((Path(tmp)/'confirm_locked.json').read_bytes(),before)
            with self.assertRaisesRegex(ValueError,'immutable'):
                io.write_sealed(Path(tmp)/'confirm_locked.json',dict(locked,B=1))


class SummaryTests(unittest.TestCase):
    def test_findings_distinguish_working_target_from_unresolved_calibration(self):
        rows=[dict(spec_id='m1_fourier5_peak1',null_group_id='m1_fourier5_peak1',n=800,p=20,
                   tau=0.,method='ours',rate=.05,level_status='unresolved'),
              dict(spec_id='m1_fourier5_peak1',null_group_id='m1_fourier5_peak1',n=800,p=20,
                   tau=.6,method='ours',rate=.9,level_status='not_applicable')]
        text=summary.findings('confirm',rows)
        self.assertIn('unresolved',text)
        self.assertIn('No confirmed unit',text)
        rows[0]['level_status']='near_nominal'
        self.assertIn('working level band and high power',summary.findings('confirm',rows))

    def test_level_band_is_two_sided_and_phase_specific(self):
        self.assertEqual(summary.level_status(50, 1000, 'confirm'), 'near_nominal')
        self.assertEqual(summary.level_status(0, 1000, 'confirm'), 'conservative')
        self.assertEqual(summary.level_status(120, 1000, 'confirm'), 'inflated')
        self.assertEqual(summary.level_status(25, 500, 'pilot'), 'exploratory_point_in_band')
        self.assertEqual(summary.level_status(25, 500, 'confirm'), 'unresolved')

    def test_all_500_counts_cannot_pass_interval_band(self):
        self.assertFalse(any(summary.level_status(k, 500, 'confirm') == 'near_nominal' for k in range(501)))

    def test_nominal_difference_survives_xue_alarm_and_zero_discordance_not_certain(self):
        scenario = dict(spec_id='m1_fourier5_peak1', family='task5_m1', n=800, p=20,
                        M=64, null_group_id='m1_fourier5_peak1', tau=0.)
        plan = dict(phase='confirm', scenarios=[dict(scenario=scenario, scenario_id='null', repeats=1000),
                    dict(scenario=dict(scenario, tau=.6), scenario_id='alt', repeats=300)])
        records = []
        for sid, n in [('null', 1000), ('alt', 300)]:
            for r in range(n):
                indicators = {m: (r < (50 if m == 'ours' else 120)) if sid == 'null' else True
                              for m in ('ours', 'xue_s5', 'xue_s11', 'xue_s21')}
                records.append(dict(scenario_id=sid, replicate=r, methods={
                    m: dict(status='ok', reject=v) for m, v in indicators.items()}))
        result = summary.summarize(plan, records)
        self.assertTrue(result['complete'])
        pair = result['paired'][0]
        self.assertEqual(pair['familywise_declarations'], 3)
        self.assertLess(pair['adjusted_ci_low'], 0)
        self.assertGreater(pair['adjusted_ci_high'], 0)
        self.assertEqual(pair['interpretation'], 'nominal_rejection_probability_only')
        partial=summary.summarize(plan,records[:-1])
        self.assertFalse(partial['complete'])
        self.assertEqual(partial['paired'][0]['label'],'incomplete')


if __name__ == '__main__':
    unittest.main()
