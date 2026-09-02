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
6. Inspect fresh VPS/runtime state before acting.

## Hard invariants

- exactly three persistent services: `n8n`, `postgres`, `media-worker`;
- external API cost per generated video: `0 PLN`;
- no Gemini or other quota-limited hosted semantic AI in the required critical path;
- no general local generative LLM in the required critical path;
- no quota waits/retries, extra keys/accounts, paid fallback, topic-specific patches, acceptance bypasses, threshold weakening, or repeated fitting TTS;
- automatic production performs exactly ONE Edge synthesis per job.

Critical path:

`topic -> factual evidence -> deterministic evidence-backed narration -> local duration preflight -> one natural Edge voice -> timed beats -> deterministic truthful visual eligibility -> local SigLIP ranking -> render -> human review`

## Runtime and source synchronization

Production:

- `/opt/ai-short-form-content-factory`
- rebuild worktree: `/opt/ai-short-form-content-factory-rebuild`
- exactly three project containers are healthy.

Published workflows:

- WF02 `TJfA4ZYUEKSTad6k` — deterministic evidence/narration;
- WF03 `UHxvCZNqaLb1RKMM` — one natural Edge voice + timed beats;
- WF04 `M6VisualSourcing1` — deterministic visual sourcing;
- WF05 `M7VideoRender1` — render.

Migration `db/migrations/012_staged_semantic_pipeline.sql` is applied in production.

IMPORTANT SOURCE NOTE: the GitHub branch code tree is currently behind the VPS rebuild worktree because the VPS has no GitHub HTTPS credentials and no SSH key. The local rebuild commits listed below are deployed and runtime-proven but are not yet all reachable from the GitHub branch ref. Do not silently assume the GitHub workflow blobs equal production until that synchronization is completed. For code decisions, read this state first and then inspect the fresh VPS rebuild/runtime before changing anything.

Current local rebuild HEAD: `99fc079baf44de28470a47f5e3101b65bd2769ad`.

Relevant local commits:

- `8af7f56` — retained Edge operating bands;
- `3619f11` — require metadata-relevant visual representation before choosing diagram/animation;
- `99fc079` — align WF04 SigLIP rank-query producer contract with media-worker maximum of 200 characters;
- earlier accepted visual fixes remain `0f4723a`, `f7c321a`, `954b383`.

Latest rollback snapshots:

- `/opt/ai-short-form-content-factory/rollback/20260902T143632Z-pre-wf02-duration-band`
- `/opt/ai-short-form-content-factory/rollback/20260902T144337Z-pre-wf04-representation`
- `/opt/ai-short-form-content-factory/rollback/20260902T160102Z-pre-wf04-rank-query-contract`

## CASE1 — zipper — PASS

Frozen CASE1:

`How does a zipper work? / en / 15`

Fresh accepted job:

`227c8a50-ef1a-49e5-8d26-fdb40f663c83`

Machine proof:

- `review_ready`, no error;
- deterministic evidence-backed narration with persisted provenance;
- Edge V2 prediction `15.033 s`;
- exactly one Edge synthesis with `en-US-AndrewNeural`;
- measured voice `15.480 s` inside unchanged `13.5–16.5 s` gate;
- six timed beats cover exactly `0.000–15.480 s`;
- truthful zipper structure/teeth/slider/animation/discrete-teeth/coil visuals;
- duplicate visual download reused locally rather than fetched twice;
- final H.264 High `1080x1920`, yuv420p, 30 fps, AAC LC 48 kHz stereo.

Human gate: PASS. On 2026-09-02 the user viewed the fresh result and explicitly said the video was normal. CASE1 is closed.

## Cross-topic systemic fixes

### Duration preflight

The former language-wide worst-case residual made valid short narration practically impossible. The retained Edge V2 corpus was reconstructed exactly: 150 measured rows (`en=40`, `pl=40`, `ru=30`, `uk=40`). The current JS retained audit gives:

- retained rows: `150`;
- preflight-safe: `40`;
- false-safe: `0`.

Where enough retained evidence exists, use a zero-false-safe operating band; otherwise remain fail-closed on the old conservative residual. Final measured `±10%` acceptance is unchanged. EN15 operating band is `13.5–15.704`.

### Visual representation relevance

Utility SVGs such as generic Wikipedia icons must not force a beat into a diagram lane. Diagram/animation is considered available only when its metadata is relevant to canonical topic/beat/evidence. Otherwise normal photo eligibility is used. Real zipper regression remained unchanged.

### SigLIP rank-query contract

WF04 previously emitted rank queries up to 500 characters while media-worker rejects queries over 200. A real induction beat produced 216 characters and HTTP 400, which later appeared as a misleading `5/6` persistence failure. WF04 now uses the same 200-character contract as media-worker.

Proof:

- `WF04_RANK_QUERY_CONTRACT_PASS 6 200`;
- `WF04_REPRESENTATION_RELEVANCE_PASS`;
- `WF04_ASSIGNMENT_REGRESSION_PASS`;
- `WF04_CODE_COMPILE_PASS 14`;
- the formerly failing real 216-character induction request, truncated by the producer contract to 200, returns HTTP 200 from the live media-worker;
- live key WF04 Code-node bodies match the rebuild worktree exactly by SHA.

## M8 Quality Run — active

Roadmap M8 requires at least 10 materially different videos and review of script, voice, visual relevance, subtitles, and render. Do not return to zipper as the default test topic. Use materially different topics and languages. First real product failure stops progression and is repaired systemically; then rerun a fresh job.

### M8 #1 — zipper

PASS, including human-visible review. Job `227c8a50-ef1a-49e5-8d26-fdb40f663c83`.

### M8 #2 — induction heating

Topic:

`How does induction heating work? / en / 15`

Fresh machine-pass job:

`13f64c50-8dd5-47e4-a88f-1411d258e7c4`

Result:

- `review_ready`, no error;
- narration: `An induction heater consists of an electromagnet and an electronic oscillator. The rapidly alternating magnetic field penetrates the object. The eddy currents flow through the resistance of the material, and heat it by Joule heating.`;
- duration prediction `14.358 s`, safe in EN15 operating band;
- measured voice `13.944 s`, `en-US-AndrewNeural`;
- WF03 execution `9768`: exactly one `Generate Natural Voiceover` run, no fallback;
- six beats cover exactly `0.000–13.944 s`;
- WF02/WF03/WF04/WF05 executions all succeeded;
- six scenes are `visual_ready`;
- final file `jobs/13f64c50-8dd5-47e4-a88f-1411d258e7c4/render/final.mp4`;
- ffprobe: H.264 High, `1080x1920`, yuv420p, 30 fps; AAC LC 48 kHz stereo; audio `13.944 s`, container `14.000 s`.

Human-visible review of this exact induction video is still pending, but M8 progression does not require waiting before generating the next materially different case. Human review must be completed before M8 is closed.

## Immediate next action

Continue M8 on the unchanged runtime with a materially different topic and preferably a different language. Do not rerun zipper or induction unless a regression specifically requires it. Record every fresh job ID and the first real failure, if any, here.