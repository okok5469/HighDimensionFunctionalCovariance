from pathlib import Path
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Main_HAR_empirical.py
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import time
import logging
import multiprocessing
import concurrent.futures

os.environ['MPLBACKEND'] = 'Agg'
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

from empirical.har_data_loader import load_har_static, build_windows
from common.statistic_calculator_517 import covariance_test
from common.statistic_calculator_xue import (
    compute_Tn_xue, xue_critical_value, xue_pvalue, gumbel_pdf
)
from common.xue_helper import project_to_fourier_basis

from common.paths import HAR_DATA_DIR, HAR_RESULTS_DIR

RESULTS_DIR = HAR_RESULTS_DIR / 'experiment_results'
FIGURES_DIR = HAR_RESULTS_DIR / 'figures'

# ====== 配置 ======
CSV_PATH_H0     = HAR_DATA_DIR / 'har_static_subject.csv'   # H0: 静态（无协方差结构变化）
CSV_PATH_H1     = HAR_DATA_DIR / 'har_dynamic_long.csv'     # H1: 动态（存在协方差结构变化）
M              = 48          # 窗口长度
Q_SMOOTH       = 5           # 傅里叶平滑基数
STRIDE         = 2           # 滑窗步长（动态调整以达到 n_pool 足够）
B              = 500         # bootstrap 重数
N_REPEATS      = 100         # 子抽样重复次数
ALPHA          = 0.05
USE_PARALLEL   = True
NUM_PROCESSES  = min(8, multiprocessing.cpu_count())

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('har_empirical')


# ====== 单次子抽样：同时计算两种检验 ======
def one_subsample_test(Y_pool, n, p_indices, B, seed, alpha=0.05):
    rng = np.random.default_rng(seed)
    N_pool = Y_pool.shape[0]
    replace = N_pool < n
    idx = rng.choice(N_pool, size=n, replace=replace)
    Y_sub = Y_pool[idx][:, list(p_indices), :]            # (n, p, M)

    # 我们方法（bootstrap）
    Tn_b, crit_b, pval_b = covariance_test(Y_sub, B=B, seed=seed)

    # Xue 渐近（s = q_smooth，即基展开截断项数，而非窗口长度 M）
    Y_sub_xue = project_to_fourier_basis(Y_sub, Q_SMOOTH)
    Tn_x = compute_Tn_xue(Y_sub_xue, s=Q_SMOOTH)
    crit_x = xue_critical_value(alpha)
    pval_x = xue_pvalue(Tn_x)

    return {
        'Tn_boot': Tn_b, 'crit_boot': crit_b, 'pval_boot': pval_b,
        'Tn_xue':  Tn_x, 'crit_xue': crit_x, 'pval_xue':  pval_x,
        'reject_boot': int(pval_b < alpha),
        'reject_xue':  int(Tn_x  > crit_x),
    }


def repeat_subsample(Y_pool, n, p_indices, n_repeats, B, base_seed, alpha=0.05):
    """串行版重复（在并行 worker 内调用）"""
    records = []
    for r in range(n_repeats):
        seed_r = base_seed + r * 1009
        rec = one_subsample_test(Y_pool, n, p_indices, B, seed_r, alpha)
        records.append(rec)
    df = pd.DataFrame(records)
    summary = {
        'boot_reject_rate': df['reject_boot'].mean(),
        'xue_reject_rate':  df['reject_xue'].mean(),
        'Tn_boot_mean':     df['Tn_boot'].mean(),
        'Tn_xue_mean':      df['Tn_xue'].mean(),
        'pval_boot_mean':   df['pval_boot'].mean(),
        'pval_xue_mean':    df['pval_xue'].mean(),
        'crit_boot_mean':   df['crit_boot'].mean(),
        'crit_xue':         df['crit_xue'].iloc[0],
        'Tn_boot_list':     df['Tn_boot'].tolist(),
        'Tn_xue_list':      df['Tn_xue'].tolist(),
    }
    return summary


def task_executor(task):
    res = repeat_subsample(
        Y_pool=task['Y_pool'], n=task['n'], p_indices=task['p_indices'],
        n_repeats=task['n_repeats'], B=task['B'],
        base_seed=task['seed'], alpha=task['alpha']
    )
    res['n'] = task['n']
    res['p'] = len(task['p_indices'])
    return res


# ====== 主流程 ======
def main():
    t0 = time.time()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    # 1) 数据加载与预处理
    logger.info("===== HAR 实证分析 启动 =====")
    df = load_har_static(CSV_PATH_H0)
    logger.info(f"原始数据 shape={df.shape}, "
                f"subjects={sorted(df['subject'].unique())}")

    Y_pool = build_windows(df, M=M, stride=STRIDE, q_smooth=Q_SMOOTH,
                           apply_log_return=True, do_smooth=True, do_std=True)
    N_pool, p_max, _ = Y_pool.shape
    logger.info(f"窗口池 shape={Y_pool.shape}")

    np.save(RESULTS_DIR / 'Y_pool.npy', Y_pool)

    # --- H1 数据加载（动态数据）---
    logger.info("\n--- 加载 H1 数据（动态） ---")
    df_h1 = load_har_static(CSV_PATH_H1)
    if 'subject' not in df_h1.columns and 'sample_id' in df_h1.columns:
        df_h1 = df_h1.rename(columns={'sample_id': 'subject'})
    logger.info(f"H1 原始数据 shape={df_h1.shape}, "
                f"subjects={df_h1['subject'].nunique()}")

    Y_pool_h1 = build_windows(df_h1, M=M, stride=STRIDE, q_smooth=Q_SMOOTH,
                               apply_log_return=True, do_smooth=True, do_std=True)
    N_pool_h1, p_max_h1, _ = Y_pool_h1.shape
    logger.info(f"H1 窗口池 shape={Y_pool_h1.shape}")
    np.save(RESULTS_DIR / 'Y_pool_h1.npy', Y_pool_h1)

    # 2) 实验 1：在全数据 (n=min(200, N_pool), p=p_max) 上的基础检验
    logger.info("\n--- 实验 1: 基础检验（单次实证）---")
    n_full = min(200, N_pool)
    rng = np.random.default_rng(42)
    idx = rng.choice(N_pool, size=n_full, replace=(N_pool < n_full))
    Y_full = Y_pool[idx]

    Tn_b, crit_b, pval_b = covariance_test(Y_full, B=B, seed=42)
    Y_full_xue = project_to_fourier_basis(Y_full, Q_SMOOTH)
    Tn_x = compute_Tn_xue(Y_full_xue, s=Q_SMOOTH)
    crit_x = xue_critical_value(ALPHA)
    pval_x = xue_pvalue(Tn_x)

    exp1 = {
        'n': n_full, 'p': p_max, 'M': M, 'B': B,
        'Tn_boot': Tn_b, 'crit_boot': crit_b, 'pval_boot': pval_b,
        'reject_boot': int(pval_b < ALPHA),
        'Tn_xue': Tn_x, 'crit_xue': crit_x, 'pval_xue': pval_x,
        'reject_xue': int(Tn_x > crit_x),
    }
    pd.DataFrame([exp1]).to_csv(RESULTS_DIR / 'har_exp1_basic.csv',
                                index=False)
    logger.info(f"Exp1 → {exp1}")

    # 3) 实验 2：子抽样 100 次重复，比较两方法的拒绝率
    logger.info("\n--- 实验 2: 子抽样重复 (n_repeats=%d) ---" % N_REPEATS)
    rep = repeat_subsample(Y_pool, n=n_full, p_indices=tuple(range(p_max)),
                           n_repeats=N_REPEATS, B=B, base_seed=2025,
                           alpha=ALPHA)
    exp2 = {k: rep[k] for k in
            ['boot_reject_rate', 'xue_reject_rate',
             'Tn_boot_mean', 'Tn_xue_mean',
             'pval_boot_mean', 'pval_xue_mean',
             'crit_boot_mean', 'crit_xue']}
    exp2.update({'n': n_full, 'p': p_max, 'M': M,
                 'B': B, 'n_repeats': N_REPEATS})
    pd.DataFrame([exp2]).to_csv(
        RESULTS_DIR / 'har_exp2_replications.csv', index=False)
    logger.info(f"Exp2 → boot_reject={exp2['boot_reject_rate']:.4f}, "
                f"xue_reject={exp2['xue_reject_rate']:.4f}")

    np.save(RESULTS_DIR / 'Tn_boot_list.npy',
            np.array(rep['Tn_boot_list']))
    np.save(RESULTS_DIR / 'Tn_xue_list.npy',
            np.array(rep['Tn_xue_list']))

    # 4) 实验 3：p/n 网格扫描
    logger.info("\n--- 实验 3: p/n 网格扫描 ---")
    if N_pool >= 50:
        n_grid = [50, 100, 150, 200]
    else:
        n_grid = sorted(set([max(3, int(round(N_pool * frac)))
                             for frac in [0.2, 0.4, 0.6, 0.8, 1.0]]))
    p_grid = [3, 4, 5, 6]
    n_grid = [n for n in n_grid if n <= int(N_pool * 1.5)]      # 安全裁剪
    p_grid = [p for p in p_grid if p <= p_max]

    if not n_grid:
        n_grid = [max(3, N_pool)]

    tasks = []
    for n_v in n_grid:
        for p_v in p_grid:
            tasks.append({
                'Y_pool': Y_pool, 'n': n_v,
                'p_indices': tuple(range(p_v)),
                'n_repeats': max(30, N_REPEATS // 2),
                'B': B, 'alpha': ALPHA,
                'seed': 1000 + n_v * 10 + p_v
            })

    grid_results = []
    if tasks:
        if USE_PARALLEL:
            with concurrent.futures.ProcessPoolExecutor(
                    max_workers=NUM_PROCESSES) as ex:
                futs = [ex.submit(task_executor, t) for t in tasks]
                for f in tqdm(concurrent.futures.as_completed(futs),
                              total=len(futs), desc="p/n grid"):
                    grid_results.append(f.result())
        else:
            for t in tqdm(tasks, desc="p/n grid"):
                grid_results.append(task_executor(t))

    if grid_results:
        grid_df = pd.DataFrame([{
            'n': r['n'], 'p': r['p'], 'p_over_n': r['p'] / r['n'],
            'boot_reject_rate': r['boot_reject_rate'],
            'xue_reject_rate':  r['xue_reject_rate'],
            'Tn_boot_mean':     r['Tn_boot_mean'],
            'Tn_xue_mean':      r['Tn_xue_mean'],
            'pval_boot_mean':   r['pval_boot_mean'],
            'pval_xue_mean':    r['pval_xue_mean'],
        } for r in grid_results]).sort_values(['n', 'p']).reset_index(drop=True)
        grid_df.to_csv(RESULTS_DIR / 'har_exp3_pn_grid.csv', index=False)
        logger.info(f"\n{grid_df}")
    else:
        grid_df = pd.DataFrame(columns=['n', 'p', 'p_over_n', 'boot_reject_rate',
                                        'xue_reject_rate', 'Tn_boot_mean',
                                        'Tn_xue_mean', 'pval_boot_mean',
                                        'pval_xue_mean'])
        grid_df.to_csv(RESULTS_DIR / 'har_exp3_pn_grid.csv', index=False)
        logger.warning("实验3: p/n 网格任务为空，已跳过 p/n 扫描。")

    # ===================================================================
    #  H1 实验（动态数据：存在协方差结构变化）
    # ===================================================================
    logger.info("\n===== H1 实验（动态数据）=====")

    # 5) 实验 4：H1 基础检验（单次实证，与 Exp1 对应）
    logger.info("\n--- 实验 4: H1 基础检验 ---")
    n_full_h1 = min(200, N_pool_h1)
    rng_h1 = np.random.default_rng(42)
    idx_h1 = rng_h1.choice(
        N_pool_h1, size=n_full_h1, replace=(N_pool_h1 < n_full_h1)
    )
    Y_full_h1 = Y_pool_h1[idx_h1]

    Tn_b_h1, crit_b_h1, pval_b_h1 = covariance_test(Y_full_h1, B=B, seed=42)
    Y_full_h1_xue = project_to_fourier_basis(Y_full_h1, Q_SMOOTH)
    Tn_x_h1 = compute_Tn_xue(Y_full_h1_xue, s=Q_SMOOTH)
    crit_x_h1 = xue_critical_value(ALPHA)
    pval_x_h1 = xue_pvalue(Tn_x_h1)

    exp4 = {
        'n': n_full_h1, 'p': p_max_h1, 'M': M, 'B': B,
        'Tn_boot': Tn_b_h1, 'crit_boot': crit_b_h1, 'pval_boot': pval_b_h1,
        'reject_boot': int(pval_b_h1 < ALPHA),
        'Tn_xue': Tn_x_h1, 'crit_xue': crit_x_h1, 'pval_xue': pval_x_h1,
        'reject_xue': int(Tn_x_h1 > crit_x_h1),
    }
    pd.DataFrame([exp4]).to_csv(RESULTS_DIR / 'har_exp4_h1_basic.csv',
                                index=False)
    logger.info(f"Exp4 (H1) -> {exp4}")

    # 6) 实验 5：H1 子抽样 100 次重复（与 Exp2 对应）
    logger.info("\n--- 实验 5: H1 子抽样重复 (n_repeats=%d) ---" % N_REPEATS)
    rep_h1 = repeat_subsample(Y_pool_h1, n=n_full_h1,
                              p_indices=tuple(range(p_max_h1)),
                              n_repeats=N_REPEATS, B=B, base_seed=2025,
                              alpha=ALPHA)
    exp5 = {k: rep_h1[k] for k in
            ['boot_reject_rate', 'xue_reject_rate',
             'Tn_boot_mean', 'Tn_xue_mean',
             'pval_boot_mean', 'pval_xue_mean',
             'crit_boot_mean', 'crit_xue']}
    exp5.update({'n': n_full_h1, 'p': p_max_h1, 'M': M,
                 'B': B, 'n_repeats': N_REPEATS})
    pd.DataFrame([exp5]).to_csv(
        RESULTS_DIR / 'har_exp5_h1_replications.csv', index=False)
    logger.info(f"Exp5 (H1) -> boot_reject={exp5['boot_reject_rate']:.4f}, "
                f"xue_reject={exp5['xue_reject_rate']:.4f}")

    np.save(RESULTS_DIR / 'Tn_boot_list_h1.npy',
            np.array(rep_h1['Tn_boot_list']))
    np.save(RESULTS_DIR / 'Tn_xue_list_h1.npy',
            np.array(rep_h1['Tn_xue_list']))

    # 7) 实验 6：H1 的 p/n 网格扫描（与 Exp3 对应）
    logger.info("\n--- 实验 6: H1 p/n 网格扫描 ---")
    if N_pool_h1 >= 50:
        n_grid_h1 = [50, 100, 150, 200]
    else:
        n_grid_h1 = sorted(set([max(3, int(round(N_pool_h1 * frac)))
                                for frac in [0.2, 0.4, 0.6, 0.8, 1.0]]))
    p_grid_h1 = [3, 4, 5, 6]
    n_grid_h1 = [n for n in n_grid_h1 if n <= int(N_pool_h1 * 1.5)]
    p_grid_h1 = [p for p in p_grid_h1 if p <= p_max_h1]
    if not n_grid_h1:
        n_grid_h1 = [max(3, N_pool_h1)]

    tasks_h1 = []
    for n_v in n_grid_h1:
        for p_v in p_grid_h1:
            tasks_h1.append({
                'Y_pool': Y_pool_h1, 'n': n_v,
                'p_indices': tuple(range(p_v)),
                'n_repeats': max(30, N_REPEATS // 2),
                'B': B, 'alpha': ALPHA,
                'seed': 5000 + n_v * 10 + p_v
            })

    grid_results_h1 = []
    if tasks_h1:
        if USE_PARALLEL:
            with concurrent.futures.ProcessPoolExecutor(
                    max_workers=NUM_PROCESSES) as ex:
                futs = [ex.submit(task_executor, t) for t in tasks_h1]
                for f in tqdm(concurrent.futures.as_completed(futs),
                              total=len(futs), desc="H1 p/n grid"):
                    grid_results_h1.append(f.result())
        else:
            for t in tqdm(tasks_h1, desc="H1 p/n grid"):
                grid_results_h1.append(task_executor(t))

    if grid_results_h1:
        grid_df_h1 = pd.DataFrame([{
            'n': r['n'], 'p': r['p'], 'p_over_n': r['p'] / r['n'],
            'boot_reject_rate': r['boot_reject_rate'],
            'xue_reject_rate':  r['xue_reject_rate'],
            'Tn_boot_mean':     r['Tn_boot_mean'],
            'Tn_xue_mean':      r['Tn_xue_mean'],
            'pval_boot_mean':   r['pval_boot_mean'],
            'pval_xue_mean':    r['pval_xue_mean'],
        } for r in grid_results_h1]).sort_values(['n', 'p']).reset_index(drop=True)
    else:
        grid_df_h1 = pd.DataFrame(columns=['n', 'p', 'p_over_n', 'boot_reject_rate',
                                           'xue_reject_rate', 'Tn_boot_mean',
                                           'Tn_xue_mean', 'pval_boot_mean',
                                           'pval_xue_mean'])
    grid_df_h1.to_csv(RESULTS_DIR / 'har_exp6_h1_pn_grid.csv', index=False)
    logger.info(f"\n{grid_df_h1}")

    # ====== H0 可视化 ======
    logger.info("\n--- 生成 H0 可视化 ---")

    # (1) Tn 分布 vs Gumbel 理论
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    Tn_b_arr = np.array(rep['Tn_boot_list'])
    Tn_x_arr = np.array(rep['Tn_xue_list'])

    bins_b = 1 if np.allclose(np.nanmax(Tn_b_arr), np.nanmin(Tn_b_arr)) else min(30, len(Tn_b_arr))
    axes[0].hist(Tn_b_arr, bins=bins_b, alpha=0.7, edgecolor='k')
    axes[0].axvline(rep['crit_boot_mean'], color='r', linestyle='--',
                    label=f"Boot crit ≈ {rep['crit_boot_mean']:.3f}")
    axes[0].set_xlabel(r'$T_n$ (Our Method)')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title(f'Our Method  (n={n_full}, p={p_max}, M={M})')
    axes[0].legend()

    bins_x = 1 if np.allclose(np.nanmax(Tn_x_arr), np.nanmin(Tn_x_arr)) else min(30, len(Tn_x_arr))
    axes[1].hist(Tn_x_arr, bins=bins_x, alpha=0.7, edgecolor='k', density=True)
    xx = np.linspace(Tn_x_arr.min() - 1, Tn_x_arr.max() + 1, 500)
    axes[1].plot(xx, gumbel_pdf(xx), 'r-', lw=2, label='Gumbel PDF')
    axes[1].axvline(crit_x, color='g', linestyle='--',
                    label=f'Xue crit = {crit_x:.3f}')
    axes[1].set_xlabel(r'$T_n$ (Xue)')
    axes[1].set_ylabel('Density')
    axes[1].set_title(f'Xue vs Gumbel  (n={n_full}, p={p_max}, M={M})')
    axes[1].legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'Tn_distributions.png', dpi=150)
    plt.close()

    # (2) p/n 热力图（拒绝率）
    if not grid_df.empty:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        for ax, col, title in zip(
                axes, ['boot_reject_rate', 'xue_reject_rate'],
                ['Our Method (Bootstrap)', 'Xue (Asymptotic Gumbel)']):
            pivot = grid_df.pivot(index='p', columns='n', values=col)
            im = ax.imshow(pivot.values, aspect='auto', cmap='YlOrRd',
                           vmin=0, vmax=1, origin='lower')
            ax.set_xticks(range(len(pivot.columns)));
            ax.set_xticklabels(pivot.columns)
            ax.set_yticks(range(len(pivot.index)));
            ax.set_yticklabels(pivot.index)
            ax.set_xlabel('n'); ax.set_ylabel('p')
            ax.set_title(f'Reject Rate: {title}')
            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    ax.text(j, i, f'{pivot.values[i, j]:.2f}',
                            ha='center', va='center', fontsize=9)
            plt.colorbar(im, ax=ax)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / 'pn_grid_heatmap.png', dpi=150)
        plt.close()

        # (3) 折线对比：拒绝率 vs n（按 p 分组）
        fig, ax = plt.subplots(figsize=(10, 6))
        for p_v in sorted(grid_df['p'].unique()):
            sub = grid_df[grid_df['p'] == p_v].sort_values('n')
            ax.plot(sub['n'], sub['boot_reject_rate'], 'o-',
                    label=f'Ours, p={p_v}')
            ax.plot(sub['n'], sub['xue_reject_rate'], 's--',
                    label=f'Xue,  p={p_v}')
        ax.set_xlabel('n'); ax.set_ylabel('Reject Rate')
        ax.set_title('Reject Rate vs n (across p)')
        ax.legend(ncol=2, fontsize=8)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / 'reject_rate_vs_n.png', dpi=150)
        plt.close()
    else:
        logger.warning('实验3 数据为空，已跳过 p/n 热力图和拒绝率折线图。')

    # ====== H1 可视化 ======
    logger.info("\n--- 生成 H1 可视化 ---")

    # (4) H1 Tn 分布
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    Tn_b_arr_h1 = np.array(rep_h1['Tn_boot_list'])
    Tn_x_arr_h1 = np.array(rep_h1['Tn_xue_list'])

    bins_b_h1 = 1 if np.allclose(np.nanmax(Tn_b_arr_h1), np.nanmin(Tn_b_arr_h1)) else min(30, len(Tn_b_arr_h1))
    axes[0].hist(Tn_b_arr_h1, bins=bins_b_h1, alpha=0.7, edgecolor='k')
    axes[0].axvline(rep_h1['crit_boot_mean'], color='r', linestyle='--',
                    label=f"Boot crit ~ {rep_h1['crit_boot_mean']:.3f}")
    axes[0].set_xlabel(r'$T_n$ (Our Method)')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title(f'H1 Our Method  (n={n_full_h1}, p={p_max_h1}, M={M})')
    axes[0].legend()

    bins_x_h1 = 1 if np.allclose(np.nanmax(Tn_x_arr_h1), np.nanmin(Tn_x_arr_h1)) else min(30, len(Tn_x_arr_h1))
    axes[1].hist(Tn_x_arr_h1, bins=bins_x_h1, alpha=0.7, edgecolor='k', density=True)
    xx_h1 = np.linspace(Tn_x_arr_h1.min() - 1, Tn_x_arr_h1.max() + 1, 500)
    axes[1].plot(xx_h1, gumbel_pdf(xx_h1), 'r-', lw=2, label='Gumbel PDF')
    axes[1].axvline(crit_x_h1, color='g', linestyle='--',
                    label=f'Xue crit = {crit_x_h1:.3f}')
    axes[1].set_xlabel(r'$T_n$ (Xue)')
    axes[1].set_ylabel('Density')
    axes[1].set_title(f'H1 Xue vs Gumbel  (n={n_full_h1}, p={p_max_h1}, M={M})')
    axes[1].legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'Tn_distributions_h1.png', dpi=150)
    plt.close()

    # (5) H1 p/n 热力图
    if not grid_df_h1.empty:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        for ax, col, title in zip(
                axes, ['boot_reject_rate', 'xue_reject_rate'],
                ['Our Method (Bootstrap)', 'Xue (Asymptotic Gumbel)']):
            pivot = grid_df_h1.pivot(index='p', columns='n', values=col)
            im = ax.imshow(pivot.values, aspect='auto', cmap='YlOrRd',
                           vmin=0, vmax=1, origin='lower')
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_xticklabels(pivot.columns)
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels(pivot.index)
            ax.set_xlabel('n'); ax.set_ylabel('p')
            ax.set_title(f'H1 Reject Rate: {title}')
            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    ax.text(j, i, f'{pivot.values[i, j]:.2f}',
                            ha='center', va='center', fontsize=9)
            plt.colorbar(im, ax=ax)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / 'pn_grid_heatmap_h1.png', dpi=150)
        plt.close()

    # ====== H0 vs H1 对比图 ======
    logger.info("\n--- 生成 H0 vs H1 对比图 ---")

    # (6) 对比柱状图：拒绝率
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    scenarios = ['H0\n(Static)', 'H1\n(Dynamic)']
    boot_rates = [exp2['boot_reject_rate'], exp5['boot_reject_rate']]
    xue_rates  = [exp2['xue_reject_rate'],  exp5['xue_reject_rate']]

    x_pos = np.arange(len(scenarios))
    w = 0.35
    axes[0].bar(x_pos - w/2, boot_rates, w, label='Our Method', color='#4C72B0')
    axes[0].bar(x_pos + w/2, xue_rates,  w, label='Xue', color='#DD8452')
    axes[0].axhline(y=ALPHA, color='r', linestyle='--', alpha=0.7,
                    label=f'Target alpha={ALPHA}')
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels(scenarios)
    axes[0].set_ylabel('Reject Rate')
    axes[0].set_title('Reject Rate Comparison')
    axes[0].set_ylim(0, 1.15)
    axes[0].legend()
    for i, (b, x) in enumerate(zip(boot_rates, xue_rates)):
        axes[0].text(i - w/2, b + 0.03, f'{b:.2f}', ha='center', fontsize=10)
        axes[0].text(i + w/2, x + 0.03, f'{x:.2f}', ha='center', fontsize=10)

    # 对比 Tn 均值与临界值
    boot_tn = [exp2['Tn_boot_mean'], exp5['Tn_boot_mean']]
    boot_crit = [exp2['crit_boot_mean'], exp5['crit_boot_mean']]
    xue_tn = [exp2['Tn_xue_mean'], exp5['Tn_xue_mean']]
    xue_crit_val = [exp2['crit_xue'], exp5['crit_xue']]

    axes[1].bar(x_pos - w/2, boot_tn, w, label='Our $T_n$', color='#4C72B0')
    axes[1].bar(x_pos + w/2, xue_tn,  w, label='Xue $T_n$', color='#DD8452')
    axes[1].scatter(x_pos - w/2, boot_crit, marker='D', color='red', s=80, zorder=5,
                    label='Our crit')
    axes[1].scatter(x_pos + w/2, xue_crit_val, marker='D', color='green', s=80, zorder=5,
                    label='Xue crit')
    axes[1].set_xticks(x_pos)
    axes[1].set_xticklabels(scenarios)
    axes[1].set_ylabel('$T_n$ / Critical Value')
    axes[1].set_title('$T_n$ vs Critical Value')
    axes[1].legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'h0_vs_h1_comparison.png', dpi=150)
    plt.close()

    # ====== LaTeX 表格 ======
    with open(RESULTS_DIR / 'table1_basic.tex', 'w') as f:
        f.write(pd.DataFrame([exp1]).to_latex(
            index=False, float_format='%.4f',
            caption='HAR Static: 基础检验（单次实证）',
            label='tab:har_basic'))
    with open(RESULTS_DIR / 'table2_replications.tex', 'w') as f:
        f.write(pd.DataFrame([exp2]).to_latex(
            index=False, float_format='%.4f',
            caption='HAR Static: 子抽样重复（两种方法对比）',
            label='tab:har_replications'))
    with open(RESULTS_DIR / 'table3_pn_grid.tex', 'w') as f:
        f.write(grid_df.to_latex(
            index=False, float_format='%.4f',
            caption='HAR Static: p/n 网格扫描',
            label='tab:har_pn_grid'))

    # ===================================================================
    #  汇总：H0 vs H1 对比
    # ===================================================================
    logger.info("\n--- 生成 H0 vs H1 汇总 ---")

    summary_h0_h1 = pd.DataFrame([
        {'hypothesis': 'H0 (static)', 'Tn_boot_mean': exp2['Tn_boot_mean'],
         'crit_boot_mean': exp2['crit_boot_mean'],
         'boot_reject_rate': exp2['boot_reject_rate'],
         'Tn_xue_mean': exp2['Tn_xue_mean'],
         'crit_xue': exp2['crit_xue'],
         'xue_reject_rate': exp2['xue_reject_rate']},
        {'hypothesis': 'H1 (dynamic)', 'Tn_boot_mean': exp5['Tn_boot_mean'],
         'crit_boot_mean': exp5['crit_boot_mean'],
         'boot_reject_rate': exp5['boot_reject_rate'],
         'Tn_xue_mean': exp5['Tn_xue_mean'],
         'crit_xue': exp5['crit_xue'],
         'xue_reject_rate': exp5['xue_reject_rate']},
    ])
    summary_h0_h1.to_csv(RESULTS_DIR / 'har_summary_h0_vs_h1.csv', index=False)
    logger.info(f"\n{summary_h0_h1.to_string(index=False)}")

    # ====== H1 LaTeX 表格 ======
    with open(RESULTS_DIR / 'table4_h1_basic.tex', 'w') as f:
        f.write(pd.DataFrame([exp4]).to_latex(
            index=False, float_format='%.4f',
            caption='HAR Dynamic (H1): 基础检验（单次实证）',
            label='tab:har_h1_basic'))
    with open(RESULTS_DIR / 'table5_h1_replications.tex', 'w') as f:
        f.write(pd.DataFrame([exp5]).to_latex(
            index=False, float_format='%.4f',
            caption='HAR Dynamic (H1): 子抽样重复（两种方法对比）',
            label='tab:har_h1_replications'))
    with open(RESULTS_DIR / 'table6_h1_pn_grid.tex', 'w') as f:
        f.write(grid_df_h1.to_latex(
            index=False, float_format='%.4f',
            caption='HAR Dynamic (H1): p/n 网格扫描',
            label='tab:har_h1_pn_grid'))
    with open(RESULTS_DIR / 'table_summary_h0_vs_h1.tex', 'w') as f:
        f.write(summary_h0_h1.to_latex(
            index=False, float_format='%.4f',
            caption='H0 vs H1 汇总对比',
            label='tab:har_summary'))

    logger.info(f"\n总耗时: {time.time() - t0:.2f}s")
    logger.info(f"结果保存于 {RESULTS_DIR}, 图保存于 {FIGURES_DIR}")


if __name__ == "__main__":
    main()
