# V5 engine bake-off — round 2 — 2026-09-04

## Context

MoneyPrinterTurbo is HUMAN FAIL after the exact volcano artifact: target duration was not respected and the engine looped already-used clips to fill the narration timeline. Do not patch or promote it.

## Additional candidate screening

### gyoridavid/short-video-maker — REJECTED at static gate

Pinned inspection commit: `9bb9a212ced86caa7e09099c382da1a44d638760`.

The current `ShortCreator.createShort()` loop calls Kokoro TTS separately for every input scene, then runs Whisper and chooses one Pexels video for that scene. This violates the project's continuous-narration contract and preserves the same scene-bound architecture that repeatedly failed product review. No render was spent on it.

### HamzaSbay/AdForge — REJECTED at static gate

Pinned inspection commit: `64fb115c6dcf9af70473359c57a88a17578e2e92`.

Positive: current 2026 codebase, 9:16, Pexels/Pixabay sourcing, Gemini/Ollama pluggable LLM, EdgeTTS fallback, Remotion overlays and exact target-duration timeline.

Hard product mismatch: `generate_aligned_voiceover()` synthesizes every timeline paragraph independently and then delay-mixes the clips. Its selector tests explicitly support looping source clips to fill duration. Both conflict with permanent requirements: one continuous narration and no repeated footage merely to fill the clock. No fixture patch was added.

### MissWangari/Youtube-Shorts-Generator — REJECTED at static gate

Pinned inspection commit: `c1b0c84fdd457f74183e4253719597edb580d7ca`.

Although it uses two Pexels clips per scene, its normal audio path generates a separate EdgeTTS file for every scene. The compositor uses `stream_loop=-1`, and media fallback may reuse clip A as clip B. This directly recreates two already rejected failure modes: fragmented narration and repeated visuals.

### OpenMontage current — DE-PRIORITIZED for direct bake-off

Pinned inspection commit: `6a6d456e502df1762aa117135a7f36284f50cbbc`.

OpenMontage is a broad agentic production toolkit, not a narrow topic-to-short executable. Its free path is capable of Pexels/Pixabay + Piper + Remotion/FFmpeg, but its documented zero-key explainer fallback is still-image-heavy. It remains useful as a component/tool reference, but it is not promoted as the next direct product core without a stronger exact short-form proof.

## New executable candidate: GoldLegendW80/llm-video-maker + HyperFrames

Pinned skill repository commit: `cee12add24317c50f8a9f9de93749089a59d9f99`.

Pinned rendering engine required by the skill: `hyperframes@0.6.91`.

Why it survives static screening:

- designed for TikTok/Reels/Shorts 9:16;
- agent-driven storyboard rather than one stock clip per narration scene;
- can combine stock video, images, icons, graphics, code, captures and HTML/GSAP motion in one deterministic composition;
- local Kokoro narration is supported; user-audio mode also allows a single externally generated continuous narration track;
- word-level captions are a full-length overlay rather than scene-local text;
- target duration is an explicit brief contract and final ffprobe validation is required;
- fetched assets are vendored with license metadata;
- no network access is required at render time.

Runtime bring-up on the VPS:

- isolated Node `v22.23.2` installed under `/opt/ai-short-form-bakeoff/hyperframes-runtime/node`;
- `hyperframes@0.6.91` installed in the isolated bake-off host;
- HyperFrames Chrome Headless Shell `131.0.6778.85` downloaded through `hyperframes browser ensure`;
- FFmpeg/FFprobe checks pass;
- current VPS has only about 3.7 GB RAM and low free disk, so memory/disk are environment risks, not acceptance bypasses.

Author-generated reference artifact copied to Studio only for immediate visual-language screening:

`/opt/ai-short-form-content-factory/studio/bakeoff/hyperframes-author-demo-worldcup.mp4`

SHA256: `a7b4f640a873fdd8c3f6d6666f1df87a2010ab0e123e8fde758f577056764d9d`

Duration: `16.821029 s`, H.264 1080x1920 + AAC.

This author demo is NOT our product proof and cannot be marked human-approved for our pipeline. The next required gate is an independently authored topic through the same pinned HyperFrames engine. If that exact artifact is poor, reject the candidate instead of building architecture around it.
