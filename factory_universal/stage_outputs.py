"""Run the normal factory worker from a staged image, without changing Studio.

Jobs stay outside user/examples lists until an operator reviews their artifacts.
An existing receipt is never replayed. All normal quota, voice and runtime gates apply.
"""
import argparse
import json
import shutil
from pathlib import Path
import uuid
import app


def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--plan',required=True)
 parser.add_argument('--receipt',required=True)
 args=parser.parse_args()
 receipt=Path(args.receipt)
 if receipt.exists():raise SystemExit('Receipt exists; inspect recorded IDs instead of replaying')
 plan=json.loads(Path(args.plan).read_text())
 cases=plan['cases']
 for case in cases:
  if case['language'] not in app.LANGS or case['duration_s'] not in app.DURATIONS:raise SystemExit('Invalid acceptance plan')
 with app.connect() as db:
  active=db.execute("SELECT id,status FROM jobs WHERE status IN ('queued','running','preflight','validating')").fetchall()
  if active:raise SystemExit('Active factory work; do not start staged acceptance')
 app.cleanup()
 rows=[{**case,'id':str(uuid.uuid4()),'status':'planned'} for case in cases]
 result={'implementation_hashes':app.implementation_hashes(),'project_ready':False,'mode':'normal worker in staged image','cases':rows}
 receipt.parent.mkdir(parents=True,exist_ok=True)
 receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2))
 for row in rows:
  with app.connect() as db:
   if db.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('queued','running','preflight','validating')").fetchone()[0]:raise SystemExit('New active factory work; remaining staged cases were not submitted')
  app.cleanup()
  if shutil.disk_usage(app.DATA).free<app.DISK_RESERVE_BYTES:raise SystemExit('Project disk reserve reached; no further jobs submitted')
  jid=row['id'];ts=app.now()
  with app.connect() as db:
   db.execute("INSERT INTO jobs(id,created_at,updated_at,topic,language,duration_s,status,stage,progress,message,origin) VALUES(?,?,?,?,?,?,'validating','queued',0,'Staged normal pipeline acceptance','staged_test')",(jid,ts,ts,row['topic'],row['language'],row['duration_s']))
  row['status']='submitted';receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2))
  # execute_job is the same 900-second process-group supervisor used by Studio.
  app.execute_job(jid)
  job=app.get_job(jid);manifest=job.get('manifest') or {}
  if isinstance(manifest,str):manifest=json.loads(manifest)
  row.update(status=job['status'],error=job.get('error'),manifest_path=str(app.RENDER/jid/'universal-manifest.json'))
  row['narration']=manifest.get('narration',{})
  row['render']=manifest.get('render',{})
  row['audit']=manifest.get('audit',{})
  with app.connect() as db:row['voice_attempts']=db.execute('SELECT COUNT(*) FROM voice_attempts WHERE job_id=?',(jid,)).fetchone()[0]
  receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2))
  print(json.dumps({key:row.get(key) for key in ('id','topic','status','error','voice_attempts')},ensure_ascii=False),flush=True)
  if row.get('error') and 'HTTP 429' in row['error']:
   result['stop_reason']='Media/source rate limit; remaining cases were not submitted'
   receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2))
   break
 print('NORMAL_PIPELINE_RESULTS',len(rows),'READY',sum(row['status']=='ready' for row in rows),flush=True)


if __name__=='__main__':main()
