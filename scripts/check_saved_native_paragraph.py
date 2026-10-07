import os,json,hashlib,datetime
from pathlib import Path
from copy import deepcopy
from factory_v3.runtime import Runtime,load_settings
from factory_v3.preflight import digest
from material_first.engine import match_materials,validate_story
plan=json.loads(Path('/tmp/paragraph-native-plan.json').read_text())
raw=Path('/tmp/paragraph-native-context.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()==plan['context_sha256']
assert os.environ['FACTORY_V3_REVISION']==plan['runtime_revision']
context=json.loads(raw)
runtime=Runtime(load_settings('/run/factory-v3/settings.json'),'/data',os.environ['FACTORY_V3_REVISION'])
ops=runtime.producer(plan['saved_request']).operations
folder=Path('/data/checks')/('paragraph-native-'+plan['diagnostic_id'])
folder.mkdir(mode=0o700,parents=False,exist_ok=False)
report={'diagnostic_id':plan['diagnostic_id'],'saved_request':plan['saved_request'],'revision':runtime.revision,
 'state':'started','calls':[],'fresh_requests':0,'tts_calls':0,'db_writes':0,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def save():
 temp=folder/'receipt.tmp'
 with temp.open('w') as stream:
  json.dump(report,stream,ensure_ascii=False,indent=2);stream.flush();os.fsync(stream.fileno())
 temp.replace(folder/'receipt.json')
save()
class DiagnosticCalls:
 def run(self,key,kind,request,invoke,**kwargs):
  assert (key,kind) in {('free-tier','metadata'),('material-compose','gemini'),('material-language-edit','gemini'),('script-review','gemini')}
  assert not any(row['key']==key for row in report['calls'])
  assert sum(row['kind']=='gemini' for row in report['calls'])<3 or kind=='metadata'
  claim={'key':key,'kind':kind,'request_sha256':digest(request),'state':'started'}
  report['calls'].append(claim);save()
  try:
   result=invoke()
   claim.update(state='succeeded',response={'status':result['status'],'body':result['body']})
   save();return result
  except BaseException as error:
   claim.update(state='failed_or_unknown',error=type(error).__name__);save();raise
calls=DiagnosticCalls();ops.gemini.calls=calls
try:
 proof=runtime.settings['free_tier_proof']
 billing=calls.run('free-tier','metadata',{'project_id':proof['project_id']},lambda:runtime.gateway.metadata('billing',{'project_id':proof['project_id']}))['body']
 assert billing.get('projectId')==proof['project_id'] and billing.get('billingEnabled') is False
 draft=ops.compose(deepcopy(context))
 draft=match_materials(context['materials'],draft,contextual=True,topical=True)
 scenes=validate_story(context['request'],context['evidence'],context['materials'],draft)
 script=' '.join(scene['narration'] for scene in scenes)
 report.update(draft=draft,script=script,words=len(script.split()),scenes=scenes);save()
 review=ops.review_script({**context['request'],'script':script,'scenes':scenes,'evidence':context['evidence'],'materials':context['materials']})
 assert review.get('native_language_quality') is True
 report.update(state='text_boundary_pass',review=review,human_pass=False,video_created=False)
except BaseException as error:
 report.update(state='terminal_failure',error=type(error).__name__,error_detail=str(error)[:600],human_pass=False,video_created=False)
finally:save()
print(json.dumps({k:report[k] for k in ('diagnostic_id','state','revision','fresh_requests','tts_calls','db_writes')} | {'gemini_calls':sum(row['kind']=='gemini' for row in report['calls']),'words':report.get('words'),'error':report.get('error'),'receipt':str(folder/'receipt.json')},ensure_ascii=False))
