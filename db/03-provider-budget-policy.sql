-- Project-owned production safety policy for Google Cloud TTS.
-- The 90% ceiling is an internal engineering guard, not a Google recommendation.

BEGIN;

UPDATE factory.provider_budget_limits
SET internal_limit = 900000,
    enabled = true,
    updated_at = now()
WHERE provider = 'google_cloud_tts'
  AND sku_family = 'chirp3_hd'
  AND usage_unit = 'characters'
  AND free_limit = 1000000;

UPDATE factory.provider_budget_limits
SET internal_limit = 3600000,
    enabled = true,
    updated_at = now()
WHERE provider = 'google_cloud_tts'
  AND sku_family = 'wavenet'
  AND usage_unit = 'characters'
  AND free_limit = 4000000;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM factory.provider_budget_limits
        WHERE provider = 'google_cloud_tts'
          AND sku_family = 'chirp3_hd'
          AND usage_unit = 'characters'
          AND free_limit = 1000000
          AND internal_limit = 900000
          AND enabled = true
    ) THEN
        RAISE EXCEPTION 'chirp3_hd production budget policy not applied';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM factory.provider_budget_limits
        WHERE provider = 'google_cloud_tts'
          AND sku_family = 'wavenet'
          AND usage_unit = 'characters'
          AND free_limit = 4000000
          AND internal_limit = 3600000
          AND enabled = true
    ) THEN
        RAISE EXCEPTION 'wavenet production budget policy not applied';
    END IF;
END;
$$;

COMMIT;
