"""Classify one Google API Keys denial without retaining the response body."""
import datetime, json, os, re, subprocess, tempfile, uuid
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

ROOT=Path("/opt/ai-short-form-content-factory")
OUT=ROOT/"acceptance/factory-v3/key-owner-after-service-enable-20261028.json"
CONTAINER="ai-short-form-n8n"
GEMINI_ID="V3GeminiFreeTier20261005"
GOOGLE_ID="8KbFC6GBZOd18bzG"
REMOTE="/tmp/key-denial-"+uuid.uuid4().hex
record={
 "diagnostic_id":"v3-key-owner-after-service-enable-20261028",
 "credential_ids":{"gemini":GEMINI_ID,"google_oauth":GOOGLE_ID},
 "http_calls_started":0,"max_http_calls":2,
 "generation_calls":0,"search_calls":0,"tts_calls":0,"billing_mutations":0,
 "calls":[],"started_at":datetime.datetime.now(datetime.timezone.utc).isoformat()
}
remote_created=False

class Stop(Exception):
 def __init__(self,reason): self.reason=reason

class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs): return None

def docker(*args):
 p=subprocess.run(["sudo","docker",*args],capture_output=True,timeout=30)
 if p.returncode: raise Stop("credential_export_failed")
 return p.stdout

def export(credential_id,tmp):
 target=REMOTE+"/"+credential_id+".json"
 docker("exec",CONTAINER,"n8n","export:credentials","--id",credential_id,"--decrypted","--output",target)
 local=Path(tmp)/(credential_id+".json")
 docker("cp",CONTAINER+":"+target,str(local))
 local.chmod(0o600)
 values=json.loads(local.read_text())
 if len(values)!=1 or values[0].get("id")!=credential_id: raise Stop("credential_identity_mismatch")
 data=values[0].get("data")
 return json.loads(data) if isinstance(data,str) else data

def safe(value):
 return value if isinstance(value,str) and re.fullmatch(r"[A-Za-z0-9._:/-]{1,120}",value) else None

def request(kind,method,url,body=None,token=None):
 if record["http_calls_started"]>=2: raise Stop("http_call_budget_exceeded")
 headers={"User-Agent":"ContentFactoryV3/1.0","Accept":"application/json"}
 payload=None
 if token: headers["Authorization"]="Bearer "+token
 if body is not None:
  headers["Content-Type"]="application/x-www-form-urlencoded"
  payload=urlencode(body).encode()
 record["http_calls_started"]+=1
 entry={"kind":kind,"status":"unknown"}
 record["calls"].append(entry)
 try:
  response=build_opener(NoRedirect()).open(Request(url,data=payload,headers=headers,method=method),timeout=8)
  with response: status=response.status; raw=response.read(1024*1024+1)
 except HTTPError as e:
  status=e.code; raw=e.read(1024*1024+1)
 except Exception:
  raise Stop("transport_error")
 entry["status"]=status
 if len(raw)>1024*1024: raise Stop("response_too_large")
 try: value=json.loads(raw)
 except Exception: raise Stop("response_invalid")
 if status!=200:
  err=value.get("error",{}) if isinstance(value,dict) else {}
  if isinstance(err,dict):
   entry["error_status"]=safe(err.get("status"))
   for detail in err.get("details",[]) if isinstance(err.get("details"),list) else []:
    if not isinstance(detail,dict): continue
    metadata=detail.get("metadata",{})
    if not isinstance(metadata,dict): metadata={}
    for key in ("reason","domain","permission","service","consumer"):
     candidate=safe(detail.get(key)) or safe(metadata.get(key))
     if candidate: entry[key]=candidate
  raise Stop(kind+"_rejected")
 return value

try:
 if OUT.exists(): raise Stop("diagnostic_already_recorded_do_not_repeat")
 docker("exec",CONTAINER,"mkdir","-m","700",REMOTE)
 remote_created=True
 with tempfile.TemporaryDirectory(prefix="key-denial-",dir="/tmp") as tmp:
  gemini=export(GEMINI_ID,tmp)
  key=gemini.get("apiKey")
  if not isinstance(key,str) or not key: raise Stop("selected_key_missing")
  google=export(GOOGLE_ID,tmp)
  token_data=google.get("oauthTokenData",{})
  if isinstance(token_data,str): token_data=json.loads(token_data)
  refresh=token_data.get("refresh_token")
  client_id=google.get("clientId")
  client_secret=google.get("clientSecret")
  if not all(isinstance(x,str) and x for x in (refresh,client_id,client_secret)):
   raise Stop("google_oauth_refresh_unavailable")
  auth=request("oauth_refresh","POST","https://oauth2.googleapis.com/token",{
   "grant_type":"refresh_token","refresh_token":refresh,
   "client_id":client_id,"client_secret":client_secret
  })
  token=auth.get("access_token")
  if not isinstance(token,str) or not token: raise Stop("access_token_missing")
  lookup="https://apikeys.googleapis.com/v2/keys:lookupKey?"+urlencode({"keyString":key})
  owner=request("key_owner","GET",lookup,token=token)
  parent=owner.get("parent","")
  match=re.fullmatch(r"projects/([0-9]+)/locations/global",parent)
  if not match: raise Stop("selected_key_project_unconfirmed")
  resource=owner.get("name","")
  if not isinstance(resource,str) or not re.fullmatch(r"projects/[0-9]+/locations/global/keys/[A-Za-z0-9-]{1,100}",resource):
   raise Stop("key_resource_identity_invalid")
  record["key_owner_parent_project_number"]=match.group(1)
  record["key_resource_id"]=resource.rsplit("/",1)[-1]
  record["status"]="passed"
except Stop as e:
 record["status"]="blocked"
 record["stop_reason"]=e.reason
except Exception as e:
 record["status"]="blocked"
 record["stop_reason"]=type(e).__name__
finally:
 if remote_created:
  try:
   docker("exec",CONTAINER,"rm","-rf",REMOTE)
   record["credential_exports_removed"]=True
  except Exception:
   record["credential_exports_removed"]=False
 record["finished_at"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 fd=os.open(OUT,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,"w") as f:
  json.dump(record,f,indent=2)
  f.write(chr(10))
 print(json.dumps(record))