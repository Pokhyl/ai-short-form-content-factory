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
7. relevant upstream/reference docs.

## Current architecture direction

`topic -> factual research -> semantic director -> speech-ready script + semantic scenes + shots[] -> TTS -> actual-audio Whisper timing -> portrait-first media / diagrams / motion beats -> Remotion/FFmpeg composition -> human review`

Critical product rules:

- evidence is not final speech;
- TTS receives speech-ready text only;
- captions/timing come from actual generated audio;
- a semantic scene is not one visual asset;
- each semantic scene may contain multiple `shots[]`;
- stock is one visual mode, never a generic factual fallback;
- normal full-screen TikTok photo/video shots must use portrait/vertical or genuinely crop-safe source media;
- widescreen exact evidence is routed to diagram/card/collage/PIP/contain treatment, not used as an ordinary full-screen photo;
- no bespoke semantic threshold maze;
- no mandatory paid-per-video provider;
- machine render is not human approval.

Authoritative editing contract: `docs/PRODUCT_FIRST_V4.md`, updated in commit `c48abce6f95e6af86dc7beb7afc540d054e8d683`.

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

Permanent record: `docs/V4_TIKTOK_FORMAT_FAIL_20260903.md`, commit `4f7194628314530055598dfb16fce3efcb62365d`.

## Current direct prototype — portrait-first multi-shot

The next direct prototype reuses the existing speech-ready Ukrainian narration. No new Edge synthesis is consumed.

Audio/timing:

- voice duration `31.968 s`;
- 68 actual-audio faster-whisper word timestamps;
- same corrected speech-ready 68-word caption stream.

New editing timeline:

- `25` visual cuts across `31.968 s` instead of `5` long scene-assets;
- semantic scenes contain multiple visual beats;
- portrait Pexels source assets include native vertical electric/induction stove media;
- exact horizontal mechanism evidence (coil, induction diagram, thermography) is used only in contain/highlight technical beats;
- ordinary full-screen wide photos are not used;
- hook and close include active portrait video;
- kinetic text/callout beats are short emphasis, not the main visual track.

Portrait asset examples selected for this prototype:

- Pexels photo `34558051` — person using a modern induction cooktop, original `4433x6650`;
- Pexels photo `36400778` — cooking instant noodles on induction stove, original `2433x3637`;
- Pexels photo `6755621` — pot on electric stove, original `4196x6294`;
- Pexels photo `6938707` — brewing coffee on induction hob, original `2923x4384`;
- Pexels photo `6755626` — induction cooking/kitchenware, original `4128x6192`;
- Pexels portrait videos include `6822626`, `6247893`, `8094272`.

Runtime files:

- assets/props: `/opt/ai-short-form-v4-upstreams/OpenMontage/remotion-composer/public/v4-induction-tiktok/`;
- timeline contains `25` cuts, final cut ends at `31.968 s`;
- nine Remotion still checkpoints rendered successfully before the full encode;
- full render target: `/opt/ai-short-form-v4-upstreams/OpenMontage/remotion-composer/out/v4-induction-tiktok.mp4`.

The full render is currently an evaluation artifact only and must not be called HUMAN PASS until the user watches the exact output.

## Immediate next action

1. Complete the 25-cut portrait-first direct render.
2. Inspect the exact MP4 before delivery, including cadence/layout and not only ffprobe.
3. User reviews the exact artifact.
4. If HUMAN FAIL, fix the general observed product defect rather than this induction fixture specifically.
5. No production/n8n rebuild until direct prototypes receive HUMAN PASS across materially different topics/languages.

M8 remains `2/10`.
