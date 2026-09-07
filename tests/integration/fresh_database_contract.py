"""Real PostgreSQL bootstrap/SQL contract; isolated container, no production I/O."""
import json
from pathlib import Path
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
NAME = "content-factory-schema-test-" + uuid.uuid4().hex[:12]


def docker(*args, input=None, check=True):
    return subprocess.run(["docker", *args], input=input, text=True,
                          capture_output=True, check=check)


def sql(text):
    return docker("exec", "-i", NAME, "psql", "-U", "test", "-d", "test",
                  "-v", "ON_ERROR_STOP=1", input=text)


try:
    docker("run", "-d", "--name", NAME, "--network", "none",
           "-e", "POSTGRES_USER=test", "-e", "POSTGRES_DB=test",
           "-e", "POSTGRES_PASSWORD=isolated-test-only", "postgres:18-alpine")
    for _ in range(60):
        if docker("exec", NAME, "pg_isready", "-h", "127.0.0.1", "-U", "test", "-d", "test",
                  check=False).returncode == 0:
            break
        time.sleep(0.25)
    else:
        raise RuntimeError("Disposable PostgreSQL did not become ready")
    sql((ROOT / "db/init/001_init.sql").read_text())
    statements = []
    persist_story_query = None
    planner_failure_query = None
    for path in sorted((ROOT / "n8n/workflows").glob("*.json")):
        raw = json.loads(path.read_text())
        for workflow in raw if isinstance(raw, list) else [raw]:
            for node in workflow["nodes"]:
                query = node.get("parameters", {}).get("query")
                if node["type"] == "n8n-nodes-base.postgres" and query:
                    statements.append(f"PREPARE q{len(statements)} AS {query.rstrip(';')};")
                    if node.get("name") == "Persist Inventory First Story":
                        persist_story_query = query.rstrip(';')
                    if node.get("name") == "Record Planner Failure":
                        planner_failure_query = query.rstrip(';')
    sql("\n".join(statements))
    if persist_story_query is None:
        raise RuntimeError("Persist Inventory First Story SQL not found")

    job_id = "44444444-4444-4444-8444-444444444444"
    sql(f"INSERT INTO public.jobs(id,topic,language_code,target_duration_seconds) VALUES ('{job_id}','Persist contract','ru',15);")
    args = [
        f"'{job_id}'",
        "'One. Two. Three.'",
        "'[1,2,3]'::jsonb",
        "'{\"exact_tts_required\":true,\"prediction_is_advisory\":true}'::jsonb",
        "'edge'",
        "'edge-tts'",
        "'inventory-first-story-v1'",
        "0",
        "'[{\"evidence_id\":\"S1\",\"source_id\":\"SRC1\",\"source_language\":\"en\",\"source_title\":\"Source\",\"source_url\":\"https://example.invalid/source\",\"passage_id\":\"P1\",\"section\":\"Test\",\"evidence_text\":\"Grounded evidence\",\"selection_score\":1,\"selection_rank\":1}]'::jsonb",
        "'en'",
        "'Source'",
        "'{\"version\":\"evidence-grounded-topic-resolution-v1\",\"raw_topic\":\"Persist contract\",\"resolved_subject\":\"Persist contract\",\"candidates\":[{\"candidate_id\":\"C1\"}],\"reasoning_evidence_ids\":[\"D-C1-1\"]}'::jsonb",
        "'{\"version\":\"inventory-first-story-v1\",\"units\":[{},{},{}],\"assets\":[{},{},{}]}'::jsonb",
    ]
    result = sql("\\pset tuples_only on\n\\pset format unaligned\n\\pset fieldsep '|'\n"
                 + f"PREPARE persist_story AS {persist_story_query};\n"
                 + f"EXECUTE persist_story({','.join(args)});\n"
                 + "DEALLOCATE persist_story;\n").stdout
    rows = [line.strip() for line in result.splitlines() if line.strip() and '|' in line]
    expected = f"{job_id}|1|t|0|3"
    if expected not in rows:
        raise RuntimeError(f"Persist Inventory First Story returned unexpected row: {rows}")
    # A delayed upstream error must neither overwrite nor mutate an already failed job.
    assert planner_failure_query
    sql(f"UPDATE public.jobs SET status='failed', current_stage='visuals', last_error='Original visual failure' WHERE id='{job_id}';")
    snapshot_query = f"SELECT md5(row_to_json(j)::text) FROM public.jobs j WHERE id='{job_id}';"
    before = sql(snapshot_query).stdout
    returned = sql("\\pset tuples_only on\n\\pset format unaligned\n"
                   + f"PREPARE planner_failure AS {planner_failure_query};\n"
                   + f"EXECUTE planner_failure('{job_id}','Delayed planner error');\n").stdout
    assert f"{job_id}|failed|visuals|Original visual failure" in returned, returned
    assert sql(snapshot_query).stdout == before, "Already failed job was mutated"
    sql("""
BEGIN;
INSERT INTO public.jobs(id,topic,language_code,target_duration_seconds,
 content_model_version,script_fit_passes)
VALUES ('11111111-1111-4111-8111-111111111111','Contract test','uk',45,'staged_v1',3);
INSERT INTO public.job_evidence(job_id,evidence_id,source_id,source_language,
 source_title,passage_id,evidence_text,selection_rank)
VALUES ('11111111-1111-4111-8111-111111111111','S1','S1','en','Source','snippet','Evidence',1);
INSERT INTO public.scenes(job_id,scene_number,narration,narration_support_evidence_ids,
 beat_start_seconds,beat_end_seconds,duration_seconds,status)
VALUES ('11111111-1111-4111-8111-111111111111',1,'A complete sentence.','["S1"]',0,3,3,'timed');
INSERT INTO public.visual_segments(id,job_id,segment_number,first_scene_number,
 last_scene_number,start_seconds,end_seconds,duration_seconds,narration,support_evidence_ids,
 canonical_subject,visual_target,visual_lane,visual_query,visual_description,planned_shot_count)
VALUES ('22222222-2222-4222-8222-222222222222','11111111-1111-4111-8111-111111111111',
 1,1,1,0,3,3,'A complete sentence.','["S1"]','Subject','Target','reference','Query','Description',1);
INSERT INTO public.media_library_assets(id,provider,provider_asset_id,canonical_subject,
 media_kind,local_path,visual_hash)
VALUES ('33333333-3333-4333-8333-333333333333','wikimedia','fixture','Subject','photo',
 'jobs/fixture/visual/image.jpg',repeat('a',64));
INSERT INTO public.visual_shots(job_id,visual_segment_id,shot_number,segment_shot_number,
 start_seconds,end_seconds,duration_seconds,media_library_asset_id,local_path,
 visual_kind,visual_cluster_key,selection_score)
VALUES ('11111111-1111-4111-8111-111111111111','22222222-2222-4222-8222-222222222222',
 1,1,0,3,3,'33333333-3333-4333-8333-333333333333','jobs/fixture/visual/image.jpg',
 'factual_image','fixture-cluster',1.05);
ROLLBACK;
""")
    print(f"FRESH_DATABASE_CONTRACT_PASS: {len(statements)} workflow SQL statements + staged writes")
except subprocess.CalledProcessError as error:
    raise RuntimeError(error.stderr) from error
finally:
    docker("rm", "-f", "-v", NAME, check=False)
