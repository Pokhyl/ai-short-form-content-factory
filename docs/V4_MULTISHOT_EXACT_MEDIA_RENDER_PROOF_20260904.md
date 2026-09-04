# V4 Multishot Exact-Media Render Proof — 2026-09-04

## Status

This document records the next Product-First V4 direct-prototype stage after the OLED pre-delivery rejection.

The exact Eiffel artifact described below is `machine_rendered`, not `human_approved`.

Semantic-v3 production remains frozen. No n8n/DB rebuild is authorized by this proof.

## Systemic timing defect found before render

The first V4 timeline compiler incorrectly treated Whisper/ASR segment boundaries as semantic scene boundaries.

Cross-topic evidence proved this was invalid:

- Eiffel happened to have five semantic scenes and five Whisper segments;
- zipper has five semantic scenes but Whisper produced eight segments, including sentence splits across different ASR chunks;
- OLED/LCD has five semantic scenes but Whisper produced six segments whose boundaries do not match the semantic script scenes.

Therefore `Whisper segment == semantic scene` was an architectural bug, not a topic-specific problem.

## General correction

`prototype/v4/timeline_builder.py` now keeps semantic narration as the scene authority and uses exact-audio Whisper `words[]` only as timing anchors.

The compiler:

1. requires semantic scene narration to reconstruct the speech-ready script exactly;
2. aligns normalized script tokens to exact-audio Whisper word timestamps;
3. derives semantic scene starts from the aligned words, independently of Whisper segment boundaries;
4. fails closed when script/audio alignment coverage is too low;
5. supports `shots[]` inside each semantic scene;
6. requires shot narration to reconstruct its parent scene narration exactly;
7. derives shot starts from the same exact-audio word alignment;
8. records `timing_source = actual_audio_whisper_word_alignment`.

This preserves the V4 rule: semantic structure comes from the director; timing comes from the actual generated audio.

## Shot-level visual contract

`prototype/v4/timeline_contract.py` now validates both semantic beats and their internal shots.

For every shot it enforces the same general factual-visual rules already applied to scenes:

- no text-only primary visual;
- no generic factual fallback stock;
- valid exact/contextual/constructed representation;
- landscape photo/video cannot silently become fullscreen evidence;
- continuous shot coverage inside the parent semantic scene;
- no shot gaps/overlaps;
- unique shot IDs.

## Shot-level exact-media resolution

`prototype/v4/asset_resolver.py` now resolves and hash-verifies exact assets by visual/shot ID rather than assuming one asset per semantic beat.

This closes the one-scene/one-file assumption that caused the earlier slideshow architecture.

`prototype/v4/render_manifest.py` flattens validated semantic shots into renderer visual items. `prototype/v4/render_bundle.py` stages assets by `visual_id`, so two shots in one semantic scene cannot overwrite each other. `prototype/v4/remotion/VerticalShort.tsx` also keys render sequences by `visual_id`.

## Caption correction without fabricated timing

A second systemic defect was found in actual Polish/Russian ASR output:

- Polish speech `je nitami` was recognized as one token similar to `jenitami`;
- the speech-ready Polish year phrase was recognized by ASR as the single display token `1889`;
- Russian fixtures also contained ordinary recognition substitutions.

New `prototype/v4/caption_alignment.py` follows the mature subtitle-correction principle already observed in MoneyPrinterTurbo:

- Whisper remains authoritative for time intervals;
- the speech-ready script is authoritative for display text where alignment is unambiguous;
- adjacent script words may share one real ASR interval when the recognizer merged them;
- when ASR collapses several spoken words into another representation, such as a year into digits, the real ASR token/timing is retained rather than inventing fake sub-word timestamps.

The Eiffel render therefore displays `je nitami.` over the real merged ASR interval and keeps `1889` over the actual recognized year interval.

## Cross-topic regression suite

A clean checkout of authoritative branch `rebuild/product-first-v4` at remote HEAD `dd8563a272178ae7a0a2cb8b86b23982f8bde23a` passed:

- `58/58` focused V4 tests;
- no failures.

New coverage includes:

- semantic scenes independent of Whisper segment boundaries;
- shot alignment inside semantic scenes from actual word timestamps;
- continuous multishot visual tracks;
- distinct exact assets per shot;
- multishot render-manifest flattening;
- no staged-asset overwrite for multiple shots in one scene;
- caption text correction while retaining exact-audio timing.

## Eiffel / Polish exact-media prototype

Run directory:

`/opt/ai-short-form-v4-runs/cross-topic-20260903/eiffel-pl/multishot-v2`

Audio/timing:

- exact voice duration in the timeline: `27.340 s`;
- audio SHA256: `711d0e23b02fcd536df83da524e756f61674523403815a6b6039bc6629169ec9`;
- semantic alignment coverage: `0.873016`;
- timing source: `actual_audio_whisper_word_alignment`.

Visual plan:

- `5` semantic scenes;
- `11` internal visual shots;
- `11` exact, hash-verified assets;
- `0` constructed primary visuals;
- `0` generic factual fallback assets.

The shots include exact historical construction images, Eiffel foundation caissons, the actual Levallois-Perret workshops used for fabrication context, exact tower rivets, and construction/completion images. Portrait exact sources use fullscreen treatment; landscape evidence such as workshops/rivets uses contain treatment rather than destructive crop/stretch.

## Exact rendered artifact

File:

`/opt/ai-short-form-v4-runs/cross-topic-20260903/eiffel-pl/multishot-v2/remotion-runtime/out/eiffel-multishot-v2.mp4`

Machine proof:

- SHA256: `068d43143e9db5d58370fd17300d4b169e2e32407bdda1b85ec1a637587349c3`;
- size: `55,143,502` bytes;
- ffprobe duration: `27.414 s`;
- video: H.264, `1080x1920`;
- audio: AAC, `48 kHz`, stereo.

A contact sheet was extracted from the exact final MP4 and visually sanity-checked before user delivery. It shows a sequence of exact historical Eiffel construction/foundation/workshop/rivet/completion images and does not contain the previous standalone text-card replacement frames or generic lifestyle stock.

This check is only pre-delivery sanity verification. It is not a product-quality approval.

## Acceptance state

Current Eiffel artifact state:

`machine_rendered`

It must remain NOT `human_approved` until the user watches this exact MP4 and explicitly accepts it.

## Next boundary

1. obtain complete-video human review of the exact Eiffel artifact;
2. if HUMAN FAIL, record the observed general defect before changing architecture;
3. apply the same semantic-scene + internal-shot + exact/annotated-media pipeline to zipper/Russian and OLED/LCD/English rather than tuning only Eiffel;
4. require multiple materially different HUMAN PASS artifacts before n8n/PostgreSQL orchestration resumes.
