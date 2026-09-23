-- M3 intake persistence.
-- One valid request creates exactly one durable job row.
-- API validation is duplicated here so invalid input cannot enter PostgreSQL
-- even if a workflow node is changed later.

CREATE TABLE IF NOT EXISTS factory.jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    topic text NOT NULL,
    language_code text NOT NULL,
    target_duration_seconds integer NOT NULL,
    visual_validation_mode text NOT NULL DEFAULT 'metadata',
    status text NOT NULL DEFAULT 'created',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT jobs_topic_trimmed CHECK (topic = btrim(topic)),
    CONSTRAINT jobs_topic_length CHECK (char_length(topic) BETWEEN 3 AND 500),
    CONSTRAINT jobs_language_code CHECK (language_code IN ('en', 'pl', 'ru', 'uk')),
    CONSTRAINT jobs_target_duration CHECK (target_duration_seconds IN (15, 30, 45, 60)),
    CONSTRAINT jobs_visual_validation_mode CHECK (visual_validation_mode IN ('metadata', 'gemini')),
    CONSTRAINT jobs_status_nonempty CHECK (char_length(status) BETWEEN 1 AND 64)
);

ALTER TABLE factory.jobs
    ADD COLUMN IF NOT EXISTS visual_validation_mode text;

UPDATE factory.jobs
   SET visual_validation_mode='metadata'
 WHERE visual_validation_mode IS NULL;

ALTER TABLE factory.jobs
    ALTER COLUMN visual_validation_mode SET DEFAULT 'metadata',
    ALTER COLUMN visual_validation_mode SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid='factory.jobs'::regclass
          AND conname='jobs_visual_validation_mode'
    ) THEN
        ALTER TABLE factory.jobs
            ADD CONSTRAINT jobs_visual_validation_mode
            CHECK (visual_validation_mode IN ('metadata', 'gemini'));
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS jobs_created_at_idx
    ON factory.jobs (created_at DESC);

CREATE INDEX IF NOT EXISTS jobs_status_created_at_idx
    ON factory.jobs (status, created_at DESC);

CREATE OR REPLACE FUNCTION factory.create_job(
    p_topic text,
    p_language_code text,
    p_target_duration_seconds integer
)
RETURNS TABLE (
    job_id uuid,
    created_at timestamptz
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id uuid;
    v_created_at timestamptz;
BEGIN
    IF p_topic IS NULL
       OR p_topic <> btrim(p_topic)
       OR char_length(p_topic) < 3
       OR char_length(p_topic) > 500 THEN
        RAISE EXCEPTION 'invalid topic'
            USING ERRCODE = '22023';
    END IF;

    IF p_language_code IS NULL
       OR p_language_code NOT IN ('en', 'pl', 'ru', 'uk') THEN
        RAISE EXCEPTION 'invalid language_code'
            USING ERRCODE = '22023';
    END IF;

    IF p_target_duration_seconds IS NULL
       OR p_target_duration_seconds NOT IN (15, 30, 45, 60) THEN
        RAISE EXCEPTION 'invalid target_duration_seconds'
            USING ERRCODE = '22023';
    END IF;

    INSERT INTO factory.jobs (
        topic,
        language_code,
        target_duration_seconds,
        status
    )
    VALUES (
        p_topic,
        p_language_code,
        p_target_duration_seconds,
        'created'
    )
    RETURNING id, factory.jobs.created_at
      INTO v_id, v_created_at;

    RETURN QUERY
    SELECT v_id, v_created_at;
END;
$$;

CREATE OR REPLACE FUNCTION factory.create_job(
    p_topic text,
    p_language_code text,
    p_target_duration_seconds integer,
    p_visual_validation_mode text
)
RETURNS TABLE (
    job_id uuid,
    created_at timestamptz
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id uuid;
    v_created_at timestamptz;
BEGIN
    IF p_topic IS NULL
       OR p_topic <> btrim(p_topic)
       OR char_length(p_topic) < 3
       OR char_length(p_topic) > 500 THEN
        RAISE EXCEPTION 'invalid topic'
            USING ERRCODE = '22023';
    END IF;

    IF p_language_code IS NULL
       OR p_language_code NOT IN ('en', 'pl', 'ru', 'uk') THEN
        RAISE EXCEPTION 'invalid language_code'
            USING ERRCODE = '22023';
    END IF;

    IF p_target_duration_seconds IS NULL
       OR p_target_duration_seconds NOT IN (15, 30, 45, 60) THEN
        RAISE EXCEPTION 'invalid target_duration_seconds'
            USING ERRCODE = '22023';
    END IF;

    IF p_visual_validation_mode IS NULL
       OR p_visual_validation_mode NOT IN ('metadata', 'gemini') THEN
        RAISE EXCEPTION 'invalid visual_validation_mode'
            USING ERRCODE = '22023';
    END IF;

    INSERT INTO factory.jobs (
        topic,
        language_code,
        target_duration_seconds,
        visual_validation_mode,
        status
    )
    VALUES (
        p_topic,
        p_language_code,
        p_target_duration_seconds,
        p_visual_validation_mode,
        'created'
    )
    RETURNING id, factory.jobs.created_at
      INTO v_id, v_created_at;

    RETURN QUERY
    SELECT v_id, v_created_at;
END;
$$;
