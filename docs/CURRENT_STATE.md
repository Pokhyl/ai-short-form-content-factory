# Current Project State

Last updated: 2026-08-24

This file is the first checkpoint to read before continuing work on this repository. If chat history conflicts with this file, `docs/ARCHITECTURE.md`, or `docs/ROADMAP.md`, the repository wins.

## Mandatory assistant protocol

Before every technical reply/action for this project, fetch this file from the active branch. Fetch `docs/ARCHITECTURE.md` when architecture is involved and `docs/ROADMAP.md` when milestone scope/acceptance/progression is involved. Repository state overrides chat memory. Unknown facts must not be guessed. After each completed implementation/runtime/setup step, update this file before moving on. Export production n8n workflows into the repository.

## Project

- repository: `Pokhyl/ai-short-form-content-factory`
- active branch: `feat/m6-visual-sourcing`
- completed milestone: M5 — Voiceover
- current milestone: M6 — Visual sourcing (`in progress`)

Target flow:

```text
Topic -> Script + scene plan -> Voiceover -> Visual sourcing -> Render -> Human review -> Buffer draft
```

## Runtime

- VPS: `root@37.27.87.6`
- project path: `/opt/ai-short-form-content-factory`
- services exactly: `n8n`, `postgres`, `media-worker`
- n8n: `https://publisher.hodor.com.pl/`
- application state: PostgreSQL `public`
- n8n internal schema: `n8n`; never modify it manually

## M5 final checkpoint

M5 — Voiceover completed on 2026-08-24.

- WF02 final export SHA-256: `d06d0ff1bb325d6c54999c2f89fee8e9b887ed436872092caff34a9d21fc60b7`
- WF03 final export SHA-256: `666a2de498e4feac7e7877bf2ebc44e61c63fbd38698f239f427ecf673042c86`
- workflow export commit preserved in remote history: `8e6e4a9a578e7d65778e4ca42a77558497549c99`
- final verified M5 remote head: `16a431209d8392c50dcc33c59444da3149744427`
- do not rerun accepted M4/M5 jobs

## M6 branch/setup checkpoint

The M6 branch was created and pushed successfully:

```text
BRANCH: feat/m6-visual-sourcing
LOCAL_HEAD:  2c7c305a8aab3b0c6b4d27a5edef7bf0c6c70451
REMOTE_HEAD: 2c7c305a8aab3b0c6b4d27a5edef7bf0c6c70451
M6_BRANCH_REMOTE_MATCH: YES
M6_SETUP_READY: YES
```

A read-only production schema inspection confirmed the existing application schema already contains all base M6 persistence fields required for the first implementation.

### `public.scenes` relevant fields

- `id uuid NOT NULL`
- `job_id uuid NOT NULL`
- `scene_number integer NOT NULL`
- `visual_description text NULL`
- `visual_query text NULL`
- `visual_subject_type text NOT NULL`
- `visual_path text NULL`
- `status text NOT NULL`

### `public.assets` existing fields

- `id uuid NOT NULL`
- `scene_id uuid NOT NULL`
- `provider text NOT NULL`
- `provider_asset_id text NULL`
- `source_url text NULL`
- `author text NULL`
- `license text NULL`
- `license_url text NULL`
- `local_path text NULL`
- `metadata jsonb NOT NULL`
- `created_at timestamptz NOT NULL`

No application-schema migration is currently required for the first M6 implementation.

## M6 architecture contract

Source of truth remains `docs/ARCHITECTURE.md`.

Visual provider route:

```text
factual -> Wikimedia Commons -> local graphic/text fallback

generic -> Pixabay -> Pexels -> local graphic/text fallback
```

For every scene M6 must receive only `job_id`, reload durable state, verify voiceover completion, enter `current_stage='visuals'`, use the deterministic provider route, select one bounded candidate, download only the selected original, persist metadata in `public.assets`, persist the normalized local path in `scenes.visual_path`, use a local graphic/text fallback when no acceptable external asset exists, and stop after verified visual persistence until M7 exists.

Provider/API requests and PostgreSQL writes remain in n8n. Media/file validation, normalization, and local storage remain in `media-worker`. Do not add a service.

## M6 media-worker implementation checkpoint

The first reusable M6 media boundary is now implemented in the repository.

Commits:

```text
007425004f780d8e25d34fe19cb644feb2057d03 feat: prepare media worker for visual normalization
379517019d9cbbbb01ddd62215f1fe7fcb90e72c feat: add visual normalization and fallback endpoints
```

Changes:

- existing `media-worker` remains the only media service
- Docker image now installs `font-dejavu` in addition to FFmpeg
- `GET /health` remains unchanged
- `POST /audio/store` remains supported
- new `POST /visual/store?job_id=<uuid>&scene_number=<n>` accepts selected image binary from n8n
- supported selected-image content types: JPEG, PNG, WebP, GIF
- request body is bounded to 25 MiB
- selected image is probed, normalized with FFmpeg to a maximum 1920x1920 bounding box while preserving aspect ratio, converted to JPEG, probed again, and stored under the deterministic path `jobs/<job_id>/visuals/scene-XX.jpg`
- response returns `visual_path`, source and normalized dimensions, codec and byte size
- new `POST /visual/fallback` accepts JSON `{job_id, scene_number, text}` and generates a deterministic 1080x1920 local text/graphic JPEG through FFmpeg using DejaVu Sans
- media-worker still does not write PostgreSQL
- no npm runtime dependency was added

This implementation is provider-agnostic: n8n remains responsible for Wikimedia/Pixabay/Pexels search, candidate selection, downloading the selected original, and PostgreSQL persistence.

## M6 acceptance from ROADMAP

- selected visual meaningfully matches narration
- attribution/license metadata is saved where required
- oversized/unusable files are normalized before render
- no acceptable external result produces a local fallback scene instead of stopping the job

Technical green execution alone is not M6 acceptance; visual relevance must be manually reviewed on real M6 output.

## Exact next action

Deploy and runtime-test only the new media-worker visual boundary before creating WF04:

1. fast-forward the VPS M6 branch from remote;
2. rebuild/recreate only `media-worker` from the M6 branch;
3. verify `/health` still succeeds;
4. generate one disposable synthetic image inside the container and POST it to `/visual/store` using a disposable UUID/scene number;
5. POST one disposable fallback request to `/visual/fallback`;
6. ffprobe both returned files and verify deterministic paths/dimensions;
7. delete the disposable synthetic job media directory;
8. do not touch PostgreSQL during this test;
9. update this file before creating WF04.

## Do not do

- do not start M7 before M6 acceptance
- do not modify the `n8n` PostgreSQL schema manually
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure
- do not add extra services
- do not put provider secrets or generated private media in GitHub
- do not hardcode one test topic/job/language into production M6 code
- do not silently substitute generic stock for a failed factual Wikimedia lookup
