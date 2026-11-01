"""Verified UCI HAR windows and recoverable CSV identities; no statistical tests.

load_source takes the directory containing README.txt, train/ and test/.
Metadata rows/global_index align exactly with the first axis of the returned Y.
All persisted paths are relative and all manifests are deterministic.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile
import numpy as np
import pandas as pd


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def read_numeric(path, shape, integer=False):
    raw=Path(path).read_bytes()
    if b'\0' in raw:
        raise ValueError(f'NUL in numeric source: {path}')
    text=raw.decode('ascii',errors='strict')
    values=np.loadtxt(io.StringIO(text),dtype=float)
    if values.shape!=shape:
        raise ValueError(f'unexpected numeric shape {values.shape}, expected {shape}: {path}')
    if not np.isfinite(values).all():
        raise ValueError(f'non-finite numeric source: {path}')
    if integer and not np.equal(values,np.floor(values)).all():
        raise ValueError(f'expected integer labels: {path}')
    return values.astype(np.int64) if integer else values


def verified_archive(source_root):
    source_root=Path(source_root)
    archive=source_root.parents[1]/'UCI HAR Dataset.zip'
    source_files={};ignored=[]
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            parts=PurePosixPath(item.filename).parts
            if item.is_dir():
                continue
            if parts[0]=='__MACOSX' or any(p.startswith('.') for p in parts):
                ignored.append(item.filename)
                continue
            if parts[0]!='UCI HAR Dataset' or '..' in parts:
                raise ValueError(f'unexpected archive member: {item.filename}')
            relative=PurePosixPath(*parts[1:]).as_posix()
            extracted=source_root/relative
            body=z.read(item)
            digest=sha_bytes(body)
            if not extracted.is_file() or sha_bytes(extracted.read_bytes())!=digest:
                raise ValueError(f'extracted file differs from archive: {relative}')
            source_files[relative]=dict(bytes=len(body),sha256=digest,zip_member=item.filename)
    return dict(archive_name=archive.name,archive_sha256=sha_bytes(archive.read_bytes()),
                files=source_files,ignored_platform_metadata=sorted(ignored),
                all_scientific_members_match=True)


def select_first_windows(metadata):
    columns=['activity_id','subject_id','split','source_row']
    return metadata.sort_values(columns,kind='stable').drop_duplicates(['activity_id','subject_id']).reset_index(drop=True)


def load_source(source_root):
    source_root=Path(source_root)
    provenance=verified_archive(source_root)
    label_lines=(source_root/'activity_labels.txt').read_text(encoding='ascii').splitlines()
    labels={int(line.split()[0]):line.split()[1] for line in label_lines if line.strip()}
    expected={1:'WALKING',2:'WALKING_UPSTAIRS',3:'WALKING_DOWNSTAIRS',4:'SITTING',5:'STANDING',6:'LAYING'}
    if labels!=expected:
        raise ValueError('activity label definition differs from UCI HAR Version 1.0')
    channels=[f'{kind}_{axis}' for kind in ('body_acc','body_gyro') for axis in 'xyz']
    arrays=[];frames=[];subject_sets={}
    offset=0
    for split,count in [('train',7352),('test',2947)]:
        directory=source_root/split
        subjects=read_numeric(directory/f'subject_{split}.txt',(count,),integer=True)
        activities=read_numeric(directory/f'y_{split}.txt',(count,),integer=True)
        if not np.isin(subjects,np.arange(1,31)).all() or not np.isin(activities,np.arange(1,7)).all():
            raise ValueError('out-of-range subject/activity identifiers')
        subject_sets[split]=sorted(np.unique(subjects).tolist())
        used={}
        for kind in ('body_acc','body_gyro','total_acc'):
            for axis in 'xyz':
                name=f'{kind}_{axis}'
                signal=read_numeric(directory/'Inertial Signals'/f'{name}_{split}.txt',(count,128))
                if name in channels:
                    used[name]=signal
        arrays.append(np.stack([used[c] for c in channels],axis=1))
        frames.append(pd.DataFrame(dict(global_index=np.arange(offset,offset+count),
            split=split,source_row=np.arange(count),subject_id=subjects,activity_id=activities,
            activity=[labels[int(a)] for a in activities],session_id=None,
            absolute_window_start=None,source_record='source signal matrix row')))
        offset+=count
    if set(subject_sets['train'])&set(subject_sets['test']):
        raise ValueError('subject sets overlap across official train/test split')
    if sorted(subject_sets['train']+subject_sets['test'])!=list(range(1,31)):
        raise ValueError('official source does not contain all 30 subjects')
    metadata=pd.concat(frames,ignore_index=True)
    if metadata.groupby(['activity_id','subject_id']).size().shape!=(180,):
        raise ValueError('not all six activities present for all 30 subjects')
    manifest=dict(source_id='UCI_HAR_Version_1.0',source_url='https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones',
        archive=provenance,shape=[10299,6,128],channel_order=channels,
        units=['g','g','g','rad/s','rad/s','rad/s'],sampling_frequency_hz=50,
        window_readings=128,window_duration_seconds=2.56,window_overlap_fraction=.5,
        train_subjects=subject_sets['train'],test_subjects=subject_sets['test'],
        split_subject_sets_disjoint=True,activity_labels=labels,
        preprocessing='Official published inertial windows; no additional log-return, smoothing, standardization, resampling or gravity transformation',
        subject_design='README records 30 volunteers and a subject-wise 70/30 train/test partition; inference uses a single complete window per subject within each activity',
        unknown_metadata=['session_id','absolute_window_start'],
        source_row_convention='zero-based row of the corresponding official signal matrices',
        selection_rule='Within each activity and true subject select smallest source_row from its unique official split; no amplitude, statistic or p-value selection')
    return np.concatenate(arrays,axis=0),metadata,manifest


def static_subject_means(Y,metadata):
    rows=[];arrays=[]
    for subject in sorted(metadata.subject_id.unique()):
        group=metadata[(metadata.subject_id==subject)&metadata.activity_id.isin([4,5,6])]
        indices=group.global_index.to_numpy()
        arrays.append(Y[indices].mean(axis=0))
        counts=group.groupby('activity_id').size()
        rows.append(dict(subject_id=int(subject),split=group.split.iloc[0],
            source_windows=len(group),source_window_count=len(group),source_global_indices=indices.tolist(),source_row=None,
            sitting_windows=int(counts.loc[4]),standing_windows=int(counts.loc[5]),laying_windows=int(counts.loc[6]),
            weighting='equal weight per published source window, not equal weight per activity',
            activity='STATIC_SUBJECT_MEAN',activity_components=[4,5,6]))
    return np.stack(arrays),pd.DataFrame(rows)


def dynamic_mapping(Y,metadata,old_path):
    old=pd.read_csv(old_path,encoding='utf-8-sig',on_bad_lines='error')
    columns=['sample_id','time',*[f'var_{j}' for j in range(6)]]
    if old.columns.tolist()!=columns or old.shape!=(420480,8) or old.duplicated(['sample_id','time']).any():
        raise ValueError('legacy dynamic structure differs from known complete input')
    old=old.sort_values(['sample_id','time']).reset_index(drop=True)
    if not np.isfinite(old.to_numpy()).all():
        raise ValueError('non-finite legacy dynamic input')
    values=old[columns[2:]].to_numpy().reshape(3285,128,6).transpose(0,2,1)
    candidate=metadata[(metadata.split=='train')&metadata.activity_id.isin([1,2,3])].copy()
    source=Y[candidate.global_index.to_numpy()]
    if source.shape!=values.shape or not np.array_equal(source,values):
        raise ValueError('legacy dynamic is not exactly the source-ordered training activity1/2/3 subset')
    digests={};duplicates=[]
    for row in candidate.itertuples():
        digest=sha_bytes(np.ascontiguousarray(Y[row.global_index]).tobytes())
        if digest in digests:
            duplicates.append([digests[digest],row.global_index])
        digests[digest]=row.global_index
    if duplicates:
        raise ValueError(f'ambiguous duplicate source windows in dynamic subset: {duplicates[:3]}')
    candidate.insert(0,'sample_id',np.arange(3285))
    evidence=dict(legacy_dynamic_sha256=sha_bytes(Path(old_path).read_bytes()),
        match='exact numerical equality on every complete six-channel 128-point window',
        matched_windows=3285,matched_subjects=sorted(candidate.subject_id.unique().tolist()),
        matched_activities=[1,2,3],max_absolute_difference=0.,unique_complete_window_hashes=len(digests),
        mapping_basis='Source row ordering and full-window exact equality; no ID-chain, overlap or clustering inference',
        source_split='train')
    return candidate,evidence


def static_prefix_evidence(old_path,meanY,mean_metadata):
    raw=Path(old_path).read_bytes();rows=[]
    for body in raw.split(b'\n')[1:]:
        try:
            row=[float(x) for x in body.decode('ascii',errors='strict').strip().split(',')]
            if len(row)!=8 or not np.isfinite(row).all():
                break
            rows.append(row)
        except (UnicodeError,ValueError):
            break
    values=np.asarray(rows)
    if values.shape!=(953,8):
        raise ValueError('static damaged-prefix identity differs from audited original')
    encoded=values[:,0].astype(int);time=values[:,1].astype(int)
    if not np.equal(values[:,:2],np.floor(values[:,:2])).all():
        raise ValueError('noninteger static prefix keys')
    real_subjects=mean_metadata.subject_id.to_numpy()[encoded]
    expected=meanY[encoded,:,time]
    if not np.array_equal(values[:,2:],expected):
        raise ValueError('static prefix does not exactly match the reconstructed subject means')
    return dict(legacy_static_sha256=sha_bytes(raw),legacy_static_bytes=len(raw),nul_bytes=raw.count(b'\0'),
        complete_observed_prefix_rows=953,complete_observed_prefix_curves=7,
        partial_eighth_curve_time_range=[0,56],prefix_numeric_match='exact',max_absolute_difference=0.,
        observed_encoded_to_real_subject={str(int(a)):int(b) for a,b in zip(encoded,real_subjects)},
        reconstruction_formula='For each real subject 1..30, pointwise arithmetic mean over every official train/test window labelled4/5/6, equal weight per window',
        validation_boundary='Only the 953 intact numeric prefix rows were validated; the corrupted/unobservable remainder of the old CSV cannot be certified',
        original_damaged_file_overwritten=False,new_reconstruction_identity='official_source_static_subject_mean_v2')


def write_json(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def prepare(project_root):
    project_root=Path(project_root)
    source_root=project_root/'data/har/UCI HAR Dataset/UCI HAR Dataset'
    Y,metadata,manifest=load_source(source_root)
    output=project_root/'data/empirical/har/metadata/task7_subject_v2'
    processed=project_root/'data/empirical/har/processed/task7_subject_v2'
    output.mkdir(parents=True,exist_ok=True);processed.mkdir(parents=True,exist_ok=True)
    write_json(output/'source_manifest.json',manifest)
    metadata.to_csv(output/'official_window_metadata.csv',index=False)
    selected=select_first_windows(metadata)
    selected.to_csv(output/'selected_first_windows.csv',index=False)
    mapping,evidence=dynamic_mapping(Y,metadata,project_root/'data/har/har_dynamic_long.csv')
    mapping.to_csv(output/'legacy_dynamic_window_mapping.csv',index=False)
    write_json(output/'legacy_dynamic_mapping_validation.json',evidence)
    means,mean_metadata=static_subject_means(Y,metadata)
    prefix=static_prefix_evidence(project_root/'data/har/har_static_subject.csv',means,mean_metadata)
    write_json(output/'legacy_static_prefix_validation.json',prefix)
    mean_metadata.to_csv(output/'static_subject_mean_metadata.csv',index=False)
    np.save(processed/'static_subject_mean.npy',means)
    recovered=pd.DataFrame(dict(subject=np.repeat(mean_metadata.subject_id.to_numpy(),128),time=np.tile(np.arange(128),30)))
    for j in range(6):
        recovered[f'var_{j}']=means[:,j,:].reshape(-1)
    recovered.to_csv(processed/'har_static_subject_recovered.csv',index=False)
    for activity in range(1,7):
        group=selected[selected.activity_id==activity]
        np.save(processed/f'activity_{activity}_first_window.npy',Y[group.global_index.to_numpy()])
    write_json(output/'data_preparation_complete.json',dict(source_windows=len(Y),source_subjects=30,activities=6,
        selected_one_window_per_subject_activity=len(selected),legacy_dynamic_mapping='exact_3285_windows',
        static_prefix='exact_953_intact_rows_only',recovered_static_shape=list(means.shape),
        scientific_source_paths='relative to source root; all source files agree with retained ZIP'))
    return Y,metadata,manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--project-root',default=str(Path(__file__).resolve().parents[1]))
    args=parser.parse_args();prepare(Path(args.project_root));print('SOURCE_AND_MAPPING_VALIDATION_COMPLETE')
