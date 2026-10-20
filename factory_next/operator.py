"""Operator-owned, checkpoint-safe local entrypoint for factory_next.

Run inside the separately built factory image, never as the legacy
production factory-v3-app entrypoint. No implicit timer or background
worker, no unbounded retries, no provider request replay after failure.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from uuid import UUID, uuid4

from factory_v3.runtime import Runtime, load_settings
from .pipeline import Pipeline
from .wiring import connected_adapters, register_next

MAX_STEPS=8


def result(state):
    outputs=state.get('outputs',{})
    receipt={'job_id':state['id'],
             'revision':state['revision'],
             'status':state['status'],
             'next_stage':state.get('next_stage'),
             'completed_stages':list(outputs)}
    if state.get('provider_wait_receipt'):
        receipt['provider_retry_at']=state['provider_wait_receipt'].get('retry_at')
    if state.get('error_type'):
        receipt['error_type']=state['error_type']
    if 'render' in outputs:
        receipt['video_sha256']=outputs['render'].get('sha256')
    if 'audit' in outputs:
        receipt['audit_passed']=outputs['audit'].get('passed') is True
    return receipt


def progress(pipeline, job_id, max_steps=MAX_STEPS):
    if type(max_steps) is not int or not 1<=max_steps<=MAX_STEPS:
        raise ValueError('step limit must be between 1 and 8')
    state=pipeline.snapshot(job_id)
    for _ in range(max_steps):
        if state['status']=='complete':
            return state
        if state['status'] not in ('ready','deferred'):
            # Never send from a running, checking, failed or uncertain job.
            raise ValueError('checkpoint requires manual reconciliation: '+state['status'])
        previous=state
        state=pipeline.step(job_id)
        if state['status']!='ready' or state==previous:
            return state
    return state


def run(argv=None, *, runtime_factory=None):
    parser=argparse.ArgumentParser(description='Checkpointed, budgeted factory_next operator')
    parser.add_argument('--data-root',default='/data')
    parser.add_argument('--settings',default='/run/factory-v3/settings.json')
    parser.add_argument('--steps',type=int,default=MAX_STEPS)
    command=parser.add_subparsers(dest='command',required=True)
    start=command.add_parser('start',help='register ONE unique new budgeted job and advance')
    start.add_argument('--topic',required=True)
    start.add_argument('--language',required=True,choices=('pl','en','ru','uk'))
    start.add_argument('--seconds',type=int,required=True,choices=(15,30,45,60))
    resume=command.add_parser('continue',help='advance existing receipt only when permitted')
    resume.add_argument('job_id')
    status=command.add_parser('status',help='read-only local checkpoint status')
    status.add_argument('job_id')
    args=parser.parse_args(argv)
    if not 1<=args.steps<=MAX_STEPS:
        parser.error('--steps must be between 1 and 8')
    revision=os.environ.get('FACTORY_V3_REVISION','')
    root=Path(args.data_root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError('existing dedicated /data media volume mount required')
    if len(revision)!=40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('exact built image revision required')
    checkpoint_root=root/'factory-next-states'

    if args.command=='status':
        job=str(UUID(args.job_id))
        # Status does not read credentials or contact any provider.
        state=Pipeline(checkpoint_root,None,revision).snapshot(job)
        print(json.dumps(result(state),ensure_ascii=False,sort_keys=True),flush=True)
        return 0

    settings=load_settings(args.settings)
    factory=runtime_factory or Runtime
    runtime=factory(settings,root,revision)
    if args.command=='start':
        job=str(uuid4())
        # Disclose the identifier BEFORE any external or database action.
        # Failed registration requires operator reconciliation, never retry ID.
        print(json.dumps({'new_job_id':job,'action':'registration_start'}),flush=True)
        registration=register_next(runtime,job,args.topic,args.language,args.seconds)
        if registration.get('created') is not True:
            raise ValueError('new job ID unexpectedly already registered')
        pipeline=Pipeline(checkpoint_root,connected_adapters(runtime,job),revision)
        pipeline.create(job,args.topic,args.language,args.seconds)
    else:
        job=str(UUID(args.job_id))
        pipeline=Pipeline(checkpoint_root,connected_adapters(runtime,job),revision)
        existing=pipeline.snapshot(job)
        if existing['revision']!=revision:
            raise ValueError('exact source revision mismatch; do not migrate checkpoint')
    state=progress(pipeline,job,args.steps)
    print(json.dumps(result(state),ensure_ascii=False,sort_keys=True),flush=True)
    return 0


def main():
    try:
        return run()
    except Exception as error:
        # Never reinterpret argparse --help/SystemExit(0) or Ctrl-C as
        # a failed provider operation. Do not expose secrets in logs.
        print(json.dumps({'status':'error',
            'error_type':type(error).__name__,
            'message':'execution stopped; inspect immutable checkpoint and ledger before retry'}),
            file=sys.stderr,flush=True)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
