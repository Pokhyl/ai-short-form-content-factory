CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Keep n8n internal tables separate from application tables.
CREATE SCHEMA IF NOT EXISTS n8n;

CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic TEXT NOT NULL,
  language_code TEXT NOT NULL,
  target_duration_seconds INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'created',
  current_stage TEXT NOT NULL DEFAULT 'intake',
  final_video_path TEXT,
  topic_resolution JSONB,
  last_error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT jobs_topic_resolution_check CHECK (
    topic_resolution IS NULL OR (
      jsonb_typeof(topic_resolution) = 'object'
      AND topic_resolution->>'version' = 'evidence-grounded-topic-resolution-v1'
      AND NULLIF(BTRIM(topic_resolution->>'raw_topic'), '') IS NOT NULL
      AND NULLIF(BTRIM(topic_resolution->>'resolved_subject'), '') IS NOT NULL
      AND jsonb_typeof(topic_resolution->'candidates') = 'array'
      AND jsonb_array_length(topic_resolution->'candidates') >= 1
      AND jsonb_typeof(topic_resolution->'reasoning_evidence_ids') = 'array'
      AND jsonb_array_length(topic_resolution->'reasoning_evidence_ids') >= 1
    )
  )
);

CREATE TABLE IF NOT EXISTS scenes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  scene_number INTEGER NOT NULL,
  narration TEXT,
  visual_description TEXT,
  visual_query TEXT,
  visual_subject_type TEXT NOT NULL,
  audio_path TEXT,
  visual_path TEXT,
  duration_seconds NUMERIC(8, 3),
  status TEXT NOT NULL DEFAULT 'planned',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (job_id, scene_number),
  CONSTRAINT scenes_visual_subject_type_check
    CHECK (visual_subject_type IN ('factual', 'generic'))
);

CREATE TABLE IF NOT EXISTS assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scene_id UUID NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
  provider TEXT NOT NULL,
  provider_asset_id TEXT,
  source_url TEXT,
  author TEXT,
  license TEXT,
  license_url TEXT,
  local_path TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS publications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  external_id TEXT,
  external_url TEXT,
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS scenes_job_id_idx ON scenes(job_id);
CREATE INDEX IF NOT EXISTS assets_scene_id_idx ON assets(scene_id);
CREATE INDEX IF NOT EXISTS publications_job_id_idx ON publications(job_id);
