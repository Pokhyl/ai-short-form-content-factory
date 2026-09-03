# Current Project State — Product-First V4

Last updated: 2026-09-03

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
11. relevant upstream/reference docs.

## Current architecture direction

`topic -> factual research -> semantic director -> speech-ready script + semantic visual obligations -> TTS -> exact-audio Whisper timing -> provenance-bound timeline compiler -> exact-media resolver / constructed-graphic compiler -> vertical renderer -> complete-video human review`

Critical rules:

- TTS receives speech-ready text only;
- captions/timing come from the exact generated audio;
- no generic factual fallback stock;
- text normally overlays meaningful visuals; it does not replace the primary visual;
- portrait orientation does not prove relevance;
- widescreen exact evidence uses contain/PIP/collage/diagram treatment;
- factual/mechanism beats show the actual subject/mechanism or a truthful constructed representation;
- pacing follows semantic/visual information, not arbitrary cut-count targets;
- exact-media identity/license/hash/dimensions are resolved before rendering;
- a renderer may not independently replace resolved exact media;
- constructed diagrams must be generated from a reusable semantic graphic grammar, not topic-specific raw SVG coordinate dumps;
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
- CLI `compile-timeline` and `validate-timeline`;
- focused suite at that stage: `15/15 PASS`.

Remote commits: `9c6216638639ad9b2a196cc96df978a2a382b053`, `af4cde4c147bc4271e46d78d588dce4ae42fa86f`, `d9b0e342926160b152ad40336865c3a7c23fd4f3`.

Proof: `docs/V4_ACTUAL_AUDIO_CROSS_TOPIC_PROOF_20260903.md`.

## Exact-media acquisition/resolution — TECHNICAL PASS

New automation:

- `prototype/v4/commons_media.py` — Commons API acquisition with license/source/dimensions/hash metadata;
- `prototype/v4/asset_resolver.py` — beat-level identity + SHA + dimensions/layout validation;
- CLI `fetch-commons` and `resolve-assets`.

Real assets resolved automatically:

### Eiffel E1

`File:Louis-Emile Durandelle, The Eiffel Tower - State of the Construction, 1888.jpg`

- `1440x1832`;
- Public domain;
- SHA256 `9c67de360bab67bc5de849d7846bf1f2972ca0722b6152c48ef753fa309bc784`.

### Eiffel E5

`File:Achèvement de la Tour Eiffel, 1889.jpg`

- `1440x1956`;
- Public domain;
- SHA256 `45ddfb7b051fe4d3e5dbb522ba9fdf96f0701cc9480fab0b9cb999105d2594ac`.

### Zipper Z1

`File:Metalzipper.jpg`

- `1440x2166`;
- Public domain;
- SHA256 `2b9f1c974e60ef7a22e55c4771126175654f75e7aa08d26240ede7cd82f18501`.

Resolved matrix state:

- Eiffel: `2 exact + 3 constructed`;
- Zipper: `1 exact + 7 constructed`;
- OLED/LCD: `0 exact + 6 constructed`;
- all exact assets hash-verified;
- no generic fallback injected.

Focused suite after resolver stage: `22/22 PASS`.

Remote commits:

- Commons adapter/tests/CLI: `2996b3807331737fe1e70a6cf641323782a0a796`, `fe8d0397b60936c33658fe08dfe1e9c39f246a34`, `c8656b2cf576547ffbb2759ef58f73d1f2038146`;
- resolver/tests/CLI: `ea2e35265dd9e850d38d35b9ce0b97c4bd83a00b`, `12372ee66094584089e1759e832943f8f5dfcd24`, `1d60ce70aaa01edd97c70aa46dba8e7a11d3dc9c`;
- local VPS stage commit: `2e9375393e85e4509f3e287251d224cd867744f9`.

Proof: `docs/V4_EXACT_MEDIA_RESOLUTION_PROOF_20260903.md`, commit `58f61750df9316ed2b80c5e505ea368b72ab434e`.

## Existing low-level motion primitive

Local repo contains a reusable Remotion SVG primitive:

- `prototype/v4/remotion/MotionDiagram.tsx`;
- local commits `00c35b5` and `4391be3`.

It supports basic shapes, lines/arrows, enter/draw/pulse/move animation. This is acceptable as a renderer backend, but the existing fixture JSONs contain many raw coordinates and therefore are NOT accepted as the semantic-director/automation contract.

## Immediate next action

Do not render hand-built fixture videos yet and do not return to induction.

1. define a high-level constructed-graphic schema with reusable archetypes such as flow, merge, split, comparison, layered stack and assembly;
2. prohibit raw x/y SVG geometry in the semantic/director-facing spec;
3. compile the high-level spec deterministically into `MotionDiagram` geometry;
4. exercise the same compiler on Eiffel, zipper and OLED/LCD;
5. bind compiled graphics to the provenance-resolved timelines;
6. only then generate renderer inputs and render materially different matrix cases;
7. inspect complete videos and record failures before architectural changes.

No n8n/DB rebuild until multiple materially different direct prototypes are HUMAN PASS.
