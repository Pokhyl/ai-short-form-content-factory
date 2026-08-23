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
After every completed implementation or runtime step, update this file before moving on.

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

- direct read-only PostgreSQL verification of the successful `Persist Scene Plan` execution has passed for retained job `ba081017-2345-4212-a1c4-cde6df8de574`. The job is exactly `status = processing`, `current_stage = script`, `last_error IS NULL`. PostgreSQL contains exactly 15 scenes numbered 1..15 with 15 distinct scene numbers; every scene has `status = planned`, non-empty narration, non-empty visual description, non-empty visual query, `visual_subject_type` limited to `factual|generic`, query length no more than 100 characters, and all 15 visual queries remain case-insensitively distinct. `audio_path`, `visual_path`, and `duration_seconds` are NULL for all 15 scenes. The job has 0 assets and 0 publications. The final aggregate persistence check returned `PASS`. This establishes structural persistence acceptance for the retained synthetic marker job; manual script/visual quality acceptance still requires a meaningful real topic;
- live WF02 contains `Persist Scene Plan` directly after `Validate Structured Plan`. The first execution was rejected before any write because `Query Parameters` had been entered as literal text, causing PostgreSQL to receive the literal `$json.job_id` instead of a UUID. After correcting the n8n expression to `{{ [ $json.job_id, JSON.stringify($json.scenes) ] }}`, the node completed successfully for retained job `ba081017-2345-4212-a1c4-cde6df8de574` and returned `status = processing`, `current_stage = script`, `inserted_scene_count = 15`, `expected_scene_count = 15`, with `updated_at = 2026-08-23T13:14:45.180Z`;
- the read-only M4 persistence inspection is complete. Production PostgreSQL is `content_factory` on PostgreSQL 18.6 and the application schema contains exactly `jobs`, `scenes`, `assets`, and `publications`. `jobs` has the expected lifecycle/state columns and no triggers; `scenes` has `UNIQUE (job_id, scene_number)`, FK `job_id -> jobs(id) ON DELETE CASCADE`, `visual_subject_type TEXT NOT NULL` with the factual/generic CHECK, nullable narration/visual-description/query/audio/visual/duration fields, and default `status = 'planned'`. `jobs` and `scenes` have RLS disabled, no public functions/procedures reference them, and there is no application migration-tracking table. The retained M3 job `ba081017-2345-4212-a1c4-cde6df8de574` was `status = 'created'`, `current_stage = 'intake'`, duration 60, language `en`, with 0 scenes, 0 assets, and 0 publications before the persistence execution. There were no duplicate scene numbers anywhere. This inspection modified nothing. Therefore M4 persistence does not require another schema migration, trigger, or database function; the smallest implementation is one PostgreSQL node after `Validate Structured Plan` using one atomic SQL statement that rechecks/locks job eligibility, writes the full validated scene set, and updates job state only if the complete write succeeds;
- production WF02 export is fully verified, committed, and present on GitHub for the pre-persistence seven-node version. The live workflow `TJfA4ZYUEKSTad6k` (`WF02 — Plan Script and Scenes`) was exported once from production and saved as `n8n/workflows/WF02-plan-script-and-scenes.json`; that export is 19,533 bytes with SHA-256 `0be23f3835b85c72cc1bc78c721ca35c617cb8c9fa1ededfb7b0d8694923a03e`. Validation confirmed exactly seven expected nodes, the updated duration-derived Gemini schema, the production M4 validator, terminal `Validate Structured Plan`, credential references only, and absence of known runtime secrets. The export commit is `58c9640c0b903c35ef506ec7f7d1daef6f5721c2` (`feat(m4): export script planning workflow`). Because `Persist Scene Plan` has now been added live and persistence verification passed, WF02 must now be exported again as the eight-node production version;
- the updated live WF02 planning contract passed one real 60-second structural run for retained job `ba081017-2345-4212-a1c4-cde6df8de574`. `Validate Structured Plan` returned exactly 15 sequential scenes numbered 1..15; every scene contained all five required fields; `visual_subject_type` was always exactly `factual` or `generic`; the validator therefore also confirmed non-empty required strings, English `visual_query` values no longer than 100 characters, and case-insensitive query uniqueness. The Gemini response used model `gemini-3.5-flash-lite`, response ID `dOqKaqXPOJGmkdUP2qW1kQk`, 507 prompt tokens, 981 output tokens, and 1488 total tokens. Because the job topic is the synthetic M3 marker `M3_VALID_BB26793B-3A2E-4B5C-AD8D-2FD22D97CA03`, this run is structural acceptance only and is not yet manual quality acceptance for a meaningful real topic;
- a second read-only inspection of saved live WF02 configuration identified the earlier mismatch exactly: `Build Planning Request` was already on the new M4 contract, while both downstream nodes were still saved in their old versions. `Generate Structured Plan` still had `responseJsonSchema.scenes.minItems = 1`, no exact `maxItems`, no `visual_subject_type` property, and only four required scene fields. `Validate Structured Plan` still accepted any non-empty scene array, required only `scene_number`, `narration`, `visual_description`, and `visual_query`, and did not enforce duration-specific scene count, `visual_subject_type`, query length, or case-insensitive query uniqueness. Those two nodes were subsequently corrected and the structural contract passed;
- the first real 60-second run after updating only `Build Planning Request` returned exactly 15 sequential scenes from `gemini-3.5-flash-lite`, but every scene lacked `visual_subject_type` and the old validator nevertheless accepted the output. That failed contract run used response ID `XeiKatXWBYirnsEP8tDG0AY` with 507 prompt tokens, 1178 output tokens, and 1685 total tokens. At that time no persistence node existed, so it created no scene rows or job-state mutation;
- the live WF02 `Build Planning Request` node emits the production duration-specific planning contract for the retained 60-second M3 job: `required_scene_count = 15`, language `English`, and a prompt/output shape containing exactly the five required scene fields `scene_number`, `narration`, `visual_subject_type`, `visual_description`, and `visual_query`. The generated instructions require exactly 15 scenes, sequential numbering, target-language narration/visual description, `factual|generic` classification, non-empty English visual queries no longer than 100 characters and unique ignoring case, and explicitly exclude `duration_seconds` and concrete provider/asset selection;
- production migration `db/migrations/002_add_scene_visual_subject_type.sql` has been applied successfully to PostgreSQL. Before destructive cleanup, the production `public` schema/data was backed up in PostgreSQL custom format at `/tmp/ai-short-form-content-factory-public-20260823T121528Z.dump` inside the PostgreSQL container and on the VPS host; both copies were validated and have SHA-256 `f147aaff08278aa09d467f5661a3b0d6e50ff5376a27faf364273678016ee39a`;
- the only rows blocking migration 002 were the verified disposable M2 manual SQL-test job `b2c1fc1c-e5f1-468b-a64d-7eeca2cb963d` and its two test scenes. Exact precondition checks confirmed the known topic, two known test scenes, zero assets, and zero publications. Deleting that one M2 test job removed exactly those two scenes through the existing `ON DELETE CASCADE` relationship;
- after migration 002, `public.scenes.visual_subject_type` exists as `TEXT NOT NULL`; constraint `scenes_visual_subject_type_check` is present and PostgreSQL reports `CHECK ((visual_subject_type = ANY (ARRAY['factual'::text, 'generic'::text])))`;
- a rollback-only functional database probe confirmed that `factual` and `generic` are accepted, an invalid value is rejected by the check constraint, and `NULL` is rejected by the NOT NULL constraint;
- retained production application data was fingerprinted before and after the M2 cleanup/migration and the retained M3 job fingerprint was unchanged before persistence;
- on the VPS, the previously untracked `n8n/` directory was inspected without deletion; it contained exactly `n8n/workflows/WF01-create-content-job.json`, and both its file list and SHA-256 matched the committed M3 copy; the duplicate VPS copy was moved to recoverable backup `/tmp/ai-short-form-content-factory-n8n-backup-20260823T120403Z`;
- the VPS repository checkout is on `feat/m4-script-scene-planning` and is used for M4 runtime work;
- the production v1 M4 scene contract is an explicit project decision: 15/30/45/60-second jobs require exactly 4/8/12/15 scenes, and each scene maps to one narration segment, one later voiceover file, one selected visual asset, and one rendered timeline segment;
- each planned scene requires `visual_subject_type = factual|generic`, target-language `visual_description`, and a case-insensitively unique English `visual_query` no longer than 100 characters; factual scenes route to Wikimedia Commons and generic scenes route to Pixabay with Pexels fallback;
- the clean-install schema includes `scenes.visual_subject_type`, and migration 002 brings the production database to the same required scene-subject contract;
- the production WF02 input block is assembled in n8n as `Receive Job ID` -> `Normalize Job ID` -> `Load Eligible Job` -> `Require Eligible Job`;
- the complete four-node input block passed a real PostgreSQL-backed test with job `ba081017-2345-4212-a1c4-cde6df8de574`: `job_exists = true`, `eligible = true`, `language_code = 'en'`, `target_duration_seconds = 60`, `status = 'created'`, and `current_stage = 'intake'` before persistence;
- M4 feature branch `feat/m4-script-scene-planning` was created from the completed M3 `main` state;
- the repository itself contains no AI credential or API secret;
- repository foundation, M1 Docker foundation, M2 PostgreSQL application-state validation, and M3 n8n intake are complete;
- the three-service runtime is deployed on the VPS and `publisher.hodor.com.pl` routes to the new n8n instance;
- internal stage hand-off is native n8n sub-workflow execution with `job_id`, not public HTTP webhooks;
- render boundary is synchronous-first `n8n -> media-worker -> n8n -> PostgreSQL`;
- media-worker is not allowed to write product state directly to PostgreSQL;
- human review is a real STOP boundary after `review_ready`;
- retry/dispatcher/watchdog/queue infrastructure remains deliberately deferred.

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

`scenes.visual_subject_type` is present in production PostgreSQL as `TEXT NOT NULL` with allowed values `factual` and `generic`.

`jobs.status` and `jobs.current_stage` are separate concepts:

- `status` is the lifecycle/result state;
- `current_stage` identifies the stage currently responsible for work or failure.

After successful atomic M4 persistence, the intended state is `status = processing`, `current_stage = script`; Voiceover changes `current_stage` only when M5 actually begins.

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

Export the updated live eight-node WF02 now that direct PostgreSQL persistence verification has passed. Verify the exported workflow is `TJfA4ZYUEKSTad6k` / `WF02 — Plan Script and Scenes`, contains exactly the previous seven nodes plus `Persist Scene Plan`, preserves the validated Gemini request/schema/validator contract, contains the atomic persistence SQL and expression `{{ [ $json.job_id, JSON.stringify($json.scenes) ] }}`, keeps `Persist Scene Plan` terminal, contains credential references only, and contains no runtime secrets. Replace `n8n/workflows/WF02-plan-script-and-scenes.json` with that verified export and commit/push it on `feat/m4-script-scene-planning` before any further M4 work. Manual script/visual quality acceptance on a meaningful real topic remains required before M4 can be considered complete.

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