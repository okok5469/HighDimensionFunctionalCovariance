"""HAR figures from actual inputs and completed diagnostics; no test reruns.

Figure contract: raw six-channel window describes the supplied measurements;
cross-block maxima describe the exact diagnostic input; nominal p values and
resampling proportions document the historical computation, not subject inference.
Python/matplotlib only, editable PDF/SVG and 600 dpi PNG, 180 mm final width.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build(root, result_dir):
    root, result_dir = Path(root), Path(result_dir)
    output = root / 'results/empirical/har/task7_v1/figures'
    output.mkdir(parents=True, exist_ok=True)
    qa = output / 'qa'
    qa.mkdir(exist_ok=True)
    source_qa = root / 'paper/task6_simulation/scripts/qa'
    for name in ('audit_panel_alignment.py', 'audit_pdf_text.py', 'audit_figure_collisions.py', 'validate_figure.py'):
        if not (qa / name).exists():
            shutil.copyfile(source_qa / name, qa / name)
    alignment = module_at('task7_alignment', qa / 'audit_panel_alignment.py')
    pdf_text = module_at('task7_pdftext', qa / 'audit_pdf_text.py')
    plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'DejaVu Sans'],
        'font.size': 8, 'axes.labelsize': 8, 'axes.titlesize': 9, 'xtick.labelsize': 7,
        'ytick.labelsize': 7, 'pdf.fonttype': 42, 'svg.fonttype': 'none',
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': .6})
    config = json.loads((root / 'config/empirical/task7_har.json').read_text(encoding='utf-8-sig'))
    figures = []

    def save(fig, name, title):
        fig.canvas.draw()
        alignment.require_matplotlib_panel_alignment(fig, json_out=output / f'{name}.alignment.json',
            overlay_svg=output / f'{name}.alignment.svg', tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True)
        for extension in ('pdf', 'svg', 'png'):
            fig.savefig(output / f'{name}.{extension}', dpi=600)
        text_report = pdf_text.audit_pdf((output / f'{name}.pdf').read_bytes(), minimum_pt=5)
        (output / f'{name}.pdf-text.json').write_text(json.dumps(text_report, indent=2), encoding='utf-8')
        if not text_report['auditable'] or text_report['below_minimum_count']:
            raise RuntimeError(f'{name}: PDF glyph floor failed')
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        deps = root / 'paper/task6_simulation/.qa_deps'
        env['PYTHONPATH'] = str(deps) + os.pathsep + env.get('PYTHONPATH', '')
        completed = subprocess.run([sys.executable, str(qa / 'audit_figure_collisions.py'), str(output / f'{name}.pdf'),
            '--json-out', str(output / f'{name}.collision.json'), '--overlay-pdf', str(output / f'{name}.collision.pdf')],
            env=env, capture_output=True, text=True, encoding='utf-8')
        (output / f'{name}.collision.log').write_text(completed.stdout + completed.stderr, encoding='utf-8')
        if completed.returncode:
            raise RuntimeError(f'{name}: collision QA blocked: {completed.stdout} {completed.stderr}')
        figures.append((name, title))
        plt.close(fig)

    # Fixed original window ID 0, no selection by magnitude or test outcome.
    raw = pd.read_csv(root / config['dynamic_csv'])
    example = raw.loc[raw.sample_id == 0].sort_values('time')
    if example.shape != (128, 8) or not np.array_equal(example.time, np.arange(128)):
        raise ValueError('Fixed raw example is incomplete')
    example.to_csv(output / 'fig1_source.csv', index=False)
    fig, axes = plt.subplots(3, 2, figsize=(180/25.4, 155/25.4))
    fig.subplots_adjust(left=.11, right=.97, bottom=.10, top=.88, hspace=.70, wspace=.40)
    for j, ax in enumerate(axes.flat):
        ax.plot(example.time, example[f'var_{j}'], color='#367A91', lw=1)
        ax.set(xlim=(0, 127), xlabel='Within-window index', ylabel=f'var_{j} (stored units)')
        ax.set_title(chr(97+j), loc='left', fontweight='bold', pad=8)
    fig.suptitle('Recorded dynamic window: sample_id = 0', x=.11, y=.97, ha='left', fontsize=11)
    fig.text(.11, .92, 'One 128-point window; subject, activity and physical channel units unknown', fontsize=8)
    save(fig, 'fig1_raw_window', '实际动态原始窗口：固定 sample_id=0')

    base = result_dir / 'legacy_diagnostic/dynamic_base'
    selected = pd.read_csv(base / 'selected_windows.csv')
    pool = np.load(root / config['processed_dir'] / 'Y_pool_dynamic.npy', mmap_mode='r')
    Y = pool[selected.pool_index.to_numpy(), :, :]
    records = json.loads((base / 'result.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256(str(Y.shape).encode()+Y.dtype.str.encode())
    digest.update(np.ascontiguousarray(Y).data)
    if digest.hexdigest() != records[0]['input_sha256']:
        raise ValueError('Figure input differs from tested array')
    residual = Y-Y.mean(axis=0, keepdims=True)
    blocks = []
    for j in range(6):
        for k in range(j+1, 6):
            cov = residual[:,j,:].T @ residual[:,k,:] / (len(Y)-1)
            blocks.append({'channel_j': f'var_{j}', 'channel_k': f'var_{k}', 'max_abs_covariance': float(np.abs(cov).max())})
    blocks = pd.DataFrame(blocks)
    blocks.to_csv(output / 'fig2_source.csv', index=False)
    fig, ax = plt.subplots(figsize=(180/25.4, 125/25.4))
    fig.subplots_adjust(left=.20, right=.95, bottom=.13, top=.82)
    positions = np.arange(len(blocks))
    ax.hlines(positions, 0, blocks.max_abs_covariance, color='#ABC5CD', lw=1.5)
    ax.scatter(blocks.max_abs_covariance, positions, color='#367A91', s=22, zorder=3)
    ax.set_yticks(positions, blocks.channel_j.str.cat(blocks.channel_k, sep=' / '))
    ax.invert_yaxis()
    ax.set(xlabel='Maximum absolute cross-block sample covariance', ylabel='Channel pair', xlim=(0, None))
    fig.suptitle('Descriptive covariance of the historical diagnostic input', x=.20, y=.97, ha='left', fontsize=10)
    fig.text(.20, .91, '200 derived windows; M = 48; 15 complete cross-channel blocks', fontsize=8)
    fig.text(.20, .87, 'Historical transform and pool standardization; no local significance claim', fontsize=8)
    save(fig, 'fig2_cross_covariance', '历史诊断输入的十五个跨通道协方差块')

    table = pd.DataFrame(records)
    table['display_method'] = ['Ours-v1.1' if r['s'] is None else f"Xue cross, s={r['s']}" for r in records]
    table[['display_method','T','critical_value','p_value','reject','status','failure_reason','n','p','M','seed','B']].to_csv(output / 'fig3_source.csv', index=False)
    fig, ax = plt.subplots(figsize=(180/25.4, 88/25.4))
    fig.subplots_adjust(left=.28, right=.96, bottom=.21, top=.74)
    for i, r in enumerate(records):
        if r['status'] == 'ok' and r['p_value'] is not None:
            ax.scatter(r['p_value'], i, color='#367A91' if i == 0 else '#8F8798', s=45, zorder=3)
        else:
            ax.text(.55, i, 'Failed: see source table', va='center', fontsize=8)
    ax.set_yticks(np.arange(4), table.display_method)
    ax.invert_yaxis()
    ax.set(xlim=(-.015, 1.02), ylim=(3.6, -.6), xlabel='Nominal p value (linear scale)')
    ax.axvline(.05, color='#777777', lw=.7, linestyle='--')
    ax.set_xticks([0, .05, .25, .5, .75, 1])
    fig.suptitle('Single historical window diagnostic: four methods', x=.10, y=.96, ha='left', fontsize=11)
    fig.text(.10, .87, 'Seed 42; n = 200; p = 6; M = 48; Ours B = 500; dashed line: 0.05', fontsize=8)
    fig.text(.10, .81, 'Dependent windows; nominal values do not support subject-level inference', fontsize=8)
    save(fig, 'fig3_nominal_p_values', '单次历史诊断四方法名义 p 值与完整状态表')

    summary = pd.read_csv(result_dir / 'summary.csv')
    grid = summary.loc[summary.experiment == 'pn_grid'].copy()
    if len(grid) != 64 or not (grid.analyses == 50).all():
        raise ValueError('Full historical 16-cell grid summary required')
    grid.to_csv(output / 'fig4_source.csv', index=False)
    fig, axes = plt.subplots(2, 2, figsize=(180/25.4, 142/25.4), sharex=True, sharey=True)
    fig.subplots_adjust(left=.12, right=.97, bottom=.22, top=.80, wspace=.35, hspace=.55)
    colors = ['#367A91', '#8F8798', '#B18F6A', '#757575']
    markers = ['o', 's', '^', 'x']
    for panel, (p, ax) in enumerate(zip((3,4,5,6), axes.flat)):
        for method_index, s in enumerate((None,5,11,21)):
            mask = grid.s.isna() if s is None else grid.s.eq(s)
            rows = grid.loc[mask & grid.p.eq(p)].sort_values('n')
            label = 'Ours-v1.1' if s is None else f'Xue cross, s={s}'
            ax.plot(rows.n, rows.rejection_proportion, label=label, color=colors[method_index],
                marker=markers[method_index], lw=1.0, ms=4, linestyle=['-','--','-.',':'][method_index])
        ax.set(xlim=(40,210), ylim=(0,1.05), xlabel='Derived windows per draw', ylabel='Rejection proportion')
        ax.set_xticks([50,100,150,200])
        ax.set_yticks([0,.25,.5,.75,1])
        ax.set_title(f'{chr(97+panel)}   p = {p}', loc='left', fontweight='bold', pad=8)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(.52,.015), ncol=2, frameon=False, fontsize=8)
    fig.suptitle('Historical window resampling: the complete n/p grid', x=.12, y=.97, ha='left', fontsize=11)
    fig.text(.12,.91,'50 draws per cell; same dependent pool; Ours B = 500 per draw',fontsize=8)
    fig.text(.12,.86,'Descriptive rejection proportions, not type-I error or power',fontsize=8)
    save(fig,'fig4_grid_diagnostic','历史窗口重抽样的完整 n/p 网格')

    captions = '''# HAR 论文候选图图注

全部图像属于数据描述或历史窗口流程数值诊断；真实受试者及活动映射尚未恢复，因此不构成受试者层面实证图。静态文件未恢复，不绘制静态协方差。时间为窗口内索引，不标为秒；var_0–var_5 为文件列名，不推断传感器物理名称。

图1｜固定原始窗口的六通道记录。读取动态原始 CSV 中 sample_id=0 的完整 128 点；按固定 ID 选择，不依赖统计量或 p 值。a–f 依次为 var_0–var_5；纵轴为文件存储尺度，物理单位未知。无聚合、插值或幅度标准化；此 ID 为窗口而非受试者。描绘全部六列、全部 128 点，无不确定性区间（单个记录实例）。

图2｜历史动态诊断输入的跨通道样本协方差。按 seed=42 从历史预处理窗口池固定抽取 n=200 个派生窗口，六通道、48 点；数组 SHA256 与实际检验输入一致。预处理为原窗口内平移后对数差分、48 点 stride=2 子窗口、q=5 Fourier 重建以及窗口池样本轴标准化。每点为 j<k 完整双时间网格协方差块的 max|Γhat_jk|，分母 n−1；展示全部 15 块，无事后选择。此图仅为描述，不提供局部显著性或置信区间；变换后尺度不可与图1原始单位直接比较。

图3｜单次历史窗口诊断的四方法名义 p 值。Ours-v1.1 与 Xue-1S-EV-cross-zero 的 s=5、11、21 使用同一输入数组；Ours B=500、seed=42。虚线为名义 0.05，判决规则 p<0.05；无新增多重比较调整。所有方法（包括失败）均列入 fig3_source.csv，附各自统计量、临界值、p、状态及失败原因；不同方法统计量尺度不直接比较。窗口彼此依赖且受试者数未知，小 p 值不代表方法功效或正确性。无区间（一次预定分析）；成功/失败完整保留。

图4｜历史窗口重抽样方案下的完整 n/p 网格拒绝比例。a–d 分别使用原列序前 p=3、4、5、6 个通道；每个 n=50、100、150、200 单元固定 50 次抽样，全部 16 单元和四种方法均展示。每个点为本次抽样方案的名义 p<0.05 比例；线仅连接同方法的离散 n。原始曲线/受试者跨重复共享，故不附独立二项置信区间，不称为第一类错误率或功效。重合曲线保留真实坐标，不作人为错位；所有精确比例、成功数和分母保存在 fig4_source.csv。Xue 方法的 cross-zero 极值校准仅作有限依据的实现对照。
'''
    (output.parent / 'FIGURE_CAPTIONS_ZH.md').write_text(captions, encoding='utf-8')
    body = ''.join(f'<section><h2>{title}</h2><img src="figures/{name}.png" alt="{title}"><p><a href="figures/{name}.pdf">PDF</a> · <a href="figures/{name}.svg">SVG</a></p></section>' for name,title in figures)
    (output.parent / 'FIGURE_GALLERY.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>HAR Task7 图册</title><style>body{font-family:Arial,sans-serif;max-width:1000px;margin:40px auto;line-height:1.6}img{width:100%;height:auto}section{margin-bottom:50px}</style><h1>HAR 数据与历史诊断候选图</h1><p>仅数据描述及依赖窗口数值诊断。受试者主分析受阻；无静态伪造核。完整图注见 FIGURE_CAPTIONS_ZH.md，精确数值及失败原因见各 source.csv。</p>'+body+'</html>', encoding='utf-8')
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    source_check = subprocess.run([sys.executable, str(qa/'validate_figure.py'), str(Path(__file__)), '--json'],
        capture_output=True, text=True, encoding='utf-8', env=env)
    (output/'source_preflight.json').write_text(source_check.stdout, encoding='utf-8')
    if source_check.returncode:
        raise RuntimeError('Plot source preflight failed: '+source_check.stdout+source_check.stderr)
    audit_rows = []
    for name, title in figures:
        layout = json.loads((output/f'{name}.alignment.json').read_text(encoding='utf-8'))
        text = json.loads((output/f'{name}.pdf-text.json').read_text(encoding='utf-8'))
        collision = json.loads((output/f'{name}.collision.json').read_text(encoding='utf-8'))
        audit_rows.append(f"| {name} | {layout['verdict']} | {text['minimum_found_pt']} pt | {collision['verdict']} ({collision['summary']['fail']} FAIL / {collision['summary']['warn']} WARN) |")
    validation = '''# HAR Figure Validation

## Contract and provenance

Python/matplotlib only. Four descriptive figures answer four separate questions: what the supplied window looks like, how the tested transformed input covaries, what the four frozen methods returned once, and how the prescribed historical resampling scheme behaves across the complete n/p grid. Figure 1 is a quantitative grid; Figures 2/3 are single quantitative panels; Figure 4 is a quantitative grid. No AI imagery, no static reconstructed data, no new tests/bootstrap calls.

Final width 180 mm; final heights 155/125/88/142 mm. PDF TrueType text and SVG editable text; PNG 600 dpi (4251 pixels wide). Input source data are fig1_source.csv–fig4_source.csv. Every channel and complete 128-point raw example is retained; all 15 cross-block pairs, four methods, and 16 n/p cells are retained. Sample_id=0 is fixed a priori. Figure 2 input is verified against the actual frozen-test array SHA256 before plotting. Biological replicate identity is unavailable. Windows must not be called people. Native sensor units, channel meanings, and activities are unknown.

## Final-render automated QA

| Figure | Alignment (1.5 pt strict) | Minimum PDF glyph | Collision audit |
|---|---|---|---|
'''+ '\n'.join(audit_rows) + '''

Single-panel alignment is NOT APPLICABLE, not an alignment pass. Every exported final PDF was collision audited after layout; no thresholds were relaxed. The alignment manifests preserve final rendered plot-area geometry. QA script copies are versioned in figures/qa and the complete reports are next to each export.

Source preflight reports no FAIL. Reviewed source WARNs: PNG is requested alongside vector PDF/SVG, so TIFF is not needed; heuristic width parser treats the expression 180/25.4 as 180 inches, while the actual final width is 180 mm; words seed/mean trigger an uncertainty heuristic, but raw examples, descriptive block maxima and a single p value have no replicate interval. Figure 4 deliberately omits binomial intervals because draws share the dependent window pool and underlying people. No uncertainty claim is made.

## Rendered visual review (2026-10-26)

All four PNGs were opened and each panel inspected, followed by the complete composition. Seven-point or larger actual PDF glyphs are readable. No labels overlap lines or one another; titles/subtitles and legend have separate margins. Full data extents are visible. Comparisons use shared scales where appropriate; original channel amplitudes are not forced onto a common scale. No local significance is implied by Figure 2; Figure 3 uses a linear p axis and supplies exact tiny p values in the source table. Its near-zero clustering is expected, not zero substitution. Figure 4 coincident curves retain their true coordinates; dash/marker styles and exact source values resolve identities without jitter.

| Panel | Unique role | Summary / uncertainty | Observation unit | Label / scale review | Result |
|---|---|---|---|---|---|
| Fig1 a | Original var_0 | raw / none: one record | window 0 | index, unknown stored units | pass |
| Fig1 b | Original var_1 | raw / none: one record | window 0 | index, unknown stored units | pass |
| Fig1 c | Original var_2 | raw / none: one record | window 0 | index, unknown stored units | pass |
| Fig1 d | Original var_3 | raw / none: one record | window 0 | index, unknown stored units | pass |
| Fig1 e | Original var_4 | raw / none: one record | window 0 | index, unknown stored units | pass |
| Fig1 f | Original var_5 | raw / none: one record | window 0 | index, unknown stored units | pass |
| Fig2 | Complete cross-block structure | max abs sample covariance / descriptive | 200 derived windows | all 15 pairs, transformed scale | pass |
| Fig3 | Complete method outcome | nominal p / single analysis | same 200 derived windows | no cross-method T comparison | pass |
| Fig4 a | n sensitivity, first 3 channels | rejection proportion / no iid interval | 50 dependent-pool draws per cell | full [0,1] y scale | pass |
| Fig4 b | n sensitivity, first 4 channels | rejection proportion / no iid interval | 50 dependent-pool draws per cell | shared full y scale | pass |
| Fig4 c | n sensitivity, first 5 channels | rejection proportion / no iid interval | 50 dependent-pool draws per cell | shared full y scale | pass |
| Fig4 d | n sensitivity, all 6 channels | rejection proportion / no iid interval | 50 dependent-pool draws per cell | shared full y scale | pass |

All four figures are candidate descriptive/diagnostic manuscript assets only. None establishes subject-level evidence, size, power, channel independence, or local significance. Main subject analyses remain blocked by the stated input metadata gaps.

Rebuild from repository root: `python -m empirical.task7_figures` after the completed diagnostic outputs exist. This command was executed successfully; it reads existing outputs and never reruns statistical tests.
'''
    (output.parent/'FIGURE_VALIDATION.md').write_text(validation, encoding='utf-8')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', default='results/empirical/har/task7_v1/har_empirical_task7_v1')
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    print(build(project, project / args.results))
