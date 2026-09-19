-- M9 deterministic render + machine QA persistence.
-- One immutable render attempt per normal product job.
-- Inputs are the exact M6 voiceover, M7 scene timings and M8 local assets.

CREATE TABLE IF NOT EXISTS factory.render_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL UNIQUE REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    status text NOT NULL DEFAULT 'running',
    expected_scene_count integer NOT NULL CHECK (expected_scene_count > 0),
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    failure_reason text,

    CONSTRAINT render_runs_status
        CHECK (status IN ('running','passed','failed')),
    CONSTRAINT render_runs_completion
        CHECK (
            (status='running' AND completed_at IS NULL)
            OR
            (status IN ('passed','failed') AND completed_at IS NOT NULL)
        )
);

CREATE TABLE IF NOT EXISTS factory.renders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL UNIQUE REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    render_run_id uuid NOT NULL UNIQUE REFERENCES factory.render_runs(id) ON DELETE RESTRICT,
    storage_path text NOT NULL UNIQUE,
    manifest_path text NOT NULL UNIQUE,
    sha256 text NOT NULL,
    bytes bigint NOT NULL CHECK (bytes > 0),
    width integer NOT NULL CHECK (width = 1080),
    height integer NOT NULL CHECK (height = 1920),
    video_codec text NOT NULL CHECK (video_codec = 'h264'),
    audio_codec text NOT NULL CHECK (audio_codec = 'aac'),
    pix_fmt text NOT NULL CHECK (pix_fmt = 'yuv420p'),
    fps_num integer NOT NULL CHECK (fps_num = 30),
    fps_den integer NOT NULL CHECK (fps_den = 1),
    duration_ms integer NOT NULL CHECK (duration_ms > 0),
    audio_duration_ms integer NOT NULL CHECK (audio_duration_ms > 0),
    duration_delta_ms integer NOT NULL CHECK (duration_delta_ms BETWEEN 0 AND 100),
    video_stream_count integer NOT NULL CHECK (video_stream_count = 1),
    audio_stream_count integer NOT NULL CHECK (audio_stream_count = 1),
    input_audio_sha256 text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT renders_sha CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT renders_input_audio_sha CHECK (input_audio_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE TABLE IF NOT EXISTS factory.render_segments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    render_id uuid NOT NULL REFERENCES factory.renders(id) ON DELETE RESTRICT,
    job_id uuid NOT NULL REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    scene_id uuid NOT NULL UNIQUE REFERENCES factory.scenes(id) ON DELETE RESTRICT,
    shot_id uuid NOT NULL UNIQUE REFERENCES factory.shots(id) ON DELETE RESTRICT,
    visual_asset_id uuid NOT NULL UNIQUE REFERENCES factory.visual_assets(id) ON DELETE RESTRICT,
    segment_order integer NOT NULL CHECK (segment_order >= 1),
    start_ms integer NOT NULL CHECK (start_ms >= 0),
    end_ms integer NOT NULL,
    duration_ms integer NOT NULL CHECK (duration_ms > 0),
    asset_sha256 text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT render_segments_end CHECK (end_ms > start_ms),
    CONSTRAINT render_segments_sha CHECK (asset_sha256 ~ '^[0-9a-f]{64}$'),
    UNIQUE (render_id, segment_order)
);

CREATE TABLE IF NOT EXISTS factory.machine_qa (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL UNIQUE REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    render_id uuid NOT NULL UNIQUE REFERENCES factory.renders(id) ON DELETE RESTRICT,
    passed boolean NOT NULL,
    gates jsonb NOT NULL,
    verified_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT machine_qa_passed CHECK (passed = true),
    CONSTRAINT machine_qa_gates_object CHECK (jsonb_typeof(gates)='object')
);

CREATE OR REPLACE FUNCTION factory.begin_render(
    p_job_id uuid
)
RETURNS TABLE (
    render_run_id uuid,
    voiceover_path text,
    audio_sha256 text,
    audio_duration_ms integer,
    expected_scene_count integer,
    scenes_json jsonb
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_job factory.jobs%ROWTYPE;
    v_voice factory.voiceovers%ROWTYPE;
    v_run_id uuid;
    v_scene_count integer;
    v_asset_count integer;
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

    IF v_job.status <> 'visuals_ready' THEN
        RAISE EXCEPTION 'job is not render-ready from status %',v_job.status
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_voice
      FROM factory.voiceovers
     WHERE job_id=p_job_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'voiceover not found'
            USING ERRCODE='22023';
    END IF;

    SELECT count(*)::integer
      INTO v_scene_count
      FROM factory.scenes
     WHERE job_id=p_job_id;

    SELECT count(*)::integer
      INTO v_asset_count
      FROM factory.visual_assets
     WHERE job_id=p_job_id;

    IF v_scene_count <= 0 OR v_asset_count <> v_scene_count THEN
        RAISE EXCEPTION 'render inputs are incomplete: scenes %, assets %',
            v_scene_count,v_asset_count
            USING ERRCODE='22023';
    END IF;

    WITH ordered AS (
        SELECT
            sc.scene_order,
            sc.id AS scene_id,
            sc.scene_key,
            sh.id AS shot_id,
            sh.shot_key,
            st.start_ms AS speech_start_ms,
            st.end_ms AS speech_end_ms,
            CASE
                WHEN sc.scene_order=1 THEN 0
                ELSE st.start_ms
            END AS segment_start_ms,
            COALESCE(
                lead(st.start_ms) OVER (ORDER BY sc.scene_order,sh.shot_order),
                v_voice.duration_ms
            ) AS segment_end_ms,
            va.id AS visual_asset_id,
            va.storage_path AS asset_path,
            va.sha256 AS asset_sha256,
            va.media_type,
            va.width AS asset_width,
            va.height AS asset_height,
            va.duration_ms AS asset_duration_ms
        FROM factory.scenes sc
        JOIN factory.scene_timings st ON st.scene_id=sc.id
        JOIN factory.shots sh ON sh.scene_id=sc.id
        JOIN factory.visual_assets va ON va.shot_id=sh.id
        WHERE sc.job_id=p_job_id
    )
    SELECT jsonb_agg(
               jsonb_build_object(
                   'scene_uuid',scene_id::text,
                   'scene_key',scene_key,
                   'shot_uuid',shot_id::text,
                   'shot_key',shot_key,
                   'scene_order',scene_order,
                   'speech_start_ms',speech_start_ms,
                   'speech_end_ms',speech_end_ms,
                   'segment_start_ms',segment_start_ms,
                   'segment_end_ms',segment_end_ms,
                   'visual_asset_id',visual_asset_id::text,
                   'asset_path',asset_path,
                   'asset_sha256',asset_sha256,
                   'media_type',media_type,
                   'asset_width',asset_width,
                   'asset_height',asset_height,
                   'asset_duration_ms',asset_duration_ms
               )
               ORDER BY scene_order
           )
      INTO v_scenes
      FROM ordered;

    IF v_scenes IS NULL
       OR jsonb_array_length(v_scenes) <> v_scene_count THEN
        RAISE EXCEPTION 'render scene manifest could not be built'
            USING ERRCODE='22023';
    END IF;

    IF EXISTS (
        WITH ordered AS (
            SELECT
                sc.scene_order,
                st.start_ms,
                st.end_ms,
                CASE WHEN sc.scene_order=1 THEN 0 ELSE st.start_ms END AS seg_start,
                COALESCE(
                    lead(st.start_ms) OVER (ORDER BY sc.scene_order,sh.shot_order),
                    v_voice.duration_ms
                ) AS seg_end
            FROM factory.scenes sc
            JOIN factory.scene_timings st ON st.scene_id=sc.id
            JOIN factory.shots sh ON sh.scene_id=sc.id
            WHERE sc.job_id=p_job_id
        )
        SELECT 1
        FROM ordered
        WHERE seg_start < 0
           OR seg_end <= seg_start
           OR start_ms < seg_start
           OR end_ms > seg_end
           OR seg_end > v_voice.duration_ms
    ) THEN
        RAISE EXCEPTION 'render segment timing coverage is invalid'
            USING ERRCODE='22023';
    END IF;

    INSERT INTO factory.render_runs (
        job_id,status,expected_scene_count
    )
    VALUES (
        p_job_id,'running',v_scene_count
    )
    RETURNING id INTO v_run_id;

    UPDATE factory.jobs
       SET status='rendering',
           updated_at=now()
     WHERE id=p_job_id;

    RETURN QUERY
    SELECT
        v_run_id,
        v_voice.storage_path,
        v_voice.audio_sha256,
        v_voice.duration_ms,
        v_scene_count,
        v_scenes;
END;
$$;

CREATE OR REPLACE FUNCTION factory.complete_render(
    p_render_run_id uuid,
    p_result jsonb
)
RETURNS TABLE (
    render_id uuid,
    render_sha256 text,
    render_duration_ms integer,
    machine_qa_passed boolean
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.render_runs%ROWTYPE;
    v_voice factory.voiceovers%ROWTYPE;
    v_render_id uuid;
    v_expected_render_path text;
    v_expected_manifest_path text;
    v_duration_ms integer;
    v_delta integer;
    v_segment jsonb;
    v_scene_id uuid;
    v_shot_id uuid;
    v_asset_id uuid;
    v_order integer;
    v_start integer;
    v_end integer;
    v_asset_sha text;
    v_expected_start integer;
    v_expected_end integer;
    v_expected_order integer;
    v_expected_sha text;
    v_count integer := 0;
    v_previous_end integer := 0;
    v_gates jsonb;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.render_runs
     WHERE id=p_render_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'render run is not active'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_voice
      FROM factory.voiceovers
     WHERE job_id=v_run.job_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'voiceover not found'
            USING ERRCODE='22023';
    END IF;

    v_expected_render_path :=
        '/data/renders/' || v_run.job_id::text || '/final.mp4';
    v_expected_manifest_path :=
        '/data/renders/' || v_run.job_id::text || '/manifest.json';

    v_duration_ms := COALESCE((p_result->>'duration_ms')::integer,0);
    v_delta := abs(v_duration_ms - v_voice.duration_ms);
    v_gates := COALESCE(p_result->'qa_gates','{}'::jsonb);

    IF COALESCE(p_result->>'status','') <> 'ready'
       OR COALESCE((p_result->>'qa_passed')::boolean,false) <> true
       OR COALESCE(p_result->>'storage_path','') <> v_expected_render_path
       OR COALESCE(p_result->>'manifest_path','') <> v_expected_manifest_path
       OR lower(COALESCE(p_result->>'input_audio_sha256','')) <> v_voice.audio_sha256
       OR lower(COALESCE(p_result->>'sha256','')) !~ '^[0-9a-f]{64}$'
       OR COALESCE((p_result->>'bytes')::bigint,0) <= 0
       OR COALESCE((p_result->>'width')::integer,0) <> 1080
       OR COALESCE((p_result->>'height')::integer,0) <> 1920
       OR lower(COALESCE(p_result->>'video_codec','')) <> 'h264'
       OR lower(COALESCE(p_result->>'audio_codec','')) <> 'aac'
       OR lower(COALESCE(p_result->>'pix_fmt','')) <> 'yuv420p'
       OR COALESCE((p_result->>'fps_num')::integer,0) <> 30
       OR COALESCE((p_result->>'fps_den')::integer,0) <> 1
       OR COALESCE((p_result->>'video_stream_count')::integer,0) <> 1
       OR COALESCE((p_result->>'audio_stream_count')::integer,0) <> 1
       OR v_duration_ms <= 0
       OR v_delta > 100 THEN
        RAISE EXCEPTION 'render metadata or machine QA failed'
            USING ERRCODE='22023';
    END IF;

    IF NOT (
        COALESCE((v_gates->>'video_dimensions')::boolean,false)
        AND COALESCE((v_gates->>'video_codec')::boolean,false)
        AND COALESCE((v_gates->>'audio_codec')::boolean,false)
        AND COALESCE((v_gates->>'stream_counts')::boolean,false)
        AND COALESCE((v_gates->>'duration_match')::boolean,false)
        AND COALESCE((v_gates->>'scene_coverage')::boolean,false)
        AND COALESCE((v_gates->>'asset_hashes')::boolean,false)
        AND COALESCE((v_gates->>'source_audio_excluded')::boolean,false)
    ) THEN
        RAISE EXCEPTION 'one or more machine QA gates are false'
            USING ERRCODE='22023';
    END IF;

    IF jsonb_typeof(p_result->'segments') <> 'array'
       OR jsonb_array_length(p_result->'segments') <> v_run.expected_scene_count THEN
        RAISE EXCEPTION 'render segment count mismatch'
            USING ERRCODE='22023';
    END IF;

    INSERT INTO factory.renders (
        job_id,render_run_id,storage_path,manifest_path,
        sha256,bytes,width,height,video_codec,audio_codec,pix_fmt,
        fps_num,fps_den,duration_ms,audio_duration_ms,duration_delta_ms,
        video_stream_count,audio_stream_count,input_audio_sha256
    )
    VALUES (
        v_run.job_id,v_run.id,v_expected_render_path,v_expected_manifest_path,
        lower(p_result->>'sha256'),(p_result->>'bytes')::bigint,
        1080,1920,'h264','aac','yuv420p',30,1,
        v_duration_ms,v_voice.duration_ms,v_delta,1,1,v_voice.audio_sha256
    )
    RETURNING id INTO v_render_id;

    FOR v_segment IN
        SELECT value
        FROM jsonb_array_elements(p_result->'segments')
    LOOP
        v_scene_id := NULLIF(v_segment->>'scene_uuid','')::uuid;
        v_shot_id := NULLIF(v_segment->>'shot_uuid','')::uuid;
        v_asset_id := NULLIF(v_segment->>'visual_asset_id','')::uuid;
        v_order := NULLIF(v_segment->>'segment_order','')::integer;
        v_start := NULLIF(v_segment->>'start_ms','')::integer;
        v_end := NULLIF(v_segment->>'end_ms','')::integer;
        v_asset_sha := lower(btrim(COALESCE(v_segment->>'asset_sha256','')));

        WITH ordered AS (
            SELECT
                sc.id AS scene_id,
                sh.id AS shot_id,
                va.id AS visual_asset_id,
                sc.scene_order,
                CASE
                    WHEN sc.scene_order=1 THEN 0
                    ELSE st.start_ms
                END AS expected_start,
                COALESCE(
                    lead(st.start_ms) OVER (
                        ORDER BY sc.scene_order,sh.shot_order
                    ),
                    v_voice.duration_ms
                ) AS expected_end,
                va.sha256 AS expected_sha
            FROM factory.scenes sc
            JOIN factory.scene_timings st ON st.scene_id=sc.id
            JOIN factory.shots sh ON sh.scene_id=sc.id
            JOIN factory.visual_assets va ON va.shot_id=sh.id
            WHERE sc.job_id=v_run.job_id
        )
        SELECT expected_start,expected_end,scene_order,expected_sha
          INTO v_expected_start,v_expected_end,v_expected_order,v_expected_sha
          FROM ordered
         WHERE scene_id=v_scene_id
           AND shot_id=v_shot_id
           AND visual_asset_id=v_asset_id;

        IF NOT FOUND
           OR v_order <> v_expected_order
           OR v_start <> v_expected_start
           OR v_end <> v_expected_end
           OR v_end <= v_start
           OR v_start <> v_previous_end
           OR v_asset_sha <> v_expected_sha THEN
            RAISE EXCEPTION 'render segment provenance/timing mismatch'
                USING ERRCODE='22023';
        END IF;

        INSERT INTO factory.render_segments (
            render_id,job_id,scene_id,shot_id,visual_asset_id,
            segment_order,start_ms,end_ms,duration_ms,asset_sha256
        )
        VALUES (
            v_render_id,v_run.job_id,v_scene_id,v_shot_id,v_asset_id,
            v_order,v_start,v_end,v_end-v_start,v_asset_sha
        );

        v_previous_end := v_end;
        v_count := v_count + 1;
    END LOOP;

    IF v_count <> v_run.expected_scene_count
       OR v_previous_end <> v_voice.duration_ms THEN
        RAISE EXCEPTION 'render segment coverage incomplete'
            USING ERRCODE='22023';
    END IF;

    INSERT INTO factory.machine_qa (
        job_id,render_id,passed,gates
    )
    VALUES (
        v_run.job_id,v_render_id,true,v_gates
    );

    UPDATE factory.render_runs
       SET status='passed',
           completed_at=now(),
           failure_reason=NULL
     WHERE id=v_run.id;

    UPDATE factory.jobs
       SET status='machine_qa_passed',
           updated_at=now()
     WHERE id=v_run.job_id;

    RETURN QUERY
    SELECT v_render_id,lower(p_result->>'sha256'),v_duration_ms,true;
END;
$$;

CREATE OR REPLACE FUNCTION factory.fail_render(
    p_render_run_id uuid,
    p_reason text
)
RETURNS TABLE (
    render_status text,
    job_status text
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.render_runs%ROWTYPE;
    v_job_status text;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.render_runs
     WHERE id=p_render_run_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'render run not found'
            USING ERRCODE='22023';
    END IF;

    IF v_run.status='passed' THEN
        RAISE EXCEPTION 'passed render run cannot be failed'
            USING ERRCODE='22023';
    END IF;

    IF v_run.status='running' THEN
        UPDATE factory.render_runs
           SET status='failed',
               completed_at=now(),
               failure_reason=left(
                   COALESCE(NULLIF(btrim(p_reason),''),'unspecified render failure'),
                   4000
               )
         WHERE id=v_run.id;

        UPDATE factory.jobs
           SET status='render_failed',
               updated_at=now()
         WHERE id=v_run.job_id;
    END IF;

    SELECT status INTO v_job_status
      FROM factory.jobs
     WHERE id=v_run.job_id;

    RETURN QUERY SELECT 'failed'::text,v_job_status;
END;
$$;
