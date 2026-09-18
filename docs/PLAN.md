# Production Plan — Clean Rebuild

Last updated: 2026-09-18

This file is the execution source of truth for the clean rebuild.

Before every meaningful change:
1. read this file;
2. read `config/free-only-policy.json`;
3. verify the change stays inside this repository and the isolated `shorts-v2` runtime;
4. do not touch other projects.

## Non-negotiable constraints

- n8n is the orchestrator.
- Production must be free-only.
- No paid API, paid fallback, hidden billing dependency, or provider added without verified Free Tier evidence.
- Allowed external AI:
  - Gemini text: `gemini-3.5-flash-lite`
  - Gemini TTS: `gemini-3.1-flash-tts-preview`
- Exactly one successful final TTS synthesis per job.
- No external transcription API.
- No external visual-verification API.
- Speech timing/alignment is local.
- Visual verification is local/deterministic.
- Rendering is local.
- Visual sourcing starts with Wikimedia Commons.
- Inputs are only: topic, language, duration.
- Languages: en / pl / ru / uk.
- Durations: 15 / 30 / 45 / 60 seconds.
- Output: one 9:16 MP4.
- No Studio/UI/publishing work until one real end-to-end MP4 passes human review.
- Do not repair or resume failed product jobs; create a new job.
- Never modify unrelated n8n instances, databases, containers, repositories, credentials, domains, or files.

## Delivery order

### M0 — Clean reset
Status: DONE

- Old project runtime removed.
- GitHub repository reset.
- Free-only policy committed.

### M1 — Isolated runtime
Status: DONE

- Dedicated `shorts-v2` Docker project.
- Dedicated n8n.
- Dedicated PostgreSQL.
- Dedicated volumes.
- Minimal `jobs` table.

### M2 — Gemini access
Status: NEXT

Goal: connect Gemini to the isolated n8n without reusing or exposing secrets from other projects.

Acceptance:
- text model call succeeds;
- TTS model call succeeds;
- no other AI provider exists in production path.

### M3 — Intake
Status: TODO

Implement one webhook:
`topic + language + duration -> job_id`

Acceptance:
- strict validation;
- one DB row;
- no AI call during intake.

### M4 — Script
Status: TODO

Generate the complete narration/script with Gemini text.

Acceptance:
- correct language;
- structured scene plan;
- no TTS yet;
- one production text path only.

### M5 — Final voice
Status: TODO

Generate one continuous narration with Gemini TTS.

Acceptance:
- exactly one successful final synthesis for the job;
- no second TTS during render;
- no speech speed-up or time-stretch.

### M6 — Local timing
Status: TODO

Derive speech timing locally from the exact final audio.

Acceptance:
- zero external transcription calls;
- timestamps belong to the exact audio that will be rendered.

### M7 — Visual sourcing
Status: TODO

Resolve visuals from Wikimedia Commons using scene semantics.

Acceptance:
- multiple relevant visuals where needed;
- license/source metadata retained;
- no paid media provider;
- no remote AI visual verification.

### M8 — Render
Status: TODO

Render locally to vertical MP4.

Acceptance:
- 1080x1920;
- continuous narration;
- visuals aligned to narration;
- target duration handled without changing speech speed;
- valid H.264/AAC MP4.

### M9 — Machine QA + human review
Status: TODO

Machine checks:
- dimensions;
- codec/container;
- duration;
- audio present;
- no missing visual assets.

Then inspect the exact MP4.

Success is only:
- machine QA PASS;
- human review PASS.

### M10 — Only after M9 PASS
Status: BLOCKED

Only then consider:
- Studio/UI;
- draft publishing;
- additional visual sources;
- performance/queue improvements.

## Change rule

If a change would introduce a new provider, external AI purpose, paid feature, retry architecture, or additional service:
- stop implementation;
- verify the real need first;
- verify official license/free-tier terms;
- update `config/free-only-policy.json` and this plan before deployment.

Do not redesign the architecture because of one failed job. Fix the proven defect and rerun a new job.
