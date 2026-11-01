"""Fixed Fourier adaptation and matched known targets for Xue-style tests.

The existing constant-first Fourier rectangle projection is a project choice,
not the paper's cubic-spline fitting or an automatic truncation-order rule.
"""
import numpy as np

from common.statistic_calculator_xue import (
    xue_one_sample, xue_cross_zero, xue_critical_value, xue_pvalue,
)

S_XUE_DEFAULT = 5


def _real_array(value, name):
    if np.iscomplexobj(value):
        raise ValueError(f'{name} must be real; complex values are unsupported')
    return np.asarray(value, dtype=float)


def _positive_integer(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < 1:
        raise ValueError(f'{name} must be a positive integer')
    return int(value)


def _grid(M, grid):
    M = _positive_integer(M, 'M')
    u = np.linspace(0., 1., M) if grid is None else _real_array(grid, 'grid')
    if u.shape != (M,) or not np.isfinite(u).all() or np.any(np.diff(u) <= 0):
        raise ValueError('grid must have M finite, strictly increasing points')
    return u


def _fourier_design(M, s, grid=None):
    s = _positive_integer(s, 's')
    u = _grid(M, grid)
    B = np.empty((M, s))
    B[:, 0] = 1.0
    for k in range(1, s):
        kk = (k + 1) // 2
        trig = np.sin if k % 2 else np.cos
        B[:, k] = np.sqrt(2.0) * trig(2.0 * np.pi * kk * u)
    return B


def _curves(Y):
    Y = _real_array(Y, 'curves')
    if Y.ndim != 3 or min(Y.shape) < 1 or not np.isfinite(Y).all():
        raise ValueError('curves must have finite shape (n, p, M) with nonempty axes')
    return Y


def project_to_fourier_basis(Y, s):
    """Preserved phi_0,...,phi_(s-1) rectangle projection, weight 1/M."""
    Y = _curves(Y)
    M = Y.shape[2]
    B = _fourier_design(M, s)
    return np.einsum('npm,ms->nps', Y, B) / M


def projection_operator(p, M, s, grid=None):
    """Actual fixed map L=I_p kron (B.T/M), channel then basis ordering."""
    p = _positive_integer(p, 'p')
    B = _fourier_design(M, s, grid)
    return np.kron(np.eye(p), B.T / M)


def _grid_covariance(gamma0, p, M):
    gamma = _real_array(gamma0, 'gamma0')
    if gamma.shape != (p, p, M, M) or not np.isfinite(gamma).all():
        raise ValueError('gamma0 must have finite shape (p, p, M, M)')
    flat = gamma.transpose(0, 2, 1, 3).reshape(p*M, p*M)
    scale = max(1., float(np.max(np.abs(flat))))
    if not np.allclose(flat, flat.T, rtol=1e-10, atol=1e-12*scale):
        raise ValueError('gamma0 must be a symmetric grid covariance')
    if np.linalg.eigvalsh(flat)[0] < -1e-10*scale:
        raise ValueError('gamma0 must be positive semidefinite; no target repair is applied')
    return flat


def run_xue_one_sample(
    Y_grid, gamma0=None, *, sigma0=None, s=S_XUE_DEFAULT, alpha=.05,
    operator=None, grid=None, target_type=None, input_type='grid', p=None,
    mean_mode='estimate', known_mean=None, basis_id=None, projection_id=None,
):
    """Xue-1S-EV with one explicit known target in the actual representation.

    gamma0 is the complete observed grid covariance, including measurement
    noise when present. sigma0 is already in the fitted coefficient ordering
    and is used directly. Supplying neither or both is an error. Custom fixed
    operators must have shape (p*s,p*M); they transform data and gamma0 alike.
    """
    if (gamma0 is None) == (sigma0 is None):
        raise ValueError('provide exactly one known target: gamma0 or sigma0')
    source_type = 'known_grid_covariance' if gamma0 is not None else 'known_coefficient_covariance'
    if target_type not in (None, source_type):
        raise ValueError(f'target_type must be {source_type}; estimated targets are unsupported')
    s = _positive_integer(s, 's')
    L, u = None, None
    if input_type == 'grid':
        Y = _curves(Y_grid)
        n, channels, M = Y.shape
        if p is not None and _positive_integer(p, 'p') != channels:
            raise ValueError('p must match the observed channel count')
        p = channels
        u = _grid(M, grid)
        if operator is None:
            L = projection_operator(p, M, s, u)
            B = _fourier_design(M, s, u)
            scores = np.einsum('npm,ms->nps', Y, B) / M
            basis_id = basis_id or 'fixed_fourier_phi_0_to_s_minus_1'
            projection_id = projection_id or 'fixed_fourier_rectangle_1_over_M'
        else:
            L = _real_array(operator, 'operator')
            if L.shape != (p*s, p*M) or not np.isfinite(L).all():
                raise ValueError('operator must have finite shape (p*s, p*M)')
            scores = Y.reshape(n, p*M) @ L.T
            basis_id = basis_id or 'provided_fixed_coefficient_representation'
            projection_id = projection_id or 'provided_fixed_linear_operator'
        if gamma0 is not None:
            sigma0 = L @ _grid_covariance(gamma0, p, M) @ L.T
    elif input_type == 'coefficients':
        if gamma0 is not None or operator is not None or grid is not None:
            raise ValueError('coefficient inputs require sigma0 and no further grid projection')
        scores = _real_array(Y_grid, 'coefficients')
        if scores.ndim == 3:
            channels, width = scores.shape[1:]
            if width != s or (p is not None and p != channels):
                raise ValueError('coefficient shape must match p and s')
            p = channels
        elif scores.ndim != 2 or p is None:
            raise ValueError('flat coefficient inputs require explicit p and s')
        p = _positive_integer(p, 'p')
        basis_id = basis_id or 'provided_coefficients'
        projection_id = projection_id or 'provided_coefficients'
    else:
        raise ValueError('input_type must be grid or coefficients')
    result = xue_one_sample(
        scores, sigma0, p=p, s=s, alpha=alpha, mean_mode=mean_mode,
        known_mean=known_mean, basis_id=basis_id, projection_id=projection_id,
        target_type='known_coefficient_covariance')
    result.update(source_target_type=source_type, test_scope='all',
                  operator=L, sigma0=np.asarray(sigma0, dtype=float),
                  projection_convention='predefined_fixed_map_not_author_spline_or_automatic_order',
                  target_noise_policy='known_target_must_include_observed_measurement_noise')
    if u is not None:
        result.update(grid=u, M=len(u))
    return result


def run_xue_cross_test(Y_grid, s=S_XUE_DEFAULT, alpha=.05):
    """Named existing cross-channel zero test; not the full known-target test."""
    Y = _curves(Y_grid)
    scores = project_to_fourier_basis(Y, s)
    result = xue_cross_zero(
        scores, p=Y.shape[1], s=s, alpha=alpha,
        basis_id='fixed_fourier_phi_0_to_s_minus_1',
        projection_id='fixed_fourier_rectangle_1_over_M')
    result.update(test_scope='cross', M=Y.shape[2], grid=np.linspace(0., 1., Y.shape[2]),
                  projection_convention='predefined_fixed_map_not_author_spline_or_automatic_order')
    return result


def run_xue_test(Y_grid, s=S_XUE_DEFAULT, alpha=.05):
    """Legacy tuple route for cross-zero only, preserving legacy tail arithmetic.

    Use run_xue_one_sample for a full known target or run_xue_cross_test for
    explicitly named structured results. Degeneracy raises, never nonrejects.
    """
    result = run_xue_cross_test(Y_grid, s=s, alpha=alpha)
    if result['status'] != 'ok':
        raise ValueError(result['status'] + ': ' + result['failure_reason'])
    return (result['T'], xue_critical_value(alpha, legacy=True),
            xue_pvalue(result['T'], legacy=True))
