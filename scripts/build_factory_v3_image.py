"""Secret-free image build with a disk-headroom preflight."""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

MINIMUM_FREE_BYTES = 5 * 1024 ** 3 // 2
ROOT = Path(__file__).resolve().parents[1]


def require_disk_headroom(path, minimum_bytes=MINIMUM_FREE_BYTES):
    free_bytes = shutil.disk_usage(path).free
    if free_bytes < minimum_bytes:
        raise RuntimeError(
            f"refusing image build: {free_bytes} bytes free; "
            f"at least {minimum_bytes} bytes required"
        )
    return free_bytes


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--platform", default="linux/amd64")
    args = parser.parse_args(argv)

    # Fail before copying source or contacting Docker; do not fill the host
    # while a large image build has insufficient temporary space.
    require_disk_headroom(ROOT)

    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--",
         "factory_v3", "material_first", "scripts/audit_final_media.py"],
        cwd=ROOT, text=True
    ).strip()
    if dirty:
        raise ValueError("commit runtime source before building")

    with tempfile.TemporaryDirectory(prefix="factory-v3-build-") as tmp:
        context = Path(tmp)
        for name in ("factory_v3", "material_first", "factory_next"):
            shutil.copytree(
                ROOT / name, context / name,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
        (context / "scripts").mkdir()
        for name in ("audit_final_media.py", "replay_material_preparation.py"):
            shutil.copy2(ROOT / "scripts" / name, context / "scripts" / name)
        result = subprocess.run(
            ["docker", "buildx", "build", "--platform", args.platform, "--load",
             "--build-arg", "SOURCE_REVISION=" + head,
             "--label", "org.opencontainers.image.revision=" + head,
             "-f", str(context / "factory_v3" / "Dockerfile"),
             "-t", args.tag, str(context)],
            capture_output=True, text=True, timeout=110,
        )
        log = result.stdout + result.stderr
        (ROOT / "acceptance/factory-v3/image-build-current.txt").write_text(log)
        print(log[-1200:])
        if result.returncode:
            raise RuntimeError("image build failed; inspect actual effects")

    identifier = subprocess.check_output(
        ["docker", "image", "inspect", "-f", "{{.Id}}", args.tag], text=True
    ).strip()
    manifest = {
        "tag": args.tag, "image_id": identifier,
        "platform": args.platform, "source_commit": head, "deployed": False,
    }
    (ROOT / "acceptance/factory-v3/image-current.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
