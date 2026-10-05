"""Actual PostgreSQL/psycopg + executor integration; controlled providers only."""
import concurrent.futures
import json
import os
from pathlib import Path
import tempfile
import uuid
import psycopg
from factory_v3.ledger import PostgresLedger
from factory_v3.executor import Executor, ReconciliationRequired
from factory_v3.preflight import freeze, digest
import hashlib

dsn=os.environ["V3_TEST_DATABASE_URL"]
with psycopg.connect(dsn) as connection:
    connection.execute(Path("/fixtures/budget.sql").read_text(),prepare=False)
    connection.execute(Path("/app/factory_v3/ledger.sql").read_text(),prepare=False)
    connection.execute("""INSERT INTO factory.provider_budget_limits
      (provider,sku_family,usage_unit,free_limit,internal_limit,enabled,source_verified_on,source_url)
      VALUES('google_cloud_tts','chirp3_hd','characters',1000000,900000,true,CURRENT_DATE,'https://example.invalid/test'),
      ('google_cloud_tts','wavenet','characters',4000000,3600000,true,CURRENT_DATE,'https://example.invalid/test')
      ON CONFLICT(provider,sku_family,usage_unit) DO UPDATE SET enabled=true,
      free_limit=excluded.free_limit,internal_limit=excluded.internal_limit""")

class ControlledAdapters:
    def __init__(self):
        self.voice_calls=0
        self.lose_response=False

    def voice(self, job_id, payload, outputs, before_send):
        before_send()
        self.voice_calls+=1
        if self.lose_response:
            raise TimeoutError("controlled timeout")
        return {"status":"ready","controlled_test":True}

    def align(self,*args):return {"status":"ready","controlled_test":True}
    def render(self,*args):return {"status":"ready","controlled_test":True}
    def qa(self,*args):return {"status":"ready","controlled_test":True}

with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    photo=root/"test.jpg";photo.write_bytes(b"controlled bytes, not visual acceptance")
    sha=hashlib.sha256(photo.read_bytes()).hexdigest()
    contract={"visual_intent":"controlled test","must_show":["object"],"must_not_show":[]}
    asset={"id":"controlled","path":"test.jpg","sha256":sha,"source_url":"https://example.invalid/test",
           "author":"test","license":"CC0","license_url":"https://example.invalid/license"}
    review={"receipt_id":"controlled","model":"controlled-test","scene_id":"s1","asset_id":"controlled",
            "asset_sha256":sha,"contract_sha256":digest(contract),"match_score":90,"must_show_visible":True,
            "must_not_show_clear":True,"intent_match":True,"must_show_checks":[{"concept":"object","visible":True}]}
    frozen=freeze(root,"pl",15,"Controlled test.",[{"id":"s1","narration":"Controlled test.",
      "evidence_ids":["controlled"],"contract":contract}],[asset],[review])
    ledger=PostgresLedger(dsn)
    adapters=ControlledAdapters();executor=Executor(ledger,root,adapters)
    first=str(uuid.uuid4());executor.create(first,frozen)
    for _ in range(4):executor.run_next(first)
    executor.run_next(first)
    assert ledger.snapshot(first)["status"]=="qa_pass" and adapters.voice_calls==1
    lost=str(uuid.uuid4());executor.create(lost,frozen);adapters.lose_response=True
    try:executor.run_next(lost)
    except TimeoutError:pass
    else:raise AssertionError("controlled timeout not propagated")
    try:Executor(ledger,root,adapters).run_next(lost)
    except ReconciliationRequired:pass
    else:raise AssertionError("ambiguous call repeated")
    assert adapters.voice_calls==2 and ledger.snapshot(lost)["status"]=="unknown"
    race_job=str(uuid.uuid4());executor.create(race_job,frozen)
    def attempt():
        try:
            ledger.claim(race_job,"voice",frozen["sha256"]);return "claimed"
        except psycopg.Error:return "blocked"
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:attempt(),range(2)))
    assert sorted(results)==["blocked","claimed"],results
    with psycopg.connect(dsn) as connection:
        amount=connection.execute(
            "SELECT count(*) FROM factory.provider_usage_ledger WHERE job_id=%s",(race_job,)).fetchone()[0]
        assert amount==1
    print(json.dumps({"status":"passed","psycopg":psycopg.__version__,
      "real_postgres":True,"full_stage_chain":True,"single_voice_attempt":True,
      "ambiguous_result_blocks":True,"concurrent_claims":results,
      "controlled_provider_calls":2,"actual_provider_calls":0}))
