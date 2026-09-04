BEGIN;

ALTER TABLE public.jobs
  ADD COLUMN IF NOT EXISTS visual_search_queries_en JSONB;

ALTER TABLE public.jobs
  DROP CONSTRAINT IF EXISTS jobs_visual_search_queries_en_check;

ALTER TABLE public.jobs
  ADD CONSTRAINT jobs_visual_search_queries_en_check CHECK (
    visual_search_queries_en IS NULL OR (
      jsonb_typeof(visual_search_queries_en) = 'array'
      AND jsonb_array_length(visual_search_queries_en) BETWEEN 4 AND 16
    )
  );

COMMENT ON COLUMN public.jobs.visual_search_queries_en IS
  'Grounded English visual concepts authored with the script and consumed by WF04 discovery.';

COMMIT;
