"""
data_generator_M1.py
====================
M1 模型数据生成器 —— 基于布朗运动 (Brownian Motion)
用于高维函数型数据协方差单样本检验的模拟研究

完整数学模型 (M1):
┌─────────────────────────────────────────────────────────────┐
│  X_{t,j}(u) = a · sin(u²) + X̃_{t,j}(u)                      │
│                                                             │
│  X̃_t(u) = {X̃_{t,1}(u), ..., X̃_{t,p}(u)}^T                   │
│  X̃_t(u) = A · ε_t(u)                                        │
│                                                             │
│  A = S^{1/2},   S = {ρ^|j-k|}_{p×p}  (原文 ρ=0.6)           │
│  ε_t: p 条 i.i.d. 标准布朗运动 on [0, 1]                     │
│                                                             │
│  协方差检验框架:                                             │
│    H0: S = I_p        (各函数变量独立)                       │
│    H1: S = I_p + Ω    (稀疏偏离, 部分变量相关)                │
└─────────────────────────────────────────────────────────────┘

与原傅里叶基模型的关键区别:
  - 傅里叶基模型: 协方差核由有限个基函数决定, 特征值 λ_k = c·k^{-α} (快速衰减)
  - 布朗运动模型: 协方差核 C(s,u) = min(s,u), 特征值 λ_k ∝ 1/k² (较慢衰减, 无限维)
"""
import numpy as np
from scipy.linalg import sqrtm

# ============================================================
# 模块一: 布朗运动路径生成
# ============================================================

def generate_brownian_motions(n,p,M):
    """
    生成 n 个样本, 每个样本包含 p 条独立标准布朗运动。
    
    ┌──────────────────────────────────────────────────────┐
    │ 对应公式:                                             │
    │   ε_t(u) = {ε_{t,1}(u), ..., ε_{t,p}(u)}^T           │
    │                                                      │
    │ 每条 ε_{t,j}(·) 是标准布朗运动 (Wiener 过程):          │
    │   (i)   ε_{t,j}(0) = 0                               │
    │   (ii)  E[ε_{t,j}(u)] = 0                            │
    │   (iii) Cov(ε_{t,j}(s), ε_{t,j}(u)) = min(s, u)      │
    │   (iv)  增量独立:                                     │
    │         ε(u_{m+1}) - ε(u_m) ~ N(0, Δu), 各增量独立    │
    └──────────────────────────────────────────────────────┘
    
    数值实现原理:
        将 [0,1] 均匀分为 M 个点: u_0=0, u_1, ..., u_{M-1}=1
        步长 Δu = 1/(M-1)
        
        增量: ΔB_m = B(u_m) - B(u_{m-1}) ~ N(0, Δu)
        路径: B(u_m) = Σ_{k=1}^{m} ΔB_k    (累积求和)
        
        验证: Var[B(u_m)] = m·Δu = m/(M-1) = u_m  ✓
    
    参数:
        n (int): 样本量 (对应 t = 1, ..., n)
        p (int): 变量维度 (对应 j = 1, ..., p, 即原文中的 r)
        M (int): [0,1] 上的离散网格点数
    
    返回:
        BM (ndarray): 形状 (n, p, M), 布朗运动路径
        u_grid (ndarray): 形状 (M,), 网格点
    """
    # 构造等间距网格: u_0 = 0, u_1, ..., u_{M-1} = 1
    u_grid = np.linspace(0,1,M)
    du = u_grid[1] - u_grid[0]  # 步长 Δu=1/(M-1)

    # ---- 生成独立增量 ΔB_{t,j,m} ~ N(0, Δu) ----
    # 标准差 = √(Δu)
    increments = np.random.normal(loc=0.0,scale=np.sqrt(du),size=(n,p,M))

    # ---- 边界条件: B(0) = 0 ----
    # 将第0个增量设为0, 确保 B(u_0) = 0
    increments[:,:,0] = 0.0

    # ---- 累积求和: B(u_m) = Σ_{k=0}^{m} ΔB_k ----
    BM = np.cumsum(increments,axis=2)  #(n, p, M),在时间轴上累计

    return BM,u_grid


# ============================================================
# 模块二: 均值函数 (信号部分)
# ============================================================
def generate_signal_M1(u_grid, a=0.0):
    """
    生成 M1 模型的均值函数。
    
    ┌──────────────────────────────────────────────────────┐
    │ 对应公式:  μ(u) = a · sin(u²)                        │
    │                                                      │
    │ - a = 0: 零均值 (标准协方差检验设置)                   │
    │ - a ≠ 0: 非零均值 (检验方法对均值偏移的鲁棒性)         │
    │                                                      │
    │ 注: 协方差检验通常先中心化, 故 a 的值不影响检验水平;    │
    │     但可测试中心化步骤的数值稳定性。                    │
    └──────────────────────────────────────────────────────┘
    
    参数:
        u_grid (ndarray): 网格点, 形状 (M,)
        a (float): 信号强度, 默认 0
    
    返回:
        signal (ndarray): 形状 (M,)
    """
    return a*np.sin(u_grid**2)


# ============================================================
# 模块三: 截面协方差矩阵生成
# ============================================================

def generate_sparse_covariance(p,s0,signal_strength):
    """
    生成备择假设下的稀疏协方差扰动矩阵。
    
    ┌──────────────────────────────────────────────────────┐
    │ 对应公式 (检验框架):                                  │
    │   H0: S = I_p                                        │
    │   H1: S = I_p + Ω                                    │
    │                                                      │
    │ 其中 Ω 是稀疏矩阵:                                   │
    │   - 共 s0 个非零元素 (s0/2 对, 因为对称)              │
    │   - 每个非零元素的值 = signal_strength                │
    │   - 位置随机选取                                      │
    └──────────────────────────────────────────────────────┘
    
    与原 data_generator.py 中 generate_sparse_covariance 完全一致,
    复制于此以保证文件独立可运行。
    """
    Sigma_star = np.eye(p)

    if s0%2 != 0:
        raise ValueError("s0 必须为偶数，以保证对称性。")
    
    num_pairs= s0 // 2
    all_indices = [(i,j) for i in range(p) for j in range(i+1,p)]
    selected_pairs = np.random.choice(len(all_indices),num_pairs,replace=False)
    
    non_zero_indices = []
    for idx in selected_pairs:
        i,j = all_indices[idx]
        Sigma_star[i,j] = signal_strength
        Sigma_star[j,i] = signal_strength
        non_zero_indices.append((i,j))
        non_zero_indices.append((j,i))

    return Sigma_star,non_zero_indices


# ============================================================
# 模块四: 主数据生成接口
# ============================================================

def create_dataset_M1(n,p,M,a=0.0,sigma_noise=0.05,h0=True,s0=4,signal_strength=0.3,seed=None):
    """
    M1 模型 (布朗运动) 数据生成主接口。
    
    输出格式与原 create_dataset() 完全一致, 可直接对接后续检验代码。
    
    ┌──────────────────────────────────────────────────────────────┐
    │ 完整生成流程:                                                 │
    │                                                              │
    │ Step 1:  ε_t(u) ← p条独立标准布朗运动, t=1,...,n               │
    │                                                              │
    │ Step 2:  构造 S (截面协方差矩阵)                               │
    │            H0: S = I_p                                       │
    │            H1: S = I_p + Ω (稀疏)                            │
    │                                                              │
    │ Step 3:  A = S^{1/2}, 计算 X̃_t(u) = A · ε_t(u)               │
    │                                                              │
    │ Step 4:  X_{t,j}(u) = a·sin(u²) + X̃_{t,j}(u)                 │
    │                                                              │
    │ Step 5:  Y_{t,j}(u_m) = X_{t,j}(u_m) + noise                 │
    └──────────────────────────────────────────────────────────────┘
    
    参数:
        n (int): 样本量
        p (int): 变量维度 (对应 M1 公式中的 r)
        M (int): 观测点数 (网格大小)
        a (float): 均值函数强度, 默认 0 (纯协方差检验)
        sigma_noise (float): 测量噪声标准差
        h0 (bool): True 为零假设, False 为备择假设
        s0 (int): H1 下非零元素个数 (必须是偶数)
        signal_strength (float): H1 下信号强度
        seed (int): 随机种子
    
    返回:
        dict: 与原 create_dataset 相同的字典结构
    """
    if seed is not None:
        np.random.seed(seed)

     # ======================================================
    # Step 1: 生成独立标准布朗运动 ε_t(u)
    # ======================================================
    # 公式: ε_t(u) = {ε_{t,1}(u), ..., ε_{t,p}(u)}^T
    # 其中各 ε_{t,j} 相互独立, 每条是标准布朗运动
    # Cov(ε_{t,j}(s), ε_{t,j}(u)) = min(s, u)
    #
    # BM 形状: (n, p, M)
    #   n → 第 t 个样本
    #   p → 第 j 个变量
    #   M → 第 m 个网格点 u_m
    BM,u_grid = generate_brownian_motions(n,p,M)


    # ======================================================
    # Step 2 & 3: 构造截面协方差 S 并引入相关性
    # ======================================================
    if h0:
        # ---- H0: S = I_p ----
        # A = S^{1/2} = I_p
        # X̃_t(u) = I_p · ε_t(u) = ε_t(u)
        # 即各变量的布朗运动保持独立
        Sigma_star = np.eye(p)
        signal_indices = None
        X_tilde = BM    # (n, p, M), 直接就是独立布朗运动

    else:
        # ---- H1: S = I_p + Ω ----
        Sigma_star,signal_indices = generate_sparse_covariance(p,s0,signal_strength)

        # 计算矩阵平方根: A = S^{1/2}
        # 使得 A · A^T = S (即 A @ A.T = Sigma_star)
        A = sqrtm(Sigma_star)
        A_real = np.real(A)  # 去除数值误差可能产生的虚部
        
        # ---- 引入截面相关性 ----
        # 公式: X̃_t(u_m) = A · ε_t(u_m)
        #
        # 逐元素理解:
        #   X̃_{t,j}(u_m) = Σ_{k=1}^{p} A_{jk} · ε_{t,k}(u_m)
        #
        # 对于固定 t 和 m:
        #   X̃_t(u_m) ∈ R^p = A_{p×p} · ε_t(u_m) ∈ R^p
        #
        # 结果的协方差:
        #   Cov(X̃_j(s), X̃_k(u)) = [A·A^T]_{jk} · min(s,u)
        #                         = S_{jk} · min(s,u)
        #   H1下某些 j≠k 的 S_{jk} ≠ 0, 因此跨变量有相关性 ✓
        #
        # Einstein 求和实现:
        #   X_tilde[n,j,m] = Σ_k  A[j,k] · BM[n,k,m]
        #       indices:       n j m     j k     n k m
        X_tilde = np.einsum('jk,nkm -> njm',A_real,BM)  # (n, p, M)

    # ======================================================
    # Step 4: 叠加均值函数
    # ======================================================
    # 公式: X_{t,j}(u) = a · sin(u²) + X̃_{t,j}(u)
    #
    # signal 形状 (M,), 通过广播加到每个 (t, j) 上:
    #   (1, 1, M) + (n, p, M) → (n, p, M)
    
    signal = generate_signal_M1(u_grid,a)  # (M,)
    X_true = signal[np.newaxis,np.newaxis,:] + X_tilde # (n, p, M)

    # ======================================================
    # Step 5: 添加独立测量噪声
    # ======================================================
    # 公式: Y_{t,j}(u_m) = X_{t,j}(u_m) + e_{t,j,m}
    # 其中 e_{t,j,m} ~ i.i.d. N(0, σ²_noise)
    noise = np.random.normal(0,sigma_noise,(n, p, M)) 
    Y = X_true + noise

    # ======================================================
    # 返回结果 (与原 create_dataset 接口一致)
    # ======================================================
    return {
        'Y': Y,                     # 观测数据        (n, p, M)
        'X_true': X_true,           # 真实函数数据    (n, p, M)
        'Sigma_star': Sigma_star,   # 截面协方差矩阵  (p, p)
        'is_h0': h0,
        'signal_indices': signal_indices,
        'params': {
            'n': n, 'p': p, 'M': M,
            'a': a,
            'sigma_noise': sigma_noise,
            's0': s0 if not h0 else 0,
            'signal_strength': signal_strength if not h0 else 0,
            'model': 'M1_Brownian_Motion'
        }
    }   


# ============================================================
# 测试与验证
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print(" M1 布朗运动模型 — 数据生成器测试")
    print("=" * 60)
    
    params = {
        'n': 200,
        'p': 100,
        'M': 50,
       # 'a': 0.0,             # 协方差检验, 零均值
        'sigma_noise': 0.05,
        'seed': 42
    }
    
    # ---- 测试 1: 零假设 H0 ----
    print("\n[测试 1] H0: S = I_p (各变量独立)")
    data_h0 = create_dataset_M1(h0=True, **params)
    print(f"  数据形状 Y: {data_h0['Y'].shape}")
    print(f"  Sigma_star 非对角线最大值 (应=0): "
          f"{np.max(np.abs(data_h0['Sigma_star'] - np.eye(params['p']))):.6f}")
    
    # 验证布朗运动协方差: Cov(B(s), B(t)) ≈ min(s, t)
    # 取第1个变量, 计算样本协方差
    X_var1 = data_h0['X_true'][:, 0, :]  # (n, M)
    sample_cov = np.cov(X_var1.T)        # (M, M)
    u = np.linspace(0, 1, params['M'])
    theoretical_cov = np.minimum(u[:, None], u[None, :])  # min(s, u)
    cov_error = np.mean((sample_cov - theoretical_cov) ** 2)
    print(f"  布朗运动协方差 MSE (样本 vs min(s,u)): {cov_error:.6f}")
    
    # 验证跨变量独立性: Cov(X_1(u), X_2(u)) ≈ 0
    X_var2 = data_h0['X_true'][:, 1, :]
    cross_cov = np.mean(X_var1 * X_var2, axis=0) - np.mean(X_var1, axis=0) * np.mean(X_var2, axis=0)
    print(f"  跨变量协方差最大值 (应≈0): {np.max(np.abs(cross_cov)):.6f}")
    
    # ---- 测试 2: 备择假设 H1 ----
    print(f"\n[测试 2] H1: S = I_p + Ω (s0=4, signal=0.3)")
    data_h1 = create_dataset_M1(h0=False, s0=4, signal_strength=0.3, **params)
    print(f"  注入信号位置: {data_h1['signal_indices'][:4]}...")
    i0, j0 = data_h1['signal_indices'][0]
    print(f"  验证 Sigma_star[{i0},{j0}] = "
          f"{data_h1['Sigma_star'][i0, j0]:.4f} (应为 0.3)")
    
    # ---- 测试 3: 带均值偏移 ----
    print(f"\n[测试 3] 非零均值 a=1.0")
    data_a = create_dataset_M1(h0=True, a=1.0, **params)
    u = np.linspace(0, 1, params['M'])
    sample_mean = np.mean(data_a['X_true'][:, 0, :], axis=0)  # (M,)
    theoretical_mean = 1.0 * np.sin(u ** 2)
    mean_error = np.max(np.abs(sample_mean - theoretical_mean))
    print(f"  均值函数最大误差: {mean_error:.4f}")
    
    # ---- 测试 4: 与原傅里叶模型接口对比 ----
    print(f"\n[测试 4] 接口兼容性检查")
    required_keys = {'Y', 'X_true', 'Sigma_star', 'is_h0', 'signal_indices', 'params'}
    actual_keys = set(data_h0.keys())
    print(f"  必需键: {required_keys}")
    print(f"  实际键: {actual_keys}")
    print(f"  匹配: {'✓ 完全一致' if required_keys == actual_keys else '✗ 不匹配!'}")
    
    print("\n" + "=" * 60)
    print(" 测试完成")
    print("=" * 60)
