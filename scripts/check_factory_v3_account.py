"""Bounded project-only read-only diagnostics; never prints exported credentials."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import uuid
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from urllib.parse import urlencode
import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"acceptance/factory-v3/account-check.json"
PRIVATE = Path("/var/lib/factory-v3")
MODEL = "gemini-3.5-flash-lite"
IDS = {"gemini":"zsRz2tvE57EKe8zy", "google":"8KbFC6GBZOd18bzG"}
RECORD = {"diagnostic_id":"v3-account-boundary-20261005","generation_calls":0,
          "tts_calls":0,"billing_mutations":0,"calls":[],"free_tier_confirmed":False,
          "started_at":datetime.datetime.now(datetime.timezone.utc).isoformat()}
SECRET_PATH = "/tmp/factory-v3-account-" + uuid.uuid4().hex
CONTAINER = "ai-short-form-n8n"


class Stop(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def command(args, timeout=4):
    result = subprocess.run(args, capture_output=True, timeout=timeout)
    if result.returncode:
        raise Stop("credential_operation_failed")
    return result.stdout


def exported(credential_id, host_directory):
    destination = SECRET_PATH + "/" + credential_id + ".json"
    command(["docker","exec",CONTAINER,"n8n","export:credentials","--id",credential_id,
             "--decrypted","--output",destination], timeout=20)
    file = Path(host_directory)/("credential-" + credential_id + ".json")
    command(["docker","cp",CONTAINER+":"+destination,str(file)])
    file.chmod(0o600)
    value = json.loads(file.read_text())
    if len(value) != 1 or value[0]["id"] != credential_id:
        raise Stop("credential_identity_mismatch")
    data = value[0]["data"]
    return json.loads(data) if isinstance(data,str) else data


def request(kind, method, url, body=None, token=None):
    headers = {"User-Agent":"ContentFactoryV3/1.0","Accept":"application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if body is not None:
        encoded = urlencode(body).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    else:
        encoded = None
    try:
        response = build_opener(NoRedirect()).open(Request(url,data=encoded,headers=headers,method=method),timeout=8)
        with response:
            status = response.status
            raw = response.read(1024*1024+1)
    except HTTPError as error:
        status = error.code
        raw = error.read(1024*1024+1)
    except Exception:
        RECORD["calls"].append({"kind":kind,"status":"unknown"})
        raise Stop("metadata_result_unknown")
    receipt = {"kind":kind,"http_status":status}
    RECORD["calls"].append(receipt)
    if len(raw) > 1024*1024:
        raise Stop("metadata_size_exceeded")
    try:
        value = json.loads(raw)
    except (ValueError,UnicodeError):
        raise Stop("metadata_response_invalid")
    if status != 200:
        error_status = value.get("error",{}).get("status") if isinstance(value.get("error"),dict) else None
        if isinstance(error_status,str) and len(error_status) < 100:
            receipt["error_status"] = error_status
        raise Stop(kind+"_rejected")
    return value


def main():
    if OUT.exists():
        raise Stop("diagnostic_already_recorded_do_not_repeat")
    PRIVATE.mkdir(mode=0o700,parents=True,exist_ok=True)
    if PRIVATE.stat().st_mode & 0o077:
        raise Stop("private_directory_permissions_invalid")
    command(["docker","exec",CONTAINER,"mkdir","-m","700",SECRET_PATH])
    try:
        with tempfile.TemporaryDirectory(prefix="account-",dir=PRIVATE) as directory:
            gemini = exported(IDS["gemini"],directory)
            key = gemini.get("apiKey")
            if not isinstance(key,str) or not key:
                raise Stop("selected_gemini_key_missing")
            model = request("model_info","GET","https://generativelanguage.googleapis.com/v1beta/models/"+MODEL+"?"+urlencode({"key":key}))
            RECORD["model"] = {k:model.get(k) for k in ("name","supportedGenerationMethods","inputTokenLimit","outputTokenLimit")}
            if model.get("name") != "models/"+MODEL or "generateContent" not in model.get("supportedGenerationMethods",[]):
                raise Stop("selected_model_unavailable")
            google = exported(IDS["google"],directory)
            token_data = google.get("oauthTokenData",{})
            if isinstance(token_data,str):
                token_data = json.loads(token_data)
            refresh = token_data.get("refresh_token")
            if not refresh or not google.get("clientId") or not google.get("clientSecret"):
                raise Stop("selected_google_refresh_unavailable")
            auth = request("oauth_refresh","POST","https://oauth2.googleapis.com/token",
                {"grant_type":"refresh_token","refresh_token":refresh,"client_id":google["clientId"],"client_secret":google["clientSecret"]})
            token = auth.get("access_token")
            if not isinstance(token,str) or not token:
                raise Stop("refreshed_google_token_missing")
            owner = request("key_owner","GET","https://apikeys.googleapis.com/v2/keys:lookupKey?"+urlencode({"keyString":key}),token=token)
            parent = owner.get("parent","")
            import re
            match = re.fullmatch(r"projects/([0-9]+)/locations/global",parent)
            if not match:
                raise Stop("selected_key_project_unconfirmed")
            project = request("project_info","GET","https://cloudresourcemanager.googleapis.com/v3/projects/"+match.group(1),token=token)
            project_id = project.get("projectId")
            if not isinstance(project_id,str) or not re.fullmatch(r"[a-z][a-z0-9-]{4,62}",project_id):
                raise Stop("selected_project_identity_invalid")
            RECORD["project_id"] = project_id
            billing = request("billing_info","GET","https://cloudbilling.googleapis.com/v1/projects/"+project_id+"/billingInfo",token=token)
            RECORD["billing_enabled"] = billing.get("billingEnabled")
            if billing.get("projectId") != project_id or billing.get("billingEnabled") is not False:
                raise Stop("gemini_project_not_confirmed_unbilled")
            proof = {"billing_enabled":False,"model":MODEL,"project_id":project_id,
                     "credential_sha256":hashlib.sha256(key.encode()).hexdigest(),
                     "diagnostic_id":RECORD["diagnostic_id"],"verified_at":datetime.datetime.now(datetime.timezone.utc).isoformat()}
            path = PRIVATE/"gemini-free-tier-proof.json"
            fd = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,"w") as file:
                json.dump(proof,file)
            RECORD["free_tier_confirmed"] = True
            RECORD["status"] = "passed"
    finally:
        command(["docker","exec",CONTAINER,"rm","-rf",SECRET_PATH])


if __name__ == "__main__":
    if OUT.exists():
        print(json.dumps({"status":"already_recorded","repeat_blocked":True}))
        raise SystemExit(2)
    try:
        main()
    except Stop as error:
        RECORD["status"] = "blocked"
        RECORD["stop_reason"] = str(error)
    except Exception as error:
        RECORD["status"] = "blocked"
        RECORD["stop_reason"] = type(error).__name__
    RECORD["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    OUT.write_text(json.dumps(RECORD,indent=2)+"\n")
    print(json.dumps(RECORD))
    raise SystemExit(0 if RECORD["status"] == "passed" else 3)
