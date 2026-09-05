BEGIN;

ALTER TABLE public.jobs
  DROP CONSTRAINT IF EXISTS jobs_script_fit_passes_check;

ALTER TABLE public.jobs
  ADD CONSTRAINT jobs_script_fit_passes_check
  CHECK (script_fit_passes >= 0 AND script_fit_passes <= 2);

COMMIT;
