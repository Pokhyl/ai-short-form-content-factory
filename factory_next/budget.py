"""Explicit next-only admission profile; never changes legacy budgets.

All Gemini calls share the same bounded preparation ledger, including
definite 503 retries. The extra nine calls cover one beat-count repair, up to
two length repairs, and six protected voice-correction calls.
These are maximum allocations, not an obligation to send provider requests.
"""
from material_first.operations import preparation_budgets

PROFILE='factory-next-measured-length-guard-v4'
EXTRA_GEMINI_CALLS=9
MIN_VOICE_CORRECTION_HEADROOM=6
# Worst case before voice: original draft/review, one beat-count correction,
# two length repairs, and six unused voice rewrite/review calls.
MIN_STORY_AND_VOICE_HEADROOM=11


def next_preparation_budgets(seconds):
    base=preparation_budgets(seconds)
    assert type(base.get('gemini')) is int and base['gemini']>0
    return {**base,'gemini':base['gemini']+EXTRA_GEMINI_CALLS}
