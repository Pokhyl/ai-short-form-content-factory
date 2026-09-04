# Current State — V5 Agentic Editor

Last updated: 2026-09-04

Branch: `rebuild/agentic-editor-v5`.

## Status

V5 rebuild has started from a clean product architecture. V4 product/runtime is frozen and the old V4 Studio self-test service is stopped.

No V5 video is `human_approved` yet. Do not call V5 working or production-ready.

## Completed rebuild foundation

- preserved the final V4 rejection/failure evidence in commit `5a38e1e` before branching;
- created `rebuild/agentic-editor-v5`;
- stopped `ai-short-form-v4-selftest.service`;
- cloned current OpenNolan into an isolated upstream checkout;
- pinned OpenNolan commit `4457349c386ea1a89c01547f9a76fa650970c131` (`v1.0.2`, AGPL-3.0);
- created isolated Python environment `/opt/ai-short-form-v5-runtime/.venv`;
- installed OpenNolan core Python requirements;
- installed host FFmpeg `6.1.1` from Ubuntu noble package `7:6.1.1-3ubuntu5`;
- installed `faster-whisper 1.2.1` and `edge-tts 7.2.8` in the V5 environment;
- added a clean V5 pin/preflight/inventory adapter with a hard guard against V4 imports;
- fresh preflight passes with OpenNolan `DirectClipSearch`, `VideoCompose` and `Transcriber` AVAILABLE;
- fresh active inventory probes across mechanism/history/comparison classes returned candidates from Pexels, Pixabay Video, Wikimedia and Archive.org;
- active probe found Coverr returns HTTP `401` despite static availability, so Coverr is excluded from the initial default source set;
- removed frozen V4 Remotion/OpenMontage/tooling runtime bulk after preserving failure history, reclaiming disk for V5.

## Important upstream finding

At the exact pinned OpenNolan commit, README/render-demo text references `remotion-composer`, but that directory is absent from the checkout. Node was also not present on the VPS at V5 start.

Therefore the first direct V5 product proof uses the real upstream FFmpeg editing/tool path. Remotion/HyperFrames are not part of the current acceptance claim.

## Architecture

`topic -> research -> actual visual inventory -> showable story angle -> script -> continuous voice -> exact-audio word timing -> concrete NLE edit plan -> OpenNolan/FFmpeg editing tools -> QA -> exact-artifact human review`

Final script freeze now occurs after visual inventory discovery, not before it.

## Immediate engineering gate

1. build the V5 story/editor controller around actual inventory rather than post-script shot obligations;
2. materialize and frame-sample candidate media through OpenNolan tools before final asset choice;
3. produce direct V5 edits through OpenNolan FFmpeg editing operations, outside Studio/n8n, on unrelated topics;
4. inspect exact artifacts before user review;
5. require cross-topic HUMAN PASS before any new Studio service or orchestration rebuild.
