# Current Project State — Product-First V4

Last updated: 2026-09-03

This file is authoritative for branch `rebuild/product-first-v4`. Repository/runtime state overrides chat memory.

## Production status

Semantic-v3 is rejected as a product architecture and remains frozen. Do not create new production jobs through it.

The last semantic-v3 artifact `61f662ee-565c-4dd6-8759-17a51f3e7ec3` was HUMAN FAIL despite machine `review_ready`. M8 remains `2/10`.

No V4 artifact is human-approved yet. No production/n8n rebuild is allowed.

## V4 source of truth

Before technical work read fresh:

1. `docs/PERMANENT_PROJECT_RULES.md`;
2. this file;
3. `docs/PRODUCT_FIRST_V4.md`;
4. `docs/ENGINEERING_HISTORY_V4.md`;
5. `docs/V4_RENDER_EVAL_20260903.md`;
6. `docs/V4_TIKTOK_FORMAT_FAIL_20260903.md`;
7. `docs/V4_MULTISHOT_HUMAN_FAIL_20260903.md`;
8. `docs/V4_CROSS_TOPIC_MATRIX.md`;
9. `docs/V4_CROSS_TOPIC_AUDIT_20260903.md`;
10. `docs/V4_CROSS_TOPIC_CONTRACT_IMPLEMENTATION_20260903.md`;
11. relevant upstream/reference docs.

## Current architecture direction

`topic -> factual research -> semantic director -> speech-ready script + semantic scenes + shots[] -> TTS -> actual-audio Whisper timing -> truthful representation selection -> exact/relevant portrait media + diagrams/motion graphics -> continuous visual track + text overlays -> Remotion/FFmpeg composition -> human review`

Critical product rules:

- evidence is not final speech;
- TTS receives speech-ready text only;
- captions/timing come from actual generated audio;
- a semantic scene is not one visual asset;
- each semantic scene may contain multiple `shots[]`;
- stock is one visual mode, never a generic factual fallback;
- portrait orientation alone does not prove semantic relevance;
- normal full-screen factual video/photo must show the actual subject/action or clearly justified context;
- generic kitchen/lifestyle/adjacent stock is forbidden as a fallback for factual/mechanism narration;
- when exact moving footage is unavailable, change representation mode to exact photo + motion, diagram, collage, PIP or motion graphic rather than insert generic stock;
- normal factual shorts maintain a continuous meaningful visual track;
- `hero_title`, `text_card`, `callout` and similar typography do not replace the primary visual by default; text normally overlays relevant visual material;
- normal full-screen TikTok photo/video shots must use portrait/vertical or genuinely crop-safe source media;
- widescreen exact evidence is routed to contain/collage/PIP/diagram treatment, not used as an ordinary full-screen photo;
- vertical captions/key text must stay inside a TikTok-safe region;
- pacing is driven by semantic/visual information, not an arbitrary fixed cut-count target;
- no bespoke semantic threshold maze;
- no mandatory paid-per-video provider;
- machine render is not human approval;
- no architecture may be validated on one topic only.

Permanent cross-topic rule: `docs/PERMANENT_PROJECT_RULES.md`, commit `427877e12e15c4c87c8c96433abadb73a9b4a845`.

## Renderer evaluation

### MoneyPrinterTurbo

Useful as reference/source for TTS, Whisper and some media contracts, but rejected as the V4 renderer on the current VPS. Clean upstream rendering was too slow and its concat run failed after a generated temp clip disappeared. No custom workaround was accepted.

### Short Video Maker

Rejected as the full pipeline because its normal path is English/Kokoro + Pexels and includes generic fallback footage behavior. Its Remotion patterns remain reference material only.

### OpenMontage

Evaluation/reference source: `calesthio/OpenMontage`, commit `cd9f3c1f03368be87b140af494914b8ee4e3c7a4`, AGPL-3.0.

No OpenMontage source code has been copied into this repository. License compatibility must be resolved before code adoption.

## Human-failed V4 artifacts

### Custom compositor prototype — HUMAN FAIL

Systemic defects: stretched/warped imagery, oversized subtitle boxes, unreadable diagrams. Bespoke compositor path retired.

### OpenMontage proof #1 — HUMAN FAIL

Artifact: `/opt/ai-short-form-v4-upstreams/OpenMontage/remotion-composer/out/v4-induction.mp4`

General defect: narrated slideshow — five long scene-assets, insufficient visual change, landscape stills as ordinary vertical shots.

### OpenMontage proof #2 — HUMAN FAIL

Artifact: `/opt/ai-short-form-v4-upstreams/OpenMontage/remotion-composer/out/v4-induction-tiktok.mp4`

SHA256: `dbaf1e92e3cd7fd66920520a683b403a46bb04b875a89fcbda696a2950b54af5`

Machine characteristics:

- `25` visual cuts across `31.968 s`;
- maximum cut duration `1.6 s`;
- portrait source-media guard passed;
- final encode `1080x1920`, H.264 + AAC;
- caption safe-zone moved upward.

Human verdict: HUMAN FAIL for the product as a whole.

Verified general defects:

1. standalone typography repeatedly replaced the meaningful visual track;
2. generic cooking/electric-stove clips were accepted even though they were not exact/relevant enough for the factual subject;
3. high cut frequency + portrait orientation were incorrectly treated as proxies for TikTok quality.

Permanent record: `docs/V4_MULTISHOT_HUMAN_FAIL_20260903.md`.

## Cross-topic validation matrix — active

Do not tune induction again as the next fixture.

Active matrix:

1. technical mechanism / Ukrainian — induction regression case;
2. exact place/history / Polish — `Jak zbudowano Wieżę Eiffla`;
3. object/mechanism / Russian — `Как работает молния на одежде`;
4. comparison / English — `OLED vs LCD: what actually changes`.

Matrix definition: `docs/V4_CROSS_TOPIC_MATRIX.md`, commit `328a4e5288ea14af532fb2eef31ef9debb65b927`.

Evidence/representation audit: `docs/V4_CROSS_TOPIC_AUDIT_20260903.md`, commit `2e015800a4e6b5f659d697d54f9becbbf23c8c26`.

Audit conclusion:

- history/exact entity -> exact archive media + collage/PIP/contain;
- physical mechanism -> macro exact media + original motion graphics;
- display comparison -> original side-by-side mechanism graphics + exact supporting shots;
- the shared architecture is truthful representation selection, not `find portrait stock for every beat`.

## Structural timeline contract — TECHNICAL PASS

New code:

- `prototype/v4/timeline_contract.py`;
- `prototype/v4/tests/test_timeline_contract.py`.

Remote commits:

- guard: `8aa5365c384a73d603a2cf072b65e51f1f5f66fb`;
- matrix tests: `47089b7e626afd5bdfcdab23dcc46bc0f0403ed0`.

Local VPS commit: `d3cfcdea7f4661bc65037aa31a0dd8001cf386a3`.

Test command:

`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest -v prototype.v4.tests.test_contract prototype.v4.tests.test_timeline_contract`

Result: `12/12 PASS`.

The same contract is exercised across induction / Eiffel / zipper / OLED fixtures.

It rejects structurally:

- text-only primary visual;
- generic factual fallback stock;
- landscape fullscreen photo/video;
- contextual media without explicit justification;
- timeline gaps/overlaps.

It deliberately does not impose semantic similarity thresholds or a fixed maximum cut duration.

Implementation proof: `docs/V4_CROSS_TOPIC_CONTRACT_IMPLEMENTATION_20260903.md`, commit `567ff6f767f6ded0ffd2733ed04f4546a3b0a95e`.

## Immediate next action

Do NOT render another induction-specific variant.

Next stage:

1. build/direct three non-induction matrix storyboards against the same timeline contract;
2. obtain exact/relevant media or choose truthful constructed representation per beat;
3. validate all timelines with `timeline_contract.py` before any render;
4. render materially different matrix cases through the same general renderer contracts;
5. inspect exact outputs as complete videos, not only isolated frames;
6. record every failure/root cause/rule change in GitHub before the next independent change;
7. only HUMAN PASS artifacts count toward resuming production orchestration.

No production/n8n rebuild until direct prototypes receive HUMAN PASS across materially different topics/languages.

M8 remains `2/10`.