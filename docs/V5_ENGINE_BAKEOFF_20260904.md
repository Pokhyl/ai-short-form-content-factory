# V5 engine bake-off — 2026-09-04

## Purpose

Stop building architecture around an unproven engine. Candidate engines are screened first, and only engines that produce watchable exact MP4 artifacts on unrelated topics may become the production core.

This is not a V5 product acceptance document. `machine_rendered` is not `human_approved`.

## Bake-off rules

- short vertical 9:16 output;
- free-required production path;
- real moving footage, not one still per semantic scene;
- no topic-specific media IDs or acceptance bypasses;
- continuous narration requirement remains mandatory for the eventual product;
- exact MP4 must be watched before quality judgment;
- weak architectural fits are rejected at static inspection instead of consuming days of integration work.

## Candidate screening

### ShortGPT — rejected at static gate

Checkout used for inspection:

- repository: `RayVentura/ShortGPT`;
- commit: `3df4e0f7a422bf7386565d498bf4521a2544c614`;
- last commit observed: 2025-02-10.

Reason for rejection: the inspected short-form path is based on Bing image search/Pexels plus MoviePy and is materially older than the other candidates. It does not justify spending a render cycle before stronger current candidates.

### AutoShorts AI — rejected at static gate

Checkout used for inspection:

- repository: `sa-ro/AI-Youtube-Shorts-Generator`;
- commit: `2d6f057d49dc33103fe4f5fd8ed53f279fe675e0`;
- last commit observed: 2026-08-01.

Positive: current, FFmpeg-based, Pexels footage, Edge TTS, two video clips per scene.

Hard mismatch: `AudioEngine.process_script()` generates a separate TTS file for every scene. That violates the permanent continuous-narration contract. The project is therefore not promoted as the production core without first proving a native continuous-audio path; no patch is added just to force this fixture through.

### MoneyPrinterTurbo — first executable candidate

Checkout:

- repository: `harry0703/MoneyPrinterTurbo`;
- commit: `9f0b28f8e87db76feee2d49ad3d98a31b43a9532`.

The current CLI supports prepared scripts, local or Pexels/Pixabay media, 9:16 output, Edge TTS, subtitles, clip-duration control, transitions and full MP4 generation.

## MoneyPrinterTurbo editing proof #1

Topic:

`Как работает автомобильный турбокомпрессор`

For this first engine-isolation proof, the media set was acquired automatically from Pexels by four deterministic broad queries, taking the first unique candidate from each query. No hand-picked provider IDs were placed in source code or acceptance logic.

Selected runtime inputs:

- `turbocharger engine` -> Pexels `4101696`;
- `turbocharger turbine` -> Pexels `7568444`;
- `car engine turbo` -> Pexels `4101729`;
- `engine air intake` -> Pexels `4101731`.

All four carry the Pexels free license in the acquisition manifest.

MoneyPrinterTurbo settings:

- local deterministic media set;
- `9:16`;
- cover fit;
- sequential edit;
- fade transition;
- source clip cap `3 s`;
- Russian Edge TTS voice `ru-RU-DmitryNeural`;
- no background music;
- burned subtitles.

Exact artifact:

`/opt/ai-short-form-bakeoff/MoneyPrinterTurbo/storage/tasks/1f988026-bb6c-4347-8882-54f41ca95d47/final-1.mp4`

Published review copy:

`/opt/ai-short-form-content-factory/studio/bakeoff/mpt-turbo-ru-15.mp4`

Machine identity:

- SHA256 `1038a41c68f397d8dd80217272fef9c9cf2c52ea2bfd0a8bdc0d4ce2340ec844`;
- size `8,967,900` bytes;
- duration `16.566667 s`;
- H.264 `1080x1920`;
- AAC audio.

Acceptance state: `machine_rendered`.

## What this proves

It proves that MoneyPrinterTurbo can execute a complete vertical video edit with continuous voice, real video clips, subtitles and transitions on the VPS.

It does **not** prove autonomous topic-to-good-video quality, because the first proof deliberately isolated the editing engine by supplying a deterministic automatically acquired clip set. It also does not prove that its own search-term generation or provider ranking produces relevant footage.

## Next gate

1. user watches the exact MoneyPrinterTurbo proof artifact;
2. HUMAN FAIL -> record the visible general defect and reject/demote the engine rather than architecting around it;
3. only if the editing language is acceptable, run the same candidate on unrelated topics with autonomous media sourcing;
4. no Studio/n8n rebuild until an engine survives cross-topic HUMAN review.
