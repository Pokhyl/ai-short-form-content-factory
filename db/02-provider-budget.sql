CREATE SCHEMA IF NOT EXISTS factory AUTHORIZATION shorts;

CREATE TABLE IF NOT EXISTS factory.provider_budget_limits (
    provider text NOT NULL,
    sku_family text NOT NULL,
    usage_unit text NOT NULL,
    free_limit bigint NOT NULL CHECK (free_limit > 0),
    internal_limit bigint,
    enabled boolean NOT NULL DEFAULT false,
    source_verified_on date NOT NULL,
    source_url text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (provider, sku_family, usage_unit),
    CHECK (
        internal_limit IS NULL
        OR (internal_limit > 0 AND internal_limit < free_limit)
    )
);

CREATE TABLE IF NOT EXISTS factory.provider_usage_ledger (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    idempotency_key text NOT NULL UNIQUE,
    provider text NOT NULL,
    sku_family text NOT NULL,
    usage_unit text NOT NULL,
    period_start date NOT NULL,
    amount bigint NOT NULL CHECK (amount > 0),
    state text NOT NULL DEFAULT 'reserved'
        CHECK (state IN ('reserved', 'committed', 'released')),
    job_id text,
    provider_request_id text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    reserved_at timestamptz NOT NULL DEFAULT now(),
    committed_at timestamptz,
    released_at timestamptz,
    FOREIGN KEY (provider, sku_family, usage_unit)
        REFERENCES factory.provider_budget_limits(provider, sku_family, usage_unit),
    CHECK (EXTRACT(DAY FROM period_start) = 1),
    CHECK (
        (state = 'reserved' AND committed_at IS NULL AND released_at IS NULL)
        OR (state = 'committed' AND committed_at IS NOT NULL AND released_at IS NULL)
        OR (state = 'released' AND committed_at IS NULL AND released_at IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS provider_usage_lookup_idx
    ON factory.provider_usage_ledger(provider, sku_family, usage_unit, period_start, state);

CREATE OR REPLACE VIEW factory.provider_budget_status AS
SELECT
    l.provider,
    l.sku_family,
    l.usage_unit,
    l.free_limit,
    l.internal_limit,
    l.enabled,
    date_trunc('month', current_date)::date AS period_start,
    COALESCE(SUM(u.amount) FILTER (WHERE u.state = 'committed'), 0)::bigint AS committed_amount,
    COALESCE(SUM(u.amount) FILTER (WHERE u.state = 'reserved'), 0)::bigint AS reserved_amount,
    COALESCE(SUM(u.amount) FILTER (WHERE u.state IN ('reserved', 'committed')), 0)::bigint AS allocated_amount,
    CASE
        WHEN l.internal_limit IS NULL THEN NULL
        ELSE l.internal_limit
             - COALESCE(SUM(u.amount) FILTER (WHERE u.state IN ('reserved', 'committed')), 0)::bigint
    END AS remaining_internal_amount
FROM factory.provider_budget_limits l
LEFT JOIN factory.provider_usage_ledger u
  ON u.provider = l.provider
 AND u.sku_family = l.sku_family
 AND u.usage_unit = l.usage_unit
 AND u.period_start = date_trunc('month', current_date)::date
GROUP BY
    l.provider,
    l.sku_family,
    l.usage_unit,
    l.free_limit,
    l.internal_limit,
    l.enabled;

CREATE OR REPLACE FUNCTION factory.reserve_provider_usage(
    p_idempotency_key text,
    p_provider text,
    p_sku_family text,
    p_usage_unit text,
    p_period_start date,
    p_amount bigint,
    p_job_id text DEFAULT NULL,
    p_metadata jsonb DEFAULT '{}'::jsonb
)
RETURNS bigint
LANGUAGE plpgsql
AS $$
DECLARE
    v_existing factory.provider_usage_ledger%ROWTYPE;
    v_internal_limit bigint;
    v_enabled boolean;
    v_allocated bigint;
    v_id bigint;
BEGIN
    IF p_amount IS NULL OR p_amount <= 0 THEN
        RAISE EXCEPTION 'usage amount must be > 0';
    END IF;

    IF p_period_start <> date_trunc('month', p_period_start)::date THEN
        RAISE EXCEPTION 'period_start must be the first day of the billing month';
    END IF;

    SELECT *
      INTO v_existing
      FROM factory.provider_usage_ledger
     WHERE idempotency_key = p_idempotency_key;

    IF FOUND THEN
        IF v_existing.provider <> p_provider
           OR v_existing.sku_family <> p_sku_family
           OR v_existing.usage_unit <> p_usage_unit
           OR v_existing.period_start <> p_period_start
           OR v_existing.amount <> p_amount THEN
            RAISE EXCEPTION 'idempotency key already exists with different usage parameters';
        END IF;

        IF v_existing.state = 'released' THEN
            RAISE EXCEPTION 'idempotency key was already released';
        END IF;

        RETURN v_existing.id;
    END IF;

    SELECT internal_limit, enabled
      INTO v_internal_limit, v_enabled
      FROM factory.provider_budget_limits
     WHERE provider = p_provider
       AND sku_family = p_sku_family
       AND usage_unit = p_usage_unit
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'provider budget is not configured';
    END IF;

    IF NOT v_enabled OR v_internal_limit IS NULL THEN
        RAISE EXCEPTION 'provider budget is not enabled or internal limit is not configured';
    END IF;

    SELECT COALESCE(SUM(amount), 0)::bigint
      INTO v_allocated
      FROM factory.provider_usage_ledger
     WHERE provider = p_provider
       AND sku_family = p_sku_family
       AND usage_unit = p_usage_unit
       AND period_start = p_period_start
       AND state IN ('reserved', 'committed');

    IF v_allocated + p_amount > v_internal_limit THEN
        RAISE EXCEPTION 'provider budget exceeded: allocated %, requested %, internal limit %',
            v_allocated, p_amount, v_internal_limit;
    END IF;

    INSERT INTO factory.provider_usage_ledger (
        idempotency_key,
        provider,
        sku_family,
        usage_unit,
        period_start,
        amount,
        state,
        job_id,
        metadata
    )
    VALUES (
        p_idempotency_key,
        p_provider,
        p_sku_family,
        p_usage_unit,
        p_period_start,
        p_amount,
        'reserved',
        p_job_id,
        COALESCE(p_metadata, '{}'::jsonb)
    )
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION factory.commit_provider_usage(
    p_idempotency_key text,
    p_provider_request_id text DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE factory.provider_usage_ledger
       SET state = 'committed',
           provider_request_id = COALESCE(p_provider_request_id, provider_request_id),
           committed_at = now(),
           released_at = NULL
     WHERE idempotency_key = p_idempotency_key
       AND state = 'reserved';

    IF NOT FOUND THEN
        IF EXISTS (
            SELECT 1
              FROM factory.provider_usage_ledger
             WHERE idempotency_key = p_idempotency_key
               AND state = 'committed'
        ) THEN
            RETURN;
        END IF;

        RAISE EXCEPTION 'no reserved provider usage exists for idempotency key';
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION factory.release_provider_usage(
    p_idempotency_key text
)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE factory.provider_usage_ledger
       SET state = 'released',
           committed_at = NULL,
           released_at = now()
     WHERE idempotency_key = p_idempotency_key
       AND state = 'reserved';

    IF NOT FOUND THEN
        IF EXISTS (
            SELECT 1
              FROM factory.provider_usage_ledger
             WHERE idempotency_key = p_idempotency_key
               AND state = 'released'
        ) THEN
            RETURN;
        END IF;

        RAISE EXCEPTION 'no reserved provider usage exists for idempotency key';
    END IF;
END;
$$;

INSERT INTO factory.provider_budget_limits (
    provider,
    sku_family,
    usage_unit,
    free_limit,
    internal_limit,
    enabled,
    source_verified_on,
    source_url
)
VALUES
    (
        'google_cloud_tts',
        'chirp3_hd',
        'characters',
        1000000,
        NULL,
        false,
        DATE '2026-09-19',
        'https://cloud.google.com/text-to-speech/pricing'
    ),
    (
        'google_cloud_tts',
        'wavenet',
        'characters',
        4000000,
        NULL,
        false,
        DATE '2026-09-19',
        'https://cloud.google.com/text-to-speech/pricing'
    )
ON CONFLICT (provider, sku_family, usage_unit)
DO UPDATE SET
    free_limit = EXCLUDED.free_limit,
    source_verified_on = EXCLUDED.source_verified_on,
    source_url = EXCLUDED.source_url,
    updated_at = now();
