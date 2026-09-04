from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "config" / "v5-upstreams.lock.json"
LOCK = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
OPENNOLAN_ROOT = Path(os.environ.get("OPENNOLAN_ROOT") or LOCK["opennolan"]["checkout"])
EXPECTED_OPENNOLAN_COMMIT = LOCK["opennolan"]["commit"]
SECRETS_ENV = Path(os.environ.get("V5_SECRETS_ENV", "/opt/ai-short-form-content-factory/.env"))


def bootstrap() -> Path:
    """Load provider config and expose only the pinned upstream package."""
    if SECRETS_ENV.is_file():
        load_dotenv(SECRETS_ENV, override=False)
    if not OPENNOLAN_ROOT.is_dir():
        raise RuntimeError(f"OpenNolan checkout missing: {OPENNOLAN_ROOT}")
    actual = subprocess.check_output(
        ["git", "-C", str(OPENNOLAN_ROOT), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if actual != EXPECTED_OPENNOLAN_COMMIT:
        raise RuntimeError(f"OpenNolan pin mismatch: {actual} != {EXPECTED_OPENNOLAN_COMMIT}")
    path = str(OPENNOLAN_ROOT)
    if path not in sys.path:
        sys.path.insert(0, path)
    return OPENNOLAN_ROOT
