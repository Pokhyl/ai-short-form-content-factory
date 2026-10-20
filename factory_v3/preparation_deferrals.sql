-- Additive queue; historical terminal requests remain immutable.
CREATE TABLE IF NOT EXISTS factory_v3.preparation_deferrals (
 preparation_id uuid PRIMARY KEY REFERENCES factory_v3.preparations(id),
 failed_call_key text NOT NULL, retry_call_key text NOT NULL,
 retry_at timestamptz NOT NULL, state text NOT NULL CHECK(state IN ('waiting','running'))
);
CREATE OR REPLACE FUNCTION factory_v3.defer_preparation_call(
 p_id uuid,p_failed text,p_next text,p_delay int,p_revision text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE prep factory_v3.preparations%ROWTYPE;
 old factory_v3.preparation_calls%ROWTYPE; due timestamptz; used bigint;
BEGIN
 SELECT * INTO STRICT prep FROM factory_v3.preparations WHERE id=p_id FOR UPDATE;
 IF prep.status<>'preparing' OR prep.source_revision IS DISTINCT FROM p_revision
 THEN RAISE EXCEPTION 'preparation terminal or revision changed'; END IF;
 IF p_delay NOT BETWEEN 60 AND 1800 OR NOT (
   (p_failed NOT LIKE '%:availability:%' AND p_next=p_failed||':availability:2') OR
   (p_failed ~ ':availability:[2-5]$' AND
    p_next=left(p_failed,length(p_failed)-1)||((right(p_failed,1)::int)+1)::text))
 THEN RAISE EXCEPTION 'invalid bounded retry sequence'; END IF;
 SELECT * INTO STRICT old FROM factory_v3.preparation_calls WHERE preparation_id=p_id AND call_key=p_failed;
 IF old.kind<>'gemini' OR old.state<>'failed' OR old.finished_at IS NULL OR
   NOT COALESCE((old.response->>'status')::int=503 AND old.response->>'error_status'='UNAVAILABLE'
       AND old.response->>'gateway_execution_id' ~ '^[0-9]+$',false)
 THEN RAISE EXCEPTION 'only explicit model rejection can defer'; END IF;
 IF EXISTS(SELECT 1 FROM factory_v3.preparation_calls WHERE preparation_id=p_id AND state IN ('started','unknown'))
 THEN RAISE EXCEPTION 'ambiguous operation blocks deferral'; END IF;
 IF EXISTS(SELECT 1 FROM factory_v3.preparation_calls WHERE preparation_id=p_id AND call_key=p_next
           AND state IN ('succeeded','failed'))
 THEN RETURN jsonb_build_object('deferred',false); END IF;
 SELECT count(*) INTO used FROM factory_v3.preparation_calls WHERE preparation_id=p_id AND kind='gemini';
 IF used>=COALESCE((prep.budgets->>'gemini')::int,0) THEN RAISE EXCEPTION 'preparation call budget exhausted'; END IF;
 due:=old.finished_at+make_interval(secs=>p_delay);
 IF due<=now() THEN RETURN jsonb_build_object('deferred',false); END IF;
 INSERT INTO factory_v3.preparation_deferrals VALUES(p_id,p_failed,p_next,due,'waiting')
 ON CONFLICT(preparation_id) DO UPDATE SET failed_call_key=excluded.failed_call_key,
 retry_call_key=excluded.retry_call_key,retry_at=excluded.retry_at,state='waiting';
 RETURN jsonb_build_object('deferred',true,'retry_at',due);
END $$;

CREATE OR REPLACE FUNCTION factory_v3.claim_preparation_run(p_id uuid,p_revision text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE prep factory_v3.preparations%ROWTYPE;
BEGIN
 SELECT * INTO STRICT prep FROM factory_v3.preparations WHERE id=p_id FOR UPDATE;
 IF prep.source_revision IS DISTINCT FROM p_revision THEN RAISE EXCEPTION 'source revision changed'; END IF;
 IF prep.status='prepared' THEN RETURN jsonb_build_object('cached',true,'frozen',prep.frozen); END IF;
 IF prep.status<>'preparing' THEN RAISE EXCEPTION 'preparation terminal'; END IF;
 IF EXISTS(SELECT 1 FROM factory_v3.preparation_runs WHERE preparation_id=p_id) THEN
  UPDATE factory_v3.preparation_deferrals SET state='running'
  WHERE preparation_id=p_id AND state='waiting' AND retry_at<=now();
  IF NOT FOUND THEN RETURN jsonb_build_object('busy',true); END IF;
  IF EXISTS(SELECT 1 FROM factory_v3.preparation_calls WHERE preparation_id=p_id AND state IN ('started','unknown'))
  THEN RAISE EXCEPTION 'ambiguous operation blocks resume'; END IF;
 ELSE
  INSERT INTO factory_v3.preparation_runs(preparation_id,source_revision) VALUES(p_id,p_revision);
 END IF;
 RETURN jsonb_build_object('cached',false,'request',prep.request);
END $$;
