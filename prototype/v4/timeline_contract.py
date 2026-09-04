from __future__ import annotations

from typing import Any

PRIMARY_MODES = {
    "exact_media",
    "justified_context",
    "diagram",
    "motion_graphic",
    "generated_image",
}
MEDIA_KINDS = {"video", "photo", "diagram", "motion_graphic", "generated_image"}
SOURCE_CLASSES = {"exact", "annotated_exact", "contextual", "constructed"}
LAYOUTS = {"fullscreen", "contain", "pip", "collage"}
ORIENTATIONS = {"portrait", "landscape", "square", "crop_safe", "not_applicable"}
_EPSILON = 0.001


def _text(value: Any, field: str) -> str:
    out = str(value or "").strip()
    if not out:
        raise ValueError(f"{field} is required")
    return out


def _number(value: Any, field: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a number") from exc


def _validate_primary(primary: Any, label: str) -> str:
    if not isinstance(primary, dict):
        raise ValueError(f"{label} requires primary_visual")
    mode = _text(primary.get("mode"), f"{label}.primary_visual.mode")
    if mode == "text" or mode in {"hero_title", "text_card", "callout"}:
        raise ValueError(f"{label} cannot replace the primary visual with text")
    if mode not in PRIMARY_MODES:
        raise ValueError(f"{label} has invalid primary visual mode: {mode}")

    kind = _text(primary.get("kind"), f"{label}.primary_visual.kind")
    if kind not in MEDIA_KINDS:
        raise ValueError(f"{label} has invalid media kind: {kind}")

    source_class = _text(primary.get("source_class"), f"{label}.primary_visual.source_class")
    if source_class == "generic_stock":
        raise ValueError(f"{label} cannot use generic_stock as factual fallback")
    if source_class not in SOURCE_CLASSES:
        raise ValueError(f"{label} has invalid source_class: {source_class}")

    visible_subject = _text(primary.get("visible_subject"), f"{label}.primary_visual.visible_subject")
    if visible_subject.lower() in {"generic b-roll", "generic stock", "background footage"}:
        raise ValueError(f"{label} visible_subject is not a factual visual obligation")

    layout = _text(primary.get("layout"), f"{label}.primary_visual.layout")
    if layout not in LAYOUTS:
        raise ValueError(f"{label} has invalid layout: {layout}")

    orientation = _text(primary.get("source_orientation"), f"{label}.primary_visual.source_orientation")
    if orientation not in ORIENTATIONS:
        raise ValueError(f"{label} has invalid source_orientation: {orientation}")
    if layout == "fullscreen" and kind in {"video", "photo"} and orientation not in {"portrait", "crop_safe"}:
        raise ValueError(f"{label} cannot fullscreen {orientation} {kind}; use contain/pip/collage")

    if source_class == "contextual":
        _text(primary.get("context_justification"), f"{label}.primary_visual.context_justification")
    elif source_class == "constructed":
        if mode not in {"diagram", "motion_graphic", "generated_image"}:
            raise ValueError(f"{label} constructed visual requires diagram/motion_graphic/generated_image mode")
    elif source_class == "annotated_exact":
        if mode not in {"exact_media", "diagram", "motion_graphic"}:
            raise ValueError(f"{label} annotated_exact visual requires exact_media/diagram/motion_graphic mode")
    return source_class


def _validate_overlays(overlays: Any, label: str) -> None:
    if overlays is None:
        overlays = []
    if not isinstance(overlays, list):
        raise ValueError(f"{label}.overlays must be an array")
    for overlay_index, overlay in enumerate(overlays, 1):
        if not isinstance(overlay, dict):
            raise ValueError(f"{label}.overlays[{overlay_index}] must be an object")
        overlay_type = _text(overlay.get("type"), f"{label}.overlays[{overlay_index}].type")
        if overlay_type not in {"caption", "label", "callout", "arrow", "highlight", "stat"}:
            raise ValueError(f"{label} has invalid overlay type: {overlay_type}")
        if overlay_type in {"label", "callout", "stat"}:
            _text(overlay.get("text"), f"{label}.overlays[{overlay_index}].text")


def validate_timeline_payload(payload: Any) -> dict[str, Any]:
    """Validate semantic beats plus their TikTok editing shots.

    Semantic beats cover the whole narration. Optional shots subdivide a beat
    without changing its meaning and must cover that beat continuously. The
    same factual visual rules apply to every shot.
    """
    if not isinstance(payload, dict):
        raise ValueError("timeline payload must be an object")
    duration = _number(payload.get("duration_seconds"), "duration_seconds")
    if duration <= 0:
        raise ValueError("duration_seconds must be positive")
    raw_beats = payload.get("beats")
    if not isinstance(raw_beats, list) or not raw_beats:
        raise ValueError("beats must be a non-empty array")

    previous_end = 0.0
    seen_ids: set[str] = set()
    seen_shot_ids: set[str] = set()
    beat_counts = {"exact": 0, "annotated_exact": 0, "contextual": 0, "constructed": 0}
    shot_counts = {"exact": 0, "annotated_exact": 0, "contextual": 0, "constructed": 0}
    shot_total = 0

    for index, beat in enumerate(raw_beats, 1):
        if not isinstance(beat, dict):
            raise ValueError(f"beats[{index}] must be an object")
        beat_id = _text(beat.get("beat_id"), f"beats[{index}].beat_id")
        if beat_id in seen_ids:
            raise ValueError(f"duplicate beat_id: {beat_id}")
        seen_ids.add(beat_id)

        start = _number(beat.get("start_seconds"), f"beats[{index}].start_seconds")
        end = _number(beat.get("end_seconds"), f"beats[{index}].end_seconds")
        if end <= start:
            raise ValueError(f"beat {beat_id} must have positive duration")
        if abs(start - previous_end) > _EPSILON:
            raise ValueError(f"timeline gap/overlap before beat {beat_id}: expected {previous_end:.3f}, got {start:.3f}")

        source_class = _validate_primary(beat.get("primary_visual"), f"beat {beat_id}")
        beat_counts[source_class] += 1
        _validate_overlays(beat.get("overlays", []), f"beat {beat_id}")

        shots = beat.get("shots")
        if shots is not None:
            if not isinstance(shots, list) or not shots:
                raise ValueError(f"beat {beat_id}.shots must be a non-empty array")
            shot_previous_end = start
            for shot_index, shot in enumerate(shots, 1):
                if not isinstance(shot, dict):
                    raise ValueError(f"beat {beat_id}.shots[{shot_index}] must be an object")
                shot_id = _text(shot.get("shot_id"), f"beat {beat_id}.shots[{shot_index}].shot_id")
                if shot_id in seen_shot_ids:
                    raise ValueError(f"duplicate shot_id: {shot_id}")
                seen_shot_ids.add(shot_id)
                shot_start = _number(shot.get("start_seconds"), f"shot {shot_id}.start_seconds")
                shot_end = _number(shot.get("end_seconds"), f"shot {shot_id}.end_seconds")
                if shot_end <= shot_start:
                    raise ValueError(f"shot {shot_id} must have positive duration")
                if abs(shot_start - shot_previous_end) > _EPSILON:
                    raise ValueError(f"shot gap/overlap before {shot_id}: expected {shot_previous_end:.3f}, got {shot_start:.3f}")
                if shot_start < start - _EPSILON or shot_end > end + _EPSILON:
                    raise ValueError(f"shot {shot_id} must stay inside beat {beat_id}")
                shot_source = _validate_primary(shot.get("primary_visual"), f"shot {shot_id}")
                shot_counts[shot_source] += 1
                _validate_overlays(shot.get("overlays", []), f"shot {shot_id}")
                shot_total += 1
                shot_previous_end = shot_end
            if abs(shot_previous_end - end) > _EPSILON:
                raise ValueError(f"shots in beat {beat_id} must end at {end:.3f}, got {shot_previous_end:.3f}")
        previous_end = end

    if abs(previous_end - duration) > _EPSILON:
        raise ValueError(f"timeline must end at duration_seconds {duration:.3f}, got {previous_end:.3f}")

    return {
        "beat_count": len(raw_beats),
        "shot_count": shot_total,
        "duration_seconds": duration,
        "exact_beats": beat_counts["exact"] + beat_counts["annotated_exact"],
        "contextual_beats": beat_counts["contextual"],
        "constructed_beats": beat_counts["constructed"],
        "exact_shots": shot_counts["exact"] + shot_counts["annotated_exact"],
        "contextual_shots": shot_counts["contextual"],
        "constructed_shots": shot_counts["constructed"],
    }
