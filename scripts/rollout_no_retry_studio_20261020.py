from pathlib import Path
import subprocess,json,os,hashlib
p=Path('/opt/factory-no-retry-20261020');a=p/'acceptance/factory-v3'
for name,total in [('no-retry-image-next-tests-20261020.txt',179),('no-retry-image-core-tests-20261020.txt',123)]:
    text=(a/name).read_text()
    assert ('Ran '+str(total)+' tests') in text and text.rstrip().endswith('OK'),name
probe=json.loads((a/'no-retry-research-boundary-result-20261020.json').read_text())
# Removing the owner-rejected retry mechanism is independent of service capacity.
# A definite503 validates the one-send stop; it is not semantic research acceptance.
assert (probe['status']=='reviewed' or
        (probe['status']=='failed' and probe.get('failure_receipt',{}).get('status')==503)),probe.get('error_type')
plan=json.loads((a/'no-retry-studio-rollout-plan-20261020.json').read_text())
current=json.loads(subprocess.check_output(['docker','inspect','factory-next-studio-v9'],text=True))[0]
assert current['Image']==plan['previous_image_id']
assert hashlib.sha256(Path('/var/lib/factory-v3/settings.json').read_bytes()).hexdigest()==plan['settings_sha256']
code="import json,urllib.request;d=json.loads(urllib.request.urlopen('http://127.0.0.1:3003/factory-next/api/jobs',timeout=3).read());r=d if isinstance(d,list) else d['jobs'];assert all(x.get('status') in ('complete','needs_attention') for x in r);print(len(r))"
r=subprocess.run(['docker','exec','factory-next-studio-v9','python3','-c',code],capture_output=True,text=True,timeout=6);assert r.returncode==0,r.stderr
before=[json.loads(l) for l in subprocess.check_output(['docker','ps','--all','--format','{{json .}}'],text=True).splitlines()]
(a/'no-retry-containers-before-20261020.json').write_text(json.dumps(before,indent=2))
fd=os.open(a/'no-retry-studio-rollout-started-20261020.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as out:json.dump({'revision':plan['source_revision'],'previous_id':current['Id']},out)
commands=[
 ['docker','stop','--time','30','factory-next-studio-v9'],
 ['docker','rename','factory-next-studio-v9',plan['previous_container_name']],
 ['docker','create','--name','factory-next-studio-v9','--network','n8n_default','--read-only','--restart','unless-stopped','--mount','type=bind,src=/var/lib/factory-v3/settings.json,dst=/run/factory-v3/settings.json,readonly','--mount','type=volume,src=shorts-v2_media_data,dst=/data','--entrypoint','python3',plan['image'],'-m','factory_next.studio_server','--port','3003'],
 ['docker','network','connect','shorts-v2_default','factory-next-studio-v9'],
 ['docker','start','factory-next-studio-v9']]
for command in commands:
    r=subprocess.run(command,capture_output=True,text=True,timeout=40);assert r.returncode==0,r.stderr
    print(json.dumps({'action':command[:3],'ok':True}),flush=True)
receipt={**plan,'started':True,'public_health_pending':True}
(a/'no-retry-studio-rollout-result-20261020.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt))
