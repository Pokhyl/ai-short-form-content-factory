# Current Project State — Product-First V4

Last updated: 2026-09-03

This file is authoritative for branch `rebuild/product-first-v4`. Repository/runtime state overrides chat memory.

## Why this branch exists

Semantic-v3 is rejected as a product architecture.

Fresh production job `61f662ee-565c-4dd6-8759-17a51f3e7ec3` reached machine `review_ready` but received explicit HUMAN FAIL. The exact video had unnatural Ukrainian narration/pronunciation and visually irrelevant footage including fried eggs, bacon and campfire material for an induction-cooking explainer.

That result proves the previous machine gates could certify a technically valid but bad video. M8 remains `2/10`. The consumed job must never be retried/reused.

## Production freeze

Do not create any more production jobs through semantic-v3.

The currently deployed VPS stack remains untouched only as rollback/reference. Do not spend more Edge calls proving the rejected architecture.

## Source of truth

Before technical work on V4 read fresh:

1. `docs/PERMANENT_PROJECT_RULES.md`;
2. this file;
3. `docs/PRODUCT_FIRST_V4.md`;
4. `docs/ENGINEERING_HISTORY.md` for prior failures;
5. relevant upstream/reference project docs when adapting an existing pattern.

## V4 direction

The redesign is based on recurring patterns from mature open-source short-video projects including MoneyPrinterTurbo, ShortGPT, AI Shorts Generator, Short Video Maker, OpenNolan, VML and Remotion-based faceless-video systems.

New critical path:

`topic -> factual research -> semantic director -> speech-ready script + scene storyboard -> TTS -> Whisper timing from actual audio -> scene-specific visual production -> preview QA -> Remotion/FFmpeg render -> human review`

Key product rules:

- source text is evidence, not final narration;
- one semantic director artifact owns the spoken script and scene visual intents;
- TTS receives normalized speech-ready text, never raw encyclopedic prose;
- captions/timing come from the generated audio via Whisper, not synthetic fixed beat counts;
- stock footage is only one visual mode;
- factual/mechanism scenes can route to exact media, diagrams/motion graphics, cards or other truthful representations instead of generic stock;
- no generic/joker visual fallback for factual scenes;
- SigLIP/CLIP may rerank candidates but cannot replace semantic planning/relevance;
- final asset relevance is more important than perceptual diversity metrics;
- `machine_rendered` is not `human_approved`.

Full contract: `docs/PRODUCT_FIRST_V4.md`.

## Cost boundary

Do not convert the project into a mandatory paid-per-video pipeline.

The semantic director is provider-pluggable. Preferred zero-variable-cost path is a capable local model on hardware that can actually run it. Do not force a weak general model onto the current 2 vCPU / 3.7 GiB VPS merely to preserve an old architecture rule.

## Immediate build sequence

1. Build V4 as a direct CLI prototype outside n8n and PostgreSQL orchestration.
2. Implement a single structured director artifact (`spoken_script` + `scenes[]`).
3. Add general multilingual speech text normalization.
4. Produce one continuous voice track and derive real word timings from that audio.
5. Implement visual-mode routing (`exact_media`, `stock`, `diagram`, `screen/text/card`, optional generated image).
6. Render one complete 9:16 prototype with Remotion/FFmpeg.
7. Human-review that direct prototype before integrating n8n/DB.
8. Repeat across materially different topics/languages before any production deployment.

## Forbidden next moves

- no semantic-v3 production retries;
- no `кГц`-specific pronunciation patch;
- no eggs/bacon/induction-specific blacklist;
- no threshold tweaking to make the old visual gate look better;
- no new elaborate deterministic semantic heuristics;
- no orchestration/database work before a direct V4 video is HUMAN PASS.

Current boundary: V4 research/design branch exists, production semantic-v3 is frozen, and the next work is the direct product prototype—not another n8n workflow patch.