# Current Project State — Rebuild

Last updated: 2026-09-02

This file is authoritative for branch `rebuild/simple-pipeline`. Repository/runtime state overrides chat memory. Detailed chronological proof is in `docs/ENGINEERING_HISTORY.md`.

## Mandatory protocol

Before EVERY technical response, diagnosis, recommendation, code/config change, deployment, or test:

1. Read `docs/PERMANENT_PROJECT_RULES.md` from GitHub.
2. Read this file from GitHub branch `rebuild/simple-pipeline`.
3. Architecture change: also read `docs/ARCHITECTURE.md`.
4. Milestone/acceptance/gate change: also read `docs/ROADMAP.md` and `docs/PROCESS_GATE.md`.
5. Upstream/provider change: also read `docs/UPSTREAM_DECISION.md`.
6. Inspect fresh VPS/runtime state before acting.

Before starting a new approach, also check `docs/ENGINEERING_HISTORY.md` for the same/equivalent failure so rejected approaches are not repeated.

## Hard invariants

- exactly three persistent services: `n8n`, `postgres`, `media-worker`;
- external API cost per generated video: `0 PLN`;
- no Gemini or other quota-limited hosted semantic AI in the required critical path;
- no general local generative LLM in the required critical path;
- no quota waits/retries, extra keys/accounts, paid fallback, topic-specific patches, acceptance bypasses, threshold weakening, or repeated fitting TTS;
- automatic production performs exactly ONE Edge synthesis per job.

Critical path:

`topic -> factual evidence -> deterministic evidence-backed narration -> local duration preflight -> one natural Edge voice -> timed beats -> deterministic truthful visual eligibility -> local SigLIP ranking + perceptual identity -> global sequence assignment -> pre-render visual gate -> render -> post-render visual-state gate -> human review`

## Runtime

Production:

- `/opt/ai-short-form-content-factory`
- rebuild worktree: `/opt/ai-short-form-content-factory-rebuild`

Fresh runtime inspection after the current proof:

- exactly `media-worker`, `n8n`, `postgres` are running;
- PostgreSQL is healthy;
- rebuild HEAD: `b83bf6d48f1df259c7c6fa0136748ca10d13f1af`;
- rebuild worktree has only the separate WF02 retrieval work dirty:
  - modified `n8n/workflows/WF02-plan-script-and-scenes.json`;
  - untracked `tests/wf02_fact_search_query_regression.mjs`.

Published workflows:

- WF02 `TJfA4ZYUEKSTad6k` — deterministic evidence/narration;
- WF03 `UHxvCZNqaLb1RKMM` — one natural Edge voice + timed beats;
- WF04 `M6VisualSourcing1` — visual-quality-v2 sourcing/assignment;
- WF05 `M7VideoRender1` — visual-quality-v2 render acceptance;
- WF06 `R8ReviewApi1` — review API.

IMPORTANT SOURCE NOTE: production/live n8n exports are authoritative for published workflow behavior when the production filesystem export is stale. In particular, the filesystem WF03 export is historical; the live published WF03 was independently exported and contains no Gemini path.

## Deployed visual-quality-v2 implementation

Primary visual rewrite commit:

- `f7c4096503c9620910b387129a5a06cce4d26d42`
- `redesign: enforce perceptual visual diversity`

Reference-media lifecycle correction:

- `b83bf6d48f1df259c7c6fa0136748ca10d13f1af`
- `fix: align reference media kind lifecycle`

Applied migrations:

- `012_staged_semantic_pipeline.sql`;
- `013_visual_quality_gate.sql`;
- `014_reference_media_kind_lifecycle.sql`.

Rollback snapshots:

- `/opt/ai-short-form-content-factory/rollback/20260902T175543Z-pre-visual-quality-v2`;
- `/opt/ai-short-form-content-factory/rollback/20260902T181813Z-pre-reference-media-kind-lifecycle`.

Current visual architecture:

`timed beat + evidence -> deterministic search intents -> multi-source candidate discovery -> metadata/provenance truth eligibility -> local SigLIP ranking + perceptual hash -> global video-level assignment -> durable sequence-quality gate -> persist -> render -> actual midpoint-frame perceptual gate -> review_ready`

Discovery adapters:

- canonical article media;
- Wikimedia Commons full search;
- Pixabay photos when healthy/configured;
- Pexels video only as optional provider.

Pexels is never required for success. No old provider retry cascade, topic mapping, or fallback-generated visual path is allowed.

## Visual-quality-v2 acceptance contract

Truth eligibility is before SigLIP. SigLIP is a relative ranking tool, never the truth oracle.

For a 6-beat job:

- all 6 beats must have persisted truth-eligible selected assets;
- at least 5 perceptually distinct clusters are required;
- adjacent duplicate perceptual clusters are forbidden;
- no perceptual cluster may occupy more than `0.34` of total beat duration;
- all metrics must be finite; missing/NaN values fail closed;
- WF05 independently reloads and validates persisted `visual_quality`;
- post-render midpoint frames are independently clustered from actual rendered pixels;
- rendered state count must also meet the required state count before `review_ready`.

The old failed induction sequence remains the permanent negative fixture: 6 scene rows but only 2 effective visual states, 4 adjacent repeats and about 68% duration share for one state -> MUST FAIL.

Still-image motion is cosmetic only. Motion does not turn reuse of one perceptual visual into diversity. Technical/factual diagrams remain stable/readable.

## CASE1 — zipper — M8 #1 PASS

Topic:

`How does a zipper work? / en / 15`

Accepted job:

`227c8a50-ef1a-49e5-8d26-fdb40f663c83`

Machine proof and user-visible review both PASS. Do not reopen CASE1 unless a later systemic change affects its contract.

## M8 #2 — induction heating

### Old job — PRODUCT FAIL, permanently invalidated

Old job:

`13f64c50-8dd5-47e4-a88f-1411d258e7c4`

Although it had reached `review_ready`, human inspection showed only two effective visual states. This job is NOT an M8 PASS and must never be reused as acceptance evidence.

### Intermediate post-rewrite job — terminal schema/workflow failure

Job:

`1afc307d-aaac-4eed-8387-b05e1b6721eb`

WF04 execution `9902` failed because the new planner persisted fake `reference_media_kind = mixed` while the DB only accepts actual `diagram|animation|photo` or NULL. The job had already consumed its single Edge synthesis, so it was not retried.

Systemic correction is commit `b83bf6d` + migration 014:

- `visual_planned + technical_reference` keeps `reference_media_kind = NULL` until asset selection;
- `visual_ready + technical_reference` requires actual `photo|diagram|animation`;
- invalid non-null kinds remain rejected.

Regression transaction proved planned+NULL PASS, ready+NULL FAIL, ready+photo PASS.

### Fresh post-fix induction — MACHINE PASS, HUMAN REVIEW PENDING

Fresh job:

`2c182ff8-ea9f-4ddf-a417-b49f796d23f5`

Topic:

`How does induction heating work? / en / 15`

Current state:

- `review_ready/review`;
- final path `jobs/2c182ff8-ea9f-4ddf-a417-b49f796d23f5/render/final.mp4`;
- no `last_error`.

Narration/evidence:

`An induction heater consists of an electromagnet and an electronic oscillator. The rapidly alternating magnetic field penetrates the object. The eddy currents flow through the resistance of the material, and heat it by Joule heating.`

- deterministic evidence compiler;
- exact persisted source/evidence support;
- duration preflight predicted `14.358 s` and was safe for the one-shot Edge boundary;
- measured voice duration `13.944 s` passed the unchanged target-duration gate.

Exactly-one-Edge proof:

- live WF03 `UHxvCZNqaLb1RKMM` exported from n8n: active, 15 nodes, no Gemini path;
- one synthesis HTTP node `Generate Natural Voiceover` using the media-worker Edge route;
- request contract includes `max_automatic_synthesis_count: 1`;
- n8n execution `9926` decoded from `execution_data`:
  - `Prepare Continuous Voiceover` runs = 1;
  - `Generate Natural Voiceover` runs = 1, success, `executionTimeMs = 1084`;
  - `Require Natural Voiceover` runs = 1;
- persisted provider `microsoft_edge_readaloud`, model `edge_neural`, voice `en-US-AndrewNeural`.

Visual pre-render proof:

- beat count 6;
- selected assets 6;
- perceptual clusters 6;
- required clusters 5;
- adjacent duplicate clusters 0;
- max cluster-duration share `0.1813`;
- pre-render visual-quality-v2 PASS.

Selected visuals:

1. `File:Induction heating of bar.jpg`;
2. `File:Stirling radioisotope generator head testing.jpg`;
3. `File:Induction heating apparatus 1927.jpg`;
4. `File:Silicon grown by Czochralski process 1956 closeup.jpg`;
5. `File:Northup induction furnace.jpg`;
6. `File:Induction heater.jpg`.

Post-render proof:

- persisted rendered clusters `[[1],[2],[3],[4],[5],[6]]`;
- rendered visual-state count 6;
- required rendered states 5;
- adjacent rendered duplicates 0;
- max cluster-duration share `0.1813`;
- independent midpoint samples at 1.1665, 3.395, 5.721, 8.145, 10.4975 and 12.817 seconds also form six separate perceptual clusters;
- all pairwise midpoint Hamming distances are far above the threshold 18, so the former two-state degeneration did not recur.

ffprobe:

- duration `14.000000 s`;
- H.264, 1080x1920, yuv420p, 30 fps;
- AAC, 48 kHz, stereo;
- size `3,767,544` bytes.

This is a MACHINE PASS only. It is NOT yet M8 #2 PASS until the user watches the exact fresh video and accepts script/voice/visual relevance/subtitles/render.

## M8 current gate

Roadmap M8 requires at least 10 materially different videos with real review of script, voice, visual relevance, subtitles and render.

Current count:

- M8 #1 zipper: PASS including human review;
- M8 #2 induction: machine PASS, human review pending.

Do not generate M8 #3 until the exact fresh induction video `2c182ff8-ea9f-4ddf-a417-b49f796d23f5` has human-visible acceptance.

If the user accepts it, record M8 #2 PASS and continue with materially different topics/languages until at least 10 human-visible reviews exist.

If the user rejects it, stop progression immediately and repair the visible defect systemically. No induction-specific patching and no gate weakening.

## Separate unfinished WF02 retrieval work — DO NOT BUNDLE

This remains intentionally outside the visual rewrite commits:

- modified `n8n/workflows/WF02-plan-script-and-scenes.json`;
- untracked `tests/wf02_fact_search_query_regression.mjs`.

Originating failure was Polish popcorn retrieval where a full native-Wikipedia AND-style query was too restrictive. The local systemic direction uses a bounded subject-leading retrieval query while preserving the full evidence-token set for downstream factual validation.

Do not silently commit/deploy this WF02 work with unrelated M8/visual changes. Handle it separately after the current induction human gate unless a new verified upstream blocker requires it first.

## Exact next action

1. Human-review the exact fresh induction video for job `2c182ff8-ea9f-4ddf-a417-b49f796d23f5` in Studio.
2. If human PASS: record M8 #2 PASS in `CURRENT_STATE.md` and `ENGINEERING_HISTORY.md`, then generate the next materially different M8 topic/language.
3. If human FAIL: record the exact visible product failure and fix the systemic cause before any M8 progression.

## Resume rule

If chat/context is lost, do not infer or restart from memory. Read fresh `PERMANENT_PROJECT_RULES.md`, this file, `ENGINEERING_HISTORY.md`, and fresh VPS/runtime. The project is currently at the human-review gate for fresh induction job `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`.
