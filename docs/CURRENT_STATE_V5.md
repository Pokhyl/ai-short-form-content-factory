# Current State — V5 Agentic Editor

Last updated: 2026-09-04

Branch: `rebuild/agentic-editor-v5`.

## Status

V4 product/runtime is frozen and the old V4 Studio self-test service is stopped.

V5 is **not** considered a chosen production architecture yet. The project is in engine bake-off so that no more months are spent building around an unproven editor.

No V5/bake-off video is `human_approved` yet. Do not call V5 working or production-ready.

## Architecture hypothesis under test

If an engine survives the bake-off, the intended product order remains:

`topic -> research -> actual visual inventory -> showable story angle -> script -> continuous voice -> exact-audio word timing -> concrete edit plan -> proven editor engine -> QA -> exact-artifact human review`

Final script freeze must occur after visual inventory discovery, not before it.

This remains a hypothesis until a real engine produces cross-topic HUMAN PASS artifacts.

## Engine bake-off — current result

Durable records:

- `docs/V5_ENGINE_BAKEOFF_20260904.md`;
- `docs/V5_ENGINE_BAKEOFF_ROUND2_20260904.md`;
- `docs/V5_MONEYPRINTERTURBO_HUMAN_FAIL_20260904.md`;
- `docs/V5_HYPERFRAMES_QR_PROOF_20260904.md`.

### Rejected / demoted

- ShortGPT — rejected at static gate;
- AutoShorts AI — rejected: per-scene TTS;
- AbdullahNaveed/ai-shorts-generator — rejected as required free baseline because normal script/TTS path depends on OpenAI;
- mzu-2410z/yt-automation — rejected: per-section TTS / one clip per point / incomplete caption path;
- gyoridavid/short-video-maker — rejected: per-scene Kokoro TTS + one Pexels per scene;
- HamzaSbay/AdForge — rejected: per-paragraph aligned TTS and looping source clips;
- MissWangari/Youtube-Shorts-Generator — rejected: per-scene Edge TTS and loop/reuse behavior;
- MoneyPrinterTurbo — **HUMAN FAIL**. Exact volcano proof was ~19.47 s because narration was ~19.44 s and the engine looped already-used clips to fill the timeline. Do not patch or promote it;
- OpenMontage current — useful component/tool reference, but de-prioritized as the direct topic-to-short core.

### Active candidate: llm-video-maker + HyperFrames

Pinned candidate:

- `GoldLegendW80/llm-video-maker` commit `cee12add24317c50f8a9f9de93749089a59d9f99`;
- `hyperframes@0.6.91` exactly.

Independent proof topic:

`Как работает QR-код`

The proof uses:

- one continuous Russian narration;
- exact-audio faster-whisper word timing;
- two unique Pexels portrait clips, each used once;
- no clip loops or repeated source material;
- animated HTML/CSS/GSAP mechanism graphics for the middle section;
- 1080x1920, 30 fps, H.264 + AAC.

Exact review copy:

`/opt/ai-short-form-content-factory/studio/bakeoff/hyperframes-qr-ru-15.mp4`

SHA256:

`c9d69c2ea8ddb4e0598ada4b9c441f99d9ef0021480f72fb5e4ddbe63ac30622`

Duration:

`15.187696 s` (narration itself `15.144 s`; remainder is frame/container overhead, not looping/padding).

HyperFrames runtime inspect: `ok: true`, 0 errors / 0 warnings / 0 info issues. Original Pexels clips were normalized to H.264 30 fps / one-second keyframe intervals after the renderer correctly warned that sparse provider keyframes could freeze seeked frames. Final render has no sparse-keyframe warning.

Acceptance state: `machine_rendered` only.

## Immediate gate

1. user watches the exact HyperFrames QR artifact;
2. HUMAN FAIL -> record the visible general defect and reject/demote HyperFrames rather than building architecture around it;
3. HUMAN PASS -> repeat the same engine on materially different topics/languages before selecting a production core;
4. no new Studio/n8n/PostgreSQL product rebuild until an engine survives multiple materially different HUMAN reviews.
