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
12. `docs/V4_ANNOTATED_MEDIA_DISCOVERY_PROOF_20260904.md`;
13. `docs/V4_MULTISHOT_EXACT_MEDIA_RENDER_PROOF_20260904.md`;
14. relevant upstream/reference docs.

## Current architecture direction

`topic -> factual research -> semantic director -> speech-ready script + semantic scenes + internal shots[] -> TTS -> exact-audio Whisper word timing -> semantic scene/shot alignment -> shot-level exact/annotated visual resolution -> render manifest v2 -> verified render bundle v2 -> unified vertical renderer -> complete-video human review`

Critical rules:

- semantic meaning comes from the director/script; Whisper segmentation is never the semantic scene structure;
- Whisper word timestamps from the exact generated audio are timing anchors for scenes, shots and captions;
- TTS receives speech-ready text only;
- no generic factual fallback stock;
- text normally overlays meaningful visuals; it does not replace the primary visual;
- one semantic scene may contain several editing shots;
- portrait orientation does not prove relevance;
- widescreen exact evidence uses contain/PIP/collage/diagram treatment;
- factual/mechanism beats show the actual subject/mechanism or a truthful pictorial representation;
- generic boxes/labels/arrows are annotation primitives, not a valid primary factual visual;
- pacing follows semantic/visual information, not arbitrary cut-count targets;
- exact-media identity/license/hash/dimensions are resolved before rendering, including per-shot assets;
- a renderer may not independently replace resolved exact media;
- captions use exact-audio timing while speech-ready script text may correct ordinary ASR recognition errors without fabricated timestamps;
- machine render is never human approval;
- general changes are exercised across materially different topics/languages;
- every meaningful failure/root cause/decision is recorded in GitHub.

## Human-failed / rejected artifacts retained as evidence

1. Custom compositor prototype — HUMAN FAIL: stretched imagery, giant subtitle blocks, unreadable diagrams.
2. OpenMontage proof #1 — HUMAN FAIL: narrated slideshow / one asset per long scene.
3. OpenMontage proof #2 — HUMAN FAIL: high cut frequency but text-only replacement frames and generic adjacent stock.
4. OLED unified-renderer artifact — PRODUCT FAIL before user delivery: six primary motion-graphic beats reduced to box/label/arrow presentation cards.

Do not patch/retry these artifacts as fixtures.

## Cross-topic matrix — active

1. Induction / Ukrainian — regression only; do not tune next on this topic.
2. Eiffel Tower construction / Polish — exact place/history; current multishot artifact is machine-rendered and awaiting human review.
3. Clothing zipper mechanism / Russian — object/mechanism; next non-Eiffel validation target after Eiffel review.
4. OLED vs LCD / English — comparison/mechanism; old card-primary visual path rejected, must use exact/annotated/pictorial visual basis.

## Structural timeline + semantic alignment — TECHNICAL PASS

Code:

- `prototype/v4/timeline_builder.py`;
- `prototype/v4/timeline_contract.py`;
- `prototype/v4/tests/test_timeline_builder.py`;
- `prototype/v4/tests/test_timeline_contract.py`.

The old assumption `Whisper segment == semantic scene` is retired. It was disproved cross-topic because zipper had five semantic scenes but eight Whisper segments, and OLED/LCD had five semantic scenes but six Whisper segments.

Current behavior:

- semantic scene narration must reconstruct the speech-ready script;
- script tokens align to exact-audio Whisper `words[]`;
- semantic scene starts come from word alignment, not ASR segment boundaries;
- optional `shots[]` are timed inside semantic scenes from the same actual-audio word alignment;
- scene and shot tracks must be continuous;
- text-only primary visuals, generic factual fallback, invalid fullscreen landscape media and unjustified contextual media remain rejected.

Current timing provenance: `actual_audio_whisper_word_alignment`.

## Actual-audio cross-topic fixtures

V4-only tooling environment: `/opt/ai-short-form-v4-tools` with `edge-tts 7.2.7`, `faster-whisper`, `requests`. Production containers unchanged.

Fresh real-audio fixtures:

- Eiffel / PL: `27.34 s`, language probability `1.0`;
- Zipper / RU: `27.14 s`, language probability `1.0`;
- OLED/LCD / EN: `32.34 s`, language probability `1.0`.

The English speech guard rejected raw `OLED/LCD` abbreviations; narration uses full spoken names. No bypass was added.

## Exact / annotated media acquisition — TECHNICAL PASS

Automation:

- `prototype/v4/commons_media.py` — Commons discovery/acquisition with free-license/source/dimensions/hash metadata and cached discovery;
- `prototype/v4/asset_resolver.py` — scene/shot identity + SHA + dimensions/layout validation;
- `prototype/v4/visual_adequacy.py` — rejects presentation-card graphics as primary factual visuals;
- `annotated_exact` combines verified exact media with motion overlays instead of replacing the subject with graphic cards.

Wikimedia `429` behavior is fail-fast/cached; no provider sleep or blind retry was added.

## Caption alignment — TECHNICAL PASS

New code:

- `prototype/v4/caption_alignment.py`;
- `prototype/v4/tests/test_caption_alignment.py`.

Contract:

- Whisper/ASR remains authoritative for timing;
- speech-ready script is authoritative display text when alignment is unambiguous;
- merged ASR words may carry combined script display text on the same real interval;
- collapsed representations such as a spoken year recognized as `1889` retain the real ASR token/timing rather than fabricating sub-word timestamps.

## Render manifest / bundle / renderer — TECHNICAL PASS

Implemented:

- `prototype/v4/render_manifest.py` — `v4-render-manifest-2`, flattens validated shots into distinct visual items;
- `prototype/v4/render_bundle.py` — `v4-render-bundle-2`, stages assets by `visual_id` to prevent multiple shots in one scene overwriting one another;
- `prototype/v4/remotion/VerticalShort.tsx` — one renderer for exact media, annotated exact media and accepted motion graphics; sequences are keyed by `visual_id`;
- CLI `build-render-manifest` and `stage-render-bundle`.

A clean checkout of authoritative remote HEAD `dd8563a272178ae7a0a2cb8b86b23982f8bde23a` passed the focused V4 suite:

`58/58 PASS`

No result from the local scratch directory is being used as substitute proof for the authoritative branch.

## Eiffel / Polish multishot exact-media prototype — MACHINE RENDERED

Run:

`/opt/ai-short-form-v4-runs/cross-topic-20260903/eiffel-pl/multishot-v2`

Timeline:

- `5` semantic scenes;
- `11` internal shots;
- timing from exact-audio word alignment;
- alignment coverage `0.873016`;
- `11` exact hash-verified assets;
- `0` constructed primary visuals;
- `0` generic factual fallback assets.

The asset set includes exact historical Eiffel construction images, foundation caissons, the actual Levallois-Perret workshops, exact Eiffel rivets and completion imagery. Landscape exact evidence uses contain treatment.

Exact artifact:

`/opt/ai-short-form-v4-runs/cross-topic-20260903/eiffel-pl/multishot-v2/remotion-runtime/out/eiffel-multishot-v2.mp4`

Machine proof:

- SHA256 `068d43143e9db5d58370fd17300d4b169e2e32407bdda1b85ec1a637587349c3`;
- size `55,143,502` bytes;
- duration `27.414 s`;
- H.264 `1080x1920`;
- AAC `48 kHz` stereo.

The exact final MP4 received a pre-delivery contact-sheet sanity check. It no longer contains the previous standalone text-card replacement frames or generic lifestyle stock. This does NOT make it human-approved.

Proof: `docs/V4_MULTISHOT_EXACT_MEDIA_RENDER_PROOF_20260904.md`.

Current acceptance state: `machine_rendered`.

## Immediate next action

1. user must watch the exact Eiffel multishot MP4;
2. if HUMAN FAIL, record the observed general defect before any architecture change and do not tune Eiffel alone;
3. apply the same semantic scene + internal shots + exact/annotated-media path to zipper/Russian and OLED/LCD/English;
4. require multiple materially different HUMAN PASS artifacts before n8n/PostgreSQL orchestration resumes.

No n8n/DB rebuild until multiple materially different direct prototypes are HUMAN PASS.
