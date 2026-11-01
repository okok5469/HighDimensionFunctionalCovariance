from pathlib import Path
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ============ 必须放在 import numpy 之前 ============
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["BLIS_NUM_THREADS"] = "1"
# ===================================================

import numpy as np
import time
import pandas as pd
from tqdm import tqdm
from simulation.data_generator_three import create_dataset_M3
from common.xue_helper import run_xue_cross_test, S_XUE_DEFAULT
from common.statistic_calculator_517 import covariance_test
import concurrent.futures
import multiprocessing
import logging
import hashlib
from common.paths import SIMULATION_RESULTS_DIR

# ----------------- 配置 -----------------
USE_PARALLEL  = True
NUM_PROCESSES = min(16, multiprocessing.cpu_count())   # 不要 50

B          = 500          # Bootstrap 重复次数
n_repeats  = 100          # 每个参数组合的重复实验次数
TEST_MODE  = False        # True=快速测试; False=正式运行
S_XUE      = S_XUE_DEFAULT  # 【新增】Xue 方法基展开截断项数(不要用 M!)
ALPHA      = 0.05           # 【新增】显著性水平

OUTPUT_DIR = SIMULATION_RESULTS_DIR / 'model3' / 'xue-audit-v1'

# ----------------- 日志 -----------------
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('high_dim_cov_test_M3')


# ----------------- 任务列表 -----------------
def create_experiment_tasks():
    """创建所有实验任务 (M3 模型版)"""
    tasks = []

    # ---- 实验 1: 类型 I 错误率 (H0) ----
    if not TEST_MODE:
        n_values = [500, 1000]
        p_values = [10, 50]
        M_values = [30]
    else:
        n_values = [50]
        p_values = [5]
        M_values = [20]

    for n in n_values:
        for p in p_values:
            for M in M_values:
                tasks.append({
                    'experiment': 1,
                    'n': n, 'p': p, 'M': M,
                    'h0': True,
                    'sigma_noise': 0.05,
                    'B': B,
                    'n_repeats': n_repeats
                })

    # ---- 实验 2: 检验功效 (H1) ----
    if not TEST_MODE:
        s0_values = [4, 8]
        signal_strength_values = [0.205, 0.215]
        n_values = [500]
        p = 50
        M = 30
    else:
        s0_values = [4]
        signal_strength_values = [0.1]
        n_values = [50]
        p = 5
        M = 20

    for s0 in s0_values:
        for ss in signal_strength_values:
            for n in n_values:
                tasks.append({
                    'experiment': 2,
                    'n': n, 'p': p, 'M': M,
                    's0': s0,
                    'signal_strength': ss,
                    'h0': False,
                    'sigma_noise': 0.05,
                    'B': B,
                    'n_repeats': n_repeats
                })

    # ---- 实验 3: 高维渐近行为 ----
    if not TEST_MODE:
        n = 500
        p_values = [50, 100]
        M = 30
    else:
        n = 50
        p_values = [5]
        M = 20

    for p in p_values:
        tasks.append({
            'experiment': 3,
            'n': n, 'p': p, 'M': M,
            's0': 4,
            'signal_strength': 0.235,
            'h0': False,
            'sigma_noise': 0.05,
            'B': B,
            'n_repeats': n_repeats
        })

    return tasks


# ----------------- 单任务执行 -----------------
def execute_single_task(task):
    """
    每个参数组合重复 n_repeats 次，
    同时运行 [我们的方法] 与 [Xue 方法] 做对照。
    """
    try:
        task_str = str(sorted(task.items()))
        base_seed = 42 + int(hashlib.md5(task_str.encode()).hexdigest(), 16) % 100000

        reject_ours = 0
        reject_xue  = 0
        time_ours   = 0.0
        time_xue    = 0.0

        start_time = time.time()
        for r in range(task['n_repeats']):
            current_seed = base_seed + r * 13579

            # ---- 调用 M3 数据生成 ----
            data = create_dataset_M3(
                n=task['n'],
                p=task['p'],
                M=task['M'],
                sigma_noise=task['sigma_noise'],
                h0=task['h0'],
                s0=task.get('s0', 4),
                signal_strength=task.get('signal_strength', 0.3),
                seed=current_seed
            )
            Y = data['Y']

            # ----- 我们的方法 -----
            t0 = time.time()
            Tn, crit, pval = covariance_test(Y, B=task['B'])
            time_ours += time.time() - t0
            if pval < ALPHA:
                reject_ours += 1

            # ----- Xue 方法（先做基展开!） -----
            t0 = time.time()
            xue = run_xue_cross_test(Y, s=S_XUE, alpha=ALPHA)
            if xue['status'] != 'ok':
                raise ValueError(f"{xue['status']}: {xue['failure_reason']}")
            Tn_x, tau_x, pval_x = xue['T'], xue['critical_T'], xue['p_value']
            time_xue += time.time() - t0
            if xue['reject']:
                reject_xue += 1

        total_time = time.time() - start_time
        rate_ours = reject_ours / task['n_repeats']
        rate_xue  = reject_xue  / task['n_repeats']

        # ---- 构建结果 ----
        common = {
            'xue_method': 'Xue-1S-EV-cross-zero',
            'xue_version': 'xue-audit-v1',
            'xue_tail_arithmetic': 'stable_expm1',
            'xue_theory': 'Gaussian innovations with MA(1) dependence across observations; iid EV theory is not established for this design',
            'xue_n': task['n'], 'xue_p': task['p'], 'xue_s': S_XUE,
            'xue_d': task['p'] * S_XUE, 'xue_status': 'ok',
            'xue_covariance_denominator': 'n', 'xue_mean_mode': 'estimate',
            'xue_projection_id': 'fixed_fourier_rectangle_1_over_M',
            'xue_basis_id': 'fixed_fourier_phi_0_to_s_minus_1',
            'time_total':  total_time,
            'time_ours':   time_ours,
            'time_xue':    time_xue,
            'B':           task['B'],
            'n_repeats':   task['n_repeats'],
            's_xue':       S_XUE,
        }
        if task['experiment'] == 1:
            result = {
                'experiment': 1,
                'n': task['n'], 'p': task['p'], 'M': task['M'],
                'reject_rate':     rate_ours,
                'reject_rate_xue': rate_xue,
                **common
            }
        elif task['experiment'] == 2:
            result = {
                'experiment': 2,
                'n': task['n'],
                's0': task['s0'],
                'signal_strength': task['signal_strength'],
                'power':     rate_ours,
                'power_xue': rate_xue,
                **common
            }
        else:  # experiment 3
            result = {
                'experiment': 3,
                'n': task['n'], 'p': task['p'],
                'p_over_n': task['p'] / task['n'],
                'power':     rate_ours,
                'power_xue': rate_xue,
                **common
            }

        logger.info(
            f"任务组完成 | 实验{task['experiment']} | "
            f"n={task['n']}, p={task['p']} | "
            f"Ours={rate_ours:.4f} | Xue={rate_xue:.4f} | "
            f"耗时(Ours/Xue)={time_ours:.1f}s/{time_xue:.1f}s"
        )
        return result

    except Exception as e:
        logger.error(f"任务组失败 | 实验{task.get('experiment','N/A')} | "
                     f"{task} | 错误：{str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise


# ----------------- 中间保存 -----------------
def save_partial_results(results, experiment_num):
    df = pd.DataFrame([r for r in results if r['experiment'] == experiment_num])
    if not df.empty:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filename = f'{OUTPUT_DIR}/experiment{experiment_num}_partial.csv'
        df.to_csv(filename, index=False)
        logger.info(f"实验{experiment_num} 中间结果已保存到 {filename}")


# ----------------- 主流程 -----------------
def run_experiment():
    start_time = time.time()
    logger.info("=" * 80)
    logger.info("M3 模型 (函数型 MA(1)) 高维协方差检验实验启动 (Ours vs Xue)")
    logger.info(f"并行模式: {USE_PARALLEL} | 进程数: {NUM_PROCESSES} | "
                f"测试模式: {TEST_MODE}")
    logger.info(f"参数: B={B}, n_repeats={n_repeats}, S_XUE={S_XUE}, ALPHA={ALPHA}")
    logger.info("=" * 80)

    tasks = create_experiment_tasks()
    logger.info(f"总任务数: {len(tasks)}")

    # 按实验编号分组
    experiment_groups = {}
    for task in tasks:
        experiment_groups.setdefault(task['experiment'], []).append(task)

    all_results = []

    for exp_num in sorted(experiment_groups.keys()):
        logger.info(f"\n开始运行实验 {exp_num}, 任务数: "
                    f"{len(experiment_groups[exp_num])}")
        group_start = time.time()
        group_results = []

        if USE_PARALLEL:
            logger.info(f"实验{exp_num}: 多进程并行 (workers={NUM_PROCESSES})")
            with concurrent.futures.ProcessPoolExecutor(max_workers=NUM_PROCESSES) as executor:
                futures = {executor.submit(execute_single_task, t): t
                           for t in experiment_groups[exp_num]}
                for fut in tqdm(concurrent.futures.as_completed(futures),
                                total=len(experiment_groups[exp_num]),
                                desc=f"实验{exp_num}进度"):
                    res = fut.result()
                    group_results.append(res)
        else:
            logger.info(f"实验{exp_num}: 串行计算")
            for t in tqdm(experiment_groups[exp_num], desc=f"实验{exp_num}进度"):
                res = execute_single_task(t)
                group_results.append(res)

        all_results.extend(group_results)

        # 反馈即时结果
        if group_results:
            if exp_num == 1:
                a = np.mean([r['reject_rate']     for r in group_results])
                b = np.mean([r['reject_rate_xue'] for r in group_results])
                msg = f"实验1完成 | Ours拒绝率={a:.4f} | Xue拒绝率={b:.4f}"
                logger.info(msg); print(msg)
            elif exp_num == 2:
                a = np.mean([r['power']     for r in group_results])
                b = np.mean([r['power_xue'] for r in group_results])
                msg = f"实验2完成 | Ours功效={a:.4f} | Xue功效={b:.4f}"
                logger.info(msg); print(msg)
            elif exp_num == 3:
                a = np.mean([r['power']     for r in group_results])
                b = np.mean([r['power_xue'] for r in group_results])
                msg = f"实验3完成 | Ours功效={a:.4f} | Xue功效={b:.4f}"
                logger.info(msg); print(msg)

        logger.info(f"实验{exp_num}耗时: {time.time() - group_start:.2f}秒")
        save_partial_results(all_results, exp_num)

    # ---- 聚合保存 ----
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_results_df = pd.DataFrame(all_results)
    all_results_df.to_csv(f'{OUTPUT_DIR}/all_experiments_results.csv', index=False)

    for exp_num in [1, 2, 3]:
        rows = [r for r in all_results if r['experiment'] == exp_num]
        if rows:
            pd.DataFrame(rows).to_csv(
                f'{OUTPUT_DIR}/experiment{exp_num}_results.csv', index=False)

    exp1 = [r for r in all_results if r['experiment'] == 1]
    exp2 = [r for r in all_results if r['experiment'] == 2]

    avg_reject_ours = np.mean([r['reject_rate']     for r in exp1]) if exp1 else 0
    avg_reject_xue  = np.mean([r['reject_rate_xue'] for r in exp1]) if exp1 else 0
    avg_power_ours  = np.mean([r['power']           for r in exp2]) if exp2 else 0
    avg_power_xue   = np.mean([r['power_xue']       for r in exp2]) if exp2 else 0

    logger.info("\n" + "=" * 80)
    logger.info("M3 模型实验总结 (Ours vs Xue)")
    logger.info("=" * 80)
    logger.info(f"实验1 类型I错误率  | Ours={avg_reject_ours:.4f}  Xue={avg_reject_xue:.4f}")
    logger.info(f"实验2 检验功效     | Ours={avg_power_ours:.4f}   Xue={avg_power_xue:.4f}")
    logger.info(f"实验3 高维渐近行为 | 结果已保存")
    logger.info(f"总耗时: {time.time() - start_time:.2f}秒")
    logger.info("=" * 80)

    return {
        'experiment1_ours': avg_reject_ours,
        'experiment1_xue':  avg_reject_xue,
        'experiment2_ours': avg_power_ours,
        'experiment2_xue':  avg_power_xue,
        'all_results': all_results_df
    }


# ----------------- 入口 -----------------
if __name__ == "__main__":
    USE_PARALLEL = True
    TEST_MODE    = False

    main_start = time.time()
    summary = run_experiment()

    print("\n" + "=" * 80)
    print(f"M3 实验完成! 结果已保存到 {OUTPUT_DIR}/ 目录")
    print(f"实验1 拒绝率 | Ours={summary['experiment1_ours']:.4f}  Xue={summary['experiment1_xue']:.4f}")
    print(f"实验2 功效   | Ours={summary['experiment2_ours']:.4f}  Xue={summary['experiment2_xue']:.4f}")
    print(f"总任务数  : {len(create_experiment_tasks())}")
    print(f"总耗时    : {time.time() - main_start:.2f}秒")
    print("=" * 80)
