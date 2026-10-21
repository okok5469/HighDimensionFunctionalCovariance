import numpy as np
import time
from tqdm import tqdm

def calculate_u_statistic_matrices(Y):
    """计算样本协方差矩阵（用 BLAS GEMM 加速版）"""
    n, p, M = Y.shape
    Y_centered = Y - np.mean(Y, axis=0, keepdims=True)

    # 等价于 einsum('kis,kjt->ijst', ...)，但走 BLAS，可加速 10~50 倍
    # sigma[i,j,s,t] = sum_k Y_c[k,i,s] * Y_c[k,j,t]
    Y_flat = Y_centered.reshape(n, p * M)              # (n, p*M)
    sigma_2d = (Y_flat.T @ Y_flat) / (n - 1)           # (p*M, p*M)，调用 GEMM
    # 还原为 (p, p, M, M)
    sigma_hat = sigma_2d.reshape(p, M, p, M).transpose(0, 2, 1, 3)
    return sigma_hat


def compute_Tn(sigma_hat, n):
    """
    计算检验统计量 Tn = sqrt(n) * max|sigma_ij| (i != j)
    支持 4D 输入 (p, p, M, M)
    
    修复策略：避免创建巨大的 4D 布尔掩码，改用索引提取法。
    """
    # 确保输入是 numpy 数组
    sigma_hat = np.asarray(sigma_hat)
    
    if sigma_hat.ndim != 4:
        raise ValueError(f"Expected 4D array (p, p, M, M), got {sigma_hat.ndim}D")

    p, p2, M, M2 = sigma_hat.shape
    if p != p2 or M != M2:
        raise ValueError("Input shape must be (p, p, M, M)")

    # 方法：将前两个维度 (p, p) 展平为 (p*p)，保留后两个维度
    # 新形状: (p*p, M, M)
    sigma_flat = sigma_hat.reshape(p * p, M, M)

    # 生成 (p, p) 的对角线掩码 (2D)
    # mask_2d[i, j] = True if i == j
    mask_2d_diag = np.eye(p, dtype=bool)
    
    # 我们想要的是 i != j，所以取反
    # 然后展平这个掩码以匹配 sigma_flat 的第一维
    mask_keep = ~mask_2d_diag.reshape(p * p)

    # 提取所有 i != j 的切片
    # non_diag_slices 的形状将是 (num_non_diag_pairs, M, M)
    non_diag_slices = sigma_flat[mask_keep]

    if non_diag_slices.size == 0:
        return 0.0

    # 在所有剩余元素中找绝对值的最大值
    max_val = np.max(np.abs(non_diag_slices))

    Tn = np.sqrt(n) * max_val
    return Tn

def multiplier_bootstrap(Y, B=300, seed=None):
    """计算临界值 - BLAS 加速版"""
    if seed is not None:
        np.random.seed(seed)

    n, p, M = Y.shape

    # 中心化（不标准化）
    Y_centered = Y - np.mean(Y, axis=0, keepdims=True)

    # 预先做好二维展开和非对角线掩码（循环外只算一次）
    Y_flat = Y_centered.reshape(n, p * M)              # (n, p*M)
    mask_2d_diag = np.eye(p, dtype=bool)
    mask_keep = ~mask_2d_diag.reshape(p * p)           # (p*p,)

    Tn_boots = np.zeros(B)
    sqrt_n = np.sqrt(n)

    for b in range(B):                                  # 去掉内层 tqdm
        xi = np.random.randn(n)
        xi -= xi.mean()

        # A[k, :] = xi[k] * Y_flat[k, :]
        A_flat = Y_flat * xi[:, None]                   # (n, p*M)

        # 等价于 einsum('k,kis,kjt->ijst'，但走 BLAS GEMM
        sigma_2d = (A_flat.T @ Y_flat) / (n - 1)        # (p*M, p*M)
        sigma_hat = sigma_2d.reshape(p, M, p, M).transpose(0, 2, 1, 3)

        # 取非对角块的最大绝对值
        sigma_flat = sigma_hat.reshape(p * p, M, M)
        non_diag = sigma_flat[mask_keep]
        if non_diag.size == 0:
            Tn_boots[b] = 0.0
        else:
            Tn_boots[b] = sqrt_n * np.max(np.abs(non_diag))

    critical_value = np.percentile(Tn_boots, 95)
    return critical_value, Tn_boots

def covariance_test(Y,B=300,seed=None):
    """执行协方差检验"""
    n,p,M = Y.shape
    Tn = compute_Tn(calculate_u_statistic_matrices(Y),n)
    critical_value,Tn_boots = multiplier_bootstrap(Y,B=B,seed=seed)
    p_value = (np.sum(Tn_boots >= Tn)+1) / (B+1)
    return Tn,critical_value,p_value

if __name__ == "__main__":
    print("=== 高维函数型协方差检验测试 ===")
    from simulation.data_generator_one import create_dataset

    # 生成一个小数据集快速测试
    data = create_dataset(n=30, p=20, M=20, q=5,  sigma_noise=0.1, h0=True, seed=42)
    
    import time
    start = time.time()
    Tn, crit, pval = covariance_test(data['Y'], B=200) # B设小点方便测试
    end = time.time()
    
    print(f"Tn: {Tn:.4f}")
    print(f"Critical Value (95%): {crit:.4f}")
    print(f"P-value: {pval:.4f}")

    print("\n=== 测试备择假设 (H1) ===")
    # 生成带信号的数据 (h0=False)
    # 假设您的 create_dataset 支持 s0 和 signal_strength 参数
    data_h1 = create_dataset(
        n=100, p=20, M=20, q=5, sigma_noise=0.1, 
        h0=False, s0=4, signal_strength=0.5, seed=42 # 信号强度设大一点方便观察
    )

    Tn_h1, crit_h1, pval_h1 = covariance_test(data_h1['Y'], B=200)
    print(f"H1 结果 -> Tn: {Tn_h1:.4f}, Critical: {crit_h1:.4f}, P-value: {pval_h1:.4f}")

    if pval_h1 < 0.05:
        print("✅ 成功拒绝 H1 (检验有效，检测到了信号！)")
    else:
        print("⚠️ 未能拒绝 H1 (可能是信号太弱，或样本量太小，或检验功效不足)")
