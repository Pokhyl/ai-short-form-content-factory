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
from .budget import PROFILE, MIN_VOICE_CORRECTION_HEADROOM, MIN_STORY_AND_VOICE_HEADROOM


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


def register_next(runtime, job_id, topic, language, seconds):
    """Use the existing immutable Runtime.create checks with next-only budget."""
    identity=str(UUID(str(job_id)))
    return runtime.create(identity,topic,language,seconds,
                          visual_validation_mode='gemini',_factory_next=True)


class NextBudgetGate:
    """Read-only admission; fail before an uncorrectable external voice send."""

    def __init__(self, runtime):
        self.runtime=runtime

    def __call__(self, stage, context):
        record=self.runtime.preparations.snapshot(context['id'])
        if (record.get('source_revision')!=self.runtime.revision or
                record.get('request',{}).get('factory_next_budget_profile')!=PROFILE):
            raise ValueError('factory_next immutable budget profile mismatch')
        if stage not in ('story','voice'):
            return
        receipt=self.runtime.ledger._call(
            "SELECT jsonb_build_object("
            "'limit', (SELECT (budgets->>'gemini')::int FROM factory_v3.preparations WHERE id=%s::uuid),"
            "'used', (SELECT count(*) FROM factory_v3.preparation_calls WHERE preparation_id=%s::uuid AND kind='gemini'),"
            "'unknown', (SELECT count(*) FROM factory_v3.preparation_calls WHERE preparation_id=%s::uuid AND state IN ('started','unknown')))",
            (context['id'],context['id'],context['id']))
        required=(MIN_STORY_AND_VOICE_HEADROOM if stage=='story'
                  else MIN_VOICE_CORRECTION_HEADROOM)
        if (not isinstance(receipt,dict) or
                type(receipt.get('limit')) is not int or
                type(receipt.get('used')) is not int or
                type(receipt.get('unknown')) is not int or
                receipt['limit']<0 or receipt['used']<0 or receipt['unknown']!=0 or
                receipt['limit']-receipt['used']<required):
            raise ValueError('insufficient reserved Gemini budget before '+stage)



def narrative_model_for(runtime, producer):
    """An opt-in private proof binds the additional fixed free-tier model."""
    from copy import copy
    from factory_v3.credential_http import NARRATIVE_MODEL
    settings=getattr(runtime,'settings',{})
    proof=settings.get('factory_next_narrative_proof')
    if proof is None:
        return None
    primary=settings.get('free_tier_proof',{})
    if (not isinstance(proof,dict) or proof.get('model')!=NARRATIVE_MODEL or
            proof.get('billing_enabled') is not False or
            proof.get('standard_free_tier') is not True or
            not isinstance(proof.get('verification_id'),str) or not proof['verification_id'] or
            not primary.get('project_id') or not primary.get('credential_sha256') or
            proof.get('project_id')!=primary['project_id'] or
            proof.get('credential_sha256')!=primary['credential_sha256']):
        raise ValueError('verified narrative free-tier proof required')
    model=copy(producer.operations.gemini)
    model.model=NARRATIVE_MODEL
    return model

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
    narrative=narrative_model_for(runtime,producer)
    preparation=PreparationStages(runtime.root,producer.operations,producer.authorize,narrative_model=narrative)
    preparation.variant_correction=narrative is not None
    tts=GoogleVoice(lambda:'gateway-managed',runtime.gateway)
    voice=VoiceStages(runtime.root,tts,runtime.direct,runtime.ledger)
    media=MediaStages(runtime.root)
    budget_gate=NextBudgetGate(runtime)
    def combined_preflight(stage, context):
        budget_gate(stage,context)
        if preflight_gate is not None:
            preflight_gate(stage,context)
    return FactoryNextAdapters(
        preparation,voice,media,preflight_gate=combined_preflight,
        provider_resume_gate=ProviderResumeGate(runtime))
