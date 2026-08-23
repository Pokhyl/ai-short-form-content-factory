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

M3 — n8n intake

Goal:

Submit `topic`, `language`, and `duration` through n8n and create one durable job in PostgreSQL.

Acceptance:

- invalid input is rejected;
- valid input creates exactly one `jobs` row;
- response contains the new `job_id`;
- no AI call during M3 acceptance testing.

Current M3 design decisions:

- public entry is `POST /jobs` through n8n;
- valid creation should return HTTP `201 Created`;
- PostgreSQL generates `jobs.id` with its existing UUID default;
- M3 stops after the job is created and the response is returned;
- M3 does not start Script & Scene Planning yet;
- exact topic-length and duration bounds are not yet fixed in source of truth and must not be guessed as previous decisions.
- production workflow name is `WF01 — Create Content Job`;
- production workflow ID is `Xy94qe35OigtMxkR`;
- the published production workflow contains the complete M3 path: `Receive Job Request` -> `Normalize and Validate Input` -> `Input Valid?`;
- the false branch is connected to `Return Invalid Input` and returned HTTP 400 for an unsupported `de` language request;
- the true branch is connected to `Insert Job` -> `Return Created Job` and returned HTTP 201 with `job_id` `ba081017-2345-4212-a1c4-cde6df8de574` for a valid request;
- direct PostgreSQL verification returned `invalid_rows = 0` and `valid_rows = 1`;
- the stored valid row UUID matches the HTTP response: `ba081017-2345-4212-a1c4-cde6df8de574`;
- the stored valid row has `language_code = 'en'`, `target_duration_seconds = 60`, `status = 'created'`, and `current_stage = 'intake'`;
- Script & Scene Planning remains disconnected.

## Current branch and PR

Branch:

`feat/m3-n8n-intake`

Draft PR:

`#4 — M3: implement n8n job intake`

Base branch:

`main`

Main currently includes public n8n access through merge commit:

`718301bf1e36dd4d6bef40292d8d2b22f08ee751`

## Completed

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
- `publisher.hodor.com.pl` routes to the new n8n instance;
- staged n8n workflow topology is defined in `docs/ARCHITECTURE.md`;
- internal stage hand-off is finalized as native n8n sub-workflow execution with `job_id`, not public webhook chaining;
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
- `scenes.duration_seconds`.

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
- each stage checks that the job is eligible for that stage;
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

Do not add `render_id`, async callback, polling, or direct media-worker database access before a real render test proves synchronous HTTP is insufficient.

## Human review boundary

After successful rendering:

```text
final_video_path persisted
status = review_ready
current_stage = review
generation execution stops
```

The later review UI creates the explicit user action that may start Buffer Draft Publishing.
Do not combine Human Review and Buffer publishing into one long-running workflow.

## Current task

Implement the production `Job Intake` workflow in n8n.

M3 scope only:

```text
topic + language + duration
  -> normalize/validate
  -> invalid: reject without inserting a job
  -> valid: INSERT exactly one row into jobs
  -> return HTTP 201 with job_id
```

Do not implement AI generation yet.
Do not implement later stage workflows yet.
Do not wire Job Intake to Script & Scene Planning during M3 acceptance.

## Exact next action

Export the published `WF01 — Create Content Job` workflow JSON into `n8n/workflows/`, verify that no credentials or secrets are included, then commit the export on `feat/m3-n8n-intake`.

Remaining M3 closure sequence:

1. export the production workflow JSON under `n8n/workflows/`;
2. verify the export contains workflow structure but no credentials or secrets;
3. update this file and `docs/ROADMAP.md` with the completed M3 result;
4. complete and merge PR #4 only after the repository export is committed.

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
- do not start M4 before M3 passes its real acceptance checks.
