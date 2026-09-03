from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

PINNED_MPT_COMMIT = "cbbb366393105d5cefc254dc9ed492d43da0711b"
DEFAULT_MPT_ROOT = Path("/opt/ai-short-form-v4-upstreams/MoneyPrinterTurbo")


def mpt_root() -> Path:
    return Path(os.environ.get("MPT_ROOT", DEFAULT_MPT_ROOT)).resolve()


def verify_upstream() -> Path:
    root = mpt_root()
    if not (root / "app").is_dir():
        raise RuntimeError(f"MoneyPrinterTurbo checkout not found at {root}")
    proc = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
    actual = proc.stdout.strip()
    if actual != PINNED_MPT_COMMIT:
        raise RuntimeError(f"MoneyPrinterTurbo commit mismatch: {actual} != {PINNED_MPT_COMMIT}")
    return root


def load_services():
    root = verify_upstream()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    from app.services import llm, material, subtitle, video, voice  # type: ignore
    from app.models.schema import VideoAspect, VideoConcatMode, VideoParams  # type: ignore
    return llm, material, subtitle, video, voice, VideoAspect, VideoConcatMode, VideoParams


def director_response(prompt: str, *, provider: str, model: str, base_url: str = "") -> str:
    llm, *_ = load_services()
    provider = provider.strip().lower()
    if not provider:
        raise ValueError("director provider is required")
    cfg: dict[str, Any] = {"llm_provider": provider}
    if model:
        cfg[f"{provider}_model_name"] = model
    if base_url:
        cfg[f"{provider}_base_url"] = base_url
    return llm._generate_response(prompt, app_config=cfg)  # pinned upstream adapter


def synthesize_edge(text: str, *, voice_name: str, output_file: str) -> float:
    *_, voice, _, _, _ = load_services()
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    maker = voice.tts(text=text, voice_name=voice_name, voice_rate=1.0, voice_file=str(path), voice_volume=1.0)
    if maker is None or not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError("MoneyPrinterTurbo Edge TTS did not produce audio")
    duration = float(voice.get_audio_duration(str(path)))
    if duration <= 0:
        raise RuntimeError("MoneyPrinterTurbo produced audio with invalid duration")
    return duration


def transcribe_whisper(audio_file: str, subtitle_file: str) -> list[dict[str, Any]]:
    _, _, subtitle, *_ = load_services()
    out = Path(subtitle_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    subtitle.create(audio_file=audio_file, subtitle_file=str(out))
    if not out.is_file() or out.stat().st_size <= 0:
        raise RuntimeError("MoneyPrinterTurbo Whisper did not produce subtitles")
    return subtitle.file_to_subtitles(str(out))


def download_ordered_stock(*, task_id: str, terms: list[str], audio_duration: float, source: str = "pexels", max_clip_duration: int = 5) -> list[str]:
    _, material, _, _, _, VideoAspect, VideoConcatMode, _ = load_services()
    if not terms:
        return []
    paths = material.download_videos(
        task_id=task_id,
        search_terms=terms,
        source=source,
        video_aspect=VideoAspect.portrait,
        video_concat_mode=VideoConcatMode.sequential,
        audio_duration=audio_duration,
        max_clip_duration=max_clip_duration,
        match_script_order=True,
    )
    return [str(path) for path in paths]
