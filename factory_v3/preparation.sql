-- Preparation operations are separate from voice/render jobs; no existing rows changed.
CREATE TABLE IF NOT EXISTS factory_v3.preparations (
 id uuid PRIMARY KEY,
 request jsonb NOT NULL,
 budgets jsonb NOT NULL,
 source_revision text NOT NULL,
 status text NOT NULL DEFAULT 'preparing' CHECK(status IN ('preparing','prepared','failed','unknown')),
 frozen jsonb,
 error_code text,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS factory_v3.preparation_calls (
 preparation_id uuid NOT NULL REFERENCES factory_v3.preparations(id),
 call_key text NOT NULL,
 kind text NOT NULL,
 request_hash text NOT NULL CHECK(request_hash ~ '^[0-9a-f]{64}$'),
 state text NOT NULL CHECK(state IN ('started','succeeded','failed','unknown')),
 response jsonb,
 error_code text,
 started_at timestamptz NOT NULL DEFAULT now(),
 finished_at timestamptz,
 PRIMARY KEY(preparation_id,call_key)
);
CREATE OR REPLACE FUNCTION factory_v3.create_preparation(p_id uuid,p_request jsonb,p_budgets jsonb,p_revision text)
RETURNS uuid LANGUAGE plpgsql AS $$
BEGIN
 IF NOT COALESCE(p_request->>'language' IN ('pl','en','ru','uk'),false)
 OR NOT COALESCE((p_request->>'seconds')::int IN (15,30,45,60),false)
 OR COALESCE(char_length(p_request->>'topic'),0) NOT BETWEEN 1 AND 300
 OR NOT COALESCE(jsonb_typeof(p_budgets)='object',false) OR COALESCE(char_length(trim(p_revision)),0)=0 THEN
  RAISE EXCEPTION 'invalid preparation request';
 END IF;
 IF EXISTS(SELECT 1 FROM jsonb_each(p_budgets) b WHERE jsonb_typeof(b.value)<>'number'
  OR b.value::text !~ '^[1-9][0-9]{0,2}$') THEN RAISE EXCEPTION 'invalid call budgets'; END IF;
 INSERT INTO factory_v3.preparations(id,request,budgets,source_revision)
 VALUES(p_id,p_request,p_budgets,p_revision);
 RETURN p_id;
END $$;
CREATE OR REPLACE FUNCTION factory_v3.claim_preparation_call(p_id uuid,p_key text,p_kind text,p_hash text,p_revision text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE prep factory_v3.preparations%ROWTYPE; existing factory_v3.preparation_calls%ROWTYPE;
 max_calls int; used bigint;
BEGIN
 SELECT * INTO STRICT prep FROM factory_v3.preparations WHERE id=p_id FOR UPDATE;
 IF prep.source_revision IS DISTINCT FROM p_revision THEN RAISE EXCEPTION 'source revision changed'; END IF;
 IF COALESCE(char_length(p_key),0)=0 OR COALESCE(char_length(p_kind),0)=0 THEN RAISE EXCEPTION 'call identity missing'; END IF;
 IF prep.status<>'preparing' THEN RAISE EXCEPTION 'preparation terminal'; END IF;
 SELECT * INTO existing FROM factory_v3.preparation_calls WHERE preparation_id=p_id AND call_key=p_key;
 IF FOUND THEN
  IF existing.kind=p_kind AND existing.request_hash=p_hash AND existing.state='succeeded' THEN
   RETURN jsonb_build_object('cached',true,'response',existing.response);
  END IF;
  RAISE EXCEPTION 'request changed or operation already claimed/ambiguous';
 END IF;
 max_calls:=COALESCE((prep.budgets->>p_kind)::int,0);
 SELECT count(*) INTO used FROM factory_v3.preparation_calls WHERE preparation_id=p_id AND kind=p_kind;
 IF max_calls<=0 OR used>=max_calls THEN RAISE EXCEPTION 'preparation call budget exhausted'; END IF;
 INSERT INTO factory_v3.preparation_calls(preparation_id,call_key,kind,request_hash,state)
 VALUES(p_id,p_key,p_kind,p_hash,'started');
 RETURN jsonb_build_object('cached',false,'used',used+1,'max_calls',max_calls);
END $$;
CREATE OR REPLACE FUNCTION factory_v3.finish_preparation_call(p_id uuid,p_key text,p_response jsonb)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 PERFORM 1 FROM factory_v3.preparations WHERE id=p_id AND status='preparing' FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'preparation terminal'; END IF;
 UPDATE factory_v3.preparation_calls SET state='succeeded',response=p_response,finished_at=now()
 WHERE preparation_id=p_id AND call_key=p_key AND state='started';
 IF NOT FOUND THEN RAISE EXCEPTION 'call not started'; END IF;
END $$;
CREATE OR REPLACE FUNCTION factory_v3.fail_preparation_call(p_id uuid,p_key text,p_code text)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 PERFORM 1 FROM factory_v3.preparations WHERE id=p_id AND status='preparing' FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'preparation terminal'; END IF;
 UPDATE factory_v3.preparation_calls SET state='unknown',error_code=p_code,finished_at=now()
 WHERE preparation_id=p_id AND call_key=p_key AND state='started';
 IF NOT FOUND THEN RAISE EXCEPTION 'call not started'; END IF;
 UPDATE factory_v3.preparations SET status='unknown' WHERE id=p_id;
END $$;
CREATE OR REPLACE FUNCTION factory_v3.complete_preparation(p_id uuid,p_frozen jsonb,p_revision text)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 PERFORM 1 FROM factory_v3.preparations WHERE id=p_id AND status='preparing' AND source_revision=p_revision FOR UPDATE;
 IF NOT FOUND OR EXISTS(SELECT 1 FROM factory_v3.preparation_calls WHERE preparation_id=p_id AND state<>'succeeded') THEN
  RAISE EXCEPTION 'preparation not ready';
 END IF;
 -- Called only by the trusted producer after local semantic/media preflight.
 PERFORM factory_v3.create_job(p_id,p_frozen);
 UPDATE factory_v3.preparations SET status='prepared',frozen=p_frozen WHERE id=p_id;
END $$;

CREATE OR REPLACE FUNCTION factory_v3.reject_preparation(p_id uuid,p_code text,p_revision text)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 PERFORM 1 FROM factory_v3.preparations WHERE id=p_id AND status='preparing' AND source_revision=p_revision FOR UPDATE;
 IF NOT FOUND OR EXISTS(SELECT 1 FROM factory_v3.preparation_calls WHERE preparation_id=p_id AND state='started') THEN
  RAISE EXCEPTION 'preparation terminal or operation outstanding'; END IF;
 UPDATE factory_v3.preparations SET status='failed',error_code=p_code WHERE id=p_id;
END $$;
