# V5 HyperFrames independent proof — QR code — 2026-09-04

## Status

Acceptance state: `machine_rendered` only. This artifact is not `human_approved` until the user watches the exact MP4.

## Candidate

- skill/reference repository: `GoldLegendW80/llm-video-maker` pinned at `cee12add24317c50f8a9f9de93749089a59d9f99`;
- rendering engine: `hyperframes@0.6.91` exactly;
- isolated Node runtime: `v22.23.2`;
- Chrome Headless Shell: `131.0.6778.85`;
- FFmpeg: host 6.1.1.

## Independent topic

`Как работает QR-код`

This is not an author demo and does not reuse the earlier turbo or volcano fixtures.

## Product characteristics exercised

- one continuous Russian narration track, not per-scene TTS;
- actual generated audio aligned with cached `faster-whisper small` word timestamps;
- two unique portrait Pexels clips, each used once;
- no visual looping/repetition to fill duration;
- middle mechanism section is animated HTML/CSS/GSAP graphics rather than a static image;
- word-highlight captions use timestamps from the exact generated audio;
- 9:16 1080x1920 output;
- no background music in this proof so narration and timing are easy to judge.

## Media

Used:

1. Pexels `7287317` — `Man Taking Photo of the QR Code on the Box` — query `qr code scan phone`;
2. Pexels `6763343` — `Bill Payment for Dental Care` — query `mobile payment qr code`.

A third provider result (`8830588`, returned for `smartphone scanning code`) was visibly/semantically wrong from its provider page metadata and was excluded instead of being forced into the edit. This reinforces the rule that provider ranking alone is not semantic proof.

Both used clips were normalized to H.264 30 fps with 1-second keyframe intervals before final render because HyperFrames correctly warned that the original sparse keyframes could freeze seeked frames. This is general media preprocessing, not a topic-specific acceptance patch.

## Narration

Voice: `ru-RU-DmitryNeural`.

Text:

`QR-код — это сетка данных. Камера находит три большие метки, выравнивает изображение и превращает чёрные и белые модули в биты. Контрольные блоки помогают восстановить данные даже при частичном повреждении.`

Generated audio duration: `15.144 s`.

Whisper transcript matched the narration content; 30 word tokens were aligned from the exact generated MP3.

## Visual timeline

- `0.0–3.0 s`: unique real QR scanning video + scan overlay/hook;
- `3.0–10.0 s`: animated QR matrix, finder markers, scanner pass, bit-stream and error/recovery demonstration;
- `10.0–15.144 s`: second unique real-use/payment video + error-correction payoff graphics.

No source clip is reused or looped.

## Machine checks

HyperFrames static lint after fixes:

- 0 errors;
- 1 non-product warning: caption track contains 8 timed caption groups.

HyperFrames runtime inspect:

- `ok: true`;
- 0 errors;
- 0 warnings;
- 0 info issues.

Final render had no sparse-keyframe warning after normalization.

## Exact artifact

Runtime artifact:

`/opt/ai-short-form-bakeoff/hyperframes-runtime/host/qr-proof/renders/qr-proof.mp4`

Studio review copy:

`/opt/ai-short-form-content-factory/studio/bakeoff/hyperframes-qr-ru-15.mp4`

Both SHA256:

`c9d69c2ea8ddb4e0598ada4b9c441f99d9ef0021480f72fb5e4ddbe63ac30622`

Final ffprobe:

- H.264;
- 1080x1920;
- 30 fps;
- AAC audio;
- duration `15.187696 s`;
- size `6,737,247` bytes.

The ~44 ms container/frame-grid overhead over the 15.144 s narration is render framing, not content padding or media looping.

## Gate

The exact MP4 must now be watched. If HUMAN FAIL, record the visible general defect and reject/demote this candidate instead of building a product architecture around it. If HUMAN PASS, repeat on materially different topics/languages before choosing it as the production core.
