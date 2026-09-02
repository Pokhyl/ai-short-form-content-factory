# Current Project State — Rebuild

Last updated: 2026-09-02

This file is authoritative for branch `rebuild/simple-pipeline`. Repository/runtime state overrides chat memory.

## Mandatory protocol

Before EVERY technical response, diagnosis, recommendation, code/config change, deployment, or test:

1. Read `docs/PERMANENT_PROJECT_RULES.md` from GitHub.
2. Read this file from GitHub branch `rebuild/simple-pipeline`.
3. Architecture change: also read `docs/ARCHITECTURE.md`.
4. Milestone/acceptance/gate change: also read `docs/ROADMAP.md` and `docs/PROCESS_GATE.md`.
5. Upstream/provider change: also read `docs/UPSTREAM_DECISION.md`.
6. Then inspect fresh VPS/runtime state before acting.

## Hard invariants

- exactly three persistent services: `n8n`, `postgres`, `media-worker`;
- external API cost per generated video: `0 PLN`;
- no Gemini or other quota-limited hosted semantic AI in the required critical path;
- no general local generative LLM in the required critical path;
- no quota waits/retries, extra keys/accounts, paid fallback, topic-specific patches, acceptance bypasses, threshold weakening, or repeated fitting TTS;
- automatic production performs exactly ONE Edge synthesis per job.

Critical path:

`topic -> factual evidence -> deterministic evidence-backed narration -> local duration preflight -> one natural Edge voice -> timed beats -> deterministic truthful visual eligibility -> local SigLIP ranking -> render -> human review`

## Production state

Production migration `db/migrations/012_staged_semantic_pipeline.sql` is applied and preserves legacy `scene_v1`, `beat_v2`, and new `staged_v1` rows.

Published staged workflows:

- WF02 `TJfA4ZYUEKSTad6k` — deterministic evidence/narration;
- WF03 `UHxvCZNqaLb1RKMM` — one natural Edge voice + timed beats;
- WF04 `M6VisualSourcing1` — deterministic visual sourcing;
- WF05 `M7VideoRender1` — render.

Exactly three project services are healthy after the latest bounded deploy.

Latest rollback snapshot:

`/opt/ai-short-form-content-factory/rollback/20260902T135709Z-pre-wf04-assignment`

## Latest systemic visual fixes

Key commits:

- `0f4723a` — dedupe selected visual downloads by `candidate_id` and reuse one stored local asset for multiple truthful scene targets;
- `f7c321a` — preserve alternative factual branches, preserve animated GIFs as video, remove hidden preview retry loop, use bounded preview cache;
- `954b383` — constrained deterministic visual assignment.

`954b383` replaces scene-order greedy selection with deterministic maximum bipartite matching over already metadata-eligible/ranked candidates. It prioritizes constrained beats and maximizes unique truthful assets. Reuse occurs only when a unique assignment cannot cover every beat.

Proof before production deploy:

- `WF04_ASSIGNMENT_PASS`;
- cross-topic constrained-assignment regression PASS;
- all edited WF04 Code nodes compile under production Node 24;
- real CASE1 planner runtime PASS: 6 plans from 17 canonical Zipper media;
- real download-dedupe regression PASS.

Production live WF04 export after deploy contains `eligible_siglip_max_unique_matching` and the augmenting-path matcher. Media-worker health reports one preview fetch attempt plus bounded cache; no retry loop.

## Fresh frozen CASE1 — current result

Frozen CASE1:

`How does a zipper work? / en / 15`

Fresh job on the unchanged post-deploy runtime:

`227c8a50-ef1a-49e5-8d26-fdb40f663c83`

Database state:

- `status = review_ready`;
- `current_stage = review`;
- `last_error = null`;
- final video: `jobs/227c8a50-ef1a-49e5-8d26-fdb40f663c83/render/final.mp4`.

Narration:

`A zipper consists of a slider mounted on two rows of metal or plastic teeth. The slider, operated by hand, contains a Y-shaped channel that meshes or separates them. The teeth may be individually discrete or shaped from a continuous coil.`

Evidence/provenance PASS:

- `W1:P3:S1` supports zipper/slider/two rows of metal or plastic teeth;
- `W1:P3:S2` supports the Y-shaped slider channel that meshes/separates teeth;
- `W1:P3:S3` supports individually discrete teeth versus a continuous coil;
- final narration segments persist exact evidence IDs/source spans.

Duration/voice PASS:

- duration V2 prediction: `15.033 s`;
- conservative interval: `13.644–16.422 s`;
- unchanged measured target gate: `13.5–16.5 s`;
- fresh measured Edge voice: `15.480 s`;
- fixed voice: `en-US-AndrewNeural`;
- WF03 execution `9690` contains exactly one `Generate Natural Voiceover` run;
- fallback voice node did not execute;
- timed beats cover exactly `0.000–15.480 s`.

Visual/provenance PASS:

1. structure -> `File:Reissverschluss Teile 2 (fcm).jpg` component diagram;
2. metal/plastic teeth -> `File:Plastic watertight drysuit zipper closed teeth detail P8110024.jpg`, required anchor `teeth`;
3. slider -> `File:Zipper Pullers.jpg`, required anchor `slider`;
4. Y-channel/meshing mechanism -> `File:Zipper animated.gif`, stored as `scene-04.mp4` with `stored_media_type=video`;
5. individually discrete teeth -> the truthful closed-teeth detail asset, with `excluded_metadata_anchors=["coil"]`;
6. continuous coil -> `File:Coil plastic and metal zippers.jpg`, required anchor `coil`.

The closed-teeth asset is reused locally for scenes 2 and 5; `shared_download_target_count=2`. It is not downloaded twice. The continuous-coil beat no longer receives the historical unsupported drysuit substitution.

Render/ffprobe PASS:

- H.264 High;
- `1080x1920`;
- `yuv420p`;
- `30 fps`;
- AAC LC;
- `48 kHz` stereo;
- audio duration `15.480 s`;
- container/video duration about `15.534 s` due to 30 fps frame quantization;
- final MP4 exists in the production media volume.

## Acceptance status

All machine-verifiable frozen CASE1 gates currently PASS on one unchanged fresh runtime:

- persisted evidence/provenance;
- factual deterministic narration;
- pre-TTS duration gate;
- exactly one Edge synthesis path;
- measured duration;
- exact timed-beat coverage;
- visual eligibility/provenance/content constraints;
- duplicate-download reuse;
- animated mechanism representation;
- render and ffprobe.

The only remaining frozen CASE1 gate is **human-visible review of this exact fresh job** `227c8a50-ef1a-49e5-8d26-fdb40f663c83` for voice/video quality. A previously viewed older video is a useful quality baseline but is not evidence for this fresh unchanged runtime.

Do not start the next matrix case until that exact fresh video is human-accepted. Do not modify the runtime merely to seek cosmetic improvement before an actual product failure is observed.
