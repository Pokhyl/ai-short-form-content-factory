from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unicodedata


DATA_ROOT = Path("/data")
VOICEOVER_ROOT = DATA_ROOT / "voiceovers"
ALIGNMENT_ROOT = DATA_ROOT / "alignments"
WHISPER_CLI = Path("/opt/whisper/whisper-cli")
WHISPER_MODEL = Path("/models/ggml-base.bin")
WHISPER_IMAGE_DIGEST = (
    "sha256:9cfbaf11ef5bec57ec9cade6af7ed991ab5e32b01a6e40db3380a12363336e11"
)
EXPECTED_MODEL_SHA256 = (
    "60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe"
)
MAX_JSON_BODY_BYTES = 20 * 1024 * 1024
JOB_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
    r"[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-"
    r"[0-9a-fA-F]{12}$"
)
LANGUAGE_CODES = {"en", "pl", "ru", "uk"}
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


def normalize_alignment_text(value):
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(char for char in normalized if char.isalnum())


def _lexical_tokens(whisper_payload):
    rows = []

    for segment in whisper_payload.get("transcription") or []:
        for token in segment.get("tokens") or []:
            token_text = str(token.get("text") or "")
            stripped = token_text.strip()

            if stripped.startswith("[_") and stripped.endswith("]"):
                continue

            token_normalized = normalize_alignment_text(token_text)
            if not token_normalized:
                continue

            offsets = token.get("offsets") or {}
            try:
                start_ms = int(offsets.get("from"))
                end_ms = int(offsets.get("to"))
            except (TypeError, ValueError) as exc:
                raise ValueError("whisper lexical token is missing numeric offsets") from exc

            if start_ms < 0 or end_ms < start_ms:
                raise ValueError("whisper lexical token has invalid offsets")

            rows.append(
                {
                    "text": token_text,
                    "normalized": token_normalized,
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                }
            )

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

    if transcript_normalized != expected_normalized:
        raise ValueError(
            "normalized whisper transcript does not exactly match narration"
        )

    tokens = _lexical_tokens(whisper_payload)
    token_normalized = "".join(token["normalized"] for token in tokens)

    if token_normalized != transcript_normalized:
        raise ValueError(
            "whisper lexical tokens do not reconstruct the normalized transcript"
        )

    if tokens[-1]["end_ms"] > audio_duration_ms:
        raise ValueError("whisper lexical timing exceeds audio duration")

    scene_joined = " ".join(
        str(scene.get("narration") or "").strip()
        for scene in scenes
    )
    if normalize_alignment_text(scene_joined) != expected_normalized:
        raise ValueError("scene narrations do not reconstruct the final narration")

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

        overlapping = [
            token
            for token in token_ranges
            if token["end_char"] > scene_start_char
            and token["start_char"] < scene_end_char
        ]

        if not overlapping:
            raise ValueError(f"scene {scene_key} has no lexical timing coverage")

        start_ms = overlapping[0]["start_ms"]
        end_ms = overlapping[-1]["end_ms"]

        if start_ms < previous_end_ms:
            raise ValueError(f"scene {scene_key} timing is not monotonic")
        if end_ms <= start_ms:
            raise ValueError(f"scene {scene_key} timing has non-positive duration")
        if end_ms > audio_duration_ms:
            raise ValueError(f"scene {scene_key} timing exceeds audio duration")

        scene_timings.append(
            {
                "scene_uuid": scene_uuid,
                "scene_key": scene_key,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "coverage": 1.0,
            }
        )

        previous_end_ms = end_ms
        expected_cursor = scene_end_char

    if expected_cursor != len(expected_normalized):
        raise ValueError("scene timing coverage does not reach narration end")

    return {
        "transcript": transcript,
        "normalized_match": True,
        "global_coverage": 1.0,
        "lexical_token_count": len(tokens),
        "lexical_start_ms": tokens[0]["start_ms"],
        "lexical_end_ms": tokens[-1]["end_ms"],
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

    def _alignment_job_id(self, suffix=""):
        return self._job_id_for_path("alignments", suffix)

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

        self._json(404, {"error": "not_found"})

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

    def do_POST(self):
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
    ALIGNMENT_ROOT.mkdir(parents=True, exist_ok=True)
    ThreadingHTTPServer(("0.0.0.0", 3001), Handler).serve_forever()
