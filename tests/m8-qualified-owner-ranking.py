"""Exact owner retrieval/ranking replay in transaction-local PostgreSQL tables."""
import json,re,subprocess,uuid
from pathlib import Path
root=Path(__file__).resolve().parents[1]
f=json.loads((root/"tests/fixtures/m8-12040-qualified-owner.json").read_text())
shot=f["shot"];pool=f["candidate_pool"]
searches={r["search_id"]:{"id":r["search_id"],"query_index":r["query_index"]} for r in pool}
query_id=str(uuid.uuid5(uuid.NAMESPACE_URL,"m8-12040-owner-query"));searches[query_id]={"id":query_id,"query_index":3}
template=next(r for r in pool if r["provider"]=="wikimedia")
added=[{**template,**c,"id":str(uuid.uuid5(uuid.NAMESPACE_URL,"m8-12040:"+c["provider_asset_id"])),"provider":"wikimedia","search_id":query_id,"query_text":"desktop stapler"} for c in f["normalized_owner_candidates"]]
def lit(x):return "'"+x.replace("'","''")+"'"
def ranking(source):
 source=source[source.index("CREATE OR REPLACE FUNCTION factory.get_gemini_visual_candidate_sets("):]
 start=re.search(r"WITH(?: RECURSIVE)? eligible AS",source).start()
 end=source.index("WHERE candidate_index <= p_limit_per_shot;",start)+len("WHERE candidate_index <= p_limit_per_shot;")
 query=source[start:end].replace("INTO v_candidates","")
 replacements={"factory.visual_candidates":"pg_temp.visual_candidates","factory.visual_searches":"pg_temp.visual_searches","v_run.id":lit(shot["visual_run_id"])+"::uuid","v_shot.id":lit(shot["shot_uuid"])+"::uuid","v_shot.preferred_media_type":"'photo'","v_reviewed_assets":"ARRAY["+ ",".join(lit(a) for a in f["prior_reviewed_assets"])+"]::text[]","p_min_relevance_score":"55","p_limit_per_shot":"3"}
 for a,b in replacements.items():query=query.replace(a,b)
 return query
baseline=ranking(f["baseline_selection_function"]);current=ranking((root/"db/09-visuals.sql").read_text())
setup="""BEGIN;
SET LOCAL statement_timeout='5s';
CREATE TEMP TABLE visual_candidates AS SELECT * FROM factory.visual_candidates WITH NO DATA;
CREATE TEMP TABLE visual_searches(id uuid,query_index integer);
"""
setup+="INSERT INTO pg_temp.visual_candidates SELECT * FROM json_populate_recordset(NULL::pg_temp.visual_candidates,"+lit(json.dumps(pool))+");\n"
setup+="INSERT INTO pg_temp.visual_searches SELECT * FROM json_populate_recordset(NULL::pg_temp.visual_searches,"+lit(json.dumps(list(searches.values())))+");\n"
sql=setup+baseline+current
sql+="INSERT INTO pg_temp.visual_candidates SELECT * FROM json_populate_recordset(NULL::pg_temp.visual_candidates,"+lit(json.dumps(added))+");\n"+baseline+current
sql+="UPDATE pg_temp.visual_candidates SET rejected=false,rejection_reason=NULL WHERE provider='pexels' AND provider_asset_id='7578202';\n"+baseline+current+"ROLLBACK;"
out=subprocess.check_output(["docker","exec","-i","shorts-v2-postgres-1","psql","-U","shorts","-d","shorts_factory","-qAt","-v","ON_ERROR_STOP=1"],input=sql,text=True)
before,before_current,owner_old,after,trusted_old,trusted_new=[json.loads(l) for l in out.splitlines() if l.startswith("[")]
assert before==before_current
assert [(c["provider"],c["provider_asset_id"]) for c in before]==[(c["provider"],c["provider_asset_id"]) for c in shot["candidates"]]
assert "7824198" not in {c["provider_asset_id"] for c in before}
assert owner_old==after
assert "7824198" in {c["provider_asset_id"] for c in after},after
assert len(after)==3 and len({(c["provider"],c["provider_asset_id"]) for c in after})==3
assert all(c["metadata_rejected"] and c["relevance_score"]>=55 for c in after)
assert all(c["provider"]=="wikimedia" for c in after)
assert trusted_old==trusted_new
print(json.dumps({"production_baseline":[(c["provider"],c["provider_asset_id"]) for c in before],"owner_query_only":[(c["provider"],c["provider_asset_id"]) for c in owner_old],"after":[(c["provider"],c["provider_asset_id"]) for c in after],"slots":3,"metadata_rejection_preserved":True,"trusted_order_unchanged":True}))
