from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import base64
import binascii
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request


DATA_ROOT = Path("/data")
VOICEOVER_ROOT = DATA_ROOT / "voiceovers"
VOICEOVER_CANDIDATE_ROOT = DATA_ROOT / "voiceover-candidates"
ALIGNMENT_ROOT = DATA_ROOT / "alignments"
VISUAL_ROOT = DATA_ROOT / "visuals"
RENDER_ROOT = DATA_ROOT / "renders"
WHISPER_CLI = Path("/opt/whisper/whisper-cli")
WHISPER_MODEL = Path("/models/ggml-small.bin")
WHISPER_IMAGE_DIGEST = (
    "sha256:9cfbaf11ef5bec57ec9cade6af7ed991ab5e32b01a6e40db3380a12363336e11"
)
MAX_WHISPER_TERMINAL_OVERRUN_MS = 1000

EXPECTED_MODEL_SHA256 = (
    "1be3a9b2063867b937e64e2ec7483364a79917e157fa98c5d94b5c1fffea987b"
)
MAX_JSON_BODY_BYTES = 20 * 1024 * 1024
MAX_VISUAL_BYTES = 80 * 1024 * 1024
MAX_VISION_PREVIEW_BYTES = 3 * 1024 * 1024
MAX_VISION_PREVIEW_TOTAL_BYTES = 8 * 1024 * 1024
VISION_PREVIEW_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
WIKIMEDIA_DOWNLOAD_LOCK = threading.Lock()
WIKIMEDIA_LAST_DOWNLOAD_AT = 0.0
WIKIMEDIA_MIN_DOWNLOAD_INTERVAL_SECONDS = 8.0
WIKIMEDIA_PREVIEW_DOWNLOAD_LOCK = threading.Lock()
WIKIMEDIA_PREVIEW_LAST_DOWNLOAD_AT = 0.0
WIKIMEDIA_PREVIEW_MIN_DOWNLOAD_INTERVAL_SECONDS = 1.0
ALIGNMENT_EXECUTION_LOCK = threading.Lock()
VISUAL_MEDIA_TYPES = {"photo", "video", "diagram"}
VISUAL_PROVIDERS = {"pixabay", "pexels", "wikimedia"}
VISUAL_MIME_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "video/mp4": "mp4",
    "video/webm": "webm",
}
JOB_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
    r"[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-"
    r"[0-9a-fA-F]{12}$"
)
LANGUAGE_CODES = {"en", "pl", "ru", "uk"}
ALIGNMENT_NUMBER_VALUES = {
    # English
    "zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,
    "eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12,"thirteen":13,
    "fourteen":14,"fifteen":15,"sixteen":16,"seventeen":17,"eighteen":18,
    "nineteen":19,"twenty":20,"thirty":30,"forty":40,"fifty":50,"sixty":60,
    "seventy":70,"eighty":80,"ninety":90,"hundred":100,"thousand":1000,
    # Polish
    "zero":0,"jeden":1,"jedna":1,"jedno":1,"dwa":2,"dwie":2,"trzy":3,
    "cztery":4,"pięć":5,"piec":5,"sześć":6,"szesc":6,"siedem":7,"osiem":8,
    "dziewięć":9,"dziewiec":9,"dziesięć":10,"dziesiec":10,
    "jedenaście":11,"jedenascie":11,"dwanaście":12,"dwanascie":12,
    "trzynaście":13,"trzynascie":13,"czternaście":14,"czternascie":14,
    "piętnaście":15,"pietnascie":15,"szesnaście":16,"szesnascie":16,
    "siedemnaście":17,"siedemnascie":17,"osiemnaście":18,"osiemnascie":18,
    "dziewiętnaście":19,"dziewietnascie":19,"dwadzieścia":20,"dwadziescia":20,
    "trzydzieści":30,"trzydziesci":30,"czterdzieści":40,"czterdziesci":40,
    "pięćdziesiąt":50,"piecdziesiat":50,"sześćdziesiąt":60,"szescdziesiat":60,
    "siedemdziesiąt":70,"siedemdziesiat":70,"osiemdziesiąt":80,
    "osiemdziesiat":80,"dziewięćdziesiąt":90,"dziewiecdziesiat":90,
    "sto":100,"tysiąc":1000,"tysiac":1000,
    # Russian
    "ноль":0,"один":1,"одна":1,"одно":1,"два":2,"две":2,"три":3,"четыре":4,
    "пять":5,"шесть":6,"семь":7,"восемь":8,"девять":9,"десять":10,
    "одиннадцать":11,"двенадцать":12,"тринадцать":13,"четырнадцать":14,
    "пятнадцать":15,"шестнадцать":16,"семнадцать":17,"восемнадцать":18,
    "девятнадцать":19,"двадцать":20,"тридцать":30,"сорок":40,"пятьдесят":50,
    "шестьдесят":60,"семьдесят":70,"восемьдесят":80,"девяносто":90,
    "сто":100,"тысяча":1000,"тысяч":1000,
    # Ukrainian
    "нуль":0,"один":1,"одна":1,"одне":1,"два":2,"дві":2,"три":3,"чотири":4,
    "п’ять":5,"п'ять":5,"шість":6,"сім":7,"вісім":8,"дев’ять":9,"дев'ять":9,
    "десять":10,"одинадцять":11,"дванадцять":12,"тринадцять":13,
    "чотирнадцять":14,"п’ятнадцять":15,"п'ятнадцять":15,"шістнадцять":16,
    "сімнадцять":17,"вісімнадцять":18,"дев’ятнадцять":19,"дев'ятнадцять":19,
    "двадцять":20,"тридцять":30,"сорок":40,"п’ятдесят":50,"п'ятдесят":50,
    "шістдесят":60,"сімдесят":70,"вісімдесят":80,"дев’яносто":90,
    "дев'яносто":90,"сто":100,"тисяча":1000,"тисяч":1000,
}

# Common grammatical inflections of cardinal numbers in the supported languages.
# They canonicalize to the same numeric value without collapsing different values.
ALIGNMENT_NUMBER_VALUES.update({
    # Polish
    "jednego":1,"jednej":1,"jednemu":1,"jednym":1,
    "dwóch":2,"dwoch":2,"dwóm":2,"dwom":2,"dwoma":2,
    "trzech":3,"trzem":3,"trzema":3,
    "czterech":4,"czterem":4,"czterema":4,
    "pięciu":5,"pieciu":5,"sześciu":6,"szesciu":6,"siedmiu":7,
    "ośmiu":8,"osmiu":8,"dziewięciu":9,"dziewieciu":9,
    "dziesięciu":10,"dziesieciu":10,
    "jedenastu":11,"dwunastu":12,"trzynastu":13,"czternastu":14,
    "piętnastu":15,"pietnastu":15,"szesnastu":16,"siedemnastu":17,
    "osiemnastu":18,"dziewiętnastu":19,"dziewietnastu":19,
    "dwudziestu":20,"trzydziestu":30,"czterdziestu":40,
    "pięćdziesięciu":50,"piecdziesieciu":50,
    "sześćdziesięciu":60,"szescdziesieciu":60,
    "siedemdziesięciu":70,"siedemdziesieciu":70,
    "osiemdziesięciu":80,"osiemdziesieciu":80,
    "dziewięćdziesięciu":90,"dziewiecdziesieciu":90,
    "stu":100,"tysiąca":1000,"tysiaca":1000,
    "tysięcy":1000,"tysiecy":1000,
    # Russian
    "одного":1,"одной":1,"одному":1,"одним":1,"одном":1,
    "двух":2,"двум":2,"двумя":2,
    "трех":3,"трёх":3,"трем":3,"трём":3,"тремя":3,
    "четырех":4,"четырёх":4,"четырем":4,"четырём":4,"четырьмя":4,
    "пяти":5,"шести":6,"семи":7,"восьми":8,"девяти":9,"десяти":10,
    "одиннадцати":11,"двенадцати":12,"тринадцати":13,"четырнадцати":14,
    "пятнадцати":15,"шестнадцати":16,"семнадцати":17,"восемнадцати":18,
    "девятнадцати":19,"двадцати":20,"тридцати":30,"сорока":40,
    "пятидесяти":50,"шестидесяти":60,"семидесяти":70,
    "восьмидесяти":80,"девяноста":90,"ста":100,
    "тысячи":1000,"тысячу":1000,"тысяче":1000,"тысячей":1000,
    # Ukrainian
    "одній":1,
    "двох":2,"двом":2,"двома":2,
    "трьох":3,"трьом":3,"трьома":3,
    "чотирьох":4,"чотирьом":4,"чотирма":4,
    "п’яти":5,"п'яти":5,"шести":6,"семи":7,"восьми":8,
    "дев’яти":9,"дев'яти":9,"десяти":10,
    "одинадцяти":11,"дванадцяти":12,"тринадцяти":13,
    "чотирнадцяти":14,"п’ятнадцяти":15,"п'ятнадцяти":15,
    "шістнадцяти":16,"сімнадцяти":17,"вісімнадцяти":18,
    "дев’ятнадцяти":19,"дев'ятнадцяти":19,
    "двадцяти":20,"тридцяти":30,"п’ятдесяти":50,"п'ятдесяти":50,
    "шістдесяти":60,"сімдесяти":70,"вісімдесяти":80,
    "дев’яноста":90,"дев'яноста":90,
    "тисячі":1000,"тисячу":1000,
})
_MODEL_SHA256_CACHE = None


def ffmpeg_version():
    result = subprocess.run(
        ["ffmpeg", "-version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.stdout.splitlines()[0]


def ffprobe_audio(path: Path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:stream=codec_type,codec_name,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    payload = json.loads(result.stdout)
    streams = payload.get("streams") or []
    audio_streams = [
        stream for stream in streams
        if stream.get("codec_type") == "audio"
    ]

    if len(audio_streams) != 1:
        raise ValueError("voiceover must contain exactly one audio stream")

    audio = audio_streams[0]
    codec = str(audio.get("codec_name") or "")
    if codec != "mp3":
        raise ValueError(f"voiceover codec must be mp3, received {codec or 'unknown'}")

    duration_seconds = float((payload.get("format") or {}).get("duration") or 0)
    sample_rate = int(audio.get("sample_rate") or 0)
    channels = int(audio.get("channels") or 0)

    if duration_seconds <= 0:
        raise ValueError("voiceover duration must be positive")
    if sample_rate <= 0:
        raise ValueError("voiceover sample rate must be positive")
    if channels <= 0:
        raise ValueError("voiceover channel count must be positive")

    return {
        "codec": codec,
        "duration_ms": round(duration_seconds * 1000),
        "sample_rate": sample_rate,
        "channels": channels,
    }


def file_sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def whisper_model_sha256():
    global _MODEL_SHA256_CACHE

    if _MODEL_SHA256_CACHE is not None:
        return _MODEL_SHA256_CACHE

    if not WHISPER_MODEL.is_file():
        raise ValueError("whisper model is missing")

    digest = file_sha256(WHISPER_MODEL)
    if digest != EXPECTED_MODEL_SHA256:
        raise ValueError(
            "whisper model SHA256 mismatch: "
            f"expected {EXPECTED_MODEL_SHA256}, received {digest}"
        )

    _MODEL_SHA256_CACHE = digest
    return digest


def _alignment_lexemes(value):
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    # Whisper may preserve an apostrophe in the segment transcript while
    # dropping it at token boundaries (for example Ukrainian в'язкою).
    # Apostrophes are punctuation, not lexical content, so remove common
    # apostrophe variants before both transcript and token normalization.
    normalized = re.sub(r"['’ʼ‘]", "", normalized)
    return re.findall(
        r"\d+|[^\W\d_]+",
        normalized,
        flags=re.UNICODE,
    )


def _number_words_to_int(words):
    current = 0
    total = 0
    for word in words:
        value = ALIGNMENT_NUMBER_VALUES[word]
        if value == 100:
            current = max(1, current) * 100
        elif value == 1000:
            total += max(1, current) * 1000
            current = 0
        else:
            current += value
    return total + current


def _canonical_alignment_lexemes(lexemes):
    out = []
    index = 0
    while index < len(lexemes):
        token = lexemes[index]
        if token.isdigit():
            out.append(str(int(token)))
            index += 1
            continue

        if token in ALIGNMENT_NUMBER_VALUES:
            end = index + 1
            while end < len(lexemes) and lexemes[end] in ALIGNMENT_NUMBER_VALUES:
                end += 1
            out.append(str(_number_words_to_int(lexemes[index:end])))
            index = end
            continue

        out.append(token)
        index += 1
    return out


def normalize_alignment_text(value):
    return "".join(_canonical_alignment_lexemes(_alignment_lexemes(value)))

def _lexical_tokens(whisper_payload):
    raw_rows = []
    pending_boundary = True

    for segment_index, segment in enumerate(
        whisper_payload.get("transcription") or []
    ):
        segment_boundary = True
        for token in segment.get("tokens") or []:
            token_text = str(token.get("text") or "")
            stripped = token_text.strip()

            if stripped.startswith("[_") and stripped.endswith("]"):
                pending_boundary = True
                continue

            lexemes = _alignment_lexemes(token_text)
            if not lexemes:
                if stripped:
                    pending_boundary = True
                continue

            offsets = token.get("offsets") or {}
            try:
                start_ms = int(offsets.get("from"))
                end_ms = int(offsets.get("to"))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "whisper lexical token is missing numeric offsets"
                ) from exc

            if start_ms < 0 or end_ms < start_ms:
                raise ValueError("whisper lexical token has invalid offsets")

            starts_word = bool(re.match(r"\s", token_text))
            raw_rows.append(
                {
                    "text": token_text,
                    "lexemes": lexemes,
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "segment_index": segment_index,
                    "starts_word": (
                        starts_word or pending_boundary or segment_boundary
                    ),
                }
            )
            pending_boundary = False
            segment_boundary = False

    if not raw_rows:
        raise ValueError("whisper returned no lexical tokens")

    # Whisper tokens are model subwords, not guaranteed lexical words.
    # Rejoin adjacent subword pieces before semantic normalization so a
    # lexical item has the same representation in transcript text and
    # token timing data.
    word_rows = []
    current = None
    for row in raw_rows:
        if current is None or row["starts_word"]:
            if current is not None:
                word_rows.append(current)
            current = {
                "text": row["text"],
                "start_ms": row["start_ms"],
                "end_ms": row["end_ms"],
                "segment_index": row["segment_index"],
            }
        else:
            current["text"] += row["text"]
            current["end_ms"] = row["end_ms"]

    if current is not None:
        word_rows.append(current)

    for row in word_rows:
        row["lexemes"] = _alignment_lexemes(row["text"])

    rows = []
    index = 0
    while index < len(word_rows):
        row = word_rows[index]
        lexemes = row["lexemes"]

        if lexemes and all(
            token in ALIGNMENT_NUMBER_VALUES for token in lexemes
        ):
            end = index + 1
            merged_lexemes = list(lexemes)
            while end < len(word_rows):
                next_lexemes = word_rows[end]["lexemes"]
                if not next_lexemes or not all(
                    token in ALIGNMENT_NUMBER_VALUES
                    for token in next_lexemes
                ):
                    break
                merged_lexemes.extend(next_lexemes)
                end += 1

            rows.append(
                {
                    "text": "".join(
                        word_rows[pos]["text"]
                        for pos in range(index, end)
                    ),
                    "normalized": str(
                        _number_words_to_int(merged_lexemes)
                    ),
                    "start_ms": row["start_ms"],
                    "end_ms": word_rows[end - 1]["end_ms"],
                }
            )
            index = end
            continue

        token_normalized = "".join(
            _canonical_alignment_lexemes(lexemes)
        )
        if token_normalized:
            rows.append(
                {
                    "text": row["text"],
                    "normalized": token_normalized,
                    "start_ms": row["start_ms"],
                    "end_ms": row["end_ms"],
                }
            )
        index += 1

    if not rows:
        raise ValueError("whisper returned no lexical tokens")

    return rows

def _build_scene_timings(
    narration,
    scenes,
    whisper_payload,
    audio_duration_ms,
):
    if not isinstance(narration, str) or not narration.strip():
        raise ValueError("narration is required")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("scenes must be a non-empty array")

    expected_normalized = normalize_alignment_text(narration)
    if not expected_normalized:
        raise ValueError("normalized narration is empty")

    whisper_segments = whisper_payload.get("transcription") or []
    transcript = "".join(
        str(segment.get("text") or "")
        for segment in whisper_segments
    ).strip()
    transcript_normalized = normalize_alignment_text(transcript)
    if not transcript_normalized:
        raise ValueError("normalized whisper transcript is empty")

    tokens = _lexical_tokens(whisper_payload)
    token_normalized = "".join(token["normalized"] for token in tokens)

    if token_normalized != transcript_normalized:
        raise ValueError(
            "whisper lexical tokens do not reconstruct the normalized transcript"
        )

    raw_lexical_end_ms = tokens[-1]["end_ms"]
    terminal_overrun_ms = max(0, raw_lexical_end_ms - audio_duration_ms)
    if terminal_overrun_ms > MAX_WHISPER_TERMINAL_OVERRUN_MS:
        raise ValueError(
            "whisper lexical timing exceeds audio duration beyond tolerance: "
            f"{terminal_overrun_ms}ms"
        )

    scene_joined = " ".join(
        str(scene.get("narration") or "").strip()
        for scene in scenes
    )
    if normalize_alignment_text(scene_joined) != expected_normalized:
        raise ValueError("scene narrations do not reconstruct the final narration")

    matcher = difflib.SequenceMatcher(
        a=expected_normalized,
        b=transcript_normalized,
        autojunk=False,
    )
    matching_blocks = [
        block
        for block in matcher.get_matching_blocks()
        if block.size > 0
    ]

    matched_chars = sum(block.size for block in matching_blocks)
    global_coverage = matched_chars / len(expected_normalized)

    if global_coverage < 0.95:
        raise ValueError(
            "global lexical alignment coverage below 0.95: "
            f"{global_coverage:.4f}"
        )

    token_ranges = []
    char_cursor = 0
    for token in tokens:
        start_char = char_cursor
        end_char = start_char + len(token["normalized"])
        token_ranges.append(
            {
                **token,
                "start_char": start_char,
                "end_char": end_char,
            }
        )
        char_cursor = end_char

    scene_timings = []
    expected_cursor = 0
    previous_end_ms = 0

    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            raise ValueError(f"scene {index} must be an object")

        scene_uuid = str(scene.get("scene_uuid") or "").strip().lower()
        scene_key = str(scene.get("scene_key") or "").strip()
        scene_narration = str(scene.get("narration") or "").strip()

        if not JOB_ID_RE.fullmatch(scene_uuid):
            raise ValueError(f"scene {index} has invalid scene_uuid")
        if not scene_key:
            raise ValueError(f"scene {index} has empty scene_key")

        scene_normalized = normalize_alignment_text(scene_narration)
        if not scene_normalized:
            raise ValueError(f"scene {scene_key} has empty narration")

        scene_start_char = expected_cursor
        scene_end_char = scene_start_char + len(scene_normalized)

        if expected_normalized[scene_start_char:scene_end_char] != scene_normalized:
            raise ValueError(f"scene {scene_key} is not contiguous in narration")

        scene_matched_chars = 0
        matched_actual_spans = []

        for block in matching_blocks:
            overlap_start = max(scene_start_char, block.a)
            overlap_end = min(scene_end_char, block.a + block.size)
            if overlap_end <= overlap_start:
                continue

            span_size = overlap_end - overlap_start
            scene_matched_chars += span_size

            actual_start = block.b + (overlap_start - block.a)
            actual_end = actual_start + span_size
            matched_actual_spans.append((actual_start, actual_end))

        scene_coverage = scene_matched_chars / len(scene_normalized)
        if scene_coverage < 0.85:
            raise ValueError(
                f"scene {scene_key} lexical coverage below 0.85: "
                f"{scene_coverage:.4f}"
            )

        overlapping = [
            token
            for token in token_ranges
            if any(
                token["end_char"] > span_start
                and token["start_char"] < span_end
                for span_start, span_end in matched_actual_spans
            )
        ]

        if not overlapping:
            raise ValueError(f"scene {scene_key} has no matched lexical timing coverage")

        start_ms = overlapping[0]["start_ms"]
        raw_end_ms = overlapping[-1]["end_ms"]
        end_ms = min(raw_end_ms, audio_duration_ms)

        if start_ms < previous_end_ms:
            raise ValueError(f"scene {scene_key} timing is not monotonic")
        if start_ms >= audio_duration_ms:
            raise ValueError(f"scene {scene_key} starts beyond audio duration")
        if end_ms <= start_ms:
            raise ValueError(f"scene {scene_key} timing has non-positive duration")

        scene_timings.append(
            {
                "scene_uuid": scene_uuid,
                "scene_key": scene_key,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "coverage": round(scene_coverage, 6),
            }
        )

        previous_end_ms = end_ms
        expected_cursor = scene_end_char

    if expected_cursor != len(expected_normalized):
        raise ValueError("scene timing coverage does not reach narration end")

    return {
        "transcript": transcript,
        "normalized_match": transcript_normalized == expected_normalized,
        "alignment_method": "whisper_token_sequence_match",
        "global_coverage": round(global_coverage, 6),
        "lexical_token_count": len(tokens),
        "lexical_start_ms": tokens[0]["start_ms"],
        "lexical_end_ms": min(raw_lexical_end_ms, audio_duration_ms),
        "lexical_end_ms_raw": raw_lexical_end_ms,
        "terminal_overrun_ms": terminal_overrun_ms,
        "scene_timings": scene_timings,
    }


def run_local_alignment(
    audio_path: Path,
    language_code: str,
    narration: str,
    scenes,
    audio_duration_ms: int,
    work_dir: Path,
):
    if language_code not in LANGUAGE_CODES:
        raise ValueError("unsupported alignment language")
    if not WHISPER_CLI.is_file():
        raise ValueError("whisper-cli is missing")

    whisper_model_sha256()

    wav_path = work_dir / "input.wav"
    output_base = work_dir / "whisper"
    output_json = work_dir / "whisper.json"

    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-y",
            "-v",
            "error",
            "-i",
            str(audio_path),
            "-ar",
            "16000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(wav_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )

    subprocess.run(
        [
            str(WHISPER_CLI),
            "-m",
            str(WHISPER_MODEL),
            "-f",
            str(wav_path),
            "-l",
            language_code,
            "-sow",
            "-ojf",
            "-of",
            str(output_base),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=240,
    )

    if not output_json.is_file():
        raise ValueError("whisper did not create full JSON output")

    with output_json.open("r", encoding="utf-8") as handle:
        whisper_payload = json.load(handle)

    summary = _build_scene_timings(
        narration,
        scenes,
        whisper_payload,
        audio_duration_ms,
    )

    return whisper_payload, summary


def _write_json_fsync(path: Path, payload):
    encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    fd = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o640,
    )

    with os.fdopen(fd, "wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())


def _visual_host_allowed(provider, hostname):
    host = str(hostname or "").strip().lower().rstrip(".")
    if not host:
        return False

    if provider == "pixabay":
        return host == "pixabay.com" or host.endswith(".pixabay.com")
    if provider == "pexels":
        return host == "pexels.com" or host.endswith(".pexels.com")
    if provider == "wikimedia":
        return host in {"upload.wikimedia.org", "thumb.wikimedia.org"}

    return False


def _validate_visual_url(provider, value):
    if provider not in VISUAL_PROVIDERS:
        raise ValueError("unsupported visual provider")

    parsed = urllib.parse.urlparse(str(value or "").strip())
    if parsed.scheme.lower() != "https":
        raise ValueError("visual download URL must use https")
    if parsed.username or parsed.password:
        raise ValueError("visual download URL must not contain user info")
    if parsed.port not in (None, 443):
        raise ValueError("visual download URL uses a non-HTTPS port")
    if not _visual_host_allowed(provider, parsed.hostname):
        raise ValueError("visual download host is not allowed")

    return parsed.geturl()



def _fetch_visual_preview_inner(provider, preview_url):
    safe_url = _validate_visual_url(provider, preview_url)
    request = urllib.request.Request(
        safe_url,
        headers={
            "User-Agent": "ai-short-form-content-factory/1.0",
            "Accept": "image/jpeg,image/png,image/webp",
        },
        method="GET",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        final_url = response.geturl()
        _validate_visual_url(provider, final_url)

        content_type = str(
            response.headers.get("Content-Type") or ""
        ).split(";", 1)[0].strip().lower()
        if content_type not in VISION_PREVIEW_MIME_TYPES:
            raise ValueError(
                "visual preview must be jpeg, png or webp"
            )

        raw_length = response.headers.get("Content-Length")
        if raw_length:
            try:
                content_length = int(raw_length)
            except ValueError as exc:
                raise ValueError("invalid preview Content-Length") from exc
            if content_length <= 0 or content_length > MAX_VISION_PREVIEW_BYTES:
                raise ValueError("visual preview size is outside allowed bounds")

        data = response.read(MAX_VISION_PREVIEW_BYTES + 1)
        if not data:
            raise ValueError("visual preview is empty")
        if len(data) > MAX_VISION_PREVIEW_BYTES:
            raise ValueError("visual preview exceeds maximum allowed size")

    return {
        "mime_type": content_type,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "data_base64": base64.b64encode(data).decode("ascii"),
        "final_url": final_url,
    }


def fetch_visual_preview(provider, preview_url):
    global WIKIMEDIA_PREVIEW_LAST_DOWNLOAD_AT

    if provider != "wikimedia":
        return _fetch_visual_preview_inner(provider, preview_url)

    with WIKIMEDIA_PREVIEW_DOWNLOAD_LOCK:
        now = time.monotonic()
        wait_seconds = (
            WIKIMEDIA_PREVIEW_MIN_DOWNLOAD_INTERVAL_SECONDS
            - (now - WIKIMEDIA_PREVIEW_LAST_DOWNLOAD_AT)
        )
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        try:
            return _fetch_visual_preview_inner(provider, preview_url)
        finally:
            WIKIMEDIA_PREVIEW_LAST_DOWNLOAD_AT = time.monotonic()



def ffprobe_visual(path: Path, media_type: str):
    if media_type not in VISUAL_MEDIA_TYPES:
        raise ValueError("unsupported visual media type")

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,format_name:stream=codec_type,codec_name,width,height",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    payload = json.loads(result.stdout)
    streams = payload.get("streams") or []
    visual_streams = [
        stream
        for stream in streams
        if stream.get("codec_type") == "video"
        and int(stream.get("width") or 0) > 0
        and int(stream.get("height") or 0) > 0
    ]

    if not visual_streams:
        raise ValueError("visual asset has no valid video/image stream")

    stream = visual_streams[0]
    width = int(stream.get("width") or 0)
    height = int(stream.get("height") or 0)
    codec = str(stream.get("codec_name") or "").strip().lower()

    if width <= 0 or height <= 0 or not codec:
        raise ValueError("visual asset stream metadata is invalid")

    raw_duration = (payload.get("format") or {}).get("duration")
    duration_ms = None
    if media_type == "video":
        try:
            duration_ms = round(float(raw_duration or 0) * 1000)
        except (TypeError, ValueError) as exc:
            raise ValueError("video duration is invalid") from exc

        if duration_ms <= 0:
            raise ValueError("video duration must be positive")

    return {
        "width": width,
        "height": height,
        "codec": codec,
        "duration_ms": duration_ms,
        "format_name": str((payload.get("format") or {}).get("format_name") or ""),
    }


def download_visual_asset(
    provider,
    download_url,
    media_type,
    final_dir: Path,
):
    global WIKIMEDIA_LAST_DOWNLOAD_AT

    if provider != "wikimedia":
        return _download_visual_asset_inner(
            provider,
            download_url,
            media_type,
            final_dir,
        )

    with WIKIMEDIA_DOWNLOAD_LOCK:
        now = time.monotonic()
        wait_seconds = (
            WIKIMEDIA_MIN_DOWNLOAD_INTERVAL_SECONDS
            - (now - WIKIMEDIA_LAST_DOWNLOAD_AT)
        )
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        try:
            return _download_visual_asset_inner(
                provider,
                download_url,
                media_type,
                final_dir,
            )
        finally:
            WIKIMEDIA_LAST_DOWNLOAD_AT = time.monotonic()


def _download_visual_asset_inner(
    provider,
    download_url,
    media_type,
    final_dir: Path,
):
    if media_type not in VISUAL_MEDIA_TYPES:
        raise ValueError("unsupported visual media type")

    safe_url = _validate_visual_url(provider, download_url)

    if provider == "wikimedia":
        parsed_url = urllib.parse.urlsplit(safe_url)
        safe_url = urllib.parse.urlunsplit(
            (
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                "",
                "",
            )
        )
        safe_url = _validate_visual_url(provider, safe_url)

    request = urllib.request.Request(
        safe_url,
        headers={
            "User-Agent": "ai-short-form-content-factory/1.0",
            "Accept": "*/*",
        },
        method="GET",
    )

    temp_path = final_dir / ".download"

    response = None
    for attempt in range(1, 4):
        try:
            response = urllib.request.urlopen(request, timeout=60)
            break
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt >= 3:
                raise

            retry_after = str(exc.headers.get("Retry-After") or "").strip()
            try:
                wait_seconds = int(retry_after)
            except ValueError:
                wait_seconds = 10 if attempt == 1 else 25

            wait_seconds = max(1, min(wait_seconds, 45))
            time.sleep(wait_seconds)

    if response is None:
        raise ValueError("visual download produced no HTTP response")

    with response:
        final_url = response.geturl()
        _validate_visual_url(provider, final_url)

        content_type = str(
            response.headers.get("Content-Type") or ""
        ).split(";", 1)[0].strip().lower()

        extension = VISUAL_MIME_EXTENSIONS.get(content_type)
        if extension is None:
            raise ValueError(
                f"visual content type is not supported: {content_type or 'missing'}"
            )

        if media_type == "video" and not content_type.startswith("video/"):
            raise ValueError("selected video returned non-video content")
        if media_type != "video" and not content_type.startswith("image/"):
            raise ValueError("selected image returned non-image content")

        raw_length = response.headers.get("Content-Length")
        if raw_length:
            try:
                content_length = int(raw_length)
            except ValueError as exc:
                raise ValueError("invalid visual Content-Length") from exc

            if content_length <= 0 or content_length > MAX_VISUAL_BYTES:
                raise ValueError("visual asset size is outside allowed bounds")

        digest = hashlib.sha256()
        total = 0

        fd = os.open(
            temp_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o640,
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break

                    total += len(chunk)
                    if total > MAX_VISUAL_BYTES:
                        raise ValueError("visual asset exceeds maximum allowed size")

                    digest.update(chunk)
                    handle.write(chunk)

                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

    if total <= 0:
        temp_path.unlink(missing_ok=True)
        raise ValueError("downloaded visual asset is empty")

    probe = ffprobe_visual(temp_path, media_type)
    final_path = final_dir / f"selected.{extension}"

    try:
        os.rename(temp_path, final_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    return {
        "storage_path": str(final_path),
        "sha256": digest.hexdigest(),
        "bytes": total,
        "mime_type": content_type,
        "media_type": media_type,
        "width": probe["width"],
        "height": probe["height"],
        "duration_ms": probe["duration_ms"],
        "codec": probe["codec"],
        "final_url": final_url,
    }



def ffprobe_render(path: Path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            (
                "format=duration,size:"
                "stream=codec_type,codec_name,width,height,pix_fmt,"
                "r_frame_rate,duration,channels,sample_rate"
            ),
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    payload = json.loads(result.stdout)
    streams = payload.get("streams") or []
    video_streams = [
        stream for stream in streams
        if stream.get("codec_type") == "video"
    ]
    audio_streams = [
        stream for stream in streams
        if stream.get("codec_type") == "audio"
    ]

    if len(video_streams) != 1 or len(audio_streams) != 1:
        raise ValueError("render must contain exactly one video and one audio stream")

    video = video_streams[0]
    audio = audio_streams[0]

    try:
        width = int(video.get("width") or 0)
        height = int(video.get("height") or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError("render dimensions are invalid") from exc

    rate = str(video.get("r_frame_rate") or "0/1")
    match = re.fullmatch(r"([0-9]+)/([0-9]+)", rate)
    if not match:
        raise ValueError("render frame rate is invalid")

    fps_num = int(match.group(1))
    fps_den = int(match.group(2))
    if fps_den <= 0:
        raise ValueError("render frame-rate denominator is invalid")

    try:
        duration_ms = round(
            float((payload.get("format") or {}).get("duration") or 0) * 1000
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("render duration is invalid") from exc

    if duration_ms <= 0:
        raise ValueError("render duration must be positive")

    return {
        "width": width,
        "height": height,
        "video_codec": str(video.get("codec_name") or "").lower(),
        "audio_codec": str(audio.get("codec_name") or "").lower(),
        "pix_fmt": str(video.get("pix_fmt") or "").lower(),
        "fps_num": fps_num,
        "fps_den": fps_den,
        "duration_ms": duration_ms,
        "video_stream_count": len(video_streams),
        "audio_stream_count": len(audio_streams),
    }


def _safe_render_asset_path(job_id, shot_id, path_value):
    path = Path(str(path_value or "").strip())
    if not path.is_absolute():
        raise ValueError("render asset path must be absolute")

    expected_dir = (VISUAL_ROOT / job_id / shot_id).resolve()
    resolved = path.resolve()

    if resolved.parent != expected_dir:
        raise ValueError("render asset path is outside the selected shot directory")
    if not resolved.name.startswith("selected."):
        raise ValueError("render asset filename is not a selected asset")
    if not resolved.is_file():
        raise ValueError("render asset file is missing")

    return resolved


def _render_segment(asset_path, media_type, duration_ms, output_path):
    if media_type not in VISUAL_MEDIA_TYPES:
        raise ValueError("unsupported render media type")
    if duration_ms <= 0:
        raise ValueError("render segment duration must be positive")

    duration_seconds = duration_ms / 1000.0
    if media_type != "video":
        filter_graph = (
            "[0:v]split=2[bg][fg];"
            "[bg]"
            "scale=1080:1920:force_original_aspect_ratio=increase:force_divisible_by=2:"
            "in_range=full:out_range=tv,"
            "crop=1080:1920,"
            "gblur=sigma=30:steps=2[bgfill];"
            "[fg]"
            "scale=1080:1920:force_original_aspect_ratio=decrease:force_divisible_by=2:"
            "in_range=full:out_range=tv[foreground];"
            "[bgfill][foreground]"
            "overlay=(W-w)/2:(H-h)/2,"
            "fps=30,format=yuv420p,setsar=1[v]"
        )
    else:
        filter_graph = (
            "[0:v]"
            "scale=1080:1920:force_original_aspect_ratio=decrease:force_divisible_by=2,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
            "fps=30,format=yuv420p,setsar=1[v]"
        )

    command = ["ffmpeg", "-nostdin", "-y"]

    if media_type == "video":
        command.extend(["-stream_loop", "-1", "-i", str(asset_path)])
    else:
        command.extend(
            ["-loop", "1", "-framerate", "30", "-i", str(asset_path)]
        )

    command.extend(
        [
            "-filter_complex",
            filter_graph,
            "-map",
            "[v]",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-fps_mode",
            "cfr",
            "-t",
            f"{duration_seconds:.3f}",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )

    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=180,
    )


def render_final_video(
    job_id,
    input_audio_sha256,
    audio_duration_ms,
    scenes,
    final_dir: Path,
):
    audio_path = VOICEOVER_ROOT / job_id / "final.mp3"
    if not audio_path.is_file():
        raise ValueError("render voiceover is missing")

    actual_audio_sha = file_sha256(audio_path)
    if actual_audio_sha != input_audio_sha256:
        raise ValueError("render voiceover SHA256 mismatch")

    audio_probe = ffprobe_audio(audio_path)
    if audio_probe["duration_ms"] != audio_duration_ms:
        raise ValueError("render voiceover duration mismatch")

    if not isinstance(scenes, list) or not scenes:
        raise ValueError("render scenes must be a non-empty array")

    work_dir = final_dir / ".work"
    work_dir.mkdir()

    segment_files = []
    segment_manifest = []
    previous_end = 0
    asset_hashes = set()

    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            raise ValueError(f"render scene {index} must be an object")

        scene_uuid = str(scene.get("scene_uuid") or "").strip().lower()
        shot_uuid = str(scene.get("shot_uuid") or "").strip().lower()
        visual_asset_id = str(scene.get("visual_asset_id") or "").strip().lower()
        media_type = str(scene.get("media_type") or "").strip().lower()
        asset_sha = str(scene.get("asset_sha256") or "").strip().lower()

        if not JOB_ID_RE.fullmatch(scene_uuid):
            raise ValueError(f"render scene {index} has invalid scene UUID")
        if not JOB_ID_RE.fullmatch(shot_uuid):
            raise ValueError(f"render scene {index} has invalid shot UUID")
        if not JOB_ID_RE.fullmatch(visual_asset_id):
            raise ValueError(f"render scene {index} has invalid visual asset UUID")
        if media_type not in VISUAL_MEDIA_TYPES:
            raise ValueError(f"render scene {index} has invalid media type")
        if not re.fullmatch(r"[0-9a-f]{64}", asset_sha):
            raise ValueError(f"render scene {index} has invalid asset SHA256")

        try:
            scene_order = int(scene.get("scene_order"))
            start_ms = int(scene.get("segment_start_ms"))
            end_ms = int(scene.get("segment_end_ms"))
            speech_start_ms = int(scene.get("speech_start_ms"))
            speech_end_ms = int(scene.get("speech_end_ms"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"render scene {index} has invalid timings") from exc

        if scene_order != index:
            raise ValueError("render scene order is not sequential")
        if start_ms != previous_end:
            raise ValueError("render segments are not contiguous")
        if end_ms <= start_ms or end_ms > audio_duration_ms:
            raise ValueError("render segment bounds are invalid")
        if speech_start_ms < start_ms or speech_end_ms > end_ms:
            raise ValueError("speech timing is outside render segment")
        if speech_end_ms <= speech_start_ms:
            raise ValueError("speech timing has non-positive duration")

        asset_width = int(scene.get("asset_width") or 0)
        asset_height = int(scene.get("asset_height") or 0)
        if asset_width <= 0 or asset_height <= 0:
            raise ValueError("render asset dimensions are invalid")

        asset_path = _safe_render_asset_path(
            job_id,
            shot_uuid,
            scene.get("asset_path"),
        )
        if file_sha256(asset_path) != asset_sha:
            raise ValueError("render asset SHA256 mismatch")
        if asset_sha in asset_hashes:
            raise ValueError("render asset hash is reused")
        asset_hashes.add(asset_sha)

        segment_path = work_dir / f"segment-{index:02d}.mp4"
        _render_segment(
            asset_path,
            media_type,
            end_ms - start_ms,
            segment_path,
        )

        segment_probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=codec_type,codec_name,width,height,pix_fmt,r_frame_rate",
                "-of",
                "json",
                str(segment_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        segment_probe_payload = json.loads(segment_probe.stdout)
        video_streams = [
            stream
            for stream in segment_probe_payload.get("streams") or []
            if stream.get("codec_type") == "video"
        ]
        if len(video_streams) != 1:
            raise ValueError("render segment must contain exactly one video stream")

        segment_video = video_streams[0]
        if (
            str(segment_video.get("codec_name") or "").lower() != "h264"
            or int(segment_video.get("width") or 0) != 1080
            or int(segment_video.get("height") or 0) != 1920
            or str(segment_video.get("pix_fmt") or "").lower() != "yuv420p"
            or str(segment_video.get("r_frame_rate") or "") != "30/1"
        ):
            raise ValueError("render segment video parameters are invalid")

        segment_files.append(segment_path)
        segment_manifest.append(
            {
                "scene_uuid": scene_uuid,
                "shot_uuid": shot_uuid,
                "visual_asset_id": visual_asset_id,
                "segment_order": index,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_ms": end_ms - start_ms,
                "asset_sha256": asset_sha,
                "media_type": media_type,
            }
        )
        previous_end = end_ms

    if previous_end != audio_duration_ms:
        raise ValueError("render segments do not cover the full voiceover")
    if len(asset_hashes) != len(scenes):
        raise ValueError("render asset hashes are not unique")

    concat_path = work_dir / "concat.txt"
    concat_path.write_text(
        "".join(f"file '{path}'\n" for path in segment_files),
        encoding="utf-8",
    )

    video_only_path = work_dir / "video-only.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-c",
            "copy",
            str(video_only_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )

    temp_final_path = work_dir / "final.tmp.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-y",
            "-i",
            str(video_only_path),
            "-i",
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-t",
            f"{audio_duration_ms / 1000.0:.3f}",
            "-movflags",
            "+faststart",
            str(temp_final_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=90,
    )

    probe = ffprobe_render(temp_final_path)
    duration_delta_ms = abs(probe["duration_ms"] - audio_duration_ms)

    qa_gates = {
        "video_dimensions":
            probe["width"] == 1080 and probe["height"] == 1920,
        "video_codec":
            probe["video_codec"] == "h264" and probe["pix_fmt"] == "yuv420p",
        "audio_codec":
            probe["audio_codec"] == "aac",
        "stream_counts":
            probe["video_stream_count"] == 1
            and probe["audio_stream_count"] == 1,
        "duration_match":
            duration_delta_ms <= 100,
        "scene_coverage":
            len(segment_manifest) == len(scenes)
            and segment_manifest[0]["start_ms"] == 0
            and segment_manifest[-1]["end_ms"] == audio_duration_ms,
        "asset_hashes":
            len(asset_hashes) == len(scenes),
        "source_audio_excluded":
            True,
    }

    if not all(qa_gates.values()):
        raise ValueError(
            "machine QA failed: "
            + json.dumps(qa_gates, sort_keys=True)
        )

    final_path = final_dir / "final.mp4"
    os.rename(temp_final_path, final_path)

    result = {
        "status": "ready",
        "job_id": job_id,
        "storage_path": str(final_path),
        "manifest_path": str(final_dir / "manifest.json"),
        "sha256": file_sha256(final_path),
        "bytes": final_path.stat().st_size,
        **probe,
        "audio_duration_ms": audio_duration_ms,
        "duration_delta_ms": duration_delta_ms,
        "input_audio_sha256": input_audio_sha256,
        "segments": segment_manifest,
        "qa_gates": qa_gates,
        "qa_passed": True,
    }

    _write_json_fsync(final_dir / "manifest.json", result)
    shutil.rmtree(work_dir)

    return result


class Handler(BaseHTTPRequestHandler):
    def _json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _job_id_for_path(self, prefix, suffix=""):
        pattern = rf"^/{prefix}/([^/]+){suffix}$"
        match = re.fullmatch(pattern, self.path)
        if not match:
            return None

        job_id = match.group(1)
        if not JOB_ID_RE.fullmatch(job_id):
            return None

        return job_id.lower()

    def _voiceover_job_id(self, suffix=""):
        return self._job_id_for_path("voiceovers", suffix)

    def _voiceover_candidate_job_id(self, suffix=""):
        return self._job_id_for_path("voiceover-candidates", suffix)

    def _alignment_job_id(self, suffix=""):
        return self._job_id_for_path("alignments", suffix)

    def _render_job_id(self, suffix=""):
        return self._job_id_for_path("renders", suffix)

    def _visual_ids(self, suffix=""):
        pattern = rf"^/visuals/([^/]+)/([^/]+){suffix}$"
        match = re.fullmatch(pattern, self.path)
        if not match:
            return None

        job_id, shot_id = match.groups()
        if not JOB_ID_RE.fullmatch(job_id) or not JOB_ID_RE.fullmatch(shot_id):
            return None

        return job_id.lower(), shot_id.lower()

    def _read_json_body(self):
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise ValueError("Content-Length is required")

        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc

        if length <= 0 or length > MAX_JSON_BODY_BYTES:
            raise ValueError("request body size is invalid")

        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("request body must be valid JSON") from exc

        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")

        return payload

    def _voiceover_metadata(self, job_id):
        path = VOICEOVER_ROOT / job_id / "final.mp3"
        if not path.is_file():
            return None

        probe = ffprobe_audio(path)
        return {
            "status": "ready",
            "job_id": job_id,
            "storage_path": str(path),
            "sha256": file_sha256(path),
            "bytes": path.stat().st_size,
            **probe,
        }

    def _voiceover_candidate_metadata(self, job_id):
        path = VOICEOVER_CANDIDATE_ROOT / job_id / "accepted.mp3"
        if not path.is_file():
            return None

        probe = ffprobe_audio(path)
        return {
            "status": "ready",
            "job_id": job_id,
            "storage_path": str(path),
            "sha256": file_sha256(path),
            "bytes": path.stat().st_size,
            **probe,
        }

    def _send_mp4_file(self, path: Path):
        if not path.is_file():
            self._json(404, {"error": "render_file_not_found"})
            return

        size = path.stat().st_size
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(size))
        self.send_header(
            "Content-Disposition",
            'inline; filename="final.mp4"',
        )
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()

        try:
            with path.open("rb") as handle:
                while True:
                    chunk = handle.read(1024 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            return

    def do_GET(self):
        if self.path == "/healthz":
            try:
                model_sha = whisper_model_sha256()
                body = {
                    "status": "ok",
                    "service": "media-worker",
                    "ffmpeg": ffmpeg_version(),
                    "whisper_cli": str(WHISPER_CLI),
                    "whisper_model_sha256": model_sha,
                    "whisper_image_digest": WHISPER_IMAGE_DIGEST,
                }
            except (OSError, subprocess.SubprocessError, ValueError) as exc:
                self._json(
                    503,
                    {
                        "status": "error",
                        "service": "media-worker",
                        "message": str(exc),
                    },
                )
                return

            self._json(200, body)
            return

        job_id = self._voiceover_candidate_job_id("/metadata")
        if job_id is not None:
            try:
                payload = self._voiceover_candidate_metadata(job_id)
                if payload is None:
                    self._json(404, {"error": "voiceover_candidate_not_found"})
                    return
            except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError) as exc:
                self._json(
                    500,
                    {
                        "error": "voiceover_candidate_metadata_failed",
                        "message": str(exc),
                    },
                )
                return

            self._json(200, payload)
            return

        job_id = self._voiceover_job_id("/metadata")
        if job_id is not None:
            try:
                payload = self._voiceover_metadata(job_id)
                if payload is None:
                    self._json(404, {"error": "voiceover_not_found"})
                    return
            except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError) as exc:
                self._json(
                    500,
                    {
                        "error": "voiceover_metadata_failed",
                        "message": str(exc),
                    },
                )
                return

            self._json(200, payload)
            return

        job_id = self._alignment_job_id("/metadata")
        if job_id is not None:
            final_path = ALIGNMENT_ROOT / job_id / "final.json"
            failure_path = ALIGNMENT_ROOT / job_id / "failure.json"

            if final_path.is_file():
                try:
                    payload = json.loads(final_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    self._json(
                        500,
                        {
                            "error": "alignment_metadata_failed",
                            "message": str(exc),
                        },
                    )
                    return

                self._json(200, payload)
                return

            if failure_path.is_file():
                try:
                    payload = json.loads(failure_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    self._json(
                        500,
                        {
                            "error": "alignment_metadata_failed",
                            "message": str(exc),
                        },
                    )
                    return

                self._json(422, payload)
                return

            self._json(404, {"error": "alignment_not_found"})
            return

        visual_ids = self._visual_ids("/metadata")
        if visual_ids is not None:
            job_id, shot_id = visual_ids
            final_dir = VISUAL_ROOT / job_id / shot_id
            metadata_path = final_dir / "metadata.json"
            failure_path = final_dir / "failure.json"

            if metadata_path.is_file():
                try:
                    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    self._json(
                        500,
                        {
                            "error": "visual_metadata_failed",
                            "message": str(exc),
                        },
                    )
                    return

                self._json(200, payload)
                return

            if failure_path.is_file():
                try:
                    payload = json.loads(failure_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    self._json(
                        500,
                        {
                            "error": "visual_metadata_failed",
                            "message": str(exc),
                        },
                    )
                    return

                self._json(422, payload)
                return

            self._json(404, {"error": "visual_not_found"})
            return

        job_id = self._render_job_id("/file")
        if job_id is not None:
            final_path = RENDER_ROOT / job_id / "final.mp4"
            self._send_mp4_file(final_path)
            return

        job_id = self._render_job_id("/metadata")
        if job_id is not None:
            final_dir = RENDER_ROOT / job_id
            manifest_path = final_dir / "manifest.json"
            failure_path = final_dir / "failure.json"

            if manifest_path.is_file():
                try:
                    payload = json.loads(
                        manifest_path.read_text(encoding="utf-8")
                    )
                except (OSError, json.JSONDecodeError) as exc:
                    self._json(
                        500,
                        {
                            "error": "render_metadata_failed",
                            "message": str(exc),
                        },
                    )
                    return

                self._json(200, payload)
                return

            if failure_path.is_file():
                try:
                    payload = json.loads(
                        failure_path.read_text(encoding="utf-8")
                    )
                except (OSError, json.JSONDecodeError) as exc:
                    self._json(
                        500,
                        {
                            "error": "render_metadata_failed",
                            "message": str(exc),
                        },
                    )
                    return

                self._json(422, payload)
                return

            self._json(404, {"error": "render_not_found"})
            return

        self._json(404, {"error": "not_found"})

    def _handle_voiceover_probe_post(self):
        probe_path = None
        try:
            payload = self._read_json_body()
            encoded = payload.get("audio_base64")
            if not isinstance(encoded, str) or not encoded:
                raise ValueError("audio_base64 is required")

            try:
                audio_bytes = base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise ValueError("audio_base64 is invalid") from exc

            if not audio_bytes:
                raise ValueError("decoded audio is empty")

            with tempfile.NamedTemporaryFile(
                mode="wb",
                suffix=".mp3",
                prefix="voiceover-probe-",
                delete=False,
            ) as handle:
                handle.write(audio_bytes)
                handle.flush()
                os.fsync(handle.fileno())
                probe_path = Path(handle.name)

            probe = ffprobe_audio(probe_path)
            self._json(
                200,
                {
                    "status": "ready",
                    "bytes": len(audio_bytes),
                    "sha256": hashlib.sha256(audio_bytes).hexdigest(),
                    **probe,
                },
            )
            return
        except ValueError as exc:
            self._json(
                400,
                {
                    "error": "invalid_voiceover_probe_request",
                    "message": str(exc),
                },
            )
            return
        except subprocess.TimeoutExpired:
            self._json(422, {"error": "voiceover_probe_timeout"})
            return
        except subprocess.CalledProcessError as exc:
            self._json(
                422,
                {
                    "error": "voiceover_probe_failed",
                    "message": (exc.stderr or exc.stdout or str(exc))[-2000:],
                },
            )
            return
        finally:
            if probe_path is not None:
                probe_path.unlink(missing_ok=True)

    def _handle_voiceover_candidate_post(self, job_id):
        candidate_dir = VOICEOVER_CANDIDATE_ROOT / job_id
        candidate_path = candidate_dir / "accepted.mp3"

        if candidate_path.exists():
            self._json(
                409,
                {
                    "error": "voiceover_candidate_already_exists",
                    "job_id": job_id,
                },
            )
            return

        try:
            payload = self._read_json_body()
            encoded = payload.get("audio_base64")
            if not isinstance(encoded, str) or not encoded:
                raise ValueError("audio_base64 is required")

            try:
                audio_bytes = base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise ValueError("audio_base64 is invalid") from exc

            if not audio_bytes:
                raise ValueError("decoded audio is empty")

            candidate_dir.mkdir(parents=True, exist_ok=True)

            try:
                fd = os.open(
                    candidate_path,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o640,
                )
            except FileExistsError:
                self._json(
                    409,
                    {
                        "error": "voiceover_candidate_already_exists",
                        "job_id": job_id,
                    },
                )
                return

            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(audio_bytes)
                    handle.flush()
                    os.fsync(handle.fileno())

                probe = ffprobe_audio(candidate_path)
                sha256 = hashlib.sha256(audio_bytes).hexdigest()
                result = {
                    "status": "ready",
                    "job_id": job_id,
                    "storage_path": str(candidate_path),
                    "sha256": sha256,
                    "bytes": len(audio_bytes),
                    **probe,
                }
            except Exception:
                try:
                    candidate_path.unlink(missing_ok=True)
                finally:
                    raise

        except ValueError as exc:
            self._json(
                400,
                {
                    "error": "invalid_voiceover_candidate_request",
                    "message": str(exc),
                },
            )
            return
        except subprocess.TimeoutExpired:
            self._json(422, {"error": "voiceover_candidate_probe_timeout"})
            return
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            self._json(
                422,
                {
                    "error": "voiceover_candidate_validation_failed",
                    "message": str(exc),
                },
            )
            return

        self._json(201, result)

    def _handle_voiceover_candidate_promote_post(self, job_id):
        candidate_path = VOICEOVER_CANDIDATE_ROOT / job_id / "accepted.mp3"
        final_dir = VOICEOVER_ROOT / job_id
        final_path = final_dir / "final.mp3"

        if not candidate_path.is_file():
            self._json(
                404,
                {
                    "error": "voiceover_candidate_not_found",
                    "job_id": job_id,
                },
            )
            return

        if final_path.exists():
            self._json(
                409,
                {
                    "error": "voiceover_already_exists",
                    "job_id": job_id,
                },
            )
            return

        try:
            payload = self._read_json_body()
            expected_sha256 = str(payload.get("expected_sha256") or "").lower()
            try:
                expected_duration_ms = int(payload.get("expected_duration_ms"))
            except (TypeError, ValueError) as exc:
                raise ValueError("expected_duration_ms must be an integer") from exc

            if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
                raise ValueError("expected_sha256 must be lowercase SHA256")
            if expected_duration_ms <= 0:
                raise ValueError("expected_duration_ms must be positive")

            actual_sha256 = file_sha256(candidate_path)
            candidate_probe = ffprobe_audio(candidate_path)
            if actual_sha256 != expected_sha256:
                raise ValueError("voiceover candidate SHA256 mismatch")
            if candidate_probe["duration_ms"] != expected_duration_ms:
                raise ValueError("voiceover candidate duration mismatch")

            final_dir.mkdir(parents=True, exist_ok=True)
            try:
                os.link(candidate_path, final_path)
            except FileExistsError:
                self._json(
                    409,
                    {
                        "error": "voiceover_already_exists",
                        "job_id": job_id,
                    },
                )
                return

            try:
                final_probe = ffprobe_audio(final_path)
                final_sha256 = file_sha256(final_path)
                if final_sha256 != actual_sha256:
                    raise ValueError("promoted voiceover SHA256 mismatch")
                if final_probe["duration_ms"] != candidate_probe["duration_ms"]:
                    raise ValueError("promoted voiceover duration mismatch")

                result = {
                    "status": "ready",
                    "job_id": job_id,
                    "storage_path": str(final_path),
                    "sha256": final_sha256,
                    "bytes": final_path.stat().st_size,
                    **final_probe,
                }
            except Exception:
                final_path.unlink(missing_ok=True)
                raise

        except ValueError as exc:
            self._json(
                400,
                {
                    "error": "invalid_voiceover_candidate_promotion",
                    "message": str(exc),
                },
            )
            return
        except subprocess.TimeoutExpired:
            self._json(422, {"error": "voiceover_candidate_promotion_timeout"})
            return
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            self._json(
                422,
                {
                    "error": "voiceover_candidate_promotion_failed",
                    "message": str(exc),
                },
            )
            return

        self._json(201, result)

    def _handle_voiceover_post(self, job_id):
        final_dir = VOICEOVER_ROOT / job_id
        final_path = final_dir / "final.mp3"

        if final_path.exists():
            self._json(
                409,
                {
                    "error": "voiceover_already_exists",
                    "job_id": job_id,
                },
            )
            return

        try:
            payload = self._read_json_body()
            encoded = payload.get("audio_base64")
            if not isinstance(encoded, str) or not encoded:
                raise ValueError("audio_base64 is required")

            try:
                audio_bytes = base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise ValueError("audio_base64 is invalid") from exc

            if not audio_bytes:
                raise ValueError("decoded audio is empty")

            final_dir.mkdir(parents=True, exist_ok=True)

            try:
                fd = os.open(
                    final_path,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o640,
                )
            except FileExistsError:
                self._json(
                    409,
                    {
                        "error": "voiceover_already_exists",
                        "job_id": job_id,
                    },
                )
                return

            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(audio_bytes)
                    handle.flush()
                    os.fsync(handle.fileno())

                probe = ffprobe_audio(final_path)
                sha256 = hashlib.sha256(audio_bytes).hexdigest()
                result = {
                    "status": "ready",
                    "job_id": job_id,
                    "storage_path": str(final_path),
                    "sha256": sha256,
                    "bytes": len(audio_bytes),
                    **probe,
                }
            except Exception:
                try:
                    final_path.unlink(missing_ok=True)
                finally:
                    raise

        except ValueError as exc:
            self._json(
                400,
                {
                    "error": "invalid_voiceover_request",
                    "message": str(exc),
                },
            )
            return
        except subprocess.TimeoutExpired:
            self._json(
                422,
                {
                    "error": "voiceover_probe_timeout",
                },
            )
            return
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            self._json(
                422,
                {
                    "error": "voiceover_validation_failed",
                    "message": str(exc),
                },
            )
            return

        self._json(201, result)

    def _handle_alignment_post(self, job_id):
        final_dir = ALIGNMENT_ROOT / job_id
        final_path = final_dir / "final.json"
        failure_path = final_dir / "failure.json"
        raw_path = final_dir / "whisper.json"

        if final_dir.exists():
            self._json(
                409,
                {
                    "error": "alignment_attempt_already_exists",
                    "job_id": job_id,
                },
            )
            return

        try:
            payload = self._read_json_body()
            language_code = str(payload.get("language_code") or "").strip().lower()
            narration = payload.get("narration")
            scenes = payload.get("scenes")
            expected_audio_sha = str(
                payload.get("audio_sha256") or ""
            ).strip().lower()

            try:
                expected_duration_ms = int(payload.get("audio_duration_ms"))
            except (TypeError, ValueError) as exc:
                raise ValueError("audio_duration_ms must be an integer") from exc

            if language_code not in LANGUAGE_CODES:
                raise ValueError("unsupported alignment language")
            if not isinstance(narration, str) or not narration.strip():
                raise ValueError("narration is required")
            if not isinstance(scenes, list) or not scenes:
                raise ValueError("scenes must be a non-empty array")
            if not re.fullmatch(r"[0-9a-f]{64}", expected_audio_sha):
                raise ValueError("audio_sha256 must be lowercase SHA256")
            if expected_duration_ms <= 0:
                raise ValueError("audio_duration_ms must be positive")

            audio_path = VOICEOVER_ROOT / job_id / "final.mp3"
            if not audio_path.is_file():
                self._json(404, {"error": "voiceover_not_found"})
                return

            actual_audio_sha = file_sha256(audio_path)
            if actual_audio_sha != expected_audio_sha:
                raise ValueError("exact voiceover SHA256 mismatch")

            audio_probe = ffprobe_audio(audio_path)
            if audio_probe["duration_ms"] != expected_duration_ms:
                raise ValueError("exact voiceover duration mismatch")

            model_sha = whisper_model_sha256()

            try:
                final_dir.mkdir(parents=True, exist_ok=False)
            except FileExistsError:
                self._json(
                    409,
                    {
                        "error": "alignment_attempt_already_exists",
                        "job_id": job_id,
                    },
                )
                return

            work_dir = final_dir / ".work"
            work_dir.mkdir()

            with ALIGNMENT_EXECUTION_LOCK:
                whisper_payload, summary = run_local_alignment(
                    audio_path,
                    language_code,
                    narration,
                    scenes,
                    audio_probe["duration_ms"],
                    work_dir,
                )

            result = {
                "status": "ready",
                "job_id": job_id,
                "alignment_path": str(final_path),
                "raw_whisper_path": str(raw_path),
                "audio_sha256": actual_audio_sha,
                "audio_duration_ms": audio_probe["duration_ms"],
                "language_code": language_code,
                "model_sha256": model_sha,
                "whisper_image_digest": WHISPER_IMAGE_DIGEST,
                **summary,
            }

            _write_json_fsync(raw_path, whisper_payload)
            _write_json_fsync(final_path, result)
            shutil.rmtree(work_dir)

        except subprocess.TimeoutExpired as exc:
            if final_dir.exists() and not final_path.exists():
                try:
                    failure = {
                        "status": "failed",
                        "job_id": job_id,
                        "error": "alignment_timeout",
                        "message": str(exc),
                    }
                    if not failure_path.exists():
                        _write_json_fsync(failure_path, failure)
                    work_dir = final_dir / ".work"
                    if work_dir.exists():
                        shutil.rmtree(work_dir)
                except Exception:
                    pass

            self._json(
                422,
                {
                    "error": "alignment_timeout",
                    "job_id": job_id,
                },
            )
            return
        except (ValueError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            if final_dir.exists() and not final_path.exists():
                try:
                    failure = {
                        "status": "failed",
                        "job_id": job_id,
                        "error": "alignment_failed",
                        "message": str(exc),
                    }
                    if not failure_path.exists():
                        _write_json_fsync(failure_path, failure)
                    work_dir = final_dir / ".work"
                    debug_whisper_path = work_dir / "whisper.json"
                    if debug_whisper_path.is_file() and not raw_path.exists():
                        with debug_whisper_path.open("r", encoding="utf-8") as handle:
                            debug_whisper_payload = json.load(handle)
                        _write_json_fsync(raw_path, debug_whisper_payload)
                    if work_dir.exists():
                        shutil.rmtree(work_dir)
                except Exception:
                    pass

            self._json(
                422,
                {
                    "error": "alignment_failed",
                    "job_id": job_id,
                    "message": str(exc),
                },
            )
            return

        self._json(201, result)

    def _handle_visual_previews_post(self):
        payload = self._read_json_body()
        candidates = payload.get("candidates")
        if not isinstance(candidates, list) or not 1 <= len(candidates) <= 3:
            raise ValueError("candidates must contain between 1 and 3 items")

        previews = []
        total_bytes = 0
        for index, candidate in enumerate(candidates, start=1):
            if not isinstance(candidate, dict):
                raise ValueError("preview candidate must be an object")

            provider = str(candidate.get("provider") or "").strip().lower()
            preview_url = str(candidate.get("preview_url") or "").strip()
            provider_asset_id = str(
                candidate.get("provider_asset_id") or ""
            ).strip()

            if provider not in VISUAL_PROVIDERS:
                raise ValueError("unsupported visual provider")
            if not provider_asset_id:
                raise ValueError("provider_asset_id is required")
            if not preview_url:
                raise ValueError("preview_url is required")

            preview = fetch_visual_preview(provider, preview_url)
            total_bytes += int(preview["bytes"])
            if total_bytes > MAX_VISION_PREVIEW_TOTAL_BYTES:
                raise ValueError("combined visual previews exceed maximum size")

            previews.append(
                {
                    "candidate_index": index,
                    "provider": provider,
                    "provider_asset_id": provider_asset_id,
                    **preview,
                }
            )

        self._json(
            200,
            {
                "status": "ready",
                "preview_count": len(previews),
                "total_bytes": total_bytes,
                "previews": previews,
            },
        )

    def _handle_visual_post(self, job_id, shot_id):
        final_dir = VISUAL_ROOT / job_id / shot_id
        metadata_path = final_dir / "metadata.json"
        failure_path = final_dir / "failure.json"

        if final_dir.exists():
            self._json(
                409,
                {
                    "error": "visual_attempt_already_exists",
                    "job_id": job_id,
                    "shot_id": shot_id,
                },
            )
            return

        try:
            payload = self._read_json_body()
            provider = str(payload.get("provider") or "").strip().lower()
            provider_asset_id = str(
                payload.get("provider_asset_id") or ""
            ).strip()
            media_type = str(payload.get("media_type") or "").strip().lower()
            download_url = str(payload.get("download_url") or "").strip()

            if provider not in VISUAL_PROVIDERS:
                raise ValueError("unsupported visual provider")
            if not provider_asset_id:
                raise ValueError("provider_asset_id is required")
            if media_type not in VISUAL_MEDIA_TYPES:
                raise ValueError("unsupported visual media type")

            _validate_visual_url(provider, download_url)

            try:
                final_dir.mkdir(parents=True, exist_ok=False)
            except FileExistsError:
                self._json(
                    409,
                    {
                        "error": "visual_attempt_already_exists",
                        "job_id": job_id,
                        "shot_id": shot_id,
                    },
                )
                return

            result = download_visual_asset(
                provider,
                download_url,
                media_type,
                final_dir,
            )

            response = {
                "status": "ready",
                "job_id": job_id,
                "shot_id": shot_id,
                "provider": provider,
                "provider_asset_id": provider_asset_id,
                **result,
            }

            _write_json_fsync(metadata_path, response)

        except Exception as exc:
            if final_dir.exists() and not metadata_path.exists():
                try:
                    failure = {
                        "status": "failed",
                        "job_id": job_id,
                        "shot_id": shot_id,
                        "error": "visual_download_failed",
                        "message": str(exc),
                    }
                    if not failure_path.exists():
                        _write_json_fsync(failure_path, failure)
                except Exception:
                    pass

            self._json(
                422,
                {
                    "error": "visual_download_failed",
                    "job_id": job_id,
                    "shot_id": shot_id,
                    "message": str(exc),
                },
            )
            return

        self._json(201, response)


    def _handle_render_post(self, job_id):
        final_dir = RENDER_ROOT / job_id
        manifest_path = final_dir / "manifest.json"
        failure_path = final_dir / "failure.json"

        if final_dir.exists():
            self._json(
                409,
                {
                    "error": "render_attempt_already_exists",
                    "job_id": job_id,
                },
            )
            return

        try:
            payload = self._read_json_body()
            input_audio_sha256 = str(
                payload.get("input_audio_sha256") or ""
            ).strip().lower()
            try:
                audio_duration_ms = int(payload.get("audio_duration_ms"))
            except (TypeError, ValueError) as exc:
                raise ValueError("audio_duration_ms must be an integer") from exc

            scenes = payload.get("scenes")
            if not re.fullmatch(r"[0-9a-f]{64}", input_audio_sha256):
                raise ValueError("input_audio_sha256 is invalid")
            if audio_duration_ms <= 0:
                raise ValueError("audio_duration_ms must be positive")
            if not isinstance(scenes, list) or not scenes:
                raise ValueError("scenes must be a non-empty array")

            try:
                final_dir.mkdir(parents=True, exist_ok=False)
            except FileExistsError:
                self._json(
                    409,
                    {
                        "error": "render_attempt_already_exists",
                        "job_id": job_id,
                    },
                )
                return

            result = render_final_video(
                job_id,
                input_audio_sha256,
                audio_duration_ms,
                scenes,
                final_dir,
            )

        except subprocess.TimeoutExpired as exc:
            if final_dir.exists() and not manifest_path.exists():
                try:
                    failure = {
                        "status": "failed",
                        "job_id": job_id,
                        "error": "render_timeout",
                        "message": str(exc),
                    }
                    if not failure_path.exists():
                        _write_json_fsync(failure_path, failure)
                    work_dir = final_dir / ".work"
                    if work_dir.exists():
                        shutil.rmtree(work_dir)
                    (final_dir / "final.mp4").unlink(missing_ok=True)
                except Exception:
                    pass

            self._json(
                422,
                {
                    "error": "render_timeout",
                    "job_id": job_id,
                    "message": str(exc),
                },
            )
            return
        except Exception as exc:
            if final_dir.exists() and not manifest_path.exists():
                try:
                    failure = {
                        "status": "failed",
                        "job_id": job_id,
                        "error": "render_failed",
                        "message": str(exc),
                    }
                    if not failure_path.exists():
                        _write_json_fsync(failure_path, failure)
                    work_dir = final_dir / ".work"
                    if work_dir.exists():
                        shutil.rmtree(work_dir)
                    (final_dir / "final.mp4").unlink(missing_ok=True)
                except Exception:
                    pass

            self._json(
                422,
                {
                    "error": "render_failed",
                    "job_id": job_id,
                    "message": str(exc),
                },
            )
            return

        self._json(201, result)

    def do_POST(self):
        if self.path == "/visual-previews":
            try:
                self._handle_visual_previews_post()
            except (
                ValueError,
                OSError,
                urllib.error.URLError,
                urllib.error.HTTPError,
            ) as exc:
                self._json(
                    422,
                    {
                        "error": "visual_preview_failed",
                        "message": str(exc),
                    },
                )
            return

        if self.path == "/voiceover-probe":
            self._handle_voiceover_probe_post()
            return

        candidate_promote_job_id = self._voiceover_candidate_job_id("/promote")
        if candidate_promote_job_id is not None:
            self._handle_voiceover_candidate_promote_post(candidate_promote_job_id)
            return

        candidate_job_id = self._voiceover_candidate_job_id()
        if candidate_job_id is not None:
            self._handle_voiceover_candidate_post(candidate_job_id)
            return

        render_job_id = self._render_job_id()
        if render_job_id is not None:
            self._handle_render_post(render_job_id)
            return

        visual_ids = self._visual_ids()
        if visual_ids is not None:
            self._handle_visual_post(*visual_ids)
            return

        alignment_job_id = self._alignment_job_id()
        if alignment_job_id is not None:
            self._handle_alignment_post(alignment_job_id)
            return

        voiceover_job_id = self._voiceover_job_id()
        if voiceover_job_id is not None:
            self._handle_voiceover_post(voiceover_job_id)
            return

        self._json(404, {"error": "not_found"})

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    VOICEOVER_ROOT.mkdir(parents=True, exist_ok=True)
    VOICEOVER_CANDIDATE_ROOT.mkdir(parents=True, exist_ok=True)
    ALIGNMENT_ROOT.mkdir(parents=True, exist_ok=True)
    VISUAL_ROOT.mkdir(parents=True, exist_ok=True)
    RENDER_ROOT.mkdir(parents=True, exist_ok=True)
    ThreadingHTTPServer(("0.0.0.0", 3001), Handler).serve_forever()
