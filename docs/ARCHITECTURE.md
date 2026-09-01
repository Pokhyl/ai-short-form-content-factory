# Architecture — Clean Rebuild

Last updated: 2026-09-01

`docs/CURRENT_STATE.md` is the operational source of truth. This file defines current architectural boundaries.

## Product

`Topic -> factual narration + compact visual plan -> one continuous natural voice -> truthful/relevant real visuals -> render -> human review`

Publishing remains outside the automatic generation chain.

## Persistent runtime

Exactly three services:

1. `n8n`
2. `postgres`
3. `media-worker`

No fourth persistent service without a separately proven blocker and documented decision.

### n8n

Owns orchestration, external factual retrieval, PostgreSQL state transitions, stage hand-offs, and compact requests to media-worker.

### PostgreSQL

Owns durable application state in `public`. The `n8n` schema belongs to n8n and is never modified manually.

### media-worker

Owns local/media operations: Edge synthesis storage/format normalization, local visual ranking primitives, image/video persistence, FFmpeg/ffprobe, rendering, and—if accepted by the current local-semantic gate—the local semantic inference runtime. It never writes product state directly to PostgreSQL.

Running a local semantic model inside the existing media-worker does not add a fourth service.

## Cost / provider boundary

Per-video external API cost must remain `0 PLN`.

A request-count/rate/quota-limited hosted AI Free Tier may not be a REQUIRED production dependency. Gemini Free Tier is specifically disallowed from the required critical path after repeated `429 RESOURCE_EXHAUSTED` and `503 UNAVAILABLE` production evidence.

Forbidden quota workarounds: sleeps, retry loops, quota-window waits, model hopping, extra keys/accounts/projects, paid fallback, or weaker acceptance.

Factual web/source retrieval that is public and zero-cost may remain external, but semantic generation must not require a quota-limited hosted AI service.

## WF02 — factual narration + visual plan

WF02 receives only `job_id`, reloads durable context, retrieves bounded factual evidence, then produces one coherent job-level narration plus compact per-beat visual intent.

Current narration invariants:

- output language: EN/PL/RU/UK;
- factual claims must be supported by retrieved evidence;
- one continuous narration, not scene-by-scene prose fragments;
- exact natural sentence count `3/5/7/9` for requested `15/30/45/60` seconds;
- target size is calibrated to untouched Edge timing;
- deterministic validation fails closed before TTS when output violates the contract.

Current visual intent includes stock/reference/exact modes, canonical `reference_query`, and `reference_media_kind = diagram | animation | photo` for reference beats.

The semantic engine behind WF02 is an implementation detail as long as it is local/non-quota-limited, produces the same validated contract, is grounded in supplied evidence, and passes cross-topic/cross-language quality acceptance.

## WF03 — continuous natural voice

Edge-only, one job-level synthesis:

- EN `en-US-AndrewNeural`
- PL `pl-PL-MarekNeural`
- RU `ru-RU-DmitryNeural`
- UK `uk-UA-OstapNeural`

Rate/pitch/volume are provider defaults. No `atempo`, time-stretch, rate correction, pause rewriting, silence removal, padding, or scene-by-scene TTS.

Media-worker may only normalize provider output to canonical 48 kHz stereo PCM WAV. Measured continuous duration is authoritative and must satisfy the current target-relative quality gate.

## WF04 — visual sourcing

Uses real source candidates and deterministic eligibility boundaries before relative ranking.

Technical reference truth has two orthogonal axes:

- `reference_query`: which canonical concept/article;
- `reference_media_kind`: which representation form (`diagram`, `animation`, `photo`).

Reference candidates must match canonical reference provenance and requested media form before ranking. Empty eligible lanes fail closed. Stock/exact subject truth remains separate. No topic-specific mappings, manual assets, semantic threshold hacks, or acceptance bypasses.

## WF05 — render

One continuous audio track + persisted visual beat timeline -> 1080x1920 H.264/yuv420p 30fps + AAC 48 kHz stereo. Subtitles are burned from persisted narration. ffprobe validates final output before `review_ready`.

## WF06 — human review

Human review is a separate boundary. Generation stops at `review_ready`; publishing is not automatic.

## Local semantic replacement gate

The quota-removal architecture is accepted only if a local semantic approach:

1. fits current VPS constraints (2 vCPU, 3.7 GiB RAM, 2 GiB swap, no GPU, constrained disk);
2. runs inside the existing media-worker or otherwise preserves exactly three persistent services;
3. generates strict structured WF02 output without hosted semantic AI;
4. is fact-grounded only in supplied evidence;
5. works across EN/PL/RU/UK and materially different science/history/product topics;
6. does not weaken duration/visual/review acceptance;
7. passes local regressions and fresh production CASE 1 on one unchanged runtime.

If a candidate local model cannot meet these conditions, reject it rather than hiding the failure with a topic-specific rule or fallback to Gemini.