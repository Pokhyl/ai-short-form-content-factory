from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


DATA_ROOT = Path("/data")
VOICEOVER_ROOT = DATA_ROOT / "voiceovers"
MAX_JSON_BODY_BYTES = 20 * 1024 * 1024
JOB_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
    r"[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-"
    r"[0-9a-fA-F]{12}$"
)


def ffmpeg_version():
    result = subprocess.run(
        ["ffmpeg", "-version"],
        check=True,
        capture_output=True,
        text=True,
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


class Handler(BaseHTTPRequestHandler):
    def _json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _voiceover_job_id(self, suffix=""):
        pattern = rf"^/voiceovers/([^/]+){suffix}$"
        match = re.fullmatch(pattern, self.path)
        if not match:
            return None

        job_id = match.group(1)
        if not JOB_ID_RE.fullmatch(job_id):
            return None

        return job_id.lower()

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

    def do_GET(self):
        if self.path == "/healthz":
            body = {
                "status": "ok",
                "service": "media-worker",
                "ffmpeg": ffmpeg_version(),
            }
            self._json(200, body)
            return

        job_id = self._voiceover_job_id("/metadata")
        if job_id is not None:
            path = VOICEOVER_ROOT / job_id / "final.mp3"
            if not path.is_file():
                self._json(404, {"error": "voiceover_not_found"})
                return

            try:
                probe = ffprobe_audio(path)
                payload = {
                    "status": "ready",
                    "job_id": job_id,
                    "storage_path": str(path),
                    "sha256": file_sha256(path),
                    "bytes": path.stat().st_size,
                    **probe,
                }
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

        self._json(404, {"error": "not_found"})

    def do_POST(self):
        job_id = self._voiceover_job_id()
        if job_id is None:
            self._json(404, {"error": "not_found"})
            return

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
                payload = {
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

        self._json(201, payload)

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    VOICEOVER_ROOT.mkdir(parents=True, exist_ok=True)
    ThreadingHTTPServer(("0.0.0.0", 3001), Handler).serve_forever()
