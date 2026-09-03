BEGIN;

ALTER TABLE public.visual_shots
  DROP CONSTRAINT IF EXISTS visual_shots_score_check;

ALTER TABLE public.visual_shots
  ADD CONSTRAINT visual_shots_score_check
  CHECK (selection_score >= -0.10 AND selection_score <= 1.09);

COMMENT ON COLUMN public.visual_shots.selection_score IS
  'Deterministic semantic-v3 selection utility: local SigLIP score plus bounded metadata bonus minus representation preference penalty; current producer domain [-0.10, 1.09].';

COMMIT;
