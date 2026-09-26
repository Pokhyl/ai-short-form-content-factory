-- M8 multi-source visual search, deterministic selection and local asset persistence.
-- Search providers: Pixabay, Pexels and Wikimedia Commons. Diagram shots also receive a deterministic local 9:16 diagram candidate.
-- Every storyboard query is executed against every enabled provider.
-- Selection is deterministic, license-aware, relevance-gated and non-reusing.

CREATE TABLE IF NOT EXISTS factory.visual_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL UNIQUE REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    alignment_id uuid NOT NULL UNIQUE REFERENCES factory.alignments(id) ON DELETE RESTRICT,
    status text NOT NULL DEFAULT 'running',
    expected_shot_count integer NOT NULL CHECK (expected_shot_count > 0),
    expected_search_count integer NOT NULL CHECK (expected_search_count > 0),
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    failure_reason text,

    CONSTRAINT visual_runs_status
        CHECK (status IN ('running','passed','failed')),
    CONSTRAINT visual_runs_completion
        CHECK (
            (status='running' AND completed_at IS NULL)
            OR
            (status IN ('passed','failed') AND completed_at IS NOT NULL)
        )
);

CREATE TABLE IF NOT EXISTS factory.visual_searches (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    visual_run_id uuid NOT NULL REFERENCES factory.visual_runs(id) ON DELETE RESTRICT,
    job_id uuid NOT NULL REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    shot_id uuid NOT NULL REFERENCES factory.shots(id) ON DELETE RESTRICT,
    provider text NOT NULL,
    query_index integer NOT NULL,
    query_text text NOT NULL,
    provider_query_text text NOT NULL,
    endpoint_kind text NOT NULL,
    http_status integer NOT NULL,
    result_count integer NOT NULL CHECK (result_count >= 0),
    response_headers jsonb NOT NULL DEFAULT '{}'::jsonb,
    fetched_at timestamptz NOT NULL DEFAULT now(),
    cache_expires_at timestamptz NOT NULL,

    CONSTRAINT visual_search_provider
        CHECK (provider IN ('pixabay','pexels','wikimedia')),
    CONSTRAINT visual_search_query_index CHECK (query_index >= 1),
    CONSTRAINT visual_search_query_nonempty CHECK (char_length(btrim(query_text)) > 0),
    CONSTRAINT visual_search_provider_query_nonempty CHECK (char_length(btrim(provider_query_text)) > 0),
    CONSTRAINT visual_search_endpoint CHECK (endpoint_kind IN ('photo','video')),
    CONSTRAINT visual_search_http_status CHECK (http_status BETWEEN 100 AND 599),
    UNIQUE (visual_run_id, shot_id, provider, query_index)
);

ALTER TABLE factory.visual_searches
    ADD COLUMN IF NOT EXISTS provider_query_text text;

UPDATE factory.visual_searches
   SET provider_query_text=query_text
 WHERE provider_query_text IS NULL;

ALTER TABLE factory.visual_searches
    ALTER COLUMN provider_query_text SET NOT NULL;

ALTER TABLE factory.visual_searches
    DROP CONSTRAINT IF EXISTS visual_search_provider_query_nonempty;
ALTER TABLE factory.visual_searches
    ADD CONSTRAINT visual_search_provider_query_nonempty
    CHECK (char_length(btrim(provider_query_text)) > 0);

ALTER TABLE factory.visual_searches
    DROP CONSTRAINT IF EXISTS visual_search_http_ok;
ALTER TABLE factory.visual_searches
    DROP CONSTRAINT IF EXISTS visual_search_http_status;
ALTER TABLE factory.visual_searches
    ADD CONSTRAINT visual_search_http_status
    CHECK (http_status BETWEEN 100 AND 599);

CREATE TABLE IF NOT EXISTS factory.visual_candidates (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    visual_run_id uuid NOT NULL REFERENCES factory.visual_runs(id) ON DELETE RESTRICT,
    search_id uuid NOT NULL REFERENCES factory.visual_searches(id) ON DELETE RESTRICT,
    job_id uuid NOT NULL REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    shot_id uuid NOT NULL REFERENCES factory.shots(id) ON DELETE RESTRICT,
    provider text NOT NULL,
    provider_asset_id text NOT NULL,
    provider_rank integer NOT NULL CHECK (provider_rank >= 1),
    media_type text NOT NULL,
    source_url text NOT NULL,
    download_url text NOT NULL,
    preview_url text,
    author text,
    author_url text,
    license_name text NOT NULL,
    license_url text NOT NULL,
    width integer NOT NULL CHECK (width > 0),
    height integer NOT NULL CHECK (height > 0),
    duration_ms integer,
    metadata_text text NOT NULL DEFAULT '',
    query_text text NOT NULL,
    relevance_score integer NOT NULL,
    rejected boolean NOT NULL DEFAULT false,
    rejection_reason text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT visual_candidate_provider
        CHECK (provider IN ('pixabay','pexels','wikimedia')),
    CONSTRAINT visual_candidate_asset_nonempty
        CHECK (char_length(btrim(provider_asset_id)) > 0),
    CONSTRAINT visual_candidate_media_type
        CHECK (media_type IN ('photo','video','diagram')),
    CONSTRAINT visual_candidate_source_https
        CHECK (source_url ~ '^https://'),
    CONSTRAINT visual_candidate_download_https
        CHECK (download_url ~ '^https://'),
    CONSTRAINT visual_candidate_license_nonempty
        CHECK (
            char_length(btrim(license_name)) > 0
            AND char_length(btrim(license_url)) > 0
        ),
    CONSTRAINT visual_candidate_duration
        CHECK (
            (media_type <> 'video' AND (duration_ms IS NULL OR duration_ms >= 0))
            OR
            (media_type = 'video' AND duration_ms IS NOT NULL AND duration_ms > 0)
        ),
    CONSTRAINT visual_candidate_relevance CHECK (relevance_score BETWEEN 0 AND 1000),
    UNIQUE (search_id, provider_asset_id)
);

CREATE INDEX IF NOT EXISTS visual_candidates_shot_rank_idx
    ON factory.visual_candidates (
        visual_run_id,
        shot_id,
        rejected,
        relevance_score DESC,
        provider_rank
    );

CREATE UNIQUE INDEX IF NOT EXISTS visual_candidates_local_diagram_unique
    ON factory.visual_candidates (visual_run_id,shot_id)
    WHERE provider='local_diagram';

CREATE TABLE IF NOT EXISTS factory.visual_selections (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    visual_run_id uuid NOT NULL REFERENCES factory.visual_runs(id) ON DELETE RESTRICT,
    job_id uuid NOT NULL REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    shot_id uuid NOT NULL UNIQUE REFERENCES factory.shots(id) ON DELETE RESTRICT,
    candidate_id uuid NOT NULL UNIQUE REFERENCES factory.visual_candidates(id) ON DELETE RESTRICT,
    provider text NOT NULL,
    provider_asset_id text NOT NULL,
    validation_mode text NOT NULL DEFAULT 'metadata',
    validation_evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
    selected_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT visual_selection_provider
        CHECK (provider IN ('pixabay','pexels','wikimedia')),
    CONSTRAINT visual_selection_validation_mode
        CHECK (validation_mode IN ('metadata','gemini')),
    UNIQUE (visual_run_id, provider, provider_asset_id)
);

ALTER TABLE factory.visual_selections
    ADD COLUMN IF NOT EXISTS validation_mode text;
ALTER TABLE factory.visual_selections
    ADD COLUMN IF NOT EXISTS validation_evidence jsonb;

UPDATE factory.visual_selections
   SET validation_mode='metadata'
 WHERE validation_mode IS NULL;
UPDATE factory.visual_selections
   SET validation_evidence='{}'::jsonb
 WHERE validation_evidence IS NULL;

ALTER TABLE factory.visual_selections
    ALTER COLUMN validation_mode SET DEFAULT 'metadata',
    ALTER COLUMN validation_mode SET NOT NULL,
    ALTER COLUMN validation_evidence SET DEFAULT '{}'::jsonb,
    ALTER COLUMN validation_evidence SET NOT NULL;

ALTER TABLE factory.visual_selections
    DROP CONSTRAINT IF EXISTS visual_selection_validation_mode;
ALTER TABLE factory.visual_selections
    ADD CONSTRAINT visual_selection_validation_mode
    CHECK (validation_mode IN ('metadata','gemini'));

-- Local diagram candidates are generated from the immutable storyboard.
-- They are not external provider search results, so search_id is nullable.
ALTER TABLE factory.visual_candidates
    ALTER COLUMN search_id DROP NOT NULL;

ALTER TABLE factory.visual_candidates
    DROP CONSTRAINT IF EXISTS visual_candidate_provider;
ALTER TABLE factory.visual_candidates
    ADD CONSTRAINT visual_candidate_provider
    CHECK (provider IN ('pixabay','pexels','wikimedia','local_diagram'));

ALTER TABLE factory.visual_candidates
    DROP CONSTRAINT IF EXISTS visual_candidate_source_https;
ALTER TABLE factory.visual_candidates
    DROP CONSTRAINT IF EXISTS visual_candidate_source_location;
ALTER TABLE factory.visual_candidates
    ADD CONSTRAINT visual_candidate_source_location
    CHECK (
        (provider='local_diagram' AND source_url ~ '^local://diagram/')
        OR
        (provider<>'local_diagram' AND source_url ~ '^https://')
    );

ALTER TABLE factory.visual_candidates
    DROP CONSTRAINT IF EXISTS visual_candidate_download_https;
ALTER TABLE factory.visual_candidates
    DROP CONSTRAINT IF EXISTS visual_candidate_download_location;
ALTER TABLE factory.visual_candidates
    ADD CONSTRAINT visual_candidate_download_location
    CHECK (
        (provider='local_diagram' AND download_url ~ '^local://diagram/')
        OR
        (provider<>'local_diagram' AND download_url ~ '^https://')
    );

ALTER TABLE factory.visual_selections
    DROP CONSTRAINT IF EXISTS visual_selection_provider;
ALTER TABLE factory.visual_selections
    ADD CONSTRAINT visual_selection_provider
    CHECK (provider IN ('pixabay','pexels','wikimedia','local_diagram'));

CREATE TABLE IF NOT EXISTS factory.visual_assets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    visual_run_id uuid NOT NULL REFERENCES factory.visual_runs(id) ON DELETE RESTRICT,
    selection_id uuid NOT NULL UNIQUE REFERENCES factory.visual_selections(id) ON DELETE RESTRICT,
    job_id uuid NOT NULL REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    shot_id uuid NOT NULL UNIQUE REFERENCES factory.shots(id) ON DELETE RESTRICT,
    storage_path text NOT NULL UNIQUE,
    sha256 text NOT NULL,
    bytes bigint NOT NULL CHECK (bytes > 0),
    mime_type text NOT NULL,
    media_type text NOT NULL,
    width integer NOT NULL CHECK (width > 0),
    height integer NOT NULL CHECK (height > 0),
    duration_ms integer,
    codec text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT visual_asset_sha CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT visual_asset_media_type CHECK (media_type IN ('photo','video','diagram')),
    CONSTRAINT visual_asset_duration
        CHECK (
            (media_type <> 'video' AND (duration_ms IS NULL OR duration_ms >= 0))
            OR
            (media_type = 'video' AND duration_ms IS NOT NULL AND duration_ms > 0)
        ),
    UNIQUE (visual_run_id, sha256)
);

CREATE OR REPLACE FUNCTION factory.begin_visuals(
    p_job_id uuid
)
RETURNS TABLE (
    visual_run_id uuid,
    alignment_id uuid,
    shot_count integer,
    expected_search_count integer,
    shots_json jsonb
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_job factory.jobs%ROWTYPE;
    v_alignment factory.alignments%ROWTYPE;
    v_run_id uuid;
    v_shot_count integer;
    v_search_count integer;
    v_shots jsonb;
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

    IF v_job.status <> 'alignment_ready' THEN
        RAISE EXCEPTION 'job is not visual-ready from status %', v_job.status
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_alignment
      FROM factory.alignments
     WHERE job_id=p_job_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'alignment not found'
            USING ERRCODE='22023';
    END IF;

    SELECT
        count(*)::integer,
        (
            COALESCE(sum(jsonb_array_length(s.queries_en)),0)::integer * 3
        )
      INTO v_shot_count,v_search_count
      FROM factory.shots s
     WHERE s.job_id=p_job_id;

    IF v_shot_count <= 0 OR v_search_count <= 0 THEN
        RAISE EXCEPTION 'job has no executable visual searches'
            USING ERRCODE='22023';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM factory.shots s
        WHERE s.job_id=p_job_id
          AND (
            jsonb_typeof(s.queries_en) <> 'array'
            OR jsonb_array_length(s.queries_en) < 1
          )
    ) THEN
        RAISE EXCEPTION 'every shot must have at least one visual query'
            USING ERRCODE='22023';
    END IF;

    SELECT jsonb_agg(
               jsonb_build_object(
                   'shot_uuid', s.id::text,
                   'scene_uuid', sc.id::text,
                   'scene_key', sc.scene_key,
                   'scene_order', sc.scene_order,
                   'shot_key', s.shot_key,
                   'shot_order', s.shot_order,
                   'visual_intent', s.visual_intent,
                   'must_show', s.must_show,
                   'must_not_show', s.must_not_show,
                   'queries_en', s.queries_en,
                   'preferred_media_type', s.preferred_media_type
               )
               ORDER BY sc.scene_order,s.shot_order
           )
      INTO v_shots
      FROM factory.shots s
      JOIN factory.scenes sc ON sc.id=s.scene_id
     WHERE s.job_id=p_job_id;

    INSERT INTO factory.visual_runs (
        job_id,
        alignment_id,
        status,
        expected_shot_count,
        expected_search_count
    )
    VALUES (
        p_job_id,
        v_alignment.id,
        'running',
        v_shot_count,
        v_search_count
    )
    RETURNING id INTO v_run_id;

    UPDATE factory.jobs
       SET status='visuals_collecting',
           updated_at=now()
     WHERE id=p_job_id;

    RETURN QUERY
    SELECT v_run_id,v_alignment.id,v_shot_count,v_search_count,v_shots;
END;
$$;

CREATE OR REPLACE FUNCTION factory.record_visual_search(
    p_visual_run_id uuid,
    p_shot_id uuid,
    p_provider text,
    p_query_index integer,
    p_query_text text,
    p_endpoint_kind text,
    p_http_status integer,
    p_response_headers jsonb,
    p_candidates jsonb
)
RETURNS TABLE (
    search_id uuid,
    candidate_count integer
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.visual_runs%ROWTYPE;
    v_shot factory.shots%ROWTYPE;
    v_search_id uuid;
    v_expected_query text;
    v_expected_endpoint text;
    v_candidate jsonb;
    v_provider_asset_id text;
    v_media_type text;
    v_license_name text;
    v_count integer := 0;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.visual_runs
     WHERE id=p_visual_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'visual run is not active'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_shot
      FROM factory.shots
     WHERE id=p_shot_id
       AND job_id=v_run.job_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'shot does not belong to visual run job'
            USING ERRCODE='22023';
    END IF;

    IF p_provider NOT IN ('pixabay','pexels','wikimedia') THEN
        RAISE EXCEPTION 'unsupported visual provider'
            USING ERRCODE='22023';
    END IF;

    IF p_query_index < 1
       OR p_query_index > jsonb_array_length(v_shot.queries_en) THEN
        RAISE EXCEPTION 'invalid visual query index'
            USING ERRCODE='22023';
    END IF;

    v_expected_query := btrim(v_shot.queries_en->>(p_query_index-1));
    IF btrim(COALESCE(p_query_text,'')) <> v_expected_query THEN
        RAISE EXCEPTION 'visual query text mismatch'
            USING ERRCODE='22023';
    END IF;

    v_expected_endpoint := CASE
        WHEN v_shot.preferred_media_type='video' THEN 'video'
        ELSE 'photo'
    END;

    IF p_endpoint_kind <> v_expected_endpoint THEN
        RAISE EXCEPTION 'visual endpoint kind mismatch'
            USING ERRCODE='22023';
    END IF;

    IF jsonb_typeof(p_candidates) <> 'array' THEN
        RAISE EXCEPTION 'visual candidates must be an array'
            USING ERRCODE='22023';
    END IF;

    IF p_http_status < 100 OR p_http_status > 599 THEN
        RAISE EXCEPTION 'visual provider HTTP status is invalid: %',p_http_status
            USING ERRCODE='22023';
    END IF;

    IF p_http_status <> 200 AND jsonb_array_length(p_candidates) <> 0 THEN
        RAISE EXCEPTION 'failed visual provider search cannot contain candidates'
            USING ERRCODE='22023';
    END IF;

    INSERT INTO factory.visual_searches (
        visual_run_id,
        job_id,
        shot_id,
        provider,
        query_index,
        query_text,
        provider_query_text,
        endpoint_kind,
        http_status,
        result_count,
        response_headers,
        cache_expires_at
    )
    VALUES (
        v_run.id,
        v_run.job_id,
        v_shot.id,
        p_provider,
        p_query_index,
        v_expected_query,
        v_expected_query,
        p_endpoint_kind,
        p_http_status,
        jsonb_array_length(p_candidates),
        COALESCE(p_response_headers,'{}'::jsonb),
        CASE
            WHEN p_http_status = 200 THEN now() + interval '24 hours'
            ELSE now() + interval '5 minutes'
        END
    )
    RETURNING id INTO v_search_id;

    FOR v_candidate IN
        SELECT value
        FROM jsonb_array_elements(p_candidates)
    LOOP
        v_provider_asset_id := btrim(COALESCE(v_candidate->>'provider_asset_id',''));
        v_media_type := btrim(COALESCE(v_candidate->>'media_type',''));
        v_license_name := btrim(COALESCE(v_candidate->>'license_name',''));

        IF v_provider_asset_id=''
           OR v_media_type NOT IN ('photo','video','diagram')
           OR COALESCE((v_candidate->>'provider_rank')::integer,0) < 1
           OR COALESCE((v_candidate->>'width')::integer,0) <= 0
           OR COALESCE((v_candidate->>'height')::integer,0) <= 0
           OR COALESCE((v_candidate->>'relevance_score')::integer,-1) NOT BETWEEN 0 AND 1000
           OR COALESCE(v_candidate->>'source_url','') !~ '^https://'
           OR COALESCE(v_candidate->>'download_url','') !~ '^https://' THEN
            RAISE EXCEPTION 'invalid normalized visual candidate'
                USING ERRCODE='22023';
        END IF;

        IF v_media_type='video'
           AND COALESCE((v_candidate->>'duration_ms')::integer,0) <= 0 THEN
            RAISE EXCEPTION 'video candidate duration is required'
                USING ERRCODE='22023';
        END IF;

        IF p_provider='pixabay' AND v_license_name <> 'Pixabay Content License' THEN
            RAISE EXCEPTION 'Pixabay license metadata mismatch'
                USING ERRCODE='22023';
        ELSIF p_provider='pexels' AND v_license_name <> 'Pexels License' THEN
            RAISE EXCEPTION 'Pexels license metadata mismatch'
                USING ERRCODE='22023';
        ELSIF p_provider='wikimedia'
              AND v_license_name !~* '^(CC0|CC BY([ -]|$)|CC BY-SA([ -]|$)|Public domain|PDM)' THEN
            RAISE EXCEPTION 'Wikimedia license is not accepted: %',v_license_name
                USING ERRCODE='22023';
        END IF;

        INSERT INTO factory.visual_candidates (
            visual_run_id,
            search_id,
            job_id,
            shot_id,
            provider,
            provider_asset_id,
            provider_rank,
            media_type,
            source_url,
            download_url,
            preview_url,
            author,
            author_url,
            license_name,
            license_url,
            width,
            height,
            duration_ms,
            metadata_text,
            query_text,
            relevance_score,
            rejected,
            rejection_reason,
            metadata
        )
        VALUES (
            v_run.id,
            v_search_id,
            v_run.job_id,
            v_shot.id,
            p_provider,
            v_provider_asset_id,
            (v_candidate->>'provider_rank')::integer,
            v_media_type,
            v_candidate->>'source_url',
            v_candidate->>'download_url',
            NULLIF(btrim(COALESCE(v_candidate->>'preview_url','')),''),
            NULLIF(btrim(COALESCE(v_candidate->>'author','')),''),
            NULLIF(btrim(COALESCE(v_candidate->>'author_url','')),''),
            v_license_name,
            btrim(COALESCE(v_candidate->>'license_url','')),
            (v_candidate->>'width')::integer,
            (v_candidate->>'height')::integer,
            NULLIF(v_candidate->>'duration_ms','')::integer,
            COALESCE(v_candidate->>'metadata_text',''),
            v_expected_query,
            (v_candidate->>'relevance_score')::integer,
            COALESCE((v_candidate->>'rejected')::boolean,false),
            NULLIF(btrim(COALESCE(v_candidate->>'rejection_reason','')),''),
            COALESCE(v_candidate->'metadata','{}'::jsonb)
        );

        v_count := v_count + 1;
    END LOOP;

    RETURN QUERY SELECT v_search_id,v_count;
END;
$$;

CREATE OR REPLACE FUNCTION factory.record_local_diagram_candidate(
    p_visual_run_id uuid,
    p_shot_id uuid,
    p_visual_intent text,
    p_must_show jsonb
)
RETURNS uuid
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.visual_runs%ROWTYPE;
    v_shot factory.shots%ROWTYPE;
    v_candidate_id uuid;
    v_asset_key text;
    v_location text;
    v_metadata_text text;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.visual_runs
     WHERE id=p_visual_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'visual run is not active'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_shot
      FROM factory.shots
     WHERE id=p_shot_id
       AND job_id=v_run.job_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'shot does not belong to visual run job'
            USING ERRCODE='22023';
    END IF;

    IF v_shot.preferred_media_type <> 'diagram' THEN
        RAISE EXCEPTION 'local diagram candidate is only valid for diagram shots'
            USING ERRCODE='22023';
    END IF;

    IF btrim(COALESCE(p_visual_intent,'')) <> btrim(v_shot.visual_intent)
       OR COALESCE(p_must_show,'[]'::jsonb) <> v_shot.must_show THEN
        RAISE EXCEPTION 'local diagram storyboard payload mismatch'
            USING ERRCODE='22023';
    END IF;

    v_asset_key := 'local-diagram:' || v_shot.id::text;
    v_location := 'local://diagram/' || v_run.job_id::text || '/' || v_shot.id::text;

    SELECT concat_ws(
               ' ',
               v_shot.visual_intent,
               COALESCE(string_agg(value, ' '),'')
           )
      INTO v_metadata_text
      FROM jsonb_array_elements_text(v_shot.must_show);

    INSERT INTO factory.visual_candidates (
        visual_run_id,
        search_id,
        job_id,
        shot_id,
        provider,
        provider_asset_id,
        provider_rank,
        media_type,
        source_url,
        download_url,
        preview_url,
        author,
        author_url,
        license_name,
        license_url,
        width,
        height,
        duration_ms,
        metadata_text,
        query_text,
        relevance_score,
        rejected,
        rejection_reason,
        metadata
    )
    VALUES (
        v_run.id,
        NULL,
        v_run.job_id,
        v_shot.id,
        'local_diagram',
        v_asset_key,
        1,
        'diagram',
        v_location,
        v_location,
        NULL,
        'AI Short Form Content Factory',
        NULL,
        'Generated locally',
        'local://generated',
        1080,
        1920,
        NULL,
        v_metadata_text,
        COALESCE(v_shot.queries_en->>0, v_shot.visual_intent),
        1000,
        false,
        NULL,
        jsonb_build_object(
            'generator','deterministic_local_diagram_v1',
            'visual_intent',v_shot.visual_intent,
            'must_show',v_shot.must_show
        )
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_candidate_id;

    IF v_candidate_id IS NULL THEN
        SELECT id
          INTO v_candidate_id
          FROM factory.visual_candidates
         WHERE visual_run_id=v_run.id
           AND shot_id=v_shot.id
           AND provider='local_diagram'
           AND provider_asset_id=v_asset_key
         ORDER BY created_at
         LIMIT 1;
    END IF;

    IF v_candidate_id IS NULL THEN
        RAISE EXCEPTION 'local diagram candidate could not be recorded'
            USING ERRCODE='22023';
    END IF;

    RETURN v_candidate_id;
END;
$$;

CREATE OR REPLACE FUNCTION factory.select_visuals(
    p_visual_run_id uuid,
    p_min_relevance_score integer DEFAULT 55
)
RETURNS TABLE (
    selection_count integer,
    selections_json jsonb
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.visual_runs%ROWTYPE;
    v_shot record;
    v_candidate factory.visual_candidates%ROWTYPE;
    v_selection_id uuid;
    v_count integer := 0;
    v_search_count integer;
    v_selected jsonb := '[]'::jsonb;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.visual_runs
     WHERE id=p_visual_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'visual run is not active'
            USING ERRCODE='22023';
    END IF;

    IF p_min_relevance_score < 0 OR p_min_relevance_score > 1000 THEN
        RAISE EXCEPTION 'invalid minimum visual relevance score'
            USING ERRCODE='22023';
    END IF;

    SELECT count(*)::integer
      INTO v_search_count
      FROM factory.visual_searches
     WHERE visual_run_id=v_run.id;

    IF v_search_count <> v_run.expected_search_count THEN
        RAISE EXCEPTION 'visual search coverage incomplete: got %, expected %',
            v_search_count,v_run.expected_search_count
            USING ERRCODE='22023';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM factory.shots sh
        CROSS JOIN (VALUES ('pixabay'),('pexels'),('wikimedia')) AS p(provider)
        WHERE sh.job_id=v_run.job_id
          AND NOT EXISTS (
              SELECT 1
              FROM factory.visual_searches vs
              WHERE vs.visual_run_id=v_run.id
                AND vs.shot_id=sh.id
                AND vs.provider=p.provider
          )
    ) THEN
        RAISE EXCEPTION 'not every enabled provider was queried for every shot'
            USING ERRCODE='22023';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM factory.visual_selections
        WHERE visual_run_id=v_run.id
    ) THEN
        RAISE EXCEPTION 'visual selections already exist'
            USING ERRCODE='22023';
    END IF;

    FOR v_shot IN
        SELECT sh.*,sc.scene_order
        FROM factory.shots sh
        JOIN factory.scenes sc ON sc.id=sh.scene_id
        WHERE sh.job_id=v_run.job_id
        ORDER BY sc.scene_order,sh.shot_order,sh.id
    LOOP
        SELECT vc.*
          INTO v_candidate
          FROM factory.visual_candidates vc
          JOIN factory.visual_searches vq ON vq.id=vc.search_id
         WHERE vc.visual_run_id=v_run.id
           AND vc.shot_id=v_shot.id
           AND vc.rejected=false
           AND vc.provider <> 'local_diagram'
           AND vc.relevance_score >= p_min_relevance_score
           AND (
               (v_shot.preferred_media_type='video' AND vc.media_type='video')
               OR
               (v_shot.preferred_media_type='photo' AND vc.media_type='photo')
           )
           AND NOT EXISTS (
               SELECT 1
               FROM factory.visual_selections s
               WHERE s.visual_run_id=v_run.id
                 AND s.provider=vc.provider
                 AND s.provider_asset_id=vc.provider_asset_id
           )
         ORDER BY
           CASE
             WHEN vq.query_index <= 2 THEN 0
             ELSE 1
           END,
           CASE
             WHEN vc.media_type=v_shot.preferred_media_type THEN 0
             WHEN v_shot.preferred_media_type='diagram' AND vc.media_type='photo' THEN 1
             ELSE 2
           END,
           vc.relevance_score DESC,
           abs((vc.width::numeric / vc.height::numeric) - (9.0::numeric / 16.0::numeric)) ASC,
           vc.provider_rank ASC,
           (vc.width::bigint * vc.height::bigint) DESC,
           vc.provider ASC,
           vc.provider_asset_id ASC,
           vc.id ASC
         LIMIT 1;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'no compliant relevant visual candidate for shot %',
                v_shot.shot_key
                USING ERRCODE='22023';
        END IF;

        INSERT INTO factory.visual_selections (
            visual_run_id,
            job_id,
            shot_id,
            candidate_id,
            provider,
            provider_asset_id,
            validation_mode,
            validation_evidence
        )
        VALUES (
            v_run.id,
            v_run.job_id,
            v_shot.id,
            v_candidate.id,
            v_candidate.provider,
            v_candidate.provider_asset_id,
            'metadata',
            jsonb_build_object(
                'source','deterministic_metadata',
                'relevance_score',v_candidate.relevance_score
            )
        )
        RETURNING id INTO v_selection_id;

        v_selected := v_selected || jsonb_build_array(
            jsonb_build_object(
                'selection_id',v_selection_id::text,
                'shot_uuid',v_shot.id::text,
                'shot_key',v_shot.shot_key,
                'scene_order',v_shot.scene_order,
                'preferred_media_type',v_shot.preferred_media_type,
                'candidate_id',v_candidate.id::text,
                'provider',v_candidate.provider,
                'provider_asset_id',v_candidate.provider_asset_id,
                'media_type',v_candidate.media_type,
                'source_url',v_candidate.source_url,
                'download_url',v_candidate.download_url,
                'preview_url',v_candidate.preview_url,
                'author',v_candidate.author,
                'author_url',v_candidate.author_url,
                'license_name',v_candidate.license_name,
                'license_url',v_candidate.license_url,
                'width',v_candidate.width,
                'height',v_candidate.height,
                'duration_ms',v_candidate.duration_ms,
                'relevance_score',v_candidate.relevance_score,
                'visual_validation_mode','metadata',
                'validation_evidence',jsonb_build_object(
                    'source','deterministic_metadata',
                    'relevance_score',v_candidate.relevance_score
                ),
                'visual_intent',v_shot.visual_intent,
                'must_show',v_shot.must_show,
                'must_not_show',v_shot.must_not_show
            )
        );

        v_count := v_count + 1;
    END LOOP;

    IF v_count <> v_run.expected_shot_count THEN
        RAISE EXCEPTION 'visual selection count mismatch'
            USING ERRCODE='22023';
    END IF;

    UPDATE factory.jobs
       SET status='visuals_selected',
           updated_at=now()
     WHERE id=v_run.job_id;

    RETURN QUERY SELECT v_count,v_selected;
END;
$$;


CREATE OR REPLACE FUNCTION factory.gemini_visual_review_bucket(
    p_rejected boolean,
    p_rejection_reason text
)
RETURNS integer
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_reason text;
BEGIN
    IF COALESCE(p_rejected,false)=false THEN
        RETURN 0;
    END IF;

    IF NULLIF(btrim(COALESCE(p_rejection_reason,'')),'') IS NULL THEN
        RETURN 99;
    END IF;

    FOR v_reason IN
        SELECT btrim(value)
        FROM regexp_split_to_table(p_rejection_reason,';') AS value
    LOOP
        IF v_reason LIKE 'missing_primary_subject_anchor:%'
           OR v_reason LIKE 'insufficient_primary_subject_coverage:%'
           OR v_reason='insufficient_must_show_concept_coverage'
           OR v_reason='insufficient_query_intent_metadata_match'
           OR v_reason='missing_distinctive_domain_anchor'
           OR v_reason='missing_secondary_subject_context'
           OR v_reason LIKE 'missing_storyboard_domain_context:%'
           OR v_reason LIKE 'missing_visual_detail_anchor:%'
           OR v_reason='missing_operational_setting_context' THEN
            CONTINUE;
        END IF;

        RETURN 99;
    END LOOP;

    RETURN 1;
END;
$$;


CREATE OR REPLACE FUNCTION factory.get_gemini_visual_candidate_sets(
    p_visual_run_id uuid,
    p_min_relevance_score integer DEFAULT 55,
    p_limit_per_shot integer DEFAULT 3
)
RETURNS TABLE (
    shot_count integer,
    candidate_sets_json jsonb
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.visual_runs%ROWTYPE;
    v_job factory.jobs%ROWTYPE;
    v_shot record;
    v_candidates jsonb;
    v_sets jsonb := '[]'::jsonb;
    v_count integer := 0;
    v_search_count integer;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.visual_runs
     WHERE id=p_visual_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'visual run is not active'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_job
      FROM factory.jobs
     WHERE id=v_run.job_id;

    IF NOT FOUND OR v_job.visual_validation_mode <> 'gemini' THEN
        RAISE EXCEPTION 'job is not configured for Gemini visual validation'
            USING ERRCODE='22023';
    END IF;

    IF p_min_relevance_score < 0 OR p_min_relevance_score > 1000 THEN
        RAISE EXCEPTION 'invalid minimum visual relevance score'
            USING ERRCODE='22023';
    END IF;

    IF p_limit_per_shot < 1 OR p_limit_per_shot > 3 THEN
        RAISE EXCEPTION 'Gemini candidate limit must be between 1 and 3'
            USING ERRCODE='22023';
    END IF;

    SELECT count(*)::integer
      INTO v_search_count
      FROM factory.visual_searches
     WHERE visual_run_id=v_run.id;

    IF v_search_count <> v_run.expected_search_count THEN
        RAISE EXCEPTION 'visual search coverage incomplete: got %, expected %',
            v_search_count,v_run.expected_search_count
            USING ERRCODE='22023';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM factory.visual_selections
        WHERE visual_run_id=v_run.id
    ) THEN
        RAISE EXCEPTION 'visual selections already exist'
            USING ERRCODE='22023';
    END IF;

    FOR v_shot IN
        SELECT sh.*,sc.scene_order
        FROM factory.shots sh
        JOIN factory.scenes sc ON sc.id=sh.scene_id
        WHERE sh.job_id=v_run.job_id
        ORDER BY sc.scene_order,sh.shot_order,sh.id
    LOOP
        WITH eligible AS (
            SELECT
                vc.*,
                vq.query_index,
                CASE WHEN vq.query_index <= 2 THEN 0 ELSE 1 END AS query_bucket,
                factory.gemini_visual_review_bucket(vc.rejected,vc.rejection_reason) AS review_bucket,
                CASE
                    WHEN vc.media_type=v_shot.preferred_media_type THEN 0
                    WHEN v_shot.preferred_media_type='diagram' AND vc.media_type='photo' THEN 1
                    ELSE 2
                END AS media_bucket,
                abs((vc.width::numeric / vc.height::numeric) - (9.0::numeric / 16.0::numeric)) AS aspect_distance,
                COALESCE(
                    NULLIF(vc.preview_url,''),
                    CASE WHEN vc.media_type='photo' THEN vc.download_url ELSE NULL END
                ) AS vision_preview_url
            FROM factory.visual_candidates vc
            JOIN factory.visual_searches vq ON vq.id=vc.search_id
            WHERE vc.visual_run_id=v_run.id
              AND vc.shot_id=v_shot.id
              AND factory.gemini_visual_review_bucket(vc.rejected,vc.rejection_reason) < 99
              AND vc.provider <> 'local_diagram'
              AND vc.relevance_score >= p_min_relevance_score
              AND (
                  (v_shot.preferred_media_type='video' AND vc.media_type='video')
                  OR
                  (v_shot.preferred_media_type='photo' AND vc.media_type='photo')
              )
              AND COALESCE(
                    NULLIF(vc.preview_url,''),
                    CASE WHEN vc.media_type='photo' THEN vc.download_url ELSE NULL END
                  ) IS NOT NULL
        ),
        dedup AS (
            SELECT DISTINCT ON (provider,provider_asset_id)
                *
            FROM eligible
            ORDER BY
                provider,
                provider_asset_id,
                review_bucket,
                query_bucket,
                media_bucket,
                relevance_score DESC,
                aspect_distance ASC,
                provider_rank ASC,
                (width::bigint * height::bigint) DESC,
                id ASC
        ),
        provider_ranked AS (
            SELECT
                d.*,
                row_number() OVER (
                    PARTITION BY provider
                    ORDER BY
                        review_bucket,
                        query_bucket,
                        media_bucket,
                        relevance_score DESC,
                        aspect_distance ASC,
                        provider_rank ASC,
                        (width::bigint * height::bigint) DESC,
                        provider_asset_id ASC,
                        id ASC
                ) AS provider_candidate_rank
            FROM dedup d
        ),
        ranked AS (
            SELECT
                d.*,
                row_number() OVER (
                    ORDER BY
                        provider_candidate_rank,
                        review_bucket,
                        query_bucket,
                        media_bucket,
                        relevance_score DESC,
                        aspect_distance ASC,
                        provider_rank ASC,
                        (width::bigint * height::bigint) DESC,
                        provider ASC,
                        provider_asset_id ASC,
                        id ASC
                ) AS candidate_index
            FROM provider_ranked d
        )
        SELECT COALESCE(
            jsonb_agg(
                jsonb_build_object(
                    'candidate_index',candidate_index,
                    'candidate_id',id::text,
                    'provider',provider,
                    'provider_asset_id',provider_asset_id,
                    'media_type',media_type,
                    'source_url',source_url,
                    'download_url',download_url,
                    'preview_url',vision_preview_url,
                    'author',author,
                    'author_url',author_url,
                    'license_name',license_name,
                    'license_url',license_url,
                    'width',width,
                    'height',height,
                    'duration_ms',duration_ms,
                    'relevance_score',relevance_score,
                    'metadata_rejected',rejected,
                    'metadata_rejection_reason',rejection_reason,
                    'review_bucket',review_bucket
                )
                ORDER BY candidate_index
            ),
            '[]'::jsonb
        )
        INTO v_candidates
        FROM ranked
        WHERE candidate_index <= p_limit_per_shot;

        IF jsonb_array_length(v_candidates) = 0 THEN
            RAISE EXCEPTION 'no Gemini-previewable relevant visual candidate for shot %',
                v_shot.shot_key
                USING ERRCODE='22023';
        END IF;

        v_sets := v_sets || jsonb_build_array(
            jsonb_build_object(
                'visual_run_id',v_run.id::text,
                'shot_uuid',v_shot.id::text,
                'shot_key',v_shot.shot_key,
                'scene_order',v_shot.scene_order,
                'shot_order',v_shot.shot_order,
                'preferred_media_type',v_shot.preferred_media_type,
                'visual_intent',v_shot.visual_intent,
                'must_show',v_shot.must_show,
                'must_not_show',v_shot.must_not_show,
                'candidates',v_candidates
            )
        );
        v_count := v_count + 1;
    END LOOP;

    IF v_count <> v_run.expected_shot_count THEN
        RAISE EXCEPTION 'Gemini candidate-set count mismatch'
            USING ERRCODE='22023';
    END IF;

    RETURN QUERY SELECT v_count,v_sets;
END;
$$;


CREATE OR REPLACE FUNCTION factory.commit_gemini_visual_selections(
    p_visual_run_id uuid,
    p_min_relevance_score integer,
    p_selections jsonb
)
RETURNS TABLE (
    selection_count integer,
    selections_json jsonb
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.visual_runs%ROWTYPE;
    v_job factory.jobs%ROWTYPE;
    v_item jsonb;
    v_shot factory.shots%ROWTYPE;
    v_scene_order integer;
    v_candidate factory.visual_candidates%ROWTYPE;
    v_selection_id uuid;
    v_count integer := 0;
    v_selected jsonb := '[]'::jsonb;
    v_seen_shots text[] := ARRAY[]::text[];
    v_seen_assets text[] := ARRAY[]::text[];
    v_shot_id uuid;
    v_candidate_id uuid;
    v_asset_key text;
    v_evidence jsonb;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.visual_runs
     WHERE id=p_visual_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'visual run is not active'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_job
      FROM factory.jobs
     WHERE id=v_run.job_id;

    IF NOT FOUND OR v_job.visual_validation_mode <> 'gemini' THEN
        RAISE EXCEPTION 'job is not configured for Gemini visual validation'
            USING ERRCODE='22023';
    END IF;

    IF p_min_relevance_score < 0 OR p_min_relevance_score > 1000 THEN
        RAISE EXCEPTION 'invalid minimum visual relevance score'
            USING ERRCODE='22023';
    END IF;

    IF jsonb_typeof(p_selections) <> 'array'
       OR jsonb_array_length(p_selections) <> v_run.expected_shot_count THEN
        RAISE EXCEPTION 'Gemini selection payload count mismatch'
            USING ERRCODE='22023';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM factory.visual_selections
        WHERE visual_run_id=v_run.id
    ) THEN
        RAISE EXCEPTION 'visual selections already exist'
            USING ERRCODE='22023';
    END IF;

    FOR v_item IN
        SELECT value
        FROM jsonb_array_elements(p_selections)
    LOOP
        v_shot_id := (v_item->>'shot_uuid')::uuid;
        v_candidate_id := (v_item->>'candidate_id')::uuid;
        v_evidence := COALESCE(v_item->'validation_evidence','{}'::jsonb);

        IF v_shot_id::text = ANY(v_seen_shots) THEN
            RAISE EXCEPTION 'duplicate Gemini selection shot'
                USING ERRCODE='22023';
        END IF;

        IF jsonb_typeof(v_evidence) <> 'object'
           OR COALESCE((v_evidence->>'vision_pass')::boolean,false) <> true
           OR btrim(COALESCE(v_evidence->>'model','')) = '' THEN
            RAISE EXCEPTION 'Gemini validation evidence is not a passing object'
                USING ERRCODE='22023';
        END IF;

        SELECT *
          INTO v_shot
          FROM factory.shots
         WHERE id=v_shot_id
           AND job_id=v_run.job_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Gemini selection shot does not belong to job'
                USING ERRCODE='22023';
        END IF;

        SELECT sc.scene_order
          INTO v_scene_order
          FROM factory.scenes sc
         WHERE sc.id=v_shot.scene_id;

        SELECT *
          INTO v_candidate
          FROM factory.visual_candidates
         WHERE id=v_candidate_id
           AND visual_run_id=v_run.id
           AND shot_id=v_shot.id
           AND factory.gemini_visual_review_bucket(rejected,rejection_reason) < 99
           AND provider <> 'local_diagram'
           AND relevance_score >= p_min_relevance_score;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Gemini-selected candidate is not eligible'
                USING ERRCODE='22023';
        END IF;

        IF NOT (
            (v_shot.preferred_media_type='video' AND v_candidate.media_type='video')
            OR
            (v_shot.preferred_media_type='photo' AND v_candidate.media_type='photo')
        ) THEN
            RAISE EXCEPTION 'Gemini-selected candidate media type is incompatible'
                USING ERRCODE='22023';
        END IF;

        v_asset_key := v_candidate.provider || ':' || v_candidate.provider_asset_id;
        IF v_asset_key = ANY(v_seen_assets) THEN
            RAISE EXCEPTION 'Gemini selections reuse the same provider asset'
                USING ERRCODE='22023';
        END IF;

        INSERT INTO factory.visual_selections (
            visual_run_id,
            job_id,
            shot_id,
            candidate_id,
            provider,
            provider_asset_id,
            validation_mode,
            validation_evidence
        )
        VALUES (
            v_run.id,
            v_run.job_id,
            v_shot.id,
            v_candidate.id,
            v_candidate.provider,
            v_candidate.provider_asset_id,
            'gemini',
            v_evidence
        )
        RETURNING id INTO v_selection_id;

        v_selected := v_selected || jsonb_build_array(
            jsonb_build_object(
                'selection_id',v_selection_id::text,
                'shot_uuid',v_shot.id::text,
                'shot_key',v_shot.shot_key,
                'scene_order',v_scene_order,
                'preferred_media_type',v_shot.preferred_media_type,
                'candidate_id',v_candidate.id::text,
                'provider',v_candidate.provider,
                'provider_asset_id',v_candidate.provider_asset_id,
                'media_type',v_candidate.media_type,
                'source_url',v_candidate.source_url,
                'download_url',v_candidate.download_url,
                'preview_url',v_candidate.preview_url,
                'author',v_candidate.author,
                'author_url',v_candidate.author_url,
                'license_name',v_candidate.license_name,
                'license_url',v_candidate.license_url,
                'width',v_candidate.width,
                'height',v_candidate.height,
                'duration_ms',v_candidate.duration_ms,
                'relevance_score',v_candidate.relevance_score,
                'visual_validation_mode','gemini',
                'validation_evidence',v_evidence,
                'visual_intent',v_shot.visual_intent,
                'must_show',v_shot.must_show,
                'must_not_show',v_shot.must_not_show
            )
        );

        v_seen_shots := array_append(v_seen_shots,v_shot.id::text);
        v_seen_assets := array_append(v_seen_assets,v_asset_key);
        v_count := v_count + 1;
    END LOOP;

    IF v_count <> v_run.expected_shot_count THEN
        RAISE EXCEPTION 'Gemini visual selection count mismatch'
            USING ERRCODE='22023';
    END IF;

    UPDATE factory.jobs
       SET status='visuals_selected',
           updated_at=now()
     WHERE id=v_run.job_id;

    RETURN QUERY SELECT v_count,v_selected;
END;
$$;


CREATE OR REPLACE FUNCTION factory.record_visual_asset(
    p_visual_run_id uuid,
    p_selection_id uuid,
    p_asset jsonb
)
RETURNS TABLE (
    visual_asset_id uuid
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.visual_runs%ROWTYPE;
    v_selection factory.visual_selections%ROWTYPE;
    v_candidate factory.visual_candidates%ROWTYPE;
    v_asset_id uuid;
    v_storage_path text;
    v_sha text;
    v_bytes bigint;
    v_media_type text;
    v_width integer;
    v_height integer;
    v_duration integer;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.visual_runs
     WHERE id=p_visual_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'visual run is not active'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_selection
      FROM factory.visual_selections
     WHERE id=p_selection_id
       AND visual_run_id=v_run.id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'visual selection does not belong to run'
            USING ERRCODE='22023';
    END IF;

    SELECT *
      INTO v_candidate
      FROM factory.visual_candidates
     WHERE id=v_selection.candidate_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'selected visual candidate not found'
            USING ERRCODE='22023';
    END IF;

    v_storage_path := btrim(COALESCE(p_asset->>'storage_path',''));
    v_sha := lower(btrim(COALESCE(p_asset->>'sha256','')));
    v_bytes := NULLIF(p_asset->>'bytes','')::bigint;
    v_media_type := btrim(COALESCE(p_asset->>'media_type',''));
    v_width := NULLIF(p_asset->>'width','')::integer;
    v_height := NULLIF(p_asset->>'height','')::integer;
    v_duration := NULLIF(p_asset->>'duration_ms','')::integer;

    IF v_storage_path !~ (
           '^/data/visuals/' || v_run.job_id::text || '/' ||
           v_selection.shot_id::text || '/selected[.][A-Za-z0-9]+$'
       )
       OR v_sha !~ '^[0-9a-f]{64}$'
       OR v_bytes IS NULL OR v_bytes <= 0
       OR v_media_type <> v_candidate.media_type
       OR v_width IS NULL OR v_width <= 0
       OR v_height IS NULL OR v_height <= 0
       OR btrim(COALESCE(p_asset->>'mime_type',''))=''
       OR btrim(COALESCE(p_asset->>'codec',''))='' THEN
        RAISE EXCEPTION 'invalid persisted visual asset metadata'
            USING ERRCODE='22023';
    END IF;

    IF v_media_type='video' AND (v_duration IS NULL OR v_duration <= 0) THEN
        RAISE EXCEPTION 'video asset duration is required'
            USING ERRCODE='22023';
    END IF;

    INSERT INTO factory.visual_assets (
        visual_run_id,
        selection_id,
        job_id,
        shot_id,
        storage_path,
        sha256,
        bytes,
        mime_type,
        media_type,
        width,
        height,
        duration_ms,
        codec
    )
    VALUES (
        v_run.id,
        v_selection.id,
        v_run.job_id,
        v_selection.shot_id,
        v_storage_path,
        v_sha,
        v_bytes,
        p_asset->>'mime_type',
        v_media_type,
        v_width,
        v_height,
        v_duration,
        p_asset->>'codec'
    )
    RETURNING id INTO v_asset_id;

    RETURN QUERY SELECT v_asset_id;
END;
$$;

CREATE OR REPLACE FUNCTION factory.complete_visuals(
    p_visual_run_id uuid
)
RETURNS TABLE (
    visual_count integer
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.visual_runs%ROWTYPE;
    v_selection_count integer;
    v_asset_count integer;
    v_distinct_hashes integer;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.visual_runs
     WHERE id=p_visual_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'visual run is not active'
            USING ERRCODE='22023';
    END IF;

    SELECT count(*)::integer
      INTO v_selection_count
      FROM factory.visual_selections
     WHERE visual_run_id=v_run.id;

    SELECT count(*)::integer,count(DISTINCT sha256)::integer
      INTO v_asset_count,v_distinct_hashes
      FROM factory.visual_assets
     WHERE visual_run_id=v_run.id;

    IF v_selection_count <> v_run.expected_shot_count
       OR v_asset_count <> v_run.expected_shot_count
       OR v_distinct_hashes <> v_run.expected_shot_count THEN
        RAISE EXCEPTION 'visual assets are incomplete or reused'
            USING ERRCODE='22023';
    END IF;

    UPDATE factory.visual_runs
       SET status='passed',
           completed_at=now(),
           failure_reason=NULL
     WHERE id=v_run.id;

    UPDATE factory.jobs
       SET status='visuals_ready',
           updated_at=now()
     WHERE id=v_run.job_id;

    RETURN QUERY SELECT v_asset_count;
END;
$$;

CREATE OR REPLACE FUNCTION factory.fail_visuals(
    p_visual_run_id uuid,
    p_reason text
)
RETURNS TABLE (
    visual_status text,
    job_status text
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.visual_runs%ROWTYPE;
    v_job_status text;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.visual_runs
     WHERE id=p_visual_run_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'visual run not found'
            USING ERRCODE='22023';
    END IF;

    IF v_run.status='passed' THEN
        RAISE EXCEPTION 'passed visual run cannot be failed'
            USING ERRCODE='22023';
    END IF;

    IF v_run.status='running' THEN
        UPDATE factory.visual_runs
           SET status='failed',
               completed_at=now(),
               failure_reason=left(
                   COALESCE(NULLIF(btrim(p_reason),''),'unspecified visual failure'),
                   4000
               )
         WHERE id=v_run.id;

        UPDATE factory.jobs
           SET status='visuals_failed',
               updated_at=now()
         WHERE id=v_run.job_id;
    END IF;

    SELECT status INTO v_job_status
      FROM factory.jobs
     WHERE id=v_run.job_id;

    RETURN QUERY SELECT 'failed'::text,v_job_status;
END;
$$;


ALTER TABLE factory.visual_runs
    ADD COLUMN IF NOT EXISTS selection_claimed_at timestamptz;

ALTER TABLE factory.visual_runs
    ADD COLUMN IF NOT EXISTS completion_claimed_at timestamptz;

CREATE TABLE IF NOT EXISTS factory.visual_query_cache (
    provider text NOT NULL,
    endpoint_kind text NOT NULL,
    query_text text NOT NULL,
    http_status integer NOT NULL,
    response_headers jsonb NOT NULL DEFAULT '{}'::jsonb,
    candidates jsonb NOT NULL,
    fetched_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    PRIMARY KEY (provider, endpoint_kind, query_text),

    CONSTRAINT visual_query_cache_provider
        CHECK (provider IN ('pixabay','pexels','wikimedia')),
    CONSTRAINT visual_query_cache_endpoint
        CHECK (endpoint_kind IN ('photo','video')),
    CONSTRAINT visual_query_cache_query
        CHECK (char_length(btrim(query_text)) > 0),
    CONSTRAINT visual_query_cache_http
        CHECK (http_status=200),
    CONSTRAINT visual_query_cache_candidates
        CHECK (jsonb_typeof(candidates)='array')
);

CREATE INDEX IF NOT EXISTS visual_query_cache_expires_idx
    ON factory.visual_query_cache (expires_at);

CREATE OR REPLACE FUNCTION factory.get_visual_cache(
    p_provider text,
    p_endpoint_kind text,
    p_query_text text
)
RETURNS TABLE (
    cache_hit boolean,
    http_status integer,
    response_headers jsonb,
    candidates jsonb
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF p_provider NOT IN ('pixabay','pexels','wikimedia')
       OR p_endpoint_kind NOT IN ('photo','video')
       OR btrim(COALESCE(p_query_text,''))='' THEN
        RAISE EXCEPTION 'invalid visual cache lookup'
            USING ERRCODE='22023';
    END IF;

    RETURN QUERY
    SELECT
        true,
        c.http_status,
        c.response_headers,
        c.candidates
    FROM factory.visual_query_cache c
    WHERE c.provider=p_provider
      AND c.endpoint_kind=p_endpoint_kind
      AND c.query_text=btrim(p_query_text)
      AND c.expires_at > now();

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT false,0,'{}'::jsonb,'[]'::jsonb;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION factory.put_visual_cache(
    p_provider text,
    p_endpoint_kind text,
    p_query_text text,
    p_http_status integer,
    p_response_headers jsonb,
    p_candidates jsonb
)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_provider NOT IN ('pixabay','pexels','wikimedia')
       OR p_endpoint_kind NOT IN ('photo','video')
       OR btrim(COALESCE(p_query_text,''))=''
       OR p_http_status <> 200
       OR jsonb_typeof(p_candidates) <> 'array' THEN
        RAISE EXCEPTION 'invalid visual cache write'
            USING ERRCODE='22023';
    END IF;

    INSERT INTO factory.visual_query_cache (
        provider,
        endpoint_kind,
        query_text,
        http_status,
        response_headers,
        candidates,
        fetched_at,
        expires_at
    )
    VALUES (
        p_provider,
        p_endpoint_kind,
        btrim(p_query_text),
        p_http_status,
        COALESCE(p_response_headers,'{}'::jsonb),
        p_candidates,
        now(),
        now()+interval '24 hours'
    )
    ON CONFLICT (provider,endpoint_kind,query_text)
    DO UPDATE SET
        http_status=EXCLUDED.http_status,
        response_headers=EXCLUDED.response_headers,
        candidates=EXCLUDED.candidates,
        fetched_at=EXCLUDED.fetched_at,
        expires_at=EXCLUDED.expires_at;
END;
$$;

CREATE OR REPLACE FUNCTION factory.claim_visual_selection(
    p_visual_run_id uuid
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.visual_runs%ROWTYPE;
    v_search_count integer;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.visual_runs
     WHERE id=p_visual_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RETURN false;
    END IF;

    IF v_run.selection_claimed_at IS NOT NULL THEN
        RETURN false;
    END IF;

    SELECT count(*)::integer
      INTO v_search_count
      FROM factory.visual_searches
     WHERE visual_run_id=v_run.id;

    IF v_search_count <> v_run.expected_search_count THEN
        RETURN false;
    END IF;

    UPDATE factory.visual_runs
       SET selection_claimed_at=now()
     WHERE id=v_run.id;

    RETURN true;
END;
$$;

CREATE OR REPLACE FUNCTION factory.claim_visual_completion(
    p_visual_run_id uuid
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.visual_runs%ROWTYPE;
    v_asset_count integer;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.visual_runs
     WHERE id=p_visual_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RETURN false;
    END IF;

    IF v_run.completion_claimed_at IS NOT NULL THEN
        RETURN false;
    END IF;

    SELECT count(*)::integer
      INTO v_asset_count
      FROM factory.visual_assets
     WHERE visual_run_id=v_run.id;

    IF v_asset_count <> v_run.expected_shot_count THEN
        RETURN false;
    END IF;

    UPDATE factory.visual_runs
       SET completion_claimed_at=now()
     WHERE id=v_run.id;

    RETURN true;
END;
$$;


CREATE OR REPLACE FUNCTION factory.record_live_visual_search(
    p_visual_run_id uuid,
    p_shot_id uuid,
    p_provider text,
    p_query_index integer,
    p_query_text text,
    p_endpoint_kind text,
    p_http_status integer,
    p_response_headers jsonb,
    p_candidates jsonb
)
RETURNS TABLE (
    search_id uuid,
    candidate_count integer
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_http_status = 200 THEN
        PERFORM factory.put_visual_cache(
            p_provider,
            p_endpoint_kind,
            p_query_text,
            p_http_status,
            p_response_headers,
            p_candidates
        );
    END IF;

    RETURN QUERY
    SELECT *
    FROM factory.record_visual_search(
        p_visual_run_id,
        p_shot_id,
        p_provider,
        p_query_index,
        p_query_text,
        p_endpoint_kind,
        p_http_status,
        p_response_headers,
        p_candidates
    );
END;
$$;


CREATE OR REPLACE FUNCTION factory.record_live_visual_search_v2(
    p_visual_run_id uuid,
    p_shot_id uuid,
    p_provider text,
    p_query_index integer,
    p_query_text text,
    p_endpoint_kind text,
    p_http_status integer,
    p_response_headers jsonb,
    p_cache_candidates jsonb,
    p_scored_candidates jsonb
)
RETURNS TABLE (
    search_id uuid,
    candidate_count integer
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF jsonb_typeof(p_cache_candidates) <> 'array'
       OR jsonb_typeof(p_scored_candidates) <> 'array' THEN
        RAISE EXCEPTION 'visual candidate arrays are required'
            USING ERRCODE='22023';
    END IF;

    IF p_http_status = 200 THEN
        PERFORM factory.put_visual_cache(
            p_provider,
            p_endpoint_kind,
            p_query_text,
            p_http_status,
            p_response_headers,
            p_cache_candidates
        );
    END IF;

    RETURN QUERY
    SELECT *
    FROM factory.record_visual_search(
        p_visual_run_id,
        p_shot_id,
        p_provider,
        p_query_index,
        p_query_text,
        p_endpoint_kind,
        p_http_status,
        p_response_headers,
        p_scored_candidates
    );
END;
$$;

CREATE OR REPLACE FUNCTION factory.record_live_visual_search_v3(
    p_visual_run_id uuid,
    p_shot_id uuid,
    p_provider text,
    p_query_index integer,
    p_query_text text,
    p_provider_query_text text,
    p_endpoint_kind text,
    p_http_status integer,
    p_response_headers jsonb,
    p_cache_candidates jsonb,
    p_scored_candidates jsonb
)
RETURNS TABLE (
    search_id uuid,
    candidate_count integer
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_search_id uuid;
    v_candidate_count integer;
    v_provider_query_text text;
BEGIN
    v_provider_query_text := btrim(COALESCE(p_provider_query_text,''));

    IF v_provider_query_text='' THEN
        RAISE EXCEPTION 'effective visual provider query is required'
            USING ERRCODE='22023';
    END IF;

    IF jsonb_typeof(p_cache_candidates) <> 'array'
       OR jsonb_typeof(p_scored_candidates) <> 'array' THEN
        RAISE EXCEPTION 'visual candidate arrays are required'
            USING ERRCODE='22023';
    END IF;

    IF p_http_status = 200 THEN
        PERFORM factory.put_visual_cache(
            p_provider,
            p_endpoint_kind,
            v_provider_query_text,
            p_http_status,
            p_response_headers,
            p_cache_candidates
        );
    END IF;

    SELECT r.search_id,r.candidate_count
      INTO v_search_id,v_candidate_count
      FROM factory.record_visual_search(
          p_visual_run_id,
          p_shot_id,
          p_provider,
          p_query_index,
          p_query_text,
          p_endpoint_kind,
          p_http_status,
          p_response_headers,
          p_scored_candidates
      ) AS r;

    UPDATE factory.visual_searches
       SET provider_query_text=v_provider_query_text
     WHERE id=v_search_id;

    RETURN QUERY
    SELECT v_search_id,v_candidate_count;
END;
$$;
