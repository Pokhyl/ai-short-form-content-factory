# Roadmap

The project is built in small vertical milestones. Do not start a later milestone until the current milestone has a real acceptance result.

## M0 — Repository foundation

Goal: clean public repository with architecture rules and no inherited code.

Acceptance:

- README exists;
- secrets are ignored;
- architecture source of truth exists;
- Docker foundation is present.

## M1 — Docker foundation

Status: completed on 2026-08-22.

Goal: run the three-service stack on the persistent VPS runtime.

Services:

- PostgreSQL;
- n8n;
- media-worker.

Acceptance:

- `docker compose up -d` succeeds;
- PostgreSQL becomes healthy;
- n8n health endpoint returns `200`;
- `GET /health` on media-worker returns `200` and reports FFmpeg/ffprobe;
- application tables exist in `public`;
- n8n owns a separate `n8n` schema;
- n8n and media-worker host ports are bound to `127.0.0.1` only.

Validated runtime result:

- PostgreSQL 18 is healthy;
- n8n 2.33.3 is running and created its internal schema/tables;
- media-worker is running with FFmpeg 8.1.2 and ffprobe 8.1.2;
- `jobs`, `scenes`, `assets`, and `publications` exist;
- persistent Docker volumes exist for PostgreSQL, n8n, and media data.

Learning focus:

- Docker Compose;
- images vs containers;
- ports;
- networks;
- volumes;
- environment variables;
- healthchecks.

## M2 — PostgreSQL application state

Status: completed on 2026-08-22.

Goal: understand and use the four application tables.

Acceptance:

- create one `jobs` row manually;
- read it back;
- create scenes linked by foreign key;
- verify cascade behavior in a disposable test row.

Validated runtime result:

- manually inserted and read back a `jobs` row;
- created two `scenes` linked to the job through `scenes.job_id`;
- verified the foreign-key relationship uses the existing job UUID;
- verified `ON DELETE CASCADE` by deleting a disposable job and confirming its linked scene was automatically removed.

Learning focus:

- SQL;
- primary keys;
- foreign keys;
- indexes;
- JSONB;
- transactions at a basic level.

## M3 — n8n intake

Status: completed on 2026-08-23.

Goal: submit topic, language, and duration through n8n and create a job.

Acceptance:

- invalid input is rejected;
- valid input creates exactly one job;
- response contains the new job ID;
- no AI call yet.

Validated runtime result:

- the production invalid request returned HTTP 400 and inserted zero `jobs` rows;
- the production valid request returned HTTP 201 with `job_id` `ba081017-2345-4212-a1c4-cde6df8de574`;
- PostgreSQL contained exactly one matching job row and its UUID matched the HTTP response;
- the stored job had `language_code = 'en'`, `target_duration_seconds = 60`, `status = 'created'`, and `current_stage = 'intake'`;
- `n8n/workflows/WF01-create-content-job.json` contains the validated six-node production workflow export;
- Script & Scene Planning stayed disconnected and no AI call occurred.

Learning focus:

- Webhook/Form Trigger;
- Edit Fields;
- Code;
- IF/Switch;
- PostgreSQL node;
- JSON.

## M4 — Script + scene plan

Status: completed on 2026-08-23.

Goal: generate one structured script and persist its scenes.

Acceptance:

- one AI request returns validated structured JSON;
- 15/30/45/60-second jobs return exactly 4/8/12/15 scenes;
- every scene contains sequential `scene_number`, target-language `narration`,
  `visual_subject_type`, target-language `visual_description`, and an English
  `visual_query`;
- `visual_subject_type` is exactly `factual` or `generic`;
- visual queries are non-empty, case-insensitively unique, and no longer than 100 characters;
- scenes are stored in PostgreSQL;
- narration and visual intent are readable and coherent;
- malformed model output does not enter the database.

Learning focus:

- HTTP Request;
- API authentication;
- structured JSON;
- validation;
- loops/items.

## M5 — Voiceover

Status: in progress.

Goal: generate one audio file per scene using the previously selected voices.

Before implementation:

- recover the exact selected voice IDs for EN/PL/RU/UK;
- do not substitute guessed voices.

Recovered exact voice presets:

- EN: `en-US-Chirp3-HD-Algenib`;
- PL: `pl-PL-Chirp3-HD-Enceladus`;
- RU: `ru-RU-Wavenet-D`;
- UK: `uk-UA-Chirp3-HD-Enceladus`.

Acceptance:

- every scene has a playable audio file;
- actual audio duration is measured;
- voice quality is manually accepted in all supported languages used for testing.

Learning focus:

- binary data;
- external APIs;
- files;
- per-item processing.

## M6 — Visual sourcing

Goal: choose usable media for each scene without building a separate orchestration system.

Initial sources:

- Wikimedia Commons for exact/factual subjects;
- Pixabay for generic stock;
- Pexels as one fallback.

Acceptance:

- selected visual meaningfully matches narration;
- attribution/license metadata is saved where required;
- oversized/unusable files are normalized before render;
- no acceptable result produces a local fallback scene instead of stopping the job.

Learning focus:

- REST search APIs;
- query construction;
- item filtering;
- metadata normalization;
- API limits/caching.

## M7 — Render

Goal: media-worker creates a valid vertical MP4.

Acceptance:

- 1080x1920 output;
- H.264 video + AAC audio;
- scene timing follows actual voice duration;
- subtitles are visible and synchronized;
- ffprobe validates final output.

Learning focus:

- service-to-service HTTP;
- FFmpeg;
- media files;
- Docker volumes.

## M8 — Quality run

Goal: prove the content pipeline, not only the code.

Acceptance:

- generate at least 10 videos on materially different topics;
- review script, voice, visual relevance, subtitles, and render;
- record concrete recurring failure patterns before adding recovery complexity.

## M9 — Review UI

Goal: rebuild the useful Studio experience with new code.

Initial screen:

- topic input;
- language;
- duration;
- create button;
- current job;
- stage progress;
- error message;
- final video preview when ready.

Acceptance:

- create and monitor a job without opening n8n;
- UI reads real database/runtime state.

## M10 — Buffer draft publishing

Goal: send reviewed final output to Buffer as a draft.

Acceptance:

- final video arrives in the intended Buffer account/queue;
- draft status is persisted in `publications`;
- publishing failure does not destroy the completed video.

Learning focus:

- OAuth/API credentials;
- external publishing API;
- idempotent integration behavior.

## M11 — Additional platforms

Only after Buffer is stable:

- TikTok direct API if useful;
- Instagram Reels;
- YouTube Shorts.

Do not implement all platforms simultaneously.

## M12 — Portfolio package

Goal: make the project understandable to an employer without running it.

Deliverables:

- architecture diagram;
- screenshots;
- short demo video;
- setup instructions;
- technology explanations;
- real usage metrics from the content channel;
- lessons learned and trade-offs.
