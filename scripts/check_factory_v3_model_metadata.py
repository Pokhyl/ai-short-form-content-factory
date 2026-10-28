"""One read-only model metadata check for the exact Gemini credential."""
import datetime,json,os,re,subprocess,tempfile,uuid
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError

ROOT=Path("/opt/ai-short-form-content-factory")
OUT=ROOT/"acceptance/factory-v3/model-metadata-after-service-enable-20261028.json"
CONTAINER="ai-short-form-n8n"
CREDENTIAL_ID="V3GeminiFreeTier20261005"
MODEL="gemini-3.5-flash-lite"
REMOTE="/tmp/model-metadata-"+uuid.uuid4().hex
record={
 "diagnostic_id":"v3-model-metadata-after-service-enable-20261028",
 "credential_id":CREDENTIAL_ID,"model":MODEL,"http_calls_started":0,
 "max_http_calls":1,"generation_calls":0,"search_calls":0,"tts_calls":0,
 "billing_mutations":0,"status":"blocked",
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
def safe(v):
 return v if isinstance(v,str) and re.fullmatch(r"[A-Za-z0-9._:/-]{1,120}",v) else None
try:
 if OUT.exists(): raise Stop("diagnostic_already_recorded_do_not_repeat")
 docker("exec",CONTAINER,"mkdir","-m","700",REMOTE); remote_created=True
 with tempfile.TemporaryDirectory(prefix="model-metadata-",dir="/tmp") as tmp:
  target=REMOTE+"/"+CREDENTIAL_ID+".json"
  docker("exec",CONTAINER,"n8n","export:credentials","--id",CREDENTIAL_ID,"--decrypted","--output",target)
  local=Path(tmp)/(CREDENTIAL_ID+".json"); docker("cp",CONTAINER+":"+target,str(local)); local.chmod(0o600)
  values=json.loads(local.read_text())
  if len(values)!=1 or values[0].get("id")!=CREDENTIAL_ID: raise Stop("credential_identity_mismatch")
  data=values[0].get("data")
  if isinstance(data,str): data=json.loads(data)
  key=data.get("apiKey")
  if not isinstance(key,str) or not key: raise Stop("selected_gemini_key_missing")
  url="https://generativelanguage.googleapis.com/v1beta/models/"+MODEL+"?"+urlencode({"key":key})
  record["http_calls_started"]=1
  try:
   response=build_opener(NoRedirect()).open(Request(url,headers={"User-Agent":"ContentFactoryV3/1.0","Accept":"application/json"},method="GET"),timeout=15)
   with response: status=response.status; raw=response.read(1024*1024+1)
  except HTTPError as e:
   status=e.code; raw=e.read(1024*1024+1)
  except Exception: raise Stop("metadata_transport_error")
  record["http_status"]=status
  if len(raw)>1024*1024: raise Stop("metadata_response_too_large")
  try: value=json.loads(raw)
  except Exception: raise Stop("metadata_response_invalid")
  if status!=200:
   err=value.get("error",{}) if isinstance(value,dict) else {}
   if isinstance(err,str): record["error_status"]=safe(err)
   elif isinstance(err,dict):
    record["error_status"]=safe(err.get("status"))
    for detail in err.get("details",[]) if isinstance(err.get("details"),list) else []:
     if not isinstance(detail,dict): continue
     md=detail.get("metadata",{})
     if not isinstance(md,dict): md={}
     reason=safe(detail.get("reason")) or safe(md.get("reason"))
     if reason: record["error_reason"]=reason
   raise Stop("model_metadata_rejected")
  name=value.get("name")
  methods=value.get("supportedGenerationMethods",[])
  methods=[x for x in methods if isinstance(x,str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,60}",x)] if isinstance(methods,list) else []
  record["model_name"]=safe(name)
  record["supported_generation_methods"]=methods
  record["input_token_limit"]=value.get("inputTokenLimit") if isinstance(value.get("inputTokenLimit"),int) else None
  record["output_token_limit"]=value.get("outputTokenLimit") if isinstance(value.get("outputTokenLimit"),int) else None
  if name!="models/"+MODEL: raise Stop("model_identity_mismatch")
  record["status"]="passed"
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
