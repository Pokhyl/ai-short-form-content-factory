from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
import wave
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

VOICE_NAMES = {
    "en": "en_US-norman-medium",
    "pl": "pl_PL-darkman-medium",
    "ru": "ru_RU-dmitri-medium",
    "uk": "uk_UA-mykyta-high",
}
WHISPER_REVISION = "536b0662742c02347bc0e980a01041f333bce120"


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or ""))).strip()


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(ch for ch in text if ch.isalnum())


def _tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"\S+", _clean(text)) if _norm(token)]


def _similar(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(a=a, b=b, autojunk=False).ratio()


def align_script_to_audio_words(script_text: str, audio_words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map canonical script text onto timestamps measured from the exact WAV.

    The known speech-ready script is authoritative text; faster-whisper is only
    authoritative for timestamps. We never divide duration or synthesize missing
    timestamps. Small tokenizer joins are accepted only when the recognized form
    is strongly similar to the joined canonical tokens; otherwise alignment fails
    closed.
    """
    script = _tokens(script_text)
    words = [word for word in audio_words if _norm(word.get("word"))]
    if not script or not words:
        raise ValueError("exact-audio alignment returned no lexical words")

    def timing(word: dict[str, Any]) -> tuple[float, float]:
        start = float(word.get("start") or 0)
        end = float(word.get("end") or 0)
        if start < 0 or end <= start:
            raise ValueError("exact-audio alignment contains invalid word timing")
        return start, end

    if len(script) == len(words):
        similarities = [_similar(_norm(token), _norm(word.get("word"))) for token, word in zip(script, words)]
        if min(similarities) < 0.45 or sum(similarities) / len(similarities) < 0.82:
            raise ValueError("exact-audio alignment text confidence is insufficient")
        out = []
        for token, word in zip(script, words):
            start, end = timing(word)
            out.append({"text": token, "start_seconds": start, "end_seconds": end})
        return out

    out: list[dict[str, Any]] = []
    i = 0
    j = 0
    while i < len(script) and j < len(words):
        source = _norm(script[i])
        heard = _norm(words[j].get("word"))
        similarity = _similar(source, heard)
        if source == heard or similarity >= 0.80:
            start, end = timing(words[j])
            out.append({"text": script[i], "start_seconds": start, "end_seconds": end})
            i += 1
            j += 1
            continue

        matched = False
        # Recognizer may join 2-4 canonical tokens into one timestamp. Only accept
        # a strong lexical match, so a genuinely missed word is never fabricated.
        for width in range(2, min(4, len(script) - i) + 1):
            joined = "".join(_norm(token) for token in script[i : i + width])
            score = _similar(joined, heard)
            if joined == heard or score >= 0.86:
                start, end = timing(words[j])
                out.append({"text": " ".join(script[i : i + width]), "start_seconds": start, "end_seconds": end})
                i += width
                j += 1
                matched = True
                break
        if matched:
            continue

        # Recognizer may split one canonical token into 2-3 timestamped words.
        # The combined heard text must still strongly match the canonical token.
        for width in range(2, min(3, len(words) - j) + 1):
            joined = "".join(_norm(words[j + offset].get("word")) for offset in range(width))
            score = _similar(source, joined)
            if source == joined or score >= 0.86:
                start, _ = timing(words[j])
                _, end = timing(words[j + width - 1])
                out.append({"text": script[i], "start_seconds": start, "end_seconds": end})
                i += 1
                j += width
                matched = True
                break
        if matched:
            continue
        raise ValueError(f"exact-audio alignment diverged at canonical token {i + 1} / audio word {j + 1}")

    if i != len(script) or j != len(words):
        raise ValueError("exact-audio alignment did not consume canonical script and audio words")
    if _clean(" ".join(item["text"] for item in out)) != _clean(script_text):
        raise ValueError("exact-audio alignment does not reconstruct canonical narration")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", required=True, choices=sorted(VOICE_NAMES))
    parser.add_argument("--text", required=True)
    parser.add_argument("--output-wav", required=True)
    parser.add_argument("--voice-dir", required=True)
    parser.add_argument("--whisper-dir", required=True)
    args = parser.parse_args()

    narration = _clean(args.text)
    if not narration or len(narration) > 12000:
        raise SystemExit("narration must contain 1-12000 characters")

    from piper import PiperVoice
    from faster_whisper import WhisperModel

    voice_name = VOICE_NAMES[args.language]
    voice_dir = Path(args.voice_dir)
    model_path = voice_dir / f"{voice_name}.onnx"
    config_path = voice_dir / f"{voice_name}.onnx.json"
    if not model_path.is_file() or not config_path.is_file():
        raise SystemExit(f"pinned Piper voice is missing: {voice_name}")

    output_path = Path(args.output_wav)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    synth_started = time.monotonic()
    voice = PiperVoice.load(str(model_path), config_path=str(config_path))
    with wave.open(str(output_path), "wb") as wav_file:
        voice.synthesize(narration, wav_file)
    synth_seconds = time.monotonic() - synth_started

    with wave.open(str(output_path), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        frame_count = wav_file.getnframes()
    if sample_rate <= 0 or channels != 1 or sample_width != 2 or frame_count <= 0:
        raise SystemExit("Piper produced an invalid PCM WAV")
    duration_seconds = frame_count / sample_rate

    align_started = time.monotonic()
    whisper = WhisperModel(
        args.whisper_dir,
        device="cpu",
        compute_type="int8",
        cpu_threads=2,
        num_workers=1,
    )
    segments, info = whisper.transcribe(
        str(output_path),
        language=args.language,
        beam_size=5,
        word_timestamps=True,
        vad_filter=False,
        condition_on_previous_text=True,
        initial_prompt=narration,
    )
    segments = list(segments)
    audio_words = [
        {"start": float(word.start), "end": float(word.end), "word": str(word.word).strip()}
        for segment in segments
        for word in (segment.words or [])
        if str(word.word).strip()
    ]
    aligned_words = align_script_to_audio_words(narration, audio_words)
    align_seconds = time.monotonic() - align_started

    if not aligned_words or aligned_words[-1]["end_seconds"] > duration_seconds + 0.25:
        raise SystemExit("faster-whisper timing lies outside Piper WAV")
    if _clean(" ".join(word["text"] for word in aligned_words)) != narration:
        raise SystemExit("canonical script reconstruction failed")

    print(json.dumps({
        "provider": "self_hosted_piper",
        "model": "piper-tts-1.2.0",
        "voice": voice_name,
        "alignment_provider": "faster_whisper",
        "alignment_model": f"Systran/faster-whisper-small@{WHISPER_REVISION}",
        "alignment_runtime": "faster-whisper-1.2.1-cpu-int8",
        "detected_language": str(info.language),
        "detected_language_probability": float(info.language_probability),
        "source_duration_seconds": duration_seconds,
        "source_sample_rate": sample_rate,
        "source_channels": channels,
        "source_sample_width": sample_width,
        "synthesis_seconds": round(synth_seconds, 3),
        "alignment_seconds": round(align_seconds, 3),
        "asr_word_count": len(audio_words),
        "caption_item_count": len(aligned_words),
        "words": aligned_words,
    }, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
