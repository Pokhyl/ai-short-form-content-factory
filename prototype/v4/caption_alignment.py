from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any


def _norm(value: Any) -> str:
    text = unicodedata.normalize('NFKC', str(value or '')).casefold()
    return ''.join(ch for ch in text if ch.isalnum())


def _tokens(text: str) -> list[str]:
    return [x for x in re.findall(r'\S+', str(text or '').strip()) if _norm(x)]


def _similar(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(a=a, b=b, autojunk=False).ratio()


def _caption_item(text: str, word: dict[str, Any]) -> dict[str, Any]:
    return {
        'text': text,
        'startMs': round(float(word.get('start') or 0) * 1000),
        'endMs': round(float(word.get('end') or 0) * 1000),
    }


def align_scene_caption_words(script_text: str, audio_words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep exact-audio word timing while correcting display text from script.

    This follows the same principle as MoneyPrinterTurbo subtitle.correct(): the
    speech-ready script is authoritative text, while ASR is authoritative timing.
    Equal token counts are a direct one-to-one correction. For count mismatches,
    adjacent script tokens may merge onto one ASR word (for example a recognizer
    joining two spoken words), while unmatched collapsed forms such as a spoken
    year recognized as digits are retained from ASR rather than inventing timing.
    """
    script = _tokens(script_text)
    if not script or not audio_words:
        return []
    if len(script) == len(audio_words):
        return [_caption_item(token, word) for token, word in zip(script, audio_words)]

    out: list[dict[str, Any]] = []
    i = 0
    j = 0
    while i < len(script) and j < len(audio_words):
        s = _norm(script[i])
        a = _norm(audio_words[j].get('word'))
        if s == a or _similar(s, a) >= 0.80:
            out.append(_caption_item(script[i], audio_words[j]))
            i += 1
            j += 1
            continue

        merged = False
        for width in range(2, min(4, len(script) - i) + 1):
            joined = ''.join(_norm(x) for x in script[i:i + width])
            if joined == a or _similar(joined, a) >= 0.80:
                out.append(_caption_item(' '.join(script[i:i + width]), audio_words[j]))
                i += width
                j += 1
                merged = True
                break
        if merged:
            continue

        next_audio_norm = _norm(audio_words[j + 1].get('word')) if j + 1 < len(audio_words) else ''
        anchor = None
        if next_audio_norm:
            for si in range(i + 1, len(script)):
                if _norm(script[si]) == next_audio_norm:
                    anchor = si
                    break
        out.append(_caption_item(str(audio_words[j].get('word') or '').strip(), audio_words[j]))
        j += 1
        if anchor is not None:
            i = anchor
        else:
            i += 1

    while j < len(audio_words):
        out.append(_caption_item(str(audio_words[j].get('word') or '').strip(), audio_words[j]))
        j += 1
    return out


def build_script_aligned_captions(beats: list[dict[str, Any]], whisper_words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    captions: list[dict[str, Any]] = []
    for beat in beats:
        narration = str(beat.get('source_narration') or '').strip()
        if not narration:
            return []
        start = float(beat.get('start_seconds') or 0)
        end = float(beat.get('end_seconds') or 0)
        words = [
            word for word in whisper_words
            if float(word.get('start') or 0) >= start - 0.001 and float(word.get('start') or 0) < end - 0.001
        ]
        captions.extend(align_scene_caption_words(narration, words))
    return captions
