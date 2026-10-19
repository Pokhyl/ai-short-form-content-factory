"""Strict, read-only eligibility checks for recovering exhausted Gemini 503 calls.

Never equate a failed stage with permission to resend an unknown provider call.
This module performs no writes, sends or budget reservations.
"""
from factory_v3.preparation import model_unavailable_receipt

def inspect_exhausted_503(*, checkpoint, preparation, calls, gemini_budget):
    """Return a safe-to-consider verdict, never authorization to dispatch.

    calls must contain all durable preparation-call rows, including unknown claims.
    """
    if checkpoint.get("status") != "needs_attention" or checkpoint.get("error_type") != "ModelUnavailable":
        return {"eligible": False, "reason": "not_explicit_model_unavailable"}
    if checkpoint.get("next_stage") not in ("research", "materials", "story"):
        return {"eligible": False, "reason": "stage_not_replay_safe"}
    if checkpoint.get("revision") != preparation.get("source_revision") or preparation.get("status") != "preparing":
        return {"eligible": False, "reason": "revision_or_preparation_mismatch"}
    if any(row.get("state") in ("started", "unknown") for row in calls):
        return {"eligible": False, "reason": "unreconciled_provider_call"}
    gemini = [row for row in calls if row.get("kind") == "gemini"]
    if len(gemini) >= gemini_budget:
        return {"eligible": False, "reason": "gemini_budget_exhausted"}
    failed = [row for row in gemini if row.get("state") == "failed" and row.get("error_code") == "ModelUnavailable"]
    if len(failed) < 3 or not all(model_unavailable_receipt(row.get("response")) for row in failed):
        return {"eligible": False, "reason": "unverified_provider_failure"}
    return {"eligible": True, "reason": "verified_503_with_remaining_budget",
            "remaining_gemini_calls": gemini_budget - len(gemini)}
