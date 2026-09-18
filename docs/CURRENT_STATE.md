# Current State

Last verified: 2026-09-18

Read this file together with `docs/PLAN.md`, `docs/OPERATOR_RULES.md`, and `config/free-only-policy.json` before changing the project.

## Runtime

Isolated Docker project: `shorts-v2`.

Expected project containers:
- `shorts-v2-postgres-1`
- `shorts-v2-n8n-1`
- `shorts-v2-media-worker-1`

All three project containers were running after the latest deployment; PostgreSQL and media-worker were healthy and isolated n8n returned `/healthz -> {"status":"ok"}`.

The isolated n8n uses its own PostgreSQL database and data volumes. It is also attached to the private `n8n_default` Docker network only to call the two project-owned Gemini gateway workflows.

Do not restart or modify unrelated shared n8n workflows/services for this project.

## Active isolated workflows

- `ShortsV2Intake001` — WF01 Job Intake
- `ShortsV2Processor001` — WF10 Script + Final Voice
- `ShortsV2Render001` — WF20 Local Visuals + Render

WF20 runtime was exported after deployment and verified active. Its DB query loads `language`, and its media-worker request passes `language` explicitly.

Product input:
`topic + language + duration`

Allowed languages:
`en / pl / ru / uk`

Allowed durations:
`15 / 30 / 45 / 60`

## Confirmed product behavior

- Intake validates input and creates one queued DB row.
- Script generation uses only `gemini-3.5-flash-lite`.
- Each product job may reserve at most one Gemini TTS synthesis.
- Render never invokes TTS again.
- TTS provider failure marks the job failed; failed jobs are immutable.
- Exact final PCM is the source for local alignment and final audio.
- Gemini PCM is handled as signed 16-bit little-endian PCM.
- Scene timing is local with pinned `whisper.cpp` + multilingual `ggml-base`.
- Script/scenes are mapped to timed local speech tokens; no proportional timing fallback remains.
- Insufficient alignment coverage fails closed with `alignment_failed`.
- Wikimedia Commons is the visual source.
- Visual selection uses deterministic semantic scoring, context-conflict penalties, and comparison across deterministic query variants.
- Rendering and machine QA are local with FFmpeg.
- No external transcription or external visual-verification API is used.

## Existing product E2E evidence

Product job:
`d3acb20c-f6eb-4bf4-918d-4e35fcef0c93`

Previously verified:
- exactly one TTS synthesis;
- exact PCM retained;
- audio duration: 13.120 s;
- output duration recorded in the product row: 15.000 s;
- 1080x1920;
- H.264 video;
- AAC audio;
- machine QA PASS.

This product job predates the current Whisper token alignment and latest visual resolver behavior, so it is not evidence for the current M6/M7 implementation.

Another earlier machine-good product E2E remains:
`849f8952-a2c2-4037-a48b-8b80220b53b4`.

## Latest media-stage validation

Non-product diagnostic fixture:
`33333333-4444-4555-8666-777777777777`

It reused the exact PCM from successful product job `d3acb20c-f6eb-4bf4-918d-4e35fcef0c93`. It did not call Gemini text or TTS, did not create a product DB row, and did not mutate failed product jobs.

Verified with the currently deployed media worker:
- audio duration: 13.120 s;
- local alignment engine: `whisper.cpp`;
- model: multilingual `ggml-base`;
- global transcript coverage: 1.0000;
- scene coverage: 1.0000 / 1.0000 / 1.0000;
- scene boundaries: 5.820 s / 10.280 s;
- `fallback_used=false`;
- output: 1080x1920 H.264/AAC;
- container duration: 15.035 s;
- audio stream duration: 15.000 s;
- machine QA PASS under the existing ±0.08 s duration tolerance;
- final AAC was decoded and transcribed locally; normalized transcript similarity to the expected narration: 1.0000.

Selected visuals:
- scene 1: `File:Sunlight Spectrum.JPG`;
- scene 2: `File:Angular dependence of Rayleigh Scattering.jpg`;
- scene 3: `File:Blue clear sky.jpg`.

The contact sheet was visually inspected. Scene 3 is now sky-dominant; the previous hill/tree-dominant selection is no longer chosen.

## Local alignment runtime

The media-worker image is built from the official `ggml-org/whisper.cpp` container pinned by commit-tag and image digest.

Runtime model:
- file: `/data/models/ggml-base.bin`;
- size: 147951465 bytes;
- SHA-256: `60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe`.

The media-worker verifies the model SHA-256 before alignment.

## Current blocker

Gemini TTS Free Tier is currently quota-limited for the existing credential/model.

Observed provider evidence on 2026-09-18 included:
- HTTP 429 from the project-owned TTS gateway;
- Free Tier daily request limit message for the TTS model.

Do not add a paid fallback and do not retry the same failed job.

The next full fresh product E2E must use a new job only when the approved Free Tier TTS call is available again.

A controlled fresh-job retry was already made after the provider-supplied retry window and still failed. No further TTS attempts should be made until quota is available again.

## Human review

HUMAN PASS has not been recorded.

The latest contact sheet/media diagnostic is engineering evidence only. It does not replace explicit human review of a fresh normal product MP4 produced with the current code.

M10 (Studio/UI/publishing) remains blocked.

## Latest quota-failure evidence

Fresh immutable jobs:
- `af60238e-a6a0-44ce-9f8f-9bb272c99fdd` — failed, TTS count 1.
- `1ab7cce1-5b53-4fd6-a3b5-6b106c55a0ec` — failed, TTS count 1 after the controlled retry window.

These jobs remain failed and immutable.
