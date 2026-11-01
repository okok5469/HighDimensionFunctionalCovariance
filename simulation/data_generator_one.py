"""Fourier compatibility entry points; production data follow frozen v1.1."""
import numpy as np

from simulation.data_generation import legacy_result, legacy_task, sparse_correlation


def generate_fourier_basis(M, q):
    """Legacy constant-first basis preserved for independent projection methods.

    This is separate from the M1 DGP's phi_1,...,phi_5 basis.
    """
    t = np.linspace(0, 1, M)
    basis = np.empty((M, q))
    basis[:, 0] = 1.0
    for idx in range(1, q):
        k = (idx + 1) // 2
        trig = np.sin if idx % 2 else np.cos
        basis[:, idx] = np.sqrt(2) * trig(2 * np.pi * k * t)
    return basis


def generate_coefficients(n, p, q, decay_rate=1., decay_power=2, rng=None):
    """Independent coefficients for the legacy low-level helper."""
    rng = np.random.default_rng(rng)
    scales = np.sqrt(decay_rate * np.arange(1., q+1) ** (-decay_power))
    return rng.standard_normal((n, p, q)) * scales


def generate_function_data(a, basis):
    return np.asarray(a) @ np.asarray(basis).T


def generate_sparse_covariance(p, s0, signal_strength, rng=None):
    C, edges = sparse_correlation(p, s0, signal_strength, np.random.default_rng(rng))
    return C, [edge for i, j in edges for edge in ((i, j), (j, i))]


def create_dataset(n, p, M, q=5, decay_rate=1., decay_power=2,
                   sigma_noise=.05, h0=True, s0=4, signal_strength=.3,
                   seed=None, task=None, replicate=0):
    """Legacy keys plus v1.1 metadata; seed identifies a legacy task field.

    An explicit task is authoritative and is hashed without modifications.
    Only the frozen q=5, c=1, beta=2 DGP is accepted.
    """
    config = task if task is not None else legacy_task(
        "M1", n, p, M, sigma_noise, h0, s0, signal_strength, seed,
        q=q, c=decay_rate, beta=decay_power)
    if config["model"] != "M1":
        raise ValueError("Fourier entry point requires model M1")
    return legacy_result(config, replicate)
