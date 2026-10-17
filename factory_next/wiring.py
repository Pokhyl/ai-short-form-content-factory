"""Connect the replacement pipeline to the existing bounded provider runtime.

Construction only: no network, budget reservation, job creation or provider
send occurs here. The caller must provision a fresh job with the existing
preparation ledger and an exclusive factory_next checkpoint before stepping.
"""
from pathlib import Path
from datetime import datetime
import time
from uuid import UUID

from factory_v3.worker_adapters import GoogleVoice
from .adapters import FactoryNextAdapters
from .media import MediaStages
from .preparation import PreparationStages
from .voice import VoiceStages


class ProviderResumeGate:
    """Read persisted evidence before resuming only budgeted preparation stages.

    Explicit 503/UNAVAILABLE was already validated by the PostgreSQL
    defer_preparation_call procedure. No HTTP provider send happens here.
    """

    def __init__(self, runtime, *, clock=None):
        self.runtime=runtime
        self.clock=clock or time.time

    def __call__(self, stage, context, receipt):
        if stage not in ('research','materials','story'):
            raise ValueError('provider resume forbidden for external media stage')
        if receipt.get('protocol')!='budgeted-explicit-503' or receipt.get('stage')!=stage:
            raise ValueError('deferral identity changed')
        prep=self.runtime.preparations
        snapshot=prep.snapshot(context['id'])
        if snapshot.get('status')!='preparing' or snapshot.get('source_revision')!=self.runtime.revision:
            raise ValueError('preparation terminal or revision mismatch')
        pending=prep.waiting(context['id'])
        if not isinstance(pending,dict) or not pending.get('retry_at'):
            raise ValueError('stored provider deferral missing')
        def timestamp(value):
            dt=datetime.fromisoformat(value)
            if dt.tzinfo is None or dt.utcoffset() is None:
                raise ValueError('provider retry timestamp lacks timezone')
            return dt.timestamp()
        saved_at=timestamp(receipt['retry_at'])
        database_at=timestamp(pending['retry_at'])
        if abs(database_at-saved_at)>0.001 or self.clock()<database_at:
            raise ValueError('provider deferral due time not confirmed')
        unknown=self.runtime.ledger._call(
            "SELECT count(*) FROM factory_v3.preparation_calls "
            "WHERE preparation_id=%s::uuid AND state IN ('started','unknown')",
            (context['id'],))
        if type(unknown) is not int or unknown!=0:
            raise ValueError('unknown provider operations block resume')
        claimed=prep.claim_run(context['id'])
        if not isinstance(claimed,dict) or claimed.get('busy') or claimed.get('cached'):
            raise ValueError('preparation is not due for resume')
        return True


def connected_adapters(runtime, job_id, *, preflight_gate=None):
    """Reuse the checked native gateway and persisted free-tier request budgets."""
    identity=str(UUID(str(job_id)))
    if not hasattr(runtime,'producer') or not hasattr(runtime,'gateway'):
        raise ValueError('trusted configured factory runtime required')
    producer=runtime.producer(identity)
    if not hasattr(producer,'operations') or not callable(producer.authorize):
        raise ValueError('bounded producer with billing gate required')
    # The existing operations object already wraps Gemini, search, downloads
    # and inspections in their durable preparation budget ledger.
    preparation=PreparationStages(runtime.root,producer.operations,producer.authorize)
    tts=GoogleVoice(lambda:'gateway-managed',runtime.gateway)
    voice=VoiceStages(runtime.root,tts,runtime.direct,runtime.ledger)
    media=MediaStages(runtime.root)
    return FactoryNextAdapters(
        preparation,voice,media,preflight_gate=preflight_gate,
        provider_resume_gate=ProviderResumeGate(runtime))
