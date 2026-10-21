from pathlib import Path
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common.paths import STOCK_CACHE_DIR, STOCK_RESULTS_DIR
"""
xue_test.py
  - Xue 风格极值型检验（单样本适配）
  - T_n = log log(ps) - 4 log(ps) + max_{j1!=j2,k1,k2} n*sigma^2 / m
  - 在零假设 H0: a_{i,j1,k1}, a_{i,j2,k2} 不相关 (j1!=j2) 下渐近 Gumbel
  - F(x)=exp{-(8π)^(-1/2) exp(-x/2)}
  - τ_α = -log(8π) - 2 log log(1/(1-α))
"""
import numpy as np

def compute_xue_statistic(a):
    """a: (n, p, q) 基系数张量"""
    n, p, q = a.shape
    a_c = a - a.mean(axis=0, keepdims=True)
    af  = a_c.reshape(n, p*q)
    # σ̂ = E[XY]
    sigma = (af.T @ af) / n                      # (pq, pq)
    # E[X^2 Y^2]
    asq  = (a_c**2).reshape(n, p*q)
    m_raw = (asq.T @ asq) / n
    # m̂ = Var(XY) = E[X^2Y^2] - E[XY]^2
    m_hat = m_raw - sigma**2
    eps = 1e-12
    T = n * sigma**2 / np.maximum(m_hat, eps)    # (pq, pq)
    # 排除 j1 == j2
    T = T.reshape(p, q, p, q)
    for j in range(p): T[j, :, j, :] = -np.inf
    T_max = float(T.max())
    ps = p * q
    Tn  = np.log(np.log(ps)) - 4*np.log(ps) + T_max
    return Tn, T_max

def xue_critical_value(alpha=0.05):
    return -np.log(8*np.pi) - 2*np.log(np.log(1/(1-alpha)))

def xue_pvalue(Tn):
    """1 - F(Tn)，对极大 Tn 用 expm1 保数值稳定"""
    log_F = -(8*np.pi)**(-0.5) * np.exp(-Tn/2)
    return float(-np.expm1(log_F))

def xue_test(a, alpha=0.05):
    n, p, q = a.shape
    Tn, T_max = compute_xue_statistic(a)
    tau = xue_critical_value(alpha)
    pv  = xue_pvalue(Tn)
    return dict(Tn=Tn, T_max_raw=T_max, tau_alpha=tau,
                p_value=pv, reject=Tn > tau, n=n, p=p, q=q)