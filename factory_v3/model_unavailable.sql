-- Additive function only: historical jobs/calls are never rewritten.
CREATE OR REPLACE FUNCTION factory_v3.model_unavailable_preparation_call(p_id uuid,p_key text,p_receipt jsonb)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 IF NOT COALESCE((p_receipt->>'status')::int=503
     AND p_receipt->>'error_status'='UNAVAILABLE'
     AND p_receipt->>'gateway_execution_id' ~ '^[0-9]+$',false)
 THEN RAISE EXCEPTION 'not an explicit model unavailable receipt'; END IF;
 PERFORM 1 FROM factory_v3.preparations WHERE id=p_id AND status='preparing' FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'preparation terminal'; END IF;
 UPDATE factory_v3.preparation_calls SET state='failed',response=p_receipt,
   error_code='ModelUnavailable',finished_at=now()
 WHERE preparation_id=p_id AND call_key=p_key AND state='started' AND kind='gemini';
 IF NOT FOUND THEN RAISE EXCEPTION 'no started model call'; END IF;
END $$;
