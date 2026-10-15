DO $$
DECLARE target_id uuid := '11550300-0000-4000-8000-000000000001';
 receipt jsonb := '{"status":503,"error_status":"UNAVAILABLE","gateway_execution_id":"13142"}';
 state jsonb; blocked boolean;
BEGIN
 PERFORM factory_v3.create_preparation(target_id,'{"topic":"controlled","language":"uk","seconds":60}',
   '{"gemini":2,"metadata":1}','controlled');
 PERFORM factory_v3.claim_preparation_call(target_id,'brief','gemini',repeat('a',64),'controlled');
 PERFORM factory_v3.model_unavailable_preparation_call(target_id,'brief',receipt);
 IF (SELECT status FROM factory_v3.preparations WHERE preparations.id=target_id) <> 'preparing'
 THEN RAISE EXCEPTION 'Explicit rejection terminated active preparation'; END IF;
 state := factory_v3.claim_preparation_call(target_id,'brief','gemini',repeat('a',64),'controlled');
 IF state->>'unavailable'<>'true' OR state->'response'<>receipt
 THEN RAISE EXCEPTION 'Rejected send was not preserved'; END IF;
 PERFORM factory_v3.claim_preparation_call(target_id,'brief:availability:2','gemini',repeat('a',64),'controlled');
 PERFORM factory_v3.finish_preparation_call(target_id,'brief:availability:2','{"status":200}');
 state := factory_v3.claim_preparation_call(target_id,'brief:availability:2','gemini',repeat('a',64),'controlled');
 IF state->>'cached'<>'true' THEN RAISE EXCEPTION 'Completed retry not cached'; END IF;
 blocked := false;
 BEGIN
  PERFORM factory_v3.claim_preparation_call(target_id,'brief:availability:3','gemini',repeat('a',64),'controlled');
 EXCEPTION WHEN OTHERS THEN blocked := true; END;
 IF NOT blocked THEN RAISE EXCEPTION 'Physical retries escaped total budget'; END IF;
 PERFORM factory_v3.claim_preparation_call(target_id,'metadata','metadata',repeat('b',64),'controlled');
 blocked := false;
 BEGIN PERFORM factory_v3.model_unavailable_preparation_call(target_id,'metadata',receipt);
 EXCEPTION WHEN OTHERS THEN blocked := true; END;
 IF NOT blocked THEN RAISE EXCEPTION 'Non-model call accepted as retryable'; END IF;
 PERFORM factory_v3.fail_preparation_call(target_id,'metadata','transport_loss','{"status":502}');
 blocked := false;
 BEGIN PERFORM factory_v3.model_unavailable_preparation_call(target_id,'metadata',receipt);
 EXCEPTION WHEN OTHERS THEN blocked := true; END;
 IF NOT blocked OR (SELECT status FROM factory_v3.preparations WHERE preparations.id=target_id)<>'unknown'
 THEN RAISE EXCEPTION 'Unknown preparation was reopened'; END IF;
 RAISE NOTICE 'Explicit model503 physical budgets and immutable unknown state PASS';
END $$;

DO $$
DECLARE target_id uuid := '11550300-0000-4000-8000-000000000002'; bad jsonb; blocked boolean;
BEGIN
 PERFORM factory_v3.create_preparation(target_id,'{"topic":"controlled","language":"pl","seconds":15}',
   '{"gemini":1}','controlled');
 PERFORM factory_v3.claim_preparation_call(target_id,'brief','gemini',repeat('c',64),'controlled');
 FOR bad IN SELECT value FROM jsonb_array_elements('[
  {"status":503,"error_status":"UNAVAILABLE"},
  {"status":503,"error_status":"UNKNOWN_PROVIDER_RESULT","gateway_execution_id":"123"},
  {"status":502,"error_status":"UNAVAILABLE","gateway_execution_id":"123"},
  {"status":503,"error_status":"UNAVAILABLE","gateway_execution_id":"invalid"}]')
 LOOP
  blocked := false;
  BEGIN PERFORM factory_v3.model_unavailable_preparation_call(target_id,'brief',bad);
  EXCEPTION WHEN OTHERS THEN blocked := true; END;
  IF NOT blocked THEN RAISE EXCEPTION 'Unproven model rejection accepted'; END IF;
 END LOOP;
 IF (SELECT state FROM factory_v3.preparation_calls WHERE preparation_id=target_id AND call_key='brief')<>'started'
 THEN RAISE EXCEPTION 'Rejected classification changed started claim'; END IF;
 RAISE NOTICE 'Model503 strict provenance and error classification PASS';
END $$;
