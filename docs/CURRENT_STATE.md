# Current Project State

Last updated: 2026-08-23

This file is the first checkpoint to read before continuing work on this repository.
If chat history conflicts with this file, `docs/ARCHITECTURE.md`, or `docs/ROADMAP.md`, the repository wins.

## Mandatory assistant protocol

For every technical reply or action about this project, the assistant must first fetch the current version of `docs/CURRENT_STATE.md` from the active feature branch. Do not rely on a previously fetched copy or on chat memory.

When the reply involves architecture, also fetch `docs/ARCHITECTURE.md` before answering.
When the reply changes milestone scope, acceptance, or progression, also fetch `docs/ROADMAP.md` before answering.

If repository state and chat history disagree, stop using chat memory and follow the repository source of truth.
If a fact is not present in the repository and cannot be verified directly, state that it is unknown instead of reconstructing it from memory.
Do not introduce a new workflow, service, architectural boundary, retry mechanism, or runtime change unless it is explicitly marked as a new proposal first.
After every completed implementation or runtime step, update this file before moving to the next step.

The project owner should not need to remind the assistant to perform this protocol.

## Project

AI Short-Form Content Factory

Repository:

`Pokhyl/ai-short-form-content-factory`

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

Goal:

Generate one structured script with scene planning and persist its validated scenes in PostgreSQL.

Acceptance:

- one AI request returns validated structured JSON;
- scenes are stored in PostgreSQL;
- narration and visual intent are readable and coherent;
- malformed model output does not enter the database.

Current M4 architecture contract:

- the stage receives only `job_id`;
- it reloads the job from PostgreSQL;
- it verifies that the job is eligible for script planning;
- it requires exactly 4/8/12/15 scenes for 15/30/45/60-second jobs;
- each scene carries target-language narration and visual description, a factual/generic subject classification, and a unique English visual query;
- it makes one AI request for the structured script and scene plan;
- it validates the complete model output before persistence;
- it persists scenes and updates job state only after validation succeeds;
- malformed output must not create partial scene state;
- Voiceover Generation is not implemented as part of M4.

## Current branch and PR

Branch:

`feat/m4-script-scene-planning`

Draft PR:

`#5 — M4: implement script and scene planning`

Previous merged PR:

`#4 — M3: implement n8n job intake`

Merge commit:

`e8059f5af93f3624ee3210e8b2f66f25c72e27bd`

Base branch:

`main`

Main currently includes public n8n access through merge commit:

`718301bf1e36dd4d6bef40292d8d2b22f08ee751`

## Completed

- the updated live WF02 planning contract has now passed one real 60-second structural run for retained job `ba081017-2345-4212-a1c4-cde6df8de574`. `Validate Structured Plan` returned exactly 15 sequential scenes numbered 1..15; every scene contained all five required fields; `visual_subject_type` was always exactly `factual` or `generic`; the validator therefore also confirmed non-empty required strings, English `visual_query` values no longer than 100 characters, and case-insensitive query uniqueness. The Gemini response used model `gemini-3.5-flash-lite`, response ID `dOqKaqXPOJGmkdUP2qW1kQk`, 507 prompt tokens, 981 output tokens, and 1488 total tokens. Because the job topic is the synthetic M3 marker `M3_VALID_BB26793B-3A2E-4B5C-AD8D-2FD22D97CA03`, this run is structural acceptance only and is not yet manual quality acceptance for a meaningful real topic. No PostgreSQL scene persistence or job-state mutation exists after validation yet;
- a second read-only inspection of saved live WF02 configuration identified the mismatch exactly: `Build Planning Request` is already on the new M4 contract, but both downstream nodes are still saved in their old versions. `Generate Structured Plan` still has `responseJsonSchema.scenes.minItems = 1`, no exact `maxItems`, no `visual_subject_type` property, and only four required scene fields. `Validate Structured Plan` still accepts any non-empty scene array, requires only `scene_number`, `narration`, `visual_description`, and `visual_query`, and does not enforce duration-specific scene count, `visual_subject_type`, query length, or case-insensitive query uniqueness. This inspection modified nothing;
- the first real 60-second run after updating `Build Planning Request` returned exactly 15 sequential scenes from `gemini-3.5-flash-lite` and `Validate Structured Plan` returned a normal result, but the result does not satisfy the production M4 contract: every returned scene lacks `visual_subject_type`. The validator nevertheless accepted the output, proving that the saved live `Generate Structured Plan` and/or `Validate Structured Plan` configuration is not yet the intended production contract. The run used response ID `XeiKatXWBYirnsEP8tDG0AY` with 507 prompt tokens, 1178 output tokens, and 1685 total tokens. No persistence node exists after validation, so this failed contract test did not create scene rows or mutate job state;
- the live WF02 `Build Planning Request` node now emits the production duration-specific planning contract for the retained 60-second M3 job `ba081017-2345-4212-a1c4-cde6df8de574`: `required_scene_count = 15`, language `English`, and a prompt/output shape containing exactly the five required scene fields `scene_number`, `narration`, `visual_subject_type`, `visual_description`, and `visual_query`. The generated instructions require exactly 15 scenes, sequential numbering, target-language narration/visual description, `factual|generic` classification, non-empty English visual queries no longer than 100 characters and unique ignoring case, and explicitly exclude `duration_seconds` and concrete provider/asset selection. This confirms the request-construction node is on the new M4 contract;
- a read-only inspection of the live production WF02 identified exactly one matching workflow: ID `TJfA4ZYUEKSTad6k`, name `WF02 — Plan Script and Scenes`. Its current planning chain is `Require Eligible Job` -> `Build Planning Request` -> `Generate Structured Plan` -> `Validate Structured Plan`, with no node after validation. The pre-update `Build Planning Request` used the older open-ended scene contract and had no duration-specific required scene count or `visual_subject_type`; the Gemini `responseJsonSchema` had only `minItems: 1`, no exact `maxItems`, and no `visual_subject_type`; `Validate Structured Plan` required only a non-empty scene array and four fields (`scene_number`, `narration`, `visual_description`, `visual_query`) and did not enforce the production 4/8/12/15 scene count, `visual_subject_type`, query length, or case-insensitive query uniqueness. The inspection modified nothing;
- production migration `db/migrations/002_add_scene_visual_subject_type.sql` has now been applied successfully to PostgreSQL. Before destructive cleanup, the production `public` schema/data was backed up in PostgreSQL custom format at `/tmp/ai-short-form-content-factory-public-20260823T121528Z.dump` inside the PostgreSQL container and on the VPS host; both copies were validated and have SHA-256 `f147aaff08278aa09d467f5661a3b0d6e50ff5376a27faf364273678016ee39a`;
- the only rows blocking migration 002 were the verified disposable M2 manual SQL-test job `b2c1fc1c-e5f1-468b-a64d-7eeca2cb963d` and its two test scenes. Exact precondition checks confirmed the known topic, two known test scenes, zero assets, and zero publications. Deleting that one M2 test job removed exactly those two scenes through the existing `ON DELETE CASCADE` relationship;
- after migration 002, `public.scenes.visual_subject_type` exists as `TEXT NOT NULL`; constraint `scenes_visual_subject_type_check` is present and PostgreSQL reports `CHECK ((visual_subject_type = ANY (ARRAY['factual'::text, 'generic'::text])))`;
- a rollback-only functional database probe confirmed that `factual` and `generic` are accepted, an invalid value is rejected by the check constraint, and `NULL` is rejected by the NOT NULL constraint;
- retained production application data was fingerprinted before and after the M2 cleanup/migration. The fingerprints were unchanged: `jobs|1|8db8e4e9a7eebb6a76c7f52e5cdad46b`, `scenes|0|d41d8cd98f00b204e9800998ecf8427e`, `assets|0|d41d8cd98f00b204e9800998ecf8427e`, and `publications|0|d41d8cd98f00b204e9800998ecf8427e`;
- retained M3 job `ba081017-2345-4212-a1c4-cde6df8de574` was unchanged across cleanup/migration; its before/after fingerprint was `0e746abfd825776756963d40d0a7224c`. The current production scene count is zero;
- the first production attempt to apply migration 002 had previously been safely blocked and rolled back because two legacy M2 test scenes had no factual/generic classification; no classification was guessed and no partial migration state was left behind;
- on the VPS, the previously untracked `n8n/` directory was inspected without deletion; it contained exactly `n8n/workflows/WF01-create-content-job.json`, and both its file list and SHA-256 matched the committed M3 copy; the local file SHA-256 was `f5fee4f6ffc570cb6f3001e223c982bdeddd5d5a9fbdf38f18859ba8b97d4672`;
- the verified duplicate VPS `n8n/` directory was moved to recoverable backup `/tmp/ai-short-form-content-factory-n8n-backup-20260823T120403Z`; the backed-up WF01 retained SHA-256 `f5fee4f6ffc570cb6f3001e223c982bdeddd5d5a9fbdf38f18859ba8b97d4672`;
- the VPS repository checkout was switched safely from `feat/m3-n8n-intake` to `feat/m4-script-scene-planning` and is used for M4 runtime work;
- the production v1 M4 scene contract is an explicit project decision: 15/30/45/60-second jobs require exactly 4/8/12/15 scenes, and each scene maps to one narration segment, one later voiceover file, one selected visual asset, and one rendered timeline segment;
- each planned scene requires `visual_subject_type = factual|generic`, target-language `visual_description`, and a case-insensitively unique English `visual_query` no longer than 100 characters; factual scenes route to Wikimedia Commons and generic scenes route to Pixabay with Pexels fallback;
- the clean-install schema includes `scenes.visual_subject_type`, and migration 002 now brings the production database to the same required scene-subject contract;
- `Validate Structured Plan` previously passed against a real Gemini response under the older five-scene test contract: it parsed the model text, accepted five sequential scenes with non-empty required fields, restored the original job context, and emitted normalized scenes plus AI metadata; this is transport proof only and is not acceptance for the current 4/8/12/15 scene contract;
- the production `Generate Structured Plan` HTTP Request previously completed one real Google Gemini API call with `gemini-3.5-flash-lite`; the response finished with `STOP`, returned structured JSON containing five scenes, and reported 248 prompt tokens, 424 candidate tokens, and 672 total tokens; this proves the API/structured-output transport, not the current M4 contract or narration quality;
- the production WF02 input block is assembled in n8n as `Receive Job ID` -> `Normalize Job ID` -> `Load Eligible Job` -> `Require Eligible Job`;
- the complete four-node input block passed a real PostgreSQL-backed test with job `ba081017-2345-4212-a1c4-cde6df8de574`: `job_exists = true`, `eligible = true`, `language_code = 'en'`, `target_duration_seconds = 60`, `status = 'created'`, and `current_stage = 'intake'`;
- M4 feature branch `feat/m4-script-scene-planning` was created from the completed M3 `main` state;
- the repository itself contains no AI credential or API secret;
- repository foundation;
- M1 Docker foundation;
- M2 PostgreSQL application-state validation;
- three-service runtime is deployed on the VPS;
- public access to the new n8n instance is configured;
- n8n owner account is configured;
- production workflow shell `WF01 — Create Content Job` exists in n8n with ID `Xy94qe35OigtMxkR`;
- the complete WF01 M3 graph is configured and published in n8n;
- production HTTP testing returned 400 for invalid input and 201 with a generated `job_id` for valid input;
- direct PostgreSQL verification confirmed the invalid request inserted zero rows and the valid request inserted exactly one row;
- the PostgreSQL UUID matches the `job_id` returned by the production webhook;
- M3 runtime acceptance has passed with Script & Scene Planning disconnected and no AI call;
- n8n CLI exported one workflow and the file was copied to `n8n/workflows/WF01-create-content-job.json` in the VPS repository checkout;
- the exported workflow file is 7125 bytes, contains workflow ID `Xy94qe35OigtMxkR`, and matched neither `POSTGRES_PASSWORD` nor `N8N_ENCRYPTION_KEY` runtime values;
- the exported workflow passed structural validation: exactly six expected nodes, correct valid/invalid routing, parameterized PostgreSQL INSERT, HTTP 400/201 responses, and no AI or sub-workflow nodes;
- the export contains only the `Application PostgreSQL` credential reference, contains no credential value or runtime secret, and has SHA-256 `f5fee4f6ffc570cb6f3001e223c982bdeddd5d5a9fbdf38f18859ba8b97d4672`;
- `n8n/workflows/WF01-create-content-job.json` is committed on `feat/m3-n8n-intake` in commit `82747eba4ad7d8fd3f27dcced1f8583e0601a6e9`;
- `publisher.hodor.com.pl` routes to the new n8n instance;
- staged n8n workflow topology is defined in `docs/ARCHITECTURE.md`;
- internal stage hand-off is finalized as native n8n sub-workflow execution with `job_id`, not public HTTP webhooks;
- render boundary is finalized as synchronous-first `n8n -> media-worker -> n8n -> PostgreSQL`; async render is deferred until real behavior proves it necessary;
- media-worker is not allowed to write product state directly to PostgreSQL;
- human review is a real STOP boundary after `review_ready`; Buffer publishing starts only from a later explicit human action;
- idempotency is treated as a stage-specific concern, not an automatic property of split workflows;
- watchdog/reconciler/retry infrastructure remains deliberately deferred until real quality runs reveal recurring failure patterns.

## Runtime

VPS SSH target:

`root@37.27.87.6`

Project path:

`/opt/ai-short-form-content-factory`

Services:

- `n8n`;
- `postgres`;
- `media-worker`.

Public n8n URL:

`https://publisher.hodor.com.pl/`

Planned production Studio URL:

`https://studio.hodor.com.pl/`

The Studio URL is the user-facing project site. The publisher URL remains the public n8n endpoint.

The new n8n host port remains bound to localhost and public traffic reaches it through the existing Caddy reverse proxy.

Protected existing work runtime:

`/opt/n8n`

Do not modify or remove that runtime except for a narrowly required, backed-up, validated Caddy configuration change.

## Database

Application tables in `public`:

- `jobs`;
- `scenes`;
- `assets`;
- `publications`.

The `n8n` schema belongs to n8n and must not be modified manually.

Current schema naming that must be respected:

- `jobs.language_code`;
- `jobs.target_duration_seconds`;
- `jobs.last_error`;
- `scenes.audio_path`;
- `scenes.visual_path`;
- `scenes.duration_seconds`;
- `scenes.visual_subject_type`.

`scenes.visual_subject_type` is now present in production PostgreSQL as `TEXT NOT NULL` with allowed values `factual` and `generic`.

Do not silently replace these with alternative names from external architecture suggestions.

`jobs.status` and `jobs.current_stage` are separate concepts:

- `status` is the lifecycle/result state;
- `current_stage` identifies the stage currently responsible for work or failure.

No migration is needed merely to encode proposed state names while the existing TEXT columns are sufficient.

## Current workflow topology

The product is not implemented as one giant n8n workflow.

```text
PUBLIC ENTRY
Job Intake
  -> Script & Scene Planning
  -> Voiceover Generation
  -> Visual Sourcing
  -> Video Render
  -> review_ready
  -> STOP

HUMAN ACTION
  -> Buffer Draft Publishing
```

Stage hand-off contract:

- internal automatic stages use native n8n sub-workflow execution, not public HTTP webhooks;
- `job_id` is the normal hand-off payload;
- each stage reloads the durable state it needs from PostgreSQL;
- each stage checks that the job is eligible for the stage;
- a stage persists its result before starting the next stage;
- failure prevents the next stage from starting;
- a stage being separate does not by itself make it idempotent.

Public webhooks are reserved for real external boundaries such as Job Intake and the later human review action.

## Render boundary

Initial render design:

```text
n8n
  -> POST /render to media-worker
  -> media-worker performs FFmpeg work and returns the result
  -> n8n validates it
  -> n8n writes final_video_path and review_ready to PostgreSQL
```

Do not add `render_id`, asynchronous callbacks, polling, or direct media-worker database writes before real render behavior proves that the synchronous HTTP boundary is insufficient.

## Human review boundary

After a successful render:

```text
final_video_path persisted
status = review_ready
current_stage = review
generation execution stops
```

The later review UI creates the explicit user action that may start Buffer Draft Publishing.
Do not combine Human Review and Buffer publishing into one long-running workflow.

## Current task

Implement the production `Script & Scene Planning` stage as a separate n8n workflow.

M4 scope only:

```text
job_id
  -> load and validate eligible job
  -> one AI request for structured script + scene plan
  -> validate the complete structured result
  -> malformed: fail without inserting scenes
  -> valid: persist all scenes and update job state
```

Do not implement Voiceover Generation yet.
Do not add retry, dispatcher, queue, watchdog, or generic idempotency infrastructure.

## Exact next action

Export the current production WF02 workflow `TJfA4ZYUEKSTad6k` (`WF02 — Plan Script and Scenes`) into the repository on `feat/m4-script-scene-planning`, verify the exported workflow contains the updated production planning contract and no credential values or runtime secrets, and commit that export before adding PostgreSQL scene persistence or job-state mutation. The successful 60-second structural contract run used the synthetic marker topic, so manual script/visual quality acceptance for a meaningful real topic remains required before M4 can be considered complete.

## Working rules

Before answering or acting on this project:

1. fetch the current `docs/CURRENT_STATE.md` from the active feature branch on every technical turn;
2. fetch `docs/ARCHITECTURE.md` when architecture is involved;
3. fetch `docs/ROADMAP.md` when milestone scope or acceptance is involved;
4. do not replace missing facts with remembered chat guesses;
5. if proposing a new architecture decision, label it as a new proposal before changing the source of truth;
6. after every completed implementation or runtime step, update this file in the same feature branch;
7. export production n8n workflows into the repository so workflow structure is not dependent on chat memory.

## Do not do

- no giant single n8n workflow for the whole lifecycle;
- no public webhook chaining between internal automatic stages;
- no custom dispatcher;
- no watchdog/reconciler at this stage;
- no PostgreSQL polling queue;
- no Redis;
- no n8n queue mode;
- no leases/fencing/reconciliation engine;
- no generic retry/idempotency framework before concrete failure patterns require it;
- no direct product-state writes from media-worker to PostgreSQL;
- no async render infrastructure before synchronous render is proven insufficient;
- no extra microservices without a demonstrated requirement;
- no secrets in GitHub;
- no global Docker prune operations on the shared VPS;
- do not delete or casually modify the protected `/opt/n8n` work runtime;
- do not start M5 before M4 passes its real acceptance checks.