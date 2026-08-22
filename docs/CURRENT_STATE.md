# Current Project State

Last updated: 2026-08-22

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
- `publisher.hodor.com.pl` routes to the new n8n instance;
- staged n8n workflow topology is defined in `docs/ARCHITECTURE.md`.

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

## Current workflow topology

The product is not implemented as one giant n8n workflow.

```text
Job Intake
  -> Script & Scene Planning
  -> Voiceover Generation
  -> Visual Sourcing
  -> Video Render
  -> review_ready

Human review
  -> Buffer Draft Publishing
```

Stage hand-off contract:

- `job_id` is passed between stage workflows;
- each stage reloads the durable state it needs from PostgreSQL;
- a stage persists its result before starting the next stage;
- failure prevents the next stage from starting.

## Current task

Implement the production `Job Intake` workflow in n8n.

M3 scope only:

```text
topic + language + duration
  -> validate
  -> INSERT one row into jobs
  -> return job_id
```

Do not implement AI generation yet.
Do not implement later stage workflows yet.

## Exact next action

Create the production `Job Intake` workflow in the new n8n instance and configure its public intake trigger and validation path according to M3 acceptance criteria.

After the workflow is built, export its JSON into the repository under `n8n/workflows/` and validate M3 with real HTTP requests and direct PostgreSQL checks before merging PR #4.

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
- no custom dispatcher;
- no Redis;
- no n8n queue mode;
- no leases/fencing/reconciliation engine;
- no extra microservices without a demonstrated requirement;
- no secrets in GitHub;
- no global Docker prune operations on the shared VPS;
- do not delete or casually modify the protected `/opt/n8n` work runtime;
- do not start M4 before M3 passes its real acceptance checks.
