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

## M6 retry-fix implementation checkpoint

The second runtime attempt exposed a per-item Code-node return-shape bug and left the acceptance job in `failed/visuals` with no persisted visual output. The corrective workflow change was completed and pushed in commit:

```text
ffd27ea fix: make visual sourcing retryable
```

Verified implementation facts:

```text
WF04_PER_ITEM_RETURN_SHAPE_FIXED: 10
WF04_FAILED_VISUALS_RETRY_ELIGIBILITY: YES
WF04_FAILED_VISUALS_RESUME_TRANSITION: YES
WF04_PROVIDER_ROUTE_UNCHANGED: YES
```

The retry path is intentionally stage-specific: only a prior `failed/visuals` state may be resumed back into `processing/visuals` by WF04. No generic retry framework was added and PostgreSQL was not manually reset.

The corrected workflow was re-imported into production n8n from repository head e5cd6a7b9e722c5ac2f89036e510cdec8fe48ee9 and the clean 36-node runtime definition was verified. No acceptance execution has been run after this re-import yet.

## M6 third runtime-attempt checkpoint

A third acceptance attempt was made after the retry-fix re-import, using a temporary Manual Trigger harness inside WF04. The CLI execution still chose the native `Execute Workflow Trigger` (`Receive Job ID`) as its trigger source instead of the temporary Manual Trigger, so WF04 received no `job_id` and stopped immediately in `Normalize Job ID` with:

```text
job_id must be a valid UUID
```

This attempt did not reach PostgreSQL stage transition or provider calls. Durable state remained unchanged:

```text
job_id: db19212b-7914-4346-9ec6-234d315c80d0
status: failed
current_stage: visuals
last_error: media-worker fallback response is invalid [line 10]
scene visuals: 0/4
asset_count: 0
visual media directory: absent
```

The temporary harness was removed immediately by re-importing the clean repository WF04. Post-run cleanup verified 36 nodes, no Manual Trigger, no acceptance job literal, and empty pin data.

The next retry must invoke WF04 through its intended sub-workflow boundary with `{job_id}` rather than relying on direct CLI trigger selection. The smallest acceptance harness is a temporary wrapper workflow: Manual Trigger -> set acceptance `job_id` -> Execute Sub-workflow WF04. Remove the wrapper after execution.

## M6 wrapper execution limitation checkpoint

A temporary three-node wrapper file was prepared to invoke WF04 through its intended `{job_id}` sub-workflow boundary without importing a persistent test workflow. The installed n8n CLI does not execute workflow files directly despite still exposing the deprecated `--file` flag: `n8n execute --file=...` exits without running the workflow and reports `--id has to be set`.

Therefore a wrapper must be imported into n8n to execute by ID, which would leave a persistent temporary workflow because this n8n CLI exposes no workflow-delete command. To avoid polluting production n8n, do not import the wrapper.

The next acceptance harness will instead add a temporary private localhost-only Webhook trigger to the existing WF04, invoke it once through the running n8n service with the accepted `job_id`, then immediately re-import the clean repository WF04 and unpublish it. This preserves the production workflow ID and leaves no additional workflow object.

## M6 temporary-webhook activation checkpoint

The temporary localhost-only Webhook harness was imported and published successfully, but the running n8n process returned HTTP 404 because CLI publish changes are not applied to a currently running n8n process. The CLI explicitly reported that a restart is required for the published workflow changes to take effect.

Observed result:

```text
HTTP_STATUS: 404
message: requested webhook is not registered
```

The clean 36-node WF04 was immediately re-imported and unpublished afterward. Post-cleanup verification remained: no temporary webhook node, `active=false`, empty pin data. No acceptance job execution occurred and durable application state was not changed by this attempt.

A controlled n8n-only restart is now the smallest grounded way to register the temporary webhook harness. The acceptance procedure must: import/publish temp WF04 -> restart only n8n -> call localhost webhook -> wait/verify execution -> restore clean WF04 + unpublish -> restart only n8n again so the temporary webhook is removed from the running process.

## M6 webhook restart attempt checkpoint

The controlled temporary-webhook procedure was executed exactly as planned: temp WF04 import/publish -> n8n-only restart -> localhost POST -> clean WF04 restore/unpublish -> n8n-only restart. The running n8n service returned HTTP 404 even after the restart:

```text
Cannot POST /webhook/m6-wf04-acceptance-7a9c31
HTTP_STATUS: 404
```

Therefore CLI `publish:workflow` alone did not register the temporary production webhook in the running service for this inactive WF04. The clean workflow was restored and verified afterward:

```text
NODE_COUNT: 36
TEMP_WEBHOOK_PRESENT: NO
ACTIVE: false
PIN_DATA: EMPTY
N8N_CLEAN_READY: YES
```

No acceptance job execution occurred in this attempt. The next action is to inspect the installed n8n CLI activation command/options and verify the exact runtime active/published state before another webhook attempt; do not infer activation semantics.

## M6 n8n activation CLI checkpoint

Installed n8n CLI help was inspected directly. Exact commands/options are now known:

```text
n8n publish:workflow --id=<workflow_id> [--versionId=<version_id>]
n8n update:workflow --id=<workflow_id> --active=true|false
```

`publish:workflow` only controls the published version; `update:workflow --active=true` explicitly sets the workflow active state. The next temporary webhook attempt must use both explicit active state and publication, export/verify `active=true` plus `versionId == activeVersionId`, then restart n8n before calling the webhook.

## M6 explicit-active webhook attempt checkpoint

The temporary Webhook WF04 was re-imported, published, explicitly activated with `update:workflow --active=true`, exported, and verified before restart:

```text
TEMP_ACTIVE: true
TEMP_PUBLISHED_CURRENT: YES
TEMP_WEBHOOK_PRESENT: YES
```

After an n8n-only restart, the localhost production webhook still returned HTTP 404 (`Cannot POST /webhook/m6-wf04-acceptance-7a9c31`). Therefore active/published workflow metadata alone is not sufficient evidence that this webhook was registered by the running process.

The clean repository WF04 was immediately restored, unpublished/deactivated, n8n was restarted again, and cleanup was verified:

```text
CLEAN_ACTIVE: false
CLEAN_NODE_COUNT: 36
CLEAN_WEBHOOK_PRESENT: NO
CLEAN_PIN_DATA: EMPTY
```

No acceptance job execution occurred in this attempt. The next action is read-only inspection of n8n webhook-registration persistence/startup state for WF04 while a temporary active/published harness is loaded; do not modify the n8n schema manually.

## M6 successful corrected WF04 runtime checkpoint

The corrected retry-fix WF04 was finally executed successfully on the accepted M5 job without rerunning WF03/M5. The acceptance harness used a temporary Manual Trigger placed first in the WF04 node list so the CLI selected it as the trigger source, then set only the accepted `job_id` and routed into the normal `Normalize Job ID` path. The harness was removed immediately after execution by re-importing the clean repository workflow.

Verified execution result:

```text
job_id: db19212b-7914-4346-9ec6-234d315c80d0
CLI trigger selected: M6 Acceptance Manual Trigger
execution status: success
last node executed: Require Visual Completion
job status: processing
current_stage: visuals
scene_count: 4
visuals_complete: true
```

Post-execution clean workflow restoration was verified:

```text
CLEAN_NODE_COUNT: 36
CLEAN_MANUAL_TRIGGER: NO
CLEAN_TEST_JOB_LITERAL: NO
CLEAN_ACTIVE: false
CLEAN_PIN_DATA: EMPTY
```

The next action is durable verification of all four persisted `scenes.visual_path` values, `public.assets` metadata rows, and the four normalized visual files, followed by manual visual relevance review.

## M6 durable visual verification and relevance finding

The successful WF04 execution was verified against durable application state and media files. All four scenes now have one persisted asset and one normalized local JPEG:

```text
scene 1: pixabay, jobs/db19212b-7914-4346-9ec6-234d315c80d0/visuals/scene-01.jpg, 381899 bytes, 1371x1920
scene 2: pixabay, jobs/db19212b-7914-4346-9ec6-234d315c80d0/visuals/scene-02.jpg, 297748 bytes, 1343x1920
scene 3: pixabay, jobs/db19212b-7914-4346-9ec6-234d315c80d0/visuals/scene-03.jpg, 188382 bytes, 1280x1920
scene 4: pixabay, jobs/db19212b-7914-4346-9ec6-234d315c80d0/visuals/scene-04.jpg, 117124 bytes, 1280x1920
```

Each persisted asset contains provider/source/author/license/local-path metadata. `jobs.status='processing'`, `current_stage='visuals'`, and `last_error` is empty.

The relevance check found one concrete M6 quality failure: scene 2 query `cat larynx anatomy illustration animation` selected Pixabay asset `254129`, whose tags describe a human anatomy diagram (`anatomy, man, human, body, ...`). The current selector gives every matching query token the same weight, so the generic token `anatomy` on rank 1 narrowly beat the rank-2 cat result. M6 is therefore not accepted yet despite the green execution.

The smallest corrective change is to weight query-token matches by their position in `visual_query` for both Pixabay and Pexels selectors, preserving provider order and fallback behavior. Earlier query terms receive more weight; no provider, service, persistence, or handoff contract changes are required.

## M6 weighted visual-selection implementation checkpoint

The relevance-ranking fix was implemented in both `Select Pixabay Candidate` and `Select Pexels Candidate` without changing provider order, credentials, persistence, media-worker calls, or the handoff contract. Query-token matches are now weighted by position (`30, 25, 20, ...`, floor `10`) instead of every matched token contributing the same `10` points. Selected metadata also records `matched_tokens`.

A live Pixabay search simulation against the four accepted scene queries confirmed the corrected ranking behavior before runtime re-selection:

```text
scene 1 -> asset 5129332, matched [close, cat]
scene 2 -> asset 7965411, matched [cat]  (human anatomy asset 254129 no longer wins)
scene 3 -> asset 8032816, matched [relaxed, cat]
scene 4 -> asset 9637984, matched [cat]
```

The code change is not yet runtime-accepted against persisted re-selection output. The next step is to reselect through n8n on the same acceptance job using a temporary n8n-owned acceptance reset/retry harness; do not manually mutate PostgreSQL outside n8n and do not rerun WF03/M5.

## M6 first weighted re-selection harness attempt

The first weighted re-selection attempt did not reach the application reset or provider calls. The temporary n8n-owned reset node had an invalid `queryReplacement` expression and PostgreSQL rejected the literal string instead of a UUID:

```text
invalid input syntax for type uuid: "{ [ 'db19212b-7914-4346-9ec6-234d315c80d0' ] }"
```

Because the reset query failed before mutation, durable application state remained unchanged. The temporary 38-node harness was removed immediately and the clean weighted 36-node WF04 was restored and verified:

```text
CLEAN_NODE_COUNT: 36
CLEAN_MANUAL_TRIGGER: NO
CLEAN_RESET_NODE: NO
CLEAN_ACTIVE: false
CLEAN_PIN_DATA: EMPTY
CLEAN_WEIGHTED_SELECTOR: YES
```

The corrected acceptance harness must set `job_id` in a Code node first and pass it to the temporary PostgreSQL reset node through the standard expression `={{ [ $json.job_id ] }}`. This remains an n8n-owned application-state reset; do not mutate PostgreSQL directly outside n8n.


## M6 weighted re-selection runtime acceptance checkpoint

The corrected weighted re-selection was executed successfully on 2026-08-24 against the same accepted M5 job. WF03/M5 were not rerun.

The temporary n8n-owned acceptance harness used the required order:

```text
Manual Trigger
-> Set Acceptance Job ID (Code)
-> Reset Acceptance Visual State (PostgreSQL)
-> normal WF04 path
```

The temporary PostgreSQL reset node received the job id through the standard expression `={{ [ $json.job_id ] }}`. The n8n-owned reset succeeded:

```text
deleted_asset_count: 4
reset_scene_count: 4
job_reset: true
```

The weighted WF04 execution completed successfully with `Require Visual Completion` as the last node and `visuals_complete: true`.

Runtime weighted selections:

```text
scene 1 -> Pixabay 5129332, matched [close, cat]
scene 2 -> Pixabay 7965411, matched [cat]
scene 3 -> Pixabay 8032816, matched [relaxed, cat]
scene 4 -> Pixabay 9637984, matched [cat]
```

The previous human-anatomy asset `254129` no longer won scene 2.

Durable application state was verified read-only after the run:

```text
job status/current_stage: processing/visuals
last_error: empty
scenes.visual_path: 4/4
asset rows: 4
provider/source/author/license/license_url: present on all 4 asset rows
```

All four normalized JPEG files exist and are probeable with `ffprobe`:

```text
scene-01.jpg | 381899 bytes | mjpeg | 1371x1920
scene-02.jpg | 249448 bytes | mjpeg | 1280x1920
scene-03.jpg | 188382 bytes | mjpeg | 1280x1920
scene-04.jpg | 117124 bytes | mjpeg | 1280x1920
```

The temporary harness was immediately replaced by the clean production WF04. Runtime export verification after restoration:

```text
CLEAN_NODE_COUNT: 36
CLEAN_MANUAL_TRIGGER: NO
CLEAN_RESET_NODE: NO
CLEAN_TEST_JOB_LITERAL: NO
CLEAN_ACTIVE: false
CLEAN_PIN_DATA: EMPTY
CLEAN_WEIGHTED_SELECTOR: YES
```

This proves the weighted selector runtime path and durable persistence, but it does not close M6. Scene 2 is now a cat photo (Pixabay `7965411`) while its requested intent remains a cat larynx anatomy illustration/animation. Final real-image semantic review is still required before M6 acceptance.

## M6 stricter semantic-coverage implementation checkpoint

Manual review of the weighted runtime images found that subject-only cat photos are still too weak for acceptance when a scene requests a more specific visual relationship. Scene 2 remains the concrete failure: the query is `cat larynx anatomy illustration animation`, but weighted runtime selected Pixabay `7965411`, which is an ordinary cat portrait rather than cat-larynx anatomy.

The bounded selector acceptance was therefore tightened in both `Select Pixabay Candidate` and `Select Pexels Candidate` without changing provider order, credentials, persistence, media-worker, or handoff contracts:

- weighted token scoring remains unchanged;
- when a query contains more than one meaningful token, an external candidate must match at least 2 distinct query tokens;
- the first meaningful query token must be one of the matched tokens, so the highest-priority subject/intent term cannot disappear;
- candidates are filtered by this semantic-coverage gate before final score/rank selection, so a weak top-ranked candidate does not hide a lower-ranked acceptable candidate;
- accepted metadata now records `required_match_count` and `required_primary_token`;
- if Pixabay has no acceptable candidate, the existing route continues to Pexels; if Pexels also has none, the existing local graphic/text fallback is used.

JSON structure and both modified Code-node scripts were syntax-checked. This implementation is not yet runtime-accepted. The next action is to commit/push the clean 36-node WF04 plus this checkpoint, re-import it, then reselect the same acceptance job through the n8n-owned reset harness and review the resulting real images.

## M6 harder-topic runtime finding and core-subject gate checkpoint

A deliberately harder independent acceptance job was created through production WF01 and allowed to run normally through WF02/WF03 before WF04 was invoked with a temporary Manual Trigger harness. This was not the cat job.

```text
job_id: 82a54ce1-e306-46be-92ca-201aec4bcb9a
topic: Jak GPS ustala pozycję telefonu i dlaczego myli się między wieżowcami?
language: pl
duration: 30 seconds
scene_count: 8
voiceover_ready: 8/8
WF04 execution status: success
visuals_complete: true
```

The clean 36-node WF04 was restored immediately after execution. Durable verification found 8/8 visual paths and 8 asset rows, but the harder topic exposed that the previous two-token gate still accepts semantically wrong stock when provider tags contain query words in unrelated contexts. Concrete failures included Pixabay `4109368` (`radio poster wall`) for `radio wave bouncing off a skyscraper wall` and Pixabay `2707528` (lighthouse) for `phone navigation screen showing inaccurate location`.

A bounded stronger acceptance rule was therefore implemented in both stock selectors without changing provider order or architecture:

- weighted query scoring remains;
- the existing minimum matched-token and primary-token requirements remain;
- the first two meaningful query tokens are now treated as core subject tokens;
- Pixabay must contain both core tokens in the high-confidence page URL slug, not merely anywhere in free-form tags;
- Pexels must contain both core tokens in its descriptive `alt` text; photographer names no longer contribute to semantic scoring;
- if the high-confidence subject gate fails, the existing route continues to the next provider and ultimately local fallback;
- accepted metadata records `required_core_tokens` and `subject_matched_tokens`.

A live provider simulation on the 8-scene GPS job showed the intended conservative result: scene 1 retains a relevant smartphone-outdoors Pixabay photo, scene 6 has a relevant Pexels skyscraper-street candidate, and the six technical/relational scenes have no high-confidence stock result and therefore fall through rather than accepting unrelated imagery. This implementation still requires production re-selection runtime acceptance.

## M6 core-subject gate runtime re-selection checkpoint

The stronger core-subject gate has now been runtime-proven on both the deliberately harder GPS job and the original cat acceptance job using n8n-owned reset harnesses. Each harness was removed immediately afterward and the clean 36-node WF04 was restored.

GPS acceptance job:

```text
job_id: 82a54ce1-e306-46be-92ca-201aec4bcb9a
reset: deleted_asset_count=8, reset_scene_count=8, job_reset=true
execution status: success
last node: Require Visual Completion
visuals_complete: true
durable visual paths: 8/8
durable asset rows: 8
```

The stricter gate rejected the previously observed false positives. External stock survived only where the provider description strongly matched the scene subject:

```text
scene 1 -> Pixabay 6586105, smartphone outdoors, accepted
scene 2 -> local_fallback
scene 3 -> local_fallback
scene 4 -> local_fallback
scene 5 -> local_fallback
scene 6 -> Pexels 17002617, urban street/skyscrapers, accepted
scene 7 -> local_fallback
scene 8 -> local_fallback
```

All 8 GPS JPEGs exist, are non-empty, and are ffprobe-readable. The two external files were normalized by media-worker and the six fallbacks are 1080x1920 MJPEG JPEGs.

Original cat acceptance job:

```text
job_id: db19212b-7914-4346-9ec6-234d315c80d0
reset: deleted_asset_count=4, reset_scene_count=4, job_reset=true
execution status: success
last node: Require Visual Completion
visuals_complete: true
durable visual paths: 4/4
durable asset rows: 4
```

Final cat selections under the same production selector:

```text
scene 1 -> Pexels 18968229, close-up sleeping/resting cat
scene 2 -> local_fallback for `cat larynx anatomy illustration animation`
scene 3 -> Pexels 30243245, relaxed cat stretching
scene 4 -> Pexels 38151469, cat looking indoors
```

The larynx scene no longer resolves to a generic cat portrait or human-anatomy image. It correctly falls through to the existing local fallback because neither stock provider produced a high-confidence core-subject match.

All 4 cat JPEGs exist, are non-empty, and are ffprobe-readable. Final clean WF04 runtime verification after the cat run:

```text
node_count: 36
manual_trigger: false
acceptance_reset_node: false
acceptance_job_literal: false
active: false
pin_data: empty
core_subject_gate: present in Pixabay and Pexels selectors
```

This closes the concrete false-positive defect found during harder visual testing. M6 is still not formally closed because the repository requires final real-image semantic review through Google AI Studio before milestone acceptance.

## M6 Google AI Studio review handoff checkpoint

The exact final runtime visuals for both acceptance jobs were packaged for the required external semantic review. The package contains all 12 real JPEGs, `MANIFEST.tsv`, `AI_STUDIO_PROMPT.txt`, and `SHA256SUMS.txt`.

```text
archive: m6-visual-review.tar.gz
archive_bytes: 2008983
archive_sha256: f69a9cbbeef76178f65ed7ccc8beb3373e19155002dfc0c16f1e668517dfde11
contents: 8 GPS JPEGs + 4 cat JPEGs + manifest + review prompt + per-file SHA256 sums
```

A temporary one-hour drop share was created for operator handoff. The temporary URL is intentionally not committed to GitHub.

The current ChatGPT tool/plugin environment does not expose a Google AI Studio or Gemini Studio connector capable of uploading these real files and performing the mandated review. A plugin-directory search found no relevant Google AI Studio/Gemini review integration. Therefore the remaining Google AI Studio review is an explicit operator action, not a code/runtime blocker.

After the operator returns the AI Studio scene-by-scene verdict, continue from that verdict without rerunning accepted upstream stages. If all scenes pass, wire WF03 -> WF04 and close M6. If any scene fails, make only the smallest bounded WF04 correction justified by the failed scene and reselect that job through the existing n8n-owned reset harness.

## M6 restored semantic-ranking implementation checkpoint

The operator rejected the current result of 2 external GPS photos plus 6 text fallbacks and confirmed that the implementation had drifted from the previously agreed visual-selection plan. The tag/alt/URL core-token gates are therefore not the target architecture.

The restored production-selection contract is now explicit in `docs/ARCHITECTURE.md`:

```text
provider search (bounded to 10)
-> deterministic metadata/file-type filtering
-> surviving candidate preview pool
-> local SigLIP image/text ranking in media-worker
-> select highest-ranked real image
-> download only selected original
-> normalize/store/persist
-> provider fallback only when the current provider has no usable pool
-> local graphic/text fallback only when the configured route has no usable candidate
```

Gemini/Google AI Studio remains an acceptance/review check on the final real images; it is not the normal production image selector.

A disposable runtime feasibility probe was completed before modifying production:

```text
model: Xenova/siglip-base-patch16-224
dtype: q4
model cache: ~202 MB
VPS memory: 3.7 GiB RAM + 2.0 GiB swap
model warm load: ~1.2 s
2-image batch inference: ~1.1 s
known cat image ranked strongly above unrelated lighthouse/radio labels
known GPS smartphone image ranked above unrelated satellite/lighthouse labels
```

The first implementation slice is complete but not yet deployed: `media-worker` now has a planned `POST /visual/rank` boundary using `@huggingface/transformers` 3.8.1 and q4 SigLIP. It accepts 1-10 trusted provider preview URLs, ranks them against one query, and returns only candidate IDs/scores/ranks. Preview hosts are restricted to Wikimedia, Pixabay, and Pexels CDNs. The existing `/visual/store`, `/visual/fallback`, and audio boundaries are unchanged. The model cache is under the existing `/data` volume, so no fourth service or new persistent service is introduced. Source syntax and package lock generation passed in a disposable Node 22 container.

The modified existing media-worker has now been built and deployed in production. Runtime verification:

```text
/health: 200, semantic_ranker=Xenova/siglip-base-patch16-224 q4
/visual/rank: 200 on a real 3-candidate Pixabay pool
first production model download/cache fill: 286.39 s
production model cache after first load: 211 MB
/audio/store compatibility smoke test: 200
/visual/store compatibility smoke test: 200, mjpeg 1280x1920
/visual/fallback compatibility smoke test: 200, mjpeg 1080x1920
disposable smoke-test media removed after verification
```

The long first `/visual/rank` call was the one-time model download into the persistent existing `/data` volume. The model is now cached for subsequent ranking calls. No application database state was mutated during these media-worker smoke tests. WF04 has not yet been rewired to call `/visual/rank`.

## M6 WF04 SigLIP rewiring implementation checkpoint

WF04 has now been refactored back to the restored semantic-ranking plan. The old tag/alt/URL token gates are no longer used as the production selection mechanism.

Implemented flow per provider:

```text
provider search (max 10)
-> deterministic file/metadata usability filter
-> candidate_pool with trusted preview URLs + original/attribution metadata
-> POST /visual/rank to media-worker
-> choose ranked[0] by candidate_id
-> download only the selected original
-> existing normalize/store/persist path
```

Implementation facts:

```text
WF04 node count: 42
Wikimedia pool builder: present
Pixabay pool builder: present
Pexels pool builder: present
SigLIP rank HTTP nodes: 3
rank result resolver nodes: 3
old required_core_tokens gate: removed
old subject_matched_tokens gate: removed
old required_primary_token gate: removed
provider order: unchanged
local fallback behavior: unchanged
M7 handoff: still absent
```

Wikimedia search now requests a bounded 640px preview (`iiurlwidth=640`) for semantic ranking while retaining the original file URL for the single selected download. Pixabay ranking uses `webformatURL`/`previewURL`; Pexels ranking uses `src.medium`/`src.small`. Original provider IDs, source URLs, authors, licenses, dimensions, and provider rank remain attached to the candidate and are persisted only for the semantic winner.

All six modified/new Code-node scripts passed `node --check` inside the production n8n container, and the workflow JSON parses successfully.

The clean SigLIP-ranked WF04 has now been imported into production. Runtime export verification immediately after import:

```text
node_count: 42
active: false
pin_data: empty
manual_acceptance_trigger: absent
acceptance_reset_node: absent
SigLIP rank nodes: 3
old required_core_tokens gate: absent
```

The workflow has not yet been reselected on the GPS acceptance job after this import.

## M6 acceptance from ROADMAP

- selected visual meaningfully matches narration
- attribution/license metadata is saved where required
- oversized/unusable files are normalized before render
- no acceptable result produces a local fallback scene instead of stopping the job

Technical green execution alone is not M6 acceptance. Final scene-to-image relevance review for M6 is performed through Google AI Studio on the real selected images against each scene narration/visual intent; tag/metadata inspection is only a diagnostic aid and does not replace that review.

## Exact next action

1. reselect the existing GPS acceptance job through the n8n-owned reset harness without rerunning M4/M5;
3. inspect durable 8/8 results and run the required Gemini/Google AI Studio acceptance review on the actual selected images;
4. only after visual acceptance, wire WF03 -> WF04, export the clean production workflows, update ROADMAP M6 completed, and close M6;
5. do not start M7 before M6 is closed.

## Do not do

- do not start M7 before M6 acceptance
- do not modify the `n8n` PostgreSQL schema manually
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure
- do not add extra services
- do not put provider secrets or generated private media in GitHub
- do not hardcode one test topic/job/language into production M6 code
- do not silently substitute generic stock for a failed factual Wikimedia lookup
