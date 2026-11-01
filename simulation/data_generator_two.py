"""Brownian compatibility entry points; M2 is the v1.1 model name."""
import numpy as np

from simulation.data_generation import legacy_result, legacy_task
from simulation.data_generator_one import generate_sparse_covariance


def generate_brownian_motions(n, p, M, rng=None):
    """Exact closed-grid Brownian samples with M-1 independent increments."""
    if n < 1 or p < 1 or M < 2:
        raise ValueError("require n>=1, p>=1 and M>=2")
    rng = np.random.default_rng(rng)
    grid = np.linspace(0, 1, M)
    increments = rng.standard_normal((n, p, M-1)) * np.sqrt(np.diff(grid))
    brownian = np.zeros((n, p, M))
    brownian[:, :, 1:] = np.cumsum(increments, axis=2)
    return brownian, grid


def generate_signal_M1(u_grid, a=0.):
    """Legacy deterministic mean extension; formal v1.1 scenes have a=0."""
    return a * np.sin(np.asarray(u_grid)**2)


def create_dataset_M1(n, p, M, a=0., sigma_noise=.05, h0=True, s0=4,
                      signal_strength=.3, seed=None, task=None, replicate=0):
    """Legacy Brownian name retained; returned model metadata is M2.

    An explicit task is authoritative and is hashed without modifications.
    """
    config = task if task is not None else legacy_task(
        "M2", n, p, M, sigma_noise, h0, s0, signal_strength, seed,
        mean_amplitude=a)
    if config["model"] != "M2":
        raise ValueError("Brownian entry point requires model M2")
    result = legacy_result(config, replicate)
    result["params"]["a"] = float(config.get("mean_amplitude", 0.))
    return result
