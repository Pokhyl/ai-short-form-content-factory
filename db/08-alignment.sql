-- M7 exact local alignment persistence.
-- Alignment runs only against the immutable M6 final.mp3 and the pinned
-- whisper.cpp image/model accepted in M2. No proportional timing fallback.

CREATE TABLE IF NOT EXISTS factory.alignment_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL UNIQUE REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    voiceover_id uuid NOT NULL UNIQUE REFERENCES factory.voiceovers(id) ON DELETE RESTRICT,
    status text NOT NULL DEFAULT 'running',
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    failure_reason text,

    CONSTRAINT alignment_runs_status
        CHECK (status IN ('running','passed','failed')),
    CONSTRAINT alignment_runs_completion
        CHECK (
            (status='running' AND completed_at IS NULL)
            OR
            (status IN ('passed','failed') AND completed_at IS NOT NULL)
        )
);

CREATE TABLE IF NOT EXISTS factory.alignments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL UNIQUE REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    alignment_run_id uuid NOT NULL UNIQUE REFERENCES factory.alignment_runs(id) ON DELETE RESTRICT,
    voiceover_id uuid NOT NULL UNIQUE REFERENCES factory.voiceovers(id) ON DELETE RESTRICT,
    language_code text NOT NULL,
    alignment_path text NOT NULL UNIQUE,
    raw_whisper_path text NOT NULL UNIQUE,
    audio_sha256 text NOT NULL,
    audio_duration_ms integer NOT NULL,
    model_sha256 text NOT NULL,
    whisper_image_digest text NOT NULL,
    transcript text NOT NULL,
    normalized_match boolean NOT NULL,
    global_coverage numeric(4,3) NOT NULL,
    lexical_token_count integer NOT NULL,
    lexical_start_ms integer NOT NULL,
    lexical_end_ms integer NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT alignments_language
        CHECK (language_code IN ('en','pl','ru','uk')),
    CONSTRAINT alignments_audio_sha
        CHECK (audio_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT alignments_model_sha
        CHECK (model_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT alignments_match_true CHECK (normalized_match = true),
    CONSTRAINT alignments_global_coverage CHECK (global_coverage = 1.000),
    CONSTRAINT alignments_token_count CHECK (lexical_token_count > 0),
    CONSTRAINT alignments_audio_duration CHECK (audio_duration_ms > 0),
    CONSTRAINT alignments_lexical_start CHECK (lexical_start_ms >= 0),
    CONSTRAINT alignments_lexical_end CHECK (
        lexical_end_ms > lexical_start_ms
        AND lexical_end_ms <= audio_duration_ms
    )
);

CREATE TABLE IF NOT EXISTS factory.scene_timings (
    scene_id uuid PRIMARY KEY REFERENCES factory.scenes(id) ON DELETE RESTRICT,
    alignment_id uuid NOT NULL REFERENCES factory.alignments(id) ON DELETE RESTRICT,
    job_id uuid NOT NULL REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    start_ms integer NOT NULL,
    end_ms integer NOT NULL,
    coverage numeric(4,3) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT scene_timings_start CHECK (start_ms >= 0),
    CONSTRAINT scene_timings_end CHECK (end_ms > start_ms),
    CONSTRAINT scene_timings_coverage CHECK (coverage = 1.000)
);

CREATE INDEX IF NOT EXISTS scene_timings_job_idx
    ON factory.scene_timings (job_id);

CREATE OR REPLACE FUNCTION factory.begin_alignment(
    p_job_id uuid
)
RETURNS TABLE (
    alignment_run_id uuid,
    voiceover_id uuid,
    language_code text,
    narration text,
    audio_sha256 text,
    audio_duration_ms integer,
    scenes_json jsonb
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_job factory.jobs%ROWTYPE;
    v_voiceover factory.voiceovers%ROWTYPE;
    v_script factory.script_versions%ROWTYPE;
    v_run_id uuid;
    v_scenes jsonb;
BEGIN
    SELECT *
      INTO v_job
      FROM factory.jobs
     WHERE id=p_job_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'job not found'
            USING ERRCODE='22023';
    END IF;

    IF v_job.status <> 'voiceover_ready' THEN
        RAISE EXCEPTION 'job is not alignment-ready from status %', v_job.status
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_voiceover
      FROM factory.voiceovers
     WHERE job_id=p_job_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'voiceover not found'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_script
      FROM factory.script_versions
     WHERE job_id=p_job_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'script version not found'
            USING ERRCODE='22023';
    END IF;

    IF v_voiceover.script_version_id <> v_script.id THEN
        RAISE EXCEPTION 'voiceover/script version mismatch'
            USING ERRCODE='22023';
    END IF;

    SELECT jsonb_agg(
               jsonb_build_object(
                   'scene_uuid', s.id::text,
                   'scene_key', s.scene_key,
                   'narration', s.narration
               )
               ORDER BY s.scene_order
           )
      INTO v_scenes
      FROM factory.scenes s
     WHERE s.job_id=p_job_id;

    IF v_scenes IS NULL OR jsonb_array_length(v_scenes)=0 THEN
        RAISE EXCEPTION 'scenes not found'
            USING ERRCODE='22023';
    END IF;

    INSERT INTO factory.alignment_runs (
        job_id,voiceover_id,status
    )
    VALUES (
        p_job_id,v_voiceover.id,'running'
    )
    RETURNING id INTO v_run_id;

    UPDATE factory.jobs
       SET status='aligning',
           updated_at=now()
     WHERE id=p_job_id;

    RETURN QUERY
    SELECT
        v_run_id,
        v_voiceover.id,
        v_job.language_code,
        v_script.narration,
        v_voiceover.audio_sha256,
        v_voiceover.duration_ms,
        v_scenes;
END;
$$;

CREATE OR REPLACE FUNCTION factory.complete_alignment(
    p_alignment_run_id uuid,
    p_result jsonb
)
RETURNS TABLE (
    alignment_id uuid,
    scene_timing_count integer,
    lexical_end_ms integer
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.alignment_runs%ROWTYPE;
    v_voiceover factory.voiceovers%ROWTYPE;
    v_job factory.jobs%ROWTYPE;
    v_alignment_id uuid;
    v_expected_alignment_path text;
    v_expected_raw_path text;
    v_model_sha constant text :=
        '60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe';
    v_image_digest constant text :=
        'sha256:9cfbaf11ef5bec57ec9cade6af7ed991ab5e32b01a6e40db3380a12363336e11';
    v_timing jsonb;
    v_scene_id uuid;
    v_start integer;
    v_end integer;
    v_coverage numeric(4,3);
    v_count integer := 0;
    v_expected_scene_count integer;
    v_previous_end integer := 0;
    v_lexical_end integer;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.alignment_runs
     WHERE id=p_alignment_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'alignment run is not active'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_voiceover
      FROM factory.voiceovers
     WHERE id=v_run.voiceover_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'voiceover not found'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_job
      FROM factory.jobs
     WHERE id=v_run.job_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'job not found'
            USING ERRCODE='22023';
    END IF;

    IF COALESCE(p_result->>'status','') <> 'ready'
       OR COALESCE((p_result->>'normalized_match')::boolean,false) <> true
       OR COALESCE((p_result->>'global_coverage')::numeric,0) <> 1.000 THEN
        RAISE EXCEPTION 'alignment result did not pass exact-match gates'
            USING ERRCODE='22023';
    END IF;

    IF lower(COALESCE(p_result->>'audio_sha256','')) <> v_voiceover.audio_sha256
       OR COALESCE((p_result->>'audio_duration_ms')::integer,0) <> v_voiceover.duration_ms THEN
        RAISE EXCEPTION 'alignment audio does not match immutable voiceover'
            USING ERRCODE='22023';
    END IF;

    IF lower(COALESCE(p_result->>'model_sha256','')) <> v_model_sha
       OR COALESCE(p_result->>'whisper_image_digest','') <> v_image_digest THEN
        RAISE EXCEPTION 'alignment runtime/model mismatch'
            USING ERRCODE='22023';
    END IF;

    IF COALESCE(p_result->>'language_code','') <> v_job.language_code THEN
        RAISE EXCEPTION 'alignment language mismatch'
            USING ERRCODE='22023';
    END IF;

    v_expected_alignment_path :=
        '/data/alignments/' || v_run.job_id::text || '/final.json';
    v_expected_raw_path :=
        '/data/alignments/' || v_run.job_id::text || '/whisper.json';

    IF COALESCE(p_result->>'alignment_path','') <> v_expected_alignment_path
       OR COALESCE(p_result->>'raw_whisper_path','') <> v_expected_raw_path THEN
        RAISE EXCEPTION 'unexpected alignment storage path'
            USING ERRCODE='22023';
    END IF;

    IF btrim(COALESCE(p_result->>'transcript','')) = '' THEN
        RAISE EXCEPTION 'alignment transcript is empty'
            USING ERRCODE='22023';
    END IF;

    IF COALESCE((p_result->>'lexical_token_count')::integer,0) <= 0
       OR COALESCE((p_result->>'lexical_start_ms')::integer,-1) < 0 THEN
        RAISE EXCEPTION 'invalid lexical timing metadata'
            USING ERRCODE='22023';
    END IF;

    v_lexical_end := COALESCE((p_result->>'lexical_end_ms')::integer,0);
    IF v_lexical_end <= 0 OR v_lexical_end > v_voiceover.duration_ms THEN
        RAISE EXCEPTION 'invalid lexical end timing'
            USING ERRCODE='22023';
    END IF;

    IF jsonb_typeof(p_result->'scene_timings') <> 'array' THEN
        RAISE EXCEPTION 'scene_timings must be an array'
            USING ERRCODE='22023';
    END IF;

    SELECT count(*)
      INTO v_expected_scene_count
      FROM factory.scenes
     WHERE job_id=v_run.job_id;

    IF jsonb_array_length(p_result->'scene_timings') <> v_expected_scene_count THEN
        RAISE EXCEPTION 'scene timing count mismatch'
            USING ERRCODE='22023';
    END IF;

    INSERT INTO factory.alignments (
        job_id,alignment_run_id,voiceover_id,language_code,
        alignment_path,raw_whisper_path,audio_sha256,audio_duration_ms,
        model_sha256,whisper_image_digest,transcript,normalized_match,
        global_coverage,lexical_token_count,lexical_start_ms,lexical_end_ms
    )
    VALUES (
        v_run.job_id,v_run.id,v_voiceover.id,v_job.language_code,
        v_expected_alignment_path,v_expected_raw_path,v_voiceover.audio_sha256,
        v_voiceover.duration_ms,v_model_sha,v_image_digest,
        btrim(p_result->>'transcript'),true,1.000,
        (p_result->>'lexical_token_count')::integer,
        (p_result->>'lexical_start_ms')::integer,
        v_lexical_end
    )
    RETURNING id INTO v_alignment_id;

    FOR v_timing IN
        SELECT value
        FROM jsonb_array_elements(p_result->'scene_timings')
    LOOP
        v_scene_id := NULLIF(btrim(v_timing->>'scene_uuid'),'')::uuid;
        v_start := NULLIF(v_timing->>'start_ms','')::integer;
        v_end := NULLIF(v_timing->>'end_ms','')::integer;
        v_coverage := NULLIF(v_timing->>'coverage','')::numeric(4,3);

        IF NOT EXISTS (
            SELECT 1
            FROM factory.scenes s
            WHERE s.id=v_scene_id
              AND s.job_id=v_run.job_id
        ) THEN
            RAISE EXCEPTION 'scene timing references a scene outside this job'
                USING ERRCODE='22023';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM factory.scene_timings st
            WHERE st.scene_id=v_scene_id
        ) THEN
            RAISE EXCEPTION 'duplicate scene timing'
                USING ERRCODE='22023';
        END IF;

        IF v_start IS NULL OR v_end IS NULL
           OR v_start < v_previous_end
           OR v_end <= v_start
           OR v_end > v_voiceover.duration_ms
           OR v_coverage <> 1.000 THEN
            RAISE EXCEPTION 'invalid scene timing'
                USING ERRCODE='22023';
        END IF;

        INSERT INTO factory.scene_timings (
            scene_id,alignment_id,job_id,start_ms,end_ms,coverage
        )
        VALUES (
            v_scene_id,v_alignment_id,v_run.job_id,v_start,v_end,v_coverage
        );

        v_previous_end := v_end;
        v_count := v_count + 1;
    END LOOP;

    IF v_count <> v_expected_scene_count THEN
        RAISE EXCEPTION 'scene timing persistence count mismatch'
            USING ERRCODE='22023';
    END IF;

    UPDATE factory.alignment_runs
       SET status='passed',
           completed_at=now(),
           failure_reason=NULL
     WHERE id=v_run.id;

    UPDATE factory.jobs
       SET status='alignment_ready',
           updated_at=now()
     WHERE id=v_run.job_id;

    RETURN QUERY
    SELECT v_alignment_id,v_count,v_lexical_end;
END;
$$;

CREATE OR REPLACE FUNCTION factory.fail_alignment(
    p_alignment_run_id uuid,
    p_reason text
)
RETURNS TABLE (
    alignment_status text,
    job_status text
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.alignment_runs%ROWTYPE;
    v_job_status text;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.alignment_runs
     WHERE id=p_alignment_run_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'alignment run not found'
            USING ERRCODE='22023';
    END IF;

    IF v_run.status='passed' THEN
        RAISE EXCEPTION 'passed alignment run cannot be failed'
            USING ERRCODE='22023';
    END IF;

    IF v_run.status='running' THEN
        UPDATE factory.alignment_runs
           SET status='failed',
               completed_at=now(),
               failure_reason=left(
                   COALESCE(NULLIF(btrim(p_reason),''),'unspecified alignment failure'),
                   4000
               )
         WHERE id=v_run.id;

        UPDATE factory.jobs
           SET status='alignment_failed',
               updated_at=now()
         WHERE id=v_run.job_id;
    END IF;

    SELECT status INTO v_job_status
      FROM factory.jobs
     WHERE id=v_run.job_id;

    RETURN QUERY
    SELECT 'failed'::text,v_job_status;
END;
$$;

-- M7 robustness update: allow bounded Whisper ASR differences while keeping
-- all scene boundaries derived from real Whisper token timestamps.
ALTER TABLE factory.alignments
    DROP CONSTRAINT IF EXISTS alignments_match_true;

ALTER TABLE factory.alignments
    DROP CONSTRAINT IF EXISTS alignments_global_coverage;

ALTER TABLE factory.alignments
    ADD CONSTRAINT alignments_global_coverage
        CHECK (global_coverage BETWEEN 0.950 AND 1.000);

ALTER TABLE factory.alignments
    ADD COLUMN IF NOT EXISTS alignment_method text NOT NULL
        DEFAULT 'whisper_token_sequence_match';

ALTER TABLE factory.alignments
    DROP CONSTRAINT IF EXISTS alignments_method;

ALTER TABLE factory.alignments
    ADD CONSTRAINT alignments_method
        CHECK (alignment_method = 'whisper_token_sequence_match');

ALTER TABLE factory.scene_timings
    DROP CONSTRAINT IF EXISTS scene_timings_coverage;

ALTER TABLE factory.scene_timings
    ADD CONSTRAINT scene_timings_coverage
        CHECK (coverage BETWEEN 0.850 AND 1.000);

CREATE OR REPLACE FUNCTION factory.complete_alignment(
    p_alignment_run_id uuid,
    p_result jsonb
)
RETURNS TABLE (
    alignment_id uuid,
    scene_timing_count integer,
    lexical_end_ms integer
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.alignment_runs%ROWTYPE;
    v_voiceover factory.voiceovers%ROWTYPE;
    v_job factory.jobs%ROWTYPE;
    v_alignment_id uuid;
    v_expected_alignment_path text;
    v_expected_raw_path text;
    v_model_sha constant text :=
        '60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe';
    v_image_digest constant text :=
        'sha256:9cfbaf11ef5bec57ec9cade6af7ed991ab5e32b01a6e40db3380a12363336e11';
    v_alignment_method constant text :=
        'whisper_token_sequence_match';
    v_timing jsonb;
    v_scene_id uuid;
    v_start integer;
    v_end integer;
    v_coverage numeric(4,3);
    v_global_coverage numeric(4,3);
    v_normalized_match boolean;
    v_count integer := 0;
    v_expected_scene_count integer;
    v_previous_end integer := 0;
    v_lexical_end integer;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.alignment_runs
     WHERE id=p_alignment_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'alignment run is not active'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_voiceover
      FROM factory.voiceovers
     WHERE id=v_run.voiceover_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'voiceover not found'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_job
      FROM factory.jobs
     WHERE id=v_run.job_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'job not found'
            USING ERRCODE='22023';
    END IF;

    v_global_coverage :=
        COALESCE((p_result->>'global_coverage')::numeric,0);
    v_normalized_match :=
        COALESCE((p_result->>'normalized_match')::boolean,false);

    IF COALESCE(p_result->>'status','') <> 'ready'
       OR COALESCE(p_result->>'alignment_method','') <> v_alignment_method
       OR v_global_coverage < 0.950
       OR v_global_coverage > 1.000 THEN
        RAISE EXCEPTION 'alignment result did not pass lexical coverage gates'
            USING ERRCODE='22023';
    END IF;

    IF lower(COALESCE(p_result->>'audio_sha256','')) <> v_voiceover.audio_sha256
       OR COALESCE((p_result->>'audio_duration_ms')::integer,0) <> v_voiceover.duration_ms THEN
        RAISE EXCEPTION 'alignment audio does not match immutable voiceover'
            USING ERRCODE='22023';
    END IF;

    IF lower(COALESCE(p_result->>'model_sha256','')) <> v_model_sha
       OR COALESCE(p_result->>'whisper_image_digest','') <> v_image_digest THEN
        RAISE EXCEPTION 'alignment runtime/model mismatch'
            USING ERRCODE='22023';
    END IF;

    IF COALESCE(p_result->>'language_code','') <> v_job.language_code THEN
        RAISE EXCEPTION 'alignment language mismatch'
            USING ERRCODE='22023';
    END IF;

    v_expected_alignment_path :=
        '/data/alignments/' || v_run.job_id::text || '/final.json';
    v_expected_raw_path :=
        '/data/alignments/' || v_run.job_id::text || '/whisper.json';

    IF COALESCE(p_result->>'alignment_path','') <> v_expected_alignment_path
       OR COALESCE(p_result->>'raw_whisper_path','') <> v_expected_raw_path THEN
        RAISE EXCEPTION 'unexpected alignment storage path'
            USING ERRCODE='22023';
    END IF;

    IF btrim(COALESCE(p_result->>'transcript','')) = '' THEN
        RAISE EXCEPTION 'alignment transcript is empty'
            USING ERRCODE='22023';
    END IF;

    IF COALESCE((p_result->>'lexical_token_count')::integer,0) <= 0
       OR COALESCE((p_result->>'lexical_start_ms')::integer,-1) < 0 THEN
        RAISE EXCEPTION 'invalid lexical timing metadata'
            USING ERRCODE='22023';
    END IF;

    v_lexical_end := COALESCE((p_result->>'lexical_end_ms')::integer,0);
    IF v_lexical_end <= 0 OR v_lexical_end > v_voiceover.duration_ms THEN
        RAISE EXCEPTION 'invalid lexical end timing'
            USING ERRCODE='22023';
    END IF;

    IF jsonb_typeof(p_result->'scene_timings') <> 'array' THEN
        RAISE EXCEPTION 'scene_timings must be an array'
            USING ERRCODE='22023';
    END IF;

    SELECT count(*)
      INTO v_expected_scene_count
      FROM factory.scenes
     WHERE job_id=v_run.job_id;

    IF jsonb_array_length(p_result->'scene_timings') <> v_expected_scene_count THEN
        RAISE EXCEPTION 'scene timing count mismatch'
            USING ERRCODE='22023';
    END IF;

    INSERT INTO factory.alignments (
        job_id,alignment_run_id,voiceover_id,language_code,
        alignment_path,raw_whisper_path,audio_sha256,audio_duration_ms,
        model_sha256,whisper_image_digest,transcript,normalized_match,
        global_coverage,alignment_method,lexical_token_count,
        lexical_start_ms,lexical_end_ms
    )
    VALUES (
        v_run.job_id,v_run.id,v_voiceover.id,v_job.language_code,
        v_expected_alignment_path,v_expected_raw_path,v_voiceover.audio_sha256,
        v_voiceover.duration_ms,v_model_sha,v_image_digest,
        btrim(p_result->>'transcript'),v_normalized_match,
        v_global_coverage,v_alignment_method,
        (p_result->>'lexical_token_count')::integer,
        (p_result->>'lexical_start_ms')::integer,
        v_lexical_end
    )
    RETURNING id INTO v_alignment_id;

    FOR v_timing IN
        SELECT value
        FROM jsonb_array_elements(p_result->'scene_timings')
    LOOP
        v_scene_id := NULLIF(btrim(v_timing->>'scene_uuid'),'')::uuid;
        v_start := NULLIF(v_timing->>'start_ms','')::integer;
        v_end := NULLIF(v_timing->>'end_ms','')::integer;
        v_coverage := NULLIF(v_timing->>'coverage','')::numeric(4,3);

        IF NOT EXISTS (
            SELECT 1
            FROM factory.scenes s
            WHERE s.id=v_scene_id
              AND s.job_id=v_run.job_id
        ) THEN
            RAISE EXCEPTION 'scene timing references a scene outside this job'
                USING ERRCODE='22023';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM factory.scene_timings st
            WHERE st.scene_id=v_scene_id
        ) THEN
            RAISE EXCEPTION 'duplicate scene timing'
                USING ERRCODE='22023';
        END IF;

        IF v_start IS NULL OR v_end IS NULL
           OR v_start < v_previous_end
           OR v_end <= v_start
           OR v_end > v_voiceover.duration_ms
           OR v_coverage < 0.850
           OR v_coverage > 1.000 THEN
            RAISE EXCEPTION 'invalid scene timing'
                USING ERRCODE='22023';
        END IF;

        INSERT INTO factory.scene_timings (
            scene_id,alignment_id,job_id,start_ms,end_ms,coverage
        )
        VALUES (
            v_scene_id,v_alignment_id,v_run.job_id,v_start,v_end,v_coverage
        );

        v_previous_end := v_end;
        v_count := v_count + 1;
    END LOOP;

    IF v_count <> v_expected_scene_count THEN
        RAISE EXCEPTION 'scene timing persistence count mismatch'
            USING ERRCODE='22023';
    END IF;

    UPDATE factory.alignment_runs
       SET status='passed',
           completed_at=now(),
           failure_reason=NULL
     WHERE id=v_run.id;

    UPDATE factory.jobs
       SET status='alignment_ready',
           updated_at=now()
     WHERE id=v_run.job_id;

    RETURN QUERY
    SELECT v_alignment_id,v_count,v_lexical_end;
END;
$$;
