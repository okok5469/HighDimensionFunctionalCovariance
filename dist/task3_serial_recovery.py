"""Recover a frozen task3 release through serial Slurm arrays (Python 3.9+).

Keep this file outside the frozen release. Only the original compute entry points
run scientific work. A separate journal records the scheduling override.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import types


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_controller(release):
    """Load the old standard-library controller without writing bytecode."""
    path = Path(release) / 'cluster/task3/controller.py'
    module = types.ModuleType('frozen_task3_controller')
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


def read_mapping(output, phase):
    path = output / (phase + '_workers.json')
    if path.with_suffix('.json.sha256').read_text().strip() != sha256(path):
        raise ValueError('worker mapping seal mismatch: ' + phase)
    return json.loads(path.read_text(encoding='utf-8'))


def verify_release_before_loading(release, original):
    """Reject modified controller bytes before executing any frozen Python."""
    path = release / 'manifest.json'
    if original.get('release_manifest_sha256') != sha256(path):
        raise ValueError('controller release identity differs')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if 'cluster/task3/controller.py' not in manifest['files']:
        raise ValueError('release manifest does not cover the original controller')
    for relative, expected in manifest['files'].items():
        target = (release / relative).resolve()
        if not target.is_relative_to(release) or sha256(target) != expected:
            raise ValueError('release file differs: ' + relative)


def recover(release, config_path, dry_run=False, resume=False, controller=None,
            pause=time.sleep):
    release, config_path = Path(release).resolve(), Path(config_path).resolve()
    if Path(__file__).resolve().is_relative_to(release):
        raise ValueError('keep recovery script outside the frozen release')
    config = json.loads(config_path.read_text(encoding='utf-8-sig'))
    output = Path(config['remote_project_dir']) / 'results/task3_v1' / config['run_name']
    original_path = output / 'controller_state.json'
    original = json.loads(original_path.read_text(encoding='utf-8'))
    verify_release_before_loading(release, original)
    c = controller if controller is not None else load_controller(release)
    c.validate_config(config)
    c.validate_resume(original, config)
    if original.get('stage') != 'blocked' or original.get('blocked_stage') not in ('pilot_workers','pilot_collect'):
        raise ValueError('original controller must be blocked at pilot workers/collect')
    identity = dict(release=str(release), config_path=str(config_path),
                    release_manifest_sha256=c.source_check(release, original),
                    original_controller_state_sha256=sha256(original_path),
                    original_config_sha256=sha256(config_path),
                    recovery_script_sha256=sha256(__file__),
                    scheduling_override={'array_concurrency': 1})
    scheduling = dict(config, array_concurrency=1)
    state_path = output / 'serial_recovery_state.json'
    if dry_run:
        return dict(identity, dry_run=True, stages=['pilot_workers','pilot_collect','lock',
                    'plan_confirm','confirm_workers','confirm_collect','done'],
                    first_command=c.sbatch_args(scheduling,release,output,'worker','pilot',read_mapping(output,'pilot')))
    with c.controller_lock(output / 'controller.lock'):
        # Recheck after acquiring the same lock as the old controller.
        if sha256(original_path) != identity['original_controller_state_sha256']:
            raise ValueError('original controller state changed before recovery lock')
        latest = {}
        for event in original.get('history', []):
            if event.get('stage') in ('pilot_workers','pilot_collect') and event.get('job_id'):
                latest[event['stage']] = str(event['job_id'])
        old_ids = set(latest.values()) | {str(original[key]) for key in ('job_id','worker_job_id') if original.get(key)}
        if not {'pilot_workers','pilot_collect'} <= set(latest):
            raise ValueError('original worker/collector job history is incomplete')
        for job_id in sorted(old_ids):
            if not c.finished(c.job_state(job_id)):
                raise ValueError('old worker/collector job remains active: ' + job_id)
        if resume:
            state = json.loads(state_path.read_text(encoding='utf-8'))
            if state.get('identity') != identity:
                raise ValueError('recovery provenance changed; do not combine releases/configurations')
            if state.get('submission_intent'):
                raise ValueError('uncertain sbatch acknowledgement; inspect scheduler before any reconciliation')
            if state['stage'] == 'blocked':
                state['stage'] = state['blocked_stage']
                state['job_id'] = None
        else:
            if state_path.exists():
                raise ValueError('recovery journal exists: use --resume')
            state = dict(identity=identity, stage='pilot_workers', job_id=None,
                         history=[], original_terminal_jobs=sorted(old_ids))
            c.atomic_json(state_path,state)
        transitions = {'pilot_collect':'lock','lock':'plan_confirm',
                       'plan_confirm':'confirm_workers','confirm_collect':'done'}
        while state['stage'] != 'done':
            if sha256(config_path) != identity['original_config_sha256'] or sha256(original_path) != identity['original_controller_state_sha256']:
                raise ValueError('original config/controller state changed during recovery')
            c.source_check(release, original)
            stage = state['stage']
            phase = 'confirm' if stage in ('plan_confirm','confirm_workers','confirm_collect') else 'pilot'
            if not state.get('job_id'):
                worker = stage.endswith('_workers')
                cli_stage = 'worker' if worker else {'plan_confirm':'plan-workers'}.get(stage,stage)
                if stage.endswith('_collect'):
                    cli_stage = 'collect'
                mapping = read_mapping(output,phase) if worker else None
                dependency = state.get('worker_job_id') if cli_stage == 'collect' else None
                argv = c.sbatch_args(scheduling,release,output,cli_stage,phase,mapping,dependency)
                state['submission_intent'] = dict(stage=stage,argv=argv)
                c.atomic_json(state_path,state)
                job_id = c.command(argv).split(';')[0]
                if not job_id.isdigit():
                    raise ValueError('unrecognized sbatch acknowledgement; intent retained')
                state.pop('submission_intent')
                state['history'].append(dict(stage=stage,argv=argv,job_id=job_id))
                state['job_id'] = job_id
                if worker:
                    state['worker_job_id'] = job_id
                    state['stage'] = phase + '_collect'
                    state['job_id'] = None
                c.atomic_json(state_path,state)
                if worker:
                    continue
            status = c.job_state(state['job_id'])
            if not c.finished(status):
                pause(min(config.get('poll_seconds',30),60))
                continue
            state['history'].append(dict(stage=stage,job_id=state['job_id'],status=status))
            state['job_id'] = None
            if status != 'COMPLETED':
                state['blocked_stage'] = stage.replace('_collect','_workers')
                state['stage'] = 'blocked'
                c.atomic_json(state_path,state)
                raise ValueError('serial recovery stage failed: ' + stage + '; inspect logs before --resume')
            state.pop('worker_job_id',None)
            state['stage'] = transitions[stage]
            c.atomic_json(state_path,state)
        return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release',required=True,type=Path)
    parser.add_argument('--config',required=True,type=Path)
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--resume',action='store_true')
    args = parser.parse_args()
    result = recover(args.release,args.config,args.dry_run,args.resume)
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
