-- M6 one-final-voiceover persistence and free-only TTS accounting.

CREATE TABLE IF NOT EXISTS factory.voiceover_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL UNIQUE REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    script_version_id uuid NOT NULL UNIQUE REFERENCES factory.script_versions(id) ON DELETE RESTRICT,
    status text NOT NULL DEFAULT 'running',
    provider text NOT NULL DEFAULT 'google_cloud_tts',
    sku_family text NOT NULL,
    language_code text NOT NULL,
    locale text NOT NULL,
    voice_name text NOT NULL,
    character_count bigint NOT NULL,
    usage_idempotency_key text NOT NULL UNIQUE,
    usage_ledger_id bigint NOT NULL REFERENCES factory.provider_usage_ledger(id) ON DELETE RESTRICT,
    tts_consumed_at timestamptz,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    failure_reason text,

    CONSTRAINT voiceover_runs_status
        CHECK (status IN ('running','passed','failed')),
    CONSTRAINT voiceover_runs_provider
        CHECK (provider = 'google_cloud_tts'),
    CONSTRAINT voiceover_runs_sku
        CHECK (sku_family IN ('chirp3_hd','wavenet')),
    CONSTRAINT voiceover_runs_language
        CHECK (language_code IN ('en','pl','ru','uk')),
    CONSTRAINT voiceover_runs_character_count
        CHECK (character_count > 0),
    CONSTRAINT voiceover_runs_voice_nonempty
        CHECK (char_length(btrim(voice_name)) > 0),
    CONSTRAINT voiceover_runs_completion
        CHECK (
            (status = 'running' AND completed_at IS NULL)
            OR
            (status IN ('passed','failed') AND completed_at IS NOT NULL)
        )
);

CREATE TABLE IF NOT EXISTS factory.voiceovers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL UNIQUE REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    voiceover_run_id uuid NOT NULL UNIQUE REFERENCES factory.voiceover_runs(id) ON DELETE RESTRICT,
    script_version_id uuid NOT NULL UNIQUE REFERENCES factory.script_versions(id) ON DELETE RESTRICT,
    provider text NOT NULL,
    locale text NOT NULL,
    voice_name text NOT NULL,
    storage_path text NOT NULL UNIQUE,
    audio_sha256 text NOT NULL,
    bytes bigint NOT NULL,
    duration_ms integer NOT NULL,
    sample_rate integer NOT NULL,
    channels integer NOT NULL,
    codec text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT voiceovers_provider CHECK (provider = 'google_cloud_tts'),
    CONSTRAINT voiceovers_path_nonempty CHECK (char_length(btrim(storage_path)) > 0),
    CONSTRAINT voiceovers_sha256 CHECK (audio_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT voiceovers_bytes_positive CHECK (bytes > 0),
    CONSTRAINT voiceovers_duration_positive CHECK (duration_ms > 0),
    CONSTRAINT voiceovers_sample_rate_positive CHECK (sample_rate > 0),
    CONSTRAINT voiceovers_channels_positive CHECK (channels > 0),
    CONSTRAINT voiceovers_codec_mp3 CHECK (codec = 'mp3')
);

CREATE INDEX IF NOT EXISTS voiceover_runs_status_idx
    ON factory.voiceover_runs (status, started_at);

CREATE OR REPLACE FUNCTION factory.begin_voiceover(
    p_job_id uuid
)
RETURNS TABLE (
    voiceover_run_id uuid,
    script_version_id uuid,
    narration text,
    language_code text,
    target_duration_seconds integer,
    locale text,
    voice_name text,
    sku_family text,
    character_count bigint,
    usage_idempotency_key text
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_job factory.jobs%ROWTYPE;
    v_script factory.script_versions%ROWTYPE;
    v_locale text;
    v_voice text;
    v_sku text;
    v_chars bigint;
    v_key text;
    v_ledger_id bigint;
    v_run_id uuid;
BEGIN
    SELECT *
      INTO v_job
      FROM factory.jobs
     WHERE id = p_job_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'job not found'
            USING ERRCODE = '22023';
    END IF;

    IF v_job.status <> 'storyboard_ready' THEN
        RAISE EXCEPTION 'job is not voiceover-ready from status %', v_job.status
            USING ERRCODE = '22023';
    END IF;

    SELECT *
      INTO v_script
      FROM factory.script_versions
     WHERE job_id = p_job_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'script version not found'
            USING ERRCODE = '22023';
    END IF;

    CASE v_job.language_code
        WHEN 'en' THEN
            v_locale := 'en-US';
            v_voice := 'en-US-Chirp3-HD-Algenib';
            v_sku := 'chirp3_hd';
        WHEN 'pl' THEN
            v_locale := 'pl-PL';
            v_voice := 'pl-PL-Chirp3-HD-Enceladus';
            v_sku := 'chirp3_hd';
        WHEN 'ru' THEN
            v_locale := 'ru-RU';
            v_voice := 'ru-RU-Wavenet-D';
            v_sku := 'wavenet';
        WHEN 'uk' THEN
            v_locale := 'uk-UA';
            v_voice := 'uk-UA-Chirp3-HD-Enceladus';
            v_sku := 'chirp3_hd';
        ELSE
            RAISE EXCEPTION 'unsupported language code %', v_job.language_code
                USING ERRCODE = '22023';
    END CASE;

    v_chars := char_length(v_script.narration);
    IF v_chars <= 0 THEN
        RAISE EXCEPTION 'narration is empty'
            USING ERRCODE = '22023';
    END IF;

    v_key := 'm6-tts:' || p_job_id::text;

    v_ledger_id := factory.reserve_provider_usage(
        v_key,
        'google_cloud_tts',
        v_sku,
        'characters',
        date_trunc('month', CURRENT_DATE)::date,
        v_chars,
        p_job_id::text,
        jsonb_build_object(
            'stage', 'M6',
            'voice_name', v_voice,
            'locale', v_locale,
            'script_version_id', v_script.id::text
        )
    );

    INSERT INTO factory.voiceover_runs (
        job_id,
        script_version_id,
        status,
        provider,
        sku_family,
        language_code,
        locale,
        voice_name,
        character_count,
        usage_idempotency_key,
        usage_ledger_id
    )
    VALUES (
        p_job_id,
        v_script.id,
        'running',
        'google_cloud_tts',
        v_sku,
        v_job.language_code,
        v_locale,
        v_voice,
        v_chars,
        v_key,
        v_ledger_id
    )
    RETURNING id INTO v_run_id;

    UPDATE factory.jobs
       SET status = 'voiceover_synthesizing',
           updated_at = now()
     WHERE id = p_job_id;

    RETURN QUERY
    SELECT
        v_run_id,
        v_script.id,
        v_script.narration,
        v_job.language_code,
        v_job.target_duration_seconds,
        v_locale,
        v_voice,
        v_sku,
        v_chars,
        v_key;
END;
$$;

CREATE OR REPLACE FUNCTION factory.mark_tts_consumed(
    p_voiceover_run_id uuid
)
RETURNS TABLE (
    usage_state text,
    usage_idempotency_key text
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.voiceover_runs%ROWTYPE;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.voiceover_runs
     WHERE id = p_voiceover_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'voiceover run is not active'
            USING ERRCODE = '22023';
    END IF;

    PERFORM factory.commit_provider_usage(
        v_run.usage_idempotency_key,
        NULL
    );

    UPDATE factory.voiceover_runs
       SET tts_consumed_at = COALESCE(tts_consumed_at, now())
     WHERE id = v_run.id;

    RETURN QUERY
    SELECT 'committed'::text, v_run.usage_idempotency_key;
END;
$$;

CREATE OR REPLACE FUNCTION factory.complete_voiceover(
    p_voiceover_run_id uuid,
    p_storage_path text,
    p_audio_sha256 text,
    p_bytes bigint,
    p_duration_ms integer,
    p_sample_rate integer,
    p_channels integer,
    p_codec text
)
RETURNS TABLE (
    voiceover_id uuid,
    duration_ms integer,
    audio_sha256 text
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.voiceover_runs%ROWTYPE;
    v_voiceover_id uuid;
    v_expected_path text;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.voiceover_runs
     WHERE id = p_voiceover_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'voiceover run is not active'
            USING ERRCODE = '22023';
    END IF;

    IF v_run.tts_consumed_at IS NULL THEN
        RAISE EXCEPTION 'TTS usage is not committed'
            USING ERRCODE = '22023';
    END IF;

    v_expected_path :=
        '/data/voiceovers/' || v_run.job_id::text || '/final.mp3';

    IF btrim(COALESCE(p_storage_path,'')) <> v_expected_path THEN
        RAISE EXCEPTION 'unexpected voiceover storage path'
            USING ERRCODE = '22023';
    END IF;

    IF p_audio_sha256 !~ '^[0-9a-f]{64}$'
       OR p_bytes IS NULL OR p_bytes <= 0
       OR p_duration_ms IS NULL OR p_duration_ms <= 0
       OR p_sample_rate IS NULL OR p_sample_rate <= 0
       OR p_channels IS NULL OR p_channels <= 0
       OR p_codec <> 'mp3' THEN
        RAISE EXCEPTION 'invalid stored voiceover metadata'
            USING ERRCODE = '22023';
    END IF;

    INSERT INTO factory.voiceovers (
        job_id,
        voiceover_run_id,
        script_version_id,
        provider,
        locale,
        voice_name,
        storage_path,
        audio_sha256,
        bytes,
        duration_ms,
        sample_rate,
        channels,
        codec
    )
    VALUES (
        v_run.job_id,
        v_run.id,
        v_run.script_version_id,
        v_run.provider,
        v_run.locale,
        v_run.voice_name,
        v_expected_path,
        p_audio_sha256,
        p_bytes,
        p_duration_ms,
        p_sample_rate,
        p_channels,
        p_codec
    )
    RETURNING id INTO v_voiceover_id;

    UPDATE factory.voiceover_runs
       SET status = 'passed',
           completed_at = now(),
           failure_reason = NULL
     WHERE id = v_run.id;

    UPDATE factory.jobs
       SET status = 'voiceover_ready',
           updated_at = now()
     WHERE id = v_run.job_id;

    RETURN QUERY
    SELECT v_voiceover_id, p_duration_ms, p_audio_sha256;
END;
$$;

CREATE OR REPLACE FUNCTION factory.fail_voiceover(
    p_voiceover_run_id uuid,
    p_reason text,
    p_tts_consumed boolean
)
RETURNS TABLE (
    voiceover_status text,
    job_status text,
    usage_state text
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.voiceover_runs%ROWTYPE;
    v_job_status text;
    v_usage_state text;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.voiceover_runs
     WHERE id = p_voiceover_run_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'voiceover run not found'
            USING ERRCODE = '22023';
    END IF;

    IF v_run.status = 'passed' THEN
        RAISE EXCEPTION 'passed voiceover run cannot be failed'
            USING ERRCODE = '22023';
    END IF;

    IF v_run.status = 'running' THEN
        IF p_tts_consumed OR v_run.tts_consumed_at IS NOT NULL THEN
            PERFORM factory.commit_provider_usage(
                v_run.usage_idempotency_key,
                NULL
            );
            v_usage_state := 'committed';

            UPDATE factory.voiceover_runs
               SET tts_consumed_at = COALESCE(tts_consumed_at, now())
             WHERE id = v_run.id;
        ELSE
            PERFORM factory.release_provider_usage(
                v_run.usage_idempotency_key
            );
            v_usage_state := 'released';
        END IF;

        UPDATE factory.voiceover_runs
           SET status = 'failed',
               completed_at = now(),
               failure_reason = left(
                   COALESCE(NULLIF(btrim(p_reason), ''), 'unspecified voiceover failure'),
                   4000
               )
         WHERE id = v_run.id;

        UPDATE factory.jobs
           SET status = 'voiceover_failed',
               updated_at = now()
         WHERE id = v_run.job_id;
    ELSE
        SELECT state
          INTO v_usage_state
          FROM factory.provider_usage_ledger
         WHERE id = v_run.usage_ledger_id;
    END IF;

    SELECT status INTO v_job_status
      FROM factory.jobs
     WHERE id = v_run.job_id;

    RETURN QUERY
    SELECT 'failed'::text, v_job_status, v_usage_state;
END;
$$;
