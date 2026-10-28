"""Check and enable only required Google metadata APIs for bounded owner billing verification."""
import datetime, json, os, re, subprocess, tempfile, time, uuid
from pathlib import Path
from urllib.parse import urlencode, quote
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

ROOT=Path("/opt/ai-short-form-content-factory")
OUT=ROOT/"acceptance/factory-v3/metadata-services-after-key-owner-20261028.json"
CONTAINER="ai-short-form-n8n"
GOOGLE_ID="8KbFC6GBZOd18bzG"
CONSUMER_PROJECT="852325278216"
OWNER_PROJECT="529636078126"
SERVICES=("cloudresourcemanager.googleapis.com","cloudbilling.googleapis.com")
MAX_CALLS=11
REMOTE="/tmp/metadata-services-"+uuid.uuid4().hex
record={
 "diagnostic_id":"v3-enable-required-metadata-services-20261028",
 "credential_id":GOOGLE_ID,
 "oauth_consumer_project_number":CONSUMER_PROJECT,
 "gemini_key_owner_project_number":OWNER_PROJECT,
 "services":{},
 "http_calls_started":0,"max_http_calls":MAX_CALLS,
 "enable_posts":0,"operation_polls":0,
 "billing_mutations":0,"iam_mutations":0,
 "generation_calls":0,"search_calls":0,"tts_calls":0,
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
def api(kind,method,url,token=None,body=None,form=False):
 if record["http_calls_started"]>=MAX_CALLS: raise Stop("http_call_budget_exceeded")
 headers={"User-Agent":"ContentFactoryV3/1.0","Accept":"application/json"}
 if token: headers["Authorization"]="Bearer "+token
 data=None
 if body is not None:
  if form:
   headers["Content-Type"]="application/x-www-form-urlencoded"; data=urlencode(body).encode()
  else:
   headers["Content-Type"]="application/json"; data=json.dumps(body).encode()
 record["http_calls_started"]+=1
 if kind=="enable": record["enable_posts"]+=1
 if kind=="operation_poll": record["operation_polls"]+=1
 entry={"kind":kind,"status":"unknown"}; record["calls"].append(entry)
 try:
  response=build_opener(NoRedirect()).open(Request(url,data=data,headers=headers,method=method),timeout=15)
  with response: status=response.status; raw=response.read(1024*1024+1)
 except HTTPError as e:
  status=e.code; raw=e.read(1024*1024+1)
 except Exception: raise Stop(kind+"_transport_error")
 entry["status"]=status
 if len(raw)>1024*1024: raise Stop("response_too_large")
 try: value=json.loads(raw)
 except Exception: raise Stop("response_invalid")
 if status<200 or status>=300:
  err=value.get("error",{}) if isinstance(value,dict) else {}
  if isinstance(err,dict):
   entry["error_status"]=safe(err.get("status"))
   for d in err.get("details",[]) if isinstance(err.get("details"),list) else []:
    if not isinstance(d,dict): continue
    md=d.get("metadata",{})
    if not isinstance(md,dict): md={}
    for k in ("reason","domain","service","consumer","permission"):
     x=safe(d.get(k)) or safe(md.get(k))
     if x: entry[k]=x
  raise Stop(kind+"_rejected")
 return value
def poll_operation(name,token,service_record):
 if not isinstance(name,str) or not re.fullmatch(r"operations/[A-Za-z0-9._/-]{1,160}",name):
  raise Stop("operation_name_invalid")
 service_record["operation_name"]=name
 done=False
 for _ in range(2):
  time.sleep(2)
  state=api("operation_poll","GET","https://serviceusage.googleapis.com/v1/"+quote(name,safe="/"),token)
  done=state.get("done") is True
  if done:
   if state.get("error"):
    er=state["error"]
    if isinstance(er,dict): service_record["operation_error_status"]=safe(er.get("status"))
    raise Stop("enable_operation_failed")
   break
 service_record["operation_done"]=done
 if not done: raise Stop("operation_not_complete_within_poll_budget")
try:
 if OUT.exists(): raise Stop("diagnostic_already_recorded_do_not_repeat")
 docker("exec",CONTAINER,"mkdir","-m","700",REMOTE); remote_created=True
 with tempfile.TemporaryDirectory(prefix="metadata-services-",dir="/tmp") as tmp:
  docker("exec",CONTAINER,"n8n","export:credentials","--id",GOOGLE_ID,"--decrypted","--output",REMOTE+"/"+GOOGLE_ID+".json")
  local=Path(tmp)/(GOOGLE_ID+".json"); docker("cp",CONTAINER+":"+REMOTE+"/"+GOOGLE_ID+".json",str(local)); local.chmod(0o600)
  vals=json.loads(local.read_text())
  if len(vals)!=1 or vals[0].get("id")!=GOOGLE_ID: raise Stop("credential_identity_mismatch")
  data=vals[0].get("data")
  if isinstance(data,str): data=json.loads(data)
  td=data.get("oauthTokenData",{})
  if isinstance(td,str): td=json.loads(td)
  refresh=td.get("refresh_token"); client_id=data.get("clientId"); client_secret=data.get("clientSecret")
  if not all(isinstance(x,str) and x for x in (refresh,client_id,client_secret)): raise Stop("google_oauth_refresh_unavailable")
  auth=api("oauth_refresh","POST","https://oauth2.googleapis.com/token",body={
   "grant_type":"refresh_token","refresh_token":refresh,"client_id":client_id,"client_secret":client_secret
  },form=True)
  token=auth.get("access_token")
  if not isinstance(token,str) or not token: raise Stop("access_token_missing")
  for service in SERVICES:
   item={"state_before":"unknown","enabled_by_this_run":False}
   record["services"][service]=item
   state=api("service_state","GET","https://serviceusage.googleapis.com/v1/projects/"+CONSUMER_PROJECT+"/services/"+service,token)
   item["state_before"]=state.get("state")
   if item["state_before"]=="DISABLED":
    op=api("enable","POST","https://serviceusage.googleapis.com/v1/projects/"+CONSUMER_PROJECT+"/services/"+service+":enable",token,body={})
    item["enabled_by_this_run"]=True
    poll_operation(op.get("name"),token,item)
    item["state_after"]="ENABLED"
   elif item["state_before"]=="ENABLED":
    item["state_after"]="ENABLED"
   else:
    raise Stop("service_state_unexpected")
  project=api("project_info","GET","https://cloudresourcemanager.googleapis.com/v3/projects/"+OWNER_PROJECT,token)
  project_id=project.get("projectId")
  if not isinstance(project_id,str) or not re.fullmatch(r"[a-z][a-z0-9-]{4,62}",project_id): raise Stop("project_identity_invalid")
  record["project_id"]=project_id
  billing=api("billing_info","GET","https://cloudbilling.googleapis.com/v1/projects/"+quote(project_id,safe="")+"/billingInfo",token)
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
