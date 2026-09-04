from __future__ import annotations

from typing import Any


def parse_media_selections(payload: dict[str, Any], shot_ids: list[str]) -> dict[str, str | None]:
    if not isinstance(payload, dict):
        raise ValueError("media selector payload must be an object")

    expected = set(shot_ids)
    candidate = payload.get("selections") if "selections" in payload else payload
    if not isinstance(candidate, dict):
        raise ValueError("media selector selections must be an object")

    actual = set(candidate)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"media selector keys mismatch: missing={missing}, extra={extra}")

    out: dict[str, str | None] = {}
    for sid in shot_ids:
        value = candidate[sid]
        if value is None:
            out[sid] = None
            continue
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"invalid media selection for {sid}")
        out[sid] = value.strip()
    return out
