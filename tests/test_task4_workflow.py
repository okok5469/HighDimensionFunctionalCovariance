import unittest
import tempfile
from unittest.mock import patch
import numpy as np
from pathlib import Path
from simulation import task4_experiments as w

class WorkflowTests(unittest.TestCase):
    def test_initial_count_and_identity(self):
        p=w.create_plan()
        self.assertEqual(sum(e['repeats'] for e in p['scenarios']),600)
        self.assertEqual(len(p['scenarios']),10)
        self.assertEqual(p['study'],'task4_fixed_methods_v1')
        self.assertEqual(p['B'],500)
        self.assertEqual(len({e['scenario_id'] for e in p['scenarios']}),10)
    def test_missing_records_block_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            w.initialize(tmp)
            with self.assertRaisesRegex(ValueError,'incomplete'): w.decide(tmp)
    def test_manifest_excludes_results(self):
        self.assertTrue(w.source_manifest())
        self.assertFalse(any('/results/' in p for p in w.source_manifest()))
        self.assertIn('simulation/task4_experiments.py',w.source_manifest())
    def test_immutable_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=w.initialize(tmp)
            p['B']=3
            with self.assertRaises(ValueError): w.save_plan(tmp,p)
    def test_fallback_once_then_final_lock_no_reselection(self):
        from simulation import task4_design as d
        def rows(entries,useful=False):
            out=[]
            for e in entries:
                for m in d.METHODS:
                    count=5 if e['scenario']['tau']==0 else (40 if useful else 5)
                    out.append(dict(e['scenario'],scenario_id=e['scenario_id'],method=m,planned=e['repeats'],completed=e['repeats'],valid=e['repeats'],common_valid=e['repeats'],failed=0,missing=0,rejections=count,common_rejections=count,rate=count/e['repeats'],complete=True))
            return out
        with tempfile.TemporaryDirectory() as tmp:
            plan=w.initialize(tmp)
            initialrows=rows(d.pilot_entries())
            with patch.object(w,'_completed_records',return_value=(plan,[])), patch('simulation.task3_summary.summarize_records',return_value={'summary':initialrows}):
                first=w.decide(tmp)
                second=w.decide(tmp)
            self.assertEqual(first['action'],'fallback')
            self.assertEqual(first,second)
            fallback=w.load_plan(tmp,'fallback')
            w.io.atomic_json(Path(tmp)/'fallback_integrity.json',{'complete':True})
            combinedrows=initialrows+rows(d.fallback_entries(),True)
            with patch.object(w,'_completed_records',side_effect=[(plan,[]),(fallback,[])]), patch('simulation.task3_summary.summarize_records',side_effect=[{'summary':initialrows},{'summary':combinedrows}]):
                final=w.decide(tmp)
            self.assertEqual(final['action'],'confirm')
            locked=w.io.read_sealed(Path(tmp)/'confirm_locked.json')
            self.assertEqual(locked['planned_datasets'],1100)
            self.assertEqual(len(locked['comparisons']),6)
            with patch('simulation.task4_design.select_candidates',side_effect=AssertionError('must not reselect')):
                self.assertEqual(w.decide(tmp),final)
            self.assertEqual(w.io.read_sealed(Path(tmp)/'confirm_locked.json'),locked)

    def test_four_methods_share_inputs_and_frozen_calls(self):
        from simulation.task4_generators import make_scenario
        scenario=make_scenario('coherent_all',.3,n=8,p=4)
        observed=[]
        def ours(Y,target,**kwargs):
            observed.append((Y,target))
            self.assertEqual(kwargs['B'],500)
            self.assertEqual(kwargs['alpha'],.05)
            self.assertEqual(set(kwargs),{'B','alpha','rng','grid','config_id'})
            return dict(statistic=1.,pvalue=.5,reject=False,alpha=.05)
        def xue(Y,**kwargs):
            observed.append((Y,kwargs['gamma0']))
            self.assertIn(kwargs['s'],(5,11,21))
            self.assertEqual(set(kwargs),{'gamma0','s','alpha','grid'})
            return dict(statistic=1.,pvalue=.5,reject=False,alpha=.05,operator=np.eye(2),sigma0=np.eye(2),status='ok')
        with patch.object(w,'covariance_one_sample',side_effect=ours),patch.object(w,'run_xue_one_sample',side_effect=xue):
            record=w.run_replicate(scenario,'pilot',0)
        self.assertTrue(record['complete'])
        self.assertEqual(len(observed),4)
        self.assertTrue(all(Y is observed[0][0] and target is observed[0][1] for Y,target in observed))
        self.assertEqual(len({m['data_id'] for m in record['methods'].values()}),1)

    def test_source_change_blocks_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            w.initialize(tmp)
            with patch.object(w,'source_manifest',return_value={'changed':'yes'}):
                with self.assertRaisesRegex(ValueError,'hashes changed'):w.load_plan(tmp,'pilot')

if __name__=='__main__': unittest.main()
