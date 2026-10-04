"""Replay full saved pools through baseline/current SQL without production writes."""
import json,re,subprocess
from pathlib import Path
p=Path('tests/fixtures/m8-12108-fastening-contract.json'); f=json.loads(p.read_text())
s=Path('db/09-visuals.sql').read_text();s=s[s.index('CREATE OR REPLACE FUNCTION factory.get_gemini_visual_candidate_sets('):];a=re.search(r'WITH(?: RECURSIVE)? eligible AS',s).start();b=s.index('WHERE candidate_index <= p_limit_per_shot;')+len('WHERE candidate_index <= p_limit_per_shot;');base=s[a:b].replace('INTO v_candidates','')
def lit(s):return "'"+s.replace("'","''")+"'"
def assets(rows):return [c['provider']+':'+c['provider_asset_id'] for r in rows for c in r['candidates']]
def rank(pool,ctx,reviewed,baseline=False):
 searches={r['search_id']:{'id':r['search_id'],'query_index':r['query_index']} for r in pool}
 q=f['baseline_ranking_query'] if baseline else base
 for a,b in {'factory.visual_candidates':'pg_temp.visual_candidates','factory.visual_searches':'pg_temp.visual_searches','v_run.id':lit(ctx['visual_run_id'])+'::uuid','v_shot.id':lit(ctx['shot_uuid'])+'::uuid','v_shot.preferred_media_type':"'photo'",'v_reviewed_assets':'ARRAY['+','.join(lit(v) for v in reviewed)+']::text[]','p_min_relevance_score':'55','p_limit_per_shot':'3'}.items():q=q.replace(a,b)
 sql="BEGIN;SET LOCAL statement_timeout='5s';CREATE TEMP TABLE visual_candidates AS SELECT * FROM factory.visual_candidates WITH NO DATA;CREATE TEMP TABLE visual_searches(id uuid,query_index integer);"
 sql+='INSERT INTO pg_temp.visual_candidates SELECT * FROM json_populate_recordset(NULL::pg_temp.visual_candidates,'+lit(json.dumps(pool))+');INSERT INTO pg_temp.visual_searches SELECT * FROM json_populate_recordset(NULL::pg_temp.visual_searches,'+lit(json.dumps(list(searches.values())))+');'+q+'ROLLBACK;'
 out=subprocess.check_output(['docker','exec','-i','shorts-v2-postgres-1','psql','-U','shorts','-d','shorts_factory','-qAt','-v','ON_ERROR_STOP=1'],input=sql,text=True,timeout=10)
 return next(json.loads(l) for l in out.splitlines() if l.startswith('['))
before=[];after=[]
for ctx in f['original_candidate_sets']:
 old=rank(f['original_all_candidate_pools'],ctx,assets(before),baseline=True)
 expected=[(c['provider'],c['provider_asset_id']) for c in ctx['candidates']]
 assert [(c['provider'],c['provider_asset_id']) for c in old]==expected,(ctx['shot_key'],expected,old)
 before.append({**ctx,'candidates':old})
 shot=next(s for s in f['grounded_begin']['shots_json'] if s['shot_uuid']==ctx['shot_uuid'])
 newctx={**ctx,**shot};new=rank(f['after_candidate_pools'],newctx,assets(after));assert len(new)==3
 assert all(c['relevance_score']>=55 for c in new)
 if ctx['shot_key'] not in ['S4-A','S6-A','S7-A','S9-A']:
  assert [c for c in old if not c['metadata_rejected']]==[c for c in new if not c['metadata_rejected']],('trusted candidate order changed',ctx['shot_key'])
 after.append({**newctx,'candidates':new})
 print(json.dumps({'shot':ctx['shot_key'],'before':expected,'after':[(c['provider'],c['provider_asset_id'],c['relevance_score']) for c in new]}),flush=True)
assert after == json.loads(p.read_text())['ranking_replay']['candidate_sets'];print('PASS baseline/current SQL: original9 reproduced, new9 sets minimum55 three slots; final selected uniqueness checked by native collector; all transactions rolled back')
