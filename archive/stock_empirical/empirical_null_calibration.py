from pathlib import Path
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common.paths import STOCK_CACHE_DIR, STOCK_RESULTS_DIR
"""empirical_null_calibration.py

实证 H0 标定：基于真实/合成数据的 H0 重抽样，评估 MB Bootstrap 和 Xue 渐近检验的实际 size。

默认配置：3 组 × 200 次重复，使用 50 进程并行。
"""
import os
import time
import logging
import numpy as np
import pandas as pd
import concurrent.futures as cf
from tqdm import tqdm

from archive.stock_empirical.empirical_data_loader import prepare_empirical_data, fourier_smooth
from common.statistic_calculator_517 import covariance_test
from archive.stock_empirical.xue_test import xue_test

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger('emp_null')

NUM_PROC = 50
B = 500
ALPHA = 0.05
REPS_PER_GROUP = 200
OUT_DIR = str(STOCK_RESULTS_DIR)
CACHE_DIR = str(STOCK_CACHE_DIR)

_GD = {}

def _init_worker(Y_smooth, q):
    _GD['Y_smooth'] = Y_smooth
    _GD['q'] = q


def _run_h0_repeat(args):
    group_name, seed, n, p = args
    Y_base = _GD['Y_smooth'][-n:, :p, :]
    rng = np.random.default_rng(seed)
    Y_h0 = Y_base.copy()
    for j in range(Y_h0.shape[1]):
        perm = rng.permutation(Y_h0.shape[0])
        Y_h0[:, j, :] = Y_h0[perm, j, :]

    _, a_h0, _ = fourier_smooth(Y_h0, q=_GD['q'])
    Tn_mb, crit_mb, pval_mb = covariance_test(Y_h0, B=B, seed=seed)
    xue_r = xue_test(a_h0, alpha=ALPHA)

    return dict(
        group=group_name,
        seed=seed,
        n=n,
        p=p,
        p_over_n=p / n,
        Tn_mb=Tn_mb,
        crit_mb=crit_mb,
        pval_mb=pval_mb,
        reject_mb=pval_mb < ALPHA,
        Tn_xue=xue_r['Tn'],
        crit_xue=xue_r['tau_alpha'],
        pval_xue=xue_r['p_value'],
        reject_xue=xue_r['reject'],
    )


def run_calibration():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)

    log.info('准备实证数据，demarket=True ...')
    data = prepare_empirical_data(n=200, p=200, M=48, q=5,
                                  start='2023-01-01', end='2024-12-31',
                                  demarket=True)
    log.info(f'Loaded empirical data shape: Y_smooth={data["Y_smooth"].shape}')

    groups = [
        {'name': 'p50',  'n': 200, 'p': 50},
        {'name': 'p100', 'n': 200, 'p': 100},
        {'name': 'p150', 'n': 200, 'p': 150},
    ]

    args_list = []
    for grp_idx, grp in enumerate(groups):
        for rep in range(REPS_PER_GROUP):
            seed = grp_idx * REPS_PER_GROUP + rep
            args_list.append((grp['name'], seed, grp['n'], grp['p']))

    log.info(f'开始 H0 标定：{len(args_list)} 次重复，最多 {NUM_PROC} 进程并行。')
    results = []
    with cf.ProcessPoolExecutor(
            max_workers=min(NUM_PROC, len(args_list)),
            initializer=_init_worker,
            initargs=(data['Y_smooth'], data['a'].shape[2])) as executor:
        for r in tqdm(executor.map(_run_h0_repeat, args_list),
                      total=len(args_list), desc='H0 标定'):
            results.append(r)

    df = pd.DataFrame(results)
    path = os.path.join(OUT_DIR, 'empirical_null_calibration.csv')
    df.to_csv(path, index=False)

    summary = df.groupby('group').agg(
        n=('n', 'first'),
        p=('p', 'first'),
        p_over_n=('p_over_n', 'first'),
        size_mb=('reject_mb', 'mean'),
        size_xue=('reject_xue', 'mean'),
        mean_pval_mb=('pval_mb', 'mean'),
        mean_pval_xue=('pval_xue', 'mean'),
    ).reset_index()

    summary_path = os.path.join(OUT_DIR, 'empirical_null_calibration_summary.csv')
    summary.to_csv(summary_path, index=False)

    log.info('H0 标定完成')
    log.info(f'结果保存到: {path}')
    log.info(f'汇总保存到: {summary_path}')
    print(summary.to_string(index=False))


if __name__ == '__main__':
    start = time.time()
    run_calibration()
    log.info(f'总耗时: {time.time() - start:.1f} 秒')
