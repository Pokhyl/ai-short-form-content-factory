#!/usr/bin/env python3
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "free-only-policy.json"
policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
prod = policy["production"]

allowed_models = {
    prod["external_ai"]["text"]["model"],
    prod["external_ai"]["tts"]["model"],
}
forbidden_providers = {x.lower() for x in prod["forbidden_external_providers"]}
forbidden_purposes = {x.lower().replace("_", "-") for x in prod["forbidden_external_purposes"]}

scan_roots = [
    ROOT / "compose.yaml",
    ROOT / "n8n",
    ROOT / "src",
    ROOT / "services",
]

files = []
for root in scan_roots:
    if not root.exists():
        continue
    if root.is_file():
        files.append(root)
    else:
        files.extend(
            p for p in root.rglob("*")
            if p.is_file() and ".git" not in p.parts
        )

violations = []
gemini_model_re = re.compile(r"gemini-[a-z0-9.\-]+", re.I)

for path in files:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    low = text.lower()
    rel = path.relative_to(ROOT)

    for provider in forbidden_providers:
        pattern = rf"(?<![a-z0-9]){re.escape(provider)}(?![a-z0-9])"
        if re.search(pattern, low):
            violations.append(f"{rel}: forbidden external provider reference: {provider}")

    for purpose in forbidden_purposes:
        candidates = {purpose, purpose.replace("-", "_"), purpose.replace("-", " ")}
        if any(c in low for c in candidates):
            violations.append(f"{rel}: forbidden external purpose reference: {purpose}")

    for model in gemini_model_re.findall(text):
        normalized = model.lower()
        if normalized not in {m.lower() for m in allowed_models}:
            violations.append(f"{rel}: unapproved Gemini model: {model}")

workflow_files = list((ROOT / "n8n" / "workflows").glob("*.json")) if (ROOT / "n8n" / "workflows").exists() else []
tts_hits = 0
for wf in workflow_files:
    text = wf.read_text(encoding="utf-8").lower()
    tts_model = prod["external_ai"]["tts"]["model"].lower()
    tts_hits += text.count(tts_model)

if tts_hits > 1:
    violations.append(
        f"n8n/workflows: TTS model appears {tts_hits} times; production policy allows one TTS path"
    )

if prod.get("paid_fallbacks") is not False:
    violations.append("config/free-only-policy.json: paid_fallbacks must be false")

if violations:
    print("FREE-ONLY POLICY: FAIL")
    for item in sorted(set(violations)):
        print(f"- {item}")
    sys.exit(1)

print("FREE-ONLY POLICY: PASS")
print("Allowed external AI models:")
for model in sorted(allowed_models):
    print(f"- {model}")
print(f"Static TTS path count: {tts_hits}")
