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
SOURCE_CLASSES = {"exact", "contextual", "constructed"}
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
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a number") from exc
    return out


def validate_timeline_payload(payload: Any) -> dict[str, Any]:
    """Validate structural product invariants for a vertical factual timeline.

    This deliberately does not attempt semantic ranking. It guarantees that a
    renderer cannot replace the primary visual with typography, silently use a
    generic fallback, create uncovered narration gaps, or fullscreen landscape
    evidence as if portrait orientation alone solved the composition problem.
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
    contextual_count = 0
    constructed_count = 0
    exact_count = 0

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

        primary = beat.get("primary_visual")
        if not isinstance(primary, dict):
            raise ValueError(f"beat {beat_id} requires primary_visual")

        mode = _text(primary.get("mode"), f"beat {beat_id}.primary_visual.mode")
        if mode == "text" or mode in {"hero_title", "text_card", "callout"}:
            raise ValueError(f"beat {beat_id} cannot replace the primary visual with text")
        if mode not in PRIMARY_MODES:
            raise ValueError(f"beat {beat_id} has invalid primary visual mode: {mode}")

        kind = _text(primary.get("kind"), f"beat {beat_id}.primary_visual.kind")
        if kind not in MEDIA_KINDS:
            raise ValueError(f"beat {beat_id} has invalid media kind: {kind}")

        source_class = _text(primary.get("source_class"), f"beat {beat_id}.primary_visual.source_class")
        if source_class == "generic_stock":
            raise ValueError(f"beat {beat_id} cannot use generic_stock as factual fallback")
        if source_class not in SOURCE_CLASSES:
            raise ValueError(f"beat {beat_id} has invalid source_class: {source_class}")

        visible_subject = _text(primary.get("visible_subject"), f"beat {beat_id}.primary_visual.visible_subject")
        if visible_subject.lower() in {"generic b-roll", "generic stock", "background footage"}:
            raise ValueError(f"beat {beat_id} visible_subject is not a factual visual obligation")

        layout = _text(primary.get("layout"), f"beat {beat_id}.primary_visual.layout")
        if layout not in LAYOUTS:
            raise ValueError(f"beat {beat_id} has invalid layout: {layout}")

        orientation = _text(primary.get("source_orientation"), f"beat {beat_id}.primary_visual.source_orientation")
        if orientation not in ORIENTATIONS:
            raise ValueError(f"beat {beat_id} has invalid source_orientation: {orientation}")
        if layout == "fullscreen" and kind in {"video", "photo"} and orientation not in {"portrait", "crop_safe"}:
            raise ValueError(f"beat {beat_id} cannot fullscreen {orientation} {kind}; use contain/pip/collage")

        if source_class == "contextual":
            contextual_count += 1
            _text(primary.get("context_justification"), f"beat {beat_id}.primary_visual.context_justification")
        elif source_class == "constructed":
            constructed_count += 1
            if mode not in {"diagram", "motion_graphic", "generated_image"}:
                raise ValueError(f"beat {beat_id} constructed visual requires diagram/motion_graphic/generated_image mode")
        else:
            exact_count += 1

        overlays = beat.get("overlays", [])
        if not isinstance(overlays, list):
            raise ValueError(f"beat {beat_id}.overlays must be an array")
        for overlay_index, overlay in enumerate(overlays, 1):
            if not isinstance(overlay, dict):
                raise ValueError(f"beat {beat_id}.overlays[{overlay_index}] must be an object")
            overlay_type = _text(overlay.get("type"), f"beat {beat_id}.overlays[{overlay_index}].type")
            if overlay_type not in {"caption", "label", "callout", "arrow", "highlight", "stat"}:
                raise ValueError(f"beat {beat_id} has invalid overlay type: {overlay_type}")
            if overlay_type in {"label", "callout", "stat"}:
                _text(overlay.get("text"), f"beat {beat_id}.overlays[{overlay_index}].text")

        previous_end = end

    if abs(previous_end - duration) > _EPSILON:
        raise ValueError(f"timeline must end at duration_seconds {duration:.3f}, got {previous_end:.3f}")

    return {
        "beat_count": len(raw_beats),
        "duration_seconds": duration,
        "exact_beats": exact_count,
        "contextual_beats": contextual_count,
        "constructed_beats": constructed_count,
    }
