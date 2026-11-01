"""Actual subject-level HAR figures; Python only, no test/bootstrap calls.

Figure contract: two representative records display all six original channels;
the complete cross-block overview describes the tested processes by physical
unit family; all prespecified subject analyses and methods retain their p/status.
These are quantitative grids, followed by a single quantitative result panel.
"""
from __future__ import annotations

import argparse
import hashlib
import html
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
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _array_hash(value):
    value = np.ascontiguousarray(value)
    digest = hashlib.sha256(str(value.shape).encode()+value.dtype.str.encode())
    digest.update(value.data)
    return digest.hexdigest()


def build(root, result_dir):
    root, result_dir = Path(root), Path(result_dir)
    output = result_dir/'figures'
    output.mkdir(parents=True, exist_ok=True)
    qa = output/'qa'
    qa.mkdir(exist_ok=True)
    for name in ('audit_panel_alignment.py', 'audit_pdf_text.py', 'audit_figure_collisions.py', 'validate_figure.py'):
        target = qa/name
        if not target.exists():
            shutil.copyfile(root/'results/empirical/har/task7_v1/figures/qa'/name, target)
    alignment = _module('task7_subject_alignment', qa/'audit_panel_alignment.py')
    pdf_text = _module('task7_subject_pdftext', qa/'audit_pdf_text.py')
    plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'DejaVu Sans'],
        'font.size': 8, 'axes.labelsize': 8, 'axes.titlesize': 8.5,
        'xtick.labelsize': 7, 'ytick.labelsize': 7.5,
        'pdf.fonttype': 42, 'svg.fonttype': 'none', 'axes.spines.top': False,
        'axes.spines.right': False, 'axes.linewidth': .6, 'legend.frameon': False})
    table = pd.read_csv(result_dir/'results.csv')
    required = {'activity_id','activity','method','s','T','critical_value','p_value','status','input_sha256'}
    if not required.issubset(table) or set(table.activity_id)!=set(range(7)) or len(table)!=28:
        raise ValueError('Complete six primary activities and the separate aggregate, four methods each, required')
    labels = {1:'Walking',2:'Walking upstairs',3:'Walking downstairs',4:'Sitting',5:'Standing',6:'Laying'}
    channels = ['Body acc X','Body acc Y','Body acc Z','Gyro X','Gyro Y','Gyro Z']
    activities = {}
    for activity in range(1,7):
        path = result_dir/f'activity_{activity:02d}'
        Y = np.load(path/'Y.npy')
        selected = pd.read_csv(path/'selected_windows.csv')
        if Y.ndim!=3 or Y.shape[1:]!=(6,128) or len(selected)!=len(Y) or selected.subject_id.duplicated().any():
            raise ValueError('Subject curve shape or identity is invalid')
        expected = table.loc[table.activity_id.eq(activity),'input_sha256'].unique()
        if len(expected)!=1 or _array_hash(Y)!=expected[0]:
            raise ValueError('Plot input differs from the shared statistical input')
        activities[activity] = (Y,selected)
    figures = []

    def save(fig, name, title, axes=None):
        fig.canvas.draw()
        alignment.require_matplotlib_panel_alignment(fig,
            axes=axes, json_out=output/f'{name}.alignment.json',
            overlay_svg=output/f'{name}.alignment.svg', tolerance_pt=1.5,
            gutter_tolerance_pt=1.5, strict=True)
        fig.savefig(output/f'{name}.pdf')
        fig.savefig(output/f'{name}.svg')
        fig.savefig(output/f'{name}.png', dpi=600)
        text = pdf_text.audit_pdf((output/f'{name}.pdf').read_bytes(), minimum_pt=5)
        (output/f'{name}.pdf-text.json').write_text(json.dumps(text,indent=2),encoding='utf-8')
        if not text['auditable'] or text['below_minimum_count']:
            raise RuntimeError(name+': PDF glyph floor failed')
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        # Optional local PDF runtime is isolated from the scientific plotting process.
        deps = os.environ.get('TASK7_PDF_DEPS', str(root/'paper/task6_simulation/.qa_deps'))
        code = 'import sys,runpy;sys.path.insert(0,sys.argv[1]);sys.argv=sys.argv[2:];runpy.run_path(sys.argv[0],run_name="__main__")'
        done = subprocess.run([sys.executable,'-c',code,deps,str(qa/'audit_figure_collisions.py'),
            str(output/f'{name}.pdf'),'--json-out',str(output/f'{name}.collision.json')],
            env=env,capture_output=True,text=True,encoding='utf-8')
        (output/f'{name}.collision.log').write_text(done.stdout+done.stderr,encoding='utf-8')
        if done.returncode:
            raise RuntimeError(name+': collision audit blocked: '+done.stdout+done.stderr)
        figures.append((name,title))
        plt.close(fig)

    # Selection is fixed by subject ID and source order, not amplitude or p value.
    xyz_colors = ['#0072B2','#D55E00','#777777']
    for number, ids, group_title in ((1,(1,2,3),'Locomotor'),(2,(4,5,6),'Postural')):
        fig,axes = plt.subplots(3,2,figsize=(7.0866,6.9))
        fig.subplots_adjust(left=.12,right=.97,bottom=.10,top=.79,hspace=.70,wspace=.40)
        rows = []
        for row,activity in enumerate(ids):
            Y, selected = activities[activity]
            indices = np.flatnonzero(selected.subject_id.to_numpy()==1)
            if len(indices)!=1:
                raise ValueError('Prespecified subject 1 must have one selected curve in each activity')
            record = Y[indices[0]]
            provenance = selected.iloc[indices[0]].to_dict()
            for t in range(128):
                rows.append(dict(activity_id=activity,activity=labels[activity],subject_id=1,
                    time_index=t,time_seconds=t/50,**{f'channel_{j}':record[j,t] for j in range(6)},
                    split=provenance['split'],source_row=provenance['source_row']))
            for col,(offset,unit,sensor) in enumerate(((0,'g','Body acceleration'),(3,'rad/s','Angular velocity'))):
                ax=axes[row,col]
                for axis_index,(color,style) in enumerate(zip(xyz_colors,('-','--',':'))):
                    ax.plot(np.arange(128)/50,record[offset+axis_index],color=color,ls=style,lw=.9,label='XYZ'[axis_index])
                ax.set(xlim=(0,127/50),xlabel='Within-window time (s)',ylabel=f'{sensor} ({unit})')
                ax.set_title(f'{chr(97+row*2+col)}  {labels[activity]}',loc='left',fontweight='bold',pad=8)
        handles,legend_labels=axes[0,0].get_legend_handles_labels()
        fig.legend(handles,legend_labels,loc='upper right',bbox_to_anchor=(.97,.985),ncol=3,fontsize=8)
        fig.suptitle(f'{group_title} activities: subject 1',x=.12,y=.98,ha='left',fontsize=11)
        fig.text(.12,.91,'First complete source window for each activity; native 128-point signals',fontsize=8)
        fig.text(.12,.87,'No added per-curve transforms or amplitude standardization',fontsize=8)
        pd.DataFrame(rows).to_csv(output/f'fig{number:02d}_source.csv',index=False)
        save(fig,f'fig{number:02d}_{group_title.lower()}_curves',f'受试者1的{group_title}三活动完整六通道曲线')

    # Unit families retain distinct physical scales; no per-cell normalization.
    all_blocks=[]
    for activity,(Y,selected) in activities.items():
        residual=Y-Y.mean(axis=0,keepdims=True)
        for j in range(6):
            for k in range(j+1,6):
                cov=residual[:,j,:].T@residual[:,k,:]/(len(Y)-1)
                family='AA' if k<3 else ('GG' if j>=3 else 'AG')
                all_blocks.append(dict(activity_id=activity,activity=labels[activity],channel_j=channels[j],
                    channel_k=channels[k],j=j,k=k,family=family,max_abs_covariance=float(np.abs(cov).max()),n=len(Y)))
    blocks=pd.DataFrame(all_blocks)
    blocks.to_csv(output/'fig03_source.csv',index=False)
    fig,axes=plt.subplots(3,1,figsize=(7.0866,8.3))
    fig.subplots_adjust(left=.26,right=.84,bottom=.09,top=.81,hspace=.78)
    for row,(family,unit,title) in enumerate((('AA','g²','Body acceleration / body acceleration'),
        ('GG','rad²/s²','Angular velocity / angular velocity'),('AG','g·rad/s','Body acceleration / angular velocity'))):
        ax=axes[row]
        subset=blocks.loc[blocks.family.eq(family)]
        pairs=subset[['j','k']].drop_duplicates().itertuples(index=False,name=None)
        pairs=list(pairs)
        values=np.array([[subset.loc[subset.activity_id.eq(a)&subset.j.eq(j)&subset.k.eq(k),'max_abs_covariance'].iloc[0]
            for j,k in pairs] for a in range(1,7)])
        short=lambda j: ('a' if j<3 else 'w')+'XYZ'[j%3]
        image=ax.imshow(values,aspect='auto',cmap='Blues',vmin=0,vmax=float(values.max()),interpolation='nearest')
        ax.set_yticks(np.arange(6),[labels[a] for a in range(1,7)])
        ax.set_xticks(np.arange(len(pairs)),[short(j)+'/'+short(k) for j,k in pairs])
        ax.set_title(f'{chr(97+row)}  {title}',loc='left',fontweight='bold',pad=9)
        ax.set_xlabel('Channel pair: a = body acceleration; w = angular velocity')
        position=ax.get_position()
        cax=fig.add_axes([.875,position.y0,.02,position.height])
        bar=fig.colorbar(image,cax=cax)
        bar.set_label('Maximum |covariance| ('+unit+')',fontsize=8)
        bar.ax.tick_params(labelsize=7)
    fig.suptitle('Descriptive cross-channel covariance by activity',x=.08,y=.98,ha='left',fontsize=11)
    fig.text(.08,.93,'One first source window per subject; all 15 full double-time cross blocks',fontsize=8)
    fig.text(.08,.89,'Three physical-unit families use separate color scales; no local significance claim',fontsize=8)
    save(fig,'fig03_cross_covariance','六活动全部跨通道样本协方差，按物理单位分组',axes=list(axes))

    # All six primary activities and the separately identified aggregate are retained.
    styles=[('#0072B2','o','Ours-v1.1'),('#D55E00','s','Xue cross s5 (primary)'),
            ('#777777','^','Xue cross s11'),('#CC79A7','D','Xue cross s21')]
    order=list(range(1,7))+[0]
    table.to_csv(output/'fig04_source.csv',index=False)
    fig,ax=plt.subplots(figsize=(7.0866,6.5))
    fig.subplots_adjust(left=.30,right=.97,bottom=.13,top=.80)
    ax.axvline(.05,ls='--',color='#888888',lw=.8)
    ax.axhline(5.5,color='#BBBBBB',lw=.8,ls=':')
    for group,activity in enumerate(order):
        for index,(color,marker,display) in enumerate(styles):
            query=table.activity_id.eq(activity)
            query &= table.s.isna() if index==0 else table.s.eq((5,11,21)[index-1])
            records=table.loc[query]
            if len(records)!=1:
                raise ValueError('Each result group requires exactly four explicit method outcomes')
            record=records.iloc[0];y=group+(index-1.5)*.14
            if record.status=='ok' and pd.notna(record.p_value):
                ax.scatter(record.p_value,y,color=color,marker=marker,s=24,zorder=3)
            else:
                ax.text(.35,y,'Failed: '+str(record.failure_reason),fontsize=7,va='center',color=color)
    ax.set_yticks(range(7),[labels[a] for a in range(1,7)]+['Static subject mean\n(separate aggregate)'])
    ax.set(xlim=(-.015,1.02),ylim=(6.5,-.5),xlabel='Unadjusted p value (linear scale)')
    ax.set_xticks([0,.05,.25,.5,.75,1])
    handles=[Line2D([],[],ls='none',color=c,marker=m,label=label,ms=4) for c,m,label in styles]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.54,.975),ncol=2,fontsize=8)
    fig.text(.08,.86,'One prespecified test per group/method; dashed line: nominal 0.05',fontsize=8)
    fig.text(.08,.82,'Shared people across groups; no simultaneous 5% error guarantee',fontsize=8)
    save(fig,'fig04_subject_p_values','六活动与单列静态平均过程的四方法p值及状态')

    captions='''# 受试者层面HAR论文候选图图注

本套图读取实际受试者分析数组和全部方法结果，不重新调用检验或bootstrap。六个单活动分别固定每真实受试者在官方源文件顺序中的首条完整128点窗口；跨活动包含同一批受试者，结果不是独立重复。活动名和物理单位来自官方随包说明；加速度为去重力后的body acceleration（g），陀螺仪为angular velocity（rad/s），采样率50 Hz。窗内最后采样点为127/50=2.54 s，128个采样对应官方2.56 s窗口，图中不补入未观察的终点。

图1｜固定受试者1的三个动态活动原生信号。三行依次Walking、Walking upstairs、Walking downstairs；左列为body acceleration的X/Y/Z，右列为angular velocity的X/Y/Z。图2使用相同预定选择，三行依次Sitting、Standing、Laying。所有六通道和128个采样均保留，未根据幅度、显著性或p值选择示例，未新增去均值、平滑、标准化或插值。XYZ的颜色和线型跨图一致；不同物理单位及不同活动的纵轴范围分别显示。每面板为一条实际受试者记录实例，不表示总体均值，无抽样误差条。

图3｜六个活动的完整跨通道样本协方差概览。每组使用与实际检验完全一致且哈希核对的(n_subject,6,128)输入，沿受试者轴估计均值，分母n_subject−1；每个色块是对应j<k完整双时间协方差块的max|Γhat_jk|。全部15个通道对分为3个acc/acc、3个gyro/gyro与9个acc/gyro，三行分别使用g²、rad²/s²、g·rad/s及独立色标；不能跨单位比较颜色或大小解释生理耦合强弱，没有逐格归一化或数据筛选。a/w分别代表body acceleration/angular velocity；这是描述性统计，不把全局拒绝后最大坐标称为局部显著，无局部置信区间。

图4｜全部预定受试者组的四方法原始p值。前六行是六个真实活动，第七行单列由静态活动4/5/6全部窗口构成的受试者平均过程，与一人一条活动窗口的对象不同。本文v1.1使用B=500原始独立正态乘子，Xue-1S-EV-cross-zero固定s5主对照及s11/s21敏感性设置；四法对每组使用完全相同Y，精确统计量、各自临界值、p、判决及失败状态保存在fig04_source.csv，任何失败不会画为p=0。虚线为名义.05，不新增全表或多s校正；本图无独立二项区间，也不比较不同方法T的尺度。小p不代表更高功效或方法更正确，静态活动标签不确立真H0，不拒绝也不证明通道独立。独立受试者样本数有限，bootstrap及受限cross EV的小样本近似校准未由本数据或Task5大样本模拟证明；跨活动同人以及多s使全表不具自动统一5%错误率保证。
'''
    (result_dir/'FIGURE_CAPTIONS_ZH.md').write_text(captions,encoding='utf-8')
    sections=[]
    for name,title in figures:
        sections.append(f'<section><h2>{html.escape(title)}</h2><img src="figures/{name}.png" alt="{html.escape(title)}"><p><a href="figures/{name}.pdf">PDF</a> · <a href="figures/{name}.svg">SVG</a></p></section>')
    (result_dir/'FIGURE_GALLERY.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>HAR受试者图册</title><style>body{font-family:Arial,sans-serif;max-width:1100px;margin:35px auto;line-height:1.6}img{max-width:100%;height:auto}pre{white-space:pre-wrap}section{margin:45px 0}</style><h1>HAR受试者层面分析候选图</h1><pre>'+html.escape(captions)+'</pre>'+''.join(sections)+'</html>',encoding='utf-8')
    env=os.environ.copy();env['PYTHONIOENCODING']='utf-8'
    source=subprocess.run([sys.executable,str(qa/'validate_figure.py'),str(Path(__file__)),'--json'],
        capture_output=True,text=True,encoding='utf-8',env=env)
    (output/'source_preflight.json').write_text(source.stdout,encoding='utf-8')
    if source.returncode:
        raise RuntimeError('Figure source preflight blocked: '+source.stdout+source.stderr)
    rows=[]
    for name,title in figures:
        a=json.loads((output/f'{name}.alignment.json').read_text(encoding='utf-8'))
        p=json.loads((output/f'{name}.pdf-text.json').read_text(encoding='utf-8'))
        c=json.loads((output/f'{name}.collision.json').read_text(encoding='utf-8'))
        rows.append(f"| {name} | {a['verdict']} | {p['minimum_found_pt']} pt | {c['verdict']} | {c['summary']['fail']} / {c['summary']['warn']} |")
    validation='''# Subject-level HAR figure validation

Python/matplotlib exclusively. The first two quantitative grids display fixed subject 1 without selection by amplitude or outcome, across all six activities and channels. The third quantitative grid displays all 90 cross-block summaries (six activities × fifteen j<k pairs), partitioned by physical-unit family with independent color scales. The final quantitative panel retains all 28 outcomes including failures and explicitly separates the static subject aggregate. No test/bootstrap is called by this script.

Publication width 180 mm; 600 dpi PNG plus PDF/SVG with editable text and embedded TrueType. Minimum rendered glyph is at least 5 pt. Multi-panel final plot areas are measured with the strict 1.5 pt alignment gate; final PDFs are audited for collisions without threshold relaxation. Single-panel alignment is not applicable. Complete data, source rows, chosen subject identity and outcome tables accompany the figures.

| Figure | Alignment | Minimum glyph | Collision | FAIL / WARN |
|---|---|---|---|---|
'''+ '\n'.join(rows)+'''

Source-data mapping: actual Y.npy rows map directly to selected_windows.csv subject_id and source_row; the Y hash is checked against every group's method input. First/second figure selection is fixed subject_id=1 and the already prespecified first source window. The native channel order is body acceleration XYZ followed by angular velocity XYZ; no extra filtering/scaling is introduced. Covariance uses the residual from each activity's subject mean with n−1 denominator; units are preserved. P/status rows come directly from completed results.csv. No stochastic aggregate uncertainty is invented: representative curves are single records, covariance maxima descriptive, and p values single prespecified outcomes.

Reviewed preflight warnings may include PNG rather than TIFF (the task explicitly requests PNG plus vector formats), plus heuristics around seed/mean that do not imply missing uncertainty in these defined descriptive figures. Biological units are subjects, not overlapping windows. Small-sample calibration and cross-subset EV validity remain limitations; groups share people, and multi-s results are not a familywise guarantee. Static labels do not establish a true null. Figures do not by themselves claim local significance, causal coupling or a difference between activities.

Rendered visual review is recorded by the responsible figure reviewer after opening every final PNG; automated checks alone do not imply aesthetic or scientific approval.
'''
    review_path=output/'visual_review.json'
    if review_path.exists():
        review=json.loads(review_path.read_text(encoding='utf-8'))
        current={name:hashlib.sha256((output/f'{name}.png').read_bytes()).hexdigest() for name,title in figures}
        if current==review['png_sha256']:
            validation+='\n## Recorded final-image review\n\nAll current PNG hashes match the images independently opened and reviewed at final composition and panel level. No clipping, label/data overlap, misleading shared physical-unit scale or omitted activity/method was observed.\n\n| Figure/panel | Evidence role | Uncertainty | Replicate unit | Labels/scales/clearance | Review |\n|---|---|---|---|---|---|\n'
            validation+='\n'.join('| '+' | '.join(row)+' |' for row in review['panel_review'])+'\n'
        else:
            validation+='\nVisual review record does not match the current PNG hashes; a fresh visual review is required.\n'
    (result_dir/'FIGURE_VALIDATION.md').write_text(validation,encoding='utf-8')
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--results',default='results/empirical/har/task7_subject_v2')
    args=parser.parse_args()
    project=Path(__file__).resolve().parents[1]
    print(build(project,project/args.results))
