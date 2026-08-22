# Architecture — Source of Truth

Last updated: 2026-08-22

This document is the current architecture source of truth for the clean rebuild.
If older prototypes, screenshots, deleted repositories, or previous workflow designs conflict with this file, this file wins unless it is explicitly updated.

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

- intake;
- external API calls;
- branching and loops;
- PostgreSQL reads/writes;
- TTS requests;
- visual-provider requests;
- calling media-worker;
- Buffer publishing;
- workflow-level error reporting.

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

The worker should expose small HTTP operations instead of embedding large FFmpeg scripts in n8n Code nodes.

## Orchestration model

The production pipeline is split into stage workflows. Do not build the whole product as one large n8n workflow and do not keep one execution open across the complete lifecycle.

Initial workflow topology:

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

### Workflow responsibilities

#### Job Intake

Public entry point for creating a content job.

- accepts `topic`, `language`, and `duration`;
- validates input;
- creates exactly one row in `jobs`;
- returns the new `job_id` to the caller;
- starts `Script & Scene Planning` with that `job_id` only after the job exists durably.

M3 implements this workflow only. It does not call AI yet during M3 acceptance testing.

#### Script & Scene Planning

- receives `job_id`;
- loads the job from PostgreSQL;
- generates the structured script and scene plan;
- validates model output;
- persists scenes;
- starts `Voiceover Generation` only after the scene plan is stored successfully.

#### Voiceover Generation

- receives `job_id`;
- loads the persisted scenes;
- generates one voiceover per scene using the configured voice for the job language;
- stores audio paths and measured durations;
- starts `Visual Sourcing` only after all required scene audio is ready.

#### Visual Sourcing

- receives `job_id`;
- loads scenes and their visual intent;
- searches the configured providers;
- persists selected asset metadata and local paths;
- uses a local fallback when no acceptable external asset exists;
- starts `Video Render` only after every scene has usable visual material.

#### Video Render

- receives `job_id`;
- loads the complete persisted job state;
- calls `media-worker` for normalization and FFmpeg rendering;
- validates the rendered output;
- stores `final_video_path`;
- marks the job `review_ready`;
- stops. It does not publish automatically.

#### Buffer Draft Publishing

This workflow is outside the automatic generation chain.

- starts only after an explicit human review action;
- receives `job_id`;
- verifies that a completed rendered video exists;
- sends the approved video to Buffer as a draft;
- persists the publishing result in `publications`.

The exact review UI trigger is implemented when the review UI/publishing milestones are reached. Do not keep the generation execution waiting for human input.

### Workflow hand-off contract

`job_id` is the contract between stage workflows.

Each stage:

1. receives `job_id`;
2. reloads the durable state it needs from PostgreSQL;
3. updates `jobs.current_stage` before or as the stage begins;
4. performs only its own responsibility;
5. persists its output before starting the next stage;
6. starts the next workflow only after successful persistence;
7. on failure, records the error and does not start the next stage.

Stage workflows are internal n8n workflows and are not exposed as public webhooks merely to pass data between stages. The public entry point is `Job Intake`; the later human review action provides the explicit entry point for publishing.

This design deliberately avoids one giant workflow while also avoiding a custom orchestration platform. n8n remains the orchestrator and PostgreSQL remains the durable source of truth.

Do not build:

- custom dispatcher;
- leases;
- fencing;
- reconciliation engine;
- Redis queue;
- n8n queue mode;
- event bus;
- Kubernetes;
- microservices without a current requirement.

## Error model

A failed stage records:

- `jobs.status = 'failed'`;
- `jobs.current_stage`;
- `jobs.last_error`.

The n8n execution may then fail normally.

Retry design comes after the first working end-to-end pipeline. Do not build a recovery subsystem before a real failure pattern proves it is required.

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
