-- M4 research/evidence persistence.
-- Research is evidence-first and fail-closed. M5 may only consume jobs whose
-- status is evidence_ready.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS factory.research_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL UNIQUE REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    status text NOT NULL DEFAULT 'running',
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    failure_reason text,

    CONSTRAINT research_runs_status
        CHECK (status IN ('running', 'passed', 'failed')),
    CONSTRAINT research_runs_completion
        CHECK (
            (status = 'running' AND completed_at IS NULL)
            OR
            (status IN ('passed','failed') AND completed_at IS NOT NULL)
        )
);

CREATE TABLE IF NOT EXISTS factory.evidence (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL REFERENCES factory.jobs(id) ON DELETE RESTRICT,
    research_run_id uuid NOT NULL REFERENCES factory.research_runs(id) ON DELETE RESTRICT,
    search_query text NOT NULL,
    search_rank integer NOT NULL,
    search_engines jsonb NOT NULL DEFAULT '[]'::jsonb,
    source_url text NOT NULL,
    canonical_url text NOT NULL,
    source_domain text NOT NULL,
    title text NOT NULL,
    snippet text NOT NULL DEFAULT '',
    content_text text NOT NULL,
    content_sha256 text NOT NULL,
    source_http_status integer NOT NULL,
    source_content_type text NOT NULL,
    retrieved_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT evidence_search_rank_positive CHECK (search_rank >= 1),
    CONSTRAINT evidence_domain_nonempty CHECK (char_length(btrim(source_domain)) > 0),
    CONSTRAINT evidence_url_nonempty CHECK (char_length(btrim(canonical_url)) > 0),
    CONSTRAINT evidence_title_nonempty CHECK (char_length(btrim(title)) > 0),
    CONSTRAINT evidence_content_minimum CHECK (char_length(content_text) >= 500),
    CONSTRAINT evidence_http_success CHECK (source_http_status BETWEEN 200 AND 299),
    CONSTRAINT evidence_sha256_shape CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    UNIQUE (job_id, canonical_url),
    UNIQUE (job_id, content_sha256)
);

CREATE INDEX IF NOT EXISTS evidence_job_domain_idx
    ON factory.evidence (job_id, source_domain);

CREATE INDEX IF NOT EXISTS evidence_run_rank_idx
    ON factory.evidence (research_run_id, search_rank);

CREATE OR REPLACE FUNCTION factory.begin_research(
    p_job_id uuid
)
RETURNS TABLE (
    research_run_id uuid,
    topic text,
    language_code text
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_job factory.jobs%ROWTYPE;
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

    IF v_job.status <> 'created' THEN
        RAISE EXCEPTION 'job is not researchable from status %', v_job.status
            USING ERRCODE = '22023';
    END IF;

    INSERT INTO factory.research_runs (job_id, status)
    VALUES (p_job_id, 'running')
    RETURNING id INTO v_run_id;

    UPDATE factory.jobs
       SET status = 'researching',
           updated_at = now()
     WHERE id = p_job_id;

    RETURN QUERY
    SELECT v_run_id, v_job.topic, v_job.language_code;
END;
$$;

CREATE OR REPLACE FUNCTION factory.store_evidence(
    p_research_run_id uuid,
    p_search_query text,
    p_search_rank integer,
    p_search_engines jsonb,
    p_source_url text,
    p_canonical_url text,
    p_source_domain text,
    p_title text,
    p_snippet text,
    p_content_text text,
    p_source_http_status integer,
    p_source_content_type text
)
RETURNS TABLE (
    evidence_id uuid,
    inserted boolean
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.research_runs%ROWTYPE;
    v_content text;
    v_hash text;
    v_id uuid;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.research_runs
     WHERE id = p_research_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'research run is not active'
            USING ERRCODE = '22023';
    END IF;

    v_content := regexp_replace(btrim(COALESCE(p_content_text, '')), '[[:space:]]+', ' ', 'g');

    IF char_length(v_content) < 500 THEN
        RETURN QUERY SELECT NULL::uuid, false;
        RETURN;
    END IF;

    IF p_source_http_status < 200 OR p_source_http_status > 299 THEN
        RETURN QUERY SELECT NULL::uuid, false;
        RETURN;
    END IF;

    v_hash := encode(digest(convert_to(v_content, 'UTF8'), 'sha256'), 'hex');

    INSERT INTO factory.evidence (
        job_id,
        research_run_id,
        search_query,
        search_rank,
        search_engines,
        source_url,
        canonical_url,
        source_domain,
        title,
        snippet,
        content_text,
        content_sha256,
        source_http_status,
        source_content_type
    )
    VALUES (
        v_run.job_id,
        v_run.id,
        btrim(p_search_query),
        p_search_rank,
        COALESCE(p_search_engines, '[]'::jsonb),
        btrim(p_source_url),
        btrim(p_canonical_url),
        lower(btrim(p_source_domain)),
        btrim(p_title),
        btrim(COALESCE(p_snippet, '')),
        v_content,
        v_hash,
        p_source_http_status,
        btrim(p_source_content_type)
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_id;

    RETURN QUERY
    SELECT v_id, (v_id IS NOT NULL);
END;
$$;

CREATE OR REPLACE FUNCTION factory.finalize_research(
    p_research_run_id uuid,
    p_min_evidence integer DEFAULT 3,
    p_min_domains integer DEFAULT 3
)
RETURNS TABLE (
    research_status text,
    evidence_count integer,
    independent_domain_count integer
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.research_runs%ROWTYPE;
    v_evidence_count integer;
    v_domain_count integer;
BEGIN
    IF p_min_evidence < 1 OR p_min_domains < 1 THEN
        RAISE EXCEPTION 'minimum thresholds must be positive'
            USING ERRCODE = '22023';
    END IF;

    SELECT *
      INTO v_run
      FROM factory.research_runs
     WHERE id = p_research_run_id
     FOR UPDATE;

    IF NOT FOUND OR v_run.status <> 'running' THEN
        RAISE EXCEPTION 'research run is not active'
            USING ERRCODE = '22023';
    END IF;

    SELECT count(*), count(DISTINCT source_domain)
      INTO v_evidence_count, v_domain_count
      FROM factory.evidence
     WHERE research_run_id = p_research_run_id;

    IF v_evidence_count >= p_min_evidence
       AND v_domain_count >= p_min_domains THEN
        UPDATE factory.research_runs
           SET status = 'passed',
               completed_at = now(),
               failure_reason = NULL
         WHERE id = p_research_run_id;

        UPDATE factory.jobs
           SET status = 'evidence_ready',
               updated_at = now()
         WHERE id = v_run.job_id;

        RETURN QUERY
        SELECT 'passed'::text, v_evidence_count, v_domain_count;
    ELSE
        UPDATE factory.research_runs
           SET status = 'failed',
               completed_at = now(),
               failure_reason = format(
                   'insufficient evidence: %s rows / %s independent domains; required %s / %s',
                   v_evidence_count,
                   v_domain_count,
                   p_min_evidence,
                   p_min_domains
               )
         WHERE id = p_research_run_id;

        UPDATE factory.jobs
           SET status = 'research_failed',
               updated_at = now()
         WHERE id = v_run.job_id;

        RETURN QUERY
        SELECT 'failed'::text, v_evidence_count, v_domain_count;
    END IF;
END;
$$;


CREATE OR REPLACE FUNCTION factory.fail_research(
    p_research_run_id uuid,
    p_reason text
)
RETURNS TABLE (
    research_status text,
    job_status text
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run factory.research_runs%ROWTYPE;
    v_job_status text;
BEGIN
    SELECT *
      INTO v_run
      FROM factory.research_runs
     WHERE id = p_research_run_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'research run not found'
            USING ERRCODE = '22023';
    END IF;

    IF v_run.status = 'passed' THEN
        RAISE EXCEPTION 'passed research run cannot be failed'
            USING ERRCODE = '22023';
    END IF;

    IF v_run.status = 'running' THEN
        UPDATE factory.research_runs
           SET status = 'failed',
               completed_at = now(),
               failure_reason = left(
                   COALESCE(NULLIF(btrim(p_reason), ''), 'unspecified research failure'),
                   4000
               )
         WHERE id = p_research_run_id;

        UPDATE factory.jobs
           SET status = 'research_failed',
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
