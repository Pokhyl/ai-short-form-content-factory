"""Submit each recorded operator test at most once; resume only by observing its existing id."""
import argparse,json,sqlite3,time,urllib.request
from pathlib import Path
from datetime import datetime,timezone

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--plan',required=True)
 parser.add_argument('--cases',required=True,help='Comma-separated zero-based case indices')
 parser.add_argument('--api',default='http://127.0.0.1:3000')
 parser.add_argument('--database',default='/data/factory-universal/jobs.sqlite3')
 args=parser.parse_args();path=Path(args.plan);plan=json.loads(path.read_text())
 def save():path.write_text(json.dumps(plan,ensure_ascii=False,indent=2))
 def query(sql,values=()):
  with sqlite3.connect(args.database,timeout=20) as db:
   db.row_factory=sqlite3.Row;return [dict(r) for r in db.execute(sql,values)]
 failures=[]
 for index in [int(x) for x in args.cases.split(',')]:
  case=plan['cases'][index]
  if not case.get('id'):
   if case.get('submission_state'):raise RuntimeError('Uncertain or previous submission must be reconciled before sending')
   active=query("SELECT id FROM jobs WHERE status IN ('queued','running')")
   if active:raise RuntimeError('Wait for existing normal jobs before submitting more')
   case.update(submission_state='sending_once',submitted_after=time.time(),submitted_at=datetime.now(timezone.utc).isoformat());save()
   payload={k:case[k] for k in ['topic','language','duration_s']};payload['origin']='test'
   request=urllib.request.Request(args.api+'/api/jobs',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
   try:
    with urllib.request.urlopen(request,timeout=30) as response:admitted=json.load(response)
   except Exception:
    case['submission_state']='uncertain';save();raise
   case.update(id=admitted['id'],submission_state='submitted');save()
  print('OBSERVING',index,case['topic'],case['id'],flush=True)
  deadline=time.monotonic()+950;previous=None
  while time.monotonic()<deadline:
   rows=query('SELECT status,stage,progress,error,message FROM jobs WHERE id=?',(case['id'],))
   if len(rows)!=1:raise RuntimeError('Recorded job disappeared')
   row=rows[0]
   if (row['status'],row['stage'])!=previous:
    print(json.dumps({'id':case['id'],**row},ensure_ascii=False),flush=True);previous=(row['status'],row['stage'])
   if row['status'] not in {'queued','running'}:
    case.update(status=row['status'],stage=row['stage'],error=row['error']);save()
    if row['status']!='ready':
     failures.append(case['id'])
     if 'selected Google voice' in (row['error'] or ''):raise RuntimeError('Provider failure; observe existing attempt without replaying')
    break
   time.sleep(10)
  else:raise TimeoutError('Observe existing id later; never automatically resend')
 print('REQUESTED_CASES_FINISHED',args.cases,'FAILED',failures,flush=True)
 if failures:raise RuntimeError('Diagnose recorded failed cases; successful independent cases remain preserved')
if __name__=='__main__':main()
