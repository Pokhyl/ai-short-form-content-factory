"""Explicit next-only admission profile; never changes legacy budgets.

All Gemini calls share the same bounded preparation ledger, including
definite 503 retries. The extra three calls fund at most one schema-count
repair and a rewritten/re-reviewed natural narration. These are maximum
allocations, not an obligation to send provider requests.
"""
from material_first.operations import preparation_budgets

PROFILE='factory-next-bounded-corrections-v1'
EXTRA_GEMINI_CALLS=3
MIN_VOICE_CORRECTION_HEADROOM=2
# A story draft + independent review, optional one-shot count correction,
# plus two *unused* requests for a subsequent measured voice rewrite/review.
MIN_STORY_AND_VOICE_HEADROOM=5


def next_preparation_budgets(seconds):
    base=preparation_budgets(seconds)
    assert type(base.get('gemini')) is int and base['gemini']>0
    return {**base,'gemini':base['gemini']+EXTRA_GEMINI_CALLS}
