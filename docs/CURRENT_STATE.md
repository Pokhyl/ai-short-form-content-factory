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

Commits:

```text
007425004f780d8e25d34fe19cb644feb2057d03 feat: prepare media worker for visual normalization
379517019d9cbbbb01ddd62215f1fe7fcb90e72c feat: add visual normalization and fallback endpoints
```

Implemented boundary:

- existing `media-worker` remains the only media service
- Docker image includes FFmpeg and `font-dejavu`
- `GET /health` remains supported
- `POST /audio/store` remains supported
- `POST /visual/store?job_id=<uuid>&scene_number=<n>` accepts selected JPEG/PNG/WebP/GIF binary from n8n, validates/probes it, normalizes it to JPEG within a 1920x1920 bounding box, and stores it at `jobs/<job_id>/visuals/scene-XX.jpg`
- `POST /visual/fallback` accepts `{job_id, scene_number, text}` and creates a deterministic 1080x1920 local graphic/text JPEG
- media-worker does not write PostgreSQL
- no npm runtime dependency was added

## M6 media-worker runtime acceptance checkpoint

The new media boundary was deployed and tested on the VPS with disposable synthetic input only. PostgreSQL was not touched.

Runtime head used for deployment:

```text
68da38cd345f9059239eaf1bf2f4080ff0f1899e
```

Verified results:

```text
MEDIA_WORKER_HEALTH: OK
VISUAL_STORE_STATUS: 200
VISUAL_STORE_PATH: jobs/11111111-1111-4111-8111-111111111111/visuals/scene-01.jpg
VISUAL_STORE_NORMALIZED: mjpeg 1920x1080
VISUAL_FALLBACK_STATUS: 200
VISUAL_FALLBACK_PATH: jobs/11111111-1111-4111-8111-111111111111/visuals/scene-02.jpg
VISUAL_FALLBACK_NORMALIZED: mjpeg 1080x1920
STORE_FILE_BYTES: 26056
FALLBACK_FILE_BYTES: 33566
DISPOSABLE_MEDIA_REMOVED: YES
M6_MEDIA_WORKER_RUNTIME_TEST: OK
```

Therefore the reusable media-worker visual storage/normalization/fallback boundary is runtime-proven and ready for WF04.

## M6 provider prerequisite checkpoint

Production runtime key-presence check on 2026-08-24 now confirms both configured stock-provider keys are present in `/opt/ai-short-form-content-factory/.env`:

```text
PIXABAY_API_KEY: PRESENT
PEXELS_API_KEY: PRESENT
WIKIMEDIA_API_KEY: NOT_REQUIRED
```

No secret value was printed or committed.

Repository placeholders were added to `.env.example` in commit:

```text
721318ed0bc5423d5daf5b87343a5d30eb446150 docs: add M6 provider env placeholders
```

`.env.example` documents `PIXABAY_API_KEY` and `PEXELS_API_KEY` with placeholder values only. Wikimedia Commons requires no API key.

The n8n service definition explicitly passes both provider variables from `.env` into the container in commit:

```text
84bcdfd661c033a8a1a277eaffc1d42fd8230d1b feat: expose visual provider keys to n8n
```

Runtime deployment was completed on 2026-08-24 after syncing the VPS branch through remote checkpoint `83956e329129f015c2d17d3bb44c146065c08da6`. Only the `n8n` service was recreated. Verification result:

```text
PIXABAY_API_KEY: PRESENT
PEXELS_API_KEY: PRESENT
N8N_HEALTH_STATUS: 200
```

The complete configured provider route is therefore available to WF04 at runtime.

## SentinelX operator checkpoint

The VPS is enrolled in SentinelX. The operator explicitly approved adding `sudo git` to the SentinelX command allowlist so repository synchronization can be performed through the connected server tool. The policy was reloaded successfully and `sudo git` access was verified before the M6 runtime sync.

## M6 WF04 implementation/import checkpoint

The first production-shaped `WF04 — Visual Sourcing` definition was added to the repository and imported into n8n on 2026-08-24.

Repository workflow commit:

```text
e13f6105b0cad74a4a88295547319d622a3ce752 feat: add WF04 visual sourcing
```

Imported runtime structure:

```text
WF04_ID: M6VisualSourcing1
WF04_ACTIVE: false
WF04_NODE_COUNT: 36
WF04_PIN_DATA_EMPTY: YES
HAS_WIKIMEDIA: YES
HAS_PIXABAY: YES
HAS_PEXELS: YES
HAS_LOCAL_FALLBACK: YES
HAS_M7_HANDOFF: NO
PROVIDER_KEY_LITERALS_IN_WORKFLOW: NO
PROVIDER_ENV_REFERENCES_ONLY: YES
WF04_IMPORT_STRUCTURE: OK
```

The workflow receives only `job_id`, reloads durable job/scene state, verifies completed voiceover, transitions/resumes `current_stage=visuals`, applies the deterministic factual/generic provider routes, downloads only the selected external candidate, delegates file validation/normalization/fallback generation to `media-worker`, persists one `public.assets` row plus `scenes.visual_path`, and stops after verified visual persistence because M7 does not exist yet.

The workflow is intentionally inactive and has not yet been runtime-accepted on real scene output. Technical import success is not M6 acceptance.

## M6 real-job eligibility checkpoint

A read-only production query identified exactly one job eligible for the first WF04 runtime acceptance without rerunning M4 or M5:

```text
job_id: db19212b-7914-4346-9ec6-234d315c80d0
topic: Dlaczego koty mruczą?
language_code: pl
target_duration_seconds: 15
scene_count: 4
audio_ready: 4
visuals_ready: 0
asset_count: 0
status/current_stage filter: processing/voiceover
```

This is the already accepted M5 job. Do not execute WF03 again. It is eligible to enter WF04 directly.

## M6 first WF04 runtime attempt checkpoint

The first real WF04 execution attempt was made on 2026-08-24 using the accepted M5 job directly; WF03/M5 were not rerun.

Runtime facts:

```text
job_id: db19212b-7914-4346-9ec6-234d315c80d0
isolated CLI task-broker port: 5680
Begin Visual Stage: succeeded
job status/current_stage after attempt: processing/visuals
visuals_ready: 0
asset_count: 0
last_error: empty
```

The alternate task-broker port removed the previous CLI port collision, so WF04 reached provider execution. Two concrete workflow/runtime blockers were then exposed:

```text
Search Pixabay: access to env vars denied
Recover Generic Context: Can't use .first() here ... This is only available in Run Once for All Items mode
```

Therefore the provider key values are present in the n8n container, but direct `$env` access from workflow nodes is blocked by the current n8n runtime policy. Also, at least one `runOnceForEachItem` Code node incorrectly uses `$input.first()` and must be corrected before the next attempt.

The temporary Manual Trigger acceptance harness was removed immediately after the attempt. The clean runtime WF04 was re-imported and verified:

```text
WF04_CLEAN_NODE_COUNT: 36
WF04_CLEAN_NATIVE_TRIGGER: YES
WF04_CLEAN_MANUAL_TRIGGER: NO
WF04_CLEAN_TEST_JOB_LITERAL: NO
WF04_CLEAN_PIN_DATA: EMPTY
```

No visual files or `public.assets` rows were persisted by this failed attempt. The acceptance job is now resumable from `processing/visuals`; do not move it back to voiceover and do not rerun WF03.

## M6 provider credential runtime checkpoint

Two project-scoped n8n generic credentials were created/imported on 2026-08-24 from the already configured container environment without printing or committing secret values:

```text
M6PixabayQuery01: PRESENT (httpQueryAuth)
M6PexelsHeader01: PRESENT (httpHeaderAuth)
```

Credential intent:

- Pixabay uses query authentication with parameter name `key`;
- Pexels uses header authentication with header name `Authorization`;
- secret values remain encrypted in n8n credentials and are not stored in the public workflow export.

The repository WF04 still requires a follow-up edit to reference these credentials and remove the blocked `$env` expressions. No second WF04 runtime attempt has been made yet.

## M6 WF04 blocker-fix checkpoint

The two blockers from the first runtime attempt were corrected in repository commit:

```text
be38e82 fix: use n8n credentials for visual providers
```

Verified workflow changes:

```text
WF04_PER_ITEM_CODE_FIXED: 10
WF04_PIXABAY_AUTH: httpQueryAuth
WF04_PEXELS_AUTH: httpHeaderAuth
WF04_PROVIDER_ENV_REFERENCES: NONE
```

Pixabay now references credential `M6PixabayQuery01`; Pexels references credential `M6PexelsHeader01`. Secret values are not present in the workflow export. All `runOnceForEachItem` Code nodes that used `$input.first()` were corrected to use the current item directly.

This corrected workflow has been committed and pushed but has not yet been re-imported/runtime-proven after the fix.

## M6 second WF04 runtime attempt checkpoint

The corrected provider-auth workflow was re-imported and the same acceptance job was resumed from `processing/visuals` on 2026-08-24. WF03/M5 were not rerun. The temporary Manual Trigger harness was again removed immediately after execution and the clean 36-node WF04 was restored.

Provider authentication is now runtime-proven:

```text
Search Pixabay: success with real provider results
Search Pexels: success with real provider results
```

The second attempt exposed a separate Code-node return-shape bug. The affected `runOnceForEachItem` nodes still returned arrays such as `[{ json: ... }]`, which n8n rejected with:

```text
Select Pixabay Candidate: A 'json' property isn't an object [item 0]
Select Pexels Candidate: A 'json' property isn't an object [item 0]
Prepare Fallback Context: A 'json' property isn't an object [item 0]
```

Because fallback context was invalid, `Create Fallback Visual` sent no valid string `text`; media-worker correctly rejected all fallback calls with HTTP 400 `invalid_text`. The workflow then recorded the stage failure.

Verified durable/runtime state after the attempt:

```text
job_id: db19212b-7914-4346-9ec6-234d315c80d0
status: failed
current_stage: visuals
last_error: media-worker fallback response is invalid [line 10]
scene 1 visual_path: empty, asset_count: 0
scene 2 visual_path: empty, asset_count: 0
scene 3 visual_path: empty, asset_count: 0
scene 4 visual_path: empty, asset_count: 0
visual media directory: absent
```

Clean WF04 restoration after the attempt was verified:

```text
WF04_CLEAN_NODE_COUNT: 36
WF04_CLEAN_NATIVE_TRIGGER: YES
WF04_CLEAN_MANUAL_TRIGGER: NO
WF04_CLEAN_TEST_JOB_LITERAL: NO
WF04_CLEAN_PIN_DATA: EMPTY
```

The next implementation must fix the per-item return shape and add the smallest WF04-specific explicit resume path for a `failed/visuals` job produced by a prior WF04 execution. Do not manually reset PostgreSQL outside n8n and do not build generic retry infrastructure.

## M6 acceptance from ROADMAP

- selected visual meaningfully matches narration
- attribution/license metadata is saved where required
- oversized/unusable files are normalized before render
- no acceptable external result produces a local fallback scene instead of stopping the job

Technical green execution alone is not M6 acceptance; visual relevance must be manually reviewed on real M6 output.

## Exact next action

1. fix all `runOnceForEachItem` Code-node return shapes in WF04 from array returns to one item/object;
2. add the smallest WF04-specific resume transition for `failed/visuals` so this acceptance job can be intentionally retried through n8n without manual PostgreSQL mutation;
3. re-import the clean corrected WF04 and resume the same acceptance job; do not rerun WF03/M5;
4. verify PostgreSQL asset/visual persistence and media files, then manually review selected visual relevance and attribution/license metadata;
5. after WF04 is runtime-proven and manually accepted, wire WF03 -> WF04 with `waitForSubWorkflow=false`, export the clean production workflows, and close M6 only after ROADMAP acceptance is satisfied.

## Do not do

- do not start M7 before M6 acceptance
- do not modify the `n8n` PostgreSQL schema manually
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure
- do not add extra services
- do not put provider secrets or generated private media in GitHub
- do not hardcode one test topic/job/language into production M6 code
- do not silently substitute generic stock for a failed factual Wikimedia lookup
