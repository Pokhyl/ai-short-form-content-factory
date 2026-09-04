# V4 Eiffel Multishot Human Approval — 2026-09-04

## Status

The exact Eiffel / Polish multishot artifact previously recorded in `V4_MULTISHOT_EXACT_MEDIA_RENDER_PROOF_20260904.md` is now `human_approved`.

Exact artifact:

`/opt/ai-short-form-v4-runs/cross-topic-20260903/eiffel-pl/multishot-v2/remotion-runtime/out/eiffel-multishot-v2.mp4`

Machine identity:

- SHA256 `068d43143e9db5d58370fd17300d4b169e2e32407bdda1b85ec1a637587349c3`;
- duration `27.414 s`;
- H.264 `1080x1920`;
- AAC `48 kHz` stereo.

## Human verdict

After watching the exact artifact, the user explicitly said: `мне нравится`.

This is the first V4 artifact promoted from `machine_rendered` to `human_approved`.

## What this proves

The following combination has now received product-level human acceptance on one exact-media/history topic:

- semantic scenes independent of Whisper segmentation;
- internal `shots[]` inside semantic scenes;
- shot timing from exact-audio Whisper word alignment;
- shot-level hash-verified exact media;
- no generic factual fallback stock;
- no standalone text-card replacement frames;
- portrait/fullscreen treatment only when appropriate, landscape evidence via contain;
- one continuous voice track and exact-audio caption timing;
- unified `VerticalShort` renderer.

## What this does NOT prove

One accepted topic is not enough to authorize orchestration or production deployment.

Permanent cross-topic rule still applies. The same architecture must obtain human approval on materially different classes such as:

1. clothing zipper mechanism / Russian;
2. OLED vs LCD / English or another comparison/mechanism topic.

No n8n/PostgreSQL rebuild is authorized yet.
