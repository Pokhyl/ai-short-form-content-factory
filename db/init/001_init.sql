CREATE SCHEMA IF NOT EXISTS n8n;

CREATE TABLE IF NOT EXISTS public.jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic TEXT NOT NULL,
  language TEXT NOT NULL CHECK (language IN ('en','pl','ru','uk')),
  target_duration_seconds INTEGER NOT NULL CHECK (target_duration_seconds IN (15,30,45,60)),
  status TEXT NOT NULL DEFAULT 'queued',
  script_text TEXT,
  audio_path TEXT,
  video_path TEXT,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
