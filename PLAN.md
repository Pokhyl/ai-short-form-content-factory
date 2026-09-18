# AI Short-Form Content Factory — Production Plan

## Goal

Build the project again from a clean repository.

Input:

```text
topic + language + duration
```

Output:

```text
one finished 9:16 MP4
```

Target pipeline:

```text
topic
→ research
→ script / storyboard
→ one continuous voiceover
→ speech timing
→ relevant visuals
→ local render
→ machine QA
→ human review
→ only then Studio / publishing
```

The previous implementation is not a baseline and must not be restored.

---

## Non-negotiable product constraints

- n8n is mandatory and is the orchestrator.
- PostgreSQL is the source of truth for production state.
- Inputs are only:
  - `topic`
  - `language`
  - `duration`
- Supported languages:
  - `en`
  - `pl`
  - `ru`
  - `uk`
- Supported target durations:
  - `15`
  - `30`
  - `45`
  - `60` seconds.
- Production must remain free-only.
- No paid fallback.
- Do not use:
  - OpenAI
  - Anthropic
  - OpenRouter
  - Groq
  - ElevenLabs
  - FAL
- Gemini may be used only for functions that have been verified to be available under the approved free tier.
- No Ollama/local LLM/model-worker.
- No external transcription API.
- No external AI visual-verification API.
- Rendering and speech alignment run locally.
- Never speed up, slow down, or trim narration to force duration.
- Never synthesize narration a second time during render.
- Failed/rejected production jobs are immutable. A new test means a new job.
- Credentials and secrets must never be committed to Git.

---

## Voiceover

Voiceover is one continuous narration for the whole video.

Provider:

```text
Google Cloud Text-to-Speech
POST https://texttospeech.googleapis.com/v1/text:synthesize
OAuth2
MP3
```

Locked voice profile: `google-selected-v1`

| Language | Voice |
|---|---|
| English | `en-US-Chirp3-HD-Algenib` |
| Polish | `pl-PL-Chirp3-HD-Enceladus` |
| Russian | `ru-RU-Wavenet-D` |
| Ukrainian | `uk-UA-Chirp3-HD-Enceladus` |

Rules:

- exactly one final TTS synthesis per job;
- narration is synthesized only after the final script is accepted by validation;
- use the real audio duration returned by the final voiceover;
- all visual timing is derived from that exact audio;
- no speech-rate manipulation.

Do not replace these voices merely to simplify implementation.

---

## Visuals

Visuals must match the actual narration, not merely the general topic.

Initial source:

```text
Wikimedia Commons
```

Only free sources may be added later and only after their terms, API limits, and production usefulness are verified.

Rules:

- research/script decides what must be shown;
- resolver chooses assets only after the visual intent is known;
- no manually selected topic-specific assets in production logic;
- no topic-specific hacks;
- every visual must have source/license metadata;
- avoid one or two generic images stretched across the whole video;
- use enough visual changes to follow the narration naturally;
- a visual must support the exact scene/shot meaning;
- reject obviously irrelevant results instead of filling the timeline with them.

The planner chooses visual intent, not a hard-coded asset.

---

## Timing and alignment

Timing is created from the exact final voiceover.

Pipeline:

```text
final voiceover
→ local decode when required
→ local speech alignment
→ timed words/tokens
→ map narration units to speech timestamps
→ visual shot boundaries
```

Requirements:

- local transcription/alignment only;
- no proportional timing fallback when reliable speech timestamps are unavailable;
- fail closed if narration coverage is insufficient;
- render the same narration that was aligned;
- no second TTS call.

---

## Render

Rendering is local using FFmpeg/Remotion-compatible local tooling.

Final media requirements:

- portrait `1080×1920`;
- H.264 video;
- AAC audio;
- continuous narration;
- valid MP4;
- no stretched/distorted source media;
- visuals aligned to narration;
- target duration handled by visual pacing, not voice manipulation.

---

## Machine QA

A job may reach review only after automated checks pass.

Minimum checks:

- output file exists;
- MP4 container valid;
- `1080×1920`;
- H.264 video;
- AAC audio;
- audio present;
- duration within the agreed tolerance;
- every planned visual exists;
- no missing render segment;
- speech alignment coverage passes;
- no narration speed manipulation;
- exactly one TTS synthesis;
- visual/source metadata preserved.

Machine PASS is not final PASS.

---

## Human review

The exact produced MP4 must be reviewed by the user.

Only explicit:

```text
HUMAN PASS
```

means the production pipeline is accepted.

If the user rejects the video, diagnose the systemic cause and create a new job after the fix.

Do not manually repair the failed/rejected production job.

---

# Delivery milestones

## M0 — Empty clean repository

Acceptance:

- repository contains only the new project;
- no old workflows;
- no old DB dump;
- no recovery code;
- no legacy runtime copied into the project;
- no secrets.

Status: current starting point.

---

## M1 — Minimal isolated runtime

Create only what the first E2E requires:

- Docker Compose;
- n8n;
- PostgreSQL;
- media worker;
- persistent media storage;
- health checks.

Do not build a large workflow catalog in advance.

Acceptance:

- runtime starts cleanly;
- isolated from unrelated projects;
- restart preserves production state;
- no dependency on old project containers.

---

## M2 — Verify dependencies before architecture

Before integrating a provider or library, verify it in isolation.

Verify:

1. text/research model actually works under the approved free tier;
2. Google Cloud TTS OAuth works;
3. all four locked voices synthesize correctly;
4. Wikimedia retrieval works;
5. local alignment works for `en/pl/ru/uk`;
6. local rendering works.

No production workflow should be built around an unverified provider.

Acceptance:

- one small proof for every external dependency;
- real returned data/audio inspected;
- limits documented.

---

## M3 — Job intake

Implement one n8n entrypoint:

```text
topic + language + duration → job_id
```

Validation:

- topic non-empty;
- language in `en/pl/ru/uk`;
- duration in `15/30/45/60`.

Acceptance:

- exactly one durable DB row;
- invalid request creates no job;
- intake itself calls no AI/TTS provider.

---

## M4 — Research and script

Generate a grounded short-form story.

The result must contain:

- final narration text;
- narration units/scenes;
- visual intent for each unit;
- English search queries for asset discovery;
- evidence/source references where factual claims require them.

Narration and visual description use the video language.

Search query remains concise English suitable for media discovery.

Acceptance:

- coherent continuous narration;
- no unsupported factual claims;
- no generic visual plan when the narration requires a specific object/event/mechanism;
- script is ready before TTS is called.

---

## M5 — One continuous final voiceover

Use the locked Google Cloud TTS voice for the selected language.

Acceptance:

- one synthesis;
- MP3 stored durably;
- actual audio duration measured;
- voice/language recorded in DB;
- no re-TTS in later stages.

---

## M6 — Local speech alignment

Align the exact final voiceover locally.

Acceptance:

- timestamps come from actual speech;
- narration-unit coverage passes;
- no external transcription API;
- no proportional fallback hiding alignment failure.

---

## M7 — Visual discovery and selection

For every narration unit/shot:

1. derive the exact visual intent;
2. query Wikimedia;
3. collect multiple candidates where possible;
4. score relevance deterministically;
5. reject conflicts/irrelevant candidates;
6. persist source/license metadata.

Acceptance:

- visuals visibly correspond to narration;
- sufficient visual variety;
- no manual per-topic choices;
- no generic “same subject” substitution when the narration requires something specific.

---

## M8 — Local render

Render one complete MP4 from the accepted voiceover, aligned timings, and selected visuals.

Acceptance:

- `1080×1920`;
- H.264/AAC;
- continuous narration;
- correct timing;
- no voice speed changes;
- no missing visual segment.

---

## M9 — Full fresh E2E

Create a completely new normal job through the real intake.

Do not use diagnostic fixtures as final proof.

Required path:

```text
intake
→ research
→ script
→ one TTS
→ local alignment
→ visuals
→ render
→ machine QA
```

Acceptance:

- fresh production job reaches machine QA PASS;
- exact MP4 is delivered for human review.

---

## M10 — Human PASS

Stop feature expansion until the real MP4 receives explicit HUMAN PASS.

After HUMAN PASS only:

- Studio UI;
- draft publishing;
- TikTok integration;
- additional free visual providers;
- throughput/queue optimisation.

---

# Engineering rules

1. Inspect before changing.
2. Never replace a working component unless it is the proven cause of a defect.
3. Keep a working baseline before every meaningful change.
4. Change one subsystem at a time.
5. After every change, test the complete affected path.
6. Do not invent new architecture to solve a local defect.
7. No hacks or topic-specific exceptions.
8. No silent fallback to another provider/model.
9. Do not weaken QA to make a test pass.
10. Do not claim completion from unit tests alone.
11. A machine PASS is provisional until the exact MP4 receives HUMAN PASS.
12. Never touch unrelated projects, databases, credentials, containers, domains, repositories, or workflows.
13. If an approach fails twice for the same reason, stop repeating it and re-evaluate the root cause.
14. Preserve proven working choices such as selected voices unless evidence shows they are the defect.

---

# Repository policy

The repository starts clean.

Initial implementation should remain deliberately small:

```text
PLAN.md
compose.yaml
config/
db/
n8n/
services/media-worker/
tests/
docs/
```

Add a component only when its milestone requires it.

Do not restore deleted legacy project files merely because they existed before.
