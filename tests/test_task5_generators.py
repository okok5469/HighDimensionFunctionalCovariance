"""Deterministic truth checks for the task5 unified distributions."""
import unittest

import numpy as np

from simulation import task3_generators as legacy

try:
    from simulation import task5_generators as gen
except ImportError:
    gen = None


class Task5GeneratorsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(gen, 'task5 generator adapter must exist')

    def test_catalog_and_normalized_kernel_truth(self):
        self.assertEqual(gen.STUDY, 'task5_unified_v1')
        self.assertEqual(tuple(gen.MAIN_MODELS),
                         ('m1_fourier5_peak1', 'm2_brownian_peak1', 'coherent_all'))
        self.assertEqual(len(gen.spec_ids()), 5)
        for name in gen.spec_ids():
            scenario = gen.make_scenario(name, .6, n=6, p=4)
            truth = gen.diagnostics(scenario)
            np.testing.assert_array_equal(truth['grid'], np.arange(64)/64)
            self.assertAlmostEqual(truth['latent_point_variance'].max(), 1.)
            self.assertAlmostEqual(np.abs(truth['signal_time_kernel']).max(), 1.)
            self.assertAlmostEqual(truth['time_peak_effect'], .6)
            self.assertAlmostEqual(truth['rho'], .6*(14/11 if name == 'local_fejer' else 1))
            self.assertAlmostEqual(truth['maximum_marginal_variance'], 1.0025)
            self.assertEqual(truth['support_frobenius_squared'], 4.)

    def test_m1_exact_five_basis_and_projection_coverage(self):
        scenario = gen.make_scenario('m1_fourier5_peak1', .3)
        truth = gen.diagnostics(scenario)
        u = np.arange(64)/64
        phi = np.sqrt(2)*np.stack([np.sin(2*np.pi*u), np.cos(2*np.pi*u),
             np.sin(4*np.pi*u), np.cos(4*np.pi*u), np.sin(6*np.pi*u)], axis=1)
        raw = (phi*np.arange(1.,6.)**-2)@phi.T
        np.testing.assert_allclose(truth['raw_time_kernel'], raw, atol=1e-15)
        np.testing.assert_allclose(truth['basis'], phi, atol=1e-15)
        np.testing.assert_allclose(truth['latent_time_kernel'], raw/2.205, atol=1e-15)
        self.assertEqual(scenario['q'], 5)
        self.assertAlmostEqual(truth['raw_kappa'], 2.205)
        self.assertEqual(truth['effective_latent_rank'], 5)
        self.assertLess(truth['projections']['5']['energy_ratio'], 1.)
        for s in ('11','21'):
            self.assertAlmostEqual(truth['projections'][s]['energy_ratio'], 1.)
        self.assertEqual(truth['correlation_delta'], .3)

    def test_brownian_exact_kernel_and_unclipped_projection(self):
        scenario = gen.make_scenario('m2_brownian_peak1', .3)
        truth = gen.diagnostics(scenario)
        raw = np.minimum.outer(np.arange(64)/64, np.arange(64)/64)
        np.testing.assert_allclose(truth['raw_time_kernel'], raw, atol=1e-15)
        np.testing.assert_allclose(truth['latent_time_kernel'], raw/(63/64), atol=1e-15)
        self.assertEqual(truth['effective_latent_rank'], 63)
        self.assertEqual(truth['raw_kappa'], 63/64)
        self.assertEqual(truth['standard_increment_variance'], 1/64)
        for s, expected in zip(('5','11','21'), (.956744,1.085262,1.119295)):
            projected = truth['projections'][s]
            self.assertAlmostEqual(projected['reconstructed_peak_ratio'], expected, places=5)
            covariance = projected['null_coefficient_covariance']
            self.assertGreater(np.abs(covariance-np.diag(np.diag(covariance))).max(), .01)

    def test_noise_added_after_exact_latent_generation(self):
        for name in gen.MAIN_MODELS[:2]:
            scenario = gen.make_scenario(name, .6, n=8, p=4)
            result = gen.generate(scenario, 'smoke', 7)
            z = gen.rng(scenario, 'smoke', 7, 'signal').standard_normal(
                (scenario['n'], scenario['p'], scenario['q']))
            C = np.eye(4)
            edges = result['truth_metadata']['edges_zero_based']
            self.assertEqual(len({v for edge in edges for v in edge}),4)
            for j,k in edges:
                C[j,k] = C[k,j] = .6
            values, vectors = np.linalg.eigh(C)
            root = (vectors*np.sqrt(values))@vectors.T
            correlated = np.einsum('ij,njk->nik', root, z)
            if name.startswith('m1'):
                u = np.arange(64)/64
                phi = np.sqrt(2)*np.stack([np.sin(2*np.pi*u),np.cos(2*np.pi*u),
                      np.sin(4*np.pi*u),np.cos(4*np.pi*u),np.sin(6*np.pi*u)],axis=1)
                latent = (correlated*np.sqrt((200/441)*np.arange(1.,6.)**-2))@phi.T
            else:
                latent = np.zeros((8,4,64))
                latent[:,:,1:] = np.cumsum(correlated/np.sqrt(63), axis=2)
            noise = gen.rng(scenario, 'smoke', 7, 'noise').normal(0., .05, (8,4,64))
            np.testing.assert_allclose(result['Y'], latent+noise, atol=2e-15)
            truth = gen.diagnostics(scenario)
            np.testing.assert_allclose(result['gamma0'],
                np.einsum('ij,lm->ijlm',np.eye(4),truth['null_time_block']),atol=1e-15)
            if name.startswith('m2'):
                np.testing.assert_array_equal(result['Y'][:,:,0], noise[:,:,0])

    def test_flat_null_identity_and_independent_namespaces(self):
        names = ('coherent_all','local_fejer','spectrum_flat_b0')
        scenarios = [gen.make_scenario(name,0,n=5,p=4) for name in names]
        results = [gen.generate(s,'pilot',0) for s in scenarios]
        self.assertEqual(len({r['data_id'] for r in results}),1)
        for result in results[1:]:
            np.testing.assert_array_equal(results[0]['Y'], result['Y'])
        keys = [gen.data_key(gen.make_scenario(name,0,n=5,p=4),'pilot',0)
                for name in ('m1_fourier5_peak1','m2_brownian_peak1','coherent_all','spectrum_fast_b4')]
        self.assertEqual(len({str(key) for key in keys}),4)
        s = scenarios[0]
        self.assertNotEqual(gen.data_key(s,'pilot',0), gen.data_key(s,'confirm',0))
        self.assertNotEqual(gen.data_key(s,'pilot',0), gen.data_key(s,'benchmark',0))
        self.assertNotEqual(gen.data_key(s,'pilot',0), legacy.data_key(legacy.make_scenario('coherent_all',0,n=5,p=4),'pilot',0))
        self.assertEqual(s['s0'],0)
        self.assertEqual(results[0]['truth_metadata']['edges_zero_based'],[])
        for stream in ('signal','noise','support','bootstrap'):
            self.assertEqual(gen.rng(s,'pilot',0,stream).random(), gen.rng(s,'pilot',0,stream).random())
        self.assertNotEqual(gen.rng(s,'pilot',0,'signal').random(), gen.rng(s,'pilot',0,'noise').random())

    def test_legacy_profile_is_unchanged(self):
        for model in ('M1','M2'):
            name = 'legacy_'+model+'_full_reference'
            scenario = gen.make_scenario(name,.15,n=5,p=4)
            self.assertEqual(scenario,legacy.make_scenario(name,.15,n=5,p=4))
            result = gen.generate(scenario,'smoke',2)
            old = legacy.generate(scenario,'smoke',2)
            np.testing.assert_array_equal(result['Y'],old['Y'])
            self.assertEqual(result['data_id'],old['data_id'])

    def test_confirm_null_and_alternative_streams_and_retry_identity(self):
        for name in gen.spec_ids():
            null = gen.make_scenario(name, 0., n=4, p=4)
            alternative = gen.make_scenario(name, .6, n=4, p=4)
            for stream in ('support', 'signal', 'noise', 'bootstrap'):
                self.assertNotEqual(gen.rng(null, 'confirm', 0, stream).random(),
                                    gen.rng(alternative, 'confirm', 0, stream).random())
                self.assertNotEqual(gen.rng(null, 'confirm', 0, stream).random(),
                                    gen.rng(null, 'pilot', 0, stream).random())
            first = gen.generate(alternative, 'confirm', 0)
            scheduled = dict(alternative, output_directory='other', worker=7, method_order=[21,5,11])
            retry = gen.generate(scheduled, 'confirm', 0)
            np.testing.assert_array_equal(first['Y'], retry['Y'])
            self.assertEqual(first['data_id'], retry['data_id'])
            self.assertNotEqual(first['data_id'],gen.generate(alternative,'confirm',1)['data_id'])

    def test_original_normalization_metadata_and_noise_do_not_mutate_global_rng(self):
        state = np.random.get_state()
        for name, kappa in zip(gen.MAIN_MODELS[:2], (441/200,63/64)):
            for tau in (0., .6, .999):
                scenario = gen.make_scenario(name,tau,n=4,p=4)
                result = gen.generate(scenario,'smoke',0)
                metadata = result['truth_metadata']
                self.assertEqual(metadata['correlation_delta'],tau)
                self.assertEqual(metadata['raw_kappa'],kappa)
                self.assertEqual(metadata['normalized_kernel_peak'],1.)
                self.assertGreater(np.linalg.eigvalsh(metadata['C'])[0],0.)
                self.assertAlmostEqual(metadata['min_channel_eigenvalue'],1-tau)
                np.testing.assert_array_equal(np.diag(metadata['C']),np.ones(4))
        after = np.random.get_state()
        self.assertEqual(state[0],after[0])
        np.testing.assert_array_equal(state[1],after[1])
        self.assertEqual(state[2:],after[2:])

    def test_task5_explicit_confirmation_and_small_benchmark_namespaces(self):
        for name in gen.spec_ids():
            keys = []
            for phase,tau in (('confirm_h0',0.),('confirm_h1',.3),('small_benchmark',.3)):
                scenario = gen.make_scenario(name,tau,n=4,p=4)
                key = gen.data_key(scenario,phase,0)
                self.assertEqual(key['phase'],phase)
                keys.append(str(key))
                self.assertEqual(gen.generate(scenario,phase,0)['Y'].shape,(4,4,64))
            self.assertEqual(len(set(keys)),3)
        for name in ('coherent_all','local_fejer','spectrum_flat_b0'):
            scenario = gen.make_scenario(name,0.,n=4,p=4)
            self.assertEqual(gen.data_key(scenario,'confirm_h0',0),
                gen.data_key(gen.make_scenario('spectrum_flat_b0',0.,n=4,p=4),'confirm_h0',0))
        with self.assertRaises(ValueError):
            gen.data_key(scenario,'unknown',0)

    def test_existing_fourier_sampler_is_exactly_reused(self):
        for name in ('coherent_all','local_fejer','spectrum_fast_b4'):
            for tau in (0.,.3):
                scenario=gen.make_scenario(name,tau,n=4,p=4)
                expected=legacy.generate(scenario,'pilot',0)
                observed=gen.generate(scenario,'pilot',0)
                np.testing.assert_array_equal(observed['Y'],expected['Y'])
                np.testing.assert_array_equal(observed['gamma0'],expected['gamma0'])
                self.assertEqual(observed['data_id'],expected['data_id'])
                self.assertNotIn('C', observed['truth_metadata'])
                self.assertNotIn('correlation_delta', observed['truth_metadata'])

    def test_reject_invalid_scenarios_without_covariance_repair(self):
        for name in gen.MAIN_MODELS[:2]:
            for tau in (-.1,1.,np.nan):
                with self.assertRaises(ValueError):
                    gen.make_scenario(name,tau)
        for kwargs in ({'n':True},{'p':3},{'n':1}):
            with self.assertRaises(ValueError):
                gen.make_scenario('coherent_all',.15,**kwargs)
        with self.assertRaises(ValueError):
            gen.make_scenario('coherent_two_peaks',.15)
        with self.assertRaises(ValueError):
            gen.make_scenario('local_fejer',.8)


if __name__ == '__main__':
    unittest.main()
