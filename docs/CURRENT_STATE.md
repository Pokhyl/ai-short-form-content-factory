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
8. relevant upstream/reference docs.

## Current architecture direction

`topic -> factual research -> semantic director -> speech-ready script + semantic scenes + shots[] -> TTS -> actual-audio Whisper timing -> exact/relevant portrait media + diagrams/motion graphics -> continuous visual track + text overlays -> Remotion/FFmpeg composition -> human review`

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
- when exact moving footage is unavailable, change representation mode to exact portrait photo + motion, diagram, collage, PIP or motion graphic rather than insert generic stock;
- normal factual shorts maintain a continuous meaningful visual track;
- `hero_title`, `text_card`, `callout` and similar typography do not replace the primary visual by default; text normally overlays relevant visual material;
- normal full-screen TikTok photo/video shots must use portrait/vertical or genuinely crop-safe source media;
- widescreen exact evidence is routed to diagram/card/collage/PIP/contain treatment, not used as an ordinary full-screen photo;
- vertical captions/key text must stay inside a TikTok-safe region rather than hugging the bottom UI area;
- no bespoke semantic threshold maze;
- no mandatory paid-per-video provider;
- machine render is not human approval;
- no architecture may be validated on one topic only.

Permanent cross-topic rule is in `docs/PERMANENT_PROJECT_RULES.md`, commit `427877e12e15c4c87c8c96433abadb73a9b4a845`.

## Renderer evaluation

### MoneyPrinterTurbo

Still useful as reference/source for TTS, Whisper and media contracts, but rejected as the V4 renderer on the current VPS. Clean upstream rendering was too slow and its concat run failed after a generated temp clip disappeared. No custom workaround was accepted.

### Short Video Maker

Rejected as the full pipeline because its normal path is English/Kokoro + Pexels and includes generic fallback footage behavior. Its Remotion patterns remain reference material only.

### OpenMontage

Current renderer evaluation source: `calesthio/OpenMontage`, commit `cd9f3c1f03368be87b140af494914b8ee4e3c7a4`, AGPL-3.0.

OpenMontage is evaluation/reference only. No OpenMontage source code has been copied into this repository. License compatibility must be resolved before any code adoption.

## OpenMontage proof #1 — HUMAN FAIL

Artifact:

`/opt/ai-short-form-v4-upstreams/OpenMontage/remotion-composer/out/v4-induction.mp4`

It corrected the previous stretched images/giant subtitle defects, but the user rejected it because the product still looked like a narrated slideshow rather than TikTok:

- five semantic scenes became five long visual scenes;
- approximately one asset stayed on screen for each narration block;
- insufficient motion/cut cadence;
- ordinary still-image treatment relied on landscape/widescreen sources rather than portrait-first TikTok media.

Permanent record: `docs/V4_TIKTOK_FORMAT_FAIL_20260903.md`.

## OpenMontage proof #2 — 25-cut portrait-first — HUMAN FAIL

Artifact:

`/opt/ai-short-form-v4-upstreams/OpenMontage/remotion-composer/out/v4-induction-tiktok.mp4`

SHA256:

`dbaf1e92e3cd7fd66920520a683b403a46bb04b875a89fcbda696a2950b54af5`

Machine characteristics:

- `25` visual cuts across `31.968 s`;
- maximum cut duration `1.6 s`;
- portrait source-media guard passed;
- final encode `1080x1920`, H.264 + AAC;
- TikTok caption safe-zone moved upward.

Human verdict: HUMAN FAIL for the product as a whole.

Verified general defects:

1. standalone `hero_title`, `text_card` and `callout` cuts repeatedly replaced the meaningful visual track with text-only presentation frames;
2. several moving stock shots were generic cooking/electric-stove footage rather than exact or clearly relevant visual evidence for the factual subject;
3. optimizing cut frequency and portrait orientation did not create good TikTok storytelling because relevance and continuous visual meaning were still weak.

Permanent record: `docs/V4_MULTISHOT_HUMAN_FAIL_20260903.md`, commit `b3935624174b97bcc0c432623406d7a71f8663be`.

## Immediate next action — stop tuning one fixture

Do NOT produce another induction-specific iteration now.

Build a small cross-topic validation matrix before the next candidate renderer/media/director architecture is accepted. The matrix must exercise materially different visual problems, for example:

1. technical/mechanism explainer — exact mechanism + diagrams/motion graphics;
2. concrete exact-media topic — person/place/object/history where the real entity must stay visible;
3. process/list/comparison topic — mixed real visuals + overlays/cards/diagrams;
4. multiple target languages rather than one language only.

For every matrix case, evaluate the same general contracts:

- meaningful continuous visual track;
- no standalone text substitution unless intentionally selected and justified;
- no generic factual fallback stock;
- portrait-first full-screen media;
- exact horizontal evidence only in appropriate contain/PIP/diagram treatment;
- pacing driven by meaning, not an arbitrary cut-count target;
- captions from actual audio and inside safe zone;
- human review of exact artifacts.

Every failure, root cause, rule change and architecture decision must be written to GitHub before moving to the next independent stage.

No production/n8n rebuild until direct prototypes receive HUMAN PASS across materially different topics/languages.

M8 remains `2/10`.