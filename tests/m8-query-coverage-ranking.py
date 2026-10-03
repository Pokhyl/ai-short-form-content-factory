"""Replay exact candidate ranking in transaction-local PostgreSQL tables.
No production jobs, searches, candidates, or functions are modified.
"""
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
fixture = json.loads((ROOT / "tests/fixtures/m8-11978-primary-secondary-fallback.json").read_text())
shot = fixture["shot"]
pool = fixture["candidate_pool"]
queries = [
    "basin siphon installed beneath bathroom sink",
    "sink siphon plumbing under washbasin",
    "bathroom sink",
]
searches = {}
for row in pool:
    searches[row["search_id"]] = {
        "id": row["search_id"],
        "query_index": queries.index(row["query_text"]) + 1,
    }


def sql_literal(value):
    return "'" + value.replace("'", "''") + "'"


def ranking(source):
    function_start = source.index("CREATE OR REPLACE FUNCTION factory.get_gemini_visual_candidate_sets(")
    body = source[function_start:]
    start = re.search(r"WITH(?: RECURSIVE)? eligible AS", body).start()
    terminator = "WHERE candidate_index <= p_limit_per_shot;"
    end = body.index(terminator, start) + len(terminator)
    query = body[start:end]
    query = re.sub(r"INTO v_candidates", "", query)
    replacements = {
        "factory.visual_candidates": "pg_temp.visual_candidates",
        "factory.visual_searches": "pg_temp.visual_searches",
        "v_run.id": sql_literal(shot["visual_run_id"]) + "::uuid",
        "v_shot.id": sql_literal(shot["shot_uuid"]) + "::uuid",
        "v_shot.preferred_media_type": "'photo'",
        "v_reviewed_assets": "ARRAY[]::text[]",
        "p_min_relevance_score": "55",
        "p_limit_per_shot": "3",
    }
    for old, new in replacements.items():
        query = query.replace(old, new)
    return query


baseline = fixture["baseline_selection_function"]
current = (ROOT / "db/09-visuals.sql").read_text()
setup = """
BEGIN;
SET LOCAL statement_timeout='5s';
CREATE TEMP TABLE visual_candidates AS SELECT * FROM factory.visual_candidates WITH NO DATA;
CREATE TEMP TABLE visual_searches(id uuid,query_index integer);
"""
setup += "INSERT INTO pg_temp.visual_candidates SELECT * FROM json_populate_recordset(NULL::pg_temp.visual_candidates," + sql_literal(json.dumps(pool)) + ");\n"
setup += "INSERT INTO pg_temp.visual_searches SELECT * FROM json_populate_recordset(NULL::pg_temp.visual_searches," + sql_literal(json.dumps(list(searches.values()))) + ");\n"
sql = setup + ranking(baseline) + ranking(current)
# If independently trusted metadata exists, preserve the exact baseline order.
sql += "UPDATE pg_temp.visual_candidates SET rejected=false,rejection_reason=NULL WHERE provider='pexels' AND provider_asset_id='11701113';\n"
sql += ranking(baseline) + ranking(current) + "ROLLBACK;"
output = subprocess.check_output([
    "docker", "exec", "-i", "shorts-v2-postgres-1", "psql", "-U", "shorts",
    "-d", "shorts_factory", "-qAt", "-v", "ON_ERROR_STOP=1",
], input=sql, text=True)
old, new, trusted_old, trusted_new = [json.loads(line) for line in output.splitlines() if line.startswith("[")]
assert "10475444" not in {row["provider_asset_id"] for row in old}
assert "10475444" in {row["provider_asset_id"] for row in new}
assert len(new) == 3
assert len({(row["provider"], row["provider_asset_id"]) for row in new}) == 3
assert {row["provider"] for row in new} == {"pexels", "pixabay"}
assert all(row["metadata_rejected"] for row in new)
assert all(row["relevance_score"] >= 55 for row in new)
assert trusted_old == trusted_new
print(json.dumps({"baseline": [(r["provider"],r["provider_asset_id"]) for r in old], "candidate": [(r["provider"],r["provider_asset_id"]) for r in new], "slots":len(new), "metadata_rejected_preserved":True, "trusted_order_unchanged":True}))
