"""Exercise the read-only MP4 audit with isolated ffprobe/PCM fixtures."""
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("audit_final_media", "scripts/audit_final_media.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
job_id = "11111111-1111-4111-8111-111111111111"
segments = [
    {"start_ms": i * 3200, "end_ms": (i + 1) * 3200,
     "asset_sha256": f"{i:064x}"}
    for i in range(8)
] + [{"start_ms": 25600, "end_ms": 30000, "asset_sha256": f"{8:064x}"}]
manifest = {
    "sha256": "video-hash", "input_audio_sha256": "audio-hash",
    "audio_duration_ms": 28800, "target_duration_ms": 30000,
    "segments": segments,
}

class FakePath:
    def __init__(self, value):
        self.value = str(value)

    def __truediv__(self, component):
        return FakePath(self.value + "/" + component)

    def read_text(self):
        return json.dumps(manifest)

    def stat(self):
        return type("Stat", (), {"st_size": 123456})()

    def __str__(self):
        return self.value


def fake_run(*args):
    if args[0] == "ffprobe":
        return json.dumps({
            "format": {"duration": f"{manifest['target_duration_ms'] / 1000:.3f}"},
            "streams": [
                {"codec_type": "video", "width": 1080, "height": 1920,
                 "codec_name": "h264", "pix_fmt": "yuv420p", "r_frame_rate": "30/1"},
                {"codec_type": "audio", "codec_name": "aac",
                 "duration": f"{manifest['audio_duration_ms'] / 1000:.3f}"},
            ],
        }).encode()
    return b""

with patch.object(module, "Path", FakePath), patch.object(module, "run", fake_run), \
     patch.object(module, "pcm", lambda _path: [100] * 10), \
     patch.object(module, "sha", lambda path: "video-hash" if path.value.endswith("mp4") else "audio-hash"):
    result = module.audit(job_id, 30)
    assert result["passed"], result["gates"]
    assert result["target_duration_ms"] == 30000
    manifest["audio_duration_ms"] = 27000
    assert not module.audit(job_id, 30)["gates"]["accepted_audio_window"]
    manifest["audio_duration_ms"] = 33456
    manifest["target_duration_ms"] = 33456
    segments[-1]["end_ms"] = 33456
    assert module.audit(job_id, 30)["gates"]["accepted_audio_window"]
    assert module.audit(job_id, 30)["gates"]["target_duration_contract"]

    manifest["audio_duration_ms"] = 34001
    manifest["target_duration_ms"] = 34001
    segments[-1]["end_ms"] = 34001
    assert not module.audit(job_id, 30)["gates"]["accepted_audio_window"]
print("audit: short accepted/rejected and 34s natural-overrun contract verified")
