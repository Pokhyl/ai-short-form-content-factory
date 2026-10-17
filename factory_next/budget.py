"""Explicit next-only admission profile; never changes legacy budgets.

All Gemini calls share the same bounded preparation ledger, including
definite 503 retries. The extra five calls fund at most one schema-count repair
and two separately rewritten/re-reviewed natural narrations. These are maximum
allocations, not an obligation to send provider requests.
"""
from material_first.operations import preparation_budgets

PROFILE='factory-next-three-natural-attempts-v2'
EXTRA_GEMINI_CALLS=5
MIN_VOICE_CORRECTION_HEADROOM=4
# A story draft + independent review, optional one-shot count correction,
# plus four *unused* requests for two measured voice rewrites/reviews.
MIN_STORY_AND_VOICE_HEADROOM=7


def next_preparation_budgets(seconds):
    base=preparation_budgets(seconds)
    assert type(base.get('gemini')) is int and base['gemini']>0
    return {**base,'gemini':base['gemini']+EXTRA_GEMINI_CALLS}
