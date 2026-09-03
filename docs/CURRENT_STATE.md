# Current Project State — Semantic Visual Rebuild

Last updated: 2026-09-03

This file is authoritative for active work on GitHub branch `rebuild/semantic-visual-segments`. Repository/runtime state overrides chat memory. Detailed chronology is in `docs/ENGINEERING_HISTORY.md`.

## Mandatory protocol

Before every technical response, diagnosis, recommendation, code/config change, deployment, or test:

1. read `docs/PERMANENT_PROJECT_RULES.md` fresh from GitHub;
2. read this file fresh from GitHub branch `rebuild/semantic-visual-segments`;
3. read `docs/ENGINEERING_HISTORY.md` before starting a new approach;
4. architecture change: also read `docs/ARCHITECTURE.md` and `docs/VISUAL_SEGMENTATION_DESIGN.md`;
5. milestone/gate change: also read `docs/ROADMAP.md` and `docs/PROCESS_GATE.md`;
6. provider change: also read `docs/UPSTREAM_DECISION.md`;
7. inspect fresh VPS/runtime state before acting.

## Hard invariants

- exactly three persistent project services: `n8n`, `postgres`, `media-worker`;
- external API cost per generated video: `0 PLN`;
- no quota-limited hosted semantic AI or general local generative LLM in the required critical path;
- no quota waits/retries, extra keys/accounts, paid fallback, topic-specific hacks, acceptance bypasses, threshold weakening, or repeated fitting TTS;
- automatic production performs exactly ONE Edge synthesis per job;
- a job whose Edge synthesis was consumed is never retried/reused;
- first real product failure stops M8 progression and is fixed systemically;
- material failures, root causes, changes, tests, deploys and rollbacks are logged in GitHub before moving past them.

## Production architecture

Semantic-v3 critical path:

`topic -> factual evidence -> deterministic evidence-backed narration -> local duration preflight -> exactly one natural Edge voice -> timed beats -> deterministic semantic visual segments -> truthful media eligibility -> local SigLIP + perceptual identity -> global visual-shot assignment -> pre-render gate -> independent subtitle/visual timelines -> render-v3 -> post-render state gate -> human review`

Semantic segment rules:

- boundaries only on existing timed-beat boundaries;
- one visual shot per semantic segment by default;
- no elapsed-time shot multiplication and no fixed 5-second shot rule;
- `effective_max_segment_seconds = min(8.5, accepted_voice_duration * 0.34)`;
- a beat itself is not split only to satisfy visuals; if it exceeds the cap, fail closed;
- additional shot only for deterministic semantic/representation transition.

Visual quality rules:

- asset-file uniqueness is not product-visible diversity;
- adjacent perceptual duplicate count must be 0;
- max cluster occurrence = 2;
- max cluster duration share = 0.34;
- post-render midpoint states are independently checked;
- missing/non-finite metrics fail closed.

## Live production deployment

Production root: `/opt/ai-short-form-content-factory`.

Local rebuild: `/opt/ai-short-form-content-factory-rebuild`, branch `rebuild/semantic-visual-segments-local`.

Current clean local fix HEAD:

`ad657994f910f4d2797688d290bd94a83de96d09` — `fix: align visual shot score schema with selection utility`.

Corresponding latest GitHub code commit:

`3e648b5aa6f7d357e90e8e3284f5642e4c73b4da`.

Semantic-v3 is live:

- migration `015_visual_segments.sql` live;
- `visual_segments`, `visual_shots`, `media_library_assets` live;
- WF02 `TJfA4ZYUEKSTad6k` multilingual deterministic factual path live;
- WF03 `UHxvCZNqaLb1RKMM` exactly-one-Edge + timed beats live;
- WF04 `M6VisualSourcing1` semantic-v3 published;
- WF05 `M7VideoRender1` render-v3 published;
- WF06 `R8ReviewApi1` review API live.

WF04 remains active with `versionId=activeVersionId=12e0857b-3c3c-4640-b7f1-2861050038f1` and canonical behavior SHA `b6b08f21e0fe58b6661f7413e3389834b92c6142f65831a3afcae526a31b53ed`.

WF05 remains active with `versionId=activeVersionId=ae9d00c2-bd65-4d3f-a8f5-ec0bcf840a12` and canonical behavior SHA `c5595719c63eecb2680c10dbe6a63e45bb7bc4f6d12308c3b62f5f2953f9a117`.

## HTTP visual-discovery adapter correction — LIVE

Fresh semantic-v3 production job `cb98ad2b-1aaa-4117-918d-8fef22940945` consumed exactly one Edge synthesis (`uk-UA-OstapNeural`, `57.216 s`) and then failed in WF04 execution `10799` before creating visual segments. Underlying HTTP error was:

`Visual discovery failed: visual discovery requires timed_beats or beats`.

Verified root cause: WF04 sent `timed_beats`; `visual-discovery.mjs` supported `timedBeats`; the `server.mjs` HTTP adapter forwarded only legacy `beats` and discarded `body.timed_beats`.

Systemic fix now live:

- `body.beats -> beats` retained for legacy compatibility;
- `body.timed_beats -> timedBeats` forwarded for semantic-v3;
- no provider, threshold, workflow or DB behavior was weakened/changed.

Exact Git blobs saved in GitHub:

- `server.mjs`: `4d2656e84a27d9e50f906d7360ca1c8de2c0ef30`;
- `visual-discovery-request.mjs`: `203ca6c39f553283cd84846b438cfbd294468218`;
- adapter regression: `a40c6b0fe6569791a3416ef2d2a9065f526667d9`.

Focused/static proof PASSed: server/helper syntax, HTTP-adapter regression, legacy visual discovery, semantic segmentation, visual-shot quality, WF05 semantic contract and `git diff --check`.

Disposable real HTTP `/visual/discover` proof PASSed with four contiguous 2-second semantic timed beats: HTTP 200, four visual segments, candidate counts `63/64/61/62`, provider errors `0`.

## Adapter deploy / rollback proof

Bounded pre-adapter media-worker rollback snapshot:

`/opt/ai-short-form-content-factory/rollback/20260903T143542Z-pre-visual-discovery-adapter`

Pre-fix media image:

`sha256:36a810e87e8d62b0e24795c57be0affe43b68704a42cda24ea97143b85557a59`

Rollback tag:

`ai-short-form-content-factory-media-worker:rollback-20260903T143542Z-pre-adapter`

Only `server.mjs` and `visual-discovery-request.mjs` were staged into production. Only media-worker was rebuilt/recreated; n8n and PostgreSQL were not recreated.

Current running media-worker image:

`sha256:1f231f47835ab95f0d5b96a8928a5a8a91f9d268758275724f952532fb560a80`

Host/container SHA256 equality after deploy:

- `server.mjs`: `3cae11aa4ee063743b7c696ce5c2cd9b06bff72c2e2bb442a7b75a0985bd16ba`;
- `visual-discovery-request.mjs`: `d400eeb4a0718dd1673961b44c477eb61acb9f24dd76373c92628fbe41cba45a`.

Live production HTTP proof after deploy:

- POST `/visual/discover` HTTP 200;
- `segmentation_version=semantic-visual-segments-v3`;
- four visual segments;
- candidate counts `62/62/61/62`;
- provider errors `0`;
- marker `LIVE_HTTP_SEMANTIC_DISCOVERY_PASS`.

Latest verified runtime after deploy: exactly three project services; PostgreSQL healthy; n8n `/healthz` OK; media-worker `/health` OK with local `Xenova/siglip-base-patch16-224`, q4.

## Rollback baseline for full semantic-v3

Pre-semantic-v3 rollback snapshot:

`/opt/ai-short-form-content-factory/rollback/20260903T134851Z-pre-semantic-v3`

Rollback image tag:

`ai-short-form-content-factory-media-worker:rollback-20260903T134851Z`.

## WF02 / voice contract retained

WF02 multilingual correction commit `e4e856093fa237dab9daaa56dcf443c3b6155f93`; rollback `/opt/ai-short-form-content-factory/rollback/20260903T055250Z-pre-wf02-multilingual`.

Retained rules:

- factual probe languages exactly EN/PL/RU/UK requested-first;
- one Wikipedia request/probe, no retry loop;
- official language link for cross-language handoff;
- no topic mappings/generative translation;
- narration extractive/provenance-preserving;
- local duration preflight;
- one natural Edge synthesis only;
- measured duration authoritative; miss fails closed.

## M8 accepted state

M8 requires at least 10 materially different videos with human review.

Human accepted:

1. zipper `227c8a50-ef1a-49e5-8d26-fdb40f663c83` — HUMAN PASS;
2. EN induction `2c182ff8-ea9f-4ddf-a417-b49f796d23f5` — HUMAN PASS.

Current accepted count remains `2/10`.

Permanent old visual PRODUCT FAIL fixture: `13f64c50-8dd5-47e4-a88f-1411d258e7c4`.

Consumed-Edge jobs never to retry/reuse:

- `4372be34-c417-415f-92f6-63481b3b5686`;
- `85fcc63b-b89b-40d0-b253-6383b715f105`;
- `e1399581-305b-4341-910e-b9477a04f499`;
- `cb98ad2b-1aaa-4117-918d-8fef22940945`;
- `44101dd9-d7d6-4fa7-b62b-908ecfaf0f28`.

## Latest production failure — STOP M8

Fresh job `44101dd9-d7d6-4fa7-b62b-908ecfaf0f28`, `как работает индукционная плита / uk / 60`, was created by exactly one HTTP 201 intake call and is consumed. It must never be retried/reused.

Machine facts:

- exactly one Edge synthesis: `microsoft_edge_readaloud` / `edge_neural` / `uk-UA-OstapNeural`, measured `57.216 s`;
- 18 timed beats persisted;
- 10 semantic visual segments persisted, proving the earlier HTTP `timed_beats` adapter defect is closed;
- WF04 execution `10856` failed while persisting visual shots;
- final state `failed|visuals`; `visual_segments=10`, `visual_shots=0`, no video.

Exact PostgreSQL error: `new row for relation "visual_shots" violates check constraint "visual_shots_score_check"`. Shot 4 carried `selection_score=-0.006621`.

Verified root cause: schema/producer contract mismatch. WF04 persists deterministic `selection_utility = local_rank_score + min(metadata_overlap,5)*0.018 - representation_preference_rank*0.025`, whose current bounded producer domain is `[-0.10, 1.09]`; migration 015 incorrectly constrained persisted values to `[0,2]`. Negative utility is a valid relative assignment utility, not an invalid SigLIP score or visual-quality bypass.

Migration 016 now exists and is proven locally/disposably but is NOT yet production-deployed. It changes only `visual_shots_score_check` to `[-0.10,1.09]`. Static regression and disposable PostgreSQL 18 proof PASS, including real `-0.006621` acceptance, both outside-bound rejection and repeat application. No visual quality threshold/provider/workflow behavior changed.

## Exact next action

Do not create another production job yet.

1. Fresh-read GitHub/runtime and require zero active n8n executions.
2. Capture bounded pre-migration-016 schema rollback evidence, including the current `visual_shots_score_check` and explicit rollback SQL restoring `[0,2]`.
3. Apply only migration `016_visual_shot_selection_utility.sql` transactionally to production PostgreSQL. No n8n/media-worker/workflow redeploy is required.
4. Verify live constraint `[-0.10,1.09]`, migration file equality, database health, exactly three project services and zero active executions.
5. Record deploy/rollback proof in GitHub and update this file.
6. Only then create exactly one completely fresh `как работает индукционная плита / uk / 60` job. Never reuse `44101dd9-d7d6-4fa7-b62b-908ecfaf0f28`.
7. Require full machine proof through `review_ready`; any new consumed-Edge product failure stops M8 again. If machine PASS, give the exact video to the user and do not increment M8 until human acceptance.

## Resume rule

If context is lost: read fresh `PERMANENT_PROJECT_RULES.md`, this file, `ENGINEERING_HISTORY.md`, and fresh runtime before acting.

Current boundary: semantic-v3 + HTTP adapter fix are live; fresh job `44101dd9...` exposed the verified visual-shot selection-score schema mismatch; migration 016 is locally/disposably proven and saved in GitHub but not yet deployed; M8 remains `2/10`; immediate next action is bounded production migration-016 deployment proof, not a new job.