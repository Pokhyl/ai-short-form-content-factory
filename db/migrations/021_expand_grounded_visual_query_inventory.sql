BEGIN;

ALTER TABLE public.jobs
  DROP CONSTRAINT IF EXISTS jobs_visual_search_queries_en_check;

ALTER TABLE public.jobs
  ADD CONSTRAINT jobs_visual_search_queries_en_check CHECK (
    visual_search_queries_en IS NULL
    OR (
      jsonb_typeof(visual_search_queries_en) = 'array'
      AND jsonb_array_length(visual_search_queries_en) BETWEEN 6 AND 18
    )
  );

COMMIT;
