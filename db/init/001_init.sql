-- Fresh database baseline reconciled against production on 2026-09-06.
-- For a NEW database only. Existing production volumes are not reinitialized.
-- Historical migrations through 021 are already incorporated; see db/README.md.
--
-- PostgreSQL database dump
--


-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS n8n;
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: assets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.assets (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    scene_id uuid NOT NULL,
    provider text NOT NULL,
    provider_asset_id text,
    source_url text,
    author text,
    license text,
    license_url text,
    local_path text,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: job_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.job_evidence (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    job_id uuid NOT NULL,
    evidence_id text NOT NULL,
    source_id text NOT NULL,
    source_language text NOT NULL,
    source_title text NOT NULL,
    source_url text,
    passage_id text NOT NULL,
    section text,
    evidence_text text NOT NULL,
    selection_score numeric,
    selection_rank integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT job_evidence_evidence_id_check CHECK ((NULLIF(btrim(evidence_id), ''::text) IS NOT NULL)),
    CONSTRAINT job_evidence_passage_id_check CHECK ((NULLIF(btrim(passage_id), ''::text) IS NOT NULL)),
    CONSTRAINT job_evidence_selection_rank_check CHECK ((selection_rank > 0)),
    CONSTRAINT job_evidence_source_id_check CHECK ((NULLIF(btrim(source_id), ''::text) IS NOT NULL)),
    CONSTRAINT job_evidence_source_language_check CHECK ((source_language = ANY (ARRAY['en'::text, 'pl'::text, 'ru'::text, 'uk'::text]))),
    CONSTRAINT job_evidence_source_title_check CHECK ((NULLIF(btrim(source_title), ''::text) IS NOT NULL)),
    CONSTRAINT job_evidence_text_check CHECK ((NULLIF(btrim(evidence_text), ''::text) IS NOT NULL))
);


--
-- Name: jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.jobs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    topic text NOT NULL,
    language_code text NOT NULL,
    target_duration_seconds integer NOT NULL,
    status text DEFAULT 'created'::text NOT NULL,
    current_stage text DEFAULT 'intake'::text NOT NULL,
    final_video_path text,
    final_video_sha256 text,
    last_error text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    content_model_version text DEFAULT 'beat_v2'::text NOT NULL,
    script_text text,
    voiceover_path text,
    voiceover_duration_seconds numeric(8,3),
    voiceover_provider text,
    voiceover_model text,
    voiceover_voice text,
    review_decision text,
    review_notes text,
    reviewed_at timestamp with time zone,
    fact_source_language text,
    fact_primary_title text,
    script_support jsonb,
    narration_engine text,
    narration_model text,
    narration_prompt_version text,
    duration_preflight jsonb,
    script_fit_passes smallint DEFAULT 0 NOT NULL,
    visual_quality jsonb,
    topic_resolution jsonb,
    visual_search_queries_en jsonb,
    story_package jsonb,
    CONSTRAINT jobs_content_model_version_check CHECK ((content_model_version = ANY (ARRAY['scene_v1'::text, 'beat_v2'::text, 'staged_v1'::text]))),
    CONSTRAINT jobs_duration_preflight_check CHECK (((duration_preflight IS NULL) OR (jsonb_typeof(duration_preflight) = 'object'::text))),
    CONSTRAINT jobs_final_video_sha256_check CHECK (((final_video_sha256 IS NULL) OR (final_video_sha256 ~ '^[0-9a-f]{64}$'::text))),
    CONSTRAINT jobs_fact_source_check CHECK ((((fact_source_language IS NULL) AND (fact_primary_title IS NULL)) OR ((fact_source_language IS NOT NULL) AND (fact_primary_title IS NOT NULL) AND (fact_source_language = ANY (ARRAY['en'::text, 'pl'::text, 'ru'::text, 'uk'::text])) AND (NULLIF(btrim(fact_primary_title), ''::text) IS NOT NULL)))),
    CONSTRAINT jobs_review_state_check CHECK ((((review_decision IS NULL) AND (review_notes IS NULL) AND (reviewed_at IS NULL)) OR ((review_decision = ANY (ARRAY['approved'::text, 'rejected'::text])) AND (reviewed_at IS NOT NULL)))),
    CONSTRAINT jobs_script_fit_passes_check CHECK (((script_fit_passes >= 0) AND (script_fit_passes <= 3))),
    CONSTRAINT jobs_script_support_check CHECK (((script_support IS NULL) OR (jsonb_typeof(script_support) = 'array'::text))),
    CONSTRAINT jobs_story_package_check CHECK (((story_package IS NULL) OR ((jsonb_typeof(story_package) = 'object'::text) AND ((story_package ->> 'version'::text) = 'inventory-first-story-v1'::text) AND (jsonb_typeof((story_package -> 'units'::text)) = 'array'::text) AND (jsonb_array_length((story_package -> 'units'::text)) BETWEEN 2 AND 12) AND (jsonb_typeof((story_package -> 'assets'::text)) = 'array'::text) AND (jsonb_array_length((story_package -> 'assets'::text)) = jsonb_array_length((story_package -> 'units'::text)))))),
    CONSTRAINT jobs_topic_resolution_check CHECK (((topic_resolution IS NULL) OR ((jsonb_typeof(topic_resolution) = 'object'::text) AND ((topic_resolution ->> 'version'::text) = 'evidence-grounded-topic-resolution-v1'::text) AND (NULLIF(btrim((topic_resolution ->> 'raw_topic'::text)), ''::text) IS NOT NULL) AND (NULLIF(btrim((topic_resolution ->> 'resolved_subject'::text)), ''::text) IS NOT NULL) AND (jsonb_typeof((topic_resolution -> 'candidates'::text)) = 'array'::text) AND (jsonb_array_length((topic_resolution -> 'candidates'::text)) >= 1) AND (jsonb_typeof((topic_resolution -> 'reasoning_evidence_ids'::text)) = 'array'::text) AND (jsonb_array_length((topic_resolution -> 'reasoning_evidence_ids'::text)) >= 1)))),
    CONSTRAINT jobs_visual_quality_check CHECK (((visual_quality IS NULL) OR (jsonb_typeof(visual_quality) = 'object'::text))),
    CONSTRAINT jobs_visual_search_queries_en_check CHECK (((visual_search_queries_en IS NULL) OR ((jsonb_typeof(visual_search_queries_en) = 'array'::text) AND ((jsonb_array_length(visual_search_queries_en) >= 6) AND (jsonb_array_length(visual_search_queries_en) <= 18)))))
);



COMMENT ON COLUMN public.jobs.final_video_sha256 IS 'SHA256 of the exact final MP4 artifact presented for human review.';

--
-- Name: COLUMN jobs.topic_resolution; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.jobs.topic_resolution IS 'Evidence-grounded semantic interpretation selected before factual research.';


--
-- Name: COLUMN jobs.visual_search_queries_en; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.jobs.visual_search_queries_en IS 'Grounded English visual concepts authored with the script and consumed by WF04 discovery.';


--
-- Name: COLUMN jobs.story_package; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.jobs.story_package IS 'Inventory-first story units with explicit evidence and pre-verified visual asset bindings, frozen before TTS.';


--
-- Name: media_library_assets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.media_library_assets (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    provider text NOT NULL,
    provider_asset_id text NOT NULL,
    source_url text,
    author text,
    license text,
    license_url text,
    local_path text NOT NULL,
    media_kind text NOT NULL,
    visual_hash text NOT NULL,
    canonical_subject text NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    last_used_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT media_library_hash_check CHECK ((visual_hash ~ '^[0-9a-f]{64}$'::text)),
    CONSTRAINT media_library_kind_check CHECK ((media_kind = ANY (ARRAY['photo'::text, 'video'::text, 'diagram'::text, 'animation'::text]))),
    CONSTRAINT media_library_metadata_check CHECK ((jsonb_typeof(metadata) = 'object'::text)),
    CONSTRAINT media_library_path_check CHECK ((NULLIF(btrim(local_path), ''::text) IS NOT NULL)),
    CONSTRAINT media_library_provider_check CHECK (((NULLIF(btrim(provider), ''::text) IS NOT NULL) AND (NULLIF(btrim(provider_asset_id), ''::text) IS NOT NULL))),
    CONSTRAINT media_library_subject_check CHECK ((NULLIF(btrim(canonical_subject), ''::text) IS NOT NULL))
);


--
-- Name: publications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.publications (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    job_id uuid NOT NULL,
    platform text NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    external_id text,
    external_url text,
    published_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: scenes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scenes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    job_id uuid NOT NULL,
    scene_number integer NOT NULL,
    narration text,
    visual_description text,
    visual_query text,
    audio_path text,
    visual_path text,
    duration_seconds numeric(8,3),
    status text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    visual_subject_type text,
    visual_kind text,
    exact_subject text,
    beat_start_seconds numeric(8,3),
    beat_end_seconds numeric(8,3),
    visual_evidence_type text,
    exact_subject_type text,
    visual_target text,
    fallback_visual_query text,
    fallback_visual_description text,
    fallback_visual_target text,
    reference_query text,
    concrete_subject text,
    reference_media_kind text,
    narration_support_evidence_ids jsonb,
    visual_support_evidence_ids jsonb,
    CONSTRAINT scenes_concrete_subject_check CHECK (((concrete_subject IS NULL) OR ((NULLIF(btrim(concrete_subject), ''::text) IS NOT NULL) AND (visual_evidence_type <> 'exact_subject'::text)))),
    CONSTRAINT scenes_exact_subject_type_check CHECK ((exact_subject_type = ANY (ARRAY['person'::text, 'company'::text, 'place'::text, 'event'::text, 'product'::text, 'none'::text]))),
    CONSTRAINT scenes_narration_support_evidence_ids_check CHECK (((narration_support_evidence_ids IS NULL) OR ((jsonb_typeof(narration_support_evidence_ids) = 'array'::text) AND (jsonb_array_length(narration_support_evidence_ids) > 0)))),
    CONSTRAINT scenes_reference_media_kind_check CHECK (((reference_media_kind IS NULL) OR (reference_media_kind = ANY (ARRAY['diagram'::text, 'animation'::text, 'photo'::text])))),
    CONSTRAINT scenes_visual_evidence_type_check CHECK ((visual_evidence_type = ANY (ARRAY['exact_subject'::text, 'technical_reference'::text, 'stock_footage'::text]))),
    CONSTRAINT scenes_visual_intent_consistency_check CHECK ((((visual_evidence_type = 'exact_subject'::text) AND (exact_subject_type = ANY (ARRAY['person'::text, 'company'::text, 'place'::text, 'event'::text, 'product'::text])) AND (NULLIF(btrim(exact_subject), ''::text) IS NOT NULL) AND (NULLIF(btrim(COALESCE(reference_query, ''::text)), ''::text) IS NULL)) OR ((visual_evidence_type = 'technical_reference'::text) AND (exact_subject_type = 'none'::text) AND (NULLIF(btrim(COALESCE(exact_subject, ''::text)), ''::text) IS NULL) AND (NULLIF(btrim(reference_query), ''::text) IS NOT NULL)) OR ((visual_evidence_type = 'stock_footage'::text) AND (exact_subject_type = 'none'::text) AND (NULLIF(btrim(COALESCE(exact_subject, ''::text)), ''::text) IS NULL) AND (NULLIF(btrim(COALESCE(reference_query, ''::text)), ''::text) IS NULL)))),
    CONSTRAINT scenes_visual_kind_check CHECK ((visual_kind = ANY (ARRAY['exact_person'::text, 'exact_company'::text, 'exact_place'::text, 'exact_event'::text, 'exact_product'::text, 'factual_graphic'::text, 'generic_broll'::text]))),
    CONSTRAINT scenes_visual_subject_type_check CHECK ((visual_subject_type = ANY (ARRAY['factual'::text, 'generic'::text]))),
    CONSTRAINT scenes_visual_support_evidence_ids_check CHECK (((visual_support_evidence_ids IS NULL) OR (jsonb_typeof(visual_support_evidence_ids) = 'array'::text)))
);


--
-- Name: visual_segments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.visual_segments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    job_id uuid NOT NULL,
    segment_number integer NOT NULL,
    first_scene_number integer NOT NULL,
    last_scene_number integer NOT NULL,
    start_seconds numeric NOT NULL,
    end_seconds numeric NOT NULL,
    duration_seconds numeric NOT NULL,
    narration text NOT NULL,
    support_evidence_ids jsonb NOT NULL,
    canonical_subject text NOT NULL,
    visual_target text NOT NULL,
    visual_lane text NOT NULL,
    visual_query text NOT NULL,
    visual_description text NOT NULL,
    planned_shot_count smallint NOT NULL,
    status text DEFAULT 'planned'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT visual_segments_lane_check CHECK ((visual_lane = ANY (ARRAY['exact'::text, 'reference'::text, 'stock'::text]))),
    CONSTRAINT visual_segments_number_check CHECK (((segment_number > 0) AND (first_scene_number > 0) AND (last_scene_number >= first_scene_number))),
    CONSTRAINT visual_segments_query_check CHECK (((NULLIF(btrim(visual_query), ''::text) IS NOT NULL) AND (NULLIF(btrim(visual_description), ''::text) IS NOT NULL))),
    CONSTRAINT visual_segments_shot_count_check CHECK (((planned_shot_count >= 1) AND (planned_shot_count <= 2))),
    CONSTRAINT visual_segments_status_check CHECK ((status = ANY (ARRAY['planned'::text, 'ready'::text]))),
    CONSTRAINT visual_segments_subject_check CHECK (((NULLIF(btrim(canonical_subject), ''::text) IS NOT NULL) AND (NULLIF(btrim(visual_target), ''::text) IS NOT NULL))),
    CONSTRAINT visual_segments_support_check CHECK (((jsonb_typeof(support_evidence_ids) = 'array'::text) AND (jsonb_array_length(support_evidence_ids) > 0))),
    CONSTRAINT visual_segments_timing_check CHECK (((start_seconds >= (0)::numeric) AND (end_seconds > start_seconds) AND (duration_seconds > (0)::numeric) AND (abs(((end_seconds - start_seconds) - duration_seconds)) <= 0.02)))
);


--
-- Name: visual_shots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.visual_shots (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    job_id uuid NOT NULL,
    visual_segment_id uuid NOT NULL,
    shot_number integer NOT NULL,
    segment_shot_number smallint NOT NULL,
    start_seconds numeric NOT NULL,
    end_seconds numeric NOT NULL,
    duration_seconds numeric NOT NULL,
    media_library_asset_id uuid NOT NULL,
    local_path text NOT NULL,
    visual_cluster_key text NOT NULL,
    visual_kind text NOT NULL,
    selection_score numeric NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT visual_shots_cluster_check CHECK ((NULLIF(btrim(visual_cluster_key), ''::text) IS NOT NULL)),
    CONSTRAINT visual_shots_kind_check CHECK ((visual_kind = ANY (ARRAY['generic_broll'::text, 'factual_graphic'::text, 'factual_image'::text, 'context_video'::text]))),
    CONSTRAINT visual_shots_metadata_check CHECK ((jsonb_typeof(metadata) = 'object'::text)),
    CONSTRAINT visual_shots_number_check CHECK (((shot_number > 0) AND ((segment_shot_number >= 1) AND (segment_shot_number <= 2)))),
    CONSTRAINT visual_shots_path_check CHECK ((NULLIF(btrim(local_path), ''::text) IS NOT NULL)),
    CONSTRAINT visual_shots_score_check CHECK (((selection_score >= '-0.10'::numeric) AND (selection_score <= 1.09))),
    CONSTRAINT visual_shots_timing_check CHECK (((start_seconds >= (0)::numeric) AND (end_seconds > start_seconds) AND (duration_seconds > (0)::numeric) AND (abs(((end_seconds - start_seconds) - duration_seconds)) <= 0.02)))
);


--
-- Name: COLUMN visual_shots.selection_score; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.visual_shots.selection_score IS 'Deterministic semantic-v3 selection utility: local SigLIP score plus bounded metadata bonus minus representation preference penalty; current producer domain [-0.10, 1.09].';


--
-- Name: assets assets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_pkey PRIMARY KEY (id);


--
-- Name: job_evidence job_evidence_job_id_evidence_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_evidence
    ADD CONSTRAINT job_evidence_job_id_evidence_id_key UNIQUE (job_id, evidence_id);


--
-- Name: job_evidence job_evidence_job_id_selection_rank_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_evidence
    ADD CONSTRAINT job_evidence_job_id_selection_rank_key UNIQUE (job_id, selection_rank);


--
-- Name: job_evidence job_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_evidence
    ADD CONSTRAINT job_evidence_pkey PRIMARY KEY (id);


--
-- Name: jobs jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);


--
-- Name: media_library_assets media_library_assets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.media_library_assets
    ADD CONSTRAINT media_library_assets_pkey PRIMARY KEY (id);


--
-- Name: media_library_assets media_library_assets_provider_provider_asset_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.media_library_assets
    ADD CONSTRAINT media_library_assets_provider_provider_asset_id_key UNIQUE (provider, provider_asset_id);


--
-- Name: publications publications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publications
    ADD CONSTRAINT publications_pkey PRIMARY KEY (id);


--
-- Name: scenes scenes_job_id_scene_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenes
    ADD CONSTRAINT scenes_job_id_scene_number_key UNIQUE (job_id, scene_number);


--
-- Name: scenes scenes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenes
    ADD CONSTRAINT scenes_pkey PRIMARY KEY (id);


--
-- Name: scenes scenes_reference_media_kind_consistency_check; Type: CHECK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.scenes
    ADD CONSTRAINT scenes_reference_media_kind_consistency_check CHECK ((((visual_evidence_type = 'technical_reference'::text) AND ((status = 'visual_planned'::text) OR (reference_media_kind IS NOT NULL))) OR ((visual_evidence_type <> 'technical_reference'::text) AND (reference_media_kind IS NULL)))) NOT VALID;


--
-- Name: scenes scenes_staged_pipeline_contract_check; Type: CHECK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.scenes
    ADD CONSTRAINT scenes_staged_pipeline_contract_check CHECK (((status <> ALL (ARRAY['timed'::text, 'visual_planned'::text, 'visual_ready'::text])) OR ((NULLIF(btrim(COALESCE(narration, ''::text)), ''::text) IS NOT NULL) AND (beat_start_seconds IS NOT NULL) AND (beat_end_seconds IS NOT NULL) AND (duration_seconds IS NOT NULL) AND (beat_start_seconds >= (0)::numeric) AND (beat_end_seconds > beat_start_seconds) AND (duration_seconds > (0)::numeric) AND (abs(((beat_end_seconds - beat_start_seconds) - duration_seconds)) <= 0.01) AND (narration_support_evidence_ids IS NOT NULL) AND (jsonb_typeof(narration_support_evidence_ids) = 'array'::text) AND (jsonb_array_length(narration_support_evidence_ids) > 0) AND (((status = 'timed'::text) AND (visual_description IS NULL) AND (visual_query IS NULL) AND (reference_query IS NULL) AND (reference_media_kind IS NULL) AND (concrete_subject IS NULL) AND (visual_subject_type IS NULL) AND (visual_kind IS NULL) AND (visual_evidence_type IS NULL) AND (exact_subject_type IS NULL) AND (visual_target IS NULL) AND (exact_subject IS NULL) AND (visual_support_evidence_ids IS NULL) AND (visual_path IS NULL)) OR ((status = ANY (ARRAY['visual_planned'::text, 'visual_ready'::text])) AND (NULLIF(btrim(COALESCE(visual_description, ''::text)), ''::text) IS NOT NULL) AND (NULLIF(btrim(COALESCE(visual_query, ''::text)), ''::text) IS NOT NULL) AND (visual_subject_type = ANY (ARRAY['factual'::text, 'generic'::text])) AND (visual_kind = ANY (ARRAY['exact_person'::text, 'exact_company'::text, 'exact_place'::text, 'exact_event'::text, 'exact_product'::text, 'factual_graphic'::text, 'generic_broll'::text])) AND (visual_evidence_type = ANY (ARRAY['exact_subject'::text, 'technical_reference'::text, 'stock_footage'::text])) AND (exact_subject_type = ANY (ARRAY['person'::text, 'company'::text, 'place'::text, 'event'::text, 'product'::text, 'none'::text])) AND (NULLIF(btrim(COALESCE(visual_target, ''::text)), ''::text) IS NOT NULL) AND (visual_support_evidence_ids IS NOT NULL) AND (jsonb_typeof(visual_support_evidence_ids) = 'array'::text) AND (jsonb_array_length(visual_support_evidence_ids) > 0) AND ((status <> 'visual_ready'::text) OR (NULLIF(btrim(COALESCE(visual_path, ''::text)), ''::text) IS NOT NULL))))))) NOT VALID;


--
-- Name: scenes scenes_status_check; Type: CHECK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.scenes
    ADD CONSTRAINT scenes_status_check CHECK ((status = ANY (ARRAY['planned'::text, 'timed'::text, 'visual_planned'::text, 'visual_ready'::text]))) NOT VALID;


--
-- Name: visual_segments visual_segments_job_id_segment_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visual_segments
    ADD CONSTRAINT visual_segments_job_id_segment_number_key UNIQUE (job_id, segment_number);


--
-- Name: visual_segments visual_segments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visual_segments
    ADD CONSTRAINT visual_segments_pkey PRIMARY KEY (id);


--
-- Name: visual_shots visual_shots_job_id_shot_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visual_shots
    ADD CONSTRAINT visual_shots_job_id_shot_number_key UNIQUE (job_id, shot_number);


--
-- Name: visual_shots visual_shots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visual_shots
    ADD CONSTRAINT visual_shots_pkey PRIMARY KEY (id);


--
-- Name: visual_shots visual_shots_visual_segment_id_segment_shot_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visual_shots
    ADD CONSTRAINT visual_shots_visual_segment_id_segment_shot_number_key UNIQUE (visual_segment_id, segment_shot_number);


--
-- Name: assets_scene_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX assets_scene_id_idx ON public.assets USING btree (scene_id);


--
-- Name: job_evidence_job_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX job_evidence_job_id_idx ON public.job_evidence USING btree (job_id);


--
-- Name: media_library_subject_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX media_library_subject_idx ON public.media_library_assets USING btree (canonical_subject);


--
-- Name: publications_job_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX publications_job_id_idx ON public.publications USING btree (job_id);


--
-- Name: scenes_job_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX scenes_job_id_idx ON public.scenes USING btree (job_id);


--
-- Name: visual_segments_job_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX visual_segments_job_id_idx ON public.visual_segments USING btree (job_id);


--
-- Name: visual_shots_job_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX visual_shots_job_id_idx ON public.visual_shots USING btree (job_id);


--
-- Name: visual_shots_segment_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX visual_shots_segment_id_idx ON public.visual_shots USING btree (visual_segment_id);


--
-- Name: assets assets_scene_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_scene_id_fkey FOREIGN KEY (scene_id) REFERENCES public.scenes(id) ON DELETE CASCADE;


--
-- Name: job_evidence job_evidence_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_evidence
    ADD CONSTRAINT job_evidence_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(id) ON DELETE CASCADE;


--
-- Name: publications publications_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publications
    ADD CONSTRAINT publications_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(id) ON DELETE CASCADE;


--
-- Name: scenes scenes_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenes
    ADD CONSTRAINT scenes_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(id) ON DELETE CASCADE;


--
-- Name: visual_segments visual_segments_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visual_segments
    ADD CONSTRAINT visual_segments_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(id) ON DELETE CASCADE;


--
-- Name: visual_shots visual_shots_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visual_shots
    ADD CONSTRAINT visual_shots_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(id) ON DELETE CASCADE;


--
-- Name: visual_shots visual_shots_media_library_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visual_shots
    ADD CONSTRAINT visual_shots_media_library_asset_id_fkey FOREIGN KEY (media_library_asset_id) REFERENCES public.media_library_assets(id);


--
-- Name: visual_shots visual_shots_visual_segment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visual_shots
    ADD CONSTRAINT visual_shots_visual_segment_id_fkey FOREIGN KEY (visual_segment_id) REFERENCES public.visual_segments(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--
