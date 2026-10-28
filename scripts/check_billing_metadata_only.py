"""One-shot, metadata-only Google billing diagnostic; never generates content."""
import datetime
import json
import os
import re
from pathlib import Path

from factory_v3.credential_http import CredentialHTTP
from factory_v3.runtime import load_settings

PLAN_PATH = Path("/tmp/billing-metadata-only-plan.json")
plan = json.loads(PLAN_PATH.read_text())
diagnostic_id = plan.get("diagnostic_id")
if not isinstance(diagnostic_id, str) or not re.fullmatch(r"[a-zA-Z0-9-]{8,80}", diagnostic_id):
    raise ValueError("bounded diagnostic ID required")
if plan.get("operation") != "billing" or plan.get("max_http_calls") != 1:
    raise ValueError("one-call billing-only plan required")
revision = os.environ.get("FACTORY_V3_REVISION", "")
if not re.fullmatch(r"[0-9a-f]{40}", revision) or plan.get("runtime_revision") != revision:
    raise ValueError("exact planned runtime revision required")

settings = load_settings("/run/factory-v3/settings.json")
proof = settings.get("free_tier_proof", {})
project_id = proof.get("project_id")
if (not isinstance(project_id, str) or not project_id
        or proof.get("billing_enabled") is not False
        or settings.get("gemini_free_tier_confirmed") is not True):
    raise ValueError("existing confirmed free-only proof required")
if plan.get("project_id") != project_id:
    raise ValueError("plan project binding changed")

folder = Path("/data/checks") / ("billing-metadata-only-" + diagnostic_id)
folder.mkdir(mode=0o700, parents=False, exist_ok=False)
report = {
    "diagnostic_id": diagnostic_id,
    "runtime_revision": revision,
    "operation": "billing",
    "max_http_calls": 1,
    "http_calls_started": 0,
    "generation_calls": 0,
    "search_calls": 0,
    "tts_calls": 0,
    "state": "prepared",
    "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}

def save():
    temp = folder / "receipt.tmp"
    with temp.open("w") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(folder / "receipt.json")

def safe_error_receipt(error):
    receipt = getattr(error, "receipt", None)
    if not isinstance(receipt, dict):
        return None
    allowed = ("status", "error_status", "error_reason", "gateway_execution_id")
    return {key: receipt[key] for key in allowed
            if isinstance(receipt.get(key), (int, str))
            and not isinstance(receipt.get(key), bool)}

save()
gateway = CredentialHTTP(settings["broker_token"])
report["state"] = "request_started"
report["http_calls_started"] = 1
report["request_started_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
save()
try:
    response = gateway.metadata("billing", {"project_id": project_id})
    body = response.get("body") if isinstance(response, dict) else None
    project_matches = isinstance(body, dict) and body.get("projectId") == project_id
    billing_disabled = project_matches and body.get("billingEnabled") is False
    report.update(
        state="confirmed_free" if response.get("status") == 200 and billing_disabled else "unknown",
        http_status=response.get("status"),
        project_matches=project_matches,
        billing_disabled=billing_disabled,
    )
except BaseException as error:
    report.update(
        state="unknown",
        error_type=type(error).__name__,
        error_receipt=safe_error_receipt(error),
    )
finally:
    report["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save()

print(json.dumps({
    "diagnostic_id": report["diagnostic_id"],
    "state": report["state"],
    "http_calls_started": report["http_calls_started"],
    "http_status": report.get("http_status", report.get("error_receipt", {}).get("status")),
    "billing_disabled": report.get("billing_disabled"),
    "receipt": str(folder / "receipt.json"),
}, ensure_ascii=False))
