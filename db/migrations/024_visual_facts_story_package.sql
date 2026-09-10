-- V6 Visual Facts story contract. Existing production DB upgrade only.
-- Keep V5 historical jobs valid while admitting only the explicit V6 storyboard contract.
BEGIN;

ALTER TABLE public.jobs DROP CONSTRAINT IF EXISTS jobs_story_package_check;
ALTER TABLE public.jobs ADD CONSTRAINT jobs_story_package_check CHECK (
  story_package IS NULL OR (
    jsonb_typeof(story_package) = 'object'
    AND jsonb_typeof(story_package->'units') = 'array'
    AND jsonb_array_length(story_package->'units') BETWEEN 2 AND 12
    AND jsonb_typeof(story_package->'assets') = 'array'
    AND jsonb_array_length(story_package->'assets') = jsonb_array_length(story_package->'units')
    AND (
      story_package->>'version' = 'inventory-first-story-v1'
      OR (
        story_package->>'version' = 'visual-facts-story-v1'
        AND story_package->>'editorial_contract_version' = 'storyboard-v1'
        AND story_package->>'visual_binding_mode' = 'visual-facts-first-v1'
      )
    )
  )
);

COMMENT ON COLUMN public.jobs.story_package IS
  'Frozen pre-TTS story package. Historical V5 inventory-first stories and V6 pixel-Visual-Facts storyboard stories are allowed by explicit versioned contracts.';

COMMIT;
