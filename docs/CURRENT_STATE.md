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

M4 PR `#5 — M4: implement script and scene planning` was merged into `main` on 2026-08-23.

M4 merge commit: `7d25bac1c4d1a90b2b29183d9ec3ca280d1acfc4`.

The M5 branch was created directly from that merge commit.

## Completed M4 checkpoint

Production WF02:

- workflow ID: `TJfA4ZYUEKSTad6k`;
- name: `WF02 — Plan Script and Scenes`;
- final topology: 8 nodes ending in terminal `Persist Scene Plan`;
- final accepted export SHA-256: `be35214a12a4ef933145e629a3cf070376378a1b1a9ba9cd3256b8fbd5f0fdc1`;
- final accepted export commit: `8a545d3f2fc1942b3f95aa9c6919b0cfc2995ac2`;
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

Provider: Google Cloud Text-to-Speech.

These exact presets are product decisions and must be reused exactly:

| Language | Exact voice preset |
| --- | --- |
| English (`en`) | `en-US-Chirp3-HD-Algenib` |
| Polish (`pl`) | `pl-PL-Chirp3-HD-Enceladus` |
| Russian (`ru`) | `ru-RU-Wavenet-D` |
| Ukrainian (`uk`) | `uk-UA-Chirp3-HD-Enceladus` |

Do not substitute guessed voices.

## M5 architecture contract

Voiceover Generation is a separate n8n stage workflow.

It:

- receives only `job_id`;
- reloads persisted job/scenes from PostgreSQL;
- validates stage eligibility;
- changes `jobs.current_stage` to `voiceover` only when M5 actually begins;
- generates one voiceover file per scene using the exact configured voice for the job language;
- stores `scenes.audio_path`;
- measures real audio duration and stores it in `scenes.duration_seconds`;
- persists product state through n8n, not directly from media-worker;
- starts Visual Sourcing only after every required scene audio file is ready;
- on failure records `jobs.status = failed`, `jobs.current_stage = voiceover`, and `jobs.last_error`, and does not start the next stage.

Stage hand-off remains only:

```json
{
  "job_id": "<uuid>"
}
```

## Verified M5 production boundary

Read-only runtime inspection established:

- production VPS is on `feat/m5-voiceover`;
- n8n credential metadata contains `Application PostgreSQL | postgres` and `Google Gemini API | httpHeaderAuth` only;
- no dedicated Google Cloud Text-to-Speech credential exists in the new production n8n runtime;
- the Gemini header-auth credential must not be reused for Cloud TTS;
- media-worker `GET /health` returns HTTP 200 with FFmpeg 8.1.2 and ffprobe 8.1.2;
- persistent Docker volume `ai-short-form-content-factory_media_data` is mounted at `/data` and writable by media-worker;
- n8n does not mount that media volume directly;
- accepted M4 job `6b08098c-e5c7-45bd-babb-036705b563e1` is `pl`, 30 seconds, `processing/script`, `last_error IS NULL`;
- it has exactly 8 `planned` scenes with non-empty narration;
- all 8 scenes still have `audio_path IS NULL` and `duration_seconds IS NULL` and are a clean eligible M5 test state.

## Implemented and accepted media-worker audio boundary

Commit `1ac60492baa19e113baf9d7cdb315e7641988ff0` added internal JSON `POST /audio/store` to the existing `media-worker` service while preserving the three-service architecture.

Request contract:

```json
{
  "job_id": "<uuid>",
  "scene_number": 1,
  "audio_base64": "<Google TTS MP3 base64>"
}
```

Behavior:

- validates JSON size, UUID, scene number, and canonical base64;
- stores audio under deterministic media-relative path `jobs/<job_id>/voiceover/scene-XX.mp3`;
- validates the stored candidate with ffprobe before replacing the final path;
- returns `audio_path`, measured `duration_seconds`, and byte size;
- never writes PostgreSQL directly.

Runtime acceptance passed:

- deployed FFmpeg contains `libmp3lame`;
- disposable MP3 generation returned exit code 0;
- the disposable file was 4312 bytes, MP3, duration 0.800000 seconds;
- `POST /audio/store` returned HTTP 200;
- returned path was exactly `jobs/00000000-0000-4000-8000-000000000005/voiceover/scene-999.mp3`;
- returned `duration_seconds = 0.8` and `bytes = 4312`;
- independent ffprobe on the stored file confirmed duration 0.800000 and size 4312;
- PostgreSQL was not touched by these media-worker tests;
- final explicit cleanup verification showed both disposable files already absent before removal and still absent afterward: `/tmp/m5-audio-store-test.mp3` and `/data/jobs/00000000-0000-4000-8000-000000000005/voiceover/scene-999.mp3`.

The media-worker audio persistence/probe boundary is accepted and does not need further synthetic testing before the real TTS workflow.

## Concrete smallest M5 implementation boundary

No new service is required.

- n8n owns Google Cloud TTS requests and PostgreSQL reads/writes;
- media-worker owns local audio persistence plus ffprobe duration validation;
- `scenes.audio_path` stores a media-relative path under `/data`, never a host-specific absolute path;
- no generic retry/idempotency framework is added.

A dedicated Google authentication credential for Cloud TTS must be created in n8n before the real TTS request. Current credential availability has been verified absent, so this is a required setup step, not a guess.

## Reliability constraints

TTS is an external side effect. Add only the smallest stage-specific repeated-execution guard when the real M5 behavior is implemented and tested. Do not add a generic retry/idempotency framework.

No retry, dispatcher, queue, watchdog, Redis, n8n queue mode, or extra service is allowed unless a concrete later failure pattern requires a new explicit decision.

## Exact next action

Create and verify a dedicated Google Cloud authentication credential in n8n for Cloud Text-to-Speech, then build the initial WF03 — Voiceover Generation input/eligibility block on `feat/m5-voiceover`: receive only `job_id`, reload the job/scenes from PostgreSQL, require `status = processing`, `current_stage = script`, non-empty narration, and unset `audio_path`/`duration_seconds`, then transition `current_stage` to `voiceover` only when the stage begins. After that, add the per-scene Google TTS request using the exact recovered voice preset for the job language, send returned MP3 base64 to the accepted `media-worker POST /audio/store` boundary, and persist `audio_path` plus measured `duration_seconds` through n8n. Do not start M6.

## Do not do

- do not substitute different voice presets;
- do not reuse the Gemini credential for TTS;
- do not implement M5 on the old M4 branch;
- do not start M6 before M5 passes real voice acceptance;
- do not modify the n8n PostgreSQL schema manually;
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure;
- do not add extra services;
- do not modify `/opt/n8n` casually;
- do not put secrets in GitHub.