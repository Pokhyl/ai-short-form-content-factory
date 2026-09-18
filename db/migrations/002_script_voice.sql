ALTER TABLE public.jobs
  ADD COLUMN IF NOT EXISTS script_json JSONB,
  ADD COLUMN IF NOT EXISTS tts_synthesis_count INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS audio_sample_rate INTEGER,
  ADD COLUMN IF NOT EXISTS audio_channels INTEGER,
  ADD COLUMN IF NOT EXISTS audio_mime_type TEXT;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'jobs_tts_synthesis_count_check'
      AND conrelid = 'public.jobs'::regclass
  ) THEN
    ALTER TABLE public.jobs
      ADD CONSTRAINT jobs_tts_synthesis_count_check
      CHECK (tts_synthesis_count BETWEEN 0 AND 1);
  END IF;
END
$$;
