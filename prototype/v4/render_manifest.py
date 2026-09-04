from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any

from .visual_adequacy import validate_primary_motion_graphic
from .caption_alignment import build_script_aligned_captions

DEFAULT_VERTICAL_PROFILE = {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "video_codec": "h264",
    "audio_codec": "aac",
    "caption_safe_bottom_px": 320,
    "caption_max_width_ratio": 0.70,
}
_EPSILON = 0.002


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _duration(value: Any, field: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if out <= 0:
        raise ValueError(f"{field} must be positive")
    return out


def _verified_asset(node: dict[str, Any], visual_id: str) -> dict[str, Any]:
    asset = node.get("resolved_asset")
    if not isinstance(asset, dict):
        raise ValueError(f"exact visual {visual_id} has no resolved_asset")
    asset_path = Path(str(asset.get("local_path") or ""))
    if not asset_path.is_file():
        raise ValueError(f"exact visual {visual_id} asset file is missing: {asset_path}")
    expected_sha = str(asset.get("sha256") or "")
    actual_sha = sha256_file(asset_path)
    if actual_sha != expected_sha:
        raise ValueError(f"exact visual {visual_id} asset hash mismatch")
    return {
        "path": str(asset_path),
        "sha256": actual_sha,
        "width": asset.get("width"),
        "height": asset.get("height"),
        "license": asset.get("license"),
        "license_url": asset.get("license_url"),
        "page_url": asset.get("page_url"),
        "attribution_required": bool(asset.get("attribution_required")),
        "artist": asset.get("artist"),
        "credit": asset.get("credit"),
    }


def _render_item(node: dict[str, Any], *, visual_id: str, beat_id: str) -> dict[str, Any]:
    primary = node.get("primary_visual") or {}
    source_class = str(primary.get("source_class") or "")
    item: dict[str, Any] = {
        "visual_id": visual_id,
        "beat_id": beat_id,
        "shot_id": visual_id if visual_id != beat_id else None,
        "start_seconds": float(node["start_seconds"]),
        "end_seconds": float(node["end_seconds"]),
        "layout": primary.get("layout"),
        "visible_subject": primary.get("visible_subject"),
        "overlays": copy.deepcopy(node.get("overlays", [])),
    }
    if source_class == "exact":
        item["renderer"] = "exact_media"
        item["asset"] = _verified_asset(node, visual_id)
    elif source_class == "annotated_exact":
        item["asset"] = _verified_asset(node, visual_id)
        graphic = node.get("compiled_graphic")
        if not isinstance(graphic, dict) or not graphic.get("elements"):
            raise ValueError(f"annotated exact visual {visual_id} has no compiled_graphic")
        if (graphic.get("source") or {}).get("beat_id") != visual_id:
            raise ValueError(f"annotated exact visual {visual_id} graphic provenance mismatch")
        validate_primary_motion_graphic(graphic, beat_id=visual_id)
        item["renderer"] = "annotated_media"
        item["graphic"] = copy.deepcopy(graphic)
    elif source_class == "constructed":
        graphic = node.get("compiled_graphic")
        if not isinstance(graphic, dict) or not graphic.get("elements"):
            raise ValueError(f"constructed visual {visual_id} has no compiled_graphic")
        if (graphic.get("source") or {}).get("beat_id") != visual_id:
            raise ValueError(f"constructed visual {visual_id} graphic provenance mismatch")
        validate_primary_motion_graphic(graphic, beat_id=visual_id)
        item["renderer"] = "motion_graphic"
        item["graphic"] = copy.deepcopy(graphic)
    else:
        raise ValueError(f"unsupported render source_class for visual {visual_id}: {source_class}")
    return item


def assemble_render_manifest(
    compiled_timeline: dict[str, Any],
    whisper_payload: dict[str, Any],
    *,
    audio_path: str | Path,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(compiled_timeline, dict):
        raise ValueError("compiled_timeline must be an object")
    if not isinstance(whisper_payload, dict):
        raise ValueError("whisper_payload must be an object")
    timeline_duration = _duration(compiled_timeline.get("duration_seconds"), "timeline duration")
    provenance = compiled_timeline.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("timeline provenance is required")
    expected_audio_sha = str(provenance.get("audio_sha256") or "").strip()
    if len(expected_audio_sha) != 64:
        raise ValueError("timeline audio_sha256 is required")
    audio = Path(audio_path)
    if not audio.is_file() or audio.stat().st_size <= 0:
        raise ValueError(f"audio file missing or empty: {audio}")
    actual_audio_sha = sha256_file(audio)
    if actual_audio_sha != expected_audio_sha:
        raise ValueError(f"audio provenance mismatch: {actual_audio_sha} != {expected_audio_sha}")
    whisper_duration = _duration(whisper_payload.get("duration"), "Whisper duration")
    if abs(whisper_duration - timeline_duration) > 0.25:
        raise ValueError(f"Whisper/timeline duration mismatch: {whisper_duration:.3f} != {timeline_duration:.3f}")

    beats = compiled_timeline.get("beats")
    if not isinstance(beats, list) or not beats:
        raise ValueError("compiled timeline requires beats")
    if not (compiled_timeline.get("asset_resolution") or {}).get("all_exact_assets_hash_verified"):
        raise ValueError("exact assets are not fully hash-verified")

    render_nodes: list[tuple[str, str, dict[str, Any]]] = []
    for beat in beats:
        beat_id = str(beat.get("beat_id") or "").strip()
        if not beat_id:
            raise ValueError("compiled beat has no beat_id")
        shots = beat.get("shots")
        if isinstance(shots, list) and shots:
            for shot in shots:
                shot_id = str(shot.get("shot_id") or "").strip()
                if not shot_id:
                    raise ValueError(f"beat {beat_id} contains shot without shot_id")
                render_nodes.append((shot_id, beat_id, shot))
        else:
            render_nodes.append((beat_id, beat_id, beat))

    needs_graphics = any(
        str((node.get("primary_visual") or {}).get("source_class") or "") in {"constructed", "annotated_exact"}
        for _, _, node in render_nodes
    )
    if needs_graphics:
        graphic_info = compiled_timeline.get("graphic_compilation") or {}
        if not graphic_info.get("all_required_graphics_compiled", graphic_info.get("all_constructed_beats_compiled")):
            raise ValueError("required graphic visuals are not fully compiled")

    track: list[dict[str, Any]] = []
    previous_end = 0.0
    for visual_id, beat_id, node in render_nodes:
        item = _render_item(node, visual_id=visual_id, beat_id=beat_id)
        if abs(item["start_seconds"] - previous_end) > _EPSILON:
            raise ValueError(f"render visual gap/overlap before {visual_id}")
        if item["end_seconds"] <= item["start_seconds"]:
            raise ValueError(f"render visual {visual_id} has non-positive duration")
        previous_end = item["end_seconds"]
        track.append(item)
    if abs(previous_end - timeline_duration) > _EPSILON:
        raise ValueError("render visual track does not cover full audio duration")

    words = whisper_payload.get("words")
    if not isinstance(words, list) or not words:
        raise ValueError("Whisper word timestamps are required")
    previous_word_end = 0.0
    for index, word in enumerate(words, 1):
        if not isinstance(word, dict):
            raise ValueError(f"Whisper word {index} must be an object")
        start = float(word.get("start") or 0)
        end = float(word.get("end") or 0)
        text = str(word.get("word") or "").strip()
        if not text or end <= start or start < -0.001 or end > timeline_duration + 0.25:
            raise ValueError(f"invalid Whisper word timing at index {index}")
        if start + 0.05 < previous_word_end:
            raise ValueError(f"overlapping/out-of-order Whisper words at index {index}")
        previous_word_end = end

    captions = build_script_aligned_captions(beats, words)
    caption_source = "actual_audio_whisper_timing_script_text"
    if not captions:
        captions = [
            {"text": str(word.get("word") or "").strip(), "startMs": round(float(word.get("start") or 0) * 1000), "endMs": round(float(word.get("end") or 0) * 1000)}
            for word in words
        ]
        caption_source = "actual_audio_whisper_words"

    render_profile = dict(DEFAULT_VERTICAL_PROFILE)
    if profile:
        render_profile.update(profile)
    if int(render_profile.get("width", 0)) <= 0 or int(render_profile.get("height", 0)) <= 0:
        raise ValueError("invalid render dimensions")
    if int(render_profile.get("height")) <= int(render_profile.get("width")):
        raise ValueError("V4 short-form render profile must be portrait")

    return {
        "manifest_version": "v4-render-manifest-2",
        "duration_seconds": timeline_duration,
        "profile": render_profile,
        "audio": {"path": str(audio), "sha256": actual_audio_sha, "duration_seconds": whisper_duration},
        "captions": {
            "source": caption_source,
            "language": whisper_payload.get("language"),
            "probability": whisper_payload.get("probability"),
            "items": captions,
        },
        "visual_track": track,
        "provenance": {
            "script_sha256": provenance.get("script_sha256"),
            "audio_sha256": actual_audio_sha,
            "timing_source": provenance.get("timing_source"),
            "asset_resolver": "hash_verified_exact_media",
            "graphic_compiler": (compiled_timeline.get("graphic_compilation") or {}).get("compiler"),
        },
    }
