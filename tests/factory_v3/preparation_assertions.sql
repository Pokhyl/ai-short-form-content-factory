-- Controlled isolated database tests, never live provider acceptance.
CREATE FUNCTION pg_temp.expect_failure(statement text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 BEGIN
  EXECUTE statement;
  RAISE SQLSTATE 'Z0001' USING MESSAGE='unexpected success: ' || statement;
 EXCEPTION WHEN SQLSTATE 'Z0001' THEN RAISE; WHEN OTHERS THEN NULL;
 END;
END $$;
DO $$
DECLARE
 a uuid:='33333333-3333-4333-8333-333333333333';
 b uuid:='44444444-4444-4444-8444-444444444444';
 c uuid:='55555555-5555-4555-8555-555555555555';
 result jsonb;
 frozen jsonb:=jsonb_build_object('sha256',repeat('a',64),'payload',
   jsonb_build_object('language','pl','seconds',15,'script','Controlled test.'));
BEGIN
 PERFORM factory_v3.create_preparation(a,'{"topic":"controlled","language":"pl","seconds":15}','{"search":1}','rev-a');
 result:=factory_v3.claim_preparation_call(a,'q','search',repeat('a',64),'rev-a');
 IF result->>'cached'<>'false' THEN RAISE EXCEPTION 'first call cached'; END IF;
 PERFORM pg_temp.expect_failure(format('SELECT factory_v3.claim_preparation_call(%L,%L,%L,%L,%L)',a,'q','search',repeat('a',64),'rev-a'));
 PERFORM factory_v3.finish_preparation_call(a,'q','{"photos":[1]}');
 result:=factory_v3.claim_preparation_call(a,'q','search',repeat('a',64),'rev-a');
 IF result->>'cached'<>'true' OR result->'response'<>'{"photos":[1]}'::jsonb THEN
  RAISE EXCEPTION 'exact successful response not replayed'; END IF;
 PERFORM pg_temp.expect_failure(format('SELECT factory_v3.claim_preparation_call(%L,%L,%L,%L,%L)',a,'q','search',repeat('b',64),'rev-a'));
 PERFORM pg_temp.expect_failure(format('SELECT factory_v3.claim_preparation_call(%L,%L,%L,%L,%L)',a,'q','search',repeat('a',64),'rev-b'));
 PERFORM pg_temp.expect_failure(format('SELECT factory_v3.claim_preparation_call(%L,%L,%L,%L,%L)',a,'q2','search',repeat('a',64),'rev-a'));
 IF (SELECT count(*) FROM factory_v3.preparation_calls WHERE preparation_id=a)<>1 THEN
  RAISE EXCEPTION 'budget was exceeded'; END IF;
 PERFORM pg_temp.expect_failure(format('SELECT factory_v3.complete_preparation(%L,%L::jsonb,%L)',a,frozen,'rev-b'));
 PERFORM pg_temp.expect_failure(format('SELECT factory_v3.complete_preparation(%L,%L::jsonb,%L)',a,jsonb_set(frozen,'{payload,language}','"ru"'),'rev-a'));
 PERFORM factory_v3.complete_preparation(a,frozen,'rev-a');
 IF (SELECT status FROM factory_v3.jobs WHERE id=a)<>'prepared'
 OR (SELECT status FROM factory_v3.preparations WHERE id=a)<>'prepared' THEN
  RAISE EXCEPTION 'atomic handoff failed'; END IF;
 PERFORM pg_temp.expect_failure(format('SELECT factory_v3.claim_preparation_call(%L,%L,%L,%L,%L)',a,'q','search',repeat('a',64),'rev-a'));
 PERFORM pg_temp.expect_failure(format('SELECT factory_v3.complete_preparation(%L,%L::jsonb,%L)',a,frozen,'rev-a'));

 PERFORM factory_v3.create_preparation(b,'{"topic":"controlled","language":"ru","seconds":45}','{"vision":1}','rev-a');
 PERFORM factory_v3.claim_preparation_call(b,'v','vision',repeat('a',64),'rev-a');
 PERFORM pg_temp.expect_failure(format('SELECT factory_v3.complete_preparation(%L,%L::jsonb,%L)',b,frozen,'rev-a'));
 PERFORM factory_v3.fail_preparation_call(b,'v','ControlledTimeout','{"status":429,"headers":{"retry-after":"60"}}');
 IF (SELECT response->>'status' FROM factory_v3.preparation_calls WHERE preparation_id=b)<>'429' THEN RAISE EXCEPTION 'failed HTTP receipt missing'; END IF;
 PERFORM pg_temp.expect_failure(format('SELECT factory_v3.claim_preparation_call(%L,%L,%L,%L,%L)',b,'v','vision',repeat('a',64),'rev-a'));
 IF (SELECT status FROM factory_v3.preparations WHERE id=b)<>'unknown' THEN RAISE EXCEPTION 'ambiguity not terminal'; END IF;

 PERFORM factory_v3.create_preparation(c,'{"topic":"controlled","language":"uk","seconds":60}','{"search":1}','rev-a');
 PERFORM factory_v3.reject_preparation(c,'NoFeasibleMedia','rev-a');
 PERFORM pg_temp.expect_failure(format('SELECT factory_v3.claim_preparation_call(%L,%L,%L,%L,%L)',c,'q','search',repeat('a',64),'rev-a'));
 IF EXISTS(SELECT 1 FROM factory_v3.jobs WHERE id=c) THEN RAISE EXCEPTION 'rejected preparation created voice job'; END IF;
 RAISE NOTICE 'Preparation exact replay, revision, budgets, ambiguity, terminal rejection and atomic handoff PASS';
END $$;
