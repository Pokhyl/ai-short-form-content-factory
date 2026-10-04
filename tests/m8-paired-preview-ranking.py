"""Replay paired-subject pools through unchanged production SQL in temporary tables."""
import json,re,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
path=root/"tests/fixtures/m8-12093-paired-preview.json"
f=json.loads(path.read_text())
source=(root/"db/09-visuals.sql").read_text()
source=source[source.index("CREATE OR REPLACE FUNCTION factory.get_gemini_visual_candidate_sets("):]
start=re.search(r"WITH(?: RECURSIVE)? eligible AS",source).start()
end=source.index("WHERE candidate_index <= p_limit_per_shot;",start)+len("WHERE candidate_index <= p_limit_per_shot;")
base=source[start:end].replace("INTO v_candidates","")
def lit(value):return "'"+value.replace("'","''")+"'"
def assets(rows):return [c["provider"]+":"+c["provider_asset_id"] for r in rows for c in r["candidates"]]
prior=assets(f["parsed_reviews"][:5])
def rank(pool,shot,reviewed):
 searches={r["search_id"]:{"id":r["search_id"],"query_index":r["query_index"]} for r in pool}
 query=base
 replacements={"factory.visual_candidates":"pg_temp.visual_candidates","factory.visual_searches":"pg_temp.visual_searches","v_run.id":lit(shot["visual_run_id"])+"::uuid","v_shot.id":lit(shot["shot_uuid"])+"::uuid","v_shot.preferred_media_type":"'photo'","v_reviewed_assets":"ARRAY["+ ",".join(lit(a) for a in reviewed)+"]::text[]","p_min_relevance_score":"55","p_limit_per_shot":"3"}
 for a,b in replacements.items():query=query.replace(a,b)
 sql="BEGIN; SET LOCAL statement_timeout='5s'; CREATE TEMP TABLE visual_candidates AS SELECT * FROM factory.visual_candidates WITH NO DATA; CREATE TEMP TABLE visual_searches(id uuid,query_index integer);"
 sql+="INSERT INTO pg_temp.visual_candidates SELECT * FROM json_populate_recordset(NULL::pg_temp.visual_candidates,"+lit(json.dumps(pool))+");"
 sql+="INSERT INTO pg_temp.visual_searches SELECT * FROM json_populate_recordset(NULL::pg_temp.visual_searches,"+lit(json.dumps(list(searches.values())))+");"+query+"ROLLBACK;"
 out=subprocess.check_output(["docker","exec","-i","shorts-v2-postgres-1","psql","-U","shorts","-d","shorts_factory","-qAt","-v","ON_ERROR_STOP=1"],input=sql,text=True,timeout=10)
 return next(json.loads(line) for line in out.splitlines() if line.startswith("["))
selected=[]
for i,shot in enumerate(f["candidate_sets"]):
 baseline_prior=prior+(assets([f["candidate_sets"][0]]) if i else [])
 before=rank(f["candidate_pools"],shot,baseline_prior)
 assert [(c["provider"],c["provider_asset_id"]) for c in before]==[(c["provider"],c["provider_asset_id"]) for c in shot["candidates"]],before
 after=rank(f["after_candidate_pools"],shot,prior+assets(selected))
 required=["8141312","12612756"][i]
 assert required in {c["provider_asset_id"] for c in after},after
 assert len(after)==3 and all(c["metadata_rejected"] and c["relevance_score"]>=55 for c in after)
 assert len({c["provider"]+":"+c["provider_asset_id"] for c in after})==3
 assert not set(assets([{"candidates":after}])) & set(prior+assets(selected))
 selected.append({**shot,"candidates":after})
 print(json.dumps({"shot":shot["shot_key"],"before":[(c["provider"],c["provider_asset_id"]) for c in before],"after":[(c["provider"],c["provider_asset_id"],c["relevance_score"]) for c in after]}))
 control=[]
 for rows in [f["candidate_pools"],f["after_candidate_pools"]]:
  rows=[{**r} for r in rows];trusted=next(r for r in rows if r["shot_id"]==shot["shot_uuid"] and r["provider"]=="pexels" and r["relevance_score"]>=55)
  trusted.update(rejected=False,rejection_reason=None)
  control.append(rank(rows,shot,[]))
 assert [c for c in control[0] if not c["metadata_rejected"]]==[c for c in control[1] if not c["metadata_rejected"]],"trusted order changed"
 assert not control[0][0]["metadata_rejected"] and not control[1][0]["metadata_rejected"]
f["ranking_replay"]={"candidate_sets":selected,"temporary_tables_only":True,"trusted_order_unchanged":True,"minimum_relevance_score":55,"slots_per_shot":3}
path.write_text(json.dumps(f,indent=2)+"\n")
print("PASS: exact baseline, strict eligibility, unique slots, unchanged trusted ranking; all transactions rolled back")
