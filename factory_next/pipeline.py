"""Checkpointed replacement orchestration, independent of legacy preparation.

Adapters own source/media validation and bounded provider accounting. Completed
stage outputs are immutable. An interrupted claimed stage is never resent:
its receipt must be reconciled by an operator before any further execution.
"""
from contextlib import contextmanager
from copy import deepcopy
import fcntl
import hashlib
import json
import os
import time
from pathlib import Path
from uuid import UUID

from .timeline import compile_edit

STAGES=('research','materials','story','voice','alignment','edit','render','audit')
MAX_PRE_DISPATCH_DEFERRALS=3


class PreDispatchUnavailable(RuntimeError):
    """Verified provider unavailability BEFORE any stage operation was sent.

    Only the adapter's preflight(stage, context) may raise this exception.
    An error from the stage operation itself is always ambiguous and terminal.
    """
    def __init__(self, provider, retry_after_seconds):
        if not isinstance(provider,str) or not provider.strip():
            raise ValueError('pre-dispatch provider identity required')
        if type(retry_after_seconds) is not int or not 1<=retry_after_seconds<=3600:
            raise ValueError('bounded explicit retry-after seconds required')
        self.provider=provider.strip()
        self.retry_after_seconds=retry_after_seconds
        super().__init__('provider unavailable before stage dispatch')



def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,
                                    separators=(',',':'),allow_nan=False).encode()).hexdigest()


class ReconciliationRequired(RuntimeError):
    pass


class Pipeline:
    def __init__(self, root, adapters, revision, *, clock=None):
        self.root=Path(root);self.adapters=adapters;self.revision=revision
        self.clock=clock or time.time
        if len(revision)!=40 or any(c not in '0123456789abcdef' for c in revision):
            raise ValueError('exact code revision required')

    def directory(self, job_id):
        return self.root/str(UUID(str(job_id)))

    @contextmanager
    def locked(self, job_id):
        directory=self.directory(job_id)
        with (directory/'lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            yield directory

    def save(self, directory, state):
        temporary=directory/'state.tmp'
        with temporary.open('w') as stream:
            json.dump(state,stream,ensure_ascii=False,allow_nan=False)
            stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,directory/'state.json')
        descriptor=os.open(directory,os.O_RDONLY)
        try:os.fsync(descriptor)
        finally:os.close(descriptor)

    def create(self, job_id, topic, language, seconds):
        if not isinstance(topic,str) or not 1<=len(topic.strip())<=300:
            raise ValueError('bounded topic required')
        if language not in ('pl','en','ru','uk') or type(seconds) is not int or seconds not in (15,30,45,60):
            raise ValueError('unsupported language or duration')
        self.root.mkdir(parents=True,exist_ok=True)
        directory=self.directory(job_id);directory.mkdir(exist_ok=False)
        state={'version':'factory-next-v1','id':str(UUID(str(job_id))),'revision':self.revision,
               'request':{'topic':topic.strip(),'language':language,'seconds':seconds},
               'status':'ready','next_stage':STAGES[0],'outputs':{},'receipts':{}}
        self.save(directory,state)
        return deepcopy(state)

    def snapshot(self, job_id):
        return json.loads((self.directory(job_id)/'state.json').read_text())

    def step(self, job_id):
        with self.locked(job_id) as directory:
            state=self.snapshot(job_id)
            if state['revision']!=self.revision:raise ValueError('job belongs to another revision')
            for stage,output in state['outputs'].items():
                if fingerprint(output)!=state['receipts'].get(stage):
                    raise ValueError('completed stage output changed')
            if state['status']=='complete':return state
            if state['status'] not in ('ready','deferred'):
                raise ReconciliationRequired('claimed or failed stage cannot be repeated')
            stage=state['next_stage']
            expected=list(STAGES[:STAGES.index(stage)])
            if list(state['outputs'])!=expected:raise ValueError('nonconsecutive stage history')
            context={'id':state['id'],'request':deepcopy(state['request']),
                     'outputs':deepcopy(state['outputs'])}
            # A deferred preflight is safe to revisit because no stage call was
            # made. Unknown results and interrupted checks remain immutable.
            history=state.setdefault('preflight_deferrals',{})
            previous=history.get(stage,{})
            now=int(self.clock())
            if state['status']=='deferred':
                if not previous or previous.get('status')!='deferred':
                    raise ReconciliationRequired('deferred gate receipt missing')
                if now < previous['next_retry_at']:
                    return deepcopy(state)
            gate=getattr(self.adapters,'preflight',None)
            if gate is not None:
                # Crash during this gate must NOT silently dispatch later.
                state['status']='checking';self.save(directory,state)
                try:
                    gate(stage,deepcopy(context))
                except PreDispatchUnavailable as error:
                    attempts=previous.get('attempts',0)+1
                    exhausted=attempts>=MAX_PRE_DISPATCH_DEFERRALS
                    history[stage]={'attempts':attempts,'provider':error.provider,
                                    'retry_after_seconds':error.retry_after_seconds,
                                    'next_retry_at':now+error.retry_after_seconds,
                                    'status':'exhausted' if exhausted else 'deferred'}
                    state['status']='needs_attention' if exhausted else 'deferred'
                    if exhausted:state['error_type']='PreDispatchAttemptsExhausted'
                    self.save(directory,state)
                    return deepcopy(state)
                except BaseException as error:
                    state.update(status='needs_attention',error_type=type(error).__name__)
                    self.save(directory,state)
                    raise
                if previous:
                    history[stage]={**previous,'status':'resolved'}
            elif state['status']=='deferred':
                raise ReconciliationRequired('preflight adapter missing on deferred stage')
            state['status']='running';self.save(directory,state)
            try:
                if stage=='edit':
                    outputs=context['outputs']
                    if outputs['alignment']['audio_sha256'] != outputs['voice']['sha256']:
                        raise ValueError('alignment belongs to another audio file')
                    output=compile_edit(outputs['story']['scenes'],outputs['materials']['photos'],
                                        outputs['alignment']['timings'],outputs['voice']['duration_ms'],
                                        context['request']['seconds'])
                else:
                    output=getattr(self.adapters,stage)(context)
                if not isinstance(output,dict):raise ValueError('stage must return a receipt object')
                if stage=='audit' and output.get('passed') is not True:
                    raise ValueError('actual output audit did not pass')
                receipt=fingerprint(output)
            except BaseException as error:
                state.update(status='needs_attention',error_type=type(error).__name__)
                self.save(directory,state)
                raise
            state['outputs'][stage]=output;state['receipts'][stage]=receipt
            index=STAGES.index(stage)+1
            state.update(status='complete' if index==len(STAGES) else 'ready',
                         next_stage=None if index==len(STAGES) else STAGES[index])
            self.save(directory,state)
            return deepcopy(state)
