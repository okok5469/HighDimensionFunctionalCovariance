import numpy as np
from scipy.linalg import sqrtm

def generate_fourier_basis(M, q):
    """傅里叶基函数矩阵 (M, q)：第0列常数，其余 sin/cos 交替"""
    t = np.linspace(0, 1, M)
    basis = np.empty((M, q))
    basis[:, 0] = 1.0
    for idx in range(1, q):
        k = (idx + 1) // 2          # 1,1,2,2,3,3,...
        if idx % 2 == 1:
            basis[:, idx] = np.sqrt(2) * np.sin(2 * np.pi * k * t)
        else:
            basis[:, idx] = np.sqrt(2) * np.cos(2 * np.pi * k * t)
    return basis

def generate_coefficients(n, p, q, decay_rate=1.0, decay_power=2):
    """
    生成功能系数矩阵 A，并实现文档指定的多项式特征值衰减。
    
    数学原理 (基于MD文档):
        特征值 lambda_r = c * r^(-alpha)
        这里设定 r 从 1 开始计数 (对应代码索引 k+1)
        系数 a_ijk ~ N(0, lambda_k)
        
    参数:
        n (int): 样本量。
        p (int): 变量维度。
        q (int): 基函数数量。
        decay_rate (float): 衰减系数 c (文档中的 c，通常设为 1 或 2)。
        decay_power (float): 衰减指数 alpha (文档中为 2)。
    
    返回:
        a (ndarray): 形状为 (n, p, q) 的系数张量。
    """
    # 生成标准正态随机数 Z ~ N(0, 1)
    z = np.random.normal(0, 1, (n, p, q))
    
    # 计算每个基函数对应的特征值 (方差) lambda_k
    # 注意：文档公式中 r 通常从 1 开始，代码索引 k 从 0 开始，所以用 (k+1)
    r = np.arange(1, q + 1, dtype=float)
    lambdas = decay_rate * r ** (-decay_power)
    
    # 应用标准差缩放 (因为 Var(X) = sigma^2, 所以 X = Z * sigma)
    # sigma = sqrt(lambda)
    scales = np.sqrt(lambdas)
    
    # 利用广播机制直接缩放
    # z shape: (n, p, q), scales shape: (q,) -> 自动广播到 (n, p, q)
    a = z * scales
        
    return a

def generate_function_data(a, basis):
    """
    将系数和基函数组合成最终的函数型数据 X。
    """
    n, p, q = a.shape
    M = basis.shape[0]
    
    # 优化矩阵乘法: X[n, p, M] = a[n, p, q] @ basis[M, q].T
    # 重塑 a 为 (n*p, q)
    a_reshaped = a.reshape(-1, q)
    # 计算 (n*p, M)
    X_reshaped = a_reshaped @ basis.T
    # 还原形状
    X = X_reshaped.reshape(n, p, M)
    
    return X

def generate_sparse_covariance(p, s0, signal_strength):
    """
    生成备择假设下的稀疏协方差扰动矩阵 Omega。
    H1: Sigma = I_p + Omega
    """
    Sigma_star = np.eye(p)
    
    if s0 % 2 != 0:
        raise ValueError("s0 必须是偶数，因为协方差矩阵是对称的。")
    
    num_pairs = s0 // 2
    # 获取所有可能的上三角索引
    all_indices = [(i, j) for i in range(p) for j in range(i+1, p)]
    
    # 随机抽取不重复的位置对
    selected_pairs = np.random.choice(len(all_indices), num_pairs, replace=False)
    
    non_zero_indices = []
    
    for idx in selected_pairs:
        i, j = all_indices[idx]
        # 注入信号
        Sigma_star[i, j] = signal_strength
        Sigma_star[j, i] = signal_strength
        non_zero_indices.append((i, j))
        non_zero_indices.append((j, i))
        
    return Sigma_star, non_zero_indices

def create_dataset(n, p, M, q, decay_rate=1.0, decay_power=2, sigma_noise=0.05, 
                   h0=True, s0=4, signal_strength=0.3, seed=None):
    """
    主数据生成接口 (已根据MD文档更新参数)。
    
    参数:
        n (int): 样本量。
        p (int): 变量维度。
        M (int): 观测点数。
        q (int): 基函数截断阶数。
        decay_rate (float): 特征值衰减系数 c (默认 1.0)。
        decay_power (float): 特征值衰减指数 (默认 2.0，即 r^-2)。
        sigma_noise (float): 测量噪声标准差。
        h0 (bool): True为零假设，False为备择假设。
        s0 (int): 备择假设下的非零元素个数。
        signal_strength (float): 备择假设下的信号强度。
        seed (int): 随机种子。
    """
    if seed is not None:
        np.random.seed(seed)
    
    # 1. 生成基函数
    basis = generate_fourier_basis(M, q)
    
    # 2. 生成系数 (包含新的衰减逻辑)
    # 此时生成的系数在变量间是独立的 (对应 Sigma=I 的潜在过程)
    a_independent = generate_coefficients(n, p, q, decay_rate, decay_power)
    
    # 3. 构造协方差结构
    if h0:
        Sigma_star = np.eye(p)
        signal_indices = None
        a_correlated = a_independent
    else:
        # H1: 构造稀疏协方差矩阵
        Sigma_star, signal_indices = generate_sparse_covariance(p, s0, signal_strength)
        
        # 对系数进行线性变换以引入相关性
        # a_corr = a_ind @ L.T, 其中 L @ L.T = Sigma_star
        L = sqrtm(Sigma_star)
        L_real = np.real(L) # 确保是实数矩阵
        
        a_correlated = np.zeros_like(a_independent)
        for k in range(q):
            coeff_slice = a_independent[:, :, k] # (n, p)
            # 变换: (n, p) @ (p, p)
            a_correlated[:, :, k] = coeff_slice @ L_real.T
            
    # 4. 生成真实函数数据 X
    X_true = generate_function_data(a_correlated, basis)
    
    # 5. 添加独立测量噪声
    noise = np.random.normal(0, sigma_noise, (n, p, M))
    Y = X_true + noise
    
    return {
        'Y': Y,
        'X_true': X_true,
        'Sigma_star': Sigma_star,
        'is_h0': h0,
        'signal_indices': signal_indices,
        'params': {
            'n': n, 'p': p, 'M': M, 'q': q, 
            'decay_rate': decay_rate, 'decay_power': decay_power,
            'sigma_noise': sigma_noise,
            's0': s0 if not h0 else 0,
            'signal_strength': signal_strength if not h0 else 0
        }
    }

# ==========================================
# 测试与演示部分
# ==========================================
if __name__ == "__main__":
    print("=== 高维函数型协方差数据生成器测试 (基于MD文档方案) ===")
    
    # 设置参数 (参考MD文档建议)
    params = {
        'n': 100,
        'p': 100,      
        'M': 50,
        'q': 5,
        'decay_rate': 1.0,  # 对应文档中的 c
        'decay_power': 2.0, # 对应文档中的 r^-2
        'sigma_noise': 0.05,
        'seed': 42
    }
    
    # --- 测试 1: 零假设 (H0) ---
    print("\n[测试 1] 生成零假设数据 (H0)...")
    data_h0 = create_dataset(h0=True, **params)
    print(f"   - 数据形状 Y: {data_h0['Y'].shape}")
    print(f"   - 协方差矩阵检查 (非对角线最大值应接近0): {np.max(np.abs(data_h0['Sigma_star'] - np.eye(params['p'])))}")
    
    # --- 测试 2: 备择假设 (H1) ---
    print("\n[测试 2] 生成备择假设数据 (H1)...")
    data_h1 = create_dataset(h0=False, s0=4, signal_strength=0.3, **params)
    print(f"   - 注入的非零信号位置: {data_h1['signal_indices'][:4]}...")
    val = data_h1['Sigma_star'][data_h1['signal_indices'][0][0], data_h1['signal_indices'][0][1]]
    print(f"   - 验证信号强度: {val:.4f} (应为 0.3)")
    
    # --- 测试 3: 特征值衰减验证 (核心修改点) ---
    print("\n[测试 3] 验证特征值衰减 (Lambda Decay = c * r^-2)...")
    c = params['decay_rate']
    print(f"   - 理论计算 (c={c}):")
    for k in range(params['q']):
        r = k + 1
        theoretical_lambda = c * (r ** (-params['decay_power']))
        print(f"     r={r}: Lambda = {theoretical_lambda:.4f}")
    
    print("\n=== 测试完成 ===")