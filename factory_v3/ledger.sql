-- V3-only schema. Existing factory jobs/workflows are not modified.
CREATE SCHEMA IF NOT EXISTS factory_v3;
CREATE TABLE IF NOT EXISTS factory_v3.jobs (
 id uuid PRIMARY KEY,
 frozen jsonb NOT NULL,
 plan_hash text NOT NULL CHECK(plan_hash ~ '^[0-9a-f]{64}$'),
 status text NOT NULL DEFAULT 'prepared'
   CHECK(status IN ('prepared','voice_running','voice_ready','align_running','align_ready',
                    'render_running','render_ready','qa_running','qa_pass','failed','unknown')),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS factory_v3.stage_runs (
 job_id uuid NOT NULL REFERENCES factory_v3.jobs(id),
 stage text NOT NULL CHECK(stage IN ('voice','align','render','qa')),
 state text NOT NULL CHECK(state IN ('started','succeeded','failed','unknown')),
 input_hash text NOT NULL,
 output jsonb,
 error_code text,
 budget_key text,
 started_at timestamptz NOT NULL DEFAULT now(),
 finished_at timestamptz,
 PRIMARY KEY(job_id,stage)
);
CREATE OR REPLACE FUNCTION factory_v3.create_job(p_id uuid,p_frozen jsonb)
RETURNS uuid LANGUAGE plpgsql AS $$
BEGIN
 IF p_frozen->>'sha256' IS NULL OR p_frozen->'payload' IS NULL
    OR p_frozen->'payload'->>'language' NOT IN ('pl','en','ru','uk')
    OR (p_frozen->'payload'->>'seconds')::int NOT IN (15,30,45,60) THEN
  RAISE EXCEPTION 'invalid frozen plan';
 END IF;
 INSERT INTO factory_v3.jobs(id,frozen,plan_hash)
 VALUES(p_id,p_frozen,p_frozen->>'sha256');
 RETURN p_id;
END $$;

CREATE OR REPLACE FUNCTION factory_v3.claim_stage(p_id uuid,p_stage text,p_hash text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE j factory_v3.jobs%ROWTYPE; expected text; budget text; sku text; amount bigint;
BEGIN
 SELECT * INTO STRICT j FROM factory_v3.jobs WHERE id=p_id FOR UPDATE;
 expected:=CASE p_stage WHEN 'voice' THEN 'prepared' WHEN 'align' THEN 'voice_ready'
                       WHEN 'render' THEN 'align_ready' WHEN 'qa' THEN 'render_ready' END;
 IF expected IS NULL OR j.status<>expected OR j.plan_hash<>p_hash THEN
  RAISE EXCEPTION 'stage unavailable, already started, or plan changed';
 END IF;
 IF p_stage='voice' AND j.frozen->'payload'->'voice_correction' IS NULL THEN
  sku:=CASE WHEN j.frozen->'payload'->>'language'='ru' THEN 'wavenet' ELSE 'chirp3_hd' END;
  amount:=char_length(j.frozen->'payload'->>'script');
  budget:='v3:'||p_id::text||':voice';
  PERFORM factory.reserve_provider_usage(
    budget,'google_cloud_tts',sku,'characters',date_trunc('month',CURRENT_DATE)::date,
    amount,p_id::text,jsonb_build_object('stage','v3_voice','single_attempt',true));
 END IF;
 INSERT INTO factory_v3.stage_runs(job_id,stage,state,input_hash,budget_key)
 VALUES(p_id,p_stage,'started',p_hash,budget);
 UPDATE factory_v3.jobs SET status=p_stage||'_running',updated_at=now() WHERE id=p_id;
 RETURN jsonb_build_object('stage',p_stage,'budget_key',budget,'amount',amount);
END $$;

-- Conservatively account before sending; an ambiguous send is never retried.
CREATE OR REPLACE FUNCTION factory_v3.account_voice_attempt(p_id uuid)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE op factory_v3.stage_runs%ROWTYPE;
BEGIN
 SELECT * INTO STRICT op FROM factory_v3.stage_runs
 WHERE job_id=p_id AND stage='voice' FOR UPDATE;
 IF op.state<>'started' OR op.budget_key IS NULL THEN RAISE EXCEPTION 'voice not claimed'; END IF;
 PERFORM factory.commit_provider_usage(op.budget_key,NULL);
END $$;

CREATE OR REPLACE FUNCTION factory_v3.finish_stage(p_id uuid,p_stage text,p_output jsonb)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE j factory_v3.jobs%ROWTYPE;
BEGIN
 SELECT * INTO STRICT j FROM factory_v3.jobs WHERE id=p_id FOR UPDATE;
 IF j.status<>p_stage||'_running' THEN RAISE EXCEPTION 'stage not running'; END IF;
 UPDATE factory_v3.stage_runs SET state='succeeded',output=p_output,finished_at=now()
 WHERE job_id=p_id AND stage=p_stage AND state='started';
 IF NOT FOUND THEN RAISE EXCEPTION 'missing stage claim'; END IF;
 UPDATE factory_v3.jobs SET status=CASE WHEN p_stage='qa' THEN 'qa_pass' ELSE p_stage||'_ready' END,
 updated_at=now() WHERE id=p_id;
END $$;

CREATE OR REPLACE FUNCTION factory_v3.fail_stage(p_id uuid,p_stage text,p_code text,p_unknown boolean)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 PERFORM 1 FROM factory_v3.jobs WHERE id=p_id AND status=p_stage||'_running' FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'stage not running or terminal job'; END IF;
 UPDATE factory_v3.stage_runs SET state=CASE WHEN p_unknown THEN 'unknown' ELSE 'failed' END,
 error_code=p_code,finished_at=now() WHERE job_id=p_id AND stage=p_stage AND state='started';
 IF NOT FOUND THEN RAISE EXCEPTION 'missing stage claim'; END IF;
 UPDATE factory_v3.jobs SET status=CASE WHEN p_unknown THEN 'unknown' ELSE 'failed' END,
 updated_at=now() WHERE id=p_id;
END $$;

-- User-authorized bounded text correction. Every synthesis is separately reserved.
CREATE TABLE IF NOT EXISTS factory_v3.voice_revisions (
 job_id uuid NOT NULL REFERENCES factory_v3.jobs(id),
 attempt integer NOT NULL CHECK(attempt BETWEEN 1 AND 3),
 frozen jsonb NOT NULL,
 state text NOT NULL CHECK(state IN ('started','measured')),
 measurement jsonb,
 PRIMARY KEY(job_id,attempt)
);
CREATE OR REPLACE FUNCTION factory_v3.account_voice_revision(p_id uuid,p_attempt integer,p_frozen jsonb)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE j factory_v3.jobs%ROWTYPE; previous integer; budget text; sku text; amount bigint;
BEGIN
 SELECT * INTO STRICT j FROM factory_v3.jobs WHERE id=p_id FOR UPDATE;
 IF j.status<>'voice_running' OR j.frozen->'payload'->'voice_correction' IS DISTINCT FROM
   '{"protocol":"measured-text-correction-v1","max_attempts":3}'::jsonb THEN
  RAISE EXCEPTION 'bounded voice correction unavailable';
 END IF;
 SELECT count(*) INTO previous FROM factory_v3.voice_revisions WHERE job_id=p_id;
 IF p_attempt IS NULL OR p_attempt<>previous+1 OR p_attempt>3 OR EXISTS
  (SELECT 1 FROM factory_v3.voice_revisions WHERE job_id=p_id AND state<>'measured') THEN
  RAISE EXCEPTION 'voice correction attempt already claimed or unmeasured';
 END IF;
 IF p_frozen->'payload'->>'language' IS DISTINCT FROM j.frozen->'payload'->>'language'
 OR p_frozen->'payload'->'seconds' IS DISTINCT FROM j.frozen->'payload'->'seconds'
 OR COALESCE(length(p_frozen->'payload'->>'script'),0) NOT BETWEEN 1 AND 5000
 OR COALESCE(p_frozen->>'sha256','') !~ '^[0-9a-f]{64}$' THEN
  RAISE EXCEPTION 'invalid revised voice plan';
 END IF;
 sku:=CASE WHEN j.frozen->'payload'->>'language'='ru' THEN 'wavenet' ELSE 'chirp3_hd' END;
 amount:=char_length(p_frozen->'payload'->>'script');
 budget:='v3:'||p_id::text||':voice:'||p_attempt::text;
 PERFORM factory.reserve_provider_usage(budget,'google_cloud_tts',sku,'characters',
  date_trunc('month',CURRENT_DATE)::date,amount,p_id::text,
  jsonb_build_object('stage','v3_voice_correction','attempt',p_attempt));
 PERFORM factory.commit_provider_usage(budget,NULL);
 INSERT INTO factory_v3.voice_revisions(job_id,attempt,frozen,state) VALUES(p_id,p_attempt,p_frozen,'started');
END $$;
CREATE OR REPLACE FUNCTION factory_v3.measure_voice_revision(p_id uuid,p_attempt integer,p_measurement jsonb)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 PERFORM 1 FROM factory_v3.jobs WHERE id=p_id AND status='voice_running' FOR UPDATE;
 IF NOT FOUND OR COALESCE((p_measurement->>'duration_ms')::int,0)<=0
 OR COALESCE(p_measurement->>'sha256','') !~ '^[0-9a-f]{64}$' THEN
  RAISE EXCEPTION 'invalid completed voice measurement';
 END IF;
 UPDATE factory_v3.voice_revisions SET state='measured',measurement=p_measurement
 WHERE job_id=p_id AND attempt=p_attempt AND state='started';
 IF NOT FOUND THEN RAISE EXCEPTION 'voice measurement already stored or not claimed'; END IF;
END $$;
