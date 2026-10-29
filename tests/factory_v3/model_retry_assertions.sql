-- Run only in an isolated database, never against production rows.
DO $$
DECLARE id uuid:='21550300-0000-4000-8000-000000000001';
 receipt jsonb:='{"status":503,"error_status":"UNAVAILABLE","gateway_execution_id":"123"}';
 claim jsonb; blocked boolean; key text;
BEGIN
 PERFORM factory_v3.create_preparation(id,
  '{"topic":"controlled","language":"ru","seconds":45,"model_retry_policy":"explicit-503-two-v1"}',
  '{"gemini":20}','revision');
 FOREACH key IN ARRAY ARRAY['research','inspection'] LOOP
  PERFORM factory_v3.claim_preparation_call(id,key,'gemini',repeat('a',64),'revision');
  PERFORM factory_v3.model_unavailable_preparation_call(id,key,receipt);
  blocked:=false;
  BEGIN PERFORM factory_v3.claim_model_retry(id,key||':retry503',repeat('b',64),'revision',key);
  EXCEPTION WHEN OTHERS THEN blocked:=true; END;
  IF NOT blocked THEN RAISE EXCEPTION 'changed request retried'; END IF;
  claim:=factory_v3.claim_model_retry(id,key||':retry503',repeat('a',64),'revision',key);
  IF (claim->>'retry_delay_seconds')::int<>CASE WHEN key='research' THEN 60 ELSE 180 END
  THEN RAISE EXCEPTION 'incorrect delay'; END IF;
  blocked:=false;
  BEGIN PERFORM factory_v3.claim_model_retry(id,key||':retry503',repeat('a',64),'revision',key);
  EXCEPTION WHEN OTHERS THEN blocked:=true; END;
  IF NOT blocked THEN RAISE EXCEPTION 'started reservation dispatched twice'; END IF;
  PERFORM factory_v3.finish_preparation_call(id,key||':retry503','{"status":200}');
  claim:=factory_v3.claim_model_retry(id,key||':retry503',repeat('a',64),'revision',key);
  IF claim->>'cached'<>'true' THEN RAISE EXCEPTION 'successful retry not cached'; END IF;
 END LOOP;
 PERFORM factory_v3.claim_preparation_call(id,'review','gemini',repeat('a',64),'revision');
 PERFORM factory_v3.model_unavailable_preparation_call(id,'review',receipt);
 blocked:=false;
 BEGIN PERFORM factory_v3.claim_model_retry(id,'review:retry503',repeat('a',64),'revision','review');
 EXCEPTION WHEN OTHERS THEN blocked:=true; END;
 IF NOT blocked THEN RAISE EXCEPTION 'third job-wide retry allowed'; END IF;
 IF (SELECT count(*) FROM factory_v3.preparation_calls WHERE preparation_id=id)<>5
 THEN RAISE EXCEPTION 'blocked call reserved budget'; END IF;
 RAISE NOTICE 'Global two-retry limit, exact identity, delays and crash/cached behavior PASS';
END $$;

DO $$
DECLARE id uuid; policy text; blocked boolean;
 receipt jsonb:='{"status":503,"error_status":"UNAVAILABLE","gateway_execution_id":"123"}';
BEGIN
 FOREACH policy IN ARRAY ARRAY['legacy','explicit-503-two-v1'] LOOP
  id:=CASE WHEN policy='legacy' THEN '21550300-0000-4000-8000-000000000002'::uuid
          ELSE '21550300-0000-4000-8000-000000000003'::uuid END;
  PERFORM factory_v3.create_preparation(id,jsonb_build_object('topic','controlled','language','en',
    'seconds',30,'model_retry_policy',policy),'{"gemini":1}','revision');
  PERFORM factory_v3.claim_preparation_call(id,'brief','gemini',repeat('a',64),'revision');
  PERFORM factory_v3.model_unavailable_preparation_call(id,'brief',receipt);
  blocked:=false;
  BEGIN PERFORM factory_v3.claim_model_retry(id,'brief:retry503',repeat('a',64),'revision','brief');
  EXCEPTION WHEN OTHERS THEN blocked:=true; END;
  IF NOT blocked THEN RAISE EXCEPTION 'legacy authorization or unchanged budget bypassed'; END IF;
 END LOOP;
 RAISE NOTICE 'Legacy requests and exhausted original budgets cannot retry PASS';
END $$;
