# statistic_calculator_xue.py
import numpy as np


def compute_Tn_xue(Y, s=None, eps=1e-10):
    """
    单样本 Xue 型 studentized 极值统计量（单样本化简版）
        T_n = log log(ps) - 4 log(ps) + max_{j1!=j2} n * sigma_hat^2 / m_hat

    参数:
        Y: (n, p, M) 输入张量
        s: 基展开截断项数（Fourier 基函数个数，即 q_smooth）。
           默认为 None 时使用 M，但建议显式传入正确的 s 值。
    返回:
        Tn (float)
    """
    n, p, M = Y.shape
    if s is None:
        s = M  # 向后兼容，默认值
    Y_flat = Y.reshape(n, p * M)
    Yc = Y_flat - Y_flat.mean(0, keepdims=True)

    # 协方差（用 1/n 与 Xue 理论保持一致）
    sigma_2d = (Yc.T @ Yc) / n                       # (pM, pM)

    # 4 阶矩估计:  m_ab = E[xi_a^2 xi_b^2] - sigma_ab^2
    Yc2 = Yc ** 2
    E_xi2 = (Yc2.T @ Yc2) / n                        # (pM, pM)
    m_hat = E_xi2 - sigma_2d ** 2
    m_hat = np.maximum(m_hat, eps)

    # Studentized statistic
    studentized = n * sigma_2d ** 2 / m_hat          # (pM, pM)

    # Reshape 到 (p, p, M, M) 并取 j1 != j2 块的最大值
    s_4d = studentized.reshape(p, M, p, M).transpose(0, 2, 1, 3)  # (p, p, M, M)
    mask = ~np.eye(p, dtype=bool)
    max_val = s_4d[mask].max()

    Tn = max_val - 4.0 * np.log(p * s) + np.log(np.log(p * s))
    return Tn


def xue_critical_value(alpha):
    """Gumbel 渐近临界值: tau_alpha = -log(8 pi) - 2 log log(1/(1-alpha))"""
    return -np.log(8 * np.pi) - 2 * np.log(np.log(1.0 / (1.0 - alpha)))


def xue_pvalue(Tn, *, legacy=False):
    """基于 Gumbel CDF 的 p-value: P(T > Tn) = 1 - F(Tn)"""
    if legacy:
        # Preserve the original simulation's floating-point calculation.
        F_Tn = np.exp(-((8 * np.pi) ** -0.5) * np.exp(-Tn / 2))
        return 1.0 - F_Tn
    a = (8 * np.pi) ** -0.5
    z = a * np.exp(-Tn / 2)
    return -np.expm1(-z)


def gumbel_pdf(x):
    """对应的 PDF（绘图用）"""
    a = (8 * np.pi) ** -0.5
    return a * 0.5 * np.exp(-x / 2) * np.exp(-a * np.exp(-x / 2))
