# V4 Upstream Renderer Evaluation — 2026-09-03

This document records the renderer evaluation performed after the first custom V4 compositor received HUMAN FAIL.

## Boundary

Production semantic-v3 remained frozen. No new production jobs were created. The existing V4 voice track was reused; no additional Edge synthesis was consumed for renderer comparisons.

## MoneyPrinterTurbo — useful components, rejected as V4 renderer

A clean upstream render attempt was run against pinned MoneyPrinterTurbo `cbbb366393105d5cefc254dc9ed492d43da0711b` / v1.3.6.

Findings:

- upstream correctly rejected two low-resolution source images instead of stretching them;
- after replacing those sources with higher-resolution exact Wikimedia assets, `preprocess_video()` created the expected normalized image clips;
- the render path was extremely slow on the 2-vCPU VPS because MoviePy/FFmpeg re-encoded each still/clip frame-by-frame;
- during a clean `combine_videos()` attempt, the upstream concat stage failed because `temp-clip-1.mp4` was no longer present when the concat demuxer opened the list;
- no custom concat workaround was accepted, because the purpose of the test was to prove the upstream renderer itself.

Decision: retain MPT only as a reference/reusable component source for TTS/Whisper/material contracts where independently useful. Do not use MPT as the V4 presentation/render engine.

## Short Video Maker — rejected as full pipeline

The architecture was reviewed before deployment. It is not a suitable complete foundation for this product because its normal path is English/Kokoro + Pexels and it contains generic fallback/joker footage behavior. That can reproduce the same class of semantic failure already observed in semantic-v3.

Decision: its Remotion patterns may be referenced, but the complete pipeline is not adopted.

## OpenMontage — upstream Remotion renderer prototype

Upstream: `calesthio/OpenMontage`, checked out at commit `cd9f3c1f03368be87b140af494914b8ee4e3c7a4`.

License: AGPL-3.0. Therefore this run is an evaluation/reference prototype only. No OpenMontage code has been copied into the product repository. License compatibility must be resolved before any code adoption.

Why it was evaluated:

- explicit scene plan and multiple representation/component types;
- native Remotion composition;
- normal image/video scenes plus diagram/screenshot/card/chart components;
- word-level caption overlay;
- no need to invent another Python compositor.

### Exact input

The existing speech-ready Ukrainian voice track from the V4 induction prototype was reused:

- voice: `uk-UA-OstapNeural`;
- duration: `31.968 s`;
- no new synthesis.

Faster-whisper produced 68 word timestamps. The speech-ready script also contained exactly 68 words, so recognition spellings were replaced one-for-one with the known script words while every original timestamp was preserved.

Five exact scene assets were used. Normal photographic scenes use upstream `ImageScene`; wide technical diagrams use upstream `ScreenshotScene` contain-layout rather than being forced through a crop/stretch path.

OpenMontage renderer code was not modified. The renderer received only props/assets/audio/captions.

### Render result

Artifact:

`/opt/ai-short-form-v4-upstreams/OpenMontage/remotion-composer/out/v4-induction.mp4`

Machine proof:

- SHA256 `d9b1670b6f5818036a88486582c76b5b70fe51f9b26d9e0c6a1bead638d051dc`;
- size `12,233,895` bytes;
- duration `33.046 s`;
- H.264, 1080x1920;
- AAC, 48 kHz, stereo.

### Visual inspection before user delivery

Five control frames were extracted at approximately 2 / 6 / 14 / 21 / 27 seconds and inspected as a contact sheet before sharing the MP4.

The obvious defects from the failed custom compositor are absent:

- no stretched/warped source images;
- induction coil is visibly represented;
- wide technical diagrams are contained and remain visible rather than being cropped to a narrow slice;
- thermography is visible;
- captions are a bounded bottom overlay rather than giant full-frame subtitle boxes.

This is still only `machine_rendered` / pre-human-review. It must not be counted as HUMAN PASS until the user watches this exact artifact and accepts it.

## Infrastructure findings

The upstream experiments temporarily filled the 38 GB VPS filesystem. Investigation showed multiple unused Docker image layers and disposable prototype/upstream data. Only unused Docker images and disposable V4 experiment data were removed; running production containers were not touched. Filesystem free space recovered to approximately 4.6 GB before the OpenMontage render.

## Current decision boundary

- semantic-v3 remains frozen;
- custom V4 Python compositor remains retired;
- MPT is not the renderer;
- Short Video Maker is not the complete pipeline;
- OpenMontage renderer output is the current human-review candidate, with AGPL adoption unresolved;
- M8 remains `2/10` until explicit human acceptance.