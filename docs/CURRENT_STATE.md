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

Local rebuild: `/opt/ai-short-form-content-factory-rebuild`, branch `rebuild/semantic-visual-segments-local`, clean implementation HEAD `2405d0431ff2007b52825b273267d07fad9f68ce`.

Semantic-v3 is deployed:

- migration `015_visual_segments.sql` live;
- `visual_segments`, `visual_shots`, `media_library_assets` live;
- WF02 `TJfA4ZYUEKSTad6k` multilingual deterministic factual path live;
- WF03 `UHxvCZNqaLb1RKMM` exactly-one-Edge + timed beats live;
- WF04 `M6VisualSourcing1` semantic-v3 published;
- WF05 `M7VideoRender1` render-v3 published;
- WF06 `R8ReviewApi1` review API live.

WF04 deployment proof:

- active=true, 27 nodes;
- `versionId=activeVersionId=12e0857b-3c3c-4640-b7f1-2861050038f1`;
- source/live canonical core SHA `b6b08f21e0fe58b6661f7413e3389834b92c6142f65831a3afcae526a31b53ed`.

WF05 deployment proof:

- active=true, 16 nodes;
- `versionId=activeVersionId=ae9d00c2-bd65-4d3f-a8f5-ec0bcf840a12`;
- source/live canonical core SHA `c5595719c63eecb2680c10dbe6a63e45bb7bc4f6d12308c3b62f5f2953f9a117`.

Fresh runtime after the failure still has exactly `media-worker`, `n8n`, `postgres`; PostgreSQL healthy; n8n `/healthz` OK; media-worker `/health` OK with local `Xenova/siglip-base-patch16-224`, q4, one preview attempt; no active n8n executions.

## Rollback

Pre-semantic-v3 rollback snapshot:

`/opt/ai-short-form-content-factory/rollback/20260903T134851Z-pre-semantic-v3`

Predeploy media image:

`sha256:4009376d074a271aced92aa0cde159ee46bb445af6998580e088a5d23137413d`

Rollback tag:

`ai-short-form-content-factory-media-worker:rollback-20260903T134851Z`

Snapshot SHA256-verifies old published WF04/WF05, production workflow files, media-worker source/build inputs, compose, PostgreSQL schema/state and runtime metadata.

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

Previously consumed jobs never to reuse: `4372be34-c417-415f-92f6-63481b3b5686`, `85fcc63b-b89b-40d0-b253-6383b715f105`, `e1399581-305b-4341-910e-b9477a04f499`.

## New fresh production failure — STOP M8

Exactly one fresh intake call was made after semantic-v3 deployment:

- topic `как работает индукционная плита`;
- output `uk`;
- target `60`;
- HTTP 201;
- job `cb98ad2b-1aaa-4117-918d-8fef22940945`;
- matching job count changed `3 -> 4`, so one new row was created.

The job is a real PRODUCT FAIL and is now consumed. Never retry/reuse it.

Machine facts:

- WF01 execution `10796` success;
- exactly one Edge result persisted: `microsoft_edge_readaloud`, `edge_neural`, `uk-UA-OstapNeural`, measured `57.216 s`;
- WF04 execution `10799` failed;
- final state `failed|visuals`;
- `visual_segments=0`, `visual_shots=0`;
- no final video;
- no active n8n executions remain.

Concrete error:

`Segmented visual discovery returned no visual segments [line 26]`.

Execution data proved the upstream failure was HTTP 422 from `/visual/discover`:

`Visual discovery failed: visual discovery requires timed_beats or beats`.

## Verified root cause

This is a general HTTP adapter wiring defect, not provider shortage, SigLIP, topic content or an acceptance threshold problem.

- WF04 `Prepare Canonical Media Request` correctly builds `discovery_request.canonical_source` and `discovery_request.timed_beats`.
- WF04 `Fetch Canonical Media` sends exactly `={{ $json.discovery_request }}` to `http://media-worker:3001/visual/discover`.
- `visual-discovery.mjs::discoverVisualCandidates()` correctly accepts `{ beats, timedBeats }` and enters semantic segmented mode when `timedBeats` exists.
- `server.mjs::discoverVisuals()` currently forwards only `beats: body?.beats`.
- It does not forward `timedBeats: body?.timed_beats`.
- Therefore the real HTTP semantic-v3 path discards `timed_beats` before invoking the already-proven discovery function.
- Earlier local real-provider semantic-v3 harnesses called the function directly and therefore did not cover this HTTP adapter boundary.

No threshold or provider change is justified.

## Documentation correction

The correct older CURRENT_STATE predeploy alignment commit is `f0f80836a6666b83502f6b74163936ff1a83ad85`. An earlier history transcription contained a wrong hybrid hash and is explicitly invalidated in `ENGINEERING_HISTORY.md`.

## Exact next action

Do not create another production job yet.

1. Fix the general media-worker HTTP adapter so `/visual/discover` forwards both:
   - legacy `beats: body?.beats`;
   - semantic `timedBeats: body?.timed_beats`.
2. Add a regression specifically covering the HTTP adapter contract so function-only tests cannot miss this class of defect again.
3. Run focused/static regressions plus a disposable HTTP `/visual/discover` semantic request; do not change thresholds/providers.
4. Record proof in GitHub.
5. Take a bounded pre-fix media-worker rollback snapshot/tag if needed; migration/WF04/WF05 do not require redeploy unless evidence shows otherwise.
6. Deploy only the corrected media-worker.
7. Verify host/container source equality, health, exactly three persistent services, and real HTTP semantic discovery response.
8. Only then create a different completely fresh `как работает индукционная плита / uk / 60` job.
9. Require full machine proof through `review_ready`; if it passes, give the exact video to the user for human review. Do not change M8 count until user accepts it.

## Resume rule

If context is lost: read fresh `PERMANENT_PROJECT_RULES.md`, this file, `ENGINEERING_HISTORY.md`, and fresh runtime before acting.

Current boundary: semantic-v3 remains deployed and healthy except for the verified `/visual/discover` adapter defect; fresh job `cb98ad2b...` consumed one Edge and failed before semantic segments; M8 is stopped at `2/10`; next work is adapter fix + HTTP-boundary regression + media-worker-only redeploy, not another job.