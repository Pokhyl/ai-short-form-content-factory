"""Real FFmpeg regression: natural audio ends before exact product video target."""
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
SCENE_IDS = [
    "22222222-2222-4222-8222-222222222222",
    "55555555-5555-4555-8555-555555555555",
]
SHOT_IDS = [
    "33333333-3333-4333-8333-333333333333",
    "66666666-6666-4666-8666-666666666666",
]
ASSET_IDS = [
    "44444444-4444-4444-8444-444444444444",
    "77777777-7777-4777-8777-777777777777",
]


def synth(path, seconds):
    subprocess.run([
        "ffmpeg", "-nostdin", "-y", "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={seconds}",
        "-c:a", "libmp3lame", "-b:a", "128k", str(path),
    ], check=True, capture_output=True, text=True, timeout=30)


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    media_worker.VOICEOVER_ROOT = root / "voiceovers"
    media_worker.VISUAL_ROOT = root / "visuals"
    media_worker.RENDER_ROOT = root / "renders"

    audio_dir = media_worker.VOICEOVER_ROOT / JOB_ID
    audio_dir.mkdir(parents=True)
    audio_path = audio_dir / "final.mp3"
    synth(audio_path, 28.48)
    audio = media_worker.ffprobe_audio(audio_path)
    assert 28464 <= audio["duration_ms"] < 30000, audio
    audio_sha = media_worker.file_sha256(audio_path)
    source_bytes = audio_path.read_bytes()

    scenes = []
    for i in range(2):
        visual_dir = media_worker.VISUAL_ROOT / JOB_ID / SHOT_IDS[i]
        visual_dir.mkdir(parents=True)
        image_path = visual_dir / "selected.ppm"
        width, height = 320, 480
        pixel = bytes([80 + 50 * i, 100, 120])
        image_path.write_bytes(
            f"P6\n{width} {height}\n255\n".encode()
            + pixel * (width * height)
        )
        scenes.append({
            "scene_uuid": SCENE_IDS[i],
            "shot_uuid": SHOT_IDS[i],
            "visual_asset_id": ASSET_IDS[i],
            "media_type": "photo",
            "asset_sha256": media_worker.file_sha256(image_path),
            "scene_order": i + 1,
            "segment_start_ms": 15000 * i,
            "segment_end_ms": 15000 * (i + 1),
            "speech_start_ms": 15000 * i,
            "speech_end_ms": 14000 if i == 0 else audio["duration_ms"] - 100,
            "asset_width": width,
            "asset_height": height,
            "asset_path": str(image_path),
        })

    render_dir = media_worker.RENDER_ROOT / JOB_ID
    render_dir.mkdir(parents=True)
    result = media_worker.render_final_video(
        JOB_ID, audio_sha, audio["duration_ms"], 30000, scenes, render_dir,
    )
    assert result["audio_duration_ms"] == audio["duration_ms"]
    assert result["target_duration_ms"] == 30000
    assert abs(result["duration_ms"] - 30000) <= 100, result["duration_ms"]
    assert (abs(result["muxed_audio_duration_ms"] - audio["duration_ms"])
            <= 100), result
    assert result["segments"][-1]["end_ms"] == 30000
    assert result["segments"][-1]["end_ms"] > audio["duration_ms"]
    assert result["qa_gates"]["audio_duration_match"] is True
    assert result["qa_gates"]["scene_coverage"] is True
    assert result["qa_gates"]["asset_hashes"] is True
    assert result["video_codec"] == "h264"
    assert result["audio_codec"] == "aac"
    assert (result["width"], result["height"]) == (1080, 1920)
    assert (result["fps_num"], result["fps_den"]) == (30, 1)
    assert media_worker.file_sha256(audio_path) == audio_sha
    assert audio_path.read_bytes() == source_bytes
    assert media_worker.file_sha256(render_dir / "final.mp4") == result["sha256"]

    for too_short_or_long in (27.0, 30.1):
        synth(audio_path, too_short_or_long)
        before = media_worker.ffprobe_audio(audio_path)["duration_ms"]
        try:
            media_worker.render_final_video(
                JOB_ID, media_worker.file_sha256(audio_path),
                before, 30000, scenes, render_dir,
            )
        except ValueError as exc:
            assert "render target/audio duration contract" in str(exc), exc
        else:
            raise AssertionError(f"unacceptable {before}ms audio was rendered")

print("render-target-duration-regression: PASS")
