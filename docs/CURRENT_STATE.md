# Current Project State — Product-First V4

Last updated: 2026-09-04

This file is authoritative for branch `rebuild/product-first-v4`. Repository/runtime state overrides chat memory.

## Production status

Semantic-v3 remains rejected and frozen. Do not create new production jobs through it.

No V4 artifact is human-approved yet. No production/n8n rebuild is allowed. M8 remains `2/10`.

## Mandatory source of truth

Before technical work read fresh:

1. `docs/PERMANENT_PROJECT_RULES.md`;
2. this file;
3. `docs/PRODUCT_FIRST_V4.md`;
4. `docs/ENGINEERING_HISTORY_V4.md`;
5. `docs/V4_MULTISHOT_HUMAN_FAIL_20260903.md`;
6. `docs/V4_CROSS_TOPIC_MATRIX.md`;
7. `docs/V4_CROSS_TOPIC_AUDIT_20260903.md`;
8. `docs/V4_CROSS_TOPIC_CONTRACT_IMPLEMENTATION_20260903.md`;
9. `docs/V4_ACTUAL_AUDIO_CROSS_TOPIC_PROOF_20260903.md`;
10. `docs/V4_EXACT_MEDIA_RESOLUTION_PROOF_20260903.md`;
11. `docs/V4_OLED_PREDELIVERY_REJECTION_20260904.md`;
12. relevant upstream/reference docs.

## Current architecture direction

`topic -> factual research -> semantic director -> speech-ready script + semantic visual obligations -> TTS -> exact-audio Whisper timing -> provenance-bound timeline compiler -> exact-media resolver / pictorial-or-annotated visual compiler -> render manifest -> verified render bundle -> vertical renderer -> complete-video human review`

Critical rules:

- TTS receives speech-ready text only;
- captions/timing come from the exact generated audio;
- no generic factual fallback stock;
- text normally overlays meaningful visuals; it does not replace the primary visual;
- portrait orientation does not prove relevance;
- widescreen exact evidence uses contain/PIP/collage/diagram treatment;
- factual/mechanism beats show the actual subject/mechanism or a truthful pictorial representation;
- generic boxes/labels/arrows are annotation primitives, not a valid primary factual visual;
- pacing follows semantic/visual information, not arbitrary cut-count targets;
- exact-media identity/license/hash/dimensions are resolved before rendering;
- a renderer may not independently replace resolved exact media;
- machine render is never human approval;
- general changes are exercised across materially different topics/languages;
- every meaningful failure/root cause/decision is recorded in GitHub.

## Human-failed artifacts retained as evidence

1. Custom compositor prototype — HUMAN FAIL: stretched imagery, giant subtitle blocks, unreadable diagrams.
2. OpenMontage proof #1 — HUMAN FAIL: narrated slideshow / one asset per long scene.
3. OpenMontage proof #2 — HUMAN FAIL: high cut frequency but text-only replacement frames and generic adjacent stock.

Do not patch/retry these artifacts as fixtures.

## Cross-topic matrix — active

1. Induction / Ukrainian — regression only; do not tune next on this topic.
2. Eiffel Tower construction / Polish — exact place/history.
3. Clothing zipper mechanism / Russian — object/mechanism.
4. OLED vs LCD / English — comparison/mechanism.

## Structural timeline contract — TECHNICAL PASS

Code:

- `prototype/v4/timeline_contract.py`;
- `prototype/v4/tests/test_timeline_contract.py`.

It rejects text-only primary visuals, generic factual fallback, invalid fullscreen landscape media, unjustified contextual media and timeline gaps/overlaps.

Remote commits: `8aa5365c384a73d603a2cf072b65e51f1f5f66fb`, `47089b7e626afd5bdfcdab23dcc46bc0f0403ed0`.

## Actual-audio cross-topic automation — TECHNICAL PASS

V4-only tooling environment: `/opt/ai-short-form-v4-tools` with `edge-tts 7.2.7`, `faster-whisper`, `requests`. Production containers unchanged.

Fresh real-audio fixtures:

- Eiffel / PL: `27.34 s`, 5 Whisper segments, language probability `1.0`;
- Zipper / RU: `27.14 s`, 8 Whisper segments, language probability `1.0`;
- OLED/LCD / EN: `32.34 s`, 6 Whisper segments, language probability `1.0`.

The English speech guard rejected raw `OLED/LCD` abbreviations; narration uses full spoken names. No bypass was added.

General stale-artifact fix:

- `prototype/v4/timeline_builder.py`;
- timeline timing derives from current exact-audio Whisper segment starts;
- timeline embeds current script/audio SHA256 provenance;
- CLI `compile-timeline` and `validate-timeline`.

Proof: `docs/V4_ACTUAL_AUDIO_CROSS_TOPIC_PROOF_20260903.md`.

## Exact-media acquisition/resolution — TECHNICAL PASS

Automation:

- `prototype/v4/commons_media.py` — Commons acquisition with license/source/dimensions/hash metadata;
- `prototype/v4/asset_resolver.py` — beat-level identity + SHA + dimensions/layout validation;
- CLI `fetch-commons` and `resolve-assets`.

Resolved state before visual-adequacy guard:

- Eiffel: `2 exact + 3 constructed`;
- Zipper: `1 exact + 7 constructed`;
- OLED/LCD: `0 exact + 6 constructed`;
- all exact assets hash-verified;
- no generic fallback injected.

Proof: `docs/V4_EXACT_MEDIA_RESOLUTION_PROOF_20260903.md`.

## Unified render manifest / bundle / renderer — TECHNICAL PLUMBING PASS

Implemented:

- `prototype/v4/render_manifest.py`;
- `prototype/v4/render_bundle.py`;
- `prototype/v4/remotion/VerticalShort.tsx`;
- CLI `build-render-manifest` and `stage-render-bundle`.

The bundle stage copies only hash-verified audio/assets into a separate `public/` directory and rewrites renderer props to relative staged paths. The source tree remains free of runtime media.

A real OLED/LCD artifact was rendered through this plumbing:

- duration `32.427 s`;
- H.264 `1080x1920` + AAC;
- SHA256 `e779cac7db4fc38353a0b5ad8b0f1aa463cd6e766e76c1fc62461257ea451b61`.

This proves renderer plumbing only; it is not a quality pass.

## OLED pre-delivery rejection — PRODUCT FAIL BEFORE USER REVIEW

The OLED artifact was rejected before being promoted as a review candidate.

Manifest audit showed all six primary beats were `motion_graphic` and each was dominated by generic `rect + text + line` elements with 4-5 text labels. The old semantic compiler contract only represented label boxes and relations, so the output could not become a rich factual visual.

Root cause: `graphic_spec.py` / `graphic_compiler.py` v1 are structurally capable of presentation diagrams, not adequate primary factual visuals.

Proof: `docs/V4_OLED_PREDELIVERY_REJECTION_20260904.md`.

## Primary visual adequacy guard — TECHNICAL PASS

New code:

- `prototype/v4/visual_adequacy.py`;
- `prototype/v4/tests/test_visual_adequacy.py`;
- integrated into `prototype/v4/render_manifest.py`.

Primary motion graphics now require an explicit `visual_basis` from:

- `exact_media_annotation`;
- `pictorial_primitive`;
- `data_chart`;
- `map`;
- `screen_capture`.

Generic boxes/labels/arrows without one of those bases fail before render-manifest generation.

Cross-topic result with the new guard:

- Eiffel rejects at `E2`;
- zipper rejects at `Z2`;
- OLED/LCD rejects at `O1`.

This is intentional. Do not weaken the guard to make the old fixtures pass.

Current focused V4 suite: `42/42 PASS`.

## Existing low-level motion primitive

`prototype/v4/remotion/MotionDiagram.tsx` supports basic shapes, lines/arrows and animation. It remains acceptable as an annotation/rendering backend, but generic box/label output is no longer sufficient as a primary factual visual.

## Immediate next action

Do not render Eiffel/zipper with the rejected primary-box graphic path and do not return to induction.

1. add a reusable annotated-media path: `hash-verified exact media/diagram -> crop/contain/zoom -> semantic motion overlays -> captions`;
2. add Commons search/discovery so factual beats can acquire exact diagrams/images instead of defaulting to constructed cards;
3. preserve graphic overlays as secondary explanation, not primary substitution;
4. exercise the same annotated-media path across Eiffel, zipper and OLED/LCD;
5. require complete-video human review for each materially different prototype;
6. only after multiple HUMAN PASS artifacts consider n8n/DB orchestration.

No n8n/DB rebuild until multiple materially different direct prototypes are HUMAN PASS.
