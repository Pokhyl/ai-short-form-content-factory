"""Bound the fixed narrative model with an ordered end-to-end deadline."""
from .credential_http import NARRATIVE_MODEL

NARRATIVE_CALLER_SECONDS = 270
NARRATIVE_UPSTREAM_SECONDS = 240
GATEWAY_WORKFLOW_SECONDS = 300


def model_request_timeout(model):
    return NARRATIVE_CALLER_SECONDS if model == NARRATIVE_MODEL else 90


def upstream_timeout_ms(provider):
    return (NARRATIVE_UPSTREAM_SECONDS if provider == "gemini_narrative" else 120) * 1000
