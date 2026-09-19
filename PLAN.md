# AI Short-Form Content Factory — Production Plan

## 1. Product contract

Input:

```text
topic + language + duration
```

Supported languages:

```text
en / pl / ru / uk
```

Supported durations:

```text
15 / 30 / 45 / 60 seconds
```

Output:

```text
one finished 1080×1920 H.264/AAC MP4
```

Production path:

```text
intake
→ web research
→ evidence set
→ script + storyboard
→ one continuous final voiceover
→ local speech alignment
→ multi-source visual discovery
→ deterministic visual selection
→ local render
→ machine QA
→ HUMAN PASS
→ only then Studio / publishing
```

The deleted legacy implementation is not a baseline and must not be restored.

---

## 2. Hard rules

- n8n is the orchestrator.
- PostgreSQL is the production source of truth.
- Production is free-only.
- No paid fallback.
- No OpenAI, Anthropic, OpenRouter, Groq, ElevenLabs or FAL.
- No Ollama, local LLM or model-worker.
- No external transcription service.
- No external AI visual-verification service.
- Credentials never go to Git.
- Failed/rejected product jobs are immutable.
- A new test always creates a new job.
- One final TTS synthesis per job.
- Never speed up, slow down or trim narration to force duration.
- Never re-synthesize narration during render.
- Never hard-code topic-specific assets or fixes.
- Never weaken QA to make a test pass.
- Never touch another project, database, workflow, credential, container, repository or domain.
- Do not replace a working component unless evidence identifies it as the defect.
- Two failures from the same approach require root-cause re-evaluation, not another blind retry.
- Machine PASS is not final PASS. Only explicit HUMAN PASS accepts the product pipeline.

---

## 2.1 Production n8n architecture lock — 2026-09-19

This decision overrides any earlier assumption that the clean rebuild needs a separate production n8n instance or a new public n8n domain.

Production orchestration is hosted in the existing n8n instance:

```text
https://publisher.hodor.com.pl
```

Rules:
- `publisher.hodor.com.pl` is the single production n8n for both existing MCP/ADMIN automation and the new video project.
- The existing 22 MCP/ADMIN workflows are protected and must not be deleted, renamed, repurposed, disabled, or modified unless the user explicitly asks for that exact workflow.
- The 9 restored credentials in `publisher.hodor.com.pl` are the credential base for the video project.
- New video workflows are created in the same n8n instance with a video-specific naming prefix so they remain separate from MCP/ADMIN workflows.
- Do not create a second production n8n instance for this project.
- Do not create or repurpose a new public n8n domain for this project.
- Do not route the video project through `tiktok-n8n.hodor.com.pl`.
- Do not move the video project back to `n8n.hodor.com.pl`.
- `n8n.hodor.com.pl` is unrelated and must remain untouched.
- OAuth callbacks and public webhooks must use the existing `publisher.hodor.com.pl` n8n unless a concrete technical requirement later proves a separate endpoint is mandatory.
- A separate endpoint/domain may be introduced only after a documented technical blocker is proven and the user explicitly agrees.

Supporting runtime remains isolated from n8n orchestration:
- project PostgreSQL;
- media-worker;
- SearXNG;
- local media/alignment tooling.

The bootstrap `shorts-v2` n8n container was removed on 2026-09-19 after its temporary M2 workflows/credentials were backed up and deleted. The supporting Compose stack now contains only PostgreSQL, media-worker and SearXNG.

Reason for this lock:
- credentials were restored into `publisher.hodor.com.pl` specifically so the video project can use them there;
- introducing another n8n/domain creates unnecessary credential migration, OAuth, routing, authentication and state-consistency problems;
- the attempted `tiktok-n8n.hodor.com.pl` detour was unnecessary and was rolled back.

---

## 3. Runtime architecture

Use `publisher.hodor.com.pl` as the production n8n orchestrator. Keep only the project-supporting services isolated in this repository.

Production n8n:

```text
publisher.hodor.com.pl
```

Supporting services:

```text
postgres
media-worker
searxng
```

Responsibilities:

### publisher.hodor.com.pl / n8n
- production workflow orchestration for the video project;
- state transitions;
- provider calls;
- retries only where explicitly allowed;
- no heavy media processing;
- existing MCP/ADMIN workflows remain protected and separate from video workflows.

### PostgreSQL
- jobs;
- evidence;
- scenes/shots;
- external-operation ledger;
- media metadata;
- QA results;
- immutable failure history.

### media-worker
- download/store media;
- ffprobe/ffmpeg;
- local speech alignment;
- image/video normalization;
- local deterministic visual checks;
- render;
- machine media QA.

### SearXNG
- self-hosted web-search layer for research;
- JSON API;
- broad web search across configured engines;
- not limited to Wikipedia/Wikimedia.

Do not add Redis/queue mode until measured load requires it.

---

## 4. Research architecture

Research must search the web, not only Wikipedia.

Flow:

```text
topic
→ SearXNG search queries
→ ranked search results
→ fetch selected public pages
→ extract readable text
→ deduplicate sources
→ evidence rows
→ Gemini synthesis from evidence only
```

### Research search
Use self-hosted SearXNG.

Requirements:
- JSON Search API enabled;
- multiple general-web engines configured;
- English search queries by default for broad coverage;
- additional local-language query when topic requires it;
- source URL, title, snippet and retrieval timestamp persisted;
- no scraping of search result pages from ad-hoc unofficial endpoints when an API/result endpoint exists.

### Evidence fetch
For top search results:
- request the source page directly;
- follow redirects;
- reject unsupported/binary pages unless explicitly handled;
- extract main readable text;
- cap per-source text;
- hash normalized content;
- deduplicate near-identical URLs/content.

### Script model
Use Gemini Developer API only after the exact model and current free-tier quota are verified in M2.

Current intended text model:

```text
gemini-3.5-flash-lite
```

The model receives the collected evidence, not unrestricted hidden web access.

Every factual narration unit must point to evidence IDs.

---

## 5. Voiceover architecture

Provider:

```text
Google Cloud Text-to-Speech
POST https://texttospeech.googleapis.com/v1/text:synthesize
OAuth2
MP3
```

Locked profile:

```text
google-selected-v1
```

Voices:

| Language | Voice |
|---|---|
| English | `en-US-Chirp3-HD-Algenib` |
| Polish | `pl-PL-Chirp3-HD-Enceladus` |
| Russian | `ru-RU-Wavenet-D` |
| Ukrainian | `uk-UA-Chirp3-HD-Enceladus` |

Rules:
- one continuous narration for the whole video;
- one synthesis after the final script is frozen;
- MP3 stored durably;
- voice name, locale, provider response metadata and audio hash persisted;
- actual audio duration measured from the exact stored file;
- later stages use this exact file;
- no re-TTS;
- no time-stretch or speech-rate correction.

M2 must verify all four voices with the real OAuth credential before production workflow development continues.

---

## 6. Speech alignment

Alignment runs locally from the exact final voiceover.

Flow:

```text
final MP3
→ local decode
→ local speech recognizer/alignment
→ timed words/tokens
→ map exact narration units to timestamps
→ scene/shot timing
```

Requirements:
- multilingual en/pl/ru/uk;
- timestamps originate from actual audio;
- script-to-transcript coverage gate;
- per-scene coverage gate;
- no proportional timing fallback when alignment fails;
- fail closed on insufficient coverage;
- final render uses the same voiceover that was aligned.

The exact aligner implementation is selected and pinned in M2 after a four-language smoke test.

---

## 7. Visual architecture

There is no single visual provider.

The resolver queries all enabled free sources for every shot and ranks the combined candidate pool.

### Production visual adapters

#### Wikimedia Commons
Use for:
- historical material;
- people/events/places with encyclopedic media;
- diagrams;
- public-domain/CC material.

#### Pixabay
Use official API for:
- stock photos;
- stock video;
- generic but concrete real-world visuals.

Current documented default API limit: 100 requests / 60 seconds per API key.

#### Openverse
Use official API for:
- openly licensed images from multiple upstream collections;
- additional candidates not present in Wikimedia/Pixabay.

Only licenses permitted by project policy may pass selection.

#### Unsplash
Adapter may be enabled only after M2 compliance verification.

Reason:
- free demo access exists;
- official API requires hotlinked image URLs;
- download-like use requires calling the supplied download endpoint;
- attribution/API-guideline requirements must be satisfied.

Do not silently treat Unsplash as an unrestricted file CDN.

### License policy

Accept only assets whose use/derivative requirements are compatible with the final video.

Default accepted families:

```text
Public Domain / PDM
CC0
CC BY
CC BY-SA
Pixabay Content License
```

Do not automatically accept:
- CC BY-NC;
- CC BY-ND;
- unknown license;
- missing attribution metadata;
- provider terms incompatible with local rendering.

### Candidate generation

For each shot, the storyboard must contain:
- exact visual intent;
- concrete subject/entities;
- action/mechanism/event if required;
- must-show concepts;
- must-not-show conflicts;
- 2–4 concise English search queries;
- preferred media type: photo / video / diagram / map / document.

Every enabled provider is queried with the same shot intent.

### Candidate normalization

All provider results normalize to one schema:

```text
provider
provider_asset_id
source_url
download_url / media_url
title
description
tags
author
license
license_url
media_type
width
height
duration
query_id
```

### Deterministic ranking

No remote AI decides which image is correct.

Rank candidates using:
- exact entity/title match;
- query token overlap;
- required-concept coverage;
- media-type fit;
- portrait crop viability;
- resolution;
- duplicate/near-duplicate penalty;
- forbidden-context penalty;
- repeated-asset penalty across the video.

If no candidate clears the relevance threshold, fail that shot instead of filling it with generic media.

### Visual density

Do not use one or two images for an entire video by default.

Shot count is derived from:
- narration duration;
- semantic transitions;
- available relevant assets.

A visual can remain longer only when the narration genuinely continues to describe the same visible subject.

---

## 8. Storyboard contract

The script model produces a machine-validated storyboard before TTS.

Each narration unit contains:

```json
{
  "scene_id": "S1",
  "narration": "...",
  "evidence_ids": ["E1", "E2"],
  "shots": [
    {
      "shot_id": "S1-A",
      "visual_intent": "...",
      "must_show": ["..."],
      "must_not_show": ["..."],
      "queries_en": ["...", "..."],
      "preferred_media_type": "photo"
    }
  ]
}
```

The storyboard describes what should be visible; it never names a preselected asset.

Assets are resolved only after the storyboard is frozen.

---

## 9. Render

Render locally.

Final requirements:
- 1080×1920 portrait;
- H.264 video;
- AAC audio;
- MP4;
- exact accepted voiceover;
- no stretched visuals;
- no voice speed manipulation;
- shot boundaries derived from speech timing;
- deterministic crop/fit rules;
- transitions must not conceal irrelevant or missing media.

Still images may use restrained local pan/zoom/crop motion; source geometry must remain valid.

---

## 10. Machine QA

A product job reaches review only when all mandatory checks pass.

Checks:
- file exists and is readable;
- MP4 container valid;
- 1080×1920;
- H.264;
- AAC;
- audio present;
- duration inside agreed tolerance;
- exactly one final TTS synthesis;
- voiceover hash matches aligned/rendered audio source;
- speech global coverage passes;
- every scene coverage passes;
- every planned shot has a selected stored asset;
- visual asset source/license metadata present;
- no duplicate abuse;
- no missing segment;
- no forbidden provider;
- no speech speed modification.

QA failure is terminal for that product job.

---

## 11. Human review

The exact final MP4 must be shown to the user.

Only explicit:

```text
HUMAN PASS
```

accepts the production pipeline.

A rejection creates a systemic defect investigation followed by a fresh job after the fix.

Never manually repair the rejected product job.

---

# Delivery milestones

## M0 — Clean repository
Status: DONE

Acceptance:
- only new files;
- no legacy workflow/database/runtime copied back;
- no secrets.

## M1 — Supporting runtime foundation
Status: DONE — verified 2026-09-18; production n8n architecture corrected 2026-09-19.

Historical bootstrap validation:
- isolated Docker Compose project `shorts-v2` was used to verify the clean supporting runtime;
- a temporary isolated n8n container was verified during bootstrap and then removed on 2026-09-19; production credentials were not retained there;
- PostgreSQL 18 Alpine pinned by digest;
- local media-worker with FFmpeg, pinned Python base image;
- SearXNG pinned by digest;
- persistent PostgreSQL, media and SearXNG storage;
- health checks for supporting services;
- real secrets only in local `.env`, excluded from Git.

Current production architecture:
- n8n orchestration runs only in `publisher.hodor.com.pl`;
- `shorts-v2` is supporting infrastructure only;
- no new n8n domain;
- no parallel production n8n.

Verified:
- supporting services healthy;
- media-worker health + FFmpeg PASS;
- SearXNG JSON search PASS with 30 results;
- PostgreSQL persistence PASS;
- full supporting-service restart preserved PostgreSQL data and media-volume data;
- unrelated projects were not modified.

Acceptance: PASS.

## M2 — Dependency proof before production workflows
Status: PARTIAL — verified no-secret dependencies; credential-gated providers remain pending.

Verified:
1. SearXNG JSON general-web search — PASS.
2. Direct public source-page fetch — PASS.
3. Wikimedia Commons API — PASS.
4. Local 1080×1920 H.264/AAC FFmpeg render — PASS.
5. Local whisper.cpp CPU runtime + multilingual token timestamps — PARTIAL PASS; final quality must be tested on exact Google TTS audio.

Pending credentials / provider proof:
6. Gemini text model through the production n8n at `publisher.hodor.com.pl`.
7. Google Cloud TTS OAuth through the production n8n at `publisher.hodor.com.pl`.
8. All four locked Google TTS voices through the same restored Google OAuth credential after reconnect.
9. Pixabay official API through `publisher.hodor.com.pl` using the restored credential after live validation.
10. Pexels official API through `publisher.hodor.com.pl` using the restored credential after live validation.
11. Unsplash remains optional and disabled until API/compliance proof.

Blocked:
12. Openverse API currently returns a Cloudflare HTTP 403 browser challenge from this VPS; it is disabled unless that changes through an official API-compatible path.

Evidence and exact observations are recorded in `docs/M2_DEPENDENCIES.md`.

Do not build the production pipeline around a dependency that has not passed M2.

## M3 — Intake
```text
POST topic + language + duration → job_id
```

Acceptance:
- strict validation;
- one durable DB row;
- invalid input creates no row;
- no AI/TTS call.

## M4 — Research + evidence
Acceptance:
- broad web search through SearXNG;
- multiple independent sources when available;
- evidence persisted;
- duplicate sources removed;
- no script yet if evidence is inadequate.

## M5 — Script + storyboard
Acceptance:
- continuous narration;
- each factual unit cites evidence IDs;
- each scene contains executable visual intent and search queries;
- no asset is manually selected in script logic.

## M6 — One final voiceover
Acceptance:
- one Google Cloud TTS synthesis;
- correct locked voice;
- MP3 stored;
- real duration measured;
- no later TTS.

## M7 — Local alignment
Acceptance:
- exact final audio aligned locally;
- global and per-scene coverage pass;
- no proportional fallback.

## M8 — Multi-source visuals
Acceptance:
- query every enabled provider;
- normalize candidates;
- deterministic combined ranking;
- license policy enforced;
- irrelevant shots fail closed;
- enough distinct relevant visuals for narration.

## M9 — Render + machine QA
Acceptance:
- fresh normal job;
- 1080×1920 H.264/AAC MP4;
- complete narration and visuals;
- all machine gates PASS.

## M10 — HUMAN PASS
Deliver the exact MP4.

No Studio, TikTok publishing, queue optimization or feature expansion before explicit HUMAN PASS.

---

## Current verified external facts — 2026-09-18

- Gemini 3.5 Flash-Lite currently has a free tier for text input/output.
- Google Cloud Text-to-Speech currently lists up to 1,000,000 free characters for Chirp 3 HD and a larger free allowance for legacy WaveNet; billing/free-tier behavior must still be guarded operationally.
- Pixabay official API documents a default limit of 100 requests per 60 seconds.
- Unsplash demo mode documents 50 requests/hour and specific hotlink/download tracking rules.
- Openverse exposes an official API, supports authenticated/unauthenticated use with throttling, and requires respecting upstream content licenses.
- SearXNG is self-hostable and exposes JSON search endpoints.

These facts must be rechecked before changing providers or quota assumptions.
