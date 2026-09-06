"""Verify real import cardinality, not just n8n's successful process exit."""
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
workflows = []
for path in sorted((ROOT / "n8n/workflows").glob("*.json")):
    value = json.loads(path.read_text())
    workflows.extend(value if isinstance(value, list) else [value])
with tempfile.TemporaryDirectory(prefix="content-factory-import-") as directory:
    source = Path(directory) / "workflows.json"
    source.write_text(json.dumps(workflows))
    result = subprocess.run([
        "docker", "run", "--rm", "--network", "none", "--entrypoint", "n8n",
        "-v", f"{source}:/workflows.json:ro", "n8nio/n8n:2.33.3",
        "import:workflow", "--input=/workflows.json",
    ], text=True, capture_output=True)
    output = result.stdout + result.stderr
    if result.returncode or f"Successfully imported {len(workflows)} workflows." not in output:
        raise RuntimeError(output)
    if "Skipping invalid workflow" in output:
        raise RuntimeError(output)
print(f"N8N_IMPORT_CONTRACT_PASS: {len(workflows)} workflows on 2.33.3")
