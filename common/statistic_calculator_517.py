"""Functional covariance tests: method v1.1, data axes (subjects, channels, grid)."""
import numpy as np


def _prepare_group(data):
    if np.iscomplexobj(data):
        raise ValueError("data must be real-valued")
    data = np.asarray(data, dtype=float)
    if data.ndim != 3:
        raise ValueError("data must have shape (subjects, channels, grid)")
    n, p, M = data.shape
    if n < 2 or p < 1 or M < 1 or not np.isfinite(data).all():
        raise ValueError("invalid sample size, shape or non-finite data")
    D = (data - data.mean(axis=0, keepdims=True)).reshape(n, p * M)
    gram = D.T @ D
    return n, p, M, D, gram / (n - 1), gram / n


def _flat_mask(p, M, channel_pairs=None):
    pairs = np.ones((p, p), dtype=bool) if channel_pairs is None else np.asarray(channel_pairs)
    if pairs.shape != (p, p) or pairs.dtype != np.dtype(bool):
        raise ValueError("channel_pairs must be a boolean (p, p) mask")
    if not pairs.any():
        raise ValueError("the tested index set must be non-empty")
    channel = np.repeat(np.arange(p), M)
    return pairs.copy(), pairs[channel[:, None], channel[None, :]]


def _validate_grid(grid, M):
    if grid is None:
        return None
    grid = np.asarray(grid, dtype=float)
    if grid.shape != (M,) or not np.isfinite(grid).all() or np.any(np.diff(grid) <= 0):
        raise ValueError("grid must contain M finite, strictly increasing coordinates")
    return grid.copy()


def _validate_options(B, alpha):
    if isinstance(B, (bool, np.bool_)) or not isinstance(B, (int, np.integer)) or B < 1:
        raise ValueError("B must be a positive integer")
    if not np.isscalar(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")


def _weights(multipliers, B, n):
    if np.iscomplexobj(multipliers):
        raise ValueError("multipliers must be real-valued")
    weights = np.asarray(multipliers, dtype=float)
    if weights.shape != (B, n) or not np.isfinite(weights).all():
        raise ValueError("multipliers must have finite shape (B, subjects)")
    return weights


def _get_rng(seed, rng):
    if rng is not None and seed is not None:
        raise ValueError("specify only one of seed and rng")
    return np.random.default_rng(seed if rng is None else rng)


def _centered_weighted_outer(D, qbar, weights):
    # Empirical outer-product centering; raw weights are never changed.
    return D.T @ (weights[:, None] * D) - weights.sum() * qbar


def _decision(T_obs, boot, alpha):
    boot = np.asarray(boot, dtype=float)
    if boot.ndim != 1 or len(boot) < 1 or not np.isfinite(boot).all():
        raise ValueError("bootstrap statistics must be a non-empty finite vector")
    _validate_options(len(boot), alpha)
    if not np.isfinite(T_obs):
        raise ValueError("observed statistic must be finite")
    B = len(boot)
    pvalue = (1 + np.count_nonzero(boot >= T_obs)) / (B + 1)
    # Match p < alpha exactly, including B=9, alpha=0.8 floating boundaries.
    counts = np.arange(B + 1)
    allowed = counts[(1 + counts) / (B + 1) < alpha]
    k = B - int(allowed[-1]) if allowed.size else B + 1
    critical = np.partition(boot, k - 1)[k - 1] if k <= B else np.inf
    return {"statistic": float(T_obs), "pvalue": float(pvalue),
            "critical_value": float(critical), "reject": bool(pvalue < alpha),
            "bootstrap_statistics": boot, "critical_rank": int(k)}


def _metadata(result, n, p, M, pairs, grid, alpha, B, config_id, m=None):
    result.update({
        "method_version": "v1.1",
        "method": "covariance_one_sample" if m is None else "covariance_two_sample_independent",
        "denominator": {"covariance": "n-1" if m is None else "n-1,m-1", "outer_mean": "n" if m is None else "n,m", "bootstrap": "n-1" if m is None else "n-1,m-1"},
        "n": int(n), "p": int(p), "M": int(M), "B": int(B), "alpha": float(alpha),
        "channel_pairs": pairs, "grid": grid, "config_id": config_id,
        "critical_value_rule": "finite_B_pvalue_strict_float_comparison",
        "random_rule": "local_Generator_raw_iid_normal_or_fixed_multipliers"})
    if m is not None:
        result["m"] = int(m)
    return result


def covariance_one_sample(data, gamma0, channel_pairs=None, alpha=0.05, B=500,
                          seed=None, *, multipliers=None, grid=None, rng=None,
                          config_id=None):
    """Test deterministic target (p,p,M,M); None mask tests all channel pairs.

    Fixed raw multipliers (B,n) are optional for auditing. seed accepts a local
    Generator or integer. Global random state is never consumed or modified.
    """
    _validate_options(B, alpha)
    n, p, M, D, cov, qbar = _prepare_group(data)
    grid = _validate_grid(grid, M)
    pairs, mask = _flat_mask(p, M, channel_pairs)
    if np.iscomplexobj(gamma0):
        raise ValueError("gamma0 must be real-valued")
    target = np.asarray(gamma0, dtype=float)
    if target.shape != (p, p, M, M) or not np.isfinite(target).all():
        raise ValueError("gamma0 must have finite shape (p, p, M, M)")
    target_flat = target.transpose(0, 2, 1, 3).reshape(p * M, p * M)
    observed = np.sqrt(n) * np.max(np.abs((cov - target_flat)[mask]))
    generator = _get_rng(seed, rng)
    fixed = None if multipliers is None else _weights(multipliers, B, n)
    boot = np.empty(B)
    for b in range(B):
        xi = generator.standard_normal(n) if fixed is None else fixed[b]
        G = np.sqrt(n) / (n - 1) * _centered_weighted_outer(D, qbar, xi)
        boot[b] = np.max(np.abs(G[mask]))
    return _metadata(_decision(observed, boot, alpha), n, p, M, pairs, grid, alpha, B, config_id)


def covariance_two_sample(data_x, data_y, channel_pairs=None, alpha=0.05,
                          B=500, seed=None, *, multipliers=None, grid=None,
                          grid_y=None, rng=None, config_id=None):
    """Independent groups, separately centered, with optional fixed (xi,eta).

    grid is common to both groups; if supplied, grid_y must agree exactly.
    Separate draws are used for both groups even when their sample sizes match.
    """
    _validate_options(B, alpha)
    n, p, M, Dx, cov_x, qbar_x = _prepare_group(data_x)
    m, py, My, Dy, cov_y, qbar_y = _prepare_group(data_y)
    if (p, M) != (py, My):
        raise ValueError("both groups must have the same channels and grid")
    grid = _validate_grid(grid, M)
    grid_y = _validate_grid(grid_y, M)
    if grid_y is not None and (grid is None or not np.array_equal(grid, grid_y)):
        raise ValueError("both groups must use identical grid coordinates")
    pairs, mask = _flat_mask(p, M, channel_pairs)
    scale = np.sqrt(n * m / (n + m))
    observed = scale * np.max(np.abs((cov_x - cov_y)[mask]))
    generator = _get_rng(seed, rng)
    fixed = None
    if multipliers is not None:
        if not isinstance(multipliers, (tuple, list)) or len(multipliers) != 2:
            raise ValueError("two-sample multipliers must be (xi, eta)")
        fixed = (_weights(multipliers[0], B, n), _weights(multipliers[1], B, m))
    boot = np.empty(B)
    for b in range(B):
        xi = generator.standard_normal(n) if fixed is None else fixed[0][b]
        eta = generator.standard_normal(m) if fixed is None else fixed[1][b]
        G = scale * (_centered_weighted_outer(Dx, qbar_x, xi) / (n - 1)
                     - _centered_weighted_outer(Dy, qbar_y, eta) / (m - 1))
        boot[b] = np.max(np.abs(G[mask]))
    return _metadata(_decision(observed, boot, alpha), n, p, M, pairs, grid, alpha, B, config_id, m=m)


def calculate_u_statistic_matrices(Y):
    """Unbiased covariance, equal to the legacy pair-difference U expression."""
    _, p, M, _, cov, _ = _prepare_group(Y)
    return cov.reshape(p, M, p, M).transpose(0, 2, 1, 3)


def compute_Tn(sigma_hat, n):
    """Legacy zero-cross statistic over all double time coordinates."""
    sigma_hat = np.asarray(sigma_hat, dtype=float)
    if sigma_hat.ndim != 4:
        raise ValueError("sigma_hat must have shape (p,p,M,M)")
    p, py, M, My = sigma_hat.shape
    if p != py or M != My or M < 1 or not np.isfinite(sigma_hat).all() or n < 2:
        raise ValueError("invalid covariance shape, sample size or non-finite values")
    pairs, _ = _flat_mask(p, M, ~np.eye(p, dtype=bool))
    return float(np.sqrt(n) * np.max(np.abs(sigma_hat[pairs])))


def _legacy_result(Y, B, seed):
    data = np.asarray(Y)
    if data.ndim != 3:
        raise ValueError("data must have shape (subjects, channels, grid)")
    p, M = data.shape[1:]
    return covariance_one_sample(data, np.zeros((p, p, M, M)), ~np.eye(p, dtype=bool), B=B, seed=seed)


def multiplier_bootstrap(Y, B=500, seed=None):
    """Legacy bootstrap; returns the matching alpha=0.05 critical value."""
    result = _legacy_result(Y, B, seed)
    return result["critical_value"], result["bootstrap_statistics"]


def covariance_test(Y, B=500, seed=None):
    """Compatible (statistic, critical_value, pvalue) zero-cross test."""
    result = _legacy_result(Y, B, seed)
    return result["statistic"], result["critical_value"], result["pvalue"]
