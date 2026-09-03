# Current Project State — Product-First V4

Last updated: 2026-09-03

This file is authoritative for branch `rebuild/product-first-v4`. Repository/runtime state overrides chat memory.

## Production status

Semantic-v3 remains rejected and frozen. Do not create new production jobs through it.

No V4 artifact is human-approved yet. No production/n8n rebuild is allowed. M8 remains `2/10`.

## V4 source of truth

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
10. relevant upstream/reference docs.

## Current architecture direction

`topic -> factual research -> semantic director -> speech-ready script + semantic visual obligations -> TTS -> exact-audio Whisper timing -> provenance-bound timeline compiler -> truthful representation/media acquisition -> motion graphics/exact media -> vertical renderer -> complete-video human review`

Critical rules:

- TTS receives speech-ready text only;
- captions/timing come from the exact generated audio;
- no generic factual fallback stock;
- text is normally an overlay, not the primary visual;
- portrait orientation does not prove relevance;
- widescreen exact evidence must use contain/PIP/collage/diagram treatment;
- factual/mechanism beats must show the actual subject/mechanism or use a truthful constructed representation;
- pacing follows semantic/visual information, not an arbitrary cut-count target;
- machine render is never human approval;
- general changes must be exercised across multiple materially different topics/languages;
- every meaningful failure/root cause/decision is recorded in GitHub.

Permanent cross-topic rule: `docs/PERMANENT_PROJECT_RULES.md`, commit `427877e12e15c4c87c8c96433abadb73a9b4a845`.

## Human-failed artifacts retained as evidence

1. Custom compositor prototype — HUMAN FAIL: stretched imagery, giant subtitle blocks, unreadable diagrams.
2. OpenMontage proof #1 — HUMAN FAIL: narrated slideshow / one asset per long scene.
3. OpenMontage proof #2 — HUMAN FAIL: 25 fast cuts but text-only replacement frames and generic adjacent stock; portrait/cut frequency were false quality proxies.

Do not patch or retry these artifacts as fixtures.

## Cross-topic matrix — active

1. Induction / Ukrainian — regression mechanism case only; do not tune next on this topic.
2. Eiffel Tower construction / Polish — exact place/history.
3. Clothing zipper mechanism / Russian — object/mechanism.
4. OLED vs LCD / English — comparison/mechanism.

Matrix definition: `docs/V4_CROSS_TOPIC_MATRIX.md`.

## Structural timeline contract — TECHNICAL PASS

Code:

- `prototype/v4/timeline_contract.py`;
- `prototype/v4/tests/test_timeline_contract.py`.

It rejects:

- text-only primary visual;
- generic factual fallback stock;
- landscape fullscreen photo/video;
- contextual media without explicit justification;
- timeline gaps/overlaps.

Remote commits: `8aa5365c384a73d603a2cf072b65e51f1f5f66fb`, `47089b7e626afd5bdfcdab23dcc46bc0f0403ed0`.

## Actual-audio cross-topic automation — TECHNICAL PASS

A separate V4-only tooling environment exists at `/opt/ai-short-form-v4-tools` with `edge-tts 7.2.7`, `faster-whisper`, and `requests`. Production containers were not modified.

Three non-induction fixtures now have fresh speech-ready narration, real Edge audio and Whisper timing:

### Eiffel / Polish

- voice `pl-PL-MarekNeural`;
- duration `27.34 s`;
- Whisper language probability `1.0`;
- `5` actual-audio beats after compilation;
- script SHA256 `3ed155f6496f912fe1b1e4e85434722746cd37662388bafb1433608d9dd960db`;
- audio SHA256 `711d0e23b02fcd536df83da524e756f61674523403815a6b6039bc6629169ec9`.

### Zipper / Russian

- voice `ru-RU-DmitryNeural`;
- duration `27.14 s`;
- Whisper language probability `1.0`;
- `8` actual-audio beats;
- script SHA256 `6710dcb57cdb6c1f0ee2f6df3def6518e904bec0d49a5eb474b84c7a6a177b38`;
- audio SHA256 `0cf7c311ca6affac26ae39eab19308ce7d6c4482dd87e0eb010593f0502d668c`.

### OLED/LCD / English

- voice `en-US-AndrewNeural`;
- duration `32.34 s`;
- Whisper language probability `1.0`;
- `6` actual-audio beats;
- script SHA256 `08b25e10b36cdbfc5d585d79642d3f7e818cc8f0d783bcf1e481de9a9252a15a`;
- audio SHA256 `bd1f5b6d3401e8972134dacc7c505a692fbf65dc6737a78cc2398345d104e22b`.

The English speech guard rejected raw `OLED/LCD` abbreviations; narration was corrected by using full spoken names. No acronym-specific bypass was introduced.

## Stale-artifact defect — FIXED GENERALLY

The matrix run directories contained older `director.json`/`timeline.json` artifacts whose narration and durations no longer matched the current script/audio. This could have produced a technically valid render from mismatched generations.

General fix:

- new `prototype/v4/timeline_builder.py`;
- new tests `prototype/v4/tests/test_timeline_builder.py`;
- new CLI commands `compile-timeline` and `validate-timeline`;
- timing is derived from actual Whisper segment starts;
- visual obligations carry semantic representation only, not invented timestamps;
- timeline embeds current `script_sha256` and `audio_sha256` provenance;
- silence between speech segments remains covered by the previous meaningful visual beat;
- shared structural timeline contract runs before candidate timeline output.

Remote commits:

- builder `9c6216638639ad9b2a196cc96df978a2a382b053`;
- tests `af4cde4c147bc4271e46d78d588dce4ae42fa86f`;
- CLI `d9b0e342926160b152ad40336865c3a7c23fd4f3`.

Local VPS commit: `f73d7cab98148e4c5c842ae03722c0f9d187d554`.

Focused suite: `15/15 PASS`.

The CLI independently rebuilt Eiffel, zipper and OLED timelines and byte-matched the reference compiler output for all three.

Full proof: `docs/V4_ACTUAL_AUDIO_CROSS_TOPIC_PROOF_20260903.md`, commit `811aadd76c0cf82d7b9af73fb503c45e0b097f3b`.

## Representation state of the three active cases

- Eiffel: exact historical construction media + constructed foundation/prefabrication/rivet beats. No generic Paris/travel filler.
- Zipper: exact portrait macro zipper media + constructed slider/channel/interlock mechanics. No generic fashion filler.
- OLED/LCD: constructed side-by-side light-path/mechanism graphics. No random television/device filler.

Evidence sources include official Eiffel Tower history, YKK zipper structure, a slider patent for channel geometry, LG OLED structure, and Samsung OLED architecture.

## Immediate next action

Do not hand-build final videos and do not return to induction.

Build the next reusable automation layer:

1. exact-media acquisition with source/license/hash/dimensions provenance for declared exact-media obligations;
2. deterministic constructed-graphic payloads for diagram/motion obligations;
3. renderer input generated from the provenance-bound timeline;
4. render materially different matrix cases through the same general renderer contract;
5. inspect each complete exact video, not only frames;
6. record every failure/root cause/rule change before the next architectural change.

No n8n/DB rebuild until multiple materially different direct prototypes are HUMAN PASS.
