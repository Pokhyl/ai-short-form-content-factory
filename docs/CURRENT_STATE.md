# Current Project State — Product-First V4

Last updated: 2026-09-03

This file is authoritative for branch `rebuild/product-first-v4`. Repository/runtime state overrides chat memory.

## Production status

Semantic-v3 is rejected as a product architecture and remains frozen. Do not create any more production jobs through it.

The last semantic-v3 artifact `61f662ee-565c-4dd6-8759-17a51f3e7ec3` was HUMAN FAIL despite machine `review_ready`; M8 remains `2/10`.

## V4 source of truth

Before technical work read fresh:

1. `docs/PERMANENT_PROJECT_RULES.md`;
2. this file;
3. `docs/PRODUCT_FIRST_V4.md`;
4. `docs/ENGINEERING_HISTORY_V4.md`;
5. relevant upstream/reference docs.

## Selected architecture

`topic -> factual research -> semantic director -> speech-ready script + storyboard -> TTS -> Whisper timing from actual audio -> explicit representation modes -> mature upstream render/composition -> human review`

Key rules remain:

- evidence is not final speech;
- TTS receives speech-ready text only;
- captions/timing come from the actual generated audio;
- stock is only one visual mode and is never a generic factual fallback;
- exact media / diagram / screen-card modes remain explicit;
- machine render is not human approval;
- no topic-specific hacks;
- no mandatory paid-per-video provider.

## Upstream foundation

Primary reusable engine: `harry0703/MoneyPrinterTurbo`, exact pinned commit `cbbb366393105d5cefc254dc9ed492d43da0711b`, version `1.3.6`, MIT.

Focused upstream suite on the VPS: `316 passed`, `69 subtests passed`, `7 skipped`, zero failures after the full upstream font/i18n fixture was present.

V4 adapter skeleton is saved in GitHub commit `389ae8ea16df733b956e7432808776e4d088b715` under `prototype/v4/`.

## First direct V4 prototype — HUMAN FAIL

Artifact:

`/opt/ai-short-form-v4-runs/induction-uk-30-v1/final-v4-ffmpeg.mp4`

The user watched the exact artifact and rejected it. An uploaded copy was then inspected frame-by-frame.

Visible defects:

- source images were severely stretched/warped into the vertical canvas;
- giant subtitle boxes obscured most of the visual content;
- the explanatory diagram became unreadable;
- thermography and the final scene were dominated by subtitles instead of visual storytelling.

Systemic root cause:

The prototype reused MPT TTS/Whisper modules but introduced a bespoke local Python scene compositor and custom image-to-vertical layout. This violated the project direction to prove mature upstream behavior before inventing a replacement presentation layer.

This is not to be repaired with induction-specific image swaps or font-size tweaks.

## Immediate next action

1. Retire the custom V4 scene compositor/layout path.
2. Run a mature upstream end-to-end render flow with its normal composition/subtitle defaults and inspect the exact output before adding adapters.
3. Preserve source aspect ratio and enforce bounded subtitle occupancy as general product requirements.
4. Only after a clean upstream artifact exists may V4 add the minimum director/representation adapters.

No new production deployment, no semantic-v3 jobs, and no HUMAN PASS count change. M8 remains `2/10`.