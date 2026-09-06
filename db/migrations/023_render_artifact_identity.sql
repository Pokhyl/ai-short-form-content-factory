-- Persist the exact final MP4 identity used for human review.
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS final_video_sha256 text;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'jobs_final_video_sha256_check'
      AND conrelid = 'public.jobs'::regclass
  ) THEN
    ALTER TABLE public.jobs ADD CONSTRAINT jobs_final_video_sha256_check CHECK (
      final_video_sha256 IS NULL OR final_video_sha256 ~ '^[0-9a-f]{64}$'
    );
  END IF;
END $$;

COMMENT ON COLUMN public.jobs.final_video_sha256 IS
  'SHA256 of the exact final MP4 artifact presented for human review.';
