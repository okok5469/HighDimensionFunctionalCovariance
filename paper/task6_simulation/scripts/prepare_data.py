"""Read frozen summaries and rebuild the paper data layer; no simulations."""
from pathlib import Path
import hashlib
import json
import re

import numpy as np
import pandas as pd
from scipy.stats import beta


MODEL = {'m1_fourier5_peak1': 'M1', 'm2_brownian_peak1': 'M2',
         'coherent_all': 'coherent', 'spectrum_flat_b0': 'flat',
         'local_fejer': 'local', 'spectrum_fast_b4': 'fast'}


def cp(k, n, tail=.025):
    """Exact binomial interval, including endpoints."""
    return (0. if k == 0 else float(beta.ppf(tail, k, n-k+1)),
            1. if k == n else float(beta.ppf(1-tail, k+1, n-k)))


def calibration(lo, hi):
    return ('near_nominal' if lo >= .03 and hi <= .07 else
            'conservative' if hi < .03 else 'inflated' if lo > .07 else 'unresolved')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_summary(root, phase, kind):
    path = f'inputs/{phase}_{kind}.csv'
    df = pd.read_csv(root/path)
    df['source_file'] = path
    df['source_row'] = np.arange(2, len(df)+2)
    df['source_key'] = df['phase'] + ':' + df['scenario_id'] + ':' + df.get('method', df.get('comparator'))
    return df


def table_export(root, name, frame, caption):
    frame.to_csv(root/'tables'/f'{name}.csv', index=False, float_format='%.17g')
    (root/'tables'/f'{name}.md').write_text(caption+'\n\n'+frame.to_markdown(index=False)+'\n', encoding='utf-8')
    (root/'tables'/f'{name}.tex').write_text('% '+caption+'\n'+frame.to_latex(index=False, longtable=True, escape=True), encoding='utf-8')


def fixed_table(headers, rows, widths):
    """A bounded-width longtable; widths plus padding never exceed 170 mm."""
    require(sum(widths)+len(widths)*6*25.4/72.27 <= 170, 'Table wider than 170 mm')
    columns=''.join('p{'+str(w)+'mm}' for w in widths)
    head=' & '.join(headers)+r' \\'
    return '\n'.join([r'\begingroup',r'\fontsize{8.5}{11}\selectfont',r'\setlength{\tabcolsep}{3pt}',
        r'\renewcommand{\arraystretch}{1.15}',r'\begin{longtable}{'+columns+'}',r'\toprule',
        head,r'\midrule',r'\endfirsthead',r'\toprule',head,r'\midrule',r'\endhead',
        *[' & '.join(row)+r' \\' for row in rows],r'\bottomrule',r'\end{longtable}',r'\endgroup',''])


def main_presentation_tables(root, methods, design):
    """Render human-facing main tables without changing machine CSV schemas."""
    order=['ours','xue_s5','xue_s11','xue_s21']
    status={'near_nominal':'支持接近','unresolved':'未决','conservative':'明显保守','inflated':'明显膨胀'}
    for name, alternative in [('table02_confirm_size',False),('table03_confirm_power',True)]:
        frame=methods[(methods.phase=='confirm') & ((methods.tau>0) if alternative else (methods.tau==0))].sort_values(['model','n','p','tau'])
        headers=['模型 (n,p)']+(['τ'] if alternative else [])+['本文','Xue s5','Xue s11','Xue s21']
        mdrows=[]; texrows=[]
        for (model,n,p,tau), group in frame.groupby(['model','n','p','tau'],sort=False):
            mdrow=[f'{model} ({n},{p})']+([f'{tau:.2f}'] if alternative else [])
            texrow=[model+r'\newline '+f'({n},{p})']+([f'{tau:.2f}'] if alternative else [])
            for method in order:
                r=group[group.method.eq(method)].iloc[0]
                first=f'{r.rejections}/{r.valid} ({100*r.rate:.2f}%)'
                second=f'[{100*r.ci_low:.2f}, {100*r.ci_high:.2f}]'
                third=[] if alternative else [status[r.calibration]]
                mdrow.append('<br>'.join([first,second,*third]))
                texrow.append(r'\newline '.join([first.replace('%',r'\%'),second,*third]))
            mdrows.append(mdrow);texrows.append(texrow)
        caption='表3：独立确认功效。' if alternative else '表2：独立确认水平。'
        note='单元内依次为拒绝数/重复数（拒绝率%）、逐格CP95%区间（%）'+('。' if alternative else '及工作带评价。')
        md='| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'
        md+='\n'.join('| '+' | '.join(row)+' |' for row in mdrows)+'\n'
        (root/'tables'/f'{name}.md').write_text(caption+note+'\n\n'+md,encoding='utf-8')
        texheaders=['模型 $(n,p)$']+([r'$\tau$'] if alternative else [])+['本文','Xue $s=5$','Xue $s=11$','Xue $s=21$']
        widths=[27,9,29,29,29,29] if alternative else [27,31,31,31,31]
        tex='% '+caption+note+'\n'+fixed_table(texheaders,texrows,widths)
        tex+=r'\noindent{\footnotesize '+note.replace('%',r'\%')+r'}'+'\n'
        (root/'tables'/f'{name}.tex').write_text(tex,encoding='utf-8')
    headers=['模型','潜在背景','信号结构','探索形状','确认形状']
    shapes='(200,20)、(400,20)、(800,20)、(800,50)'
    rows=[['M1','五基傅里叶；权重随基序平方倒数衰减','与背景同形的跨通道协方差',shapes,'(800,20)'],
          ['M2','规范化布朗运动；63个增量','与背景同形的跨通道协方差',shapes,'(800,20)'],
          ['coherent','20维平坦谱','秩一相干信号；中心3/8',shapes,'(400,20)、(800,20)、(800,50)'],
          ['local','20维平坦谱；共享flat H0','原Fejér局部信号','(800,20)','无'],
          ['fast','20维正余弦成对快速衰减谱','原冻结fast信号','(800,20)','无']]
    caption='表1：模型与两阶段设计。全部共用M=64、噪声标准差0.05、B=500及α=0.05。'
    note='探索τ=0/0.15/0.30/0.45/0.60，确认τ=0/0.15/0.30/0.60；τ=0为H0，其他为H1；local/fast仅在anchor探索。flat H0只计一次。'
    modelmd='| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*5)+' |\n'+'\n'.join('| '+' | '.join(row)+' |' for row in rows)
    d=design.rename(columns={'phase':'阶段','h0':'H0单元','h1':'H1单元','datasets':'数据集','methods':'方法行','paired':'配对','R_H0':'H0重复','R_H1':'H1重复'}).replace({'pilot':'探索','confirm':'独立确认'})
    (root/'tables/table01_design.md').write_text(caption+'\n\n'+modelmd+'\n\n'+note+'\n\n'+d.to_markdown(index=False)+'\n',encoding='utf-8')
    tex='% '+caption+'\n'+fixed_table(headers,rows,[18,31,31,32,32])
    phaseheaders=['阶段','H0/H1单元','数据集','方法/配对','H0/H1重复']
    phaserows=[[('探索' if r.phase=='pilot' else '独立确认'),f'{r.h0}/{r.h1}',str(r.datasets),f'{r.methods}/{r.paired}',f'{r.R_H0}/{r.R_H1}'] for r in design.itertuples()]
    tex+=fixed_table(phaseheaders,phaserows,[23,30,25,32,32])
    tex+=r'\noindent{\footnotesize '+note.replace('τ',r'$\tau$')+r'}'+'\n'
    (root/'tables/table01_design.tex').write_text(tex,encoding='utf-8')


def prepare(root):
    root = Path(root)
    for directory in ('data', 'tables'):
        (root/directory).mkdir(exist_ok=True)
    manifest = json.loads((root/'source_manifest.json').read_text(encoding='utf-8'))
    for item in manifest['inputs']:
        require(hashlib.sha256((root/item['path']).read_bytes()).hexdigest() == item['sha256'],
                'Input hash mismatch: '+item['path'])
    for name in ('pilot_plan', 'confirm_plan', 'confirm_locked'):
        require(json.loads((root/'inputs'/f'{name}.json').read_text(encoding='utf-8'))['study'] == 'task5_unified_v1',
                'Incorrect study identity: '+name)
    methods = pd.concat([read_summary(root,p,'summary') for p in ('pilot','confirm')], ignore_index=True)
    paired = pd.concat([read_summary(root,p,'paired_comparisons') for p in ('pilot','confirm')], ignore_index=True)
    diagnostics = pd.concat([read_summary(root,p,'diagnostic_summary') for p in ('pilot','confirm')], ignore_index=True)
    # The names below are exact frozen spec identities, not substring-based matching.
    identities = sorted(methods.spec_id.unique())
    require(set(identities) == set(MODEL), 'Model identity mismatch')
    for df in (methods,paired,diagnostics):
        df['model'] = df.spec_id.map(MODEL)
        require(not df.source_key.duplicated().any(), 'Duplicate summary key')
    require(len(methods)==356 and len(paired)==213, 'Unexpected summary scale')
    require(set(methods.method)=={'ours','xue_s5','xue_s11','xue_s21'}, 'Method identity mismatch')
    for row in methods.itertuples():
        require(0 <= row.rejections <= row.valid and row.valid == row.completed == row.planned,
                'Invalid integer denominator: '+row.source_key)
        require(row.failed == row.missing == 0 and row.common_valid == row.valid and row.common_rejections == row.rejections,
                'Invalid completion or common-sample counts: '+row.source_key)
        lo, hi = cp(row.rejections, row.valid)
        rate = row.rejections/row.valid
        require(np.allclose([row.rate,row.common_rate,row.mcse,row.ci_low,row.ci_high],
            [rate,rate,np.sqrt(rate*(1-rate)/row.valid),lo,hi],atol=1e-12,rtol=0),
            'Method numerical mismatch: '+row.source_key)
        if row.phase == 'confirm' and row.tau == 0:
            require(row.level_status == calibration(lo,hi), 'Source calibration mismatch: '+row.source_key)
    methods['calibration'] = [calibration(r.ci_low,r.ci_high) if r.phase=='confirm' and r.tau==0
        else 'exploratory' if r.tau==0 else 'not_applicable' for r in methods.itertuples()]
    keys = ['phase','model','n','p','method']
    nulls = methods[methods.tau.eq(0)].set_index(keys)
    lookup = methods.set_index(['phase','scenario_id','method'])
    for col in ('adjusted_ci_low','adjusted_ci_high','familywise_declarations','label'):
        paired['source_'+col] = paired[col]
    fields = []
    for row in paired.itertuples():
        n = row.common_valid
        a,b,c,d = row.both_reject,row.only_a,row.only_b,row.neither
        require(all(isinstance(x,(int,np.integer)) and x>=0 for x in (a,b,c,d)) and a+b+c+d==n==row.paired_completed==row.planned,
                'Invalid paired counts: '+row.source_key)
        ours = lookup.loc[(row.phase,row.scenario_id,'ours')]
        other = lookup.loc[(row.phase,row.scenario_id,row.comparator)]
        require(a+b==ours.rejections and a+c==other.rejections, 'Paired margin mismatch: '+row.source_key)
        diff=(b-c)/n
        se=np.sqrt(((b+c)/n-diff**2)/(n-1))
        blo,bhi=cp(b,n,.05/4)
        clo,chi=cp(c,n,.05/4)
        require(np.allclose([row.difference,row.mcse,row.ci_low,row.ci_high], [diff,se,blo-chi,bhi-clo],atol=1e-12,rtol=0),
                'Paired numerical mismatch: '+row.source_key)
        source_m = row.source_familywise_declarations
        sbl,sbu=cp(b,n,.05/(4*source_m)); scl,scu=cp(c,n,.05/(4*source_m))
        require(np.allclose([row.source_adjusted_ci_low,row.source_adjusted_ci_high],[sbl-scu,sbu-scl],atol=1e-12,rtol=0),
                'Source adjusted interval mismatch: '+row.source_key)
        m = 45 if row.phase=='confirm' else 1
        lb,ub=cp(b,n,.05/(4*m)); lc,uc=cp(c,n,.05/(4*m))
        lo,hi=lb-uc,ub-lc
        direction='positive' if lo>0 else 'negative' if hi<0 else 'unresolved'
        ni='supported' if lo>-.05 else 'not_established'
        inferior='supported' if hi<-.05 else 'not_established'
        category=direction if direction!='unresolved' else 'noninferior_only' if ni=='supported' else 'unresolved'
        null_model = 'flat' if row.model in ('coherent','local') and row.phase=='pilot' else row.model
        own_null=nulls.loc[(row.phase,null_model,row.n,row.p,'ours')]
        cmp_null=nulls.loc[(row.phase,null_model,row.n,row.p,row.comparator)]
        accepted=own_null.calibration==cmp_null.calibration=='near_nominal'
        require(row.calibration_accepted == accepted, 'Source calibration scope mismatch: '+row.source_key)
        fields.append((lo,hi,m,direction,ni,inferior,category,own_null.calibration,cmp_null.calibration,accepted,
            'power_comparison_within_tolerance' if accepted else 'nominal_rejection_probability_only'))
    columns=['adjusted_ci_low','adjusted_ci_high','familywise_declarations','direction','noninferiority',
        'inferiority_beyond_margin','display_category','ours_calibration','comparator_calibration','both_calibrated','comparison_scope']
    paired[columns]=pd.DataFrame(fields,index=paired.index)
    # Independent report cross-check: every integer count and displayed CP endpoint.
    report=(root/'inputs/task5_summary_document.md').read_text(encoding='utf-8-sig')
    documented_hashes=dict(re.findall(r'\[([^\]]+)\]\([^\)]+\) \| ([0-9a-f]{64})', report))
    for item in manifest['inputs']:
        filename=Path(item['path']).name
        if filename in documented_hashes:
            require(item['sha256']==documented_hashes[filename], 'Historical report hash mismatch: '+filename)
    report_methods=[]
    for line in report.splitlines():
        matches=re.findall(r'(\d+)/(\d+)；([\d.]+)% \[([\d.]+), ([\d.]+)\]',line)
        report_methods.extend(matches)
    require(len(report_methods)==356, 'Incomplete report method tables')
    # Table ordering differs for confirmation; use the multiset of exact counts and rounded intervals.
    from collections import Counter
    expected=Counter((str(r.rejections),str(r.valid),f'{100*r.rate:.2f}',f'{100*r.ci_low:.2f}',f'{100*r.ci_high:.2f}') for r in methods.itertuples())
    require(Counter(report_methods)==expected,'Report method counts or rounded CP conflict')
    report_paired=[]
    for line in report.splitlines():
        cells=[c.strip() for c in line.strip('|').split('|')]
        if len(cells)==9 and re.fullmatch(r'\d+/\d+/\d+/\d+',cells[6]):
            report_paired.append((cells[4],cells[5],cells[6]))
    expected_paired=Counter((f'{100*r.difference:.2f}',f'[{100*r.adjusted_ci_low:.2f}, {100*r.adjusted_ci_high:.2f}]',
        f'{r.both_reject}/{r.only_a}/{r.only_b}/{r.neither}') for r in paired.itertuples())
    require(len(report_paired)==213 and Counter(report_paired)==expected_paired,'Report paired counts/interval conflict')
    physical=methods.drop_duplicates(['phase','scenario_id'])
    counts={p: {'h0':int(((physical.phase==p)&(physical.tau==0)).sum()),
        'h1':int(((physical.phase==p)&(physical.tau>0)).sum()),
        'datasets':int(physical.loc[physical.phase==p,'valid'].sum())} for p in ('pilot','confirm')}
    require(counts=={'pilot':{'h0':13,'h1':56,'datasets':9300},'confirm':{'h0':5,'h1':15,'datasets':9500}},'Physical cell count mismatch')
    for phase in ('pilot','confirm'):
        integrity=json.loads((root/'inputs'/f'{phase}_integrity.json').read_text(encoding='utf-8'))
        require(integrity['complete'] and integrity['completed']==counts[phase]['datasets'] and not integrity['failures'], 'Integrity declaration mismatch')
    categories=paired[paired.phase.eq('confirm')].display_category.value_counts().to_dict()
    require(categories=={'positive':18,'noninferior_only':15,'negative':6,'unresolved':6}, 'Unexpected comparison labels')
    corrections=paired[(paired.phase=='confirm') & (paired.direction=='negative')]
    methods.to_csv(root/'data/methods.csv',index=False,float_format='%.17g')
    paired.to_csv(root/'data/paired.csv',index=False,float_format='%.17g')
    diagnostics.to_csv(root/'data/diagnostics.csv',index=False,float_format='%.17g')
    corrections.to_csv(root/'data/label_corrections.csv',index=False,float_format='%.17g')
    design=pd.DataFrame([{'phase':p,**v,'methods':int((methods.phase==p).sum()),'paired':int((paired.phase==p).sum()),'R_H0':500 if p=='pilot' else 1000,'R_H1':50 if p=='pilot' else 300} for p,v in counts.items()])
    table_export(root,'table01_design',design,'表1：两阶段设计。探索与确认独立；共享flat H0仅计一次。')
    compact=methods[['phase','model','n','p','tau','method','rejections','valid','rate','ci_low','ci_high','mcse','calibration']]
    table_export(root,'table02_confirm_size',compact[(compact.phase=='confirm')&(compact.tau==0)],'表2：完整确认水平；概率单位，逐格CP95%。')
    table_export(root,'table03_confirm_power',compact[(compact.phase=='confirm')&(compact.tau>0)],'表3：完整确认功效；概率单位，逐格CP95%。')
    table_export(root,'tableS01_pilot_methods',compact[compact.phase=='pilot'],'补表S1：完整探索方法汇总；概率单位，逐格CP95%。')
    paircols=['phase','model','n','p','tau','comparator','both_reject','only_a','only_b','neither','difference','adjusted_ci_low','adjusted_ci_high','familywise_declarations','direction','noninferiority','inferiority_beyond_margin','ours_calibration','comparator_calibration','comparison_scope']
    table_export(root,'tableS02_confirm_paired',paired.loc[paired.phase.eq('confirm'),paircols],'补表S2：全部45项确认配对；概率单位，m=45校正；方向与非劣独立。')
    table_export(root,'tableS03_pilot_paired',paired.loc[paired.phase.eq('pilot'),paircols],'补表S3：全部168项探索配对；概率单位，m=1逐项描述。')
    table_export(root,'tableS04_diagnostics',diagnostics[['phase','model','n','p','tau','method','statistic_median','critical_value_median']],'补表S4：统计量与临界值中位数，不可跨算法比较尺度。')
    main_presentation_tables(root,methods,design)
    report_data={'source_type':'machine_summary','methods':len(methods),'paired':len(paired),'counts':counts,
        'confirm_categories':categories,'corrected_negative_labels':len(corrections),'summary_document_counts_and_intervals':'matched',
        'raw_replicates_rescanned':False,'input_hashes':'all matched','max_method_absolute_error_tolerance':1e-12}
    (root/'data/validation.json').write_text(json.dumps(report_data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return methods,paired


if __name__ == '__main__':
    prepare(Path(__file__).resolve().parents[1])
