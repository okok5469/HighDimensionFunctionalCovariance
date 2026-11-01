"""Task5 two-sided level evaluation and fixed-family paired comparisons.

Statistical states describe results; none of them alters a planned experiment.
"""
from pathlib import Path
import numpy as np
from simulation.task3_summary import summarize_records, _cp, _write_csv


def level_status(k, n, phase):
    if n == 0:
        return 'unresolved'
    low, high = _cp(k, n, .95)
    if phase != 'confirm':
        return 'exploratory_point_in_band' if .03*n <= k <= .07*n else (
            'exploratory_point_low' if k < .03*n else 'exploratory_point_high')
    if low >= .03 and high <= .07:
        return 'near_nominal'
    if high < .03:
        return 'conservative'
    if low > .07:
        return 'inflated'
    return 'unresolved'


def summarize(plan, records, failures=None):
    # Retain the audited exact binomial/discordant-count interval arithmetic.
    result = summarize_records(plan, records, failures)
    nulls = {}
    for row in result['summary']:
        row.pop('calibration_upper_pass', None)
        row.pop('conservative', None)
        row['evaluation_band'] = '[0.03,0.07]'
        row['level_status'] = ('not_applicable' if row['tau'] else
            level_status(row['rejections'], row['valid'], plan['phase']) if row['complete'] else 'incomplete')
        row['point_in_band'] = .03 <= row['rate'] <= .07 if row['tau'] == 0 and row['rate'] is not None else None
        if row['tau'] == 0:
            nulls[row['null_group_id'], row['n'], row['p'], row['method']] = row
    for pair in result['paired']:
        matched = [nulls.get((pair['null_group_id'], pair['n'], pair['p'], m))
                   for m in ('ours', pair['comparator'])]
        statuses = [x['level_status'] if x else 'missing' for x in matched]
        pair['ours_level_status'], pair['comparator_level_status'] = statuses
        calibrated = all(x == 'near_nominal' for x in statuses)
        pair['calibration_accepted'] = calibrated
        pair.pop('null_conservative', None)
        lower = pair['adjusted_ci_low']
        formal = plan['phase'] == 'confirm' and result['complete']
        pair['label'] = ('exploratory_only' if plan['phase']!='confirm' else 'incomplete' if not formal else
            ('rejection_probability_positive' if lower > 0 else
             'rejection_probability_noninferior' if lower > -.05 else 'insufficient_evidence'))
        pair['interpretation'] = ('within_working_calibration_band' if formal and calibrated
                                  else 'nominal_rejection_probability_only')
    return result


def findings(phase, rows):
    """Describe every primary result, without upgrading exploratory evidence."""
    primary=[r for r in rows if r['method']=='ours']
    nulls={(r['null_group_id'],r['n'],r['p']):r for r in primary if r['tau']==0}
    lines=['','### Model findings','']
    supported=[]
    units=sorted({(r['spec_id'],r['n'],r['p']) for r in primary if r['tau']>0})
    for spec,n,p in units:
        alternatives=sorted([r for r in primary if (r['spec_id'],r['n'],r['p'])==(spec,n,p)
                             and r['tau']>0],key=lambda r:r['tau'])
        matched=nulls.get((alternatives[0]['null_group_id'],n,p))
        status=matched['level_status'] if matched else 'missing'
        trend=', '.join('tau=%g: %.1f%%' % (r['tau'],100*r['rate']) for r in alternatives)
        high=[r['tau'] for r in alternatives if r['rate']>=.80]
        lines.append('- %s (n=%s,p=%s): ours H0=%s; %s; high-power point estimates at %s.' %
                     (spec,n,p,status,trend,high or 'none'))
        if phase=='confirm' and status=='near_nominal' and high:
            supported.append('%s(n=%s,p=%s)' % (spec,n,p))
    for spec in sorted({r['spec_id'] for r in primary if r['tau']>0}):
        for tau in sorted({r['tau'] for r in primary if r['spec_id']==spec and r['tau']>0}):
            axis=[r for r in primary if r['spec_id']==spec and r['tau']==tau]
            sample=sorted([r for r in axis if r['p']==20],key=lambda r:r['n'])
            dimension=sorted([r for r in axis if r['n']==800],key=lambda r:r['p'])
            for name,values,coordinate in [('sample-size',sample,'n'),('channel-dimension',dimension,'p')]:
                if len(values)>1:
                    lines.append('- %s tau=%g %s trend (descriptive point estimates): %s.' %
                        (spec,tau,name,', '.join('%s=%s: %.1f%%' % (coordinate,r[coordinate],100*r['rate']) for r in values)))
    if phase!='confirm':
        lines.append('These are exploratory/workflow findings; the research target remains unconfirmed.')
    elif supported:
        lines.append('Units with working level band and high power point estimates: '+', '.join(supported)+'.')
    else:
        lines.append('No confirmed unit simultaneously supports the working level band and a high power point estimate; inspect level uncertainty/deviation and the complete power curve.')
    lines.append('High power is an estimated rejection probability, not a guarantee. Comparative claims additionally require the locked paired intervals and both method-specific level states.')
    return '\n'.join(lines)


def export(root, plan, records, failures):
    root = Path(root)
    result = summarize(plan, records, failures)
    phase = plan['phase']
    for suffix, rows in [('level_summary', [r for r in result['summary'] if r['tau'] == 0]),
                         ('power_summary', [r for r in result['summary'] if r['tau'] > 0]),
                         ('summary', result['summary']), ('paired_comparisons', result['paired']),
                         ('runtime_summary', result['runtime'])]:
        _write_csv(root/(phase+'_'+suffix+'.csv'), rows)
    directory = root/'integrity_and_failures'
    directory.mkdir(exist_ok=True)
    _write_csv(directory/(phase+'_failures.csv'), result['failures'])
    details = []
    grouped = {}
    for record in records:
        grouped.setdefault(record['scenario_id'], []).append(record)
    for entry in plan['scenarios']:
        for method in ('ours', 'xue_s5', 'xue_s11', 'xue_s21'):
            row = dict(scenario_id=entry['scenario_id'], phase=phase, method=method,
                       **{k:entry['scenario'][k] for k in ('spec_id','n','p','tau')})
            for key in ('statistic', 'critical_value', 'pvalue'):
                values = [r['methods'][method].get(key) for r in grouped.get(entry['scenario_id'], [])
                          if r['methods'][method]['status'] == 'ok']
                values = [x for x in values if x is not None and np.isfinite(x)]
                for name, quantile in [('min',0),('q25',.25),('median',.5),('q75',.75),('max',1)]:
                    row[key+'_'+name] = float(np.quantile(values,quantile)) if values else None
            details.append(row)
    _write_csv(root/(phase+'_diagnostic_summary.csv'), details)
    return result


def figures(root, phase, rows):
    """EDA curves with exact pointwise intervals; phases never share a curve."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import rc_context
    root = Path(root)/'figures'
    root.mkdir(exist_ok=True)
    groups = sorted({(r['spec_id'],r['n'],r['p']) for r in rows if r['tau'] > 0})
    colors = ['#222222','#7697b3','#8fb9b4','#b28ba6']
    with rc_context({'font.size':9,'svg.fonttype':'none','pdf.fonttype':42,
                     'axes.spines.right':False,'axes.spines.top':False}):
        for spec,n,p in groups:
            fig,ax = plt.subplots(figsize=(6.3,4.3))
            for method,color in zip(('ours','xue_s5','xue_s11','xue_s21'),colors):
                points = sorted([r for r in rows if (r['spec_id'],r['n'],r['p'],r['method']) == (spec,n,p,method)
                                 and r['tau'] > 0 and r['rate'] is not None],key=lambda r:r['tau'])
                if not points:
                    continue
                y=np.array([r['rate'] for r in points])
                error=np.array([[r['ci_low'] for r in points],[r['ci_high'] for r in points]])
                error=np.array([y-error[0],error[1]-y])
                ax.errorbar([r['tau'] for r in points],y,yerr=error,color=color,
                            marker='o',markersize=3,lw=1,capsize=2,label=method)
            ax.set(xlabel='Grid covariance effect (tau)',ylabel='Rejection probability',ylim=(-.03,1.03),
                   title='%s: %s, n=%s, p=%s' % (phase,spec,n,p))
            ax.legend(loc='upper left',bbox_to_anchor=(1.02,1),borderaxespad=0)
            fig.text(.12,.02,'Pointwise 95% exact binomial intervals; '+('workflow smoke only' if phase=='smoke' else
                     'independent confirmation' if phase=='confirm' else 'exploratory data'),fontsize=7)
            fig.subplots_adjust(right=.75,bottom=.17,top=.87)
            name=root/('%s_%s_n%s_p%s_power' % (phase,spec,n,p))
            for suffix in ('.svg','.pdf','.png'):
                fig.savefig(name.with_suffix(suffix),dpi=180)
            plt.close(fig)
        for n,p in sorted({(r['n'],r['p']) for r in rows if r['tau'] == 0}):
            nulls=[r for r in rows if (r['n'],r['p'],r['tau'])==(n,p,0) and r['rate'] is not None]
            specs=sorted({r['spec_id'] for r in nulls})
            fig,ax=plt.subplots(figsize=(6.3,4.3))
            for offset,(method,color) in enumerate(zip(('ours','xue_s5','xue_s11','xue_s21'),colors)):
                points=[next(r for r in nulls if r['spec_id']==spec and r['method']==method) for spec in specs]
                y=np.array([r['rate'] for r in points])
                errors=np.array([y-np.array([r['ci_low'] for r in points]),
                                 np.array([r['ci_high'] for r in points])-y])
                ax.errorbar(np.arange(len(specs))+(offset-1.5)*.12,y,yerr=errors,
                            color=color,fmt='o',ms=3,capsize=2,label=method)
            ax.axhspan(.03,.07,color='#dedede',alpha=.6)
            ax.axhline(.05,color='#777777',lw=.7,ls='--')
            short={'m1_fourier5_peak1':'M1','m2_brownian_peak1':'M2',
                   'spectrum_flat_b0':'Flat (shared)','spectrum_fast_b4':'Fast','coherent_all':'Flat (shared)'}
            ax.set(xticks=np.arange(len(specs)),xticklabels=[short.get(s,s) for s in specs],
                   ylabel='H0 rejection probability',title='%s H0: n=%s, p=%s' % (phase,n,p),
                   ylim=(-.01,min(1.03,max(.15,max(r['ci_high'] for r in nulls)+.03))))
            ax.legend(loc='upper left',bbox_to_anchor=(1.02,1),borderaxespad=0)
            fig.text(.12,.02,'Pointwise 95% exact intervals; band [.03,.07], alpha=.05',fontsize=7)
            fig.subplots_adjust(right=.75,bottom=.17,top=.87)
            name=root/('%s_n%s_p%s_level' % (phase,n,p))
            for suffix in ('.svg','.pdf','.png'):
                fig.savefig(name.with_suffix(suffix),dpi=180)
            plt.close(fig)
