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
from common.statistic_calculator_xue import (
    xue_cross_zero, xue_critical_value as _critical, xue_pvalue as _pvalue,
)


def _audited_cross(a, alpha=0.05):
    result = xue_cross_zero(a, s=np.asarray(a).shape[-1], alpha=alpha)
    if result['status'] != 'ok':
        raise ValueError(f"Xue cross test failed: {result['failure_reason']}")
    return result

def compute_xue_statistic(a):
    """a: (n, p, q) 基系数张量"""
    result = _audited_cross(a)
    return result['T'], result['Q']

def xue_critical_value(alpha=0.05):
    return _critical(alpha)

def xue_pvalue(Tn):
    """1 - F(Tn)，对极大 Tn 用 expm1 保数值稳定"""
    return _pvalue(Tn)

def xue_test(a, alpha=0.05):
    n, p, q = a.shape
    result = _audited_cross(a, alpha)
    return dict(result, Tn=result['T'], T_max_raw=result['Q'],
                tau_alpha=result['critical_T'], n=n, p=p, q=q,
                version='xue-audit-v1')
