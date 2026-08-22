# AI Short-Form Content Factory

Self-hosted automation project for turning a topic into a reviewed short-form video for TikTok, Instagram Reels, and YouTube Shorts.

The project is intentionally designed as a practical Automation Engineering portfolio project built around **n8n, PostgreSQL, Docker, JavaScript, REST APIs, and FFmpeg**.

## Product goal

```text
Topic
  -> Script + scene plan
  -> Voiceover
  -> Visual sourcing
  -> FFmpeg render
  -> Human review
  -> Buffer draft / social publishing
```

## Architecture principles

1. **n8n orchestrates the workflow.** We do not build a second custom scheduler around it.
2. **PostgreSQL stores product state.** It is not used as a custom distributed queue.
3. **media-worker handles media work.** FFmpeg, ffprobe, file normalization, and rendering stay outside n8n.
4. **Docker Compose is the runtime boundary.** The initial stack has only three services: n8n, PostgreSQL, and media-worker.
5. **Free-first.** Prefer self-hosted and free-tier services. Paid fallbacks must never happen silently.
6. **Build only what is currently required.** No Redis, queue mode, fencing, leases, custom dispatcher, or extra microservices without a proven need.
7. **Quality is part of acceptance.** A green workflow execution is not enough; generated voice, visuals, and final video must be reviewed.

## Decisions carried into the rebuild

- Buffer remains the first publishing target because draft publishing already proved useful in the previous prototype.
- Previously selected voice presets will be reused once their exact provider voice IDs are recovered; they will not be guessed.
- The previous Studio page layout is kept as a UX reference: job creation on the left, current job and stage progress on the right. The implementation will be new.

## Initial runtime

```text
Docker Compose
  |- n8n
  |- postgres
  `- media-worker
```

PostgreSQL uses one database with two logical areas:

- schema `n8n` — n8n internal tables;
- schema `public` — application tables owned by this project.

Do not manually modify tables inside the `n8n` schema.

## Application tables

The first schema intentionally contains only:

- `jobs`
- `scenes`
- `assets`
- `publications`

Schema changes are added only when a real requirement needs them.

## Development milestones

1. Docker foundation
2. PostgreSQL application schema
3. n8n job intake
4. AI script + scene generation
5. Voiceover with selected voice presets
6. Visual sourcing
7. FFmpeg rendering
8. Quality run across multiple topics
9. Review UI
10. Buffer draft publishing
11. Additional social platforms
12. Portfolio documentation and demo

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Security

This repository is public. Never commit:

- `.env`
- API keys
- OAuth tokens
- n8n credentials
- database passwords
- generated media containing private data

Use `.env.example` only as a list of required variable names.

## Status

Foundation setup in progress.
