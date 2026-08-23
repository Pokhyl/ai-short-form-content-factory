# Current Project State

Last updated: 2026-08-23

This file is the first checkpoint to read before continuing work on this repository.
If chat history conflicts with this file, `docs/ARCHITECTURE.md`, or `docs/ROADMAP.md`, the repository wins.

## Mandatory assistant protocol

For every technical reply or action about this project, fetch the current `docs/CURRENT_STATE.md` from the active feature branch first. Fetch `docs/ARCHITECTURE.md` when architecture is involved and `docs/ROADMAP.md` when milestone scope, acceptance, or progression is involved. Repository state overrides chat memory. Unknown facts must not be guessed. After every completed implementation or runtime step, update this file before moving on. Export production n8n workflows into the repository.

## Project

AI Short-Form Content Factory

Repository: `Pokhyl/ai-short-form-content-factory`

Product goal:

```text
Topic
  -> Script + scene plan
  -> Voiceover
  -> Visual sourcing
  -> Render
  -> Human review
  -> Buffer draft
```

## Current milestone

M5 — Voiceover

Status: in progress.

Goal:

Generate one playable voiceover file per persisted scene using the exact previously selected voice preset for the job language, measure the real audio duration, and persist `audio_path` plus `duration_seconds` before starting Visual Sourcing.

Acceptance:

- every required scene has a playable audio file;
- actual audio duration is measured and stored;
- voice quality is manually accepted in all supported languages used for testing.

## Branch / PR

Current branch: `feat/m5-voiceover`

M4 PR `#5 — M4: implement script and scene planning` was finalized and merged into `main` on 2026-08-23.

M4 merge commit: `7d25bac1c4d1a90b2b29183d9ec3ca280d1acfc4`.

The M5 branch was created directly from that merge commit.

## Completed M4 checkpoint

Production WF02:

- workflow ID: `TJfA4ZYUEKSTad6k`;
- name: `WF02 — Plan Script and Scenes`;
- final topology: 8 nodes ending in terminal `Persist Scene Plan`;
- final accepted export SHA-256: `be35214a12a4ef933145e629a3cf070376378a1b1a9ba9cd3256b8fbd5f0fdc1`;
- final export commit: `8a545d3f2fc1942b3f95aa9c6919b0cfc2995ac2`;
- accepted quality job: `6b08098c-e5c7-45bd-babb-036705b563e1` with exactly 8 persisted scenes and manual quality PASS.

Do not rerun prior M4 acceptance jobs.

## Runtime

VPS: `root@37.27.87.6`

Project path: `/opt/ai-short-form-content-factory`

Services: `n8n`, `postgres`, `media-worker`.

Public n8n URL: `https://publisher.hodor.com.pl/`

Protected old runtime: `/opt/n8n` — do not modify except for a narrowly required, backed-up, validated Caddy change.

The `n8n` PostgreSQL schema belongs to n8n and must not be modified manually.

## Exact recovered M5 voice configuration

The exact previously selected voice presets were recovered from prior project runtime/test evidence and are product decisions. Reuse them exactly; do not substitute guessed voices.

Provider family confirmed by the prior voice-testing evidence: Google Cloud Text-to-Speech.

| Language | Exact voice preset |
| --- | --- |
| English (`en`) | `en-US-Chirp3-HD-Algenib` |
| Polish (`pl`) | `pl-PL-Chirp3-HD-Enceladus` |
| Russian (`ru`) | `ru-RU-Wavenet-D` |
| Ukrainian (`uk`) | `uk-UA-Chirp3-HD-Enceladus` |

## M5 architecture contract

Voiceover Generation is a separate n8n stage workflow.

It:

- receives only `job_id`;
- reloads persisted job/scenes from PostgreSQL;
- validates that the job is eligible for voiceover;
- changes `jobs.current_stage` to `voiceover` only when M5 actually begins;
- generates one voiceover file per scene using the exact configured voice for the job language;
- stores `scenes.audio_path`;
- measures real audio duration and stores it in `scenes.duration_seconds`;
- persists product state through n8n, not directly from media-worker;
- starts Visual Sourcing only after all required scene audio is ready;
- on failure records `jobs.status = failed`, `jobs.current_stage = voiceover`, and `jobs.last_error`, and does not start the next stage.

Stage hand-off remains only:

```json
{
  "job_id": "<uuid>"
}
```

## Verified M5 repository boundary

Repository inspection established:

- `services/media-worker/src/server.mjs` currently implements only `GET /health`; there is no audio upload/save/probe endpoint yet;
- the media-worker image already has both FFmpeg and ffprobe;
- `compose.yaml` mounts persistent `media_data` only at `/data` inside `media-worker`;
- n8n does not share `media_data` directly;
- therefore the repository currently has no path for n8n to persist generated TTS audio into durable media storage or ask media-worker to measure a generated audio file;
- `.env.example` intentionally contains no external-provider configuration yet.

## Verified M5 production runtime inspection — partial

Read-only runtime inspection completed for steps 1–4:

- VPS successfully switched to `feat/m5-voiceover` and synced to repository checkpoint `5f3f2e66ab42e6d07235abb8260b11008772e588` at the time of inspection;
- `n8n.credentials_entity` contained exactly two credential metadata rows: `Application PostgreSQL | postgres` and `Google Gemini API | httpHeaderAuth`;
- no dedicated Google Cloud Text-to-Speech credential metadata exists in the current production n8n database;
- do not assume the Gemini header-auth credential is valid or authorized for Cloud Text-to-Speech;
- media-worker `GET /health` returned HTTP 200 and reported FFmpeg 8.1.2 plus ffprobe 8.1.2;
- the persistent media mount is Docker volume `ai-short-form-content-factory_media_data` at `/data`;
- `/data` exists and is writable by media-worker;
- at inspection time `/data` filesystem reported about 37.2G total, 22.3G used, 13.4G available, 63% used.

The submitted inspection run returned to the Mac prompt after step 4, so the intended step-5 PostgreSQL eligibility query did not produce output. Do not infer the current accepted-job scene/audio state from that missing output.

## Reliability constraints

TTS is an external side effect. Add only the smallest stage-specific repeated-execution guard when the real M5 behavior is implemented and tested. Do not add a generic retry/idempotency framework.

No retry, dispatcher, queue, watchdog, Redis, n8n queue mode, or extra service is allowed unless a concrete later failure pattern requires a new explicit decision.

## Exact next action

Run only the missing read-only PostgreSQL inspection for accepted M4 job `6b08098c-e5c7-45bd-babb-036705b563e1`: confirm job `status/current_stage/language`, exact scene count and narration presence, and that every scene still has `audio_path` and `duration_seconds` unset. Do not repeat the already completed credential/media-worker checks. After that one query, record the result and choose the smallest concrete M5 implementation boundary.

## Do not do

- do not substitute different voice presets;
- do not guess or reuse the Gemini credential for TTS without explicit verification;
- do not implement M5 on the old M4 branch;
- do not start M6 before M5 passes real voice acceptance;
- do not modify the n8n PostgreSQL schema manually;
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure;
- do not add extra services;
- do not modify `/opt/n8n` casually;
- do not put secrets in GitHub.