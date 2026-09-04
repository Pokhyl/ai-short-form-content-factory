from __future__ import annotations

from typing import Any

PRIMARY_VISUAL_BASES = {
    "exact_media_annotation",
    "pictorial_primitive",
    "data_chart",
    "map",
    "screen_capture",
}


def validate_primary_motion_graphic(graphic: Any, *, beat_id: str) -> None:
    """Reject label/box diagrams used as the whole factual visual.

    Text, generic containers and arrows are acceptable as annotations, but a
    primary motion-graphic beat must declare a real pictorial/data/spatial
    basis. This prevents a renderer from replacing the requested visual with
    a presentation card made of labels and boxes.
    """
    if not isinstance(graphic, dict):
        raise ValueError(f"motion graphic {beat_id} must be an object")
    source = graphic.get("source")
    if not isinstance(source, dict):
        raise ValueError(f"motion graphic {beat_id} has no source metadata")
    basis = str(source.get("visual_basis") or "").strip()
    if basis not in PRIMARY_VISUAL_BASES:
        raise ValueError(
            f"motion graphic {beat_id} is not a valid primary visual: "
            f"visual_basis must be one of {sorted(PRIMARY_VISUAL_BASES)}; "
            "generic boxes/labels/arrows may only be secondary annotations"
        )


def validate_render_visual_track(track: Any) -> None:
    if not isinstance(track, list) or not track:
        raise ValueError("visual track must be a non-empty array")
    for item in track:
        if not isinstance(item, dict):
            raise ValueError("visual track item must be an object")
        if item.get("renderer") == "motion_graphic":
            validate_primary_motion_graphic(item.get("graphic"), beat_id=str(item.get("beat_id") or "unknown"))
