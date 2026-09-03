# Current Project State — Semantic Visual Rebuild

Last updated: 2026-09-03

This file is authoritative for the active semantic visual rebuild on GitHub branch `rebuild/semantic-visual-segments`. Repository/runtime state overrides chat memory. Detailed chronological proof is in `docs/ENGINEERING_HISTORY.md`.

## Mandatory protocol

Before EVERY technical response, diagnosis, recommendation, code/config change, deployment, or test:

1. Read `docs/PERMANENT_PROJECT_RULES.md` fresh from GitHub.
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

Semantic-v3 production critical path:

`topic -> factual evidence -> deterministic evidence-backed narration -> local duration preflight -> exactly one natural Edge voice -> timed beats -> deterministic semantic visual segments -> truthful media eligibility -> local SigLIP ranking + perceptual identity -> global visual-shot assignment -> pre-render visual gate -> independent subtitle/visual timelines -> render-v3 -> post-render visual-state gate -> human review`

## Runtime — live production state

Production root: `/opt/ai-short-form-content-factory`.

Local rebuild worktree: `/opt/ai-short-form-content-factory-rebuild`.

Local rebuild branch: `rebuild/semantic-visual-segments-local`.

Clean local implementation HEAD:

`2405d0431ff2007b52825b273267d07fad9f68ce` — `redesign: separate semantic visual segments from timed beats`.

Fresh post-deploy runtime proof:

- exactly three project containers are running: `media-worker`, `n8n`, `postgres`;
- PostgreSQL is healthy;
- n8n `/healthz` returns OK;
- media-worker `/health` returns OK on bound port `3001`;
- media-worker reports local `Xenova/siglip-base-patch16-224`, dtype `q4`, and one preview fetch attempt;
- rebuild worktree remains clean.

## Semantic-v3 is fully deployed

Migration `015_visual_segments.sql` is live. All three durable relations resolve in production:

- `public.visual_segments`;
- `public.visual_shots`;
- `public.media_library_assets`.

Current published workflows:

- WF02 `TJfA4ZYUEKSTad6k` — multilingual deterministic factual retrieval + evidence-backed narration;
- WF03 `UHxvCZNqaLb1RKMM` — exactly one natural Edge voice + timed beats;
- WF04 `M6VisualSourcing1` — semantic-v3 deterministic visual segmentation/sourcing/assignment;
- WF05 `M7VideoRender1` — semantic-v3 render-v3 acceptance with independent subtitle/visual timelines;
- WF06 `R8ReviewApi1` — review API.

WF04 live published proof:

- active `true`;
- 27 nodes;
- current `versionId` = `activeVersionId` = `12e0857b-3c3c-4640-b7f1-2861050038f1`;
- source/live canonical behavior core SHA-256 = `b6b08f21e0fe58b6661f7413e3389834b92c6142f65831a3afcae526a31b53ed`.

WF05 live published proof:

- active `true`;
- 16 nodes;
- current `versionId` = `activeVersionId` = `ae9d00c2-bd65-4d3f-a8f5-ec0bcf840a12`;
- source/live canonical behavior core SHA-256 = `c5595719c63eecb2680c10dbe6a63e45bb7bc4f6d12308c3b62f5f2953f9a117`.

All semantic-v3 media-worker source files used by the deployment match byte-for-byte between the production host and running `/app/src` container.

Published workflow proof directory:

`/opt/ai-short-form-content-factory/published-proof-semantic-v3-20260903`

## Rollback boundary

Bounded pre-semantic-v3 rollback snapshot:

`/opt/ai-short-form-content-factory/rollback/20260903T134851Z-pre-semantic-v3`

The snapshot SHA256-verifies:

- pre-deploy live published WF04/WF05;
- pre-deploy production filesystem WF04/WF05;
- pre-deploy media-worker source/build inputs;
- `compose.yaml`;
- PostgreSQL schema-only dump and DB state before migration 015;
- runtime image IDs and health metadata.

Pre-deploy media-worker image:

`sha256:4009376d074a271aced92aa0cde159ee46bb445af6998580e088a5d23137413d`

Rollback image tag:

`ai-short-form-content-factory-media-worker:rollback-20260903T134851Z`

## WF02 factual + voice contract retained

WF02 multilingual correction remains live from commit:

`e4e856093fa237dab9daaa56dcf443c3b6155f93` — `fix: make factual retrieval multilingual and explanation-aware`.

Rollback:

`/opt/ai-short-form-content-factory/rollback/20260903T055250Z-pre-wf02-multilingual`

Contract retained:

- bounded factual probe languages exactly EN/PL/RU/UK, requested language first;
- exactly one Wikipedia request per probe, no retry loop;
- official Wikipedia language link required for cross-language handoff;
- no topic-specific mappings or generative translation;
- extractive/provenance-preserving narration compiler;
- local duration preflight before Edge;
- automatic production performs exactly one Edge synthesis;
- provider voice rate/pitch/volume remain natural defaults;
- measured duration is authoritative; a miss fails rather than triggering another synthesis.

## Why semantic-v3 exists

Fresh production job `4372be34-c417-415f-92f6-63481b3b5686`, topic `как работает индукционная плита`, output `uk`, target `60`, passed corrected WF02 and exactly one Edge synthesis but old WF04 failed with `perceptually unique truth-eligible assignment 11/12`.

Verified root cause: timed narration/subtitle beats are transport units and must not automatically become independent semantic media-search obligations.

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

Authoritative constraints:

- no adjacent duplicate perceptual cluster;
- max cluster occurrence = `2`;
- max cluster duration share = `0.34`;
- required rendered state count is derived from shot count and max occurrence;
- post-render midpoint frames are checked independently;
- missing/non-finite quality metrics fail closed;
- no threshold weakening.

WF05/render-v3 consumes independent timelines:

- timed beats for subtitle timing;
- visual shots for visual timing.

Both timelines must cover the same accepted continuous voice track.

## Proven semantic-v3 pre-deploy evidence

Focused/static suite PASS included semantic segmentation, visual-shot quality, WF05 visual-segments contract, visual discovery compatibility, legacy visual-quality regression, WF04 runtime/global/perceptual/download regressions, rank-query contract, representation truth eligibility, 41 Code-node compiles, Studio inline JS compile and Code-node mode regression.

Real-provider read-only semantic-v3 PASS cases:

1. zipper `227c8a50-ef1a-49e5-8d26-fdb40f663c83`: `15.480 s`, six beats -> five segments/shots, clusters 5/required 3, adjacent 0, max occurrence 1, max share `0.2958`, Pexels + Wikimedia, provider errors 0;
2. EN induction `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`: `13.944 s`, six beats -> four segments/shots, clusters 4/required 2, adjacent 0, max occurrence 1, max share `0.3374`, Wikimedia, provider errors 0;
3. UK induction fixture `4372be34-c417-415f-92f6-63481b3b5686`: `57.216 s`, 18 beats -> 10 segments/shots, clusters 9/required 5, adjacent 0, max occurrence 2, max share `0.245`, Pexels + Pixabay + Wikimedia, provider errors 0.

Disposable render-v3 proof PASSed with 24-second accepted audio, six subtitle beats, four visual shots of exactly 6 seconds, H.264/yuv420p 1080x1920, AAC 48 kHz stereo, and pre/post-render state count 4/required 2 with adjacent 0 and max share `0.25`.

Migration 015 separately PASSed against disposable PostgreSQL 18, including repeat application, FK/cascade behavior and constraint rejection. The live deployment then applied the same migration transactionally with `ON_ERROR_STOP=1`.

## Deployment diagnostics that are not product failures

- direct non-sudo Docker access through SentinelX returned `/var/run/docker.sock` permission denied; allowed `sudo docker` access proved runtime healthy;
- early snapshot shell quoting errors stopped before product mutation and were replaced by a structured script;
- `import:workflow --activeState=fromJson` was rejected because production n8n is regular mode, not queue/multi-main; immediate re-export proved published workflows unchanged;
- correct regular-mode workflow deployment is `import:workflow` followed by explicit `publish:workflow`, then one n8n restart after both publishes;
- cleanup of root-owned container `/tmp` import files initially failed and was corrected with root cleanup; import/publish had already succeeded and n8n had not yet restarted.

## Documentation correction

An earlier `docs/ENGINEERING_HISTORY.md` transcription incorrectly wrote the `docs/CURRENT_STATE.md` alignment commit as `f0f80836a666b1010625912c4ba07b8f600d8b56`. That string is incorrect. The actual CURRENT_STATE alignment commit is:

`f0f80836a6666b83502f6b74163936ff1a83ad85`.

Do not use the incorrect transcription as a repository fact.

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

Permanent product-failure fixture:

- `13f64c50-8dd5-47e4-a88f-1411d258e7c4` — old render with only two effective visible states; never use as acceptance evidence.

Consumed-Edge jobs that must never be retried/reused:

- `4372be34-c417-415f-92f6-63481b3b5686`;
- `85fcc63b-b89b-40d0-b253-6383b715f105`;
- `e1399581-305b-4341-910e-b9477a04f499`.

## Exact next action

Semantic-v3 deployment gates are complete. The next action is one completely fresh production job:

- topic: `как работает индукционная плита`;
- output language: `uk`;
- duration: `60`.

For that exact fresh job require full machine proof:

- HTTP intake creates exactly one new job;
- corrected factual retrieval/provenance succeeds;
- exactly one successful Edge synthesis occurs;
- measured duration passes the unchanged gate;
- timed beats exactly cover accepted voice;
- semantic visual segments and visual shots persist and cover the same voice duration;
- every selected media item passes truthful eligibility;
- SigLIP/perceptual sequence gates pass without threshold changes;
- render-v3 post-render frame-state gate passes;
- ffprobe proves H.264 1080x1920 30fps + AAC 48 kHz stereo;
- final job reaches `review_ready`.

If a real product failure occurs, stop M8 progression, record it, diagnose the general root cause and repair it systemically. Never retry the same job after its Edge synthesis has been consumed.

If the fresh job reaches `review_ready`, give the user the exact video for human review. Do not call PRODUCT PASS and do not change M8 accepted count until the user watches that exact video and accepts it.

## Resume rule

If chat/context is lost, read fresh `PERMANENT_PROJECT_RULES.md`, this file, `ENGINEERING_HISTORY.md`, `ARCHITECTURE.md` and fresh VPS/runtime before acting.

Current boundary: semantic-v3 is fully deployed with migration 015, WF04/WF05 and media-worker live and verified; rollback snapshot exists; three services are healthy; M8 remains `2/10`; immediate next action is the single fresh RU-topic -> UK/60 induction-cooktop production job and then exact-video human review.