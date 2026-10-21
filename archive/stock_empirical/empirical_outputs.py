from pathlib import Path
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common.paths import STOCK_CACHE_DIR, STOCK_RESULTS_DIR
"""LaTeX 表格 + 可视化"""
import os, numpy as np, pandas as pd
import matplotlib.pyplot as plt

OUT = str(STOCK_RESULTS_DIR)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['axes.unicode_minus'] = False

# ============== LaTeX ==============
def tex_exp1(df, path):
    r = df.iloc[0]
    s = (r"""\begin{table}[htbp]\centering
\caption{基础检验：MB Bootstrap 与 Xue 渐近临界值法对比 ($n=%d,p=%d,M=%d,q=%d$)}\label{tab:emp1}
\begin{tabular}{lccccc}\toprule
方法 & $T_n$ & 临界值 & $p$ 值 & 拒绝 $H_0$ & 耗时(s)\\\midrule
MB Bootstrap ($B=500$) & %.4f & %.4f & %.4g & %s & %.2f\\
Xue 渐近 (Gumbel)      & %.4f & %.4f & %.4g & %s & %.4f\\
\bottomrule\end{tabular}\end{table}
""" % (int(r.n), int(r.p), int(r.M), int(r.q),
       r.Tn_mb,  r.crit_mb,  r.pval_mb,  '是' if r.reject_mb  else '否', r.time_mb,
       r.Tn_xue, r.crit_xue, r.pval_xue, '是' if r.reject_xue else '否', r.time_xue))
    open(path,'w',encoding='utf-8').write(s)

def tex_exp3(df, path):
    rows=''
    for _,r in df.iterrows():
        rows += "%d & %d & %.3f & %.3f & %.3f & %.3g & %.3f & %.3f & %.3g & %s & %s\\\\\n"%(
            int(r.n), int(r.p), r.p_over_n,
            r.Tn_mb, r.crit_mb, r.pval_mb,
            r.Tn_xue, r.crit_xue, r.pval_xue,
            '是' if r.reject_mb else '否', '是' if r.reject_xue else '否')
    s = (r"""\begin{table}[htbp]\centering
\caption{p/n 影响：两种方法对比扫描}\label{tab:emp3}
\begin{tabular}{ccc|ccc|ccc|cc}\toprule
$n$&$p$&$p/n$&$T_n^{MB}$&$\hat c_{MB}$&$p_{MB}$&$T_n^{Xue}$&$\tau_\alpha$&$p_{Xue}$&MB拒&Xue拒\\\midrule
"""+rows+r"\bottomrule\end{tabular}\end{table}")
    open(path,'w',encoding='utf-8').write(s)

# ============== 图 ==============
def fig_smooth(data, path, n_show=4, p_show=4):
    Y, Ys = data['Y_std'], data['Y_smooth']
    n,p,M = Y.shape
    fig, ax = plt.subplots(p_show, n_show, figsize=(n_show*3.2, p_show*2.4),
                           sharex=True)
    t = np.arange(M)
    for i in range(p_show):
        for j in range(n_show):
            a = ax[i,j]
            a.plot(t, Y[j,i],  'b-', alpha=.35, lw=.8, label='标准化对数收益' if (i==j==0) else None)
            a.plot(t, Ys[j,i], 'r-', lw=1.5, label='傅里叶平滑(q=5)' if (i==j==0) else None)
            if i==0: a.set_title(f'第{j+1}天', fontsize=9)
            if j==0:
                nm = data['names'][i] if i<len(data['names']) else ''
                a.set_ylabel(f'股{i+1}\n{nm}', fontsize=8)
            if i==p_show-1: a.set_xlabel('5-min bar')
            a.grid(alpha=.25)
    ax[0,0].legend(fontsize=8, loc='upper right')
    fig.suptitle(f'对数收益标准化 + 傅里叶平滑展示  (q=5, M={M})', y=1.01)
    plt.tight_layout(); plt.savefig(path, dpi=130, bbox_inches='tight'); plt.close()

def fig_pn(df3, path):
    df = df3.sort_values('p_over_n')
    fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.2))

    a = ax[0]
    a.plot(df.p_over_n, df.Tn_mb, 'o-', lw=1.6, ms=6, label='$T_n^{MB}$')
    a.plot(df.p_over_n, df.crit_mb, 's--', lw=1.2, alpha=.7, label='MB Bootstrap 临界值')
    a.set(xlabel='$p/n$', ylabel='值', title='MB Bootstrap')
    a.legend(); a.grid(alpha=.3)

    a = ax[1]
    a.plot(df.p_over_n, df.Tn_xue, 'o-', lw=1.6, ms=6, color='C2', label='$T_n^{Xue}$')
    a.plot(df.p_over_n, df.crit_xue, 's--', lw=1.2, alpha=.7, color='C3',
            label='$\\tau_\\alpha$ (Gumbel 0.95 分位)')
    a.set(xlabel='$p/n$', ylabel='值', title='Xue 渐近')
    a.legend(); a.grid(alpha=.3)

    a = ax[2]
    a.semilogy(df.p_over_n, np.maximum(df.pval_mb, 1e-300), 'o-', lw=1.6, ms=6, label='MB $p$-value')
    a.semilogy(df.p_over_n, np.maximum(df.pval_xue, 1e-300), 's-', lw=1.6, ms=6, label='Xue $p$-value')
    a.axhline(.05, color='r', ls=':', label='$\\alpha=0.05$')
    a.set(xlabel='$p/n$', ylabel='$p$-value (log)', title='$p$-value 比较')
    a.legend(); a.grid(alpha=.3, which='both')

    plt.tight_layout(); plt.savefig(path, dpi=130); plt.close()

def fig_compare(df1, path):
    r = df1.iloc[0]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    methods = ['MB Bootstrap', 'Xue Gumbel']

    a = ax[0]; x = np.arange(2); w = .35
    a.bar(x-w/2, [r.Tn_mb, r.Tn_xue], w, label='$T_n$')
    a.bar(x+w/2, [r.crit_mb, r.crit_xue], w, label='临界值')
    a.set_xticks(x); a.set_xticklabels(methods)
    a.set_title('$T_n$ vs 临界值'); a.legend(); a.grid(alpha=.25)

    a = ax[1]
    a.bar(methods, [max(r.pval_mb,1e-300), max(r.pval_xue,1e-300)], color=['C0','C2'])
    a.axhline(.05, color='r', ls=':', label='$\\alpha=0.05$')
    a.set_yscale('log'); a.set_ylabel('p-value (log)'); a.set_title('p 值对比')
    a.legend(); a.grid(alpha=.25, which='both')

    plt.tight_layout(); plt.savefig(path, dpi=130); plt.close()

def fig_corr_heatmap(data, path):
    """日内残差相关结构可视化，已去除横截面市场均值。"""
    Y = data['Y_std']                   # (n,p,M)
    n, p, M = Y.shape
    Y_res = Y - Y.mean(axis=1, keepdims=True)
    Y_mean_t = Y_res.mean(axis=2)       # (n, p) — 每股每日残差收益
    C = np.corrcoef(Y_mean_t.T)         # (p, p)
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    im = ax.imshow(C, cmap='RdBu_r', vmin=-1, vmax=1)
    ax.set_title(f'股票残差相关矩阵 (去除市场均值, p={p})')
    plt.colorbar(im, ax=ax, fraction=.046)
    plt.tight_layout(); plt.savefig(path, dpi=130); plt.close()

def generate_all_outputs(data, df1, df3):
    os.makedirs(OUT, exist_ok=True)
    tex_exp1(df1, f'{OUT}/exp1_table.tex')
    tex_exp3(df3, f'{OUT}/exp3_table.tex')
    fig_smooth(data,    f'{OUT}/fig_smooth.png')
    fig_compare(df1,    f'{OUT}/fig_compare.png')
    fig_pn(df3,         f'{OUT}/fig_pn.png')
    fig_corr_heatmap(data, f'{OUT}/fig_corr.png')
    print(f'>>> 全部输出在 {OUT}/')