# xue_helper.py  ——  Xue 方法的实验对照辅助工具
import numpy as np
from common.statistic_calculator_xue import (
    compute_Tn_xue, xue_critical_value, xue_pvalue
)

# 严格按 Xue 原文：s 是基展开截断项数 (q_smooth)，不能默认 = M
S_XUE_DEFAULT = 5


def project_to_fourier_basis(Y, s):
    """
    把网格观测 Y: (n, p, M) 投影到 s 个 Fourier 基系数 -> (n, p, s)
    基函数: phi_0 = 1, phi_{2k-1} = sqrt(2)sin(2*pi*k*u), phi_{2k} = sqrt(2)cos(2*pi*k*u)
    系数用矩形积分近似: c = (1/M) sum_i Y(u_i) phi(u_i)
    """
    n, p, M = Y.shape
    u = np.linspace(0.0, 1.0, M)
    B = np.empty((M, s))
    B[:, 0] = 1.0
    for k in range(1, s):
        kk = (k + 1) // 2
        if k % 2 == 1:
            B[:, k] = np.sqrt(2.0) * np.sin(2.0 * np.pi * kk * u)
        else:
            B[:, k] = np.sqrt(2.0) * np.cos(2.0 * np.pi * kk * u)
    return np.einsum('npm,ms->nps', Y, B) / M


def run_xue_test(Y_grid, s=S_XUE_DEFAULT, alpha=0.05):
    """
    一次性完成: 基投影 -> 计算 Tn -> Gumbel p 值 -> 临界值。
    输入: Y_grid (n, p, M)
    返回: (Tn, tau_alpha, pval)
    """
    C = project_to_fourier_basis(Y_grid, s)
    Tn = compute_Tn_xue(C, s=s)
    tau = xue_critical_value(alpha)
    pval = xue_pvalue(Tn, legacy=True)
    return Tn, tau, pval
