-- V6 variable storyboard per-segment shot ordinal. Existing production DB upgrade only.
BEGIN;

ALTER TABLE public.visual_shots DROP CONSTRAINT IF EXISTS visual_shots_number_check;
ALTER TABLE public.visual_shots ADD CONSTRAINT visual_shots_number_check
  CHECK (shot_number > 0 AND segment_shot_number BETWEEN 1 AND 3);

COMMIT;
