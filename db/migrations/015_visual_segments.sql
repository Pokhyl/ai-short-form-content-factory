BEGIN;

CREATE TABLE IF NOT EXISTS public.visual_segments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
  segment_number INTEGER NOT NULL,
  first_scene_number INTEGER NOT NULL,
  last_scene_number INTEGER NOT NULL,
  start_seconds NUMERIC NOT NULL,
  end_seconds NUMERIC NOT NULL,
  duration_seconds NUMERIC NOT NULL,
  narration TEXT NOT NULL,
  support_evidence_ids JSONB NOT NULL,
  canonical_subject TEXT NOT NULL,
  visual_target TEXT NOT NULL,
  visual_lane TEXT NOT NULL,
  visual_query TEXT NOT NULL,
  visual_description TEXT NOT NULL,
  planned_shot_count SMALLINT NOT NULL,
  status TEXT NOT NULL DEFAULT 'planned',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (job_id, segment_number),
  CONSTRAINT visual_segments_number_check CHECK (segment_number > 0 AND first_scene_number > 0 AND last_scene_number >= first_scene_number),
  CONSTRAINT visual_segments_timing_check CHECK (start_seconds >= 0 AND end_seconds > start_seconds AND duration_seconds > 0 AND abs((end_seconds - start_seconds) - duration_seconds) <= 0.02),
  CONSTRAINT visual_segments_support_check CHECK (jsonb_typeof(support_evidence_ids) = 'array' AND jsonb_array_length(support_evidence_ids) > 0),
  CONSTRAINT visual_segments_subject_check CHECK (NULLIF(BTRIM(canonical_subject), '') IS NOT NULL AND NULLIF(BTRIM(visual_target), '') IS NOT NULL),
  CONSTRAINT visual_segments_lane_check CHECK (visual_lane IN ('exact','reference','stock')),
  CONSTRAINT visual_segments_query_check CHECK (NULLIF(BTRIM(visual_query), '') IS NOT NULL AND NULLIF(BTRIM(visual_description), '') IS NOT NULL),
  CONSTRAINT visual_segments_shot_count_check CHECK (planned_shot_count BETWEEN 1 AND 2),
  CONSTRAINT visual_segments_status_check CHECK (status IN ('planned','ready'))
);
CREATE INDEX IF NOT EXISTS visual_segments_job_id_idx ON public.visual_segments(job_id);

CREATE TABLE IF NOT EXISTS public.media_library_assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider TEXT NOT NULL,
  provider_asset_id TEXT NOT NULL,
  source_url TEXT,
  author TEXT,
  license TEXT,
  license_url TEXT,
  local_path TEXT NOT NULL,
  media_kind TEXT NOT NULL,
  visual_hash TEXT NOT NULL,
  canonical_subject TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_used_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (provider, provider_asset_id),
  CONSTRAINT media_library_provider_check CHECK (NULLIF(BTRIM(provider), '') IS NOT NULL AND NULLIF(BTRIM(provider_asset_id), '') IS NOT NULL),
  CONSTRAINT media_library_path_check CHECK (NULLIF(BTRIM(local_path), '') IS NOT NULL),
  CONSTRAINT media_library_kind_check CHECK (media_kind IN ('photo','video','diagram','animation')),
  CONSTRAINT media_library_hash_check CHECK (visual_hash ~ '^[0-9a-f]{64}$'),
  CONSTRAINT media_library_subject_check CHECK (NULLIF(BTRIM(canonical_subject), '') IS NOT NULL),
  CONSTRAINT media_library_metadata_check CHECK (jsonb_typeof(metadata) = 'object')
);
CREATE INDEX IF NOT EXISTS media_library_subject_idx ON public.media_library_assets(canonical_subject);

CREATE TABLE IF NOT EXISTS public.visual_shots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
  visual_segment_id UUID NOT NULL REFERENCES public.visual_segments(id) ON DELETE CASCADE,
  shot_number INTEGER NOT NULL,
  segment_shot_number SMALLINT NOT NULL,
  start_seconds NUMERIC NOT NULL,
  end_seconds NUMERIC NOT NULL,
  duration_seconds NUMERIC NOT NULL,
  media_library_asset_id UUID NOT NULL REFERENCES public.media_library_assets(id),
  local_path TEXT NOT NULL,
  visual_cluster_key TEXT NOT NULL,
  visual_kind TEXT NOT NULL,
  selection_score NUMERIC NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (job_id, shot_number),
  UNIQUE (visual_segment_id, segment_shot_number),
  CONSTRAINT visual_shots_number_check CHECK (shot_number > 0 AND segment_shot_number BETWEEN 1 AND 2),
  CONSTRAINT visual_shots_timing_check CHECK (start_seconds >= 0 AND end_seconds > start_seconds AND duration_seconds > 0 AND abs((end_seconds - start_seconds) - duration_seconds) <= 0.02),
  CONSTRAINT visual_shots_path_check CHECK (NULLIF(BTRIM(local_path), '') IS NOT NULL),
  CONSTRAINT visual_shots_cluster_check CHECK (NULLIF(BTRIM(visual_cluster_key), '') IS NOT NULL),
  CONSTRAINT visual_shots_kind_check CHECK (visual_kind IN ('generic_broll','factual_graphic')),
  CONSTRAINT visual_shots_score_check CHECK (selection_score >= 0 AND selection_score <= 2),
  CONSTRAINT visual_shots_metadata_check CHECK (jsonb_typeof(metadata) = 'object')
);
CREATE INDEX IF NOT EXISTS visual_shots_job_id_idx ON public.visual_shots(job_id);
CREATE INDEX IF NOT EXISTS visual_shots_segment_id_idx ON public.visual_shots(visual_segment_id);

COMMIT;
