"""Xue coefficient covariance tests: full single-sample EV and named cross variant.

The single-sample method is the documented extension, not the paper's original
independent two-sample algorithm. No epsilon repair, MB or BC is applied.
"""
import numpy as np


def _alpha(alpha):
    if not np.isscalar(alpha) or not 0 < alpha < 1:
        raise ValueError('alpha must be strictly between 0 and 1')


def xue_critical_value(alpha, *, legacy=False):
    """Critical value on the centered T scale; legacy preserves old arithmetic."""
    _alpha(alpha)
    if legacy:
        return float(-np.log(8 * np.pi) - 2 * np.log(np.log(1.0 / (1.0 - alpha))))
    return float(-np.log(8 * np.pi) - 2 * np.log(-np.log1p(-alpha)))


def xue_pvalue(Tn, *, legacy=False):
    """Stable EV right tail, including infinite or extreme T values."""
    Tn = np.asarray(Tn, dtype=float)
    if np.isnan(Tn).any():
        raise ValueError('T must not contain NaN')
    if legacy:
        with np.errstate(over='ignore', under='ignore'):
            result = 1.0 - np.exp(-((8 * np.pi) ** -0.5) * np.exp(-Tn / 2))
    else:
        # Saturation at z>~746 gives a right-tail probability rounded to 1.
        # Clipping the exponent is a numerical evaluation of the EV CDF,
        # never a modification of sample product variances.
        log_z = -.5 * np.log(8 * np.pi) - .5 * Tn
        with np.errstate(under='ignore'):
            z = np.exp(np.minimum(log_z, np.log(746.0)))
            result = -np.expm1(-z)
    return float(result) if result.ndim == 0 else result


def _positive_integer(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < 1:
        raise ValueError(name + ' must be a positive integer')
    return int(value)


def _scores(scores, p, s, mean_mode, known_mean, ordering):
    if np.iscomplexobj(scores):
        raise ValueError('scores must be real')
    A = np.asarray(scores, dtype=float)
    if A.ndim not in (2, 3) or not np.isfinite(A).all():
        raise ValueError('scores must be finite (n,p,s) or (n,p*s) coefficients')
    if ordering != 'channel_then_basis':
        raise ValueError('only channel_then_basis ordering is implemented')
    if A.ndim == 3:
        _, actual_p, actual_s = A.shape
        p = actual_p if p is None else _positive_integer(p, 'p')
        s = actual_s if s is None else _positive_integer(s, 's')
        if (p, s) != (actual_p, actual_s):
            raise ValueError('p/s must equal the actual coefficient axes')
    if p is None or s is None:
        raise ValueError('flat scores require explicit p and s')
    p, s = _positive_integer(p, 'p'), _positive_integer(s, 's')
    n, d = A.shape[0], p * s
    if d <= 1 or A.size != n * d:
        raise ValueError('EV requires d=p*s>1 and matching coefficient dimensions')
    A = A.reshape(n, d)
    if mean_mode not in ('estimate', 'known'):
        raise ValueError('mean_mode must be estimate or known')
    if n < (3 if mean_mode == 'estimate' else 2):
        raise ValueError('estimate mean requires n>=3; known mean requires n>=2')
    if mean_mode == 'estimate':
        if known_mean is not None:
            raise ValueError('known_mean requires mean_mode=known')
        center = A.mean(axis=0)
    else:
        if known_mean is None or np.iscomplexobj(known_mean):
            raise ValueError('known mean mode requires a real length-d mean')
        center = np.asarray(known_mean, dtype=float)
        if center.shape != (d,) or not np.isfinite(center).all():
            raise ValueError('known_mean must be a finite length-d vector')
    return A - center, n, p, s, d


def _target(sigma0, d):
    if np.iscomplexobj(sigma0):
        raise ValueError('sigma0 must be real')
    target = np.asarray(sigma0, dtype=float)
    if target.shape != (d, d) or not np.isfinite(target).all():
        raise ValueError('sigma0 must be a finite (d,d) coefficient covariance')
    # Tolerance is absolute 1e-12 plus relative 1e-10 times max target magnitude.
    # Targets inside this tolerance are used unchanged, never projected/repaired.
    tol = 1e-12 + 1e-10 * np.max(np.abs(target))
    if np.max(np.abs(target - target.T)) > tol:
        raise ValueError('sigma0 must be symmetric within 1e-12+1e-10*maxabs tolerance')
    if np.linalg.eigvalsh(target)[0] < -tol:
        raise ValueError('sigma0 must be positive semidefinite within declared tolerance')
    return target, float(tol)


def _evaluate(scores, sigma0, *, p, s, alpha, mean_mode, known_mean,
              basis_id, projection_id, target_type, ordering, cross):
    _alpha(alpha)
    Z, n, p, s, d = _scores(scores, p, s, mean_mode, known_mean, ordering)
    if target_type != 'known_coefficient_covariance':
        raise ValueError('only a known deterministic coefficient covariance target is supported')
    target, target_tol = _target(np.zeros((d,d)) if cross else sigma0, d)
    if not isinstance(basis_id, str) or not basis_id or not isinstance(projection_id, str) or not projection_id:
        raise ValueError('basis_id and projection_id must be non-empty strings')
    mask = np.triu(np.ones((d, d), bool))
    if cross:
        channel = np.repeat(np.arange(p), s)
        mask &= channel[:, None] != channel[None, :]
    if not mask.any():
        raise ValueError('cross-channel test requires at least two channels')
    with np.errstate(over='ignore', invalid='ignore', under='ignore'):
        S = Z.T @ Z / n
        m = np.empty((d,d))
        # At most n*d products at once; direct centered squares avoid subtracting
        # nearly equal fourth moments and do not allocate n*d*d arrays.
        for a in range(d):
            centered_products = Z[:, a, None] * Z - S[a]
            m[a] = np.mean(centered_products * centered_products, axis=0)
    tau = xue_critical_value(alpha)
    metadata = dict(mean_mode=mean_mode, covariance_denominator='n',
                    product_variance_denominator='n', basis_id=basis_id,
                    projection_id=projection_id, target_type='cross_zero' if cross else target_type,
                    ordering=ordering, target_validation_tolerance=target_tol,
                    target_repaired=False, method_version='xue_1s_ev_20261021',
                    theoretical_status='EV assumptions not verified from one sample; fixed d and fitted representations require separate justification',
                    theory_scope='cross subset EV calibration not directly established by full-index theorem' if cross else 'full upper triangle including diagonal, under documented S1-S5')
    result = dict(method='Xue-1S-EV-cross-zero' if cross else 'Xue-1S-EV',
                  sample_mode='one_sample', calibration='EV', test_scope='cross' if cross else 'all',
                  n=n,p=p,s=s,d=d,alpha=float(alpha),S=S,m=m,q=None,Q=None,T=None,
                  statistic=None,p_value=None,pvalue=None,reject=None,argmax=None,
                  critical_value=tau,critical_T=tau,critical_Q=float(4*np.log(d)-np.log(np.log(d))+tau),
                  statistic_scale='T',status='ok',failure_reason=None,failed_coordinates=[],
                  mean_mode=mean_mode,covariance_denominator='n',basis_id=basis_id,
                  projection_id=projection_id,target_type=metadata['target_type'],
                  ordering=ordering,metadata=metadata)
    invalid = mask & ((m <= 0) | ~np.isfinite(m) | ~np.isfinite(S))
    if invalid.any():
        result.update(status='degenerate_product_variance',
                      failure_reason='required centered product variances must be finite and strictly positive',
                      failed_coordinates=[tuple(map(int, pair)) for pair in np.argwhere(invalid)])
        return result
    q = np.full((d,d), np.nan)
    with np.errstate(over='ignore', invalid='ignore', under='ignore', divide='ignore'):
        q[mask] = n * ((S[mask] - target[mask]) / np.sqrt(m[mask]))**2
    if not np.isfinite(q[mask]).all():
        result.update(status='nonfinite_statistic', failure_reason='standardized covariance difference is non-finite',
                      failed_coordinates=[tuple(map(int,pair)) for pair in np.argwhere(mask & ~np.isfinite(q))])
        return result
    # Complete q by symmetry for inspection; only selected pairs enter the max.
    a, b = np.unravel_index(np.argmax(np.where(mask, q, -np.inf)), (d,d))
    q[(np.tril_indices(d,-1))] = q.T[np.tril_indices(d,-1)]
    Q = float(q[a,b]); T = float(Q - 4*np.log(d) + np.log(np.log(d)))
    pvalue = xue_pvalue(T)
    result.update(q=q,Q=Q,T=T,statistic=T,p_value=pvalue,pvalue=pvalue,
                  reject=bool(T > tau),argmax=(int(a),int(b)))
    return result


def xue_one_sample(scores, sigma0, *, p=None, s=None, alpha=.05,
                   mean_mode='estimate', known_mean=None,
                   basis_id='provided_coefficients', projection_id='provided_coefficients',
                   target_type='known_coefficient_covariance', ordering='channel_then_basis'):
    """Full coefficient covariance against a known target, including diagonals."""
    return _evaluate(scores,sigma0,p=p,s=s,alpha=alpha,mean_mode=mean_mode,
                     known_mean=known_mean,basis_id=basis_id,projection_id=projection_id,
                     target_type=target_type,ordering=ordering,cross=False)


def xue_cross_zero(scores, *, p=None, s=None, alpha=.05,mean_mode='estimate',
                   known_mean=None,basis_id='provided_coefficients',
                   projection_id='provided_coefficients',ordering='channel_then_basis'):
    """Explicit legacy cross-zero variant; EV subset theory is limited."""
    return _evaluate(scores,None,p=p,s=s,alpha=alpha,mean_mode=mean_mode,
                     known_mean=known_mean,basis_id=basis_id,projection_id=projection_id,
                     target_type='known_coefficient_covariance',ordering=ordering,cross=True)


def compute_Tn_xue(Y, s=None, eps=1e-10):
    """Legacy float cross-zero wrapper. eps is deprecated and never applied."""
    if eps != 1e-10:
        raise ValueError('eps is deprecated: product variances are never clamped or repaired')
    result = xue_cross_zero(Y, s=s)
    if result['status'] != 'ok':
        raise ValueError(result['status'] + ': ' + result['failure_reason'] + '; coordinates=' + repr(result['failed_coordinates']))
    return result['T']


def gumbel_pdf(x):
    """Corresponding EV density, evaluated in the log domain at extreme tails."""
    x = np.asarray(x,dtype=float)
    log_z = -.5*np.log(8*np.pi)-.5*x
    with np.errstate(over='ignore',under='ignore',invalid='ignore'):
        z = np.exp(log_z)
        density = np.exp(log_z-np.log(2)-z)
    density = np.where(np.isinf(x),0.,density)
    return float(density) if density.ndim==0 else density
