"""One-shot access-grant check for the exact Factory V3 Gemini credential."""
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "acceptance/factory-v3/account-check-after-owner-access-20261028.json"
PRIVATE_PARENT = Path("/tmp")
CONTAINER = "ai-short-form-n8n"
GEMINI_ID = "V3GeminiFreeTier20261005"
GOOGLE_ID = "8KbFC6GBZOd18bzG"
MODEL = "gemini-3.5-flash-lite"
MAX_HTTP_CALLS = 4
record = {
    "diagnostic_id": "v3-account-boundary-after-owner-access-20261028",
    "selected_model": MODEL,
    "credential_ids": {"gemini": GEMINI_ID, "google_oauth": GOOGLE_ID},
    "max_http_calls": MAX_HTTP_CALLS,
    "http_calls_started": 0,
    "generation_calls": 0,
    "search_calls": 0,
    "tts_calls": 0,
    "billing_mutations": 0,
    "calls": [],
    "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
remote_dir = "/tmp/factory-v3-access-" + uuid.uuid4().hex
remote_dir_created = False


class Stop(Exception):
    def __init__(self, reason):
        self.reason = reason


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def docker(*args, timeout=20):
    result = subprocess.run(["sudo", "docker", *args], capture_output=True, timeout=timeout)
    if result.returncode:
        raise Stop("credential_export_failed")
    return result.stdout


def export_credential(credential_id, host_dir):
    target = remote_dir + "/" + credential_id + ".json"
    docker("exec", CONTAINER, "n8n", "export:credentials", "--id", credential_id,
           "--decrypted", "--output", target, timeout=20)
    local = Path(host_dir) / (credential_id + ".json")
    docker("cp", CONTAINER + ":" + target, str(local))
    local.chmod(0o600)
    values = json.loads(local.read_text())
    if len(values) != 1 or values[0].get("id") != credential_id:
        raise Stop("credential_identity_mismatch")
    data = values[0].get("data")
    return json.loads(data) if isinstance(data, str) else data


def call(kind, method, url, body=None, token=None):
    if record["http_calls_started"] >= MAX_HTTP_CALLS:
        raise Stop("http_call_budget_exceeded")
    headers = {"User-Agent": "ContentFactoryV3/1.0", "Accept": "application/json"}
    payload = None
    if token:
        headers["Authorization"] = "Bearer " + token
    if body is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        payload = urlencode(body).encode()
    record["http_calls_started"] += 1
    entry = {"kind": kind, "status": "unknown"}
    record["calls"].append(entry)
    try:
        response = build_opener(NoRedirect()).open(
            Request(url, data=payload, headers=headers, method=method), timeout=8)
        with response:
            status = response.status
            raw = response.read(1024 * 1024 + 1)
    except HTTPError as error:
        status = error.code
        raw = error.read(1024 * 1024 + 1)
    except Exception:
        raise Stop("metadata_transport_error")
    entry["status"] = status
    if len(raw) > 1024 * 1024:
        raise Stop("metadata_response_too_large")
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        raise Stop("metadata_response_invalid")
    if status != 200:
        err = value.get("error", {}) if isinstance(value, dict) else {}
        error_status = err.get("status") if isinstance(err, dict) else None
        if isinstance(error_status, str) and re.fullmatch(r"[A-Z_]{1,100}", error_status):
            entry["error_status"] = error_status
        raise Stop(kind + "_rejected")
    return value


def main():
    if OUT.exists():
        raise Stop("diagnostic_already_recorded_do_not_repeat")
    if not PRIVATE_PARENT.is_dir():
        raise Stop("temporary_directory_unavailable")
    docker("exec", CONTAINER, "mkdir", "-m", "700", remote_dir)
    global remote_dir_created
    remote_dir_created = True
    with tempfile.TemporaryDirectory(prefix="v3-access-", dir=PRIVATE_PARENT) as local_dir:
        gemini = export_credential(GEMINI_ID, local_dir)
        key = gemini.get("apiKey")
        if not isinstance(key, str) or not key:
            raise Stop("selected_gemini_key_missing")
        google = export_credential(GOOGLE_ID, local_dir)
        token_data = google.get("oauthTokenData", {})
        if isinstance(token_data, str):
            token_data = json.loads(token_data)
        refresh = token_data.get("refresh_token")
        client_id, client_secret = google.get("clientId"), google.get("clientSecret")
        if not all(isinstance(v, str) and v for v in (refresh, client_id, client_secret)):
            raise Stop("google_oauth_refresh_unavailable")
        auth = call("oauth_refresh", "POST", "https://oauth2.googleapis.com/token", {
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": client_id,
            "client_secret": client_secret,
        })
        token = auth.get("access_token")
        if not isinstance(token, str) or not token:
            raise Stop("google_oauth_token_missing")
        owner = call("key_owner", "GET",
            "https://apikeys.googleapis.com/v2/keys:lookupKey?" +
            urlencode({"keyString": key}), token=token)
        parent = owner.get("parent", "")
        match = re.fullmatch(r"projects/([0-9]+)/locations/global", parent)
        if not match:
            raise Stop("selected_key_project_unconfirmed")
        project = call("project_info", "GET",
            "https://cloudresourcemanager.googleapis.com/v3/projects/" + match.group(1),
            token=token)
        project_id = project.get("projectId")
        if not isinstance(project_id, str) or not re.fullmatch(r"[a-z][a-z0-9-]{4,62}", project_id):
            raise Stop("selected_project_identity_invalid")
        record["project_id"] = project_id
        billing = call("billing_info", "GET",
            "https://cloudbilling.googleapis.com/v1/projects/" + project_id + "/billingInfo",
            token=token)
        enabled = billing.get("billingEnabled")
        record["billing_enabled"] = enabled
        if billing.get("projectId") != project_id or enabled is not False:
            raise Stop("gemini_project_not_confirmed_unbilled")
        record["status"] = "passed"


if __name__ == "__main__":
    try:
        main()
    except Stop as error:
        record["status"] = "blocked"
        record["stop_reason"] = error.reason
    except Exception as error:
        record["status"] = "blocked"
        record["stop_reason"] = type(error).__name__
    finally:
        if remote_dir_created:
            try:
                docker("exec", CONTAINER, "rm", "-rf", remote_dir, timeout=10)
                record["credential_exports_removed"] = True
            except Exception:
                record["credential_exports_removed"] = False
        record["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if not OUT.exists():
            OUT.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(OUT, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as stream:
                json.dump(record, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
        print(json.dumps({
            "diagnostic_id": record["diagnostic_id"],
            "status": record.get("status"),
            "http_calls_started": record["http_calls_started"],
            "calls": record["calls"],
            "billing_enabled": record.get("billing_enabled"),
            "stop_reason": record.get("stop_reason"),
            "receipt": str(OUT),
            "credential_exports_removed": record.get("credential_exports_removed"),
        }, ensure_ascii=False))
