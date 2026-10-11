-- Permit the bounded grammar edit in an already-running measured voice correction.
-- Rebuilds only these three installed functions, preserving their current bodies.
BEGIN;
DO $migration$
DECLARE
 signature text;
 function_oid regprocedure;
 definition text;
 previous_pattern text := '(rewrite|script-review)';
 next_pattern text := '(rewrite|proofread|script-review)';
 signatures text[] := ARRAY[
  'factory_v3.claim_preparation_call(uuid,text,text,text,text)',
  'factory_v3.finish_preparation_call(uuid,text,jsonb)',
  'factory_v3.fail_preparation_call(uuid,text,text,jsonb)'
 ];
BEGIN
 FOREACH signature IN ARRAY signatures LOOP
  function_oid := to_regprocedure(signature);
  IF function_oid IS NULL THEN
   RAISE EXCEPTION 'required preparation function missing: %', signature;
  END IF;
  definition := pg_get_functiondef(function_oid);
  IF position(next_pattern IN definition) > 0 THEN
   CONTINUE;
  END IF;
  IF position(previous_pattern IN definition) = 0 THEN
   RAISE EXCEPTION 'unexpected preparation-call allowlist: %', signature;
  END IF;
  EXECUTE replace(definition, previous_pattern, next_pattern);
 END LOOP;
END $migration$;
DO $verify$
DECLARE
 signature text;
 function_oid regprocedure;
 definition text;
 signatures text[] := ARRAY[
  'factory_v3.claim_preparation_call(uuid,text,text,text,text)',
  'factory_v3.finish_preparation_call(uuid,text,jsonb)',
  'factory_v3.fail_preparation_call(uuid,text,text,jsonb)'
 ];
BEGIN
 FOREACH signature IN ARRAY signatures LOOP
  function_oid := to_regprocedure(signature);
  definition := pg_get_functiondef(function_oid);
  IF position('(rewrite|proofread|script-review)' IN definition) = 0
     OR position('(rewrite|script-review)' IN definition) > 0 THEN
   RAISE EXCEPTION 'proofread call key migration verification failed: %', signature;
  END IF;
 END LOOP;
END $verify$;
COMMIT;
