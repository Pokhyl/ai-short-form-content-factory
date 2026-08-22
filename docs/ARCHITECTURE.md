# Architecture — Source of Truth

Last updated: 2026-08-22

This document is the current architecture source of truth for the clean rebuild.
If older prototypes, screenshots, deleted repositories, previous workflow designs, or chat suggestions conflict with this file, this file wins unless it is explicitly updated.

## Product

A self-hosted automation system that turns a topic into a short vertical video, allows human review, and sends approved output to social publishing.

Target flow:

```text
Topic
  -> Script + scene plan
  -> Voiceover
  -> Visual sourcing
  -> Render
  -> Human review
  -> Buffer draft
```

Additional platforms are added only after Buffer draft publishing is stable.

## Runtime

Exactly three services are planned for the first complete version:

1. `n8n`
2. `postgres`
3. `media-worker`

Do not add a fourth service without a concrete requirement that cannot be solved cleanly inside these three.

## Responsibilities

### n8n

Owns orchestration and integrations:

- public intake;
- internal stage orchestration;
- external API calls;
- branching and loops;
- PostgreSQL reads/writes;
- TTS requests;
- visual-provider requests;
- calling media-worker;
- Buffer publishing;
- workflow-level error handling.

n8n does not own heavy media processing.

### PostgreSQL

Owns durable product state:

- jobs;
- scenes;
- selected/source assets;
- publications.

PostgreSQL is not a custom message queue.

The `n8n` schema belongs to n8n. Application tables live in `public`.

### media-worker

Owns media/file operations:

- FFmpeg;
- ffprobe;
- media validation;
- image/video normalization;
- local file storage;
- final rendering.

The worker exposes small HTTP operations instead of embedding large FFmpeg scripts in n8n Code nodes.

The media-worker does not own product-state persistence and does not write directly to PostgreSQL. n8n remains responsible for reading and writing application state.

## Orchestration model

The production pipeline is split into stage workflows. Do not build the whole product as one large n8n workflow and do not keep one execution open across the complete lifecycle.

Initial workflow topology:

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

### Internal workflow hand-off

The automatic stage workflows communicate through native n8n sub-workflow execution, not through public HTTP webhooks.

Use the n8n `Execute Sub-workflow` / sub-workflow trigger mechanism for internal hand-off. The normal hand-off payload is only:

```json
{
  "job_id": "<uuid>"
}
```

The caller should not wait for the complete downstream pipeline. Each stage is its own execution and lifecycle boundary.

Public webhooks are reserved for real external boundaries, such as `Job Intake` and the later explicit human review/publishing action.

Do not create a network of public webhooks merely to connect internal n8n workflows.

### Workflow responsibilities

#### Job Intake

Public entry point for creating a content job.

- accepts `topic`, `language`, and `duration`;
- validates input;
- creates exactly one row in `jobs`;
- returns the new `job_id` to the caller;
- a successful creation should return HTTP `201 Created`;
- when the Script & Scene Planning stage exists, it may start that internal stage only after the job exists durably.

M3 implements Job Intake only. During M3 acceptance it stops after creating the job and returning the response. It does not start Script & Scene Planning and does not call AI.

Exact topic-length and duration bounds are not yet an architecture decision. Do not invent them as pre-existing requirements. Initial supported languages are English, Polish, Russian, and Ukrainian.

#### Script & Scene Planning

- receives `job_id`;
- loads the job from PostgreSQL;
- validates that the job is eligible for this stage;
- generates the structured script and scene plan;
- validates model output;
- persists scenes;
- updates the job state;
- starts `Voiceover Generation` only after the scene plan is stored successfully.

#### Voiceover Generation

- receives `job_id`;
- loads the persisted scenes;
- validates that the job is eligible for this stage;
- generates one voiceover per scene using the configured voice for the job language;
- stores audio paths and measured durations on the scene state;
- updates the job state;
- starts `Visual Sourcing` only after all required scene audio is ready.

#### Visual Sourcing

- receives `job_id`;
- loads scenes and their visual intent;
- validates that the job is eligible for this stage;
- searches the configured providers;
- persists selected asset metadata and local paths;
- uses a local fallback when no acceptable external asset exists;
- updates the job state;
- starts `Video Render` only after every scene has usable visual material.

#### Video Render

- receives `job_id`;
- loads the complete persisted job state;
- validates that the job is eligible for rendering;
- calls `media-worker` for normalization and FFmpeg rendering;
- validates the rendered output;
- stores `final_video_path` through n8n into PostgreSQL;
- marks the job `review_ready`;
- stops. It does not publish automatically.

The first render implementation is synchronous from n8n's point of view:

```text
n8n
  -> POST /render to media-worker
  -> media-worker renders and returns result
  -> n8n validates result
  -> n8n writes final_video_path and review_ready
```

Do not introduce `render_id`, asynchronous callbacks, polling, or direct media-worker database writes before real render behavior proves that the synchronous HTTP boundary is insufficient.

#### Buffer Draft Publishing

This workflow is outside the automatic generation chain.

- starts only after an explicit human approval action;
- receives `job_id`;
- reloads the job from PostgreSQL;
- verifies that an approved, completed rendered video exists;
- sends the approved video to Buffer as a draft;
- persists the publishing result in `publications`.

The exact review UI trigger is implemented when the review UI/publishing milestones are reached. The generation execution does not wait for human input.

## Workflow hand-off contract

`job_id` is the contract between automatic stage workflows.

Each stage:

1. receives `job_id`;
2. reloads the durable state it needs from PostgreSQL;
3. checks that the job is eligible for the stage;
4. updates `jobs.current_stage` before or as the stage begins;
5. performs only its own responsibility;
6. persists its output before starting the next stage;
7. starts the next internal workflow only after successful persistence;
8. on failure, records the error and does not start the next stage.

Do not pass large scripts, asset collections, audio binaries, or render manifests between n8n stage workflows when they can be reloaded from durable state.

## Job state semantics

`jobs.status` and `jobs.current_stage` have different meanings.

- `status` describes the lifecycle/result state of the job, for example `created`, `processing`, `review_ready`, `approved`, `rejected`, `drafted`, or `failed`.
- `current_stage` identifies the stage responsible for the current work or failure, for example `intake`, `script`, `voiceover`, `visuals`, `render`, `review`, or `publish`.

These are semantic conventions on existing TEXT columns. Do not add a migration only to enforce these values before real workflow behavior requires one.

## Idempotency and repeated execution

Splitting the pipeline into separate workflows does not automatically make stages idempotent.

A repeated stage can otherwise repeat an external side effect such as:

- an LLM request;
- a TTS request;
- an asset download;
- a render;
- a publication request.

Add the smallest stage-specific guard when that side effect is implemented and tested. Prefer existing durable state, unique constraints, explicit eligibility checks, or safe upsert behavior where appropriate.

Do not build a generic idempotency/retry framework before concrete stage behavior requires it.

## Error and reliability model

A failed stage records:

- `jobs.status = 'failed'`;
- the relevant `jobs.current_stage`;
- `jobs.last_error`.

The n8n execution may then fail normally.

The first complete pipeline deliberately does not include:

- watchdog/reconciler workflows;
- PostgreSQL polling queues;
- automatic retry orchestration;
- `job_events` infrastructure solely for recovery;
- custom dispatchers;
- leases;
- fencing;
- reconciliation engines;
- Redis queue;
- n8n queue mode;
- event bus;
- Kubernetes;
- extra microservices without a current requirement.

Retry and recovery design comes after real end-to-end quality runs reveal concrete recurring failure patterns.

## Human review boundary

Human review is a real lifecycle break, not a long-running generation execution.

After a successful render:

```text
final_video_path persisted
status = review_ready
current_stage = review
generation execution stops
```

The later review UI displays the rendered result and job state. Approval or rejection is a new user action and a new execution.

Approval may start `Buffer Draft Publishing`. Rejection/revision behavior is designed during the review milestone based on the actual UI and editing requirements.

Do not combine Human Review and Buffer publishing into one long-running workflow.

## Visual sourcing

Visual sourcing must never stop the whole product merely because no good stock asset exists.

Initial policy:

```text
exact/factual subject -> Wikimedia Commons

generic subject       -> Pixabay
                        -> Pexels fallback
```

For each scene:

1. search a bounded candidate set;
2. reject unusable metadata/file types deterministically;
3. rank/select a suitable candidate;
4. download only the selected original;
5. normalize it before render.

If no acceptable asset exists, use a local graphic/text fallback scene instead of a misleading random image.

Large files are validated and normalized before the render/publish stage.

## Voiceover

The exact voice presets previously selected by the project owner are a product decision and must be reused.

The IDs are not guessed. They are recovered from the previous runtime/configuration and then written into the runtime voice configuration.

Supported initial languages:

- English
- Polish
- Russian
- Ukrainian

## Publishing

Buffer is the first publishing integration because draft publishing already worked reliably in the previous prototype.

Initial target:

```text
final.mp4 -> human review -> Buffer draft
```

Direct TikTok/Instagram/YouTube API publishing is a later milestone, not a prerequisite for the first complete product.

## UI direction

The previous Studio screen is retained only as a UX reference, not as code.

Desired layout:

- left: create a new video — topic, language, duration;
- right: current job — title, metadata, stage progress;
- stages: Script -> Voice -> Materials -> Render -> Publish;
- visible error state with a human-readable message;
- later: recent jobs and final-video preview.

The UI implementation is new.

## Cost policy

The project is free-first.

Rules:

1. prefer self-hosted processing;
2. prefer free/free-tier external providers where quality is acceptable;
3. never silently fall back to a paid provider;
4. record external provider choice explicitly in configuration;
5. recurring paid infrastructure requires an explicit architecture decision.

## Security

The repository is public.

Never commit:

- `.env`;
- API keys;
- OAuth access/refresh tokens;
- database passwords;
- n8n encryption keys;
- exported credentials;
- private generated media.

## Acceptance philosophy

A stage is complete only when its real output is acceptable.

Examples:

- script: coherent and usable;
- voice: sounds acceptable in the target language;
- visuals: actually match the scene;
- render: valid 9:16 video with correct audio/subtitles;
- publishing: draft really appears in Buffer.

A green technical execution alone is not acceptance.
