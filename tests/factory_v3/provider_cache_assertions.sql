CREATE FUNCTION pg_temp.expect_failure(statement text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 BEGIN
  EXECUTE statement;
  RAISE SQLSTATE 'Z0001' USING MESSAGE='unexpected success: ' || statement;
 EXCEPTION WHEN SQLSTATE 'Z0001' THEN RAISE; WHEN OTHERS THEN NULL;
 END;
END $$;
DO $$
DECLARE key text:=repeat('c',64); result jsonb;
BEGIN
 result:=factory_v3.claim_provider_cache(key,'pixabay');
 IF result->>'cached'<>'false' THEN RAISE EXCEPTION 'new query incorrectly cached'; END IF;
 PERFORM pg_temp.expect_failure(format('SELECT factory_v3.claim_provider_cache(%L,%L)',key,'pixabay'));
 PERFORM factory_v3.finish_provider_cache(key,'{"status":200,"headers":{"x-ratelimit-remaining":"99"},"body":{"hits":[]}}');
 result:=factory_v3.claim_provider_cache(key,'pixabay');
 IF result->>'cached'<>'true' OR result->'receipt'->'headers'->>'x-ratelimit-remaining'<>'99' THEN
  RAISE EXCEPTION 'cache receipt lost'; END IF;
 IF (SELECT expires_at-updated_at FROM factory_v3.provider_cache WHERE identity_hash=key)<interval '24 hours' THEN
  RAISE EXCEPTION 'cache shorter than required24h'; END IF;
 PERFORM pg_temp.expect_failure(format('SELECT factory_v3.claim_provider_cache(%L,%L)',key,'pexels'));
 UPDATE factory_v3.provider_cache SET expires_at=now()-interval '1 second' WHERE identity_hash=key;
 result:=factory_v3.claim_provider_cache(key,'pixabay');
 IF result->>'cached'<>'false' THEN RAISE EXCEPTION 'expired cache reused'; END IF;
 PERFORM factory_v3.fail_provider_cache(key,'{"status":429,"headers":{"retry-after":"60"}}');
 PERFORM pg_temp.expect_failure(format('SELECT factory_v3.claim_provider_cache(%L,%L)',key,'pixabay'));
 IF (SELECT receipt->>'status' FROM factory_v3.provider_cache WHERE identity_hash=key)<>'429' THEN
  RAISE EXCEPTION 'failed receipt missing'; END IF;
 RAISE NOTICE 'Exact provider cache,24h retention, expiry, pending/ambiguous blocks and failed headers PASS';
END $$;
