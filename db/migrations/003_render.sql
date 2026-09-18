ALTER TABLE public.jobs
  ADD COLUMN IF NOT EXISTS audio_duration_seconds NUMERIC(9,3),
  ADD COLUMN IF NOT EXISTS video_duration_seconds NUMERIC(9,3),
  ADD COLUMN IF NOT EXISTS visual_assets JSONB,
  ADD COLUMN IF NOT EXISTS timing_json JSONB,
  ADD COLUMN IF NOT EXISTS render_qa JSONB;
