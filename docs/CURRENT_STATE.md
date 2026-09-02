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

Last verified runtime before the current human-acceptance update:

- exactly `media-worker`, `n8n`, `postgres` running;
- PostgreSQL healthy;
- rebuild HEAD `b83bf6d48f1df259c7c6fa0136748ca10d13f1af`;
- rebuild worktree had only the separate WF02 retrieval work dirty:
  - modified `n8n/workflows/WF02-plan-script-and-scenes.json`;
  - untracked `tests/wf02_fact_search_query_regression.mjs`.

On the acceptance turn, fresh runtime inspection was attempted twice but SentinelX returned `agent_offline` because its hub had restarted. No production mutation was performed while runtime verification was unavailable. Fresh runtime verification is required before the next deploy/test action.

Published workflows at the last verified checkpoint:

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

## M8 Quality Run — active

Roadmap M8 requires at least 10 materially different videos with human-visible review of script, voice, visual relevance, subtitles and render.

### M8 #1 — zipper — PASS

Topic:

`How does a zipper work? / en / 15`

Accepted job:

`227c8a50-ef1a-49e5-8d26-fdb40f663c83`

Machine proof and user-visible review both PASS. Do not reopen CASE1 unless a later systemic change affects its contract.

### M8 #2 — induction heating — PASS

#### Old job — PRODUCT FAIL, permanently invalidated

Old job:

`13f64c50-8dd5-47e4-a88f-1411d258e7c4`

Although it had reached `review_ready`, human inspection showed only two effective visual states. This job is NOT acceptance evidence and must never be reused as a PASS.

#### Intermediate post-rewrite job — terminal schema/workflow failure

Job:

`1afc307d-aaac-4eed-8387-b05e1b6721eb`

WF04 execution `9902` failed because the planner persisted fake `reference_media_kind = mixed` while the DB only accepts actual `diagram|animation|photo` or NULL. The job had already consumed its single Edge synthesis, so it was not retried.

Systemic correction is commit `b83bf6d` + migration 014:

- `visual_planned + technical_reference` keeps `reference_media_kind = NULL` until asset selection;
- `visual_ready + technical_reference` requires actual `photo|diagram|animation`;
- invalid non-null kinds remain rejected.

#### Fresh post-fix induction — MACHINE + HUMAN PASS

Accepted job:

`2c182ff8-ea9f-4ddf-a417-b49f796d23f5`

Topic:

`How does induction heating work? / en / 15`

Machine state/proof:

- `review_ready/review`;
- final path `jobs/2c182ff8-ea9f-4ddf-a417-b49f796d23f5/render/final.mp4`;
- no `last_error`;
- deterministic evidence-backed narration;
- duration preflight predicted `14.358 s`;
- exactly one Edge synthesis in n8n execution `9926` (`Generate Natural Voiceover` runs = 1, success, `executionTimeMs = 1084`);
- voice `en-US-AndrewNeural`;
- measured voice duration `13.944 s` passed the unchanged target-duration gate;
- 6 timed beats;
- 6 selected assets / 6 perceptual clusters, required 5;
- adjacent duplicate clusters 0;
- max cluster-duration share `0.1813`;
- post-render rendered-state count 6, required 5;
- midpoint-frame hashing independently produced six distinct states;
- ffprobe: `14.000000 s`, H.264 1080x1920 yuv420p 30 fps + AAC 48 kHz stereo.

Human gate:

- on 2026-09-02 the user watched the exact fresh video and responded `мне нравится`;
- this is explicit human-visible acceptance of the fresh induction result;
- M8 #2 is therefore PASS.

Current M8 accepted count: `2/10`.

## Separate unfinished WF02 retrieval work — NEXT TECHNICAL TASK

This remains intentionally outside the visual rewrite commits:

- modified `n8n/workflows/WF02-plan-script-and-scenes.json`;
- untracked `tests/wf02_fact_search_query_regression.mjs`.

Originating real failure:

- Polish topic `Dlaczego popcorn pęka podczas podgrzewania?`;
- native Wikipedia full-text retrieval query was too AND-constrained and returned no full-text pages;
- manual evidence showed the shorter subject-leading query returns relevant pages, including Popcorn.

Systemic direction already prepared locally:

- retrieval uses a bounded subject-leading native-Wikipedia query (currently first two meaningful subject tokens);
- the full `fact_search_tokens` remain unchanged for downstream evidence validation;
- no retry, topic mapping, provider fallback, or factual-gate weakening.

This work must remain a separate commit/deploy from the visual rewrite.

## Exact next action

1. Reconnect/fresh-inspect VPS runtime after the SentinelX hub restart; do not mutate production before this check.
2. Inspect the exact WF02 diff and regression, correct any stale/test-only assumptions, and run the relevant WF02/static/staged regressions.
3. If regression proof passes, commit the WF02 retrieval fix separately, create a bounded rollback snapshot, deploy WF02 only, verify live workflow equality/runtime health.
4. Start M8 #3 on a materially different topic/language. The intended regression candidate is Polish `Dlaczego popcorn pęka podczas podgrzewania? / pl / 15` because it previously exposed the real retrieval defect; use a completely fresh job and do not reuse the failed job.
5. Require full machine proof including exactly one Edge synthesis, then human-visible review before counting M8 #3.
6. Continue until at least 10 materially different human-reviewed videos exist; the first real product failure stops progression and is fixed systemically.

## Resume rule

If chat/context is lost, do not infer or restart from memory. Read fresh `PERMANENT_PROJECT_RULES.md`, this file, `ENGINEERING_HISTORY.md`, and fresh VPS/runtime. The project is currently at M8 `2/10` PASS, with the separate WF02 native-Wikipedia retrieval fix as the next technical task before fresh Polish popcorn M8 #3.