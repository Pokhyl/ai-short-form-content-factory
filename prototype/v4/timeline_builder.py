from __future__ import annotations

import hashlib
import re
import unicodedata
from difflib import SequenceMatcher
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


def _normalize_token(value: Any) -> str:
    text = unicodedata.normalize('NFKC', str(value or '')).casefold()
    return ''.join(ch for ch in text if ch.isalnum())


def _text_tokens(text: str) -> list[str]:
    return [token for token in re.findall(r'\S+', text.strip()) if _normalize_token(token)]


def _script_to_audio_map(script_tokens: list[str], audio_words: list[dict[str, Any]]) -> dict[int, int]:
    script_norm = [_normalize_token(token) for token in script_tokens]
    audio_norm = [_normalize_token(word.get('word')) for word in audio_words]
    matcher = SequenceMatcher(a=script_norm, b=audio_norm, autojunk=False)
    mapping: dict[int, int] = {}
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            mapping[block.a + offset] = block.b + offset
    return mapping


def _scene_start_from_alignment(
    *,
    scene_start_token: int,
    scene_end_token: int,
    script_to_audio: dict[int, int],
    audio_words: list[dict[str, Any]],
    scene_index: int,
) -> float:
    if scene_index == 0:
        return 0.0
    probe_end = min(scene_end_token, scene_start_token + 5)
    candidates = [script_to_audio[i] for i in range(scene_start_token, probe_end) if i in script_to_audio]
    if not candidates:
        candidates = [script_to_audio[i] for i in range(scene_start_token, scene_end_token) if i in script_to_audio]
    if not candidates:
        raise ValueError(f'cannot align semantic scene {scene_index + 1} to Whisper words')
    return float(audio_words[min(candidates)].get('start') or 0)


def compile_segment_timeline(
    *,
    whisper_payload: dict[str, Any],
    visual_obligations: list[dict[str, Any]],
    script_text: str,
    audio_sha256: str,
) -> dict[str, Any]:
    """Compile semantic scenes and internal shots against exact-audio word timing."""
    if not isinstance(visual_obligations, list) or not visual_obligations:
        raise ValueError('visual_obligations must be a non-empty array')
    words = whisper_payload.get('words')
    if not isinstance(words, list) or not words:
        raise ValueError('whisper payload requires non-empty word timestamps')

    duration = float(whisper_payload.get('duration') or 0)
    if duration <= 0:
        duration = max(float(word.get('end') or 0) for word in words)
    if duration <= 0:
        raise ValueError('Whisper duration must be positive')

    narrations: list[str] = []
    for index, obligation in enumerate(visual_obligations, 1):
        if not isinstance(obligation, dict):
            raise ValueError(f'visual_obligations[{index}] must be an object')
        narration = str(obligation.get('narration') or '').strip()
        if not narration:
            raise ValueError(f'visual_obligations[{index}] requires semantic narration')
        primary = obligation.get('primary_visual')
        if not isinstance(primary, dict):
            raise ValueError(f'visual_obligations[{index}] requires primary_visual')
        narrations.append(narration)

    normalized_script = script_text.strip()
    if ' '.join(narrations) != normalized_script:
        raise ValueError('visual obligation narration must reconstruct script_text exactly')

    script_tokens: list[str] = []
    scene_ranges: list[tuple[int, int]] = []
    for narration in narrations:
        start = len(script_tokens)
        script_tokens.extend(_text_tokens(narration))
        scene_ranges.append((start, len(script_tokens)))
    if not script_tokens:
        raise ValueError('script_text has no alignable tokens')

    script_to_audio = _script_to_audio_map(script_tokens, words)
    matched_ratio = len(script_to_audio) / len(script_tokens)
    if matched_ratio < 0.60:
        raise ValueError(f'script/Whisper word alignment coverage too low: {matched_ratio:.3f}')

    starts: list[float] = []
    for scene_index, (start_token, end_token) in enumerate(scene_ranges):
        start = _scene_start_from_alignment(
            scene_start_token=start_token,
            scene_end_token=end_token,
            script_to_audio=script_to_audio,
            audio_words=words,
            scene_index=scene_index,
        )
        if starts and start <= starts[-1]:
            raise ValueError('aligned semantic scene starts must increase strictly')
        starts.append(start)

    beats: list[dict[str, Any]] = []
    for index, obligation in enumerate(visual_obligations, 1):
        start = starts[index - 1]
        end = starts[index] if index < len(starts) else duration
        transcript_words = [
            str(word.get('word') or '').strip()
            for word in words
            if float(word.get('start') or 0) >= start - 0.001 and float(word.get('start') or 0) < end - 0.001
        ]
        beat = {
            'beat_id': str(obligation.get('beat_id') or f'B{index}'),
            'start_seconds': round(start, 3),
            'end_seconds': round(end, 3),
            'source_scene_index': index - 1,
            'source_narration': narrations[index - 1],
            'source_transcript': ' '.join(transcript_words).strip(),
            'primary_visual': obligation['primary_visual'],
            'overlays': obligation.get('overlays', [{'type': 'caption'}]),
        }
        raw_shots = obligation.get('shots')
        if raw_shots is not None:
            if not isinstance(raw_shots, list) or not raw_shots:
                raise ValueError(f'visual_obligations[{index}].shots must be a non-empty array')
            shot_narrations: list[str] = []
            for shot_index, shot in enumerate(raw_shots, 1):
                if not isinstance(shot, dict):
                    raise ValueError(f'visual_obligations[{index}].shots[{shot_index}] must be an object')
                shot_narration = str(shot.get('narration') or '').strip()
                if not shot_narration:
                    raise ValueError(f'visual_obligations[{index}].shots[{shot_index}] requires narration')
                if not isinstance(shot.get('primary_visual'), dict):
                    raise ValueError(f'visual_obligations[{index}].shots[{shot_index}] requires primary_visual')
                shot_narrations.append(shot_narration)
            if ' '.join(shot_narrations) != narrations[index - 1]:
                raise ValueError(f'visual_obligations[{index}].shots narration must reconstruct scene narration exactly')

            scene_token_start, _scene_token_end = scene_ranges[index - 1]
            shot_ranges: list[tuple[int, int]] = []
            cursor = scene_token_start
            for shot_narration in shot_narrations:
                shot_start_token = cursor
                cursor += len(_text_tokens(shot_narration))
                shot_ranges.append((shot_start_token, cursor))

            shot_starts: list[float] = []
            for shot_index, (shot_start_token, shot_end_token) in enumerate(shot_ranges):
                if shot_index == 0:
                    shot_start = start
                else:
                    shot_start = _scene_start_from_alignment(
                        scene_start_token=shot_start_token,
                        scene_end_token=shot_end_token,
                        script_to_audio=script_to_audio,
                        audio_words=words,
                        scene_index=1,
                    )
                if shot_starts and shot_start <= shot_starts[-1]:
                    raise ValueError(f'aligned shot starts must increase strictly inside beat {beat["beat_id"]}')
                if shot_start < start - 0.001 or shot_start >= end - 0.001:
                    raise ValueError(f'aligned shot start is outside beat {beat["beat_id"]}')
                shot_starts.append(shot_start)

            timed_shots: list[dict[str, Any]] = []
            for shot_index, raw_shot in enumerate(raw_shots, 1):
                shot_start = shot_starts[shot_index - 1]
                shot_end = shot_starts[shot_index] if shot_index < len(shot_starts) else end
                timed_shots.append({
                    'shot_id': str(raw_shot.get('shot_id') or f'{beat["beat_id"]}-S{shot_index}'),
                    'start_seconds': round(shot_start, 3),
                    'end_seconds': round(shot_end, 3),
                    'source_narration': shot_narrations[shot_index - 1],
                    'primary_visual': raw_shot['primary_visual'],
                    'overlays': raw_shot.get('overlays', [{'type': 'caption'}]),
                })
            beat['shots'] = timed_shots
        beats.append(beat)

    timeline: dict[str, Any] = {
        'duration_seconds': round(duration, 3),
        'provenance': {
            'script_sha256': sha256_text(normalized_script),
            'audio_sha256': audio_sha256,
            'timing_source': 'actual_audio_whisper_word_alignment',
            'alignment_coverage': round(matched_ratio, 6),
        },
        'beats': beats,
    }
    timeline['contract'] = validate_timeline_payload(timeline)
    return timeline
