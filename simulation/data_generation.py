"""Frozen v1.1 Fourier/Brownian DGP and independent reproducible streams.

The task JSON is hashed exactly as specified in docs/两套模拟数据生成.
All public generators leave NumPy's global RNG untouched.
"""
import hashlib
import json

import numpy as np

BASE_SEED = 20261021
STREAM_IDS = {"support": 1, "signal": 2, "noise": 3, "bootstrap": 4}
GROUP_IDS = {"single": 0, "X": 1, "Y": 2}


def _integer(value, name, minimum=0):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


def make_rng(task, replicate, stream, group="single"):
    """Stable SHA-256 task seed, split by replicate, stream and group."""
    replicate = _integer(replicate, "replicate")
    if stream not in STREAM_IDS or group not in GROUP_IDS:
        raise ValueError("unknown random stream or group")
    payload = json.dumps(task, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("utf-8")
    digest = int.from_bytes(hashlib.sha256(payload).digest()[:8], "little")
    seed64 = (BASE_SEED + digest + replicate * 13579) % (1 << 64)
    return np.random.default_rng(np.random.SeedSequence([
        seed64 & 0xffffffff, seed64 >> 32, STREAM_IDS[stream], GROUP_IDS[group]]))


def sparse_correlation(p, s0, delta, rng):
    """Draw s0/2 distinct upper-triangle edges, allowing shared vertices."""
    p, s0 = _integer(p, "p", 2), _integer(s0, "s0")
    if s0 % 2 or s0 > p * (p - 1):
        raise ValueError("s0 must be even and <= p*(p-1)")
    if not np.isfinite(delta) or (s0 == 0 and delta != 0) or (s0 > 0 and delta <= 0):
        raise ValueError("use s0=delta=0 under H0 and positive delta under H1")
    upper_i, upper_j = np.triu_indices(p, k=1)
    chosen = rng.choice(len(upper_i), size=s0 // 2, replace=False)
    edge_i, edge_j = upper_i[chosen], upper_j[chosen]
    C = np.eye(p)
    C[edge_i, edge_j] = delta
    C[edge_j, edge_i] = delta
    symmetric_sqrt(C)  # Validate without altering the sampled matrix.
    return C, [(int(i), int(j)) for i, j in zip(edge_i, edge_j)]


def symmetric_sqrt(C):
    """Symmetric positive-definite square root; never repair eigenvalues."""
    C = np.asarray(C, dtype=float)
    if C.ndim != 2 or C.shape[0] != C.shape[1] or not np.isfinite(C).all():
        raise ValueError("C must be a finite square matrix")
    if not np.allclose(C, C.T, rtol=1e-12, atol=1e-12):
        raise ValueError("C must be symmetric")
    values, vectors = np.linalg.eigh(C)
    if values[0] <= 1e-12:
        raise ValueError("C must be positive definite; do not silently repair")
    return (vectors * np.sqrt(values)[None, :]) @ vectors.T


def fourier_literal_basis(u):
    """Rows phi_1,...,phi_5: sin1, cos1, sin2, cos2, sin3."""
    u = np.asarray(u, dtype=float)
    if u.ndim != 1 or not np.isfinite(u).all():
        raise ValueError("u must be a finite one-dimensional grid")
    return np.sqrt(2.0) * np.stack([
        np.sin(2*np.pi*u), np.cos(2*np.pi*u), np.sin(4*np.pi*u),
        np.cos(4*np.pi*u), np.sin(6*np.pi*u)])


def _sample_components(task, replicate, n, C, group):
    n = _integer(n, "n", 2)
    p, M = _integer(task["p"], "p", 2), _integer(task["M"], "M", 2)
    C = np.asarray(C, dtype=float)
    if C.shape != (p, p):
        raise ValueError("C shape must match task p")
    if task["grid"] != "closed_0_1" or task["basis"] != "phi_1_to_phi_5":
        raise ValueError("only the frozen closed grid and literal Fourier basis are implemented")
    if task["q"] != 5 or task["c"] != 1.0 or task["beta"] != 2.0:
        raise ValueError("only q=5, c=1, beta=2 are implemented")
    sigma = float(task["sigma_noise"])
    if sigma < 0 or not np.isfinite(sigma):
        raise ValueError("sigma_noise must be finite and nonnegative")
    u, L = np.linspace(0, 1, M), symmetric_sqrt(C)
    signal_rng = make_rng(task, replicate, "signal", group)
    noise_rng = make_rng(task, replicate, "noise", group)
    if task["model"] == "M1":
        phi = fourier_literal_basis(u)
        eigenvalues = np.arange(1., 6.) ** -2
        z = signal_rng.standard_normal((n, p, 5))
        coefficients = np.einsum("ij,ajk->aik", L, z, optimize=True)
        coefficients *= np.sqrt(eigenvalues)[None, None, :]
        signal = np.einsum("aik,kl->ail", coefficients, phi, optimize=True)
        K = (phi.T * eigenvalues[None, :]) @ phi
    elif task["model"] == "M2":
        increments = signal_rng.standard_normal((n, p, M-1))
        increments *= np.sqrt(np.diff(u))[None, None, :]
        brownian = np.zeros((n, p, M))
        brownian[:, :, 1:] = np.cumsum(increments, axis=2)
        signal = np.einsum("ij,ajl->ail", L, brownian, optimize=True)
        K = np.minimum.outer(u, u)
    else:
        raise ValueError("model must be M1 or M2")
    mean_amplitude = float(task.get("mean_amplitude", 0.0))
    if not np.isfinite(mean_amplitude):
        raise ValueError("mean_amplitude must be finite")
    signal += mean_amplitude * np.sin(u**2)[None, None, :]
    noise = noise_rng.normal(0., sigma, (n, p, M))
    return signal, noise, u, K


def sample_curves(task, replicate, n, C, group="single"):
    """Return observed curves (n,p,M), closed grid and latent time kernel."""
    signal, noise, u, K = _sample_components(task, replicate, n, C, group)
    return signal + noise, u, K


def simulate_one(task, replicate):
    """Draw support once per replicate, shared by all subjects and methods."""
    if task["support_policy"] != "redraw_each_replicate_allow_shared_vertices":
        raise ValueError("only support redrawn each replicate with shared vertices is implemented")
    p, n = _integer(task["p"], "p", 2), _integer(task["n"], "n", 2)
    C, edges = sparse_correlation(p, task["s0"], task["delta"],
                                 make_rng(task, replicate, "support"))
    signal, noise, u, K = _sample_components(task, replicate, n, C, "single")
    return dict(Y=signal+noise, X_true=signal, noise=noise, grid=u, C=C,
                latent_time_kernel=K, noise_variance=float(task["sigma_noise"])**2,
                edges_zero_based=edges, task=dict(task), replicate=int(replicate),
                base_seed=BASE_SEED)


def legacy_task(model, n, p, M, sigma_noise, h0, s0, delta, seed,
                q=5, c=1., beta=2., mean_amplitude=0.):
    """Identify legacy calls explicitly while applying frozen v1.1 mathematics."""
    task = dict(experiment="legacy_api", model=model, n=n, p=p, M=M,
                s0=0 if h0 else s0, delta=0. if h0 else delta,
                sigma_noise=sigma_noise, grid="closed_0_1", basis="phi_1_to_phi_5",
                q=q, c=c, beta=beta,
                support_policy="redraw_each_replicate_allow_shared_vertices")
    if seed is not None:
        task["legacy_seed"] = _integer(seed, "seed")
    if mean_amplitude != 0:
        task["mean_amplitude"] = mean_amplitude
    return task


def legacy_result(task, replicate):
    result = simulate_one(task, replicate)
    edges = result["edges_zero_based"]
    result.update(Sigma_star=result["C"], is_h0=task["s0"] == 0,
                  signal_indices=[edge for i, j in edges for edge in ((i, j), (j, i))] or None,
                  params=dict(task))
    result["params"].update(signal_strength=task["delta"],
                            decay_rate=task["c"], decay_power=task["beta"])
    return result
