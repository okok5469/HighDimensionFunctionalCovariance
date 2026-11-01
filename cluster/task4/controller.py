"""Resumable login-node orchestration. Scientific work runs only via sbatch."""
import argparse
from contextlib import contextmanager
import getpass
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import time


TERMINAL = {'COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY',
            'NODE_FAIL', 'PREEMPTED', 'BOOT_FAIL', 'DEADLINE', 'REVOKED'}
ACTIVE = {'PENDING', 'RUNNING', 'CONFIGURING', 'COMPLETING', 'SUSPENDED',
          'RESIZING', 'REQUEUED', 'REQUEUE_FED', 'REQUEUE_HOLD', 'SIGNALING', 'STAGE_OUT'}
NEXT = {'smoke': 'init', 'init': 'benchmark', 'benchmark': 'plan_pilot',
        'plan_pilot': 'pilot_workers', 'pilot_collect': 'decision',
        'fallback_collect': 'decision', 'plan_fallback': 'fallback_workers',
        'plan_confirm': 'confirm_workers', 'confirm_collect': 'done'}


def decision_stage(output):
    path = Path(output)/'search_decision.json'
    if not path.exists():
        path = Path(output)/'fallback_trigger.json'
        if hashlib.sha256(path.read_bytes()).hexdigest() != path.with_suffix('.json.sha256').read_text().strip():
            raise ValueError('fallback trigger seal mismatch')
        trigger = json.loads(path.read_text())
        if not trigger.get('selection',{}).get('fallback_required'):
            raise ValueError('fallback trigger lacks eligible routing decision')
        integrity = json.loads((Path(output)/'pilot_integrity.json').read_text())
        if not integrity.get('complete'):
            raise ValueError('pilot incomplete; fallback prohibited')
        return 'plan_fallback'
    if hashlib.sha256(path.read_bytes()).hexdigest() != path.with_suffix('.json.sha256').read_text().strip():
        raise ValueError('decision seal mismatch')
    action = json.loads(path.read_text())['action']
    return {'fallback':'plan_fallback', 'confirm':'plan_confirm',
            'done_no_eligible_candidates':'done'}[action]


def config_hash(config):
    # Connection and download preferences do not change an existing experiment.
    values = {k:v for k,v in config.items() if k not in ('ssh','download_dir','package_file')}
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def validate_config(config):
    required = ('remote_project_dir', 'account', 'partition', 'bootstrap_memory_mb',
                'bootstrap_time_minutes', 'control_memory_mb', 'control_time_minutes',
                'worker_memory_limit_mb', 'worker_time_limit_minutes')
    missing = [key for key in required if not config.get(key)]
    if missing:
        raise ValueError('fill cluster configuration: ' + ', '.join(missing))
    for key in required[3:]:
        if not isinstance(config[key], int) or isinstance(config[key], bool) or config[key] <= 0:
            raise ValueError('positive integer required: ' + key)
    if config.get('module','anaconda3') != 'anaconda3' or config.get('conda_env','myenv') != 'myenv':
        raise ValueError('this package requires existing anaconda3/myenv; do not change environment')
    if not 1 <= config.get('array_concurrency',8) <= 8:
        raise ValueError('array_concurrency must be in 1..8')
    if config.get('run_name') in ('.','..') or not re.fullmatch(r'[A-Za-z0-9_.-]+',config.get('run_name','')):
        raise ValueError('run_name requires a simple nonempty directory name')
    if not str(config['remote_project_dir']).startswith('/'):
        raise ValueError('remote_project_dir must be absolute')
    return config


def validate_resume(state, config):
    if state.get('config_hash') != config_hash(config):
        raise ValueError('resume configuration differs; preserve original config')
    if state.get('submission_intent'):
        raise ValueError('interrupted sbatch acknowledgement: inspect squeue/sacct and reconcile controller_state.json before resume')


def finished(status):
    if status not in TERMINAL | ACTIVE:
        raise ValueError('unknown scheduler state: ' + status)
    return status in TERMINAL


def next_stage(stage, status):
    if not finished(status):
        return stage
    return NEXT[stage] if status == 'COMPLETED' else 'blocked'


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)


def command(argv):
    result = subprocess.run([str(x) for x in argv],check=False,text=True,capture_output=True)
    if result.returncode:
        raise RuntimeError('command failed (exit %s): %s\n%s\n%s' %
                           (result.returncode, ' '.join(map(str,argv)), result.stderr, result.stdout))
    return result.stdout.strip()


def job_state(job_id, run=None):
    run = command if run is None else run
    queued = run(['squeue','--noheader','--array','--user='+getpass.getuser(), '--format=%F|%T'])
    values = [line.split('|')[1].strip().split()[0] for line in queued.splitlines()
              if len(line.split('|')) >= 2 and line.split('|')[0].strip() == str(job_id)]
    for value in values:
        finished(value)
    if any(value in ACTIVE for value in values):
        return 'RUNNING'
    accounting = run(['sacct','--noheader','--parsable2','--allocations','--jobs='+str(job_id),
                      '--format=JobID%64,State%40,ExitCode'])
    rows=[]
    for line in accounting.splitlines():
        fields = [field.strip() for field in line.split('|')]
        if len(fields) >= 3 and re.fullmatch(re.escape(str(job_id))+r'(?:_\d+)?', fields[0]):
            status = fields[1].split()[0].rstrip('+')
            finished(status)
            rows.append((status, fields[2]))
    if not rows:
        raise ValueError('job absent from squeue and sacct; accounting must be available: '+str(job_id))
    if any(not finished(status) for status,_ in rows):
        return 'RUNNING'
    return 'COMPLETED' if all(status=='COMPLETED' and code=='0:0' for status,code in rows) else 'FAILED'


def sbatch_args(config, release, output, stage, phase='pilot', mapping=None, dependency=None):
    worker = stage == 'worker'
    memory = mapping['memory_mb'] if worker else config['control_memory_mb']
    minutes = max(1,math.ceil(mapping['seconds_per_chunk']/60)) if worker else config['control_time_minutes']
    if stage in ('smoke','benchmark','init'):
        memory,minutes = config['bootstrap_memory_mb'],config['bootstrap_time_minutes']
    if worker and (memory>config['worker_memory_limit_mb'] or minutes>config['worker_time_limit_minutes']):
        raise ValueError('measured worker resources exceed configured site budget; stop and inspect production benchmark')
    argv=['sbatch','--parsable','--account='+config['account'],'--partition='+config['partition'],
          '--nodes=1','--ntasks=1','--cpus-per-task=1','--no-requeue',
          '--mem='+str(memory)+'M','--time='+str(minutes),
          '--job-name=t4-'+stage,'--chdir='+str(release),
          '--output='+str(Path(output)/'logs'/(stage+'-%A_%a.out')),
          '--error='+str(Path(output)/'logs'/(stage+'-%A_%a.err'))]
    if dependency:
        argv.append('--dependency=afterany:'+dependency)
    if worker:
        indexes=mapping['array'].split('%')[0]
        argv.append('--array='+indexes+'%'+str(config.get('array_concurrency',8)))
    argv += [str(Path(release)/'cluster/task4/run.slurm'),str(release),str(output),stage,phase]
    if stage == 'plan-workers':
        argv.append(str(config.get('seconds_per_chunk',1800)))
    return argv


def submit_phase(config, release, output, phase, mapping, submit=command):
    worker = submit(sbatch_args(config,release,output,'worker',phase,mapping)).split(';')[0]
    collect = submit(sbatch_args(config,release,output,'collect',phase,dependency=worker)).split(';')[0]
    return worker,collect


@contextmanager
def controller_lock(path):
    import fcntl
    with Path(path).open('a') as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def source_check(release, state):
    manifest=json.loads((release/'manifest.json').read_text(encoding='utf-8'))
    for relative,expected in manifest['files'].items():
        if hashlib.sha256((release/relative).read_bytes()).hexdigest()!=expected:
            raise ValueError('release file differs: '+relative)
    identity=hashlib.sha256((release/'manifest.json').read_bytes()).hexdigest()
    if state.get('release_manifest_sha256',identity)!=identity:
        raise ValueError('controller release identity differs')
    return identity


def run_controller(config, release, output, resume=False, dry_run=False):
    validate_config(config)
    if dry_run:
        return {'dry_run':True,'stages':['smoke','init','benchmark','pilot workers','afterany collect',
                                       'decision/conditional fallback <=150','immutable lock','confirm <=2200','afterany collect/report'],
                'first_command':sbatch_args(config,release,output,'smoke')}
    output.mkdir(parents=True,exist_ok=True)
    (output/'logs').mkdir(exist_ok=True)
    state_path=output/'controller_state.json'
    with controller_lock(output/'controller.lock'):
        if resume:
            state=json.loads(state_path.read_text(encoding='utf-8'))
            validate_resume(state,config)
            source_check(release,state)
            if state['stage']=='blocked':
                # Retry exactly the failed stage; workers validate existing complete records.
                state['stage']=state['blocked_stage']
                state['job_id']=None
                state.pop('worker_job_id',None)
        else:
            if state_path.exists():
                raise ValueError('run exists: use resume with identical config')
            state=dict(config_hash=config_hash(config),stage='smoke',job_id=None,history=[],
                       release=str(release),release_manifest_sha256=source_check(release,{}))
            atomic_json(state_path,state)
        def submit(argv,stage):
            state['submission_intent']={'stage':stage,'argv':argv}
            atomic_json(state_path,state)
            job=command(argv).split(';')[0]
            if not job.isdigit():
                raise ValueError('unrecognized sbatch acknowledgement: '+job)
            state.pop('submission_intent')
            state['history'].append(dict(stage=stage,job_id=job,argv=argv))
            return job
        while state['stage']!='done':
            stage=state['stage']
            if not state.get('job_id'):
                if stage.endswith('_workers'):
                    phase=stage.split('_')[0]
                    mapping_path=output/(phase+'_workers.json')
                    # plan-workers is executed on a compute node and seals this file.
                    expected=mapping_path.with_suffix('.json.sha256').read_text().strip()
                    if hashlib.sha256(mapping_path.read_bytes()).hexdigest()!=expected:
                        raise ValueError('worker mapping seal mismatch')
                    mapping=json.loads(mapping_path.read_text())
                    if not state.get('worker_job_id'):
                        state['worker_job_id']=submit(sbatch_args(config,release,output,'worker',phase,mapping),stage)
                        atomic_json(state_path,state)
                    state['job_id']=submit(sbatch_args(config,release,output,'collect',phase,
                                                     dependency=state['worker_job_id']),phase+'_collect')
                    state['stage']=phase+'_collect'
                else:
                    cli_stage='plan-workers' if stage.startswith('plan_') else stage
                    phase=stage[5:] if stage.startswith('plan_') else 'pilot'
                    state['job_id']=submit(sbatch_args(config,release,output,cli_stage,phase),stage)
                atomic_json(state_path,state)
            status=job_state(state['job_id'])
            state['last_scheduler_state']=status
            atomic_json(state_path,state)
            if not finished(status):
                time.sleep(config.get('poll_seconds',30))
                continue
            stage=state['stage']
            transition=decision_stage(output) if stage=='decision' and status=='COMPLETED' else next_stage(stage,status)
            state['history'].append(dict(stage=stage,job_id=state['job_id'],status=status))
            state['stage']=transition
            state['job_id']=None
            state.pop('worker_job_id',None)
            if transition=='blocked':
                state['blocked_stage']=stage.replace('_collect','_workers')
                atomic_json(state_path,state)
                raise ValueError('stage failed: '+stage+'; retained failures/logs; inspect then resume')
            atomic_json(state_path,state)
        return state


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('start','resume','status'))
    parser.add_argument('--config',required=True,type=Path)
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args(argv)
    config=json.loads(args.config.read_text(encoding='utf-8-sig'))
    release=Path(__file__).resolve().parents[2]
    output=Path(config['remote_project_dir'])/'results/task4_fixed_methods_v1'/config['run_name']
    if args.action=='status':
        result=json.loads((output/'controller_state.json').read_text())
    else:
        result=run_controller(config,release,output,args.action=='resume',args.dry_run)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
