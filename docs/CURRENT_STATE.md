# Current Project State — Product-First V4

Last updated: 2026-09-03

This file is authoritative for branch `rebuild/product-first-v4`. Repository/runtime state overrides chat memory.

## Production status

Semantic-v3 is rejected as a product architecture and remains frozen. Do not create new production jobs through it.

The last semantic-v3 artifact `61f662ee-565c-4dd6-8759-17a51f3e7ec3` was HUMAN FAIL despite machine `review_ready`. M8 remains `2/10`.

The first direct V4 custom-compositor artifact was also HUMAN FAIL. Its bespoke Python image/layout compositor is permanently retired.

## V4 source of truth

Before technical work read fresh:

1. `docs/PERMANENT_PROJECT_RULES.md`;
2. this file;
3. `docs/PRODUCT_FIRST_V4.md`;
4. `docs/ENGINEERING_HISTORY_V4.md`;
5. `docs/V4_RENDER_EVAL_20260903.md`;
6. relevant upstream/reference docs.

## Current architecture direction

`topic -> factual research -> semantic director -> speech-ready script + storyboard -> TTS -> Whisper word timing from actual audio -> explicit representation modes -> mature Remotion/FFmpeg composition -> human review`

Key rules:

- evidence is not final speech;
- TTS receives speech-ready text only;
- captions/timing come from the actual generated audio;
- stock is one visual mode, never a generic factual fallback;
- exact media / diagram / card modes remain explicit;
- no bespoke presentation compositor until an upstream renderer is proven;
- machine render is not human approval;
- no topic-specific hacks;
- no mandatory paid-per-video provider.

## Renderer evaluation

### MoneyPrinterTurbo

Pinned upstream MPT remains useful as a source/reference for TTS, Whisper and some media contracts, but is rejected as the V4 renderer. Its clean upstream render path was too slow on the 2-vCPU VPS and the concat stage failed when a generated temp clip disappeared before FFmpeg concat. No custom workaround was accepted.

### Short Video Maker

Rejected as the full pipeline because its normal architecture is English/Kokoro + Pexels and includes generic fallback footage behavior. Its Remotion patterns may still be referenced.

### OpenMontage

Current renderer candidate: `calesthio/OpenMontage`, commit `cd9f3c1f03368be87b140af494914b8ee4e3c7a4`.

Important: upstream license is AGPL-3.0. The current run is an evaluation/reference prototype only. No OpenMontage code has been copied into this repository; license compatibility must be resolved before code adoption.

## Current V4 review artifact

Artifact on VPS:

`/opt/ai-short-form-v4-upstreams/OpenMontage/remotion-composer/out/v4-induction.mp4`

Input reused the existing speech-ready Ukrainian voice track; no new Edge synthesis was consumed for this renderer comparison.

Timing/captions:

- voice duration `31.968 s`;
- 68 faster-whisper word timestamps;
- speech-ready script also exactly 68 words;
- script spellings replace recognition spellings one-for-one while preserving every actual timestamp.

Visual path:

- five exact scene assets;
- normal photos use upstream OpenMontage `ImageScene`;
- wide technical diagrams use upstream `ScreenshotScene` contain-layout;
- upstream renderer code was not modified;
- only props/assets/audio/captions were supplied.

Machine proof:

- SHA256 `d9b1670b6f5818036a88486582c76b5b70fe51f9b26d9e0c6a1bead638d051dc`;
- size `12,233,895` bytes;
- duration `33.046 s`;
- H.264 `1080x1920`;
- AAC `48 kHz` stereo.

Pre-delivery visual inspection was performed on frames near 2 / 6 / 14 / 21 / 27 seconds. The prior gross layout failures are absent: images are not warped, wide diagrams are visible via contain-layout, the coil and thermography are visible, and captions remain a bounded bottom overlay rather than covering most of the frame.

Full evaluation: `docs/V4_RENDER_EVAL_20260903.md`, commit `ad20b43111aa70a2ef7cbc16119015930ddcf0d3`.

## Immediate next action

The user watches the exact OpenMontage artifact.

- If HUMAN FAIL: reject/fix the observed general defect; do not patch this induction fixture specifically.
- If HUMAN PASS: do not deploy production yet; resolve renderer licensing/adoption and then run materially different direct prototypes before rebuilding n8n/DB orchestration.

No HUMAN PASS count change yet. M8 remains `2/10`.