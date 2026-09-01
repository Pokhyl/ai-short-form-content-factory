# Current Project State — Rebuild

Last updated: 2026-09-01

This file is the authoritative source of truth for active branch `rebuild/simple-pipeline`. If chat memory, old branches, old workflow exports, or older docs conflict with this file, this file wins.

## Mandatory protocol

Before EVERY technical response, diagnosis, recommendation, code/config change, deployment, or test for this project:

1. Read `docs/PERMANENT_PROJECT_RULES.md` from GitHub.
2. Read this file from GitHub branch `rebuild/simple-pipeline`.
3. Architecture change: also read `docs/ARCHITECTURE.md`.
4. Milestone/acceptance/gate change: also read `docs/ROADMAP.md` and `docs/PROCESS_GATE.md`.
5. Upstream/provider change: also read `docs/UPSTREAM_DECISION.md`.

Repository state overrides chat memory. Unknown state must not be guessed.

## Product

Self-hosted AI Short-Form Content Factory:

`topic -> factual narration + visual plan -> continuous natural voice -> truthful/relevant visuals -> render -> human review`

Publishing is outside the automatic generation chain.

## Runtime invariants

Exactly three persistent project services:

- `ai-short-form-content-factory-n8n-1`
- `ai-short-form-content-factory-postgres-1`
- `ai-short-form-content-factory-media-worker-1`

Per-video external API cost must remain `0 PLN`.

Measured VPS capacity on 2026-09-01:

- 2 vCPU
- 3.7 GiB RAM
- 2.0 GiB swap
- no GPU
- root filesystem 38 GiB, about 2.7 GiB free at measurement time

Do not add a fourth persistent service unless a separately measured blocker proves it necessary and the architecture decision is documented first.

## Voice — current production

WF03 is Edge-only continuous voice. Fixed voices:

- EN `en-US-AndrewNeural`
- PL `pl-PL-MarekNeural`
- RU `ru-RU-DmitryNeural`
- UK `uk-UA-OstapNeural`

Provider rate/pitch/volume remain default. No `atempo`, rate correction, pause rewrite, or silence-removal filter is allowed.

The destructive `silenceremove` stage was removed in implementation commit `146abeb`. Media-worker preserves provider timing and only normalizes format to 48 kHz stereo PCM WAV.

WF02 was recalibrated against untouched/default-rate Edge timing in implementation commit `097cdb7`. Current production WF02 active/published version is `857ac0dd-f1e7-4a55-825c-ba21dc70ad9d`, exact published core SHA-256 `030cf6b5ec6f9e75bcef8c5714ed618831c02f6aa899a38db39aafd76af2b0a3`.

EN15 planning currently targets about 196 non-space characters / 33 words; equivalent per-language clean-Edge calibration exists for PL/RU/UK. The measured WF03 duration gate remains authoritative.

## Visuals — current production

WF04 preserves canonical reference provenance plus structured `reference_media_kind = diagram | animation | photo` for technical-reference beats. The repair implementation is commit `7a302ce`.

Current production WF04 active/published version is `772c8790-0538-4e28-9892-7f3c94ff6e66`, exact core SHA-256 `a4bbfb6affc3d64433f01aa3be92a97b46c9a643d3eb0b88883f7e8053cc0d85`.

Stock/exact semantics, renderer and review remain unchanged by the current provider work.

## Permanent provider rule — active blocker

Production MUST NOT depend on request-count/rate/quota-limited hosted AI Free Tier as a required generation dependency.

Latest production evidence after clean-Edge deployment:

- primary `gemini-3.6-flash` returned `429 RESOURCE_EXHAUSTED` for Free Tier metric `generativelanguage.googleapis.com/generate_content_free_tier_requests`, limit `20`, with explicit retry-after;
- fallback `gemini-3.5-flash` simultaneously returned `503 UNAVAILABLE / high demand`;
- prior fresh attempts also produced repeated `503` from both models.

Therefore Gemini Free Tier is not an acceptable critical-path dependency. Do not wait for quota reset and do not repair this with sleeps, retry loops, model hopping, extra keys/accounts/projects, paid fallback, or weakened acceptance.

## Current systemic objective

Remove Gemini / any hosted quota-limited semantic AI from the REQUIRED production generation path while preserving:

- 0 PLN per-video API cost;
- truthful factual narration grounded in retrieved evidence;
- output languages EN/PL/RU/UK;
- natural Edge voice with no speed/pause manipulation;
- current duration and visual truth gates;
- exactly three persistent services.

A local semantic engine may run inside the existing `media-worker`; that does not add a fourth service. Any local model must fit measured VPS CPU/RAM/disk constraints and must not become a silent quality downgrade. Candidate/model selection must be proven on materially different topics and all four languages before production deployment.

## Acceptance matrix

Frozen CASE 1 remains:

`How does a zipper work?` / `en` / `15`

No later matrix case may be accepted before CASE 1 passes on one unchanged runtime:

- factual/coherent narration;
- natural clean Edge measured duration;
- every selected visual/provenance/content check;
- final ffprobe;
- human-visible voice/render quality.

First real product failure stops progression and is repaired systemically, never with a topic-specific patch.

## Immediate next action

Design and prove a local, zero-API-cost semantic replacement for Gemini inside the existing three-service architecture. Start with read-only capability/resource/model probes; do not mutate production until the model/approach passes cross-topic/cross-language structured-output and factual-grounding tests against the existing WF02 contract. Then document architecture decision, implement behind the same durable WF02 boundary, run full local regression, deploy boundedly, and restart CASE 1 from a completely fresh job.