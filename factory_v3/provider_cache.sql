-- Exact non-secret query identity; isolated/new V3 schema only.
CREATE TABLE IF NOT EXISTS factory_v3.provider_cache (
 identity_hash text PRIMARY KEY CHECK(identity_hash ~ '^[0-9a-f]{64}$'),
 provider text NOT NULL,
 state text NOT NULL CHECK(state IN ('started','succeeded','unknown')),
 receipt jsonb,
 expires_at timestamptz,
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE OR REPLACE FUNCTION factory_v3.claim_provider_cache(p_hash text,p_provider text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE old factory_v3.provider_cache%ROWTYPE;
BEGIN
 PERFORM pg_advisory_xact_lock(hashtextextended(p_hash,0));
 SELECT * INTO old FROM factory_v3.provider_cache WHERE identity_hash=p_hash FOR UPDATE;
 IF FOUND THEN
  IF old.provider<>p_provider THEN RAISE EXCEPTION 'provider identity mismatch'; END IF;
  IF old.state='succeeded' AND old.expires_at>now() THEN
   RETURN jsonb_build_object('cached',true,'receipt',old.receipt);
  END IF;
  IF old.state<>'succeeded' THEN RAISE EXCEPTION 'provider query pending or ambiguous'; END IF;
  UPDATE factory_v3.provider_cache SET state='started',receipt=NULL,expires_at=NULL,updated_at=now()
   WHERE identity_hash=p_hash;
 ELSE
  INSERT INTO factory_v3.provider_cache(identity_hash,provider,state) VALUES(p_hash,p_provider,'started');
 END IF;
 RETURN jsonb_build_object('cached',false);
END $$;
CREATE OR REPLACE FUNCTION factory_v3.finish_provider_cache(p_hash text,p_receipt jsonb)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 UPDATE factory_v3.provider_cache SET state='succeeded',receipt=p_receipt,
  expires_at=now()+interval '24 hours',updated_at=now()
 WHERE identity_hash=p_hash AND state='started';
 IF NOT FOUND THEN RAISE EXCEPTION 'provider query not claimed'; END IF;
END $$;
CREATE OR REPLACE FUNCTION factory_v3.fail_provider_cache(p_hash text,p_receipt jsonb)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 UPDATE factory_v3.provider_cache SET state='unknown',receipt=p_receipt,updated_at=now()
 WHERE identity_hash=p_hash AND state='started';
 IF NOT FOUND THEN RAISE EXCEPTION 'provider query not claimed'; END IF;
END $$;
