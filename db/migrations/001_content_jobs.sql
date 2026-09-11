CREATE TABLE IF NOT EXISTS content_jobs (
    job_id uuid PRIMARY KEY,
    topic text NOT NULL,
    language text NOT NULL CHECK (language IN ('en','pl','ru','uk')),
    target_duration_seconds integer NOT NULL CHECK (target_duration_seconds IN (15,30,45,60)),
    status text NOT NULL CHECK (status IN ('queued','script_ready','rendering','ready','failed','rejected')),
    video_id text UNIQUE,
    video_status text,
    output_path text,
    error_message text,
    input_payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_content_jobs_status_created
    ON content_jobs(status, created_at);
