-- Inventory-first story contract. Existing production DB upgrade only.
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS story_package jsonb;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'jobs_story_package_check'
      AND conrelid = 'public.jobs'::regclass
  ) THEN
    ALTER TABLE public.jobs ADD CONSTRAINT jobs_story_package_check CHECK (
      story_package IS NULL OR (
        jsonb_typeof(story_package) = 'object'
        AND story_package->>'version' = 'inventory-first-story-v1'
        AND jsonb_typeof(story_package->'units') = 'array'
        AND jsonb_array_length(story_package->'units') BETWEEN 2 AND 12
        AND jsonb_typeof(story_package->'assets') = 'array'
        AND jsonb_array_length(story_package->'assets') = jsonb_array_length(story_package->'units')
      )
    );
  END IF;
END $$;

COMMENT ON COLUMN public.jobs.story_package IS
  'Inventory-first story units with explicit evidence and pre-verified visual asset bindings, frozen before TTS.';
