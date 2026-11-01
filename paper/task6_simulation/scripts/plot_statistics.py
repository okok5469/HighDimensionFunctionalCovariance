"""Deterministic figures from the audited display layer; no tests or simulation run."""
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
sys.path.insert(0, str(Path(__file__).parent / 'qa'))
from audit_panel_alignment import require_matplotlib_panel_alignment


def figure_plan():
    return dict(fig01_confirm_size=20, fig02_confirm_power=60,
                fig03_paired_differences=27, figS01_all_confirm_pairs=45)


def style():
    plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['DejaVu Sans'], 'font.size': 8,
                         'axes.titlesize': 9, 'axes.labelsize': 8,
                         'pdf.fonttype': 42, 'svg.fonttype': 'none',
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'legend.frameon': False, 'lines.linewidth': 1})
    return {'ours': ('#0072B2', 'o', '-', 'Proposed'),
            'xue_s5': ('#D55E00', 's', '--', 'Xue s5 (primary)'),
            'xue_s11': ('#666666', '^', ':', 'Xue s11'),
            'xue_s21': ('#CC79A7', 'D', '-.', 'Xue s21')}


def save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig, json_out=str(path)+'.alignment.json', strict=True)
    fig.savefig(str(path)+'.pdf', facecolor='white')
    fig.savefig(str(path)+'.svg', facecolor='white')
    fig.savefig(str(path)+'.png', dpi=360, facecolor='white')
    plt.close(fig)


def legend(fig, styles, y=.985):
    handles = [Line2D([], [], color=c, marker=m, linestyle=l, label=name,
                      markersize=4) for c,m,l,name in styles.values()]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.52,y),
               ncol=2, fontsize=8, columnspacing=1.4)


def title(model, n, p):
    return f'{model}: n={n}, p={p}'


def power_panels(df, cells, styles, path, exploratory=False):
    cols = 2
    rows = (len(cells)+1)//2
    fig, axes = plt.subplots(rows, cols, figsize=(7.05, 1.95*rows+0.95), squeeze=False)
    fig.subplots_adjust(left=.105, right=.98, bottom=max(.11,.60/fig.get_figheight()), top=1-.95/fig.get_figheight(),
                        hspace=.65, wspace=.30)
    count = 0
    for i,(model,n,p) in enumerate(cells):
        ax = axes.flat[i]
        ax.set_title(f'{chr(97+i)}  '+title(model,n,p), loc='left', pad=7)
        d = df[(df.model==model)&(df.n==n)&(df.p==p)&(df.tau>0)]
        for j,(method,(c,m,l,_)) in enumerate(styles.items()):
            sub = d[d.method==method].sort_values('tau')
            x = sub.tau.to_numpy()+(j-1.5)*.003
            y = 100*sub.rate.to_numpy()
            err = 100*np.array([sub.rate-sub.ci_low, sub.ci_high-sub.rate])
            ax.errorbar(x,y,yerr=err,color=c,marker=m,linestyle=l,ms=3.5,
                        capsize=1.4,elinewidth=.7)
            count += len(sub)
        ax.set(xlim=(.12,.63), ylim=(-3,104), xlabel=r'Signal peak $\tau$',
               ylabel='Rejection rate (%)', xticks=([.15,.30,.45,.60] if exploratory else [.15,.30,.60]))
        ax.set_yticks([0,25,50,75,100]); ax.grid(axis='y', alpha=.14)
    for ax in list(axes.flat)[len(cells):]:
        ax.remove()
    legend(fig, styles)
    save(fig,path)
    return count


def size_plot(df, styles, path):
    cells = list(df[['model','n','p']].drop_duplicates().itertuples(index=False,name=None))
    cells.sort(key=lambda x: ({'M1':0,'M2':1,'coherent':2,'flat':3,'fast':4}[x[0]],x[1],x[2]))
    fig, ax = plt.subplots(figsize=(7.05, max(3.,.9+len(cells)*.9)))
    fig.subplots_adjust(left=.30,right=.97,bottom=max(.13,.55/fig.get_figheight()),top=1-.65/fig.get_figheight())
    labels=[]; count=0
    ax.axvspan(3,7,color='#E7E7E7',zorder=0)
    ax.axvline(5,color='#888888',ls='--',lw=.8)
    for i,(model,n,p) in enumerate(cells):
        d=df[(df.model==model)&(df.n==n)&(df.p==p)]
        labels.append(title(model,n,p))
        for j,(method,(c,m,l,_)) in enumerate(styles.items()):
            row=d[d.method==method].iloc[0]
            ax.errorbar(row.rate*100,i+(j-1.5)*.16,
                        xerr=np.array([[row.rate-row.ci_low],[row.ci_high-row.rate]])*100,
                        fmt=m,color=c,ms=4,capsize=2,lw=.8)
            count+=1
    ax.set_yticks(range(len(cells)),labels)
    ax.invert_yaxis(); ax.set_xlabel('Null rejection rate (%) with pointwise CP95 interval')
    ax.set_xlim(0,max(10,df.ci_high.max()*100+1)); legend(fig,styles)
    save(fig,path)
    return count


def paired_plot(df,cells,styles,path):
    fig, axes = plt.subplots(len(cells),1,figsize=(7.05, .7+len(cells)*2.03),squeeze=False)
    fig.subplots_adjust(left=.18,right=.98,top=1-.57/fig.get_figheight(),bottom=.065,
                        hspace=.58)
    total=0
    for i,(model,n,p) in enumerate(cells):
        ax=axes.flat[i]; labels=[]
        ax.axvline(0,color='#888888',lw=.8)
        ax.axvline(-5,color='#AAAAAA',ls=':',lw=.8)
        sub=df[(df.model==model)&(df.n==n)&(df.p==p)].sort_values(['tau','comparator'])
        # Stable method order keeps the primary s5 first at each real tau.
        sub=sub.assign(order=sub.comparator.map({'xue_s5':0,'xue_s11':1,'xue_s21':2})).sort_values(['tau','order'])
        for j,row in enumerate(sub.itertuples()):
            c,m,_,_=styles[row.comparator]
            accepted=row.ours_level_status=='near_nominal' and row.comparator_level_status=='near_nominal'
            ax.errorbar(row.difference*100,j,
                        xerr=np.array([[row.difference-row.adjusted_ci_low],
                                       [row.adjusted_ci_high-row.difference]])*100,
                        fmt=m,ms=4,color=c,mfc=(c if accepted else 'white'),capsize=2,lw=.9)
            labels.append(f'{row.tau:.2f} / {row.comparator.replace("xue_", "")}')
        total+=len(sub)
        ax.set(yticks=range(len(labels)),yticklabels=labels,xlim=(-48,103),ylim=(-.6,8.6))
        ax.invert_yaxis(); ax.set_title(f'{chr(97+i)}  '+title(model,n,p),loc='left',pad=6)
        ax.grid(axis='x',alpha=.12)
        ax.set_xlabel('Proposed minus comparator (percentage points)')
        ax.set_ylabel(r'$\tau$ / comparator')
    # Points use method identity; the hollow/filled distinction carries calibration.
    fig.text(.5, .99, 'Filled: both H0 near nominal; open: at least one unresolved',
             ha='center', va='top',fontsize=8)
    save(fig,path)
    return total


def build(root, methods, paired):
    styles=style()
    main=root/'figures/main'; supp=root/'figures/supplement'
    confirm=methods[methods.phase=='confirm']; cp=paired[paired.phase=='confirm']
    cells=[('M1',800,20),('M2',800,20),('coherent',400,20),('coherent',800,20),('coherent',800,50)]
    coverage={}
    coverage['fig01_confirm_size']=size_plot(confirm[confirm.tau==0],styles,main/'fig01_confirm_size')
    coverage['fig02_confirm_power']=power_panels(confirm,cells,styles,main/'fig02_confirm_power')
    coverage['fig03_paired_differences']=paired_plot(cp,[cells[0],cells[1],cells[-1]],styles,main/'fig03_paired_differences')
    coverage['figS01_all_confirm_pairs']=paired_plot(cp,cells,styles,supp/'figS01_all_confirm_pairs')
    assert coverage==figure_plan(),coverage
    pilot=methods[methods.phase=='pilot']
    for model in ('M1','M2','coherent','local','fast'):
        d=pilot[(pilot.model==model)&(pilot.tau>0)]
        pcells=list(d[['model','n','p']].drop_duplicates().itertuples(index=False,name=None))
        power_panels(pilot,pcells,styles,supp/f'figS_power_{model}',True)
    for model in ('M1','M2','flat','fast'):
        d=pilot[(pilot.model==model)&(pilot.tau==0)]
        size_plot(d,styles,supp/f'figS_size_{model}')
    return coverage
