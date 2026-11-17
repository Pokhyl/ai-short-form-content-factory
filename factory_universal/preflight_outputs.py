"""Image-only operator acceptance; never calls narration or rendering."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import signal
import uuid
import app

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--plan',required=True)
 parser.add_argument('--receipt',required=True)
 args=parser.parse_args()
 receipt=Path(args.receipt)
 if receipt.exists():raise SystemExit('Receipt already exists; inspect it instead of replaying jobs')
 cases=json.loads(Path(args.plan).read_text())['cases']
 app.cleanup()
 if shutil.disk_usage(app.DATA).free<app.DISK_RESERVE_BYTES:raise SystemExit('Insufficient project disk reserve; no test jobs created')
 results=[];receipt.write_text('[]')
 class PreflightDeadline(BaseException):pass
 def deadline(signum,frame):raise PreflightDeadline('image preflight exceeded its duration-scaled per-case deadline')
 signal.signal(signal.SIGALRM,deadline)
 for case in cases:
  topic=case['topic'];lang=case['language'];duration=case['duration_s']
  jid=str(uuid.uuid4());ts=app.now()
  with app.connect() as db:
   db.execute("INSERT INTO jobs(id,created_at,updated_at,topic,language,duration_s,status,stage,progress,message,origin) VALUES(?,?,?,?,?,?,'preflight','visuals',0,'Image-only check; no narration requested','test')",(jid,ts,ts,topic,lang,duration))
  app.SEARCH_QUERIES={'stock':set(),'commons':set()};app.DISCOVERED_PHOTOS={};app.IMAGE_SERVICE_RETRIES=0
  result={'topic':topic,'language':lang,'duration':duration,'id':jid,'voice_sends':0,'source_sha256':hashlib.sha256(Path(app.__file__).read_bytes()).hexdigest(),'implementation_hashes':app.implementation_hashes()}
  sources=[]
  try:
   signal.alarm(max(300,duration*8))
   sources=app.relevant_sources(app.load_sources(topic,lang),topic,lang)
   planning_seconds=app.initial_natural_budget(sources,topic,lang,duration)
   result['planning_seconds']=planning_seconds
   slots=app.plan_script(sources,topic,lang,planning_seconds,max_beats=duration//5)
   if not slots:raise ValueError('no complete source overview fits')
   prepared={}
   def before_send(planned_slots):
    app.shutil.rmtree(app.VISUAL/jid,ignore_errors=True)
    value=app.prepare_visuals(jid,sources,topic,lang,duration,planned_slots)
    prepared.clear();prepared.update(value)
   before_send.job_id=jid
   slots=app.prepare_illustrated_slots(sources,topic,lang,duration,planning_seconds,slots,before_send)
   directory=app.RENDER/jid;directory.mkdir(parents=True,exist_ok=True)
   count=len(prepared['selected']);rows=(count+3)//4
   sheet=app.Image.new('RGB',(1080,rows*480),(7,13,23))
   for index,item in enumerate(prepared['selected']):
    with app.Image.open(item['path']) as picture:sheet.paste(app.ImageOps.contain(picture.convert('RGB'),(270,480)),(index%4*270,index//4*480))
   sheet.save(directory/'preflight-sheet.jpg',quality=90)
   longest=max(prepared['selected'],key=lambda item:len(item['row']['caption']))
   shutil.copy2(longest['path'],directory/'preflight-caption.jpg')
   result.update(status='preflight_passed',images=count,script=prepared['script'],searches={key:len(value) for key,value in app.SEARCH_QUERIES.items()},visuals=prepared['visual_rows'],contact_sheet=str(directory/'preflight-sheet.jpg'),longest_caption_frame=str(directory/'preflight-caption.jpg'))
   (directory/'preflight-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
   app.update(jid,status='preflight_passed',stage='visuals',progress=100,message='Images verified; no narration requested',manifest=json.dumps({'script':prepared['script'],'sources':[{'title':source['title'],'url':source['url']} for source in sources],'audit':{'images':count,'voice_sends':0}}))
  except (Exception,PreflightDeadline) as error:
   result.update(status='failed',error=app.scrub_error(error))
   result['planning_rejections']=[rejection for source in sources for rejection in source.get('visual_planning_rejections',[])]
   app.update(jid,status='failed',stage='preflight',progress=100,message='Image-only verification stopped',error=result['error'])
  finally:
   signal.alarm(0)
   for directory in (app.VISUAL/jid,app.VOICE/jid,app.ROOT/'tmp'/jid):shutil.rmtree(directory,ignore_errors=True)
   with app.connect() as db:assert db.execute('SELECT COUNT(*) FROM voice_attempts WHERE job_id=?',(jid,)).fetchone()[0]==0
  app.cleanup()
  results.append(result);receipt.write_text(json.dumps(results,ensure_ascii=False,indent=2))
  print(json.dumps({key:value for key,value in result.items() if key not in {'visuals','script'}},ensure_ascii=False),flush=True)
 print('IMAGE_ONLY_RESULTS',len(results),'PASSED',sum(row['status']=='preflight_passed' for row in results),'VOICE_SENDS',0)

if __name__=='__main__':main()
