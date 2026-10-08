import os,json,datetime
from pathlib import Path
from factory_v3.runtime import Runtime,load_settings
from material_first.operations import preparation_budgets
from factory_v3.preparation import ResourceUnavailable
ID='0d9cf03a-5178-4442-a24c-fea5f6a9dc33';SOURCE='72705d11-4556-4a4a-b751-676cc71e215d'
r=Runtime(load_settings('/run/factory-v3/settings.json'),'/data',os.environ['FACTORY_V3_REVISION'])
assert r.revision=='de5094f0aceee928cc389b1e836015070f739c99'
try:r.preparations.snapshot(ID)
except KeyError:pass
else:raise ValueError('diagnostic identity already exists; never repeat')
folder=Path('/data/checks')/('correction-boundary-'+ID);folder.mkdir(parents=True,exist_ok=False)
receipt={'id':ID,'source_job':SOURCE,'mode':'saved_material_corpus_live_voice_boundary','state':'started','reused_calls':[],'revision':r.revision}
def save():
 (folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:receipt[k] for k in ('id','state')},ensure_ascii=False),flush=True)
save()
rows=r.ledger._call("SELECT jsonb_agg(jsonb_build_object('key',call_key,'state',state,'response',response)) FROM factory_v3.preparation_calls WHERE preparation_id=%s::uuid",(SOURCE,))
saved={x['key']:x for x in rows}
request=r.preparations.snapshot(SOURCE)['request']
budgets=preparation_budgets(request['seconds']);budgets['gemini']=8
r.preparations.create(ID,request,budgets)
producer=r.producer(ID);ops=producer.operations;fresh=ops.gemini.calls
class Hybrid:
 request_id=ID
 def run(self,key,kind,request,invoke,**kwargs):
  if key in {'material-compose','material-compose-length-repair','material-language-edit','script-review'}:
   receipt['state']=key;save()
   return fresh.run(key,kind,request,invoke,**kwargs)
  row=saved[key]
  receipt['reused_calls'].append({'key':key,'source_job':SOURCE})
  if row['state']=='failed' and kwargs.get('allow_unavailable'):raise ResourceUnavailable(row['response'])
  if row['state']!='succeeded':raise ValueError('saved fixture call was not successful')
  return row['response']
for component in (ops.source,ops.gemini,ops.search,ops.downloader,ops.downloader.downloader):component.calls=Hybrid()
try:
 frozen=producer.prepare(ID)
 assert frozen['payload']['voice_correction']['max_attempts']==3
 receipt.update(state='prepared',plan_sha256=frozen['sha256']);save()
 executor=r.executor()
 for stage in ['voice','align','render','qa']:
  receipt['state']=stage;save()
  result=executor.run_next(ID)
 receipt.update(state=result['status'],voice_attempts=result['outputs']['voice'].get('voice_attempts'),render=result['outputs']['render'],qa=result['outputs']['qa']);save()
except BaseException as error:
 receipt.update(state='terminal_failure',error=type(error).__name__,reason=str(error));save();raise
