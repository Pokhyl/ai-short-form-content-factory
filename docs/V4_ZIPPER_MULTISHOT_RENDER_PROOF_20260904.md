# V4 Zipper / Russian Multishot Render Proof — 2026-09-04

## Status

This document records the next Product-First V4 cross-topic prototype after the Eiffel / Polish human-approved artifact.

The exact zipper artifact described below is `machine_rendered`, not `human_approved`.

Semantic-v3 production remains frozen. No n8n/DB rebuild is authorized by this proof.

## Topic / language

- topic: `Как работает молния на одежде`
- language: `ru`
- target class: object / mechanism explainer

The existing speech-ready Russian narration and exact generated voice were reused. No new semantic-v3 job and no redundant TTS synthesis were created.

## Architecture exercised

The prototype uses the same V4 path that received HUMAN PASS on Eiffel, but on a materially different mechanism topic:

`semantic script -> 5 semantic scenes -> internal shots[] -> exact-audio Whisper word timing -> shot alignment -> shot-level exact media resolution -> render manifest v2 -> verified render bundle v2 -> VerticalShort render`

Whisper segmentation is not used as scene structure. The zipper fixture has five semantic scenes while ASR produced eight segments, so semantic timing continues to come from script-to-Whisper word alignment.

## Visual plan

- `5` semantic scenes;
- `11` internal shots;
- `11` exact/hash-verified media assignments;
- `0` constructed primary visuals;
- `0` generic factual fallback assets;
- `59` caption items in the final render manifest;
- all renderer visual items use `exact_media`.

The shot set stays on the actual subject: metal zipper, slider, zipper element rows, component photo, macro/open zipper views. Generic fashion-model/lifestyle footage and standalone text-card replacement frames are not part of this render path.

Portrait assets use fullscreen treatment. Landscape exact/close-up assets use contain treatment instead of destructive crop/stretch.

## Exact-audio / caption behavior

Timeline duration from exact-audio alignment: `27.140 s`.

The Russian ASR contains ordinary recognition substitutions. Caption display correction uses the existing V4 rule: exact-audio Whisper timestamps remain authoritative, while speech-ready script text may correct unambiguous display text without fabricating timing.

## Exact rendered artifact

File:

`/opt/ai-short-form-v4-runs/cross-topic-20260903/zipper-ru/multishot-v2/remotion-runtime/out/zipper-multishot-v2.mp4`

Machine proof:

- SHA256 `fe94b639c6822cdd339e4e5cd22927dc60821353dba290c085d45b72aa9c2027`;
- size `59,777,504` bytes;
- ffprobe duration `27.222 s`;
- video H.264 `1080x1920`;
- audio AAC `48 kHz`, stereo.

A contact sheet was extracted from the exact final MP4 for pre-delivery inspection support. This is not human approval.

## Render wrapper note

The Sentinel background wrapper later reported `timeout`, but the actual transient Remotion Docker render container completed with exit code `0`, and the final MP4 was independently verified by file existence, SHA256 and ffprobe. Therefore the wrapper timeout is not classified as a render failure.

No retry/sleep workaround was added.

## Review endpoint

The exact artifact was copied to the temporary read-only review share and the endpoint returned HTTP `200` with the expected `59,777,504` byte content length.

## Acceptance state

Current zipper artifact state:

`machine_rendered`

It must remain NOT `human_approved` until the user watches this exact MP4 and explicitly accepts it.

## Next boundary

1. obtain complete-video human review of this exact zipper artifact;
2. on HUMAN FAIL, record the observed general defect before changing architecture;
3. on HUMAN PASS, mark this exact SHA as `human_approved`;
4. then validate a third materially different class, preferably comparison/technology such as OLED vs LCD / English, before any n8n/PostgreSQL orchestration resumes.
