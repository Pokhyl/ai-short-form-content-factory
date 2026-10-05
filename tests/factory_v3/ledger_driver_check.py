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
from factory_v3.runtime import Runtime
from factory_v3.preparation import BudgetedCalls
import hashlib

dsn=os.environ["V3_TEST_DATABASE_URL"]
with psycopg.connect(dsn) as connection:
    connection.execute(Path("/fixtures/budget.sql").read_text(),prepare=False)
    connection.execute(Path("/app/factory_v3/ledger.sql").read_text(),prepare=False)
    connection.execute(Path("/app/factory_v3/preparation.sql").read_text(),prepare=False)
    connection.execute(Path("/app/factory_v3/provider_cache.sql").read_text(),prepare=False)
    connection.execute(Path("/app/factory_v3/review.sql").read_text(),prepare=False)
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
    runtime=Runtime({"database_url":dsn,"broker_token":"controlled-"+"x"*40},root,
                    os.environ["FACTORY_V3_REVISION"])
    request_id=str(uuid.uuid4())
    assert runtime.create(request_id,"Controlled topic","pl",15)["created"] is True
    assert runtime.create(request_id,"Controlled topic","pl",15)["created"] is False
    assert runtime.status(request_id)["status"]=="preparing"
    try: runtime.create(request_id,"Changed topic","pl",15)
    except ValueError: pass
    else: raise AssertionError("request parameters changed")
    def claim_producer():
        try:
            runtime.preparations.claim_run(request_id);return "claimed"
        except psycopg.Error:return "blocked"
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        producer_race=list(pool.map(lambda _:claim_producer(),range(2)))
    assert sorted(producer_race)==["blocked","claimed"],producer_race
    calls=BudgetedCalls(runtime.preparations,request_id)
    attempts=[]
    def ambiguous():
        attempts.append(1)
        raise TimeoutError("controlled metadata timeout")
    try: calls.run("billing","metadata",{"controlled":True},ambiguous)
    except TimeoutError:pass
    else:raise AssertionError("timeout not propagated")
    try:calls.run("billing","metadata",{"controlled":True},ambiguous)
    except psycopg.Error:pass
    else:raise AssertionError("unknown preparation repeated")
    assert len(attempts)==1 and runtime.status(request_id)["status"]=="unknown"
    with psycopg.connect(dsn) as connection:
        connection.execute("INSERT INTO factory_v3.human_reviews(job_id,video_sha256,decision,comment) VALUES(%s,%s,'accepted','controlled owner review')",(first,"a"*64))
        connection.execute("INSERT INTO factory_v3.human_reviews(job_id,video_sha256,decision,comment) VALUES(%s,%s,'rejected','changed') ON CONFLICT(job_id) DO NOTHING",(first,"b"*64))
        saved=connection.execute("SELECT decision,video_sha256 FROM factory_v3.human_reviews WHERE job_id=%s",(first,)).fetchone()
        assert saved==("accepted","a"*64)
    print(json.dumps({"status":"passed","psycopg":psycopg.__version__,
      "real_postgres":True,"packaged_runtime":True,"request_identity_immutable":True,"owner_review_insert_once":True,
      "concurrent_producer_claims":producer_race,"preparation_unknown_blocks":True,"full_stage_chain":True,"single_voice_attempt":True,
      "ambiguous_result_blocks":True,"concurrent_claims":results,
      "controlled_provider_calls":2,"actual_provider_calls":0}))
