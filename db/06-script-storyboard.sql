-- M5 script + storyboard persistence.
-- One evidence-ready job gets one immutable script-generation attempt.
-- The model output is validated before this migration persists it.

CREATE TABLE IF NOT EXISTS factory.script_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL UNIQUE REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    status text NOT NULL DEFAULT 'running',
    model text NOT NULL,
    prompt_token_count integer,
    output_token_count integer,
    total_token_count integer,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    failure_reason text,

    CONSTRAINT script_runs_status
        CHECK (status IN ('running', 'passed', 'failed')),
    CONSTRAINT script_runs_model_nonempty
        CHECK (char_length(btrim(model)) > 0),
    CONSTRAINT script_runs_completion
        CHECK (
            (status = 'running' AND completed_at IS NULL)
            OR
            (status IN ('passed','failed') AND completed_at IS NOT NULL)
        )
);

CREATE TABLE IF NOT EXISTS factory.script_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL UNIQUE REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    script_run_id uuid NOT NULL UNIQUE REFERENCES factory.script_runs(id) ON DELETE RESTRICT,
    model text NOT NULL,
    narration text NOT NULL,
    word_count integer NOT NULL,
    storyboard jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT script_versions_narration_nonempty
        CHECK (char_length(btrim(narration)) > 0),
    CONSTRAINT script_versions_word_count_positive
        CHECK (word_count > 0),
    CONSTRAINT script_versions_storyboard_object
        CHECK (jsonb_typeof(storyboard) = 'object')
);

CREATE TABLE IF NOT EXISTS factory.scenes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    script_version_id uuid NOT NULL REFERENCES factory.script_versions(id) ON DELETE RESTRICT,
    job_id uuid NOT NULL REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    scene_key text NOT NULL,
    scene_order integer NOT NULL,
    narration text NOT NULL,

    CONSTRAINT scenes_key_nonempty CHECK (char_length(btrim(scene_key)) > 0),
    CONSTRAINT scenes_order_positive CHECK (scene_order >= 1),
    CONSTRAINT scenes_narration_nonempty CHECK (char_length(btrim(narration)) > 0),
    UNIQUE (script_version_id, scene_key),
    UNIQUE (script_version_id, scene_order)
);

CREATE TABLE IF NOT EXISTS factory.scene_evidence (
    scene_id uuid NOT NULL REFERENCES factory.scenes(id) ON DELETE RESTRICT,
    evidence_id uuid NOT NULL REFERENCES factory.evidence(id) ON DELETE RESTRICT,
    PRIMARY KEY (scene_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS factory.shots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    scene_id uuid NOT NULL REFERENCES factory.scenes(id) ON DELETE RESTRICT,
    job_id uuid NOT NULL REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    shot_key text NOT NULL,
    shot_order integer NOT NULL,
    visual_intent text NOT NULL,
    must_show jsonb NOT NULL,
    must_not_show jsonb NOT NULL,
    queries_en jsonb NOT NULL,
    preferred_media_type text NOT NULL,

    CONSTRAINT shots_key_nonempty CHECK (char_length(btrim(shot_key)) > 0),
    CONSTRAINT shots_order_positive CHECK (shot_order >= 1),
    CONSTRAINT shots_visual_intent_nonempty CHECK (char_length(btrim(visual_intent)) > 0),
    CONSTRAINT shots_must_show_array CHECK (jsonb_typeof(must_show) = 'array'),
    CONSTRAINT shots_must_not_show_array CHECK (jsonb_typeof(must_not_show) = 'array'),
    CONSTRAINT shots_queries_array CHECK (jsonb_typeof(queries_en) = 'array'),
    CONSTRAINT shots_media_type CHECK (
        preferred_media_type IN ('photo','video','diagram','map','document')
    ),
    UNIQUE (scene_id, shot_key),
    UNIQUE (scene_id, shot_order)
);

CREATE INDEX IF NOT EXISTS scenes_job_order_idx
    ON factory.scenes (job_id, scene_order);

CREATE INDEX IF NOT EXISTS shots_job_idx
    ON factory.shots (job_id);

CREATE INDEX IF NOT EXISTS scene_evidence_evidence_idx
    ON factory.scene_evidence (evidence_id);

CREATE OR REPLACE FUNCTION factory.begin_script(
    p_job_id uuid,
    p_model text
)
RETURNS TABLE (
    script_run_id uuid,
    topic text,
    language_code text,
    target_duration_seconds integer,
    evidence_json jsonb
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_job factory.jobs%ROWTYPE;
    v_run_id uuid;
    v_evidence jsonb;
    v_evidence_count integer;
    v_domain_count integer;
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

    IF v_job.status <> 'evidence_ready' THEN
        RAISE EXCEPTION 'job is not scriptable from status %', v_job.status
            USING ERRCODE = '22023';
    END IF;

    IF p_model IS NULL OR char_length(btrim(p_model)) = 0 THEN
        RAISE EXCEPTION 'model is required'
            USING ERRCODE = '22023';
    END IF;

    SELECT count(*), count(DISTINCT source_domain)
      INTO v_evidence_count, v_domain_count
      FROM factory.evidence
     WHERE job_id = p_job_id;

    IF v_evidence_count < 3 OR v_domain_count < 3 THEN
        RAISE EXCEPTION 'job does not have sufficient persisted evidence'
            USING ERRCODE = '22023';
    END IF;

    SELECT jsonb_agg(
               jsonb_build_object(
                   'evidence_ref', 'E' || ranked.rn,
                   'evidence_uuid', ranked.id::text,
                   'source_domain', ranked.source_domain,
                   'title', ranked.title,
                   'source_url', ranked.canonical_url,
                   'snippet', ranked.snippet,
                   'content', left(ranked.content_text, 6000)
               )
               ORDER BY ranked.rn
           )
      INTO v_evidence
      FROM (
          SELECT e.*,
                 row_number() OVER (
                     ORDER BY e.search_rank, e.retrieved_at, e.id
                 ) AS rn
          FROM factory.evidence e
          WHERE e.job_id = p_job_id
      ) ranked;

    INSERT INTO factory.script_runs (job_id, status, model)
    VALUES (p_job_id, 'running', btrim(p_model))
    RETURNING id INTO v_run_id;

    UPDATE factory.jobs
       SET status = 'scripting',
           updated_at = now()
     WHERE id = p_job_id;

    RETURN QUERY
    SELECT
        v_run_id,
        v_job.topic,
        v_job.language_code,
        v_job.target_duration_seconds,
        v_evidence;
END;
$$;

CREATE OR REPLACE FUNCTION factory.commit_storyboard(
    p_script_run_id uuid,
    p_model text,
    p_storyboard jsonb,
    p_usage jsonb DEFAULT '{}'::jsonb
)
RETURNS TABLE (
    script_version_id uuid,
    scene_count integer,
    shot_count integer,
    narration_word_count integer
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.script_runs%ROWTYPE;
    v_version_id uuid;
    v_narration text;
    v_word_count integer;
    v_scene jsonb;
    v_scene_order integer;
    v_scene_id uuid;
    v_evidence_value jsonb;
    v_evidence_id uuid;
    v_shot jsonb;
    v_shot_order integer;
    v_scene_count integer := 0;
    v_shot_count integer := 0;
    v_prompt_tokens integer;
    v_output_tokens integer;
    v_total_tokens integer;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.script_runs
     WHERE id = p_script_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'script run is not active'
            USING ERRCODE = '22023';
    END IF;

    IF p_model IS NULL OR btrim(p_model) <> v_run.model THEN
        RAISE EXCEPTION 'script model mismatch'
            USING ERRCODE = '22023';
    END IF;

    IF jsonb_typeof(p_storyboard) <> 'object'
       OR jsonb_typeof(p_storyboard->'scenes') <> 'array' THEN
        RAISE EXCEPTION 'storyboard must be an object with scenes array'
            USING ERRCODE = '22023';
    END IF;

    v_narration := btrim(COALESCE(p_storyboard->>'narration', ''));
    IF v_narration = '' THEN
        RAISE EXCEPTION 'storyboard narration is empty'
            USING ERRCODE = '22023';
    END IF;

    v_word_count := cardinality(
        regexp_split_to_array(v_narration, '[[:space:]]+')
    );

    INSERT INTO factory.script_versions (
        job_id,
        script_run_id,
        model,
        narration,
        word_count,
        storyboard
    )
    VALUES (
        v_run.job_id,
        v_run.id,
        v_run.model,
        v_narration,
        v_word_count,
        p_storyboard
    )
    RETURNING id INTO v_version_id;

    FOR v_scene, v_scene_order IN
        SELECT value, ordinality::integer
        FROM jsonb_array_elements(p_storyboard->'scenes')
             WITH ORDINALITY
    LOOP
        IF jsonb_typeof(v_scene) <> 'object'
           OR jsonb_typeof(v_scene->'evidence_uuids') <> 'array'
           OR jsonb_typeof(v_scene->'shots') <> 'array' THEN
            RAISE EXCEPTION 'invalid scene structure'
                USING ERRCODE = '22023';
        END IF;

        INSERT INTO factory.scenes (
            script_version_id,
            job_id,
            scene_key,
            scene_order,
            narration
        )
        VALUES (
            v_version_id,
            v_run.job_id,
            btrim(v_scene->>'scene_id'),
            v_scene_order,
            btrim(v_scene->>'narration')
        )
        RETURNING id INTO v_scene_id;

        FOR v_evidence_value IN
            SELECT value
            FROM jsonb_array_elements(v_scene->'evidence_uuids')
        LOOP
            v_evidence_id := trim(both '"' from v_evidence_value::text)::uuid;

            IF NOT EXISTS (
                SELECT 1
                FROM factory.evidence e
                WHERE e.id = v_evidence_id
                  AND e.job_id = v_run.job_id
            ) THEN
                RAISE EXCEPTION 'scene references evidence outside this job'
                    USING ERRCODE = '22023';
            END IF;

            INSERT INTO factory.scene_evidence (scene_id, evidence_id)
            VALUES (v_scene_id, v_evidence_id);
        END LOOP;

        FOR v_shot, v_shot_order IN
            SELECT value, ordinality::integer
            FROM jsonb_array_elements(v_scene->'shots')
                 WITH ORDINALITY
        LOOP
            INSERT INTO factory.shots (
                scene_id,
                job_id,
                shot_key,
                shot_order,
                visual_intent,
                must_show,
                must_not_show,
                queries_en,
                preferred_media_type
            )
            VALUES (
                v_scene_id,
                v_run.job_id,
                btrim(v_shot->>'shot_id'),
                v_shot_order,
                btrim(v_shot->>'visual_intent'),
                v_shot->'must_show',
                v_shot->'must_not_show',
                v_shot->'queries_en',
                btrim(v_shot->>'preferred_media_type')
            );

            v_shot_count := v_shot_count + 1;
        END LOOP;

        v_scene_count := v_scene_count + 1;
    END LOOP;

    IF v_scene_count = 0 OR v_shot_count = 0 THEN
        RAISE EXCEPTION 'storyboard must contain scenes and shots'
            USING ERRCODE = '22023';
    END IF;

    v_prompt_tokens := NULLIF(p_usage->>'promptTokenCount', '')::integer;
    v_output_tokens := NULLIF(p_usage->>'candidatesTokenCount', '')::integer;
    v_total_tokens := NULLIF(p_usage->>'totalTokenCount', '')::integer;

    UPDATE factory.script_runs
       SET status = 'passed',
           prompt_token_count = v_prompt_tokens,
           output_token_count = v_output_tokens,
           total_token_count = v_total_tokens,
           completed_at = now(),
           failure_reason = NULL
     WHERE id = v_run.id;

    UPDATE factory.jobs
       SET status = 'storyboard_ready',
           updated_at = now()
     WHERE id = v_run.job_id;

    RETURN QUERY
    SELECT v_version_id, v_scene_count, v_shot_count, v_word_count;
END;
$$;

CREATE OR REPLACE FUNCTION factory.fail_script(
    p_script_run_id uuid,
    p_reason text
)
RETURNS TABLE (
    script_status text,
    job_status text
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.script_runs%ROWTYPE;
    v_job_status text;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.script_runs
     WHERE id = p_script_run_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'script run not found'
            USING ERRCODE = '22023';
    END IF;

    IF v_run.status = 'passed' THEN
        RAISE EXCEPTION 'passed script run cannot be failed'
            USING ERRCODE = '22023';
    END IF;

    IF v_run.status = 'running' THEN
        UPDATE factory.script_runs
           SET status = 'failed',
               completed_at = now(),
               failure_reason = left(
                   COALESCE(NULLIF(btrim(p_reason), ''), 'unspecified script failure'),
                   4000
               )
         WHERE id = p_script_run_id;

        UPDATE factory.jobs
           SET status = 'script_failed',
               updated_at = now()
         WHERE id = v_run.job_id;
    END IF;

    SELECT status INTO v_job_status
      FROM factory.jobs
     WHERE id = v_run.job_id;

    RETURN QUERY
    SELECT 'failed'::text, v_job_status;
END;
$$;
