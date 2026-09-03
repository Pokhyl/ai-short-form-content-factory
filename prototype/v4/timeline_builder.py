from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .timeline_contract import validate_timeline_payload


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def compile_segment_timeline(
    *,
    whisper_payload: dict[str, Any],
    visual_obligations: list[dict[str, Any]],
    script_text: str,
    audio_sha256: str,
) -> dict[str, Any]:
    """Compile a continuous visual timeline from actual Whisper segment starts.

    Visual obligations contain semantics/representation only. They do not carry
    invented timestamps. Timing comes from the exact audio transcription. Any
    silence between spoken segments remains covered by the previous visual beat.
    """
    segments = whisper_payload.get('segments')
    if not isinstance(segments, list) or not segments:
        raise ValueError('whisper payload requires non-empty segments')
    if len(visual_obligations) != len(segments):
        raise ValueError(
            f'visual obligations must match Whisper segment count: '
            f'{len(visual_obligations)} != {len(segments)}'
        )

    duration = float(whisper_payload.get('duration') or 0)
    if duration <= 0:
        duration = max(float(segment.get('end') or 0) for segment in segments)
    if duration <= 0:
        raise ValueError('Whisper duration must be positive')

    starts: list[float] = []
    for index, segment in enumerate(segments):
        start = float(segment.get('start') or 0)
        if index == 0:
            start = 0.0
        if starts and start <= starts[-1]:
            raise ValueError('Whisper segment starts must increase strictly')
        starts.append(start)

    beats: list[dict[str, Any]] = []
    for index, (segment, obligation) in enumerate(zip(segments, visual_obligations), 1):
        if not isinstance(obligation, dict):
            raise ValueError(f'visual_obligations[{index}] must be an object')
        primary = obligation.get('primary_visual')
        if not isinstance(primary, dict):
            raise ValueError(f'visual_obligations[{index}] requires primary_visual')
        end = starts[index] if index < len(starts) else duration
        beats.append(
            {
                'beat_id': str(obligation.get('beat_id') or f'B{index}'),
                'start_seconds': round(starts[index - 1], 3),
                'end_seconds': round(end, 3),
                'source_segment_index': index - 1,
                'source_transcript': str(segment.get('text') or '').strip(),
                'primary_visual': primary,
                'overlays': obligation.get('overlays', [{'type': 'caption'}]),
            }
        )

    timeline: dict[str, Any] = {
        'duration_seconds': round(duration, 3),
        'provenance': {
            'script_sha256': sha256_text(script_text.strip()),
            'audio_sha256': audio_sha256,
            'timing_source': 'actual_audio_whisper_segments',
        },
        'beats': beats,
    }
    timeline['contract'] = validate_timeline_payload(timeline)
    return timeline
