# Current Project State — Semantic Visual Rebuild

Last updated: 2026-09-03

This file is authoritative for the active semantic visual rebuild on GitHub branch `rebuild/semantic-visual-segments`. Repository/runtime state overrides chat memory. Detailed chronological proof is in `docs/ENGINEERING_HISTORY.md`.

## Mandatory protocol

Before EVERY technical response, diagnosis, recommendation, code/config change, deployment, or test:

1. Read `docs/PERMANENT_PROJECT_RULES.md` from GitHub.
2. Read this file fresh from GitHub branch `rebuild/semantic-visual-segments`.
3. Before starting a new approach, read `docs/ENGINEERING_HISTORY.md` so rejected/broken approaches are not repeated.
4. Architecture change: also read `docs/ARCHITECTURE.md` and `docs/VISUAL_SEGMENTATION_DESIGN.md`.
5. Milestone/acceptance/gate change: also read `docs/ROADMAP.md` and `docs/PROCESS_GATE.md`.
6. Upstream/provider change: also read `docs/UPSTREAM_DECISION.md`.
7. Inspect fresh VPS/runtime state before acting.

## Hard invariants

- exactly three persistent project services: `n8n`, `postgres`, `media-worker`;
- external API cost per generated video: `0 PLN`;
- no Gemini or other quota-limited hosted semantic AI in the required critical path;
- no general local generative LLM in the required critical path;
- no quota waits/retries, extra keys/accounts, paid fallback, topic-specific patches, acceptance bypasses, threshold weakening, or repeated fitting TTS;
- automatic production performs exactly ONE Edge synthesis per job;
- meaningful failures, root causes, rejected approaches, changes, tests, deploys and rollbacks are recorded in GitHub before moving past them.

Semantic-v3 critical path:

`topic -> factual evidence -> deterministic evidence-backed narration -> local duration preflight -> exactly one natural Edge voice -> timed beats -> deterministic semantic visual segments -> truthful media eligibility -> local SigLIP ranking + perceptual identity -> global visual-shot assignment -> pre-render visual gate -> independent subtitle/visual timelines -> render-v3 -> post-render visual-state gate -> human review`

## Runtime — current verified state

Production: `/opt/ai-short-form-content-factory`

Local rebuild worktree: `/opt/ai-short-form-content-factory-rebuild`

Local rebuild branch: `rebuild/semantic-visual-segments-local`

Local rebuild HEAD:

`2405d0431ff2007b52825b273267d07fad9f68ce` — `redesign: separate semantic visual segments from timed beats`

Current verified rebuild state:

- worktree clean;
- n8n `/healthz` returns OK;
- media-worker `/health` returns OK on bound port `3001`;
- media-worker reports local `Xenova/siglip-base-patch16-224`, dtype `q4`, and one preview fetch attempt;
- production has not been changed by the GitHub synchronization work.

## Production deployment boundary

Semantic-v3 is **NOT deployed yet**.

Current production still uses:

- WF02 `TJfA4ZYUEKSTad6k` — multilingual deterministic factual retrieval + evidence-backed narration;
- WF03 `UHxvCZNqaLb1RKMM` — exactly one natural Edge voice + timed beats;
- WF04 `M6VisualSourcing1` — currently published old `visual-quality-v2` path;
- WF05 `M7VideoRender1` — currently published old `visual-quality-v2` render path;
- WF06 `R8ReviewApi1` — review API.

Live production migrations relevant to the current boundary:

- `013_visual_quality_gate.sql` — live;
- `014_reference_media_kind_lifecycle.sql` — live;
- `015_visual_segments.sql` — **not live yet**.

Production semantic-v3 media-worker has not been deployed and semantic-v3 WF04/WF05 have not been published.

Therefore no fresh M8 production job may be started yet. Deployment gates and rollback proof come first.

## Existing deployed facts retained

Visual-quality-v2 production rewrite:

- commit `f7c4096503c9620910b387129a5a06cce4d26d42`;
- rollback `/opt/ai-short-form-content-factory/rollback/20260902T175543Z-pre-visual-quality-v2`.

Reference-media lifecycle fix:

- commit `b83bf6d48f1df259c7c6fa0136748ca10d13f1af`;
- rollback `/opt/ai-short-form-content-factory/rollback/20260902T181813Z-pre-reference-media-kind-lifecycle`.

WF02 multilingual factual retrieval:

- commit `e4e856093fa237dab9daaa56dcf443c3b6155f93`;
- rollback `/opt/ai-short-form-content-factory/rollback/20260903T055250Z-pre-wf02-multilingual`;
- live WF02 core SHA-256 `0f5893ffba59b23d181c363b26b991450e3fc016a52016e1ec686797dbfe23c1`;
- bounded probe languages EN/PL/RU/UK;
- one Wikipedia request per probe, no retry loop;
- official language link required for cross-language handoff;
- extractive/provenance-preserving narration compiler;
- unchanged final measured duration gate.

## Why semantic-v3 exists

Fresh production job `4372be34-c417-415f-92f6-63481b3b5686`, topic `как работает индукционная плита`, output `uk`, target `60`, passed corrected WF02 and exactly one Edge synthesis but old WF04 failed with `perceptually unique truth-eligible assignment 11/12`.

Verified root cause: timed narration/subtitle beats are transport units and must not automatically become independent semantic media-search obligations.

Systemic correction:

`accepted voice -> timed beats -> deterministic semantic visual segments -> visual shots -> truth eligibility -> local SigLIP -> perceptual sequence gate -> independent visual timeline -> render-v3 -> post-render frame-state gate -> human review`

Never return to `timed beat = independent visual obligation` without new verified evidence.

## Semantic-v3 contract

### Segmentation

- segment boundaries occur only on existing timed-beat boundaries;
- a semantic segment is one visual obligation by default;
- elapsed time alone never creates extra shots;
- no fixed `5 seconds = new visual` rule;
- quality-constrained maximum:

`effective_max_segment_seconds = min(8.5, accepted_voice_duration * 0.34)`;

- if one timed beat itself exceeds the effective cap, fail closed rather than splitting it only to satisfy visuals;
- additional shots may exist only for a deterministic semantic/representation transition;
- same-duration content may produce different segment counts.

### Visual quality

Asset file uniqueness is not a product-visible diversity gate.

Authoritative constraints are perceptual/rendered state constraints:

- no adjacent duplicate perceptual cluster;
- max cluster occurrence = `2`;
- max cluster duration share = `0.34`;
- required rendered state count is derived from shot count and max occurrence;
- post-render midpoint frames are checked independently;
- missing/non-finite quality metrics fail closed;
- no threshold weakening.

### Durable semantic visual entities

Migration `db/migrations/015_visual_segments.sql` adds:

- `visual_segments`;
- `visual_shots`;
- `media_library_assets`.

WF05/render-v3 consumes independent timelines:

- timed beats for subtitle timing;
- visual shots for visual timing.

Both timelines must cover the same accepted continuous voice track.

## Semantic-v3 implementation synchronization

Local semantic implementation is the clean `2405d04` commit.

GitHub branch `rebuild/semantic-visual-segments` now contains the full semantic-v3 implementation/migration/test set while preserving the remote documentation history. No force push or destructive history rewrite was used.

Material sync commits include:

- `62fef92819b6093ec0f876e112ff44752feb9f8e` — semantic visual quality evaluator;
- `c62fd62591db6c9594066fb82881da049437a7ce` — semantic-v3 WF05;
- `bc1f6515eab5fc449af5b4ef6500530caca52232` — semantic-v3 WF04;
- `602ab214035a051e41a47394d0b0db31b6e5cc1e` — semantic-v3 media-worker server;
- architecture aligned in `b71ce862a606b1010625912c4ba07b8f600d8b56`.

Cross-check against local `2405d04`:

- 16/17 semantic-v3 files have exact Git blob equality;
- `services/media-worker/src/server.mjs` differs only by the final EOF newline;
- appending one LF to the remote bytes produces the exact local Git blob `a07fb3396602a0923fa081c022cd3739f6076caf`;
- `diff -u` reports no source-code difference beyond `No newline at end of file`.

Treat this as newline normalization, not semantic code divergence.

## Existing semantic-v3 proof on exact local implementation

Focused/static suite PASS includes:

- semantic segmentation regression;
- visual-shot quality regression;
- WF05 visual-segments-v3 contract;
- visual discovery compatibility;
- legacy visual-quality-v2 regression;
- WF04 Code-node runtime-v3;
- WF04 global assignment-v3;
- WF04 perceptual assignment-v3;
- WF04 download/store expansion-v3;
- rank-query contract at 200 chars;
- representation relevance/truth eligibility;
- Code-node compile `41` PASS on Node v24.18.0;
- Studio inline JS compile;
- Code-node mode regression.

Real-provider read-only semantic-v3 PASS cases:

1. zipper `227c8a50-ef1a-49e5-8d26-fdb40f663c83`: `15.480 s`, six beats -> five segments/shots, clusters 5/required 3, adjacent 0, max occurrence 1, max share `0.2958`, Pexels + Wikimedia, provider errors 0;
2. EN induction `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`: `13.944 s`, six beats -> four segments/shots, clusters 4/required 2, adjacent 0, max occurrence 1, max share `0.3374`, Wikimedia, provider errors 0;
3. UK induction fixture `4372be34-c417-415f-92f6-63481b3b5686`: `57.216 s`, 18 beats -> 10 segments/shots, clusters 9/required 5, adjacent 0, max occurrence 2, max share `0.245`, Pexels + Pixabay + Wikimedia, provider errors 0.

Disposable render-v3 proof on the exact local implementation PASSed with:

- 24-second accepted audio;
- six subtitle beats;
- four visual shots of exactly 6 seconds each;
- 1080x1920 H.264/yuv420p;
- AAC 48 kHz stereo;
- pre-render states 4/required 2, adjacent 0, max share `0.25`;
- post-render states 4/required 2, adjacent 0, max share `0.25`.

The first synthetic render with perceptually similar flat images correctly returned HTTP 422. That was a valid post-render gate failure and the gate was not weakened.

## M8 Quality Run

Roadmap requires at least 10 materially different videos with human-visible review.

### M8 #1 — zipper — HUMAN PASS

- `How does a zipper work? / en / 15`;
- accepted job `227c8a50-ef1a-49e5-8d26-fdb40f663c83`.

### M8 #2 — induction heating — HUMAN PASS

- `How does induction heating work? / en / 15`;
- accepted job `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`;
- exactly one Edge synthesis;
- measured voice `13.944 s`;
- user watched exact video and accepted it.

Current human-accepted count: `2/10`.

Do not increment this count from a machine-only result.

## Exact next action

Do **not** start another production job yet.

1. Fresh-read mandatory GitHub docs and fresh-inspect runtime.
2. Complete pre-deploy full diff/migration review for exact semantic-v3 implementation; do not rerun already proven tests without a specific reason.
3. Prove migration `015_visual_segments.sql` safely in a disposable environment if that proof is not already durable.
4. Create a bounded rollback snapshot of current live state before any production mutation, including:
   - live WF04 export;
   - live WF05 export;
   - current production media-worker source/image state;
   - DB migration state;
   - hashes/runtime metadata.
5. Apply migration 015.
6. Deploy only intended semantic-v3 media-worker changes.
7. Publish only semantic-v3 WF04 and WF05.
8. Verify live workflow/code equality, exactly three persistent services, n8n HTTP 200, media-worker HTTP 200 and PostgreSQL healthy.
9. Only then create a **completely fresh** production job:
   - topic: `как работает индукционная плита`;
   - output language: `uk`;
   - duration: `60`.
10. Never reuse consumed-Edge jobs `4372be34-c417-415f-92f6-63481b3b5686`, `85fcc63b-b89b-40d0-b253-6383b715f105`, or `e1399581-305b-4341-910e-b9477a04f499`.
11. Require exactly one Edge synthesis, measured duration gate, timed-beat coverage, semantic visual segments, truthful eligibility, SigLIP/perceptual assignment, render-v3 post-render gate, ffprobe and `review_ready`.
12. Give the user the exact fresh video for human review. Do not call PRODUCT PASS or change M8 accepted count until the user watches that exact video and accepts it.

## Resume rule

If chat/context is lost, read fresh `PERMANENT_PROJECT_RULES.md`, this file, `ENGINEERING_HISTORY.md`, `ARCHITECTURE.md` and fresh VPS/runtime before acting.

Current boundary: semantic-v3 implementation is synchronized to GitHub and architecture docs are aligned; semantic-v3 is not deployed; migration 015 is not live; production WF04/WF05/media-worker remain old visual-quality-v2; M8 is `2/10`; next work is pre-deploy proof + rollback snapshot, not another architecture rewrite and not a fresh job yet.