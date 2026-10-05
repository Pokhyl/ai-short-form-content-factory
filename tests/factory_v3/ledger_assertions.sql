-- All input/results in this file are controlled tests, not provider acceptance.
INSERT INTO factory.provider_budget_limits
(provider,sku_family,usage_unit,free_limit,internal_limit,enabled,source_verified_on,source_url)
VALUES('google_cloud_tts','chirp3_hd','characters',1000000,900000,true,CURRENT_DATE,'https://example.invalid/test'),
('google_cloud_tts','wavenet','characters',4000000,3600000,true,CURRENT_DATE,'https://example.invalid/test')
ON CONFLICT(provider,sku_family,usage_unit) DO UPDATE SET enabled=true,
free_limit=excluded.free_limit,internal_limit=excluded.internal_limit;

DO $$
DECLARE job uuid:='11111111-1111-4111-8111-111111111111';
 frozen jsonb:=jsonb_build_object('sha256',repeat('a',64),'payload',
   jsonb_build_object('language','pl','seconds',15,'script','Controlled test.'));
 result jsonb; amount bigint;
BEGIN
 PERFORM factory_v3.create_job(job,frozen);
 BEGIN
  PERFORM factory_v3.claim_stage(job,'voice',repeat('b',64));
  RAISE SQLSTATE 'Z0001' USING MESSAGE='wrong hash unexpectedly accepted';
 EXCEPTION WHEN SQLSTATE 'Z0001' THEN RAISE; WHEN OTHERS THEN NULL; END;
 IF EXISTS(SELECT 1 FROM factory.provider_usage_ledger) THEN
  RAISE EXCEPTION 'wrong hash reserved quota'; END IF;
 result:=factory_v3.claim_stage(job,'voice',repeat('a',64));
 IF result->>'amount'<>'16' THEN RAISE EXCEPTION 'incorrect character budget'; END IF;
 BEGIN
  PERFORM factory_v3.claim_stage(job,'voice',repeat('a',64));
  RAISE SQLSTATE 'Z0001' USING MESSAGE='duplicate voice claim accepted';
 EXCEPTION WHEN SQLSTATE 'Z0001' THEN RAISE; WHEN OTHERS THEN NULL; END;
 IF (SELECT count(*) FROM factory.provider_usage_ledger)<>1 THEN
  RAISE EXCEPTION 'duplicate budget allocation'; END IF;
 PERFORM factory_v3.account_voice_attempt(job);
 IF (SELECT state FROM factory.provider_usage_ledger)<>'committed' THEN
  RAISE EXCEPTION 'attempt not accounted'; END IF;
 PERFORM factory_v3.finish_stage(job,'voice','{"status":"ready"}');
 PERFORM factory_v3.claim_stage(job,'align',repeat('a',64));
 PERFORM factory_v3.finish_stage(job,'align','{"status":"ready"}');
 PERFORM factory_v3.claim_stage(job,'render',repeat('a',64));
 PERFORM factory_v3.finish_stage(job,'render','{"status":"ready"}');
 PERFORM factory_v3.claim_stage(job,'qa',repeat('a',64));
 PERFORM factory_v3.finish_stage(job,'qa','{"status":"ready"}');
 IF (SELECT status FROM factory_v3.jobs WHERE id=job)<>'qa_pass' THEN
  RAISE EXCEPTION 'pipeline did not reach QA'; END IF;
 BEGIN
  PERFORM factory_v3.claim_stage(job,'voice',repeat('a',64));
  RAISE SQLSTATE 'Z0001' USING MESSAGE='completed job repeated voice';
 EXCEPTION WHEN SQLSTATE 'Z0001' THEN RAISE; WHEN OTHERS THEN NULL; END;
 job:='22222222-2222-4222-8222-222222222222';
 PERFORM factory_v3.create_job(job,frozen);
 PERFORM factory_v3.claim_stage(job,'voice',repeat('a',64));
 PERFORM factory_v3.fail_stage(job,'voice','ControlledTimeout',true);
 BEGIN
  PERFORM factory_v3.claim_stage(job,'voice',repeat('a',64));
  RAISE SQLSTATE 'Z0001' USING MESSAGE='ambiguous job retried';
 EXCEPTION WHEN SQLSTATE 'Z0001' THEN RAISE; WHEN OTHERS THEN NULL; END;
 IF (SELECT count(*) FROM factory.provider_usage_ledger)<>2 THEN
  RAISE EXCEPTION 'ambiguous result double allocated'; END IF;
 RAISE NOTICE 'V3 PostgreSQL claims, order, quota, terminal and ambiguous-result checks PASS';
END $$;
