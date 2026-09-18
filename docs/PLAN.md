# Production Plan — Clean Rebuild

Last updated: 2026-09-18

This file is the execution source of truth for the clean rebuild.

Before every meaningful change:
1. read this file;
2. read `config/free-only-policy.json`;
3. verify the change stays inside this repository and the isolated `shorts-v2` runtime;
4. do not touch other projects.

## Non-negotiable constraints

- n8n is the orchestrator.
- Production must be free-only.
- No paid API, paid fallback, hidden billing dependency, or provider added without verified Free Tier evidence.
- Allowed external AI:
  - Gemini text: `gemini-3.5-flash-lite`
  - Gemini TTS: `gemini-3.1-flash-tts-preview`
- Exactly one successful final TTS synthesis per job.
- No external transcription API.
- No external visual-verification API.
- Speech timing/alignment is local.
- Visual verification is local/deterministic.
- Rendering is local.
- Visual sourcing starts with Wikimedia Commons.
- Inputs are only: topic, language, duration.
- Languages: en / pl / ru / uk.
- Durations: 15 / 30 / 45 / 60 seconds.
- Output: one 9:16 MP4.
- No Studio/UI/publishing work until one real end-to-end MP4 passes human review.
- Do not repair or resume failed product jobs; create a new job.
- Never modify unrelated n8n instances, databases, containers, repositories, credentials, domains, or files.

## Delivery order

### M0 — Clean reset
Status: DONE

- Old project runtime removed.
- GitHub repository reset.
- Free-only policy committed.

### M1 — Isolated runtime
Status: DONE

- Dedicated `shorts-v2` Docker project.
- Dedicated n8n.
- Dedicated PostgreSQL.
- Dedicated volumes.
- Minimal `jobs` table.

### M2 — Gemini access
Status: DONE

Goal: use the already-existing Gemini credential without exposing or copying the API key.

Implementation:
- the secret remains in the existing shared n8n credential store;
- two project-owned internal-only gateway workflows expose only the approved text and TTS operations;
- the isolated shorts-v2 n8n calls those gateways over the private Docker network;
- no unrelated shared workflow is modified.

Acceptance:
- text model call succeeds — VERIFIED 2026-09-18;
- TTS model call succeeds — VERIFIED 2026-09-18;
- no other AI provider exists in production path.

### M3 — Intake
Status: DONE

Implement one webhook:
`topic + language + duration -> job_id`

Acceptance:
- strict validation;
- one DB row;
- no AI call during intake.

Verified on 2026-09-18 with one invalid request (HTTP 400, no row) and one valid request (HTTP 201, exactly one queued job row).

### M4 — Script
Status: DONE — verified on job d3acb20c-f6eb-4bf4-918d-4e35fcef0c93

Generate the complete narration/script with Gemini text.

Acceptance:
- correct language;
- structured scene plan;
- no TTS yet;
- one production text path only.

### M5 — Final voice
Status: DONE — exactly one TTS synthesis verified on job d3acb20c-f6eb-4bf4-918d-4e35fcef0c93

Generate one continuous narration with Gemini TTS.

Acceptance:
- exactly one successful final synthesis for the job;
- no second TTS during render;
- no speech speed-up or time-stretch.

### M6 — Local timing
Status: DONE for current local scene alignment implementation.

Implementation:
- exact final PCM is treated as signed 16-bit little-endian PCM;
- local `whisper.cpp` with multilingual `ggml-base` produces timed speech tokens from that exact PCM;
- scene boundaries are mapped from the exact script/scenes to timed local speech tokens;
- no proportional timing fallback remains in the production media worker;
- low transcript/scene coverage fails closed with `alignment_failed`;
- no external transcription API and no second TTS call are used.

Diagnostic evidence on 2026-09-18 with exact PCM from product job `d3acb20c-f6eb-4bf4-918d-4e35fcef0c93`:
- non-product fixture `33333333-4444-4555-8666-777777777777`;
- audio duration: 13.120 s;
- global transcript coverage: 1.0000;
- scene coverages: 1.0000 / 1.0000 / 1.0000;
- speech-derived boundaries: 5.820 s and 10.280 s;
- `fallback_used=false`;
- final rendered AAC was decoded locally and matched the expected narration with normalized similarity 1.0000.

Acceptance:
- zero external transcription calls;
- timestamps belong to the exact audio that is rendered;
- no narration speed change, trim, or second TTS synthesis.

### M7 — Visual sourcing
Status: IMPLEMENTED and latest resolver diagnostic PASS.

Implementation:
- Wikimedia Commons remains the only visual source;
- semantic scoring and context-conflict penalties remain deterministic;
- all deterministic query variants are now compared instead of stopping at the first non-empty Wikimedia result set;
- score remains the primary rank; deterministic title-match precision breaks equal-score cases.

Latest non-product diagnostic `33333333-4444-4555-8666-777777777777` selected:
- scene 1: `File:Sunlight Spectrum.JPG`;
- scene 2: `File:Angular dependence of Rayleigh Scattering.jpg`;
- scene 3: `File:Blue clear sky.jpg`.

The contact sheet was inspected after render; scene 3 is now sky-dominant instead of the earlier hill/tree-dominant result.

Acceptance:
- multiple relevant visuals where needed;
- license/source metadata retained;
- no paid media provider;
- no remote AI visual verification.

### M8 — Render
Status: IMPLEMENTED — current media worker diagnostic PASS.

Latest non-product diagnostic `33333333-4444-4555-8666-777777777777` using exact previously generated PCM:
- machine QA: PASS;
- 1080x1920;
- H.264 video;
- AAC audio;
- container duration: 15.035 s, within the existing ±0.08 s machine-QA tolerance;
- audio stream duration: 15.000 s;
- narration was neither sped up nor trimmed;
- final AAC transcript matched the expected narration locally with similarity 1.0000.

Render locally to vertical MP4.

Acceptance:
- 1080x1920;
- continuous narration;
- visuals aligned to narration;
- target duration handled without changing speech speed;
- valid H.264/AAC MP4.

### M9 — Machine QA + human review
Status: CURRENT MEDIA DIAGNOSTIC MACHINE QA PASS; FRESH PRODUCT E2E + HUMAN REVIEW PENDING

Machine checks:
- dimensions;
- codec/container;
- duration;
- audio present;
- no missing visual assets;
- local alignment metadata.

A fresh normal product E2E with the current M6/M7 implementation has not been run because the approved Gemini TTS Free Tier credential is currently quota-limited. Failed quota jobs remain immutable and must not be retried.

Success is only:
- a fresh normal product job reaches machine QA PASS with the current code;
- the exact final MP4 receives explicit human review PASS.

### M10 — Only after M9 PASS
Status: BLOCKED

Only then consider:
- Studio/UI;
- draft publishing;
- additional visual sources;
- performance/queue improvements.

## Change rule

If a change would introduce a new provider, external AI purpose, paid feature, retry architecture, or additional service:
- stop implementation;
- verify the real need first;
- verify official license/free-tier terms;
- update `config/free-only-policy.json` and this plan before deployment.

Do not redesign the architecture because of one failed job. Fix the proven defect and rerun a new job.
