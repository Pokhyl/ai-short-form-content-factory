"""Inspect identity and billing state for the verified Gemini key owner project."""
import datetime, json, os, re, subprocess, tempfile, uuid
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

ROOT=Path("/opt/ai-short-form-content-factory")
OUT=ROOT/"acceptance/factory-v3/project-billing-after-key-owner-20261028.json"
CONTAINER="ai-short-form-n8n"
GOOGLE_ID="8KbFC6GBZOd18bzG"
PROJECT_NUMBER="529636078126"
REMOTE="/tmp/project-billing-"+uuid.uuid4().hex
record={
 "diagnostic_id":"v3-project-billing-after-key-owner-20261028",
 "credential_id":GOOGLE_ID,
 "project_number":PROJECT_NUMBER,
 "max_http_calls":3,"http_calls_started":0,
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

def safe(v):
 return v if isinstance(v,str) and re.fullmatch(r"[A-Za-z0-9._:/-]{1,120}",v) else None

def get(kind,url,token):
 if record["http_calls_started"]>=3: raise Stop("http_call_budget_exceeded")
 record["http_calls_started"]+=1
 entry={"kind":kind,"status":"unknown"}; record["calls"].append(entry)
 headers={"User-Agent":"ContentFactoryV3/1.0","Accept":"application/json","Authorization":"Bearer "+token}
 try:
  response=build_opener(NoRedirect()).open(Request(url,headers=headers,method="GET"),timeout=12)
  with response: status=response.status; raw=response.read(1024*1024+1)
 except HTTPError as e:
  status=e.code; raw=e.read(1024*1024+1)
 except Exception: raise Stop(kind+"_transport_error")
 entry["status"]=status
 if len(raw)>1024*1024: raise Stop("response_too_large")
 try: value=json.loads(raw)
 except Exception: raise Stop("response_invalid")
 if status!=200:
  err=value.get("error",{}) if isinstance(value,dict) else {}
  if isinstance(err,dict):
   entry["error_status"]=safe(err.get("status"))
   for d in err.get("details",[]) if isinstance(err.get("details"),list) else []:
    if not isinstance(d,dict): continue
    meta=d.get("metadata",{})
    if not isinstance(meta,dict): meta={}
    for k in ("reason","domain","service","consumer","permission"):
     v=safe(d.get(k)) or safe(meta.get(k))
     if v: entry[k]=v
  raise Stop(kind+"_rejected")
 return value

try:
 if OUT.exists(): raise Stop("diagnostic_already_recorded_do_not_repeat")
 docker("exec",CONTAINER,"mkdir","-m","700",REMOTE); remote_created=True
 with tempfile.TemporaryDirectory(prefix="project-billing-",dir="/tmp") as tmp:
  target=REMOTE+"/"+GOOGLE_ID+".json"
  docker("exec",CONTAINER,"n8n","export:credentials","--id",GOOGLE_ID,"--decrypted","--output",target)
  local=Path(tmp)/(GOOGLE_ID+".json"); docker("cp",CONTAINER+":"+target,str(local)); local.chmod(0o600)
  values=json.loads(local.read_text())
  if len(values)!=1 or values[0].get("id")!=GOOGLE_ID: raise Stop("credential_identity_mismatch")
  data=values[0].get("data")
  if isinstance(data,str): data=json.loads(data)
  token_data=data.get("oauthTokenData",{})
  if isinstance(token_data,str): token_data=json.loads(token_data)
  refresh=token_data.get("refresh_token")
  client_id=data.get("clientId"); client_secret=data.get("clientSecret")
  if not all(isinstance(x,str) and x for x in (refresh,client_id,client_secret)): raise Stop("google_oauth_refresh_unavailable")
  auth_data={"grant_type":"refresh_token","refresh_token":refresh,"client_id":client_id,"client_secret":client_secret}
  if record["http_calls_started"]>=3: raise Stop("http_call_budget_exceeded")
  record["http_calls_started"]+=1; record["calls"].append({"kind":"oauth_refresh","status":"unknown"})
  req=Request("https://oauth2.googleapis.com/token",data=__import__("urllib.parse",fromlist=["urlencode"]).urlencode(auth_data).encode(),headers={"User-Agent":"ContentFactoryV3/1.0","Accept":"application/json","Content-Type":"application/x-www-form-urlencoded"},method="POST")
  try:
   response=build_opener(NoRedirect()).open(req,timeout=12)
   with response: status=response.status; raw=response.read(1024*1024+1)
  except HTTPError as e: status=e.code; raw=e.read(1024*1024+1)
  except Exception: raise Stop("oauth_refresh_transport_error")
  record["calls"][-1]["status"]=status
  if status!=200:
   try:
    v=json.loads(raw); er=v.get("error")
    if isinstance(er,str) and re.fullmatch(r"[a-z][a-z0-9_]{1,63}",er): record["calls"][-1]["error_code"]=er
   except Exception: pass
   raise Stop("oauth_refresh_rejected")
  auth=json.loads(raw); token=auth.get("access_token")
  if not isinstance(token,str) or not token: raise Stop("access_token_missing")
  project=get("project_info","https://cloudresourcemanager.googleapis.com/v3/projects/"+PROJECT_NUMBER,token)
  project_id=project.get("projectId")
  if not isinstance(project_id,str) or not re.fullmatch(r"[a-z][a-z0-9-]{4,62}",project_id): raise Stop("project_identity_invalid")
  record["project_id"]=project_id
  billing=get("billing_info","https://cloudbilling.googleapis.com/v1/projects/"+quote(project_id,safe="")+"/billingInfo",token)
  if billing.get("projectId")!=project_id: raise Stop("billing_project_identity_mismatch")
  record["billing_enabled"]=billing.get("billingEnabled")
  record["status"]="passed_free_billing" if billing.get("billingEnabled") is False else "billing_enabled"
except Stop as e:
 record["status"]="blocked"; record["stop_reason"]=e.reason
except Exception as e:
 record["status"]="blocked"; record["stop_reason"]=type(e).__name__
finally:
 if remote_created:
  try: docker("exec",CONTAINER,"rm","-rf",REMOTE); record["credential_export_removed"]=True
  except Exception: record["credential_export_removed"]=False
 record["finished_at"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 fd=os.open(OUT,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,"w") as f: json.dump(record,f,indent=2); f.write(chr(10))
 print(json.dumps(record))
