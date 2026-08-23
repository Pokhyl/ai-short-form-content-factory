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

## Completed milestone

M4 — Script + scene plan

Status: completed on 2026-08-23.

Production WF02:

- workflow ID: `TJfA4ZYUEKSTad6k`;
- name: `WF02 — Plan Script and Scenes`;
- final topology: 8 nodes ending in terminal `Persist Scene Plan`;
- final accepted export SHA-256: `be35214a12a4ef933145e629a3cf070376378a1b1a9ba9cd3256b8fbd5f0fdc1`;
- final export commit: `8a545d3f2fc1942b3f95aa9c6919b0cfc2995ac2`;
- M4 completion docs commit: `9e1336775165702b60d94474b449b09fb0148042`.

M4 acceptance passed:

- one Gemini request returns validated structured JSON;
- 15/30/45/60-second jobs require exactly 4/8/12/15 scenes;
- every scene has sequential `scene_number`, target-language `narration`, `visual_subject_type = factual|generic`, target-language `visual_description`, and a unique English `visual_query` no longer than 100 characters;
- scene persistence and job-state mutation are atomic;
- malformed output creates no partial scene state;
- the fourth meaningful-topic quality run passed manual review for language, coherence, factual/causal accuracy, narration-to-visual alignment, classifications, and visual queries.

Accepted quality job:

`6b08098c-e5c7-45bd-babb-036705b563e1`

It remains `processing/script` with exactly 8 persisted scenes. Do not rerun it.

## Runtime

VPS: `root@37.27.87.6`

Project path: `/opt/ai-short-form-content-factory`

Services: `n8n`, `postgres`, `media-worker`.

Public n8n URL: `https://publisher.hodor.com.pl/`

Protected old runtime: `/opt/n8n` — do not modify except for a narrowly required, backed-up, validated Caddy change.

The `n8n` PostgreSQL schema belongs to n8n and must not be modified manually.

## M5 voice configuration recovered

The exact previously selected voice presets have now been recovered from prior project runtime/test evidence. These are product decisions and must be reused exactly; do not substitute guessed voices.

Google Cloud Text-to-Speech voice presets:

| Language | Exact voice preset |
| --- | --- |
| English (`en`) | `en-US-Chirp3-HD-Algenib` |
| Polish (`pl`) | `pl-PL-Chirp3-HD-Enceladus` |
| Russian (`ru`) | `ru-RU-Wavenet-D` |
| Ukrainian (`uk`) | `uk-UA-Chirp3-HD-Enceladus` |

Prior evidence also confirms that the previous voice-testing work used Google Cloud Text-to-Speech. Current production credential availability in the new n8n runtime has not yet been verified and must not be assumed.

## M5 contract already defined by architecture

Voiceover Generation is a separate stage workflow.

It:

- receives only `job_id`;
- reloads the persisted job/scenes from PostgreSQL;
- validates stage eligibility;
- changes `jobs.current_stage` to `voiceover` only when M5 actually begins;
- generates one voiceover file per scene using the exact configured voice for the job language;
- stores `scenes.audio_path`;
- measures real audio duration and stores it in `scenes.duration_seconds`;
- persists state through n8n, not directly from media-worker;
- starts Visual Sourcing only after every required scene audio file is ready;
- on failure records `jobs.status = failed`, `jobs.current_stage = voiceover`, and `jobs.last_error`, and does not start the next stage.

Do not add a generic retry/idempotency framework. Add only the smallest stage-specific guard required when the TTS side effect is implemented and tested.

## Branch / PR checkpoint

Current branch: `feat/m4-script-scene-planning`

PR `#5 — M4: implement script and scene planning` is still open and draft even though M4 acceptance is complete. Before M5 implementation, finalize and merge PR #5 into `main`, then create the M5 feature branch from the resulting `main` head.

## Exact next action

Finalize PR #5 so its description reflects the completed M4 state, mark it ready, and merge it into `main` only if its head is still the verified M4 head and GitHub reports it mergeable. Then create a new M5 feature branch from the resulting `main` head, update this checkpoint for M5, and perform a read-only inspection of the new production runtime for the Google Cloud TTS credential/auth configuration and any existing media-worker audio/file capabilities before building the Voiceover workflow. Do not guess current credential availability or invent a new service.

## Do not do

- do not rerun accepted or failed M4 quality-test jobs;
- do not substitute different voice presets;
- do not start M5 implementation on the M4 branch;
- do not modify the n8n PostgreSQL schema manually;
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure;
- do not add extra services;
- do not modify `/opt/n8n` casually;
- do not put secrets in GitHub.