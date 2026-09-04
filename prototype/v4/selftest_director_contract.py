from __future__ import annotations

import copy
from typing import Any

SHOT_RANGE: dict[int, tuple[int, int]] = {
    15: (5, 7),
    30: (8, 10),
    45: (10, 12),
    60: (12, 14),
}

_ALLOWED_MODES = {"exact_media", "stock"}
_CONTEXTUAL_PURPOSES = {"hook", "example", "transition"}
_PLACEHOLDER_MUST_SHOW = {"subject", "object", "actual subject", "actual object"}


def shot_target_text(duration: int) -> str:
    lo, hi = SHOT_RANGE[int(duration)]
    return f"{lo}-{hi}"


def normalize_director_visual_contract(raw: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(raw)
    for scene in out.get("scenes", []):
        purpose = str(scene.get("purpose") or "")
        shots = scene.get("shots") or []
        for shot in shots:
            query = str(shot.get("visual_query") or scene.get("visual_query") or "").strip()
            mode = str(shot.get("visual_mode") or scene.get("visual_mode") or "").strip()
            if mode == "stock" and purpose not in _CONTEXTUAL_PURPOSES:
                shot["visual_mode"] = "exact_media"
            visible = [str(v).strip().lower() for v in (shot.get("must_show") or []) if str(v).strip()]
            if (not visible or all(v in _PLACEHOLDER_MUST_SHOW for v in visible)) and query:
                shot["must_show"] = [query]
        if shots:
            scene["visual_mode"] = str(shots[0].get("visual_mode") or scene.get("visual_mode") or "exact_media")
            scene["visual_query"] = str(shots[0].get("visual_query") or scene.get("visual_query") or "")
            scene["must_show"] = list(shots[0].get("must_show") or scene.get("must_show") or [])
    return out


def validate_director_shot_contract(raw: dict[str, Any], duration: int) -> int:
    if int(duration) not in SHOT_RANGE:
        raise ValueError(f"unsupported duration: {duration}")

    total = 0
    shot_ids: set[str] = set()
    scene_shot_counts: list[int] = []

    for scene in raw.get("scenes", []):
        purpose = str(scene.get("purpose") or "")
        shots = scene.get("shots")
        if not isinstance(shots, list) or not shots:
            raise ValueError(f"scene {scene.get('scene_id')} has no shots")

        reconstructed = " ".join(str(x.get("narration") or "").strip() for x in shots)
        if reconstructed != str(scene.get("narration") or "").strip():
            raise ValueError("shot narration does not reconstruct scene narration")

        scene_shot_counts.append(len(shots))
        for shot in shots:
            sid = str(shot.get("shot_id") or "").strip()
            if not sid or sid in shot_ids:
                raise ValueError(f"invalid or duplicate shot_id: {sid}")
            shot_ids.add(sid)

            mode = str(shot.get("visual_mode") or scene.get("visual_mode") or "").strip()
            if mode not in _ALLOWED_MODES:
                raise ValueError(f"invalid shot visual_mode: {mode}")
            if mode == "stock" and purpose not in _CONTEXTUAL_PURPOSES:
                raise ValueError(f"stock is not allowed for {purpose} scene {scene.get('scene_id')}")

            if not str(shot.get("visual_query") or "").strip() or not shot.get("must_show"):
                raise ValueError("invalid shot visual obligation")
            visible = [str(v).strip().lower() for v in (shot.get("must_show") or []) if str(v).strip()]
            if any(v in _PLACEHOLDER_MUST_SHOW for v in visible):
                raise ValueError(f"non-specific must_show in shot {sid}")

        total += len(shots)

    lo, hi = SHOT_RANGE[int(duration)]
    if total < lo:
        raise ValueError(f"shot count {total} is below duration minimum {lo} (normal target {lo}-{hi})")
    if len(scene_shot_counts) > 1 and all(n == 1 for n in scene_shot_counts):
        raise ValueError("semantic scenes collapsed to one editing shot each")
    return total
