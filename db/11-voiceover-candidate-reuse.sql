-- Reuse the exact M5 timing-qualified TTS audio in M6.
-- M5 persists one accepted MP3 candidate; M6 adopts it instead of re-synthesizing.

CREATE TABLE IF NOT EXISTS factory.voiceover_candidates (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL UNIQUE
        REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    script_run_id uuid NOT NULL UNIQUE
        REFERENCES factory.script_runs(id) ON DELETE RESTRICT,
    provider text NOT NULL DEFAULT 'google_cloud_tts',
    sku_family text NOT NULL,
    locale text NOT NULL,
    voice_name text NOT NULL,
    narration text NOT NULL,
    usage_idempotency_key text NOT NULL UNIQUE,
    usage_ledger_id bigint NOT NULL UNIQUE
        REFERENCES factory.provider_usage_ledger(id) ON DELETE RESTRICT,
    storage_path text NOT NULL UNIQUE,
    audio_sha256 text NOT NULL,
    bytes bigint NOT NULL,
    duration_ms integer NOT NULL,
    sample_rate integer NOT NULL,
    channels integer NOT NULL,
    codec text NOT NULL,
    voiceover_run_id uuid UNIQUE
        REFERENCES factory.voiceover_runs(id) ON DELETE RESTRICT,
    adopted_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT voiceover_candidates_provider
        CHECK (provider = 'google_cloud_tts'),
    CONSTRAINT voiceover_candidates_sku
        CHECK (sku_family IN ('chirp3_hd','wavenet')),
    CONSTRAINT voiceover_candidates_locale_nonempty
        CHECK (char_length(btrim(locale)) > 0),
    CONSTRAINT voiceover_candidates_voice_nonempty
        CHECK (char_length(btrim(voice_name)) > 0),
    CONSTRAINT voiceover_candidates_narration_nonempty
        CHECK (char_length(btrim(narration)) > 0),
    CONSTRAINT voiceover_candidates_path_nonempty
        CHECK (char_length(btrim(storage_path)) > 0),
    CONSTRAINT voiceover_candidates_sha256
        CHECK (audio_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT voiceover_candidates_bytes_positive
        CHECK (bytes > 0),
    CONSTRAINT voiceover_candidates_duration_positive
        CHECK (duration_ms > 0),
    CONSTRAINT voiceover_candidates_sample_rate_positive
        CHECK (sample_rate > 0),
    CONSTRAINT voiceover_candidates_channels_positive
        CHECK (channels > 0),
    CONSTRAINT voiceover_candidates_codec_mp3
        CHECK (codec = 'mp3'),
    CONSTRAINT voiceover_candidates_adoption
        CHECK (
            (voiceover_run_id IS NULL AND adopted_at IS NULL)
            OR
            (voiceover_run_id IS NOT NULL AND adopted_at IS NOT NULL)
        )
);

CREATE INDEX IF NOT EXISTS voiceover_candidates_created_idx
    ON factory.voiceover_candidates (created_at DESC);

CREATE OR REPLACE FUNCTION factory.register_voiceover_candidate(
    p_script_run_id uuid,
    p_narration text,
    p_locale text,
    p_voice_name text,
    p_sku_family text,
    p_usage_idempotency_key text,
    p_storage_path text,
    p_audio_sha256 text,
    p_bytes bigint,
    p_duration_ms integer,
    p_sample_rate integer,
    p_channels integer,
    p_codec text
)
RETURNS TABLE (
    candidate_id uuid,
    duration_ms integer,
    audio_sha256 text
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.script_runs%ROWTYPE;
    v_job factory.jobs%ROWTYPE;
    v_usage factory.provider_usage_ledger%ROWTYPE;
    v_locale text;
    v_voice text;
    v_sku text;
    v_expected_path text;
    v_target_ms integer;
    v_tolerance_ms integer;
    v_candidate_id uuid;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.script_runs
     WHERE id = p_script_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'script run is not active'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_job
      FROM factory.jobs
     WHERE id = v_run.job_id
     FOR UPDATE;

    IF NOT FOUND OR v_job.status <> 'scripting' THEN
        RAISE EXCEPTION 'job is not in scripting state'
            USING ERRCODE='22023';
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
                USING ERRCODE='22023';
    END CASE;

    IF btrim(COALESCE(p_narration,'')) = '' THEN
        RAISE EXCEPTION 'candidate narration is empty'
            USING ERRCODE='22023';
    END IF;

    IF p_locale <> v_locale
       OR p_voice_name <> v_voice
       OR p_sku_family <> v_sku THEN
        RAISE EXCEPTION 'candidate TTS configuration mismatch'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_usage
      FROM factory.provider_usage_ledger
     WHERE idempotency_key = p_usage_idempotency_key
     FOR UPDATE;

    IF NOT FOUND
       OR v_usage.state <> 'committed'
       OR v_usage.provider <> 'google_cloud_tts'
       OR v_usage.sku_family <> v_sku
       OR v_usage.usage_unit <> 'characters'
       OR v_usage.job_id <> v_job.id::text
       OR v_usage.amount <> char_length(p_narration) THEN
        RAISE EXCEPTION 'candidate provider usage is not a committed matching M5 TTS call'
            USING ERRCODE='22023';
    END IF;

    IF COALESCE(v_usage.metadata->>'stage','') <> 'M5_TIMING_PROBE' THEN
        RAISE EXCEPTION 'candidate provider usage is not an M5 timing probe'
            USING ERRCODE='22023';
    END IF;

    v_expected_path :=
        '/data/voiceover-candidates/' || v_job.id::text || '/accepted.mp3';

    IF btrim(COALESCE(p_storage_path,'')) <> v_expected_path THEN
        RAISE EXCEPTION 'unexpected voiceover candidate storage path'
            USING ERRCODE='22023';
    END IF;

    v_target_ms := v_job.target_duration_seconds * 1000;
    v_tolerance_ms := GREATEST(
        750,
        round(v_target_ms * 0.05)::integer
    ) + 50;

    IF p_duration_ms IS NULL
       OR abs(p_duration_ms - v_target_ms) > v_tolerance_ms THEN
        RAISE EXCEPTION
            'voiceover candidate duration outside final tolerance: got % ms, target % ms, tolerance % ms',
            p_duration_ms,v_target_ms,v_tolerance_ms
            USING ERRCODE='22023';
    END IF;

    IF p_audio_sha256 !~ '^[0-9a-f]{64}$'
       OR p_bytes IS NULL OR p_bytes <= 0
       OR p_sample_rate IS NULL OR p_sample_rate <= 0
       OR p_channels IS NULL OR p_channels <= 0
       OR p_codec <> 'mp3' THEN
        RAISE EXCEPTION 'invalid voiceover candidate metadata'
            USING ERRCODE='22023';
    END IF;

    INSERT INTO factory.voiceover_candidates (
        job_id,
        script_run_id,
        provider,
        sku_family,
        locale,
        voice_name,
        narration,
        usage_idempotency_key,
        usage_ledger_id,
        storage_path,
        audio_sha256,
        bytes,
        duration_ms,
        sample_rate,
        channels,
        codec
    )
    VALUES (
        v_job.id,
        v_run.id,
        'google_cloud_tts',
        v_sku,
        v_locale,
        v_voice,
        p_narration,
        p_usage_idempotency_key,
        v_usage.id,
        v_expected_path,
        lower(p_audio_sha256),
        p_bytes,
        p_duration_ms,
        p_sample_rate,
        p_channels,
        p_codec
    )
    RETURNING id INTO v_candidate_id;

    RETURN QUERY
    SELECT v_candidate_id,p_duration_ms,lower(p_audio_sha256);
END;
$$;

CREATE OR REPLACE FUNCTION factory.begin_voiceover_v2(
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
    usage_idempotency_key text,
    reuse_candidate boolean,
    candidate_id uuid,
    candidate_storage_path text,
    candidate_audio_sha256 text,
    candidate_bytes bigint,
    candidate_duration_ms integer,
    candidate_sample_rate integer,
    candidate_channels integer,
    candidate_codec text
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_job factory.jobs%ROWTYPE;
    v_script factory.script_versions%ROWTYPE;
    v_candidate factory.voiceover_candidates%ROWTYPE;
    v_usage factory.provider_usage_ledger%ROWTYPE;
    v_locale text;
    v_voice text;
    v_sku text;
    v_chars bigint;
    v_key text;
    v_ledger_id bigint;
    v_run_id uuid;
    v_reuse boolean := false;
    v_expected_candidate_path text;
    v_target_ms integer;
    v_tolerance_ms integer;
BEGIN
    SELECT *
      INTO v_job
      FROM factory.jobs
     WHERE id = p_job_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'job not found'
            USING ERRCODE='22023';
    END IF;

    IF v_job.status <> 'storyboard_ready' THEN
        RAISE EXCEPTION 'job is not voiceover-ready from status %', v_job.status
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_script
      FROM factory.script_versions
     WHERE job_id = p_job_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'script version not found'
            USING ERRCODE='22023';
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
                USING ERRCODE='22023';
    END CASE;

    v_chars := char_length(v_script.narration);
    IF v_chars <= 0 THEN
        RAISE EXCEPTION 'narration is empty'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_candidate
      FROM factory.voiceover_candidates
     WHERE job_id = p_job_id
     FOR UPDATE;

    IF FOUND THEN
        IF v_candidate.voiceover_run_id IS NOT NULL
           OR v_candidate.adopted_at IS NOT NULL THEN
            RAISE EXCEPTION 'voiceover candidate is already adopted'
                USING ERRCODE='22023';
        END IF;

        SELECT *
          INTO v_usage
          FROM factory.provider_usage_ledger
         WHERE id = v_candidate.usage_ledger_id
         FOR UPDATE;

        v_expected_candidate_path :=
            '/data/voiceover-candidates/' || p_job_id::text || '/accepted.mp3';
        v_target_ms := v_job.target_duration_seconds * 1000;
        v_tolerance_ms := GREATEST(
            750,
            round(v_target_ms * 0.05)::integer
        ) + 50;

        IF v_candidate.script_run_id <> v_script.script_run_id
           OR v_candidate.narration <> v_script.narration
           OR v_candidate.locale <> v_locale
           OR v_candidate.voice_name <> v_voice
           OR v_candidate.sku_family <> v_sku
           OR v_candidate.storage_path <> v_expected_candidate_path
           OR abs(v_candidate.duration_ms - v_target_ms) > v_tolerance_ms
           OR NOT FOUND
           OR v_usage.state <> 'committed'
           OR v_usage.id <> v_candidate.usage_ledger_id
           OR v_usage.idempotency_key <> v_candidate.usage_idempotency_key
           OR v_usage.provider <> 'google_cloud_tts'
           OR v_usage.sku_family <> v_sku
           OR v_usage.job_id <> p_job_id::text THEN
            RAISE EXCEPTION 'stored voiceover candidate does not match committed script/TTS usage'
                USING ERRCODE='22023';
        END IF;

        v_key := v_candidate.usage_idempotency_key;
        v_ledger_id := v_candidate.usage_ledger_id;
        v_reuse := true;
    ELSE
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
    END IF;

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
        usage_ledger_id,
        tts_consumed_at
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
        v_ledger_id,
        CASE WHEN v_reuse THEN now() ELSE NULL END
    )
    RETURNING id INTO v_run_id;

    IF v_reuse THEN
        UPDATE factory.voiceover_candidates
           SET voiceover_run_id = v_run_id,
               adopted_at = now()
         WHERE id = v_candidate.id;
    END IF;

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
        v_key,
        v_reuse,
        CASE WHEN v_reuse THEN v_candidate.id ELSE NULL END,
        CASE WHEN v_reuse THEN v_candidate.storage_path ELSE NULL END,
        CASE WHEN v_reuse THEN v_candidate.audio_sha256 ELSE NULL END,
        CASE WHEN v_reuse THEN v_candidate.bytes ELSE NULL END,
        CASE WHEN v_reuse THEN v_candidate.duration_ms ELSE NULL END,
        CASE WHEN v_reuse THEN v_candidate.sample_rate ELSE NULL END,
        CASE WHEN v_reuse THEN v_candidate.channels ELSE NULL END,
        CASE WHEN v_reuse THEN v_candidate.codec ELSE NULL END;
END;
$$;
