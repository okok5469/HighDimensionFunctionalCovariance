"""Traceable HAR historical diagnostics; frozen statistical cores are imported."""
from __future__ import annotations
import os
for _name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name]='1'
import argparse
import hashlib
import io
import json
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import pandas as pd
import psutil
from empirical.har_data_loader import build_windows
from common.statistic_calculator_517 import covariance_one_sample
from common.xue_helper import run_xue_cross_test


def file_hash(path):
    with open(path,'rb') as handle:
        return hashlib.file_digest(handle,'sha256').hexdigest()


def array_hash(array):
    array=np.ascontiguousarray(array)
    h=hashlib.sha256(str(array.shape).encode()+array.dtype.str.encode())
    h.update(array.data)
    return h.hexdigest()


def clean(value):
    if isinstance(value,np.ndarray):
        return clean(value.tolist())
    if isinstance(value,np.generic):
        return clean(value.item())
    if isinstance(value,dict):
        return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):
        return [clean(v) for v in value]
    if isinstance(value,float) and not np.isfinite(value):
        return None
    return value


def write_json(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(clean(value),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def strict_dynamic(path):
    raw=Path(path).read_bytes()
    if b'\x00' in raw:
        raise ValueError('NUL bytes in CSV')
    frame=pd.read_csv(io.StringIO(raw.decode('utf-8-sig',errors='strict')),on_bad_lines='error')
    expected=['sample_id','time',*[f'var_{j}' for j in range(6)]]
    if frame.columns.tolist()!=expected:
        raise ValueError('unexpected dynamic columns')
    values=frame.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError('non-finite input')
    if not np.equal(values[:,:2],np.floor(values[:,:2])).all():
        raise ValueError('noninteger ID/time')
    if frame.duplicated(['sample_id','time']).any():
        raise ValueError('duplicate window/time keys')
    frame=frame.sort_values(['sample_id','time']).reset_index(drop=True)
    groups=frame.groupby('sample_id',sort=True)
    if not (groups.size()==128).all():
        raise ValueError('incomplete windows')
    times=frame['time'].to_numpy().reshape(-1,128)
    if not np.equal(times,np.arange(128)).all():
        raise ValueError('unexpected time grid')
    Y=frame[expected[2:]].to_numpy().reshape(-1,128,6).transpose(0,2,1)
    return frame,Y


def cross_mask(p,M):
    return np.repeat(np.repeat(~np.eye(p,dtype=bool),M,axis=0),M,axis=1)


def valid_artifacts(artifacts,root):
    return all((Path(root)/name).is_file() and file_hash(Path(root)/name)==digest for name,digest in artifacts.items())


def evaluate(Y,*,seed,B,alpha,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    n,p,M=Y.shape
    digest=array_hash(Y)
    common=dict(input_sha256=digest,n=n,p=p,M=M,alpha=alpha,seed=seed,
                true_subject_count=None,observation_unit='derived_overlapping_window',
                independent_units_basis='not established; numerical legacy diagnostic only')
    started=time.perf_counter()
    ours=covariance_one_sample(Y,np.zeros((p,p,M,M)),~np.eye(p,dtype=bool),
        alpha=alpha,B=B,seed=seed,grid=np.linspace(0,1,M))
    np.save(output/'bootstrap.npy',ours.pop('bootstrap_statistics'))
    write_json(output/'ours_diagnostics.json',ours)
    records=[dict(common,method='Ours-v1.1',s=None,T=ours['statistic'],
        critical_value=ours['critical_value'],p_value=ours['pvalue'],reject=ours['reject'],
        B=B,status='ok',failure_reason=None,elapsed_seconds=time.perf_counter()-started)]
    for s in (5,11,21):
        started=time.perf_counter()
        x=run_xue_cross_test(Y,s=s,alpha=alpha)
        arrays={key:x.pop(key) for key in ('S','m','q') if isinstance(x.get(key),np.ndarray)}
        np.savez_compressed(output/f'xue_s{s}_arrays.npz',**arrays)
        write_json(output/f'xue_s{s}_diagnostics.json',x)
        records.append(dict(common,method='Xue-1S-EV-cross-zero',s=s,T=x['T'],
            critical_value=x['critical_T'],p_value=x['p_value'],reject=x['reject'],B=None,
            status=x['status'],failure_reason=x['failure_reason'],elapsed_seconds=time.perf_counter()-started))
    return records


def analysis_specs(pool_size):
    specifications=[dict(analysis_id='dynamic_base',experiment='basic',n=200,p=6,seed=42,repeat=0)]
    specifications += [dict(analysis_id=f'dynamic_repeat_{r:03d}',experiment='replications',n=200,p=6,seed=2025+r*1009,repeat=r) for r in range(100)]
    specifications += [dict(analysis_id=f'dynamic_grid_n{n}_p{p}_r{r:03d}',experiment='pn_grid',n=n,p=p,seed=5000+n*10+p+r*1009,repeat=r) for n in (50,100,150,200) for p in (3,4,5,6) for r in range(50)]
    for spec in specifications:
        spec['pool_indices']=np.random.default_rng(spec['seed']).choice(pool_size,size=spec['n'],replace=pool_size<spec['n']).tolist()
    return specifications


def execute_one(task):
    spec,pool_path,result_root,identity,B,alpha=task
    out=Path(result_root)/'legacy_diagnostic'/spec['analysis_id']
    checkpoint=out/'checkpoint.json'
    if checkpoint.exists():
        previous=json.loads(checkpoint.read_text(encoding='utf-8'))
        if previous['identity']!=identity or not valid_artifacts(previous['artifacts'],out):
            raise ValueError(f'checkpoint identity or artifact mismatch: {out}')
        return json.loads((out/'result.json').read_text(encoding='utf-8'))
    out.mkdir(parents=True,exist_ok=True)
    pool=np.load(pool_path,mmap_mode='r')
    indices=np.asarray(spec['pool_indices'])
    selected=pool[indices,:spec['p'],:]
    pd.DataFrame(dict(pool_index=indices,source_sample_id=indices//40,log_return_start=2*(indices%40))).to_csv(out/'selected_windows.csv',index=False)
    start=time.perf_counter()
    records=evaluate(selected,seed=spec['seed'],B=B,alpha=alpha,output=out)
    process=psutil.Process()
    memory=process.memory_info()._asdict()
    for record in records:
        record.update(analysis_id=spec['analysis_id'],experiment=spec['experiment'],repeat=spec['repeat'],
            branch='legacy_diagnostic',data_group='dynamic',preprocessing_version='historical_M48_stride2_q5_logreturn_pool_standardize',
            source_sha256=identity['dynamic_sha256'],pool_sha256=identity['pool_sha256'],
            total_elapsed_seconds=time.perf_counter()-start,process_memory=memory)
    write_json(out/'result.json',records)
    artifacts={p.name:file_hash(p) for p in out.iterdir() if p.is_file() and p.name!='checkpoint.json'}
    write_json(checkpoint,dict(identity=identity,artifacts=artifacts,status='complete'))
    return records


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    config=json.loads((root/args.config).read_text(encoding='utf-8-sig'))
    output=root/config['results_dir'];output.mkdir(parents=True,exist_ok=True)
    meta=root/config['metadata_dir'];meta.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter()
    paths={name:root/config[name] for name in ('dynamic_csv','static_csv')}
    inputs={name:dict(path=str(path.relative_to(root)),size_bytes=path.stat().st_size,sha256=file_hash(path)) for name,path in paths.items()}
    write_json(meta/'input_manifest.json',inputs)
    frame,raw=strict_dynamic(paths['dynamic_csv'])
    raw_ids=frame['sample_id'].drop_duplicates().to_numpy()
    if not np.array_equal(raw_ids,np.arange(len(raw_ids))):
        raise ValueError('historical source ID derivation requires exact sequential IDs')
    overlap=np.all(raw[:-1,:,64:]==raw[1:,:,:64],axis=(1,2))
    pd.DataFrame(dict(left_sample_id=raw_ids[:-1],right_sample_id=raw_ids[1:],exact_half_overlap=overlap)).to_csv(meta/'overlap_pairs.csv',index=False)
    static_raw=paths['static_csv'].read_bytes()
    static_error=None
    try:
        static_raw.decode('utf-8-sig',errors='strict')
        if b'\x00' in static_raw:
            raise ValueError('NUL bytes')
    except (UnicodeDecodeError,ValueError) as error:
        static_error=str(error)
    branch_status={
        'subject_dynamic':dict(status='blocked',reason='No sample_id to true subject_id/activity/split/session/window-position/source mapping or verified export script'),
        'subject_static':dict(status='blocked',reason=static_error or 'No verified subject/activity provenance or aggregation specification'),
        'legacy_static':dict(status='blocked',reason=static_error or 'No verified historical source identity'),
        'legacy_dynamic':dict(status='ready',true_subject_count=None,overlap_pairs=int(overlap.sum()),adjacent_pairs=len(overlap))}
    write_json(output/'branch_status.json',branch_status)
    processed=root/config['processed_dir'];processed.mkdir(parents=True,exist_ok=True)
    pool_path=processed/'Y_pool_dynamic.npy'
    preprocess_source=root/'empirical/har_data_loader.py'
    fingerprint=dict(dynamic_sha256=inputs['dynamic_csv']['sha256'],preprocessing_sha256=file_hash(preprocess_source))
    provenance=processed/'provenance.json'
    if pool_path.exists():
        old=json.loads(provenance.read_text(encoding='utf-8'))
        if old['input']!=fingerprint or file_hash(pool_path)!=old['pool_sha256']:
            raise ValueError('processed cache fingerprint mismatch; use new version directory')
        pool=np.load(pool_path,mmap_mode='r')
    else:
        pool=build_windows(frame.rename(columns={'sample_id':'subject'}),M=48,stride=2,q_smooth=5,
            apply_log_return=True,do_smooth=True,do_std=True,verbose=False)
        np.save(pool_path,pool)
        write_json(provenance,dict(input=fingerprint,pool_sha256=file_hash(pool_path),shape=pool.shape))
    cache=root/config['historical_dynamic_cache']
    verification=dict(cache_path=str(cache.relative_to(root)),cache_present=cache.exists())
    if cache.exists():
        historical=np.load(cache,mmap_mode='r')
        verification.update(cache_sha256=file_hash(cache),historical_shape=historical.shape)
        if historical.shape!=pool.shape:
            raise ValueError('historical dynamic cache shape differs from reconstructed source')
        difference=max(float(np.max(np.abs(pool[i:i+512]-historical[i:i+512]))) for i in range(0,len(pool),512))
        verification['max_absolute_difference']=difference
        if difference>=1e-12:
            raise ValueError('historical dynamic preprocessing mismatch')
    write_json(meta/'preprocessing_verification.json',verification)
    identity=dict(fingerprint,pool_sha256=file_hash(pool_path),config_sha256=file_hash(root/args.config),
        runner_sha256=file_hash(Path(__file__)),core_sha256=file_hash(root/'common/statistic_calculator_517.py'),
        xue_sha256=file_hash(root/'common/statistic_calculator_xue.py'),xue_helper_sha256=file_hash(root/'common/xue_helper.py'))
    specs=analysis_specs(len(pool))
    plan=dict(run_id='har_empirical_task7_v1',branch_status=branch_status,identity=identity,
        B=config['B'],alpha=config['alpha'],grid=np.linspace(0,1,48),channel_order=[f'var_{j}' for j in range(6)],
        actual_pool_shape=pool.shape,methods=['Ours-v1.1','Xue-cross-s5','Xue-cross-s11','Xue-cross-s21'],
        preprocessing='per original sample_id: shift nonpositive channel minima; diff(log(x+shift+1e-8)); 48-point stride2; Fourier q5 pinv reconstruction; pool-axis standardize with existing +1e-12 rule; no new preprocessing repair',
        interpretation='Nominal window diagnostic; observations are dependent; rejection proportions are not size or power',analyses=specs)
    plan_path=output/'analysis_plan.json'
    if plan_path.exists() and json.loads(plan_path.read_text(encoding='utf-8'))!=clean(plan):
        raise ValueError('analysis plan changed; use new version directory')
    write_json(plan_path,plan)
    tasks=[(spec,str(pool_path),str(output),identity,config['B'],config['alpha']) for spec in specs]
    records=[]
    records.extend(execute_one(tasks[0]))
    print('BASE_COMPLETE '+str(time.perf_counter()-start)+' seconds',flush=True)
    pd.DataFrame(records).to_csv(output/'results_partial.csv',index=False)
    with ProcessPoolExecutor(max_workers=config['workers']) as executor:
        futures=[executor.submit(execute_one,task) for task in tasks[1:]]
        for count,future in enumerate(as_completed(futures),start=1):
            records.extend(future.result())
            if count%25==0:
                pd.DataFrame(records).to_csv(output/'results_partial.csv',index=False)
                print(f'COMPLETE {count+1}/{len(tasks)} elapsed {time.perf_counter()-start:.1f}s',flush=True)
    table=pd.DataFrame(records).sort_values(['experiment','n','p','repeat','method','s'],na_position='first')
    table.to_csv(output/'results.csv',index=False)
    write_json(output/'results.json',table.to_dict('records'))
    summary=table.groupby(['experiment','n','p','method','s'],dropna=False).agg(analyses=('status','size'),successful=('status',lambda x:int((x=='ok').sum())),rejection_proportion=('reject','mean'),mean_p_value=('p_value','mean'),mean_T=('T','mean'),mean_critical_value=('critical_value','mean')).reset_index()
    summary.to_csv(output/'summary.csv',index=False)
    write_json(output/'run_complete.json',dict(status='complete_available_branches',analyses=len(tasks),method_results=len(table),
        elapsed_seconds=time.perf_counter()-start,identity=identity,branch_status=branch_status,
        process_memory=psutil.Process().memory_info()._asdict()))
    print('COMPLETE available diagnostic branches',flush=True)


if __name__=='__main__':
    main()
