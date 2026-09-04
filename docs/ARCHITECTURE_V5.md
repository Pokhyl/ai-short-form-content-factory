# Architecture V5 — Asset-First Agentic Editor

## Goal

Build an automated short-form editor, not another handcrafted scene-to-image generator.

The V5 codebase is intentionally thin. The production engine is a pinned mature editing toolkit; V5 owns factual policy, free-provider policy, input/output contracts, reproducibility and human acceptance state.

## Critical path

1. `JobSpec`: topic, language, target duration.
2. `Research`: gather factual sources and claims.
3. `VisualInventory`: search actual available free/licensed video/image/evidence sources before the final script is frozen.
4. `StoryEditor`: choose a factual angle that can be shown with that inventory; reject unshowable claims/angles rather than invent media.
5. `Script`: write natural speech around the chosen evidence-backed/showable angle.
6. `Voice`: one continuous narration.
7. `Alignment`: faster-whisper word timestamps from that exact voice file.
8. `EditPlan`: a real NLE-style plan referencing concrete assets: source in/out, duration, crop/reframe, transitions, overlays, motion ops, caption/audio decisions.
9. `Editor`: OpenNolan/FFmpeg editing primitives execute the plan. No V5 custom renderer.
10. `QA`: ffprobe/decode/black-frame/caption/audio checks plus contact-sheet/frame sampling.
11. `HumanReview`: exact MP4 is the only product acceptance artifact.

## Upstream engine

Pinned initial upstream: `het8802/OpenNolan` commit `4457349c386ea1a89c01547f9a76fa650970c131` (`v1.0.2`).

V5 initially uses the upstream FFmpeg/tooling path because it is present in the pinned source and does not require Node. The current pinned checkout references a `remotion-composer` in documentation, but that directory is not present at this exact commit. V5 therefore does not claim Remotion readiness and does not fabricate that missing runtime.

Relevant upstream capabilities already present at the pin include:

- provider-agnostic `DirectClipSearch`;
- stock adapters including Wikimedia Commons, Archive.org, NASA, Pexels/Pixabay when configured, and others;
- source metadata/provenance in provider candidates;
- `Transcriber` with faster-whisper word timestamps;
- `VideoCompose` and FFmpeg composition/editing paths;
- motion/cut/reframe/overlay/audio tool families;
- agent-oriented pipeline manifests such as `instagram-reels-studio` and retrieval-first `documentary-montage`.

## What V5 does not contain

- no semantic-v3 reuse;
- no V4 scene/shot schema reuse;
- no `VerticalShort`/`SequenceShort` reuse;
- no custom Remotion composition as the default product core;
- no one-asset-per-shot abstraction;
- no fixed shot-count target as a quality gate;
- no post-script invented exact-media obligation;
- no automatic machine promotion to HUMAN PASS.

## Provider order

Provider choice is an inventory concern, not a fallback ladder that may silently insert irrelevant footage.

For a factual visual need, V5 records all considered real candidates and the exact chosen asset. If inventory is weak, `StoryEditor` may change the angle before script freeze. After script freeze, factual meaning cannot be silently changed merely to fill a visual slot.

## Initial runtime

- upstream checkout: `/opt/ai-short-form-v5-upstreams/OpenNolan`;
- V5 environment: `/opt/ai-short-form-v5-runtime/.venv`;
- FFmpeg: host package;
- speech draft/baseline: Edge TTS;
- alignment: faster-whisper CPU int8;
- existing self-hosted SearXNG remains available for factual research;
- old `ai-short-form-v4-selftest.service` is stopped.
