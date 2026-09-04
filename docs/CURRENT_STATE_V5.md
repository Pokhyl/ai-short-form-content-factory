# Current State — V5 Agentic Editor

Last updated: 2026-09-04

Branch: `rebuild/agentic-editor-v5`.

## Status

V4 product/runtime is frozen and the old V4 Studio self-test service is stopped.

V5 is **not** considered a chosen production architecture yet. The project is currently in an engine bake-off stage so that no more months are spent building around an unproven editor.

No V5/bake-off video is `human_approved` yet. Do not call V5 working or production-ready.

## Completed rebuild foundation

- preserved the final V4 rejection/failure evidence before branching;
- created `rebuild/agentic-editor-v5`;
- stopped `ai-short-form-v4-selftest.service`;
- isolated V5 from V4 product code with a hard import guard;
- pinned OpenNolan commit `4457349c386ea1a89c01547f9a76fa650970c131` for toolkit evaluation;
- installed host FFmpeg, faster-whisper and Edge TTS;
- verified active free-media inventory from Pexels, Pixabay Video, Wikimedia and Archive.org;
- proved that static provider availability is insufficient: Coverr reported available but active calls returned HTTP `401`;
- removed obsolete bulky V4 rendering/runtime material after preserving failure history.

## Architecture hypothesis under test

If an engine survives the bake-off, the intended product order remains:

`topic -> research -> actual visual inventory -> showable story angle -> script -> continuous voice -> exact-audio word timing -> concrete edit plan -> proven editor engine -> QA -> exact-artifact human review`

Final script freeze must occur after visual inventory discovery, not before it.

This remains a hypothesis until a real engine produces cross-topic HUMAN PASS artifacts.

## Engine bake-off — active

Durable proof: `docs/V5_ENGINE_BAKEOFF_20260904.md`.

Static screening so far:

- ShortGPT: rejected before render; older 2025 path and image/Pexels/MoviePy approach is a weaker fit than current candidates;
- AutoShorts AI (`sa-ro/AI-Youtube-Shorts-Generator`): rejected before promotion because its normal path generates TTS separately per scene, violating the continuous-narration contract;
- MoneyPrinterTurbo: first executable candidate; exact vertical MP4 produced on the VPS.

MoneyPrinterTurbo proof #1:

- topic: `Как работает автомобильный турбокомпрессор`;
- review copy: `/opt/ai-short-form-content-factory/studio/bakeoff/mpt-turbo-ru-15.mp4`;
- SHA256 `1038a41c68f397d8dd80217272fef9c9cf2c52ea2bfd0a8bdc0d4ce2340ec844`;
- H.264 1080x1920 + AAC;
- duration `16.566667 s`;
- state: `machine_rendered` only.

This first proof intentionally isolated editing quality by feeding a deterministic automatically acquired Pexels clip set. It does not yet prove the candidate's autonomous media ranking.

## Immediate gate

1. user watches the exact MoneyPrinterTurbo artifact;
2. if HUMAN FAIL, record the visible general defect and reject/demote MoneyPrinterTurbo rather than integrating or patching it;
3. only if its editing language is acceptable, run unrelated autonomous-sourcing proofs;
4. no new Studio/n8n/PostgreSQL product rebuild until an engine survives multiple materially different HUMAN reviews.
