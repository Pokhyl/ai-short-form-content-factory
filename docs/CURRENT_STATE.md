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

`topic -> factual research -> semantic director -> speech-ready script + storyboard -> TTS -> Whisper timing from actual audio -> explicit representation modes -> FFmpeg/Remotion render -> human review`

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

## First direct V4 prototype — MACHINE RENDERED

Run directory:

`/opt/ai-short-form-v4-runs/induction-uk-30-v1`

Topic/language/target:

`Як працює індукційна плита / uk / 30 s`

Important boundary: the first run used a manually authored/reference `director.json` to prove the downstream product path. This is not yet proof of an automatic semantic-director provider.

Speech/timing:

- exactly one V4 Edge synthesis via MoneyPrinterTurbo;
- `uk-UA-OstapNeural`, rate `1.0`, no speed fitting;
- measured voice `31.968 s`;
- faster-whisper `small`, CPU `int8`, on the exact audio;
- MPT subtitle correction fixed recognition spelling while preserving real timestamps;
- scene boundaries from actual-audio sentence starts: `0.0 / 4.36 / 11.62 / 19.09 / 23.70 / 31.968`.

Visuals:

1. real induction cooktop;
2. real induction coil/electronics interior;
3. induction-heating diagram;
4. induction-pan thermography;
5. compatibility explanation card.

No generic stock fallback was used.

Final artifact:

`/opt/ai-short-form-v4-runs/induction-uk-30-v1/final-v4-ffmpeg.mp4`

Machine proof:

- SHA256 `a2fe175acbc35a36185d1044eb4358595bc96ec7766287d9862f59db25842d61`;
- `32.000000 s`;
- H.264 / 1080x1920 / yuv420p;
- AAC / 48 kHz / stereo;
- state `machine_rendered` only.

The full proof and environment findings are recorded in `docs/ENGINEERING_HISTORY_V4.md`, commit `2418290a8589c19137bf1f33ce66bf08e412d6a6`.

## Immediate next action

The user must watch the exact first V4 prototype.

- If HUMAN FAIL: fix the observed general product defect in V4; do not patch the induction topic specifically.
- If HUMAN PASS: keep production frozen, integrate an automatic provider-pluggable semantic director, then make a materially different second direct prototype before any n8n/PostgreSQL orchestration work.

No production deployment is allowed yet.