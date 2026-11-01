"""Unified task5 distributions; frozen methods and legacy sources stay untouched.

M1 uses its original five Fourier directions. M2 uses all 63 independent
increments on the half-open grid, without inversion or repair of its singular
time kernel. Noise is sampled independently after deterministic normalization.
"""
import numpy as np

from common.xue_helper import projection_operator
from simulation import task3_generators as previous
from simulation.data_generation import fourier_literal_basis, make_rng, symmetric_sqrt
from simulation.task3_io import digest

STUDY = 'task5_unified_v1'
MAIN_MODELS = ('m1_fourier5_peak1', 'm2_brownian_peak1', 'coherent_all')
_LEGACY = ('legacy_M1_full_reference', 'legacy_M2_full_reference')
_ORIGINAL = MAIN_MODELS[:2]


def spec_ids():
    """Default main and supplementary models, excluding legacy profiles."""
    return list(MAIN_MODELS) + ['local_fejer', 'spectrum_fast_b4']


def geometry(scenario):
    """Return a time design and latent covariance/signal shapes, without inverses."""
    u = np.asarray(scenario['grid'])
    if scenario['spec_id'] == _ORIGINAL[0]:
        covariance = np.diag((200/441)*np.arange(1., 6.)**-2)
        return fourier_literal_basis(u).T, covariance, covariance.copy()
    if scenario['spec_id'] == _ORIGINAL[1]:
        # 1/sqrt(63) is the normalized increment SD, not the grid step.
        design = (np.arange(64)[:, None] > np.arange(63)[None, :])/np.sqrt(63)
        return design, np.eye(63), np.eye(63)
    return previous._geometry(scenario)


def make_scenario(spec_id, tau, n=200, p=20):
    """Build the JSON-compatible unified scenario or an unchanged legacy profile."""
    if spec_id in _LEGACY:
        return previous.make_scenario(spec_id, tau, n=n, p=p)
    if spec_id not in spec_ids()+['spectrum_flat_b0']:
        raise ValueError('unknown task5 specification: '+spec_id)
    base = spec_id if spec_id not in _ORIGINAL else 'spectrum_flat_b0'
    scenario = previous.make_scenario(base, tau, n=n, p=p)
    scenario.update(study=STUDY, spec_id=spec_id, s0=4 if tau else 0,
                    normalized_kernel_peak=1., raw_kappa=1.)
    if spec_id in _ORIGINAL:
        is_fourier = spec_id == _ORIGINAL[0]
        scenario.update(family='task5_original', model='M1' if is_fourier else 'M2',
                        q=5 if is_fourier else 63, null_group_id=spec_id,
                        basis='phi_1_to_phi_5' if is_fourier else 'brownian_increments_63',
                        grid_id='half_open_0_1_M64', correlation_delta=float(tau),
                        raw_kappa=441/200 if is_fourier else 63/64)
        for inactive in ('H', 't0'):
            scenario.pop(inactive, None)
        _, covariance, shape = geometry(scenario)
        scenario.update(lambda_diagonal=np.diag(covariance).tolist(),
                        signal_cov_shape=shape.tolist())
    _, covariance, shape = geometry(scenario)
    white = shape/np.sqrt(np.outer(np.diag(covariance), np.diag(covariance)))
    if float(tau)*np.linalg.norm(white, 2) >= 1:
        raise ValueError('coefficient covariance is not positive definite; no repair is permitted')
    return scenario


def data_key(scenario, phase, replicate):
    """Canonical physical-distribution identity, sharing only the flat H0."""
    if scenario.get('family') == 'legacy':
        return previous.data_key(scenario, phase, replicate)
    if scenario.get('study') != STUDY:
        raise ValueError('task5 requires its independent study namespace')
    if phase not in ('smoke', 'benchmark', 'small_benchmark', 'pilot', 'confirm',
                     'confirm_h0', 'confirm_h1'):
        raise ValueError('unknown task5 phase')
    key = previous.data_key(scenario, 'pilot', replicate)
    key['phase'] = phase
    return key


def rng(scenario, phase, replicate, stream):
    """Separate support, innovations, noise and multiplier streams by identity."""
    if scenario.get('family') == 'legacy':
        return previous.rng(scenario, phase, replicate, stream)
    return make_rng(data_key(scenario, phase, replicate), replicate, stream)


def generate(scenario, phase, replicate):
    """Return observed curves and their complete noise-inclusive known null."""
    key = data_key(scenario, phase, replicate)
    if scenario['family'] == 'legacy':
        return previous.generate(scenario, phase, replicate)
    n, p, M, tau = (scenario[k] for k in ('n', 'p', 'M', 'tau'))
    C, edges = np.eye(p), []
    if tau:
        vertices = rng(scenario, phase, replicate, 'support').choice(p, size=4, replace=False)
        edges = [(int(vertices[i]), int(vertices[i+1])) for i in (0, 2)]
        for j, k in edges:
            C[j, k] = C[k, j] = tau
    z = rng(scenario, phase, replicate, 'signal').standard_normal((n, p, scenario['q']))
    basis, covariance, shape = geometry(scenario)
    coefficients = z*np.sqrt(np.diag(covariance))
    if scenario['spec_id'] in _ORIGINAL:
        correlated = np.einsum('ij,njk->nik', symmetric_sqrt(C), z, optimize=True)
        coefficients = correlated*np.sqrt(np.diag(covariance))
    elif tau:
        # Preserve the frozen task3/task4 Fourier plus/minus transform exactly;
        # task5 owns its random namespace, including explicit confirm H0/H1.
        plus_root = np.linalg.cholesky(covariance+tau*shape)
        minus_root = np.linalg.cholesky(covariance-tau*shape)
        for j, k in edges:
            plus, minus = z[:, j]@plus_root.T, z[:, k]@minus_root.T
            coefficients[:, j], coefficients[:, k] = (plus+minus)/np.sqrt(2), (plus-minus)/np.sqrt(2)
    latent = coefficients@basis.T
    noise_variance = scenario['sigma_noise']**2
    noise = rng(scenario, phase, replicate, 'noise').normal(0., scenario['sigma_noise'], (n, p, M))
    block = basis@covariance@basis.T + noise_variance*np.eye(M)
    metadata = dict(tau=tau, noise_variance=noise_variance, data_key=key,
                    base_seed=20261021, edges_zero_based=edges,
                    raw_kappa=scenario['raw_kappa'], normalized_kernel_peak=1.)
    if scenario['spec_id'] in _ORIGINAL:
        metadata.update(C=C, min_channel_eigenvalue=float(np.linalg.eigvalsh(C)[0]),
                        correlation_delta=tau)
    return dict(Y=latent+noise, grid=np.asarray(scenario['grid']),
                gamma0=np.einsum('ij,lm->ijlm', np.eye(p), block), data_id=digest(key),
                truth_metadata=metadata)


def _projections(scenario, kernel, signal):
    M, tau = scenario['M'], scenario['tau']
    null = kernel+scenario['sigma_noise']**2*np.eye(M)
    result = {}
    for s in (5, 11, 21):
        L = projection_operator(1, M, s, grid=np.asarray(scenario['grid']))
        design = L.T*M
        target, delta = L@null@L.T, tau*(L@signal@L.T)
        Q = np.linalg.qr(design, mode='reduced')[0]
        ratio = float(np.linalg.norm(Q@(Q.T@signal@Q)@Q.T)/np.linalg.norm(signal))
        reconstructed_peak = float(np.abs(design@(L@signal@L.T)@design.T).max())
        result[str(s)] = dict(s=s, channel_operator=L,
            null_coefficient_covariance=target, signal_coefficient_difference=delta,
            coefficient_max_difference=float(np.abs(delta).max()),
            reconstructed_peak_ratio=reconstructed_peak/float(np.abs(signal).max()),
            orthogonal_frobenius_ratio=ratio, energy_ratio=ratio**2,
            standardized_null_effect=float(np.sqrt(scenario['n'])*np.max(
                np.abs(delta)/np.sqrt(np.outer(np.diag(target), np.diag(target))))),
            full_operator_rule='I_p kron channel_operator',
            full_null_rule='I_p kron null_coefficient_covariance',
            full_delta_rule='E kron signal_coefficient_difference')
    return result


def diagnostics(scenario):
    """Exact latent, observed and actually projected truth, never empirical scaling."""
    if scenario['family'] == 'legacy':
        return previous.diagnostics(scenario)
    basis, covariance, shape = geometry(scenario)
    kernel, signal = basis@covariance@basis.T, basis@shape@basis.T
    M, tau = scenario['M'], scenario['tau']
    null = kernel+scenario['sigma_noise']**2*np.eye(M)
    white = shape/np.sqrt(np.outer(np.diag(covariance), np.diag(covariance)))
    norm = float(np.linalg.norm(white, 2))
    result = dict(scenario=dict(scenario), basis=basis, grid=np.asarray(scenario['grid']),
        lambda_diagonal=np.diag(covariance), coefficient_null_covariance=covariance,
        signal_cov_shape=shape, raw_kappa=scenario['raw_kappa'],
        raw_time_kernel=kernel*scenario['raw_kappa'], latent_time_kernel=kernel,
        normalized_kernel_peak=float(np.diag(kernel).max()),
        normalized_kernel_reference='latent_time_kernel', raw_kernel_reference='raw_time_kernel',
        effective_latent_rank=scenario['q'], correlation_delta=scenario.get('correlation_delta'),
        null_time_block=null, signal_time_kernel=signal,
        support_template_zero_based=[[0, 1], [2, 3]], support_template_operator_norm=1.,
        support_frobenius_squared=4., latent_point_variance=np.diag(kernel),
        observed_point_variance=np.diag(null),
        maximum_latent_marginal_variance=float(np.diag(kernel).max()),
        average_latent_marginal_variance=float(np.diag(kernel).mean()),
        maximum_marginal_variance=float(np.diag(null).max()),
        average_marginal_variance=float(np.diag(null).mean()),
        time_peak_effect=float(tau*np.abs(signal).max()),
        signal_cov_shape_frobenius=float(np.linalg.norm(shape)),
        weighted_frobenius_effect=float(2*tau*np.linalg.norm(signal)/M),
        whitened_signal_operator_norm=norm, rho=tau*norm,
        minimum_whitened_eigenvalue=1-tau*norm,
        positive_definiteness_bound='rho < 1; exact matching support in latent space',
        full_null_rule='I_p kron null_time_block', full_delta_rule='tau E kron signal_time_kernel',
        null_group_id=scenario['null_group_id'], projections=_projections(scenario, kernel, signal))
    if scenario['spec_id'] == _ORIGINAL[1]:
        result.update(standard_increment_variance=1/64, normalized_increment_variance=1/63,
                      increment_count=63, brownian_grid_step=1/64,
                      latent_zero_time_value=0.)
    return result
