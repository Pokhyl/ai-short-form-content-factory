BEGIN;

ALTER TABLE public.scenes
  ADD COLUMN IF NOT EXISTS visual_subject_type TEXT;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM public.scenes
    WHERE visual_subject_type IS NULL
  ) THEN
    RAISE EXCEPTION
      'Cannot enforce scenes.visual_subject_type: existing scenes require factual/generic classification';
  END IF;
END
$$;

ALTER TABLE public.scenes
  ALTER COLUMN visual_subject_type SET NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'scenes_visual_subject_type_check'
      AND conrelid = 'public.scenes'::regclass
  ) THEN
    ALTER TABLE public.scenes
      ADD CONSTRAINT scenes_visual_subject_type_check
      CHECK (visual_subject_type IN ('factual', 'generic'));
  END IF;
END
$$;

COMMIT;
