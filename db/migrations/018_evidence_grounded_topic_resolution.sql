BEGIN;

ALTER TABLE public.jobs
  ADD COLUMN IF NOT EXISTS topic_resolution JSONB;

ALTER TABLE public.jobs
  DROP CONSTRAINT IF EXISTS jobs_topic_resolution_check;

ALTER TABLE public.jobs
  ADD CONSTRAINT jobs_topic_resolution_check CHECK (
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
  );

COMMENT ON COLUMN public.jobs.topic_resolution IS
  'Evidence-grounded semantic interpretation selected before factual research.';

COMMIT;
