import os,json,statistics
from factory_v3.runtime import Runtime,load_settings
r=Runtime(load_settings('/run/factory-v3/settings.json'),'/data',os.environ['FACTORY_V3_REVISION'])
rows=r.ledger._call("SELECT jsonb_agg(jsonb_build_object('id',j.id,'language',j.frozen->'payload'->>'language','script',j.frozen->'payload'->>'script','duration_ms',s.output->'duration_ms')) FROM factory_v3.jobs j JOIN factory_v3.stage_runs s ON s.job_id=j.id WHERE s.stage='voice' AND s.state='succeeded'",())
result=[]
for row in rows:
 peers=[p for p in rows if p['language']==row['language'] and p['id']!=row['id']]
 if not peers:continue
 wr=statistics.median(len(p['script'].split())/(p['duration_ms']/1000) for p in peers)
 cr=statistics.median(len(p['script'].strip())/(p['duration_ms']/1000) for p in peers)
 estimated=(len(row['script'].split())/wr+len(row['script'].strip())/cr)/2
 result.append({'id':row['id'],'language':row['language'],'peer_count':len(peers),'actual_seconds':row['duration_ms']/1000,'estimated_seconds':round(estimated,3),'error_seconds':round(estimated-row['duration_ms']/1000,3)})
print(json.dumps({'method':'leave-one-out on saved original voice-stage duration and frozen text; grouped by language; historical exact voice identity not independently verified','samples':result,'maximum_absolute_error_seconds':max(abs(p['error_seconds']) for p in result),'new_provider_calls':0,'database_writes':0,'conclusion':'Word/character estimate alone cannot establish the one-second natural-duration window.'},ensure_ascii=False,indent=2))
