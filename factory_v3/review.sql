-- User decisions are immutable and bound to an actual machine-passed MP4.
CREATE TABLE IF NOT EXISTS factory_v3.human_reviews (
 job_id uuid PRIMARY KEY REFERENCES factory_v3.jobs(id),
 video_sha256 text NOT NULL CHECK(video_sha256 ~ '^[0-9a-f]{64}$'),
 decision text NOT NULL CHECK(decision IN ('accepted','rejected')),
 comment text NOT NULL CHECK(char_length(comment)<=2000),
 created_at timestamptz NOT NULL DEFAULT now()
);
