"""Real FFmpeg regression for bounded audio padding + exact product duration."""
import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "services" / "media-worker" / "server.py"

spec = importlib.util.spec_from_file_location("media_worker", SERVER)
media_worker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(media_worker)

JOB_ID = "11111111-1111-4111-8111-111111111111"
SCENE_ID = "22222222-2222-4222-8222-222222222222"
SHOT_ID = "33333333-3333-4333-8333-333333333333"
ASSET_ID = "44444444-4444-4444-8444-444444444444"

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    media_worker.VOICEOVER_ROOT = root / "voiceovers"
    media_worker.VISUAL_ROOT = root / "visuals"
    media_worker.RENDER_ROOT = root / "renders"

    audio_dir = media_worker.VOICEOVER_ROOT / JOB_ID
    audio_dir.mkdir(parents=True)
    audio_path = audio_dir / "final.mp3"

    subprocess.run(
        [
            "ffmpeg", "-nostdin", "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=0.70",
            "-c:a", "libmp3lame", "-b:a", "128k",
            str(audio_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )

    before = media_worker.ffprobe_audio(audio_path)
    padded = media_worker.pad_mp3_to_minimum_duration(audio_path, 1000)
    after = media_worker.ffprobe_audio(audio_path)

    assert before["duration_ms"] < 1000
    assert 1000 <= after["duration_ms"] <= 1150
    assert padded["source_duration_ms"] == before["duration_ms"]
    assert padded["padding_ms"] == after["duration_ms"] - before["duration_ms"]

    visual_dir = media_worker.VISUAL_ROOT / JOB_ID / SHOT_ID
    visual_dir.mkdir(parents=True)
    image_path = visual_dir / "selected.ppm"
    width, height = 320, 480
    image_path.write_bytes(
        f"P6\n{width} {height}\n255\n".encode()
        + b"\x80\x80\x80" * (width * height)
    )

    target_duration_ms = 1200
    render_dir = media_worker.RENDER_ROOT / JOB_ID
    render_dir.mkdir(parents=True)

    scenes = [
        {
            "scene_uuid": SCENE_ID,
            "shot_uuid": SHOT_ID,
            "visual_asset_id": ASSET_ID,
            "media_type": "photo",
            "asset_sha256": media_worker.file_sha256(image_path),
            "scene_order": 1,
            "segment_start_ms": 0,
            "segment_end_ms": target_duration_ms,
            "speech_start_ms": 0,
            "speech_end_ms": min(after["duration_ms"], 900),
            "asset_width": width,
            "asset_height": height,
            "asset_path": str(image_path),
        }
    ]

    result = media_worker.render_final_video(
        JOB_ID,
        media_worker.file_sha256(audio_path),
        after["duration_ms"],
        target_duration_ms,
        scenes,
        render_dir,
    )

    assert result["audio_duration_ms"] == after["duration_ms"]
    assert result["target_duration_ms"] == target_duration_ms
    assert abs(result["duration_ms"] - target_duration_ms) <= 100
    assert result["segments"][-1]["end_ms"] == target_duration_ms
    assert result["qa_passed"] is True

print("render-target-duration-regression: PASS")
