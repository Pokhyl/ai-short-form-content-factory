# Current State

Last verified: 2026-09-18

Read this file together with `docs/PLAN.md`, `docs/OPERATOR_RULES.md`, and `config/free-only-policy.json` before changing the project.

## Runtime

Isolated Docker project: `shorts-v2`.

Expected project containers:
- `shorts-v2-postgres-1`
- `shorts-v2-n8n-1`
- `shorts-v2-media-worker-1`

The isolated n8n uses its own PostgreSQL database and data volumes. It is also attached to the private `n8n_default` Docker network only to call the two project-owned Gemini gateway workflows.

Do not restart or modify unrelated shared n8n workflows/services for this project.

## Active isolated workflows

- `ShortsV2Intake001` — WF01 Job Intake
- `ShortsV2Processor001` — WF10 Script + Final Voice
- `ShortsV2Render001` — WF20 Local Visuals + Render

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
- Exact final PCM is the source for timing and final audio.
- Scene timing is local: FFmpeg silence detection first, proportional fallback if no suitable pause is found.
- Wikimedia Commons is the visual source.
- Visual selection uses deterministic scoring, context-conflict penalties, and deterministic query fallback.
- Rendering and machine QA are local with FFmpeg.
- No external transcription or external visual-verification API is used.

## Machine-good E2E evidence

Product job:
`849f8952-a2c2-4037-a48b-8b80220b53b4`

Verified:
- exactly one TTS synthesis;
- audio duration: 12.600 s;
- output duration: 15.000 s;
- 1080x1920;
- H.264 video;
- AAC audio;
- machine QA PASS.

This job predates the latest visual resolver improvements, so it is evidence for the E2E architecture, not final visual quality.

## Latest media-stage validation

Non-product diagnostic fixture:
`11111111-2222-4333-8444-555555555555`

It reused exact PCM from an already successful product job; it did not synthesize new speech and did not mutate a failed job.

Verified with the current media worker:
- 15.000 s;
- 1080x1920;
- H.264/AAC;
- machine QA PASS;
- scene 1: `Sunlight Spectrum.JPG`;
- scene 2: `Angular dependence of Rayleigh Scattering.jpg`;
- scene 3: `Rice fields under the clear blue sky.jpg`;
- Rayleigh query fallback works;
- ordinary blue-sky imagery is preferred over eclipse/sunrise edge cases;
- scene 1 boundary aligned to a detected pause in exact PCM.

## Current blocker

Gemini TTS Free Tier is currently quota-limited for the existing credential/model.

Observed provider response on 2026-09-18:
- HTTP 429;
- model: `gemini-3.1-flash-tts`;
- reported limit: 10 requests/day on Free Tier.

Do not add a paid fallback and do not retry the same failed job.

The next full fresh E2E must use a new job only when the approved Free Tier TTS call is available again.

A controlled fresh-job retry was made after the provider-supplied retry window on 2026-09-18 and still failed with the same Free Tier TTS quota condition. No further TTS attempts should be made until the quota is available again.

## Human review

HUMAN PASS has not been recorded.

Machine QA or a contact sheet is not sufficient to mark M9 complete. The exact final MP4 must be reviewed before M10 (Studio/UI/publishing) is unblocked.

## Latest quota-failure evidence

Fresh immutable jobs:
- `af60238e-a6a0-44ce-9f8f-9bb272c99fdd` — failed, TTS count 1.
- `1ab7cce1-5b53-4fd6-a3b5-6b106c55a0ec` — failed after one controlled retry following the provider retry window, TTS count 1.

The corresponding shared Gemini gateway returned HTTP 429 with the Free Tier TTS limit message. These jobs must not be retried or resumed.
