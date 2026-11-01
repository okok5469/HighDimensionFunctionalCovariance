"""Task4 distribution namespace and exact finite-Fourier Gaussian sampler.

The task3 sources and all statistical methods remain unchanged. The two-peak
shape is a sum, never a peak-normalized average.
"""
import numpy as np
from simulation import task3_generators as previous
from simulation.task3_io import digest
from common.xue_helper import projection_operator

STUDY = 'task4_fixed_methods_v1'


def spec_ids():
    return ['coherent_all', 'local_fejer', 'spectrum_fast_b4', 'coherent_two_peaks']


def make_scenario(spec_id, tau, n=200, p=20):
    if spec_id not in spec_ids()+['spectrum_flat_b0']:
        raise ValueError('unknown task4 specification: '+spec_id)
    base = 'coherent_all' if spec_id == 'coherent_two_peaks' else spec_id
    scenario = previous.make_scenario(base, tau, n=n, p=p)
    scenario.update(study=STUDY, spec_id=spec_id)
    if spec_id == 'coherent_two_peaks':
        basis = previous._fourier([3/8, 7/8])
        shape = basis.T@basis/20**2
        scenario.update(signal_cov_shape=shape.tolist(), t1=7/8,
                        family='task4_coherent_two_peaks')
    _, covariance, shape = geometry(scenario)
    rho = float(tau*np.linalg.norm(shape/np.sqrt(np.outer(np.diag(covariance),np.diag(covariance))),2))
    if rho >= 1:
        raise ValueError('coefficient covariance is not positive definite; no repair is permitted')
    return scenario


def geometry(scenario):
    return (previous._fourier(scenario['grid']), np.diag(scenario['lambda_diagonal']),
            np.asarray(scenario['signal_cov_shape']))


def data_key(scenario, phase, replicate):
    if scenario.get('study') != STUDY:
        raise ValueError('task4 requires its independent study namespace')
    return previous.data_key(scenario, phase, replicate)


def rng(scenario, phase, replicate, stream):
    from simulation.data_generation import make_rng
    return make_rng(data_key(scenario,phase,replicate),replicate,stream)


def generate(scenario, phase, replicate):
    key = data_key(scenario,phase,replicate)
    basis, covariance, shape = geometry(scenario)
    n,p,M,tau = (scenario[k] for k in ('n','p','M','tau'))
    # Cholesky validation precedes random sampling, with no eigenvalue repair.
    plus_root = np.linalg.cholesky(covariance+tau*shape)
    minus_root = np.linalg.cholesky(covariance-tau*shape)
    z = rng(scenario,phase,replicate,'signal').standard_normal((n,p,20))
    coefficients = z*np.sqrt(np.diag(covariance))[None,None,:]
    edges = []
    if tau:
        vertices = rng(scenario,phase,replicate,'support').choice(p,size=4,replace=False)
        edges = [(int(vertices[i]),int(vertices[i+1])) for i in (0,2)]
        for j,k in edges:
            plus,minus = z[:,j]@plus_root.T,z[:,k]@minus_root.T
            coefficients[:,j],coefficients[:,k] = (plus+minus)/np.sqrt(2),(plus-minus)/np.sqrt(2)
    noise = rng(scenario,phase,replicate,'noise').normal(0,scenario['sigma_noise'],(n,p,M))
    block = basis@covariance@basis.T+scenario['sigma_noise']**2*np.eye(M)
    return dict(Y=coefficients@basis.T+noise, grid=np.asarray(scenario['grid']),
                gamma0=np.einsum('ij,lm->ijlm',np.eye(p),block),data_id=digest(key),
                truth_metadata=dict(tau=tau,noise_variance=scenario['sigma_noise']**2,
                    data_key=key,base_seed=20261021,edges_zero_based=edges))


def diagnostics(scenario):
    basis,covariance,shape = geometry(scenario)
    signal = basis@shape@basis.T
    kernel = basis@covariance@basis.T
    M,tau = scenario['M'],scenario['tau']
    null = kernel+scenario['sigma_noise']**2*np.eye(M)
    white = shape/np.sqrt(np.outer(np.diag(covariance),np.diag(covariance)))
    norm = float(np.linalg.norm(white,2))
    projections = {}
    for s in (5,11,21):
        L = projection_operator(1,M,s,grid=np.asarray(scenario['grid']))
        design = L.T*M
        Q = np.linalg.qr(design,mode='reduced')[0]
        ratio = float(np.linalg.norm(Q@(Q.T@signal@Q)@Q.T)/np.linalg.norm(signal))
        delta,target = tau*L@signal@L.T,L@null@L.T
        projections[str(s)] = dict(s=s,channel_operator=L,null_coefficient_covariance=target,
            signal_coefficient_difference=delta,coefficient_max_difference=float(np.abs(delta).max()),
            reconstructed_peak_ratio=float(np.abs(design@delta@design.T).max()/(tau*np.abs(signal).max())) if tau else None,
            orthogonal_frobenius_ratio=ratio if tau else None,energy_ratio=ratio**2 if tau else None,
            standardized_null_effect=float(np.sqrt(scenario['n'])*np.max(np.abs(delta)/np.sqrt(np.outer(np.diag(target),np.diag(target))))))
    return dict(scenario=dict(scenario),basis=basis,grid=np.asarray(scenario['grid']),
        lambda_diagonal=np.diag(covariance),coefficient_null_covariance=covariance,
        signal_cov_shape=shape,null_time_block=null,signal_time_kernel=signal,
        support_template_zero_based=[[0,1],[2,3]],support_template_operator_norm=1.,
        support_frobenius_squared=4.,latent_point_variance=np.diag(kernel),observed_point_variance=np.diag(null),
        maximum_marginal_variance=float(np.diag(null).max()),average_marginal_variance=float(np.diag(null).mean()),
        time_peak_effect=float(tau*np.abs(signal).max()),signal_cov_shape_frobenius=float(np.linalg.norm(shape)),
        weighted_frobenius_effect=float(2*tau*np.linalg.norm(signal)/M),
        whitened_signal_operator_norm=norm,rho=tau*norm,minimum_whitened_eigenvalue=1-tau*norm,
        positive_definiteness_bound='rho < 1; exact matching support',
        full_null_rule='I_p kron null_time_block',full_delta_rule='tau E kron signal_time_kernel',
        null_group_id=scenario['null_group_id'],projections=projections)
