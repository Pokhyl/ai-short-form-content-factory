"""Connect the replacement pipeline to the existing bounded provider runtime.

Construction only: no network, budget reservation, job creation or provider
send occurs here. The caller must provision a fresh job with the existing
preparation ledger and an exclusive factory_next checkpoint before stepping.
"""
from pathlib import Path
from uuid import UUID

from factory_v3.worker_adapters import GoogleVoice
from .adapters import FactoryNextAdapters
from .media import MediaStages
from .preparation import PreparationStages
from .voice import VoiceStages


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
    return FactoryNextAdapters(preparation,voice,media,preflight_gate=preflight_gate)
