# har_data_loader.py
import numpy as np
import pandas as pd
import csv
from common.paths import HAR_DATA_DIR

VAR_COLS = [f'var_{i}' for i in range(6)]


def load_har_static(csv_path=HAR_DATA_DIR / 'har_static_subject.csv', verbose=True):
    # 防止极长字段导致的 ParserWarning
    try:
        csv.field_size_limit(10 * 1024 * 1024)
    except Exception:
        pass

    path = str(csv_path)
    if path.lower().endswith(('.csv', '.txt')):
        encodings = ['utf-8', 'gbk', 'latin1', 'cp1252']
        last_exc = None
        for enc in encodings:
            try:
                df = pd.read_csv(csv_path, encoding=enc, engine='python',
                                 on_bad_lines='warn')
                if verbose:
                    print(f"[Loader] 读取表格: {csv_path} (encoding={enc})")
                break
            except Exception as e:
                last_exc = e
            else:
                raise last_exc
    else:
        # 先尝试 Excel，再回退为 CSV 多编码尝试
        try:
            df = pd.read_excel(csv_path)
            if verbose:
                print(f"[Loader] 读取 Excel: {csv_path}")
        except Exception as e:
            encodings = ['utf-8', 'gbk', 'latin1', 'cp1252']
            last_exc = e
            for enc in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=enc, engine='python',
                                     on_bad_lines='warn')
                    if verbose:
                        print(f"[Loader] 回退按表格读取: {csv_path} (encoding={enc})")
                    break
                except Exception as e2:
                    last_exc = e2
            else:
                raise last_exc

    # 强制 VAR_COLS 为数值，删除无法解析或含 NaN 的行
    try:
        for c in VAR_COLS:
            df[c] = pd.to_numeric(df[c], errors='coerce')
        n_before = len(df)
        df = df.dropna(subset=VAR_COLS).reset_index(drop=True)
        n_dropped = n_before - len(df)
        if n_dropped > 0 and verbose:
            print(f"[Loader] 已删除 {n_dropped} 行含 NaN 的记录（共 {n_before} → {len(df)}）")
    except Exception:
        # 如果强转失败则直接返回原始 df
        pass

    return df


def fourier_basis(M, q):
    """与 data_generator 完全一致的傅里叶基"""
    t = np.linspace(0, 1, M)
    basis = np.empty((M, q))
    basis[:, 0] = 1.0
    for idx in range(1, q):
        k = (idx + 1) // 2
        if idx % 2 == 1:
            basis[:, idx] = np.sqrt(2) * np.sin(2 * np.pi * k * t)
        else:
            basis[:, idx] = np.sqrt(2) * np.cos(2 * np.pi * k * t)
    return basis


def fourier_smooth_batch(Y, q):
    """对 (n, p, M) 张量按 (n,p) 通道 Fourier 投影 + 重构平滑"""
    n, p, M = Y.shape
    B = fourier_basis(M, q)                # (M, q)
    pinvB = np.linalg.pinv(B)              # (q, M)
    Y_2d = Y.reshape(n * p, M).T           # (M, n*p)
    coef = pinvB @ Y_2d                    # (q, n*p)
    Y_smooth = (B @ coef).T.reshape(n, p, M)
    return Y_smooth


def safe_log_return(x, eps=1e-8):
    """
    对 (T, p) 时序做对数收益。
    HAR 传感器数据可能含负值，做平移：x' = x - min + 1，再 log-diff。
    """
    x = np.asarray(x, dtype=float)
    mins = x.min(axis=0, keepdims=True)
    shift = np.where(mins <= 0, -mins + 1.0, 0.0)
    x_pos = x + shift
    log_x = np.log(x_pos + eps)
    return np.diff(log_x, axis=0)          # (T-1, p)


def standardize_tensor(Y):
    """沿 sample 轴标准化（zero mean, unit var）"""
    mu = Y.mean(axis=0, keepdims=True)
    sd = Y.std(axis=0, keepdims=True) + 1e-12
    return (Y - mu) / sd


def build_windows(df, var_cols=VAR_COLS, M=48, stride=2,
                  apply_log_return=True, q_smooth=5,
                  do_smooth=True, do_std=True, verbose=True):
    """
    主接口：返回 (n, p, M) 张量
    流程：按 subject 分组 → log-return → 非重叠滑动窗口 → Fourier 平滑 → 标准化
    """
    subjects = sorted(df['subject'].unique())
    windows = []
    per_sub_count = {}

    # 使用传入的 stride 参数（之前错误地强制设为 M 导致总是非重叠）
    # stride = M
    for sub in subjects:
        sub_df = df[df['subject'] == sub].sort_values('time')
        X = sub_df[var_cols].values                 # (T, p)

        if apply_log_return:
            X = safe_log_return(X)                  # (T-1, p)

        T = X.shape[0]
        if T < M:
            continue
        cnt = 0
        for start in range(0, T - M + 1, stride):
            window = X[start:start + M, :].T        # (p, M)
            windows.append(window)
            cnt += 1
        per_sub_count[sub] = cnt

    Y = np.array(windows)                           # (n, p, M)

    if do_smooth:
        Y = fourier_smooth_batch(Y, q_smooth)
    if do_std:
        Y = standardize_tensor(Y)

    if verbose:
        print(f"[Loader] 每个 subject 产生窗口数: {per_sub_count}")
        print(f"[Loader] 最终张量形状: {Y.shape}  (n, p, M)")
    return Y
