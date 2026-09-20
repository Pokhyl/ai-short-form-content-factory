"""Read-only audit of an exact production MP4, run inside media-worker.

Usage: docker exec -i shorts-v2-media-worker-1 python3 - JOB_ID TARGET_SECONDS
       < scripts/audit_final_media.py
Prints JSON; never changes product artifacts or calls providers.
This supplements machine QA and does not grant HUMAN PASS.
"""

import array
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import uuid


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, timeout=180).stdout


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pcm(path):
    samples = array.array("h")
    samples.frombytes(run("ffmpeg", "-v", "error", "-i", str(path), "-vn",
                          "-f", "s16le", "-ar", "16000", "-ac", "1", "-"))
    if sys.byteorder != "little":
        samples.byteswap()
    return samples


def audit(job_id, target):
    job_id = str(uuid.UUID(job_id))
    if target not in (15, 30, 45, 60):
        raise ValueError("unsupported target duration")
    directory = Path("/data/renders") / job_id
    video = directory / "final.mp4"
    voice = Path("/data/voiceovers") / job_id / "final.mp3"
    manifest = json.loads((directory / "manifest.json").read_text())
    probe = json.loads(run("ffprobe", "-v", "error", "-show_streams",
                           "-show_format", "-of", "json", str(video)))
    streams = probe["streams"]
    videos = [s for s in streams if s["codec_type"] == "video"]
    audios = [s for s in streams if s["codec_type"] == "audio"]
    run("ffmpeg", "-v", "error", "-xerror", "-i", str(video), "-f", "null", "-")
    source, final = pcm(voice), pcm(video)
    n = min(len(source), len(final))
    energy_source = sum(x * x for x in source[:n])
    energy_final = sum(x * x for x in final[:n])
    correlation = sum(x * y for x, y in zip(source, final)) / math.sqrt(
        energy_source * energy_final)
    video_sha, audio_sha = sha(video), sha(voice)
    segments = manifest["segments"]
    expected_scenes = {15: 5, 30: 9, 45: 13, 60: 17}[target]
    gates = {
        "manifest_video_hash": video_sha == manifest["sha256"],
        "manifest_voice_hash": audio_sha == manifest["input_audio_sha256"],
        "full_decode": True,
        "stream_counts": len(streams) == 2 and len(videos) == len(audios) == 1,
        "video_format": len(videos) == 1 and all((
            videos[0]["width"] == 1080, videos[0]["height"] == 1920,
            videos[0]["codec_name"] == "h264", videos[0]["pix_fmt"] == "yuv420p",
            videos[0]["r_frame_rate"] == "30/1")),
        "audio_format": len(audios) == 1 and audios[0]["codec_name"] == "aac",
        "narration_preserved": correlation >= 0.99 and abs(len(source) - len(final)) <= 1600,
        "target_duration": abs(manifest["audio_duration_ms"] - target * 1000)
                           <= max(750, target * 50) + 50,
        "mux_duration": abs(round(float(probe["format"]["duration"]) * 1000)
                            - manifest["audio_duration_ms"]) <= 100,
        "scene_density": len(segments) == expected_scenes,
        "unique_assets": len({s["asset_sha256"] for s in segments}) == expected_scenes,
        "contiguous_coverage": bool(segments) and segments[0]["start_ms"] == 0
            and segments[-1]["end_ms"] == manifest["audio_duration_ms"]
            and all(a["end_ms"] == b["start_ms"] for a, b in zip(segments, segments[1:])),
    }
    return {"job_id": job_id, "sha256": video_sha, "bytes": video.stat().st_size,
            "duration_ms": round(float(probe["format"]["duration"]) * 1000),
            "audio_duration_ms": manifest["audio_duration_ms"],
            "audio_correlation": correlation, "scene_count": len(segments),
            "gates": gates, "passed": all(gates.values())}


if __name__ == "__main__":
    result = audit(sys.argv[1], int(sys.argv[2]))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)
