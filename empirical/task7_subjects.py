"""Six predefined subject-level HAR cross-covariance tests using frozen cores."""
from __future__ import annotations
import os
for _thread_name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_thread_name]='1'
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import psutil
from common.statistic_calculator_517 import covariance_one_sample
from common.xue_helper import run_xue_cross_test


def file_hash(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle,'sha256').hexdigest()


def array_hash(array):
    array=np.ascontiguousarray(array)
    digest=hashlib.sha256(str(array.shape).encode()+array.dtype.str.encode())
    digest.update(array.data)
    return digest.hexdigest()


def clean(value):
    if isinstance(value,np.ndarray):
        return clean(value.tolist())
    if isinstance(value,np.generic):
        return clean(value.item())
    if isinstance(value,dict):
        return {key:clean(item) for key,item in value.items()}
    if isinstance(value,(tuple,list)):
        return [clean(item) for item in value]
    if isinstance(value,float) and not np.isfinite(value):
        return None
    return value


def write_json(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(clean(value),indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')


def select_first_windows(metadata,activity_ids):
    required=['subject_id','activity_id','split','source_row']
    if not set(required).issubset(metadata.columns):
        raise ValueError('source metadata lacks subject/activity/split/source-row identity')
    if metadata[required].isna().any().any():
        raise ValueError('missing source identity')
    order=metadata.assign(split_order=metadata.split.map({'train':0,'test':1}))
    if order.split_order.isna().any():
        raise ValueError('unrecognized source split')
    order=order[order.activity_id.isin(activity_ids)].sort_values(['activity_id','subject_id','split_order','source_row'],kind='stable')
    selected=order.drop_duplicates(['activity_id','subject_id'],keep='first').drop(columns='split_order')
    if set(selected.activity_id)!=set(activity_ids):
        raise ValueError('a planned activity lacks complete observations')
    return selected.reset_index(drop=True)


def validate_checkpoint(checkpoint,identity,directory):
    if checkpoint['identity']!=identity:
        raise ValueError('checkpoint identity mismatch')
    artifacts=checkpoint['artifacts']
    if not all((directory/name).is_file() and file_hash(directory/name)==digest for name,digest in artifacts.items()):
        raise ValueError('checkpoint artifact mismatch')


def evaluate_group(Y,*,activity_id,activity_name,seed,B,alpha,output,analysis_id=None,
                   branch='subject_primary',representation='native body_acc_xyz + body_gyro_xyz; no added log/smoothing/standardization'):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    n,p,M=Y.shape
    common=dict(analysis_id=analysis_id or f'activity_{activity_id:02d}',activity_id=activity_id,activity=activity_name,
        n=n,p=p,M=M,seed=seed,alpha=alpha,input_sha256=array_hash(Y),
        branch=branch,observation_unit='real_subject',true_subject_count=n,
        independence_basis='Distinct real subjects from source subject IDs; one curve per person within this analysis',
        representation=representation)
    records=[]
    started=time.perf_counter()
    try:
        ours=covariance_one_sample(Y,np.zeros((p,p,M,M)),~np.eye(p,dtype=bool),
            alpha=alpha,B=B,seed=seed,grid=np.linspace(0,1,M),config_id='har_task7_subject_v2')
        np.save(output/'bootstrap.npy',ours.pop('bootstrap_statistics'))
        write_json(output/'ours_diagnostics.json',ours)
        records.append(dict(common,method='Ours-v1.1',s=None,B=B,T=ours['statistic'],
            critical_value=ours['critical_value'],p_value=ours['pvalue'],reject=ours['reject'],
            status='ok',failure_reason=None,elapsed_seconds=time.perf_counter()-started))
    except (ValueError,FloatingPointError,ArithmeticError) as error:
        write_json(output/'ours_diagnostics.json',dict(status='failed',failure_reason=f'{type(error).__name__}: {error}'))
        records.append(dict(common,method='Ours-v1.1',s=None,B=B,T=None,critical_value=None,
            p_value=None,reject=None,status='failed',failure_reason=f'{type(error).__name__}: {error}',
            elapsed_seconds=time.perf_counter()-started))
    for s in (5,11,21):
        started=time.perf_counter()
        try:
            result=run_xue_cross_test(Y,s=s,alpha=alpha)
            arrays={key:result.pop(key) for key in ('S','m','q') if isinstance(result.get(key),np.ndarray)}
            np.savez_compressed(output/f'xue_s{s}_arrays.npz',**arrays)
            write_json(output/f'xue_s{s}_diagnostics.json',result)
            records.append(dict(common,method='Xue-1S-EV-cross-zero',s=s,B=None,T=result['T'],
                critical_value=result['critical_T'],p_value=result['p_value'],reject=result['reject'],
                status=result['status'],failure_reason=result['failure_reason'],elapsed_seconds=time.perf_counter()-started))
        except (ValueError,FloatingPointError,ArithmeticError) as error:
            write_json(output/f'xue_s{s}_diagnostics.json',dict(status='failed',failure_reason=f'{type(error).__name__}: {error}'))
            records.append(dict(common,method='Xue-1S-EV-cross-zero',s=s,B=None,T=None,
                critical_value=None,p_value=None,reject=None,status='failed',
                failure_reason=f'{type(error).__name__}: {error}',elapsed_seconds=time.perf_counter()-started))
    return records


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='config/empirical/task7_subjects_v2.json')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    config_path=root/args.config
    config=json.loads(config_path.read_text(encoding='utf-8-sig'))
    from empirical.task7_uci_data import load_source,static_subject_means
    started=time.perf_counter()
    Y,metadata,manifest=load_source(root/config['source_dir'])
    if Y.ndim!=3 or Y.shape[1:]!=(6,128) or not np.isfinite(Y).all() or len(Y)!=len(metadata):
        raise ValueError('official curve/metadata shape mismatch')
    selected=select_first_windows(metadata,config['activity_ids'])
    output=root/config['results_dir'];output.mkdir(parents=True,exist_ok=True)
    source_paths=['common/statistic_calculator_517.py','common/statistic_calculator_xue.py','common/xue_helper.py',
        'empirical/task7_subjects.py','empirical/task7_uci_data.py']
    source_hashes={path:file_hash(root/path) for path in source_paths}
    identity=dict(source_hashes=source_hashes,config_sha256=file_hash(config_path),
        source_manifest_sha256=hashlib.sha256(json.dumps(clean(manifest),sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest())
    write_json(output/'input_manifest.json',manifest)
    plans=[]
    arrays={}
    for activity_id in config['activity_ids']:
        people=selected[selected.activity_id==activity_id].copy()
        global_index=people.global_index.to_numpy(dtype=int)
        data=Y[global_index]
        if len(data)<2 or people.subject_id.duplicated().any():
            raise ValueError('invalid independent observation unit')
        name=str(people.activity.iloc[0])
        entry=dict(analysis_id=f'activity_{activity_id:02d}',activity_id=activity_id,activity=name,
            n=len(data),p=6,M=128,seed=config['seed_base']+activity_id,
            branch='subject_primary',representation='native body_acc_xyz + body_gyro_xyz; one source window per true subject; no added log/smoothing/standardization',
            observation_unit='real_subject',subject_ids=people.subject_id.astype(int).tolist(),
            selected_global_indices=global_index.tolist(),input_sha256=array_hash(data),
            selected_windows=people.to_dict('records'))
        plans.append(entry);arrays[entry['analysis_id']]=(data,people)
    if config['include_static_subject_mean']:
        data,people=static_subject_means(Y,metadata)
        if len(data)<2 or people.subject_id.duplicated().any() or len(data)!=len(people):
            raise ValueError('invalid subject aggregation identities')
        entry=dict(analysis_id='static_subject_mean',activity_id=0,activity='STATIC_SUBJECT_MEAN',
            n=len(data),p=6,M=128,seed=config['seed_base']+7,branch='subject_aggregate',
            representation='Within each true subject, pointwise mean over every source window from activities 4/5/6; window-count weighted across static activities; no additional transforms',
            observation_unit='real_subject',subject_ids=people.subject_id.astype(int).tolist(),
            input_sha256=array_hash(data),selected_windows=people.to_dict('records'))
        plans.append(entry);arrays[entry['analysis_id']]=(data,people)
    plan=dict(version='har_subject_primary_task7_v2',identity=identity,analyses=plans,
        B=config['B'],alpha=config['alpha'],grid=np.linspace(0,1,128),
        physical_time_seconds=np.arange(128)/50,
        channel_order=['body_acc_x','body_acc_y','body_acc_z','body_gyro_x','body_gyro_y','body_gyro_z'],
        units=['g','g','g','radian/second','radian/second','radian/second'],
        selection='For every planned activity and true subject: first complete source window in train-before-test and original source-row order; no amplitude or p-value selection',
        preprocessing='Source native window values only; no added log-return, smoothing, centering per curve, scaling or standardization',
        methods=['Ours-v1.1','Xue-1S-EV-cross-zero s5 primary','Xue cross s11 sensitivity','Xue cross s21 sensitivity'],
        interpretation='Single-activity cross-channel zero covariance, subject sampling units; finite small-n approximation and cross EV limitations apply; no simultaneous familywise claim')
    plan_path=output/'analysis_plan.json'
    if plan_path.exists() and json.loads(plan_path.read_text(encoding='utf-8'))!=clean(plan):
        raise ValueError('analysis plan changed; choose a new version output directory')
    write_json(plan_path,plan)
    selected.to_csv(output/'selected_windows.csv',index=False)
    records=[];computed=0;resumed=0
    for entry in plans:
        directory=output/entry['analysis_id'];directory.mkdir(exist_ok=True)
        checkpoint=directory/'checkpoint.json'
        group_identity=dict(identity,analysis=entry,B=config['B'],alpha=config['alpha'])
        if checkpoint.exists():
            previous=json.loads(checkpoint.read_text(encoding='utf-8'))
            validate_checkpoint(previous,group_identity,directory)
            records.extend(json.loads((directory/'result.json').read_text(encoding='utf-8')))
            resumed+=1
            continue
        data,people=arrays[entry['analysis_id']]
        np.save(directory/'Y.npy',data)
        people.to_csv(directory/'selected_windows.csv',index=False)
        rows=evaluate_group(data,activity_id=entry['activity_id'],activity_name=entry['activity'],
            seed=entry['seed'],B=config['B'],alpha=config['alpha'],output=directory,
            analysis_id=entry['analysis_id'],branch=entry['branch'],representation=entry['representation'])
        write_json(directory/'result.json',rows)
        artifacts={path.name:file_hash(path) for path in directory.iterdir() if path.is_file() and path.name!='checkpoint.json'}
        write_json(checkpoint,dict(identity=group_identity,artifacts=artifacts))
        records.extend(rows);computed+=1
        print(f"Completed {entry['analysis_id']}: n={entry['n']}",flush=True)
    table=pd.DataFrame(records)
    table.to_csv(output/'results.csv',index=False)
    write_json(output/'results.json',records)
    after={path:file_hash(root/path) for path in source_paths}
    if after!=source_hashes:
        raise ValueError('source changed during analysis')
    write_json(output/'source_integrity.json',dict(before=source_hashes,after=after,all_unchanged=True))
    write_json(output/'run_complete.json',dict(status='complete',activities=len(config['activity_ids']),analyses=len(plans),method_results=len(records),
        successful=int((table.status=='ok').sum()),failed=int((table.status!='ok').sum()),
        computed_activities=computed,resumed_activities=resumed,elapsed_seconds=time.perf_counter()-started,
        process_memory=psutil.Process().memory_info()._asdict(),identity=identity))
    print(f'SUBJECT_COMPLETE {len(plans)} analyses / {len(records)} method results',flush=True)


if __name__=='__main__':
    main()
