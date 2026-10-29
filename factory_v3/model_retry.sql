-- Additive, opt-in for new requests only. Each reservation consumes the existing budget.
CREATE OR REPLACE FUNCTION factory_v3.claim_model_retry(
 p_id uuid,p_key text,p_hash text,p_revision text,p_prior text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE prep factory_v3.preparations%ROWTYPE;
 prior factory_v3.preparation_calls%ROWTYPE;
 used bigint; result jsonb;
BEGIN
 SELECT * INTO STRICT prep FROM factory_v3.preparations WHERE id=p_id FOR UPDATE;
 IF prep.status<>'preparing' OR prep.source_revision IS DISTINCT FROM p_revision
 OR prep.request->>'model_retry_policy' IS DISTINCT FROM 'explicit-503-two-v1'
 THEN RAISE EXCEPTION 'model retry not authorized for this preparation'; END IF;
 IF p_key IS DISTINCT FROM p_prior||':retry503' OR p_prior IS NULL
 THEN RAISE EXCEPTION 'invalid retry chain'; END IF;
 SELECT * INTO STRICT prior FROM factory_v3.preparation_calls
 WHERE preparation_id=p_id AND call_key=p_prior;
 IF prior.kind<>'gemini' OR prior.state<>'failed' OR prior.error_code IS DISTINCT FROM 'ModelUnavailable'
 OR prior.request_hash IS DISTINCT FROM p_hash
 OR NOT COALESCE(prior.response->>'status'='503'
   AND prior.response->>'error_status'='UNAVAILABLE'
   AND prior.response->>'gateway_execution_id' ~ '^[0-9]+$',false)
 THEN RAISE EXCEPTION 'retry requires identical explicitly rejected model request'; END IF;
 -- Existing successful/failed receipts may be read, but started/unknown calls cannot resend.
 IF EXISTS(SELECT 1 FROM factory_v3.preparation_calls WHERE preparation_id=p_id AND call_key=p_key)
 THEN RETURN factory_v3.claim_preparation_call(p_id,p_key,'gemini',p_hash,p_revision); END IF;
 SELECT count(*) INTO used FROM factory_v3.preparation_calls
 WHERE preparation_id=p_id AND kind='gemini' AND position(':retry503' in call_key)>0;
 IF used>=2 THEN RAISE EXCEPTION 'job model retry limit exhausted'; END IF;
 result:=factory_v3.claim_preparation_call(p_id,p_key,'gemini',p_hash,p_revision);
 RETURN result || jsonb_build_object('retry_delay_seconds',CASE WHEN used=0 THEN 60 ELSE 180 END);
END $$;
