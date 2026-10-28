"""Enable only the API Keys API in the confirmed OAuth consumer project."""
import datetime, json, os, re, subprocess, tempfile, time, uuid
from pathlib import Path
from urllib.parse import urlencode, quote
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

ROOT=Path("/opt/ai-short-form-content-factory")
OUT=ROOT/"acceptance/factory-v3/enable-apikeys-api-consumer-project-20261028.json"
CONTAINER="ai-short-form-n8n"
GOOGLE_ID="8KbFC6GBZOd18bzG"
PROJECT="852325278216"
SERVICE="apikeys.googleapis.com"
REMOTE="/tmp/enable-apikeys-"+uuid.uuid4().hex
record={
 "diagnostic_id":"v3-enable-apikeys-service-consumer-project-20261028",
 "credential_id":GOOGLE_ID,
 "project_number":PROJECT,
 "service":SERVICE,
 "http_calls_started":0,
 "max_http_calls":5,
 "enable_posts":0,
 "operation_polls":0,
 "billing_mutations":0,
 "generation_calls":0,
 "search_calls":0,
 "tts_calls":0,
 "calls":[],
 "started_at":datetime.datetime.now(datetime.timezone.utc).isoformat()
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

def safe(value):
 return value if isinstance(value,str) and re.fullmatch(r"[A-Za-z0-9._:/-]{1,120}",value) else None

def api(kind,method,url,token,body=None):
 if record["http_calls_started"]>=5: raise Stop("http_call_budget_exceeded")
 headers={"User-Agent":"ContentFactoryV3/1.0","Accept":"application/json","Authorization":"Bearer "+token}
 data=None
 if body is not None:
  headers["Content-Type"]="application/json"
  data=json.dumps(body).encode()
 record["http_calls_started"]+=1
 if kind=="enable": record["enable_posts"]+=1
 if kind=="operation_poll": record["operation_polls"]+=1
 entry={"kind":kind,"status":"unknown"}
 record["calls"].append(entry)
 try:
  response=build_opener(NoRedirect()).open(Request(url,data=data,headers=headers,method=method),timeout=15)
  with response: status=response.status; raw=response.read(1024*1024+1)
 except HTTPError as e:
  status=e.code; raw=e.read(1024*1024+1)
 except Exception:
  raise Stop(kind+"_transport_error")
 entry["status"]=status
 if len(raw)>1024*1024: raise Stop("response_too_large")
 try: value=json.loads(raw)
 except Exception: raise Stop("response_invalid")
 if status<200 or status>=300:
  err=value.get("error",{}) if isinstance(value,dict) else {}
  if isinstance(err,dict):
   entry["error_status"]=safe(err.get("status"))
   for detail in err.get("details",[]) if isinstance(err.get("details"),list) else []:
    if not isinstance(detail,dict): continue
    meta=detail.get("metadata",{})
    if not isinstance(meta,dict): meta={}
    for k in ("reason","domain","service","consumer","permission"):
     v=safe(detail.get(k)) or safe(meta.get(k))
     if v: entry[k]=v
  raise Stop(kind+"_rejected")
 return value

try:
 if OUT.exists(): raise Stop("diagnostic_already_recorded_do_not_repeat")
 docker("exec",CONTAINER,"mkdir","-m","700",REMOTE)
 remote_created=True
 with tempfile.TemporaryDirectory(prefix="enable-apikeys-",dir="/tmp") as tmp:
  docker("exec",CONTAINER,"n8n","export:credentials","--id",GOOGLE_ID,"--decrypted","--output",REMOTE+"/"+GOOGLE_ID+".json")
  local=Path(tmp)/(GOOGLE_ID+".json")
  docker("cp",CONTAINER+":"+REMOTE+"/"+GOOGLE_ID+".json",str(local))
  local.chmod(0o600)
  values=json.loads(local.read_text())
  if len(values)!=1 or values[0].get("id")!=GOOGLE_ID: raise Stop("credential_identity_mismatch")
  data=values[0].get("data")
  if isinstance(data,str): data=json.loads(data)
  token_data=data.get("oauthTokenData",{})
  if isinstance(token_data,str): token_data=json.loads(token_data)
  refresh=token_data.get("refresh_token")
  client_id=data.get("clientId"); client_secret=data.get("clientSecret")
  if not all(isinstance(x,str) and x for x in (refresh,client_id,client_secret)):
   raise Stop("google_oauth_refresh_unavailable")
  auth=api("oauth_refresh","POST","https://oauth2.googleapis.com/token","",{
   "grant_type":"refresh_token","refresh_token":refresh,
   "client_id":client_id,"client_secret":client_secret
  })
  token=auth.get("access_token")
  if not isinstance(token,str) or not token: raise Stop("access_token_missing")
  url="https://serviceusage.googleapis.com/v1/projects/"+PROJECT+"/services/"+SERVICE+":enable"
  op=api("enable","POST",url,token,body={})
  name=op.get("name")
  if not isinstance(name,str) or not re.fullmatch(r"operations/[A-Za-z0-9._/-]{1,160}",name):
   raise Stop("operation_name_invalid")
  record["operation_name"]=name
  done=op.get("done") is True
  record["operation_done"]=done
  for _ in range(3):
   if done: break
   time.sleep(2)
   state=api("operation_poll","GET","https://serviceusage.googleapis.com/v1/"+quote(name,safe="/"),token)
   done=state.get("done") is True
   record["operation_done"]=done
   if state.get("error") and isinstance(state["error"],dict):
    record["operation_error_status"]=safe(state["error"].get("status"))
    raise Stop("enable_operation_failed")
  if not done: raise Stop("operation_not_complete_within_poll_budget")
  record["status"]="enabled"
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
   record["credential_export_removed"]=True
  except Exception:
   record["credential_export_removed"]=False
 record["finished_at"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 fd=os.open(OUT,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,"w") as f:
  json.dump(record,f,indent=2)
  f.write(chr(10))
 print(json.dumps(record))
