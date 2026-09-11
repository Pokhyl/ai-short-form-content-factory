-- V6 storyboard-first story contract. Backward-compatible production DB upgrade.
-- Preserve historical V5 and Visual-Facts V6 jobs while admitting the new representation-first storyboard contract.
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
      OR (
        story_package->>'version' = 'storyboard-first-v1'
        AND story_package->>'editorial_contract_version' = 'storyboard-v1'
        AND story_package->>'visual_binding_mode' = 'representation-first-v1'
      )
    )
  )
);

COMMENT ON COLUMN public.jobs.story_package IS
  'Frozen pre-TTS story package. Historical V5 inventory-first, V6 Visual-Facts, and V6 storyboard-first representation contracts are allowed by explicit versioned checks.';

COMMIT;
