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

M4 — Script + scene plan

Status: in progress.

Acceptance:

- one AI request returns validated structured JSON;
- 15/30/45/60-second jobs return exactly 4/8/12/15 scenes;
- every scene contains sequential `scene_number`, target-language `narration`, `visual_subject_type`, target-language `visual_description`, and an English `visual_query`;
- `visual_subject_type` is exactly `factual` or `generic`;
- visual queries are non-empty, case-insensitively unique, and no longer than 100 characters;
- scenes are stored atomically in PostgreSQL;
- narration and visual intent are readable and coherent;
- malformed model output does not enter the database.

## Branch / PR

Branch: `feat/m4-script-scene-planning`

Draft PR: `#5 — M4: implement script and scene planning`

## Runtime

VPS: `root@37.27.87.6`

Project path: `/opt/ai-short-form-content-factory`

Services: `n8n`, `postgres`, `media-worker`.

Public n8n URL: `https://publisher.hodor.com.pl/`

Protected old runtime: `/opt/n8n` — do not modify except for a narrowly required, backed-up, validated Caddy change.

The `n8n` PostgreSQL schema belongs to n8n and must not be modified manually.

## Current M4 production contract

WF02: `TJfA4ZYUEKSTad6k` / `WF02 — Plan Script and Scenes`

Topology:

```text
Receive Job ID
  -> Normalize Job ID
  -> Load Eligible Job
  -> Require Eligible Job
  -> Build Planning Request
  -> Generate Structured Plan
  -> Validate Structured Plan
  -> Persist Scene Plan
```

`Persist Scene Plan` is terminal.

The stage receives only `job_id`, reloads PostgreSQL state, verifies eligibility, makes one Gemini request, validates the complete result, then atomically persists all scenes and updates the job. After successful M4 persistence the intended state is `status = processing`, `current_stage = script`. M5 has not started.

Production scene counts: 15/30/45/60 seconds -> exactly 4/8/12/15 scenes.

Each scene requires:

- sequential `scene_number`;
- target-language `narration`;
- `visual_subject_type = factual|generic`;
- target-language `visual_description`;
- unique English `visual_query` <= 100 characters.

`audio_path`, `visual_path`, and `duration_seconds` remain unset in M4.

## Verified implementation state

- production migration `002_add_scene_visual_subject_type.sql` is applied; `scenes.visual_subject_type` is `TEXT NOT NULL` with `factual|generic` CHECK;
- PostgreSQL persistence was verified with a 60-second structural job: exactly 15 scenes, sequential 1..15, valid required fields, unique queries, no audio/visual/duration values, 0 assets, 0 publications;
- an eight-node WF02 export is committed in `n8n/workflows/WF02-plan-script-and-scenes.json` from commit `5208dc1fc6b8f6ea47179dc70c0b0494c7c5aebc`, but the live `Build Planning Request` prompt has been refined since that export, so the repository export is now stale and must be refreshed before M4 can be completed;
- previous verified eight-node export SHA-256: `fc8088d678999774021bfe745b0d17507e5bfde2f71e407b4e9f8bd6230e87aa`;
- no retry, dispatcher, queue, watchdog, Redis, new service, or M5 work has been added.

## M4 manual-quality history

Quality topic used: `Jak działa Kanał Panamski i jego system śluz`, language `pl`, duration 30 seconds.

1. Job `80638242-ebee-4848-a1a4-9090446a95a8`: structural/persistence PASS, manual quality FAIL due Polish grammar error (`opadaj`) and an incorrect pump claim.
2. Job `ac32c553-dacd-4a21-bd7e-af3cd4941a82`: structural/persistence PASS, manual quality FAIL due `z widokom` grammar error and narration/visual mismatch.
3. Job `1ff6453a-177c-4dc4-9b16-3cac05b2243a`: structural/persistence PASS, manual quality FAIL because the pump claim reappeared and scene 3 used a misleading causal explanation about differing sea levels.
4. Job `6b08098c-e5c7-45bd-babb-036705b563e1`: structural/persistence PASS and manual quality PASS. The job remains `processing/script` with exactly 8 scenes. Polish narration and visual descriptions are readable and grammatically acceptable; scene sequence is coherent; narration-to-visual alignment is acceptable; factual/generic classifications are usable; English visual queries are relevant. The earlier pump error is gone. The explanation now correctly centers the elevation difference between sea level and Gatún Lake and uses gravity-driven lock filling. The final statement that transit takes a few hours is consistent with the Panama Canal Authority's published average transit time of roughly 8–10 hours.

The current live `Build Planning Request` prompt requires natural target-language grammar, conservative factual accuracy, correct causal/mechanistic explanations, avoidance of unsupported technical details, direct narration-to-visual alignment, correct names/spelling, and aligned English visual queries. Schema, validator, persistence SQL, topology, credentials, DB schema, and job-state contract were not changed by these prompt refinements.

## Fourth quality run — accepted checkpoint

Job: `6b08098c-e5c7-45bd-babb-036705b563e1`

Topic: `Jak działa Kanał Panamski i jego system śluz`

Language: `pl`

Duration: 30 seconds

The complete eight-node WF02 ran exactly once and persistence returned:

- `status = processing`;
- `current_stage = script`;
- `inserted_scene_count = 8`;
- `expected_scene_count = 8`;
- `updated_at = 2026-08-23T14:28:00.905Z`.

Read-only PostgreSQL inspection confirmed the same job state and exactly 8 persisted scenes. Manual quality acceptance passed. Do not rerun this job.

## Exact next action

Export the final live eight-node WF02 again because `Build Planning Request` changed after the previous repository export. Validate that the export still contains exactly the eight-node production topology, the accepted current planning prompt, the existing Gemini structured-output schema and validator, the existing atomic `Persist Scene Plan` SQL and query-parameter expression, credential references only, and no runtime secrets. Replace `n8n/workflows/WF02-plan-script-and-scenes.json`, commit and push the refreshed export, then update `CURRENT_STATE.md` and mark M4 complete. Do not start M5 until that final export checkpoint is committed.

## Do not do

- do not rerun any previous quality-test job;
- do not start M5 before the final refreshed WF02 export is committed and M4 is marked complete;
- do not modify the n8n PostgreSQL schema manually;
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure;
- do not add extra services;
- do not modify `/opt/n8n` casually;
- do not put secrets in GitHub.