from pathlib import Path
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common.paths import STOCK_CACHE_DIR, STOCK_RESULTS_DIR
"""
empirical_main.py
  实验1：基础检验 (n=200, p=50, M=48)
  实验2：MB Bootstrap vs Xue 渐近临界值
  实验3：p/n 网格扫描
  并行：ProcessPoolExecutor，共享数据通过 initializer
"""
import os, time, logging
import numpy as np, pandas as pd
import concurrent.futures as cf
from tqdm import tqdm

from common.statistic_calculator_517 import covariance_test
from archive.stock_empirical.xue_test import xue_test
from archive.stock_empirical.empirical_data_loader import prepare_empirical_data

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger('emp')

NUM_PROC = 50
B = 500
ALPHA = 0.05

# ----------- 进程间共享数据 -----------
_GD = {}
def _init_worker(Y_smooth, a):
    _GD['Y'] = Y_smooth; _GD['a'] = a

def _run_pn(args):
    n, p, B = args
    Y = _GD['Y'][-n:, :p, :]
    a = _GD['a'][-n:, :p, :]
    t0 = time.time()
    Tn_mb, crit_mb, pv_mb = covariance_test(Y, B=B, seed=None)
    t_mb = time.time() - t0
    t0 = time.time()
    xr = xue_test(a, alpha=ALPHA)
    t_xue = time.time() - t0
    return dict(n=n, p=p, p_over_n=p/n,
                Tn_mb=Tn_mb, crit_mb=crit_mb, pval_mb=pv_mb, time_mb=t_mb,
                Tn_xue=xr['Tn'], crit_xue=xr['tau_alpha'],
                pval_xue=xr['p_value'], time_xue=t_xue,
                reject_mb=pv_mb < ALPHA, reject_xue=xr['reject'])

# ----------- 实验 -----------
def experiment_basic(data, B=500):
    log.info('=== 实验1+2：基础检验与对比 ===')
    res = _run_pn((data['Y_smooth'].shape[0], data['Y_smooth'].shape[1], B))
    res['M'] = data['Y_smooth'].shape[2]
    res['q'] = data['a'].shape[2]
    return pd.DataFrame([res])

def experiment_pn(data, B=500):
    log.info('=== 实验3：p/n 网格扫描 ===')
    n_max, p_max, _ = data['Y_smooth'].shape
    grid = []
    for n in [50, 100, 150, 200]:
        for p in [10, 20, 30, 50, 80]:
            if p <= p_max and n <= n_max:
                grid.append((n, p))
    # 加入 Bonferroni 边界附近的较大 p
    for p in [100, 150, 200]:
        if p <= p_max:
            grid.append((100, p))
    log.info(f'网格组合数: {len(grid)} | {grid}')
    args_list = [(n, p, B) for (n, p) in grid]

    results = []
    with cf.ProcessPoolExecutor(
            max_workers=min(NUM_PROC, len(args_list)),
            initializer=_init_worker,
            initargs=(data['Y_smooth'], data['a'])) as ex:
        for r in tqdm(ex.map(_run_pn, args_list),
                      total=len(args_list), desc='p/n扫描'):
            results.append(r)
    return pd.DataFrame(results).sort_values(['n','p']).reset_index(drop=True)


def build_synthetic_H0_from_real(data, seed=0):
    """按行/股独立打乱时间索引 → 破坏跨股相关，构造 H0 数据"""
    rng = np.random.default_rng(seed)
    Y = data['Y_smooth'].copy()
    n, p, M = Y.shape
    for j in range(p):
        perm = rng.permutation(n)              # 每只股独立重排日期
        Y[:, j, :] = Y[perm, j, :]
    return Y


def sanity_check(data):
    """聚合到日收益层面，检查应当显著的相关结构。"""
    Y = data['Y_raw']                         # 未标准化，5-min 对数收益
    daily_ret = Y.sum(axis=2)                 # (n_days, p) ≈ 日对数收益
    C = np.corrcoef(daily_ret.T)
    off = C[~np.eye(C.shape[0], dtype=bool)]
    print(f"日收益相关系数: 均值={off.mean():.3f}, 中位={np.median(off):.3f}, "
          f"P75={np.percentile(off,75):.3f}, max={off.max():.3f}")
    print(f"交易日数={Y.shape[0]}, 应≈480(2年)")
    print(f"前5个股票名: {data['names'][:5]}")
    return off.mean()

# ----------- 主流程 -----------
def main():
    log.info('准备实证数据 ...')
    data = prepare_empirical_data(n=200, p=50, M=48, q=5,
              start='2023-01-01', end='2024-12-31', demarket=True)
    log.info(f"Y_smooth: {data['Y_smooth'].shape}  a: {data['a'].shape}")

    mean_corr = sanity_check(data)
    assert mean_corr > 0.15, "❌ 数据管道有问题：HS300 日收益平均相关系数 < 0.15，请检查对齐!"

    os.makedirs(str(STOCK_RESULTS_DIR), exist_ok=True)

    # 实验1+2：用单进程跑（只一个任务）
    _init_worker(data['Y_smooth'], data['a'])    # 给主进程也注入
    df1 = experiment_basic(data, B=B)
    df1.to_csv(f'{STOCK_RESULTS_DIR}/exp1_basic.csv', index=False)
    print('\n', df1.to_string(), '\n')

    # 实验3：并行 p/n 扫描
    df3 = experiment_pn(data, B=B)
    df3.to_csv(f'{STOCK_RESULTS_DIR}/exp3_pn.csv', index=False)
    print('\n', df3.to_string(), '\n')

    # 输出
    from archive.stock_empirical.empirical_outputs import generate_all_outputs
    generate_all_outputs(data, df1, df3)
    log.info('全部完成')

if __name__ == '__main__':
    main()