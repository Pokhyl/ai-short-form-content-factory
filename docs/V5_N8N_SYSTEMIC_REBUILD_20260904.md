# V5 n8n systemic rebuild — 2026-09-04

This record captures general defects fixed after cross-topic user testing. It is not a one-video patch log.

## Defects and general fixes

### 1. Topic understanding / narration

Failure: deterministic entity matching and extractive narration produced wrong entities and encyclopedia-like text.

Fix: semantic topic interpretation + web research + grounded AI narration in the selected output language. Input-topic language is independent from output language.

### 2. Duration control

Failure: pre-TTS formulas rejected otherwise usable scripts and could not know real speech duration.

Fix: synthesize one continuous natural-rate narration, measure exact audio, rewrite/re-synthesize the script when duration is outside the accepted target window. No speech-speed fitting.

### 3. Free TTS transport timeout

Failure: Edge Read Aloud could exceed the old 30-90 second transport budget.

Fix: bounded 120-240 second provider transport budget; n8n request timeout aligned to 270 seconds. No retry/sleep loop was added.

### 4. Structured model output

Failure: a validator sometimes returned valid semantic content with `used_source_ids: [S2,S3,S4]`, which is invalid JSON.

Fix: a bounded safe normalizer quotes only controlled `S<number>` identifiers inside `used_source_ids`, then standard JSON parsing continues. No eval and no arbitrary JSON repair.

### 5. Cross-provider visual identity

Failure: numeric asset IDs from different media providers were treated as globally unique, e.g. the same numeric candidate ID could resolve to different provider URLs.

Fix: visual identity is now provider-scoped (`provider + provider_asset_id`) before ranking/assignment/download grouping. This matches the durable media-library uniqueness contract.

## Evidence

Autonomous jobs reaching `review_ready` after the rebuild include:

- `1bf8089f-eecf-4b93-83f4-a1a5862a4044` — English topic -> Russian output, 30 s request, 27.360 s measured voiceover;
- `6cf62378-51be-4694-9e4e-5f096a7f1769` — English topic -> Ukrainian output, 30 s request, 31.152 s measured voiceover;
- `656656f1-5f75-4a8e-a5ef-bf8bd1608e16` — Russian topic -> Polish output, 30 s request, 29.160 s measured voiceover.

No manual creative intervention was performed after each job submission.

Acceptance remains `machine_rendered / review_ready`, not HUMAN PASS.

## Regression gate after systemic rebuild

Static workflow regression suite: **10/10 PASS**.

Coverage includes cross-language topic understanding, selected output-language authority, grounded-AI WF02 architecture, exact measured TTS gate, natural-rate duration rewrite loop, bounded Edge provider budget, short canonical titles, provider-scoped visual asset identity, and local media-worker import completeness. Node syntax checks pass for `server.mjs`, `edge-provider-budget.mjs`, and `media-range.mjs`.

The latest Polish volcano job `656656f1-5f75-4a8e-a5ef-bf8bd1608e16` passed the full n8n chain to `review_ready` after the provider-identity fix. This remains machine evidence only until exact-artifact HUMAN PASS.
