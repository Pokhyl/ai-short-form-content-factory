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

Start with one main n8n workflow.

```text
Intake
  -> Create job
  -> Generate script
  -> Save scenes
  -> Generate voiceovers
  -> Source visuals
  -> Render
  -> Review-ready
  -> Buffer draft
```

A sub-workflow is introduced only when extraction makes the main workflow objectively easier to understand or reuse.

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
final.mp4 -> Buffer draft -> manual review -> publish
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
