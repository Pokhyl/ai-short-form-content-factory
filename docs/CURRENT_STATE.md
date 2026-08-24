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
- WF02 -> WF03 native hand-off uses dynamic `job_id` only with `waitForSubWorkflow=false`
- both workflows are active/current/published and contain no pinned acceptance data
- do not rerun accepted M4/M5 jobs

## M6 branch/setup checkpoint

The M6 branch was created from the completed M5/doc checkpoint and pushed successfully:

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

No application-schema migration is currently required for the first M6 implementation. Do not add one unless concrete workflow behavior proves a missing durable field.

## M6 architecture contract

Source of truth remains `docs/ARCHITECTURE.md`.

Visual provider route:

```text
factual -> Wikimedia Commons -> local graphic/text fallback

generic -> Pixabay -> Pexels -> local graphic/text fallback
```

For every scene M6 must:

1. receive only `job_id` from WF03;
2. reload job/scenes from PostgreSQL;
3. validate stage eligibility and that voiceover output is complete;
4. set `jobs.current_stage = 'visuals'` only when M6 begins;
5. search a bounded candidate set using `visual_query` and the deterministic provider route;
6. reject unusable candidates deterministically;
7. choose one candidate;
8. download only the selected original;
9. use existing `media-worker` for validation, normalization, and local storage;
10. persist selected asset metadata in `public.assets` and the local normalized path in `scenes.visual_path`;
11. create a local graphic/text fallback instead of failing merely because no provider result is acceptable;
12. start Video Render only after every scene has usable visual material. M7 is not implemented yet, so M6 must stop after verified visual persistence until the render workflow exists.

Provider/API requests and PostgreSQL writes remain in n8n. Media/file validation, normalization, and local storage remain in `media-worker`. Do not add a service.

## Existing M6-relevant code

- repository currently contains production workflows WF01, WF02, WF03 only; WF04 does not yet exist
- existing media-worker uses Node 22 + built-in modules, FFmpeg/ffprobe and no npm runtime dependencies
- media-worker currently exposes only `GET /health` and `POST /audio/store`
- media-worker stores durable media under `/data` through the existing `media_data` Docker volume
- `.env.example` currently has no Wikimedia/Pixabay/Pexels configuration; external provider configuration must be added only as M6 implements each provider and no real secret may be committed

## M6 acceptance from ROADMAP

- selected visual meaningfully matches narration
- attribution/license metadata is saved where required
- oversized/unusable files are normalized before render
- no acceptable external result produces a local fallback scene instead of stopping the job

Technical green execution alone is not M6 acceptance; visual relevance must be manually reviewed on real M6 output.

## Exact next action

Implement the smallest reusable media-worker visual boundary before building WF04:

1. add one visual storage/normalization operation to the existing media-worker, without a new service or database write;
2. keep the first operation provider-agnostic so n8n remains responsible for Wikimedia/Pixabay/Pexels search/selection;
3. use deterministic job/scene paths under `jobs/<job_id>/visuals/`;
4. validate/normalize selected media with FFmpeg/ffprobe and return only local path plus technical metadata;
5. add local fallback generation through the same existing service boundary;
6. test this media-worker boundary with disposable synthetic input only;
7. update this file before creating WF04.

## Do not do

- do not start M7 before M6 acceptance
- do not modify the `n8n` PostgreSQL schema manually
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure
- do not add extra services
- do not put provider secrets or generated private media in GitHub
- do not hardcode one test topic/job/language into production M6 code
- do not silently substitute generic stock for a failed factual Wikimedia lookup
