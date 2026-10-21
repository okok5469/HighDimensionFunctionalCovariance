"""
data_generator_M3.py
====================
M3 模型数据生成器 —— 函数型 MA(1) (基于布朗运动 + 积分核)
用于高维函数型数据协方差单样本检验的模拟研究

完整数学模型 (M3):
┌─────────────────────────────────────────────────────────────────┐
│  X_{t,j}(u) = a · {1/(1+e^{-u}) - 0.4} + X̃_{t,j}(u)              │
│                                                                 │
│  X̃_t(u) = ∫ X̌_{t-1}(v) · ψ(u,v) dv + X̌_t(u)                     │
│                                                                 │
│  ψ(u,v) = 1.2247 · min(u, v)                                    │
│  X̌_t(u) = A · ε_t(u)                                            │
│                                                                 │
│  ε_t: p 条 i.i.d. 标准布朗运动 on [0, 1]                         │
│  A = S^{1/2}                                                    │
│                                                                 │
│  协方差检验框架 (沿用 M1 惯例):                                  │
│    H0: S = I_p        (变量间独立)                               │
│    H1: S = I_p + Ω    (稀疏扰动)                                 │
└─────────────────────────────────────────────────────────────────┘

关键性质:
  - 算子 Ψ(f)(u) = ∫ f(v) ψ(u,v) dv 的 Hilbert-Schmidt 范数 = 1/2 < 1
    (因 ‖min(u,v)‖_HS² = 1/6, 而 1.2247² ≈ 3/2, 故 ‖ψ‖_HS = √(3/2·1/6)=1/2)
  - 这是函数型 MA(1): X̃_t = Ψ(X̌_{t-1}) + X̌_t
  - 样本间有时间相关性: Cov(X̃_t, X̃_{t-1}) ≠ 0 (通过共享 X̌_{t-1})
  - 跨变量独立性 (H0) 仍由 A=I_p 决定, 不受积分核影响
"""
import numpy as np
from scipy.linalg import sqrtm


# ============================================================
# 模块一: 布朗运动路径生成 (与 M1 相同)
# ============================================================
def generate_brownian_motions(n, p, M):
    """
    生成 n 个样本, 每个样本含 p 条独立标准布朗运动.

    返回:
        BM      : (n, p, M) 布朗运动路径
        u_grid  : (M,)      网格点
    """
    u_grid = np.linspace(0, 1, M)
    du = u_grid[1] - u_grid[0]                  # Δu = 1/(M-1)

    increments = np.random.normal(loc=0.0, scale=np.sqrt(du), size=(n, p, M))
    increments[:, :, 0] = 0.0                   # B(0) = 0
    BM = np.cumsum(increments, axis=2)          # B(u_m) = Σ ΔB
    return BM, u_grid


# ============================================================
# 模块二: 均值函数 (M3 特有)
# ============================================================
def generate_signal_M3(u_grid, a=0.0):
    """
    M3 均值函数:  μ(u) = a · {1/(1+e^{-u}) - 0.4}

    协方差检验默认 a=0 (内部会做中心化, a 不影响检验水平)。
    """
    return a * (1.0 / (1.0 + np.exp(-u_grid)) - 0.4)


# ============================================================
# 模块三: 稀疏协方差扰动 (与 M1 相同)
# ============================================================
def generate_sparse_covariance(p, s0, signal_strength):
    """
    H1 下生成稀疏对称协方差矩阵: S = I_p + Ω.
    s0 必须为偶数 (保证对称).
    """
    Sigma_star = np.eye(p)

    if s0 % 2 != 0:
        raise ValueError("s0 必须为偶数, 以保证对称性。")

    num_pairs = s0 // 2
    all_indices = [(i, j) for i in range(p) for j in range(i + 1, p)]
    selected_pairs = np.random.choice(len(all_indices), num_pairs, replace=False)

    non_zero_indices = []
    for idx in selected_pairs:
        i, j = all_indices[idx]
        Sigma_star[i, j] = signal_strength
        Sigma_star[j, i] = signal_strength
        non_zero_indices.append((i, j))
        non_zero_indices.append((j, i))

    return Sigma_star, non_zero_indices


# ============================================================
# 模块四: 主数据生成接口
# ============================================================
def create_dataset_M3(n, p, M,
                      a=0.0,
                      sigma_noise=0.05,
                      h0=True,
                      s0=4,
                      signal_strength=0.3,
                      psi_const=1.2247,
                      seed=None):
    """
    M3 模型 (函数型 MA(1) + 布朗运动) 数据生成主接口.
    输出格式与 create_dataset / create_dataset_M1 完全一致.

    ┌──────────────────────────────────────────────────────────────┐
    │ 完整生成流程:                                                 │
    │                                                              │
    │ Step 1:  生成 n+1 条独立 p-维布朗运动 ε_t  (t=0,...,n)         │
    │          (需要额外的 ε_0 用于计算第一个 X̃_1)                   │
    │                                                              │
    │ Step 2:  构造截面协方差 S, 计算 X̌_t = A·ε_t                   │
    │            H0:  A = I_p                                      │
    │            H1:  A = (I_p + Ω)^{1/2}                          │
    │                                                              │
    │ Step 3:  应用积分核:                                          │
    │          X̃_t(u_m) = du · Σ_l X̌_{t-1}(v_l)·ψ(u_m,v_l) + X̌_t   │
    │                                                              │
    │ Step 4:  X_{t,j}(u) = a · {1/(1+e^{-u}) - 0.4} + X̃_{t,j}(u)  │
    │                                                              │
    │ Step 5:  Y_{t,j}(u_m) = X_{t,j}(u_m) + 噪声                   │
    └──────────────────────────────────────────────────────────────┘

    参数:
        n (int)               : 样本量
        p (int)               : 变量维度
        M (int)               : 网格点数
        a (float)             : 均值函数强度 (默认 0)
        sigma_noise (float)   : 测量噪声标准差
        h0 (bool)             : True 为零假设 (S=I_p), False 为备择
        s0 (int)              : H1 下非零元素个数 (偶数)
        signal_strength (float): H1 下信号强度
        psi_const (float)     : 积分核常数, 默认 1.2247 (对应 ‖ψ‖_HS=1/2)
        seed (int)            : 随机种子

    返回:
        dict, 与 create_dataset_M1 相同的结构.
    """
    if seed is not None:
        np.random.seed(seed)

    # ======================================================
    # Step 1: 生成 n+1 条独立标准布朗运动 ε_t
    # ======================================================
    # 索引 0 → ε_0  (辅助, 用于计算 X̃_1 中的积分项)
    # 索引 1..n → ε_1..ε_n  (对应最终的 t=1..n 个样本)
    BM, u_grid = generate_brownian_motions(n + 1, p, M)         # (n+1, p, M)
    du = u_grid[1] - u_grid[0]

    # ======================================================
    # Step 2: 构造截面协方差 S 并计算 X̌_t = A · ε_t
    # ======================================================
    if h0:
        # H0: A = I_p, 即 X̌_t = ε_t
        Sigma_star = np.eye(p)
        signal_indices = None
        X_check = BM                                            # (n+1, p, M)
    else:
        # H1: 加稀疏扰动
        Sigma_star, signal_indices = generate_sparse_covariance(p, s0, signal_strength)
        A = sqrtm(Sigma_star)
        A_real = np.real(A)                                     # 去除数值虚部

        # X_check[t, j, m] = Σ_k A[j,k] · BM[t, k, m]
        X_check = np.einsum('jk,tkm->tjm', A_real, BM)          # (n+1, p, M)

    # ======================================================
    # Step 3: 应用积分核  ψ(u,v) = psi_const · min(u, v)
    # ======================================================
    # 离散化:  ∫ X̌_{t-1}(v) ψ(u_m, v) dv
    #         ≈ du · Σ_l X̌_{t-1}(v_l) · ψ(u_m, v_l)
    #
    # 提取相邻样本对:
    X_check_prev = X_check[0:n]        # (n, p, M)  ← X̌_0..X̌_{n-1}
    X_check_curr = X_check[1:n + 1]    # (n, p, M)  ← X̌_1..X̌_n

    # 构造核矩阵 psi[m, l] = psi_const · min(u_m, v_l)   shape (M, M)
    psi = psi_const * np.minimum(u_grid[:, None], u_grid[None, :])

    # 离散积分:  integral[t, j, m] = du · Σ_l X_check_prev[t, j, l] · psi[m, l]
    integral = np.einsum('tjl,ml->tjm', X_check_prev, psi) * du   # (n, p, M)

    # X̃_t = ∫ X̌_{t-1}·ψ dv + X̌_t
    X_tilde = integral + X_check_curr                              # (n, p, M)

    # ======================================================
    # Step 4: 叠加均值函数  μ(u) = a · {1/(1+e^{-u}) - 0.4}
    # ======================================================
    signal = generate_signal_M3(u_grid, a)                         # (M,)
    X_true = signal[np.newaxis, np.newaxis, :] + X_tilde           # (n, p, M)

    # ======================================================
    # Step 5: 加测量噪声
    # ======================================================
    noise = np.random.normal(0, sigma_noise, (n, p, M))
    Y = X_true + noise

    return {
        'Y': Y,
        'X_true': X_true,
        'Sigma_star': Sigma_star,
        'is_h0': h0,
        'signal_indices': signal_indices,
        'params': {
            'n': n, 'p': p, 'M': M,
            'a': a,
            'sigma_noise': sigma_noise,
            'psi_const': psi_const,
            's0': s0 if not h0 else 0,
            'signal_strength': signal_strength if not h0 else 0,
            'model': 'M3_FunctionalMA1_BrownianMotion'
        }
    }


# ============================================================
# 测试与验证
# ============================================================
if __name__ == "__main__":
    print("=" * 64)
    print(" M3 函数型 MA(1) 模型 — 数据生成器测试")
    print("=" * 64)

    params = {
        'n': 200,
        'p': 50,
        'M': 50,
        'sigma_noise': 0.05,
        'seed': 42
    }

    # ---- 测试 1: 零假设 H0 ----
    print("\n[测试 1] H0: S = I_p (跨变量独立)")
    data_h0 = create_dataset_M3(h0=True, **params)
    print(f"  数据形状 Y: {data_h0['Y'].shape}")
    print(f"  Sigma_star 与 I_p 的最大偏差 (应=0): "
          f"{np.max(np.abs(data_h0['Sigma_star'] - np.eye(params['p']))):.6e}")

    # 验证跨变量独立性 (H0)
    X1 = data_h0['X_true'][:, 0, :]
    X2 = data_h0['X_true'][:, 1, :]
    cross_cov = np.mean(X1 * X2, axis=0) - np.mean(X1, axis=0) * np.mean(X2, axis=0)
    print(f"  跨变量协方差最大值 (应≈0): {np.max(np.abs(cross_cov)):.4f}")

    # 验证时间相关性 (M3 特有, 由积分核引入)
    # E[X̃_t · X̃_{t-1}] 不为零, 因为它们共享 X̌_{t-1}
    X_var1 = data_h0['X_true'][:, 0, :]            # (n, M)
    lag1_corr = np.mean(X_var1[1:] * X_var1[:-1], axis=0)
    print(f"  滞后1自协方差最大值 (M3 应≠0): {np.max(np.abs(lag1_corr)):.4f}")

    # ---- 测试 2: 备择假设 H1 ----
    print(f"\n[测试 2] H1: S = I_p + Ω  (s0=4, signal=0.3)")
    data_h1 = create_dataset_M3(h0=False, s0=4, signal_strength=0.3, **params)
    print(f"  注入信号位置 (前4个): {data_h1['signal_indices'][:4]}")
    i0, j0 = data_h1['signal_indices'][0]
    print(f"  Sigma_star[{i0},{j0}] = "
          f"{data_h1['Sigma_star'][i0, j0]:.4f}  (应为 0.3)")

    # ---- 测试 3: 均值函数 ----
    print(f"\n[测试 3] 非零均值 a = 1.0")
    data_a = create_dataset_M3(h0=True, a=1.0, **params)
    u = np.linspace(0, 1, params['M'])
    sample_mean = np.mean(data_a['X_true'][:, 0, :], axis=0)
    theoretical_mean = 1.0 * (1.0 / (1.0 + np.exp(-u)) - 0.4)
    # 由于 X̃ 均值不一定严格为 0 (有积分项), 我们看趋势是否一致
    diff = sample_mean - theoretical_mean
    print(f"  样本均值 - 理论均值: 最大|偏差| ≈ {np.max(np.abs(diff)):.4f} "
          f"(因有限样本噪声, 不等于 0 正常)")

    # ---- 测试 4: 接口兼容性 ----
    print(f"\n[测试 4] 接口兼容性")
    required_keys = {'Y', 'X_true', 'Sigma_star', 'is_h0', 'signal_indices', 'params'}
    actual_keys = set(data_h0.keys())
    print(f"  必需键 == 实际键: "
          f"{'✓' if required_keys == actual_keys else '✗'}")

    # ---- 测试 5: 与统计量计算器联调 ----
    print(f"\n[测试 5] 与 covariance_test 联调")
    try:
        from common.statistic_calculator_517 import covariance_test
        Tn0, c0, p0 = covariance_test(data_h0['Y'], B=200, seed=0)
        Tn1, c1, p1 = covariance_test(
            create_dataset_M3(h0=False, s0=4, signal_strength=0.6, **params)['Y'],
            B=200, seed=0)
        print(f"  H0  → Tn={Tn0:.3f}  crit={c0:.3f}  p={p0:.3f}")
        print(f"  H1  → Tn={Tn1:.3f}  crit={c1:.3f}  p={p1:.3f}")
    except ImportError:
        print("  (跳过, 未找到 statistic_calculator_517)")

    print("\n" + "=" * 64)
    print(" 测试完成")
    print("=" * 64)
