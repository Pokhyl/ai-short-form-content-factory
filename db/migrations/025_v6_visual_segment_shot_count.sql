-- V6 variable storyboard cardinality. Existing production DB upgrade only.
BEGIN;

ALTER TABLE public.visual_segments DROP CONSTRAINT IF EXISTS visual_segments_shot_count_check;
ALTER TABLE public.visual_segments ADD CONSTRAINT visual_segments_shot_count_check
  CHECK (planned_shot_count BETWEEN 1 AND 3);

COMMIT;
