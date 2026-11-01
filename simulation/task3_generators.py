"""Task3 finite Fourier alternatives and untouched legacy DGP references.

Only data generation and deterministic truth diagnostics live here.  All
tests receive observed curves and the complete noise-inclusive null target.
"""
import hashlib
import json

import numpy as np

from simulation.data_generation import (
    fourier_literal_basis, make_rng, sample_curves, sparse_correlation,
)
from common.xue_helper import projection_operator


def spec_ids():
    """Eight new specifications followed by two legacy full references."""
    return ["spectrum_fast_b4", "spectrum_slow_b1", "spectrum_flat_b0",
            "band_head", "band_tail", "coherent_all", "coherent_tail",
            "local_fejer", "legacy_M1_full_reference", "legacy_M2_full_reference"]


def _integer(value, name, minimum):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < minimum:
        raise ValueError("%s must be an integer >= %s" % (name, minimum))
    return int(value)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def _fourier(grid):
    angles = 2 * np.pi * np.asarray(grid)[:, None] * np.arange(1, 11)[None, :]
    basis = np.empty((len(grid), 20))
    basis[:, 0::2], basis[:, 1::2] = np.sqrt(2)*np.sin(angles), np.sqrt(2)*np.cos(angles)
    return basis


def _geometry(scenario):
    grid = np.asarray(scenario["grid"], dtype=float)
    spec = scenario["spec_id"]
    if scenario["family"] == "legacy":
        basis = fourier_literal_basis(grid).T if scenario["model"] == "M1" else np.eye(len(grid))
        covariance = np.diag(np.arange(1., 6.)**-2) if scenario["model"] == "M1" else np.minimum.outer(grid, grid)
        kernel = basis @ covariance @ basis.T
        return basis, covariance, covariance / np.max(np.abs(kernel))
    basis = _fourier(grid)
    beta = {"spectrum_fast_b4": 4., "spectrum_slow_b1": 1., "spectrum_flat_b0": 0.}.get(spec, 0.)
    weights = np.arange(1., 11.)**-beta
    weights /= weights.sum()
    covariance = np.diag(np.repeat(weights/2, 2))
    shape = covariance.copy()
    if scenario["family"] == "task3_band":
        indices = np.arange(8) if spec == "band_head" else np.arange(12, 20)
        shape = np.diag(np.isin(np.arange(20), indices).astype(float)/8)
    if scenario["family"] == "task3_coherent":
        indices = np.arange(20) if spec == "coherent_all" else np.arange(12, 20)
        coefficient = np.zeros(20)
        coefficient[indices] = _fourier([3/8])[0, indices]/len(indices)
        shape = np.outer(coefficient, coefficient)
    if scenario["family"] == "task3_local":
        taper = np.repeat(1-np.arange(1., 11.)/11, 2)/10
        coefficient = _fourier([3/8])[0] * taper
        shape = np.outer(coefficient, coefficient)
    return basis, covariance, shape


def make_scenario(spec_id, tau, n=200, p=20):
    """Create the complete JSON-compatible immutable-by-convention DGP."""
    if spec_id not in spec_ids():
        raise ValueError("unknown task3 specification: %s" % spec_id)
    n, p = _integer(n, "n", 2), _integer(p, "p", 4)
    tau = float(tau)
    if not np.isfinite(tau) or tau < 0:
        raise ValueError("tau must be finite and nonnegative")
    legacy = spec_id.startswith("legacy_")
    families = {"spectrum": "task3_spectrum", "band": "task3_band",
                "coherent": "task3_coherent", "local": "task3_local", "legacy": "legacy"}
    family = families[spec_id.split("_")[0]]
    null_group = spec_id if legacy else {"spectrum_fast_b4": "spectrum_fast_b4",
                                        "spectrum_slow_b1": "spectrum_slow_b1"}.get(spec_id, "spectrum_flat_b0")
    scenario = dict(study="task3_v1", spec_id=spec_id, family=family,
                    null_group_id=null_group, n=n, p=p, tau=tau, M=30 if legacy else 64,
                    q=5 if legacy else 20, sigma_noise=.05, mean_amplitude=0.,
                    support_mode="legacy_upper_triangle" if legacy else "matching",
                    support_policy="redraw_each_replicate_allow_shared_vertices" if legacy else "redraw_matching_each_replicate",
                    s0=4, grid_id="closed_0_1_M30" if legacy else "periodic_endpoint_excluded_M64",
                    grid=np.linspace(0, 1, 30).tolist() if legacy else (np.arange(64)/64).tolist(),
                    basis="phi_1_to_phi_5" if legacy else "phi_1_to_phi_20", model=spec_id.split("_")[1] if legacy else "finite_fourier")
    basis, covariance, shape = _geometry(scenario)
    if legacy:
        kappa = float(np.max(np.abs(basis @ covariance @ basis.T)))
        scenario.update(kappa=kappa, legacy_delta=tau/kappa, c=1., beta=2.)
        rho = np.sqrt(2)*tau/kappa  # Worst possible support for two legacy edges.
    else:
        scale = 1/np.sqrt(np.diag(covariance))
        rho = tau * np.linalg.norm(scale[:, None]*shape*scale[None, :], 2)
        scenario.update(lambda_diagonal=np.diag(covariance).tolist(),
                        signal_cov_shape=shape.tolist(), t0=3/8, H=10)
    if rho >= 1:
        raise ValueError("coefficient covariance is not positive definite; no repair is permitted")
    return scenario


def data_key(scenario, phase, replicate):
    """Canonical distribution key: excludes scheduling and inactive H1 fields."""
    if phase not in ("smoke", "benchmark", "pilot", "confirm"):
        raise ValueError("unknown task3 phase")
    replicate = _integer(replicate, "replicate", 0)
    fields = ("study", "n", "p", "M", "q", "sigma_noise", "mean_amplitude", "grid_id", "grid", "basis", "model")
    key = {name: scenario[name] for name in fields}
    key.update(phase=phase, replicate=replicate, tau=scenario["tau"])
    if scenario["tau"] == 0:
        key["null_group_id"] = scenario["null_group_id"]
    else:
        key.update(alternative_spec_id=scenario["spec_id"], s0=scenario["s0"],
                   support_mode=scenario["support_mode"], support_policy=scenario["support_policy"])
    if scenario["family"] != "legacy":
        key["lambda_diagonal"] = scenario["lambda_diagonal"]
    if scenario["tau"] > 0 and scenario["family"] != "legacy":
        key["signal_cov_shape"] = scenario["signal_cov_shape"]
    if scenario["family"] == "legacy":
        key.update(c=1., beta=2., legacy_delta=scenario["legacy_delta"])
    return key


def _seed_task(scenario, phase, replicate):
    task = data_key(scenario, phase, replicate)
    if scenario["family"] == "legacy":
        task.update(grid="closed_0_1", basis="phi_1_to_phi_5", c=1., beta=2.,
                    s0=4 if scenario["tau"] else 0, delta=scenario["legacy_delta"],
                    support_policy="redraw_each_replicate_allow_shared_vertices")
    return task


def rng(scenario, phase, replicate, stream):
    """Reuse frozen SHA-256/SeedSequence streams with task3 distribution keys."""
    return make_rng(_seed_task(scenario, phase, replicate), replicate, stream)


def generate(scenario, phase, replicate):
    """Generate observed data once, with a complete full-known null target."""
    key = data_key(scenario, phase, replicate)
    n, p, M, tau = scenario["n"], scenario["p"], scenario["M"], scenario["tau"]
    basis, covariance, shape = _geometry(scenario)
    kernel = basis @ covariance @ basis.T
    metadata = dict(tau=tau, noise_variance=scenario["sigma_noise"]**2,
                    data_key=key, base_seed=20261021, edges_zero_based=[])
    if scenario["family"] == "legacy":
        task = _seed_task(scenario, phase, replicate)
        C, edges = sparse_correlation(p, 4 if tau else 0, scenario["legacy_delta"],
                                     rng(scenario, phase, replicate, "support"))
        observed, grid, kernel = sample_curves(task, replicate, n, C)
        metadata.update(legacy_task=task, C=C, edges_zero_based=edges,
                        kappa=scenario["kappa"], legacy_delta=scenario["legacy_delta"],
                        min_channel_eigenvalue=float(np.linalg.eigvalsh(C)[0]))
    else:
        z = rng(scenario, phase, replicate, "signal").standard_normal((n, p, 20))
        coefficients = z * np.sqrt(np.diag(covariance))[None, None, :]
        edges = []
        if tau:
            vertices = rng(scenario, phase, replicate, "support").choice(p, size=4, replace=False)
            edges = [(int(vertices[i]), int(vertices[i+1])) for i in (0, 2)]
            root_plus, root_minus = np.linalg.cholesky(covariance+tau*shape), np.linalg.cholesky(covariance-tau*shape)
            for j, k in edges:
                plus, minus = z[:, j] @ root_plus.T, z[:, k] @ root_minus.T
                coefficients[:, j], coefficients[:, k] = (plus+minus)/np.sqrt(2), (plus-minus)/np.sqrt(2)
        noise = rng(scenario, phase, replicate, "noise").normal(0., scenario["sigma_noise"], (n, p, M))
        observed, grid = coefficients @ basis.T + noise, np.asarray(scenario["grid"])
        metadata.update(edges_zero_based=edges)
    target_block = kernel + scenario["sigma_noise"]**2*np.eye(M)
    gamma0 = np.einsum("ij,lm->ijlm", np.eye(p), target_block)
    return dict(Y=observed, grid=grid, gamma0=gamma0, truth_metadata=metadata,
                data_id=_digest(key))


def diagnostics(scenario):
    """Channel-level truth and actual-grid projections, without p²M² blocks.

    Full null and alternative targets reconstruct as I_p tensor null_block
    and tau*E tensor signal_time_kernel.  The fixed support template is only
    for truth diagnostics; generate() records the randomly drawn support.
    """
    basis, covariance, shape = _geometry(scenario)
    M, tau, p = scenario["M"], scenario["tau"], scenario["p"]
    kernel, signal = basis @ covariance @ basis.T, basis @ shape @ basis.T
    null = kernel + scenario["sigma_noise"]**2*np.eye(M)
    legacy = scenario["family"] == "legacy"
    whitened_norm = 1/scenario["kappa"] if legacy else float(np.linalg.norm(
        shape/np.sqrt(np.diag(covariance)[:, None]*np.diag(covariance)[None, :]), 2))
    support_norm = np.sqrt(2) if legacy else 1.
    projections = {}
    for s in (5, 11, 21):
        L = projection_operator(1, M, s, grid=np.asarray(scenario["grid"]))
        design = L.T*M
        delta = tau*(L @ signal @ L.T)
        target = L @ null @ L.T
        reconstruction = design @ delta @ design.T
        Q = np.linalg.qr(design, mode="reduced")[0]
        orthogonal = Q @ (Q.T @ signal @ Q) @ Q.T
        frobenius_ratio = float(np.linalg.norm(orthogonal)/np.linalg.norm(signal)) if tau else None
        denominator = np.sqrt(np.diag(target)[:, None]*np.diag(target)[None, :])
        projections[str(s)] = dict(
            s=s, channel_operator=L, null_coefficient_covariance=target,
            signal_coefficient_difference=delta, coefficient_max_difference=float(np.max(np.abs(delta))),
            reconstructed_peak_ratio=float(np.max(np.abs(reconstruction))/(tau*np.max(np.abs(signal)))) if tau else None,
            orthogonal_frobenius_ratio=frobenius_ratio,
            energy_ratio=frobenius_ratio**2 if tau else None,
            standardized_null_effect=float(np.sqrt(scenario["n"])*np.max(np.abs(delta)/denominator)),
            full_operator_rule="I_p kron channel_operator",
            full_null_rule="I_p kron null_coefficient_covariance",
            full_delta_rule="E kron signal_coefficient_difference")
    return dict(
        scenario=dict(scenario), basis=basis, grid=np.asarray(scenario["grid"]),
        lambda_diagonal=np.diag(covariance), coefficient_null_covariance=covariance,
        signal_cov_shape=shape, null_time_block=null, signal_time_kernel=signal,
        support_template_zero_based=[[0, 1], [0, 2]] if legacy else [[0, 1], [2, 3]],
        support_template_operator_norm=support_norm, support_frobenius_squared=4.,
        latent_point_variance=np.diag(kernel), observed_point_variance=np.diag(null),
        maximum_marginal_variance=float(np.diag(null).max()), average_marginal_variance=float(np.diag(null).mean()),
        time_peak_effect=float(tau*np.max(np.abs(signal))), signal_cov_shape_frobenius=float(np.linalg.norm(shape)),
        weighted_frobenius_effect=float(2*tau*np.linalg.norm(signal)/M),
        whitened_signal_operator_norm=whitened_norm, rho=float(tau*whitened_norm*support_norm),
        positive_definiteness_bound="rho < 1; legacy rho is the worst two-edge support bound",
        full_null_rule="I_p kron null_time_block", full_delta_rule="tau E kron signal_time_kernel",
        null_group_id=scenario["null_group_id"], projections=projections)
