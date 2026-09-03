from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any

DEFAULT_VERTICAL_PROFILE = {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "video_codec": "h264",
    "audio_codec": "aac",
    "caption_safe_bottom_px": 320,
    "caption_max_width_ratio": 0.70,
}


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


def assemble_render_manifest(
    compiled_timeline: dict[str, Any],
    whisper_payload: dict[str, Any],
    *,
    audio_path: str | Path,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one deterministic renderer input from already validated V4 artifacts.

    This is intentionally a packaging/provenance boundary, not a semantic layer.
    Every factual exact-media beat must already be resolved and hash-verifiable;
    every constructed beat must already contain a compiled graphic. Word captions
    must come from the exact audio transcription used by the timeline.
    """
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
    if not (compiled_timeline.get("graphic_compilation") or {}).get("all_constructed_beats_compiled"):
        raise ValueError("constructed beats are not fully compiled")

    track: list[dict[str, Any]] = []
    for index, beat in enumerate(beats, 1):
        beat_id = str(beat.get("beat_id") or "").strip()
        if not beat_id:
            raise ValueError(f"beat {index} has no beat_id")
        primary = beat.get("primary_visual") or {}
        source_class = str(primary.get("source_class") or "")
        item = {
            "beat_id": beat_id,
            "start_seconds": float(beat["start_seconds"]),
            "end_seconds": float(beat["end_seconds"]),
            "layout": primary.get("layout"),
            "visible_subject": primary.get("visible_subject"),
            "overlays": copy.deepcopy(beat.get("overlays", [])),
        }
        if source_class == "exact":
            asset = beat.get("resolved_asset")
            if not isinstance(asset, dict):
                raise ValueError(f"exact beat {beat_id} has no resolved_asset")
            asset_path = Path(str(asset.get("local_path") or ""))
            if not asset_path.is_file():
                raise ValueError(f"exact beat {beat_id} asset file is missing: {asset_path}")
            expected_sha = str(asset.get("sha256") or "")
            actual_sha = sha256_file(asset_path)
            if actual_sha != expected_sha:
                raise ValueError(f"exact beat {beat_id} asset hash mismatch")
            item["renderer"] = "exact_media"
            item["asset"] = {
                "path": str(asset_path),
                "sha256": actual_sha,
                "width": asset.get("width"),
                "height": asset.get("height"),
                "license": asset.get("license"),
                "page_url": asset.get("page_url"),
                "attribution_required": bool(asset.get("attribution_required")),
                "artist": asset.get("artist"),
            }
        elif source_class == "constructed":
            graphic = beat.get("compiled_graphic")
            if not isinstance(graphic, dict) or not graphic.get("elements"):
                raise ValueError(f"constructed beat {beat_id} has no compiled_graphic")
            if (graphic.get("source") or {}).get("beat_id") != beat_id:
                raise ValueError(f"constructed beat {beat_id} graphic provenance mismatch")
            item["renderer"] = "motion_graphic"
            item["graphic"] = copy.deepcopy(graphic)
        else:
            raise ValueError(f"unsupported render source_class for beat {beat_id}: {source_class}")
        track.append(item)

    words = whisper_payload.get("words")
    if not isinstance(words, list) or not words:
        raise ValueError("Whisper word timestamps are required")
    captions: list[dict[str, Any]] = []
    previous_end = 0.0
    for index, word in enumerate(words, 1):
        if not isinstance(word, dict):
            raise ValueError(f"Whisper word {index} must be an object")
        start = float(word.get("start") or 0)
        end = float(word.get("end") or 0)
        text = str(word.get("word") or "").strip()
        if not text or end <= start or start < -0.001 or end > timeline_duration + 0.25:
            raise ValueError(f"invalid Whisper word timing at index {index}")
        if start + 0.05 < previous_end:
            raise ValueError(f"overlapping/out-of-order Whisper words at index {index}")
        previous_end = end
        captions.append({"text": text, "startMs": round(start * 1000), "endMs": round(end * 1000)})

    render_profile = dict(DEFAULT_VERTICAL_PROFILE)
    if profile:
        render_profile.update(profile)
    if int(render_profile.get("width", 0)) <= 0 or int(render_profile.get("height", 0)) <= 0:
        raise ValueError("invalid render dimensions")
    if int(render_profile.get("height")) <= int(render_profile.get("width")):
        raise ValueError("V4 short-form render profile must be portrait")

    return {
        "manifest_version": "v4-render-manifest-1",
        "duration_seconds": timeline_duration,
        "profile": render_profile,
        "audio": {
            "path": str(audio),
            "sha256": actual_audio_sha,
            "duration_seconds": whisper_duration,
        },
        "captions": {
            "source": "actual_audio_whisper_words",
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
