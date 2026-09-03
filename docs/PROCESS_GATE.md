# Process Gate — Product-First V4

Last updated: 2026-09-03

`docs/CURRENT_STATE.md` is authoritative.

## Active gate

Semantic-v3 production generation is frozen after a machine `review_ready` video received explicit HUMAN FAIL.

Do not patch or retest that architecture.

The active gate is a direct product prototype outside n8n/PostgreSQL.

## Mandatory sequence

1. Read fresh `PERMANENT_PROJECT_RULES`, `CURRENT_STATE`, `PRODUCT_FIRST_V4` and V4 history.
2. Prefer a mature upstream component before implementing a commodity subsystem.
3. Keep MoneyPrinterTurbo pinned and verify its upstream tests before adapting its services.
4. Produce one validated semantic director artifact containing natural spoken script and explicit scene storyboard.
5. Reject raw written-form speech before TTS: no unspoken digits/units/abbreviations/URLs/editorial notation.
6. Generate one continuous voice at natural rate.
7. Derive subtitles/timing from the actual audio with Whisper/faster-whisper or equivalent alignment.
8. Produce scene assets according to explicit representation modes; no automatic generic-stock fallback for factual/mechanism scenes.
9. Preview scene selections before final render.
10. Render one 9:16 artifact and perform technical checks.
11. User watches the exact artifact. Only explicit acceptance becomes `human_approved`.
12. Repeat on materially different topics/languages before designing n8n/DB integration.

## Upstream proof gate

Pinned MoneyPrinterTurbo commit:

`cbbb366393105d5cefc254dc9ed492d43da0711b`

Focused upstream suite currently proved:

- 316 tests passed;
- 69 subtests passed;
- 7 skipped;
- 0 failures.

Do not silently change the pin.

## Product gates

### Script

- conversational rather than encyclopedic;
- facts trace to evidence;
- no raw source-copy cadence;
- target language natural to a human listener.

### Speech

- speech-ready written form;
- no ambiguous abbreviation pronunciation;
- natural male voice for the supported language unless a later human-approved voice profile changes it;
- no tempo/rate fitting.

### Visuals

- every scene has an intentional representation mode;
- a viewer can identify the intended subject/process from the selected asset/graphic;
- unrelated lifestyle stock is a fail even if metadata/CLIP/diversity scores pass;
- unresolved factual media does not get replaced by a generic joker clip.

### Captions/edit

- timing derives from actual voice;
- readable short-form captions;
- visual changes support the narration rather than arbitrary cadence.

### Render

- playable vertical MP4;
- technical validation is necessary but not sufficient.

## Forbidden shortcuts

- no semantic-v3 fresh jobs;
- no topic-specific pronunciation mapping;
- no topic-specific visual blacklist;
- no threshold tuning to rescue irrelevant stock;
- no fixed synthetic subtitle beat count;
- no rebuilding MoneyPrinterTurbo TTS/Whisper/material/render layers without a proven gap;
- no n8n/DB integration before direct prototype HUMAN PASS;
- no mandatory paid-per-video provider.