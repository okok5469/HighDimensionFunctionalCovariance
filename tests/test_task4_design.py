import unittest
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import numpy as np
from simulation import task4_generators as g, task4_design as d


METHODS = ('ours', 'xue_s5', 'xue_s11', 'xue_s21')


def rows(ours=40, xue=45, null=10, fallback=False):
    result = []
    for entry in d.pilot_entries()+(d.fallback_entries() if fallback else []):
        s, count = entry['scenario'], entry['repeats']
        for m in METHODS:
            k = null if not s['tau'] else (ours if m == 'ours' else xue)
            result.append(dict(scenario_id=entry['scenario_id'], spec_id=s['spec_id'],
                null_group_id=s['null_group_id'], n=200, p=20, tau=s['tau'], method=m,
                planned=count, completed=count, valid=count, common_valid=count,
                failed=0, missing=0, rejections=k, common_rejections=k, complete=True))
    return result


class Task4DesignTests(unittest.TestCase):
    def test_policy_file_is_validated_and_drift_fails_closed(self):
        policy=d.load_policy()
        self.assertEqual(policy['maximum_formal_datasets'],2950)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'search_policy.json'
            policy['minimum_ours_rejections']=29
            path.write_text(json.dumps(policy),encoding='utf-8')
            with patch.object(d,'_policy_path',return_value=path):
                with self.assertRaises(ValueError): d.pilot_entries()
                with self.assertRaises(ValueError): d.fallback_entries()
                with self.assertRaises(ValueError): d.select_candidates([])
                with self.assertRaises(ValueError): d.confirmation_entries({})
            policy=d.load_policy()
            policy['unexpected_override']=True
            path.write_text(json.dumps(policy),encoding='utf-8')
            with self.assertRaises(ValueError): d.load_policy(path)

    def test_counts_and_shared_null(self):
        p, f = d.pilot_entries(), d.fallback_entries()
        self.assertEqual((len(p), sum(e['repeats'] for e in p)), (10, 600))
        self.assertEqual(sum(e['repeats'] for e in f), 150)
        self.assertEqual(sum(not e['scenario']['tau'] for e in p+f), 2)
        for entry in p+f:
            truth = g.diagnostics(entry['scenario'])
            self.assertLess(truth['rho'],1.)
            self.assertAlmostEqual(truth['time_peak_effect'],entry['scenario']['tau'])
            scenario=entry['scenario']
            lam=np.diag(scenario['lambda_diagonal'])
            shape=np.asarray(scenario['signal_cov_shape'])
            tau=scenario['tau']
            for sign in (-1,1):
                self.assertGreater(np.linalg.eigvalsh(lam+sign*tau*shape).min(),0.)
            angles=2*np.pi*np.asarray(scenario['grid'])[:,None]*np.arange(1,11)
            phi=np.empty((64,20)); phi[:,::2]=np.sqrt(2)*np.sin(angles)
            phi[:,1::2]=np.sqrt(2)*np.cos(angles)
            self.assertAlmostEqual(float(np.abs(tau*phi@shape@phi.T).max()),tau)

    def test_two_peaks_geometry(self):
        s = g.make_scenario('coherent_two_peaks', .6)
        truth = g.diagnostics(s)
        D = np.asarray(s['signal_cov_shape'])
        grid = np.arange(64)/64
        angle = 2*np.pi*grid[:, None]*np.arange(1, 11)
        phi = np.empty((64, 20)); phi[:, ::2] = np.sqrt(2)*np.sin(angle)
        phi[:, 1::2] = np.sqrt(2)*np.cos(angle)
        a, b = phi[24]/20, phi[56]/20
        np.testing.assert_allclose(D, np.outer(a,a)+np.outer(b,b), atol=1e-16)
        self.assertAlmostEqual(a@b, 0.)
        self.assertAlmostEqual(np.linalg.norm(20*D,2), 1.)
        kernel = phi@D@phi.T
        self.assertAlmostEqual(kernel[24,24],1.)
        self.assertAlmostEqual(kernel[56,56],1.)
        self.assertAlmostEqual(kernel[24,56],0.)
        self.assertAlmostEqual(np.abs(kernel).max(),1.)
        self.assertAlmostEqual(np.linalg.norm(D),np.sqrt(2)/20)
        self.assertAlmostEqual(truth['time_peak_effect'],.6)
        self.assertAlmostEqual(truth['rho'],.6)
        with self.assertRaises(ValueError): g.make_scenario('coherent_two_peaks',1.)

    def test_independent_and_deduplicated_keys(self):
        a = g.make_scenario('coherent_all',0,n=8,p=4)
        b = g.make_scenario('coherent_two_peaks',0,n=8,p=4)
        self.assertEqual(g.data_key(a,'pilot',0),g.data_key(b,'pilot',0))
        x = g.generate(a,'pilot',0)
        y = g.generate(b,'pilot',0)
        np.testing.assert_array_equal(x['Y'],y['Y'])
        self.assertEqual(x['data_id'],y['data_id'])
        np.testing.assert_array_equal(x['gamma0'],y['gamma0'])
        self.assertNotEqual(x['data_id'],g.generate(a,'confirm',0)['data_id'])
        from simulation.task3_generators import make_scenario, data_key
        self.assertNotEqual(g.data_key(a,'pilot',0),data_key(make_scenario('coherent_all',0,n=8,p=4),'pilot',0))

    def test_two_peak_sampling_replays_exact_transform(self):
        scenario=g.make_scenario('coherent_two_peaks',.45,n=9,p=4)
        first=g.generate(scenario,'pilot',3)
        second=g.generate(scenario,'pilot',3)
        np.testing.assert_array_equal(first['Y'],second['Y'])
        self.assertEqual(first['truth_metadata']['edges_zero_based'],second['truth_metadata']['edges_zero_based'])
        phi,lam,D=g.geometry(scenario)
        # Independent block covariance proof for the plus/minus construction.
        plus=np.linalg.cholesky(lam+.45*D)
        minus=np.linalg.cholesky(lam-.45*D)
        transform=np.block([[plus,minus],[plus,-minus]])/np.sqrt(2)
        np.testing.assert_allclose(transform@transform.T,np.block([[lam,.45*D],[.45*D,lam]]),atol=1e-16)
        single=g.diagnostics(g.make_scenario('coherent_all',.45))
        double=g.diagnostics(g.make_scenario('coherent_two_peaks',.45))
        self.assertAlmostEqual(double['weighted_frobenius_effect']/single['weighted_frobenius_effect'],np.sqrt(2))
        self.assertNotEqual(first['data_id'],g.generate(scenario,'confirm',3)['data_id'])

    def test_integer_boundary_selection_and_budget(self):
        selected = d.select_candidates(rows(45,50))
        self.assertIsNotNone(selected['selected_model'])
        self.assertIsNotNone(selected['selected_reference'])
        self.assertEqual(sum(e['repeats'] for e in d.confirmation_entries(selected)),2200)
        self.assertEqual(d.select_candidates(rows(29,30))['selected_model'],None)
        self.assertEqual(d.select_candidates(rows(30,36))['selected_model'],None)

    def test_calibration_and_fallback_gates(self):
        weak = d.select_candidates(rows(5,5))
        self.assertTrue(weak['fallback_required'])
        suspect = rows(40,45,null=11)
        selected = d.select_candidates(suspect)
        self.assertFalse(selected['fallback_required'])
        self.assertEqual(d.confirmation_entries(selected),[])
        secondary = rows(40,45)
        for r in secondary:
            if not r['tau'] and r['method']=='xue_s5': r['rejections']=r['common_rejections']=11
        self.assertIsNotNone(d.select_candidates(secondary)['selected_model'])
        with self.assertRaises(ValueError): d.select_candidates(rows(),integrity_complete=False)
        missing = rows()[:-1]
        with self.assertRaises(ValueError): d.select_candidates(missing)

    def test_each_missing_method_and_missing_candidate_prohibits_selection(self):
        complete=rows()
        for index in range(len(complete)):
            with self.subTest(index=index), self.assertRaises(ValueError):
                d.select_candidates(complete[:index]+complete[index+1:])
        missing_candidate=[r for r in complete if not (r['spec_id']=='coherent_all' and r['tau']==.60)]
        with self.assertRaises(ValueError): d.select_candidates(missing_candidate)
        incomplete=rows()
        incomplete[0]['valid']=99
        with self.assertRaises(ValueError): d.select_candidates(incomplete)

    def test_completed_weak_fallback_stops_and_never_confirms(self):
        selection=d.select_candidates(rows(5,5,fallback=True),fallback_complete=True)
        self.assertFalse(selection['fallback_required'])
        self.assertEqual(selection['decision'],'no_eligible_interval')
        self.assertEqual(d.confirmation_entries(selection),[])
        self.assertEqual(d.lock_spec(selection,'hash',{})['planned_datasets'],0)

    def test_fallback_selects_two_peak_once_and_uses_adjacent_lower_tau(self):
        values=rows(5,5,fallback=True)
        for row in values:
            if row['spec_id']=='coherent_two_peaks' and row['tau']==.60:
                row['rejections']=row['common_rejections']=40 if row['method']=='ours' else 45
        selection=d.select_candidates(values,fallback_complete=True)
        self.assertEqual(selection['selected_model']['spec_id'],'coherent_two_peaks')
        self.assertEqual(selection['selected_model']['tau'],.60)
        confirmation=d.confirmation_entries(selection)
        self.assertEqual(sum(e['repeats'] for e in confirmation),1100)
        self.assertEqual(sorted(e['scenario']['tau'] for e in confirmation if e['scenario']['tau']),[.45,.60])

    def test_each_primary_calibration_failure_excludes_only_matched_background(self):
        for primary in ('ours','xue_s21'):
            values=rows()
            for row in values:
                if row['tau']==0 and row['null_group_id']=='spectrum_flat_b0' and row['method']==primary:
                    row['rejections']=row['common_rejections']=11
            selected=d.select_candidates(values)
            self.assertIsNone(selected['selected_model'])
            self.assertFalse(selected['fallback_required'])
            self.assertIsNotNone(selected['selected_reference'])
            self.assertEqual(sum(e['repeats'] for e in d.confirmation_entries(selected)),1100)

    def test_lower_strength_and_locked_comparisons(self):
        selection = d.select_candidates(rows(40,45))
        self.assertEqual(selection['selected_model']['tau'],.30)
        selected = selection['selected_model']
        self.assertTrue(selected['selected'])
        self.assertTrue(all(r['selected'] or r['not_selected_reason'] for r in selection['ranking']))
        lock = d.lock_spec(selection,'frozen-hash',{'fixed':True})
        self.assertEqual(lock['familywise_declarations'],12)
        self.assertEqual(lock['epsilon'],.05)
        self.assertEqual(sorted(e['scenario']['tau'] for e in lock['scenarios'] if e['scenario']['spec_id']=='coherent_all' and e['scenario']['tau']),[.30,.45])
        weak = rows(5,5)
        with self.assertRaises(ValueError): d.lock_spec(d.select_candidates(weak),'hash',{})


if __name__ == '__main__': unittest.main()
