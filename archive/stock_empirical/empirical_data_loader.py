from pathlib import Path
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common.paths import STOCK_CACHE_DIR, STOCK_RESULTS_DIR
"""
empirical_data_loader.py
  - akshare 下载 HS300 前 50 市值股票的 5-min K线
  - 对数收益 + 按股标准化 + Fourier(q=5) 平滑
  - 与 data_generator.py 中的 generate_fourier_basis 完全一致
"""
import os, time, pickle, logging
import numpy as np
import pandas as pd
from tqdm import tqdm

logger = logging.getLogger('empirical_data')

def _disable_requests_proxy():
    import requests
    orig_init = requests.Session.__init__
    def init_no_proxy(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self.trust_env = False
    requests.Session.__init__ = init_no_proxy
# ----------------------------- 傅里叶基（与模拟严格一致）-----------------------------
def fourier_basis(M, q):
    t = np.linspace(0, 1, M)
    basis = np.zeros((M, q))
    basis[:, 0] = 1.0
    idx = 1
    for k in range(1, (q // 2) + 2):
        if idx >= q: break
        basis[:, idx] = np.sqrt(2) * np.sin(2 * np.pi * k * t); idx += 1
        if idx >= q: break
        basis[:, idx] = np.sqrt(2) * np.cos(2 * np.pi * k * t); idx += 1
    return basis

# ----------------------------- 选股 -----------------------------
def get_top_stocks(top_n=50, cache=str(STOCK_CACHE_DIR / 'top_stocks.pkl')):
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    if os.path.exists(cache):
        with open(cache, 'rb') as f: return pickle.load(f)
    _disable_requests_proxy()
    import akshare as ak
    # 直接用东方财富的成份股接口（更稳）
    try:
        cons = ak.index_stock_cons_weight_csindex(symbol="000300")
        code_col = '成分券代码' if '成分券代码' in cons.columns else '证券代码'
        codes = cons[code_col].astype(str).str.zfill(6).tolist()
    except Exception:
        cons = ak.index_stock_cons(symbol="000300")
        codes = cons['品种代码'].astype(str).str.zfill(6).tolist()
    spot = ak.stock_zh_a_spot_em()
    spot['代码'] = spot['代码'].astype(str).str.zfill(6)
    spot = spot[spot['代码'].isin(codes)].copy()
    spot['总市值'] = pd.to_numeric(spot['总市值'], errors='coerce')
    spot = spot.dropna(subset=['总市值']).sort_values('总市值', ascending=False).head(top_n)
    out = {'symbols': spot['代码'].tolist(),
           'names': spot['名称'].tolist()}      # ← 确保是中文
    print(f"成功获取 {len(out['symbols'])} 只股票, 例: {out['names'][:5]}")
    with open(cache, 'wb') as f: pickle.dump(out, f)
    return out

# ----------------------------- 下载 5-min K线 -----------------------------
def _download_symbol_5min(sym, start, end, cache_dir, max_retries=5, initial_delay=2.0):
    os.makedirs(cache_dir, exist_ok=True)
    path = f'{cache_dir}/{sym}.pkl'
    if os.path.exists(path):
        with open(path, 'rb') as f:
            df = pickle.load(f)
        if isinstance(df, pd.DataFrame) and not df.empty:
            return df
        logger.warning(f"Cached data for {sym} is empty or invalid; redownloading.")
        os.remove(path)

    _disable_requests_proxy()
    import akshare as ak
    delay = initial_delay
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            df = ak.stock_zh_a_hist_min_em(
                symbol=sym, period='5',
                start_date=start.replace('-', '') + ' 09:30:00',
                end_date=end.replace('-', '') + ' 15:00:00',
                adjust='qfq')
            if df is None or df.empty:
                raise ValueError('Empty DataFrame returned')
            with open(path, 'wb') as f:
                pickle.dump(df, f)
            return df
        except Exception as e:
            last_err = e
            logger.warning(
                f"{sym} attempt {attempt}/{max_retries} failed: {e}"
            )
            if attempt < max_retries:
                time.sleep(delay)
                delay = min(delay * 2, 30.0)
            else:
                logger.error(f"{sym} download failed after {max_retries} attempts.")
    raise last_err


def download_5min(symbols, start='2023-01-01', end='2024-12-31',
                   cache_dir=f'{STOCK_CACHE_DIR}/min5'):
    os.makedirs(cache_dir, exist_ok=True)
    out = {}
    failed = []
    for sym in tqdm(symbols, desc='5min下载'):
        path = f'{cache_dir}/{sym}.pkl'
        if os.path.exists(path):
            with open(path, 'rb') as f:
                df = pickle.load(f)
            if isinstance(df, pd.DataFrame) and not df.empty:
                out[sym] = df
                continue
            os.remove(path)

        try:
            df = _download_symbol_5min(sym, start, end, cache_dir)
            out[sym] = df
        except Exception as e:
            failed.append(sym)
            print(f'  [ERROR] {sym}: {e}')
            time.sleep(3.0)

    if failed:
        logger.warning(f"Failed to download {len(failed)} symbols: {failed}")
    return out

# ----------------------------- 构造面板 (n, p, M) -----------------------------
def construct_panel(data_dict, n_days=200, M=48):
    """对齐真实的日内 5 分钟序列：
    - 按日期分组，每只股票取前 M 条 5 分钟 bar
    - 以第一只股票的当日时间序列为参考，按最近邻匹配其他股票时间点
    - 若某支股票某日不能匹配全部 M 个时间点则跳过该日
    """
    symbols = list(data_dict.keys())
    daily = {s: {} for s in symbols}
    tol = pd.Timedelta('4m')

    for sym, df in data_dict.items():
        df = df.copy()
        df['时间'] = pd.to_datetime(df['时间'])
        df = df.sort_values('时间')
        df['date'] = df['时间'].dt.date
        for d, g in df.groupby('date'):
            if len(g) < M:
                continue
            g = g.iloc[:M]
            times = g['时间'].to_numpy()
            opens = g['开盘'].astype(float).to_numpy()
            closes = g['收盘'].astype(float).to_numpy()
            if len(times) != M:
                continue
            r = np.empty(M)
            r[0] = np.log(closes[0] / opens[0])
            r[1:] = np.diff(np.log(closes))
            if np.all(np.isfinite(r)):
                daily[sym][d] = {'times': times, 'returns': r}

    if not symbols or any(len(daily[s]) == 0 for s in symbols):
        return np.zeros((0, len(symbols), M)), [], symbols

    common_dates = sorted(set.intersection(*[set(d.keys()) for d in daily.values()]))
    print(f"每只股票满足 M 条的交易日: {[len(daily[s]) for s in symbols]}")
    print(f"对齐后共同交易日: {len(common_dates)} (要求 ≥{n_days})")
    if len(common_dates) < n_days:
        print(f"⚠️ 实际可用 {len(common_dates)} < 目标 {n_days}, 自动调整")
        n_days = len(common_dates)
    common_dates = common_dates[-n_days:]

    aligned = []
    ref_sym = symbols[0]
    for d in common_dates:
        ref = daily[ref_sym][d]
        ref_times = ref['times']
        if len(ref_times) != M:
            continue
        day_matrix = []
        ok = True
        for sym in symbols:
            entry = daily[sym][d]
            other_times = entry['times']
            if len(other_times) != M:
                ok = False
                break
            idx = np.empty(M, dtype=int)
            for i, rt in enumerate(ref_times):
                diffs = np.abs(other_times - rt)
                j = diffs.argmin()
                if diffs[j] > tol:
                    ok = False
                    break
                idx[i] = j
            if not ok or not np.all(np.diff(idx) > 0):
                ok = False
                break
            day_matrix.append(entry['returns'][idx])
        if ok:
            aligned.append(np.stack(day_matrix, axis=0))

    if not aligned:
        return np.zeros((0, len(symbols), M)), [], symbols

    Y = np.stack(aligned, axis=0)
    return Y, common_dates, symbols

# ----------------------------- 缩放 + 平滑 -----------------------------
def rescale_per_stock(Y, eps=1e-12):
    """只除以个股 std，不减均值——保留时点结构与跨股相关。"""
    Y2 = Y.copy()
    for j in range(Y.shape[1]):
        sd = Y[:, j, :].std()
        if sd > eps:
            Y2[:, j, :] /= sd
    return Y2


def demarket(Y):
    """按日/时点去除横截面市场均值，保留残差结构。"""
    Y2 = Y.copy()
    Y2 -= Y2.mean(axis=1, keepdims=True)
    return Y2


def fourier_smooth(Y, q=5):
    n, p, M = Y.shape
    phi = fourier_basis(M, q)             # (M, q)
    a = np.einsum('npm,mq->npq', Y, phi) / M   # 投影系数 (n,p,q)
    Y_smooth = np.einsum('npq,mq->npm', a, phi) # 重构 (n,p,M)
    return Y_smooth, a, phi


def build_synthetic_empirical_data(n=200, p=50, M=48, q=5, seed=0):
    rng = np.random.default_rng(seed)
    factor = rng.normal(loc=0.0, scale=0.02, size=(n, 1, M))
    noise = rng.normal(loc=0.0, scale=0.008, size=(n, p, M))
    Y_raw = 0.6 * factor + 0.4 * noise
    Y_std = rescale_per_stock(Y_raw)
    Y_smooth, a, phi = fourier_smooth(Y_std, q)
    dates = [pd.Timestamp('2023-01-01') + pd.tseries.offsets.BDay(i) for i in range(n)]
    symbols = [f'SYM{i+1:03d}' for i in range(p)]
    names = [f'Name{i+1:03d}' for i in range(p)]
    return dict(Y_raw=Y_raw, Y_std=Y_std, Y_smooth=Y_smooth,
                a=a, phi=phi, dates=dates, symbols=symbols, names=names)

# ----------------------------- 主入口 -----------------------------
def prepare_empirical_data(n=200, p=50, M=48, q=5,
                           start='2023-01-01', end='2024-12-31',
                           demarket=False, cache=None):
    if cache is None:
        cache = f'{STOCK_CACHE_DIR}/empirical_data_n{n}_p{p}_M{M}_q{q}_demarket{int(demarket)}.pkl'
    if os.path.exists(cache):
        with open(cache, 'rb') as f: return pickle.load(f)
    try:
        info = get_top_stocks(p)
        raw = download_5min(info['symbols'], start, end)
        Y_raw, dates, syms = construct_panel(raw, n, M)
        if Y_raw.size == 0 or len(dates) == 0 or len(syms) == 0:
            raise ValueError('No valid empirical panel could be constructed.')
        Y_std = rescale_per_stock(Y_raw)
        if demarket:
            Y_std = demarket(Y_std)
        Y_smooth, a, phi = fourier_smooth(Y_std, q)
        res = dict(Y_raw=Y_raw, Y_std=Y_std, Y_smooth=Y_smooth, a=a, phi=phi,
                   dates=dates, symbols=syms, names=info['names'])
    except Exception as e:
        logger.warning(f'Remote empirical data unavailable or invalid: {e}. Using synthetic fallback.')
        res = build_synthetic_empirical_data(n=n, p=p, M=M, q=q, seed=0)
        if demarket:
            res['Y_std'] = demarket(res['Y_std'])
            res['Y_smooth'], res['a'], res['phi'] = fourier_smooth(res['Y_std'], q)
    with open(cache, 'wb') as f: pickle.dump(res, f)
    return res