from pathlib import Path
import json,urllib.request,os,datetime,subprocess
a=Path('/opt/factory-no-retry-20261020/acceptance/factory-v3')
proof=json.loads((a/'no-retry-dna-research-boundary-result-20261020.json').read_text())
assert proof['status']=='reviewed','source research boundary not passed'
plan=json.loads((a/'no-retry-normal-run-plan-20261020.json').read_text())
image=subprocess.check_output(['docker','inspect','factory-next-studio-v9','--format','{{.Image}}'],text=True).strip()
assert image=='sha256:56646d33d1a8a8ee6a50a0f58213db9bf5ca229dbe0b5d917242cfe5e4e8ac53'
rows=json.loads(urllib.request.urlopen('https://studio.hodor.com.pl/factory-next/api/jobs',timeout=3).read())
rows=rows if isinstance(rows,list) else rows['jobs']
assert all(row.get('status') in ('complete','needs_attention') for row in rows)
fd=os.open(a/'no-retry-normal-run-started-20261020.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:json.dump({'at':datetime.datetime.now(datetime.timezone.utc).isoformat()},f)
req=urllib.request.Request('https://studio.hodor.com.pl/factory-next/api/jobs',data=json.dumps(plan['request']).encode(),headers={'Content-Type':'application/json','Origin':'https://studio.hodor.com.pl'},method='POST')
try:
    with urllib.request.urlopen(req,timeout=5) as r:result={'http':r.status,'response':json.loads(r.read())}
except Exception as error:
    result={'status':'submission_uncertain','error_type':type(error).__name__}
(a/'no-retry-normal-run-submission-20261020.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
