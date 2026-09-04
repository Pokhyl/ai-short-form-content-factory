from __future__ import annotations

import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "config" / "v5-upstreams.lock.json").read_text(encoding="utf-8"))
UPSTREAM = Path(os.environ.get("OPENNOLAN_ROOT") or LOCK["opennolan"]["checkout"])
EXPECTED_COMMIT = LOCK["opennolan"]["commit"]
SECRETS_ENV = Path(os.environ.get("V5_SECRETS_ENV", "/opt/ai-short-form-content-factory/.env"))
if SECRETS_ENV.is_file():
    load_dotenv(SECRETS_ENV, override=False)


def cmd(args: list[str]) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()


def main() -> int:
    failures: list[str] = []
    forbidden_hits = []
    for source in (ROOT / "v5").glob("*.py"):
        text = source.read_text(encoding="utf-8")
        for forbidden in ("prototype.v4", "services.v4", "VerticalShort", "SequenceShort"):
            if forbidden in text and source.name != "preflight.py":
                forbidden_hits.append(f"{source.name}:{forbidden}")

    report: dict[str, object] = {
        "architecture": "v5_asset_first_agentic_editor",
        "v4_imported": bool(forbidden_hits),
        "v4_forbidden_hits": forbidden_hits,
        "upstream": {},
        "runtime": {},
        "tools": {},
    }

    if forbidden_hits:
        failures.append("V5 source contains forbidden V4 dependency: " + ", ".join(forbidden_hits))

    if not UPSTREAM.is_dir():
        failures.append(f"OpenNolan checkout missing: {UPSTREAM}")
    else:
        try:
            actual = cmd(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"])
        except Exception as exc:
            actual = f"ERROR:{exc}"
        report["upstream"] = {"path": str(UPSTREAM), "expected_commit": EXPECTED_COMMIT, "actual_commit": actual}
        if actual != EXPECTED_COMMIT:
            failures.append(f"OpenNolan pin mismatch: {actual} != {EXPECTED_COMMIT}")

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    report["runtime"] = {
        "python": sys.version.split()[0],
        "ffmpeg": ffmpeg,
        "ffprobe": ffprobe,
        "faster_whisper": importlib.metadata.version("faster-whisper"),
        "edge_tts": importlib.metadata.version("edge-tts"),
    }
    if not ffmpeg or not ffprobe:
        failures.append("ffmpeg/ffprobe unavailable")

    sys.path.insert(0, str(UPSTREAM))
    try:
        from tools.video.stock_sources import source_summary
        from tools.video.direct_clip_search import DirectClipSearch
        from tools.video.video_compose import VideoCompose
        from tools.analysis.transcriber import Transcriber

        summary = source_summary()
        report["tools"] = {
            "stock_sources": summary,
            "direct_clip_search": str(DirectClipSearch().get_status()),
            "video_compose": str(VideoCompose().get_status()),
            "transcriber": str(Transcriber().get_status()),
        }
        if not summary.get("available_source_names"):
            failures.append("no OpenNolan stock source is available")
        if "AVAILABLE" not in str(VideoCompose().get_status()).upper():
            failures.append("OpenNolan VideoCompose unavailable")
        if "AVAILABLE" not in str(Transcriber().get_status()).upper():
            failures.append("OpenNolan Transcriber unavailable")
    except Exception as exc:
        failures.append(f"OpenNolan tool import/preflight failed: {type(exc).__name__}: {exc}")

    report["ok"] = not failures
    report["failures"] = failures
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
