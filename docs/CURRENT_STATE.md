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
- exactly three project containers are running; PostgreSQL is healthy.

Published workflows:

- WF02 `TJfA4ZYUEKSTad6k` — deterministic evidence/narration;
- WF03 `UHxvCZNqaLb1RKMM` — one natural Edge voice + timed beats;
- WF04 `M6VisualSourcing1` — current production visual sourcing;
- WF05 `M7VideoRender1` — current production render.

Migration `db/migrations/012_staged_semantic_pipeline.sql` is applied in production.

IMPORTANT SOURCE NOTE: the GitHub branch code tree is behind the VPS rebuild worktree because the VPS has no GitHub HTTPS credentials and no SSH key. Do not silently assume GitHub workflow blobs equal production or the current local rewrite. For code decisions, read this state and then inspect fresh VPS rebuild/runtime state.

Current local rebuild HEAD before the active rewrite commit: `99fc079baf44de28470a47f5e3101b65bd2769ad`.

Current rebuild worktree has active uncommitted visual-pipeline rewrite changes in:

- `n8n/workflows/WF02-plan-script-and-scenes.json`;
- `n8n/workflows/WF04-visual-sourcing.json`;
- `n8n/workflows/WF05-video-render.json`;
- `services/media-worker/src/server.mjs`;
- `services/media-worker/src/visual-framing.mjs`;
- `db/migrations/013_visual_quality_gate.sql`;
- `services/media-worker/src/visual-discovery.mjs`;
- `services/media-worker/src/visual-quality.mjs`;
- `tests/visual_discovery_regression.mjs`;
- `tests/visual_quality_regression.mjs`;
- `tests/wf02_fact_search_query_regression.mjs`.

Relevant earlier local commits:

- `8af7f56` — retained Edge operating bands;
- `3619f11` — require metadata-relevant visual representation before choosing diagram/animation;
- `99fc079` — align WF04 SigLIP rank-query producer contract with media-worker maximum of 200 characters;
- earlier visual commits: `0f4723a`, `f7c321a`, `954b383`.

Latest earlier rollback snapshots:

- `/opt/ai-short-form-content-factory/rollback/20260902T143632Z-pre-wf02-duration-band`
- `/opt/ai-short-form-content-factory/rollback/20260902T144337Z-pre-wf04-representation`
- `/opt/ai-short-form-content-factory/rollback/20260902T160102Z-pre-wf04-rank-query-contract`

## CASE1 — zipper — PASS

Frozen CASE1:

`How does a zipper work? / en / 15`

Fresh accepted job:

`227c8a50-ef1a-49e5-8d26-fdb40f663c83`

Machine proof included evidence-backed narration, one Edge synthesis, measured duration in gate, six timed beats, truthful zipper visuals and valid final H.264/AAC output.

Human gate: PASS. On 2026-09-02 the user viewed this fresh result and explicitly accepted it as normal.

## M8 Quality Run — active

Roadmap M8 requires at least 10 materially different videos and review of script, voice, visual relevance, subtitles, and render.

### M8 #1 — zipper

PASS, including human-visible review. Job `227c8a50-ef1a-49e5-8d26-fdb40f663c83`.

### M8 #2 — induction heating — PRODUCT FAIL

Topic:

`How does induction heating work? / en / 15`

Job:

`13f64c50-8dd5-47e4-a88f-1411d258e7c4`

The previous machine state `review_ready` is NOT a valid quality pass. Human-visible inspection showed that the 14-second video had only two effective visual states: roughly the first four seconds used one image and roughly the remaining ten seconds used another. Six database scenes marked `visual_ready` therefore did not represent six useful visual states.

This is the trigger for the active visual-pipeline rewrite below. Do not describe this induction job as a successful M8 result.

## ACTIVE WORK — FULL VISUAL PIPELINE REWRITE

This is the current task. DO NOT resume the old incremental Wikimedia-only matcher patching. DO NOT continue M8 generation until this rewrite is regression-tested and deployed boundedly.

### Root architectural failure

The current production visual path can truthfully assign an asset to every beat while still producing a visually degenerate video. The former acceptance contract checked per-scene asset presence but did not validate the quality of the sequence as a whole.

The clean rebuild also removed the previously available multi-provider sourcing layer and effectively constrained WF04 to canonical/Wikimedia media. A max-unique matcher cannot manufacture diversity when the eligible pool itself is tiny.

### Stable parts that remain

Do not rebuild these unless a separate real defect proves it necessary:

- WF01 intake;
- PostgreSQL durable state model, extended only where the new visual-quality contract needs durable fields;
- persisted factual evidence/provenance;
- deterministic evidence-backed narration architecture;
- local duration preflight architecture;
- exactly one natural Edge synthesis per automatic job;
- measured voice duration as authoritative;
- timed beats created after accepted voice;
- exactly three persistent services;
- 0 PLN per-video external API cost.

### New visual architecture

Replace the current `canonical article media -> per-beat eligibility -> rank -> assignment` bottleneck with:

`timed beat + evidence -> deterministic search intents -> multi-source candidate discovery -> metadata/provenance eligibility -> local SigLIP ranking + perceptual identity -> global sequence assignment -> sequence quality gate -> persist -> render -> post-render visual-state gate -> review_ready`

#### 1. Multi-source discovery

Build one normalized candidate pool from independent zero-cost provider adapters:

- canonical article media;
- Wikimedia Commons full search;
- Pixabay photo search when the key is available/healthy;
- Pexels video search only as an optional provider when authorization is healthy.

Pexels MUST NOT be required for pipeline success. Current direct provider check returned HTTP 403 with the configured key.

The production `.env` and compose contain `PIXABAY_API_KEY` and `PEXELS_API_KEY`, but the currently running media-worker was created without those environment variables. Bounded deploy must recreate media-worker and verify actual container environment/provider behavior without exposing secret values.

Do not restore the old 66-node provider cascade, provider retry tree, topic-specific fallback mappings, or fallback-generated visuals. Discovery belongs behind a small bounded media-worker adapter contract.

#### 2. Deterministic intent and truth eligibility

For each beat derive multiple bounded search intents from:

- canonical title;
- beat narration;
- supporting evidence text;
- named/concrete entities and mechanism terms available in evidence;
- target-language/English source metadata when already available.

Truth eligibility occurs before SigLIP.

Do not use SigLIP as a truth oracle. Do not weaken factual gates merely to obtain diversity.

#### 3. Local semantic ranking

Only truth-eligible candidates reach local SigLIP relative ranking.

Rank-query producer contract remains maximum 200 characters.

Ranking must return enough metadata for global sequence selection, including a perceptual preview identity/hash so visually near-identical files cannot masquerade as different assets.

#### 4. Global sequence assignment

Assignment is a video-level optimization, not six independent choices.

It must consider:

- semantic relevance;
- visual/perceptual uniqueness, not just provider asset ID;
- no adjacent repeat cluster;
- duration share of each visual cluster;
- representation/media-type usefulness;
- diversity across beats without selecting factually unsupported media.

The old rule `different candidate_id == different visual` is insufficient.

#### 5. Pre-render visual quality gate

A job cannot reach render merely because every scene is `visual_ready`.

The new gate currently targets these fail-closed properties:

- every beat has one persisted truth-eligible selected asset;
- for 6 beats, at least 5 distinct visual/perceptual clusters;
- no adjacent duplicate visual cluster;
- no single visual cluster may dominate more than roughly one third of total voice duration;
- all diversity metrics must be finite numeric values; `NaN`/missing values fail closed;
- quality metrics must be persisted durably on the job (`visual_quality`) so WF05 can independently verify them.

The exact thresholds may only be changed from cross-topic evidence; do not lower them to make one topic pass.

The failed induction sequence is the negative regression fixture: `2/6` unique assets, 4 adjacent repeats, one asset about 68% of duration => MUST FAIL.

A representative 6-beat sequence with 5 unique assets, no adjacent duplicates and max asset share about 33% => PASS in current regression.

#### 6. Render behavior

Still images must not produce dead static frames by default. For normal photographic stills use deterministic subtle pan/zoom motion. Technical/factual diagrams must remain readable and must not be distorted for cosmetic movement.

Motion is NOT a substitute for source diversity: reuse of the same visual cluster remains reuse and cannot satisfy the diversity gate merely because a different crop/pan is applied.

#### 7. WF05 independent acceptance

WF05 must load selected asset IDs/metadata and persisted `visual_quality`, validate the sequence independently, then render.

`review_ready` must require both:

- standard media/ffprobe/timing/subtitle checks;
- visual-quality acceptance.

#### 8. Post-render visual-state gate

After rendering, inspect representative frames at beat midpoints and compute perceptual hashes/clusters from the actual rendered pixels.

This catches cases where different provider IDs still render as effectively the same visual.

The rendered video cannot become `review_ready` if the actual frame-state diversity is below the accepted sequence contract.

### Work already completed locally for this rewrite

The following is work-in-progress in `/opt/ai-short-form-content-factory-rebuild`; it is NOT yet production acceptance and MUST NOT be described as deployed:

- `services/media-worker/src/visual-discovery.mjs` added;
- multi-provider discovery endpoint integration added locally to `server.mjs`;
- `services/media-worker/src/visual-quality.mjs` added;
- `db/migrations/013_visual_quality_gate.sql` added;
- WF04 rewritten locally toward 27-node multi-source discovery/rank/global-assignment flow;
- WF05 rewritten locally to carry/validate visual quality;
- still-image motion added locally to visual framing;
- pre-render and post-render visual-state checks added locally to media-worker;
- perceptual preview hashing is being integrated into `/visual/rank` and global assignment;
- provider discovery regression PASS;
- visual quality negative/positive regression PASS;
- WF04 Code-node compile PASS before the latest perceptual-cluster change;
- WF05 Code-node compile PASS before the latest perceptual-cluster change.

### Real induction dry-run evidence for the new design

Using the exact induction context without deploying the rewrite:

- deterministic beat intents were generated for induction/electronic oscillator/alternating magnetic field/eddy currents/resistance/Joule heating;
- expanded Wikimedia Commons discovery returned about 20-22 candidates per beat instead of the former tiny canonical-only pool;
- eligible pools contained up to 10 candidates per beat;
- a dry-run global assignment found six different induction-related Wikimedia assets rather than the former two repeated assets.

This dry-run is evidence that the pool bottleneck can be removed, but it is NOT final acceptance. The dry-run exposed a missing `duration_seconds` propagation that produced `NaN` in one quality metric; this has been corrected locally and the quality evaluator is being made fail-closed on non-finite values.

### Next actions — exact order

1. Finish perceptual hash output from local SigLIP rank and cluster-aware global assignment.
2. Re-run static compile and all visual discovery/quality/assignment regressions after that latest change.
3. Re-run exact induction dry-run and require finite quality metrics plus perceptual-cluster diversity acceptance.
4. Run cross-topic dry-runs on materially different topics/languages; do not optimize only for induction/zipper.
5. Inspect complete git diff and remove accidental/unrelated changes. WF02 retrieval work must be handled explicitly, not silently bundled into visual rewrite.
6. Commit the completed rewrite locally as a coherent systemic change.
7. Create bounded rollback snapshot for production workflow/media-worker/database state.
8. Apply migration `013_visual_quality_gate.sql`.
9. Deploy media-worker, WF04 and WF05 only as required by the final diff; recreate media-worker so provider env is actually present.
10. Verify exactly three persistent services, health, no secret leakage, live workflow code equality with the deployed local files, provider discovery behavior, SigLIP, store, render and review endpoints.
11. Start a completely fresh induction job. Do not reuse `13f64c50-...`.
12. Require full machine proof: evidence, one Edge synthesis, timed beats, rich candidate pools, truth eligibility, perceptual/global assignment, persisted visual_quality, render quality gate, ffprobe and post-render frame-state gate.
13. Human-review the exact new induction video. It is not an M8 PASS until the visible result is actually acceptable.
14. Then continue M8 with materially different topics/languages until at least 10 videos have human-visible quality review.
15. The first real product failure stops progression and is fixed systemically. No topic-specific patching.

## Resume rule

If a later chat/context loses the recent conversation, DO NOT infer the next step from memory. Read this file, inspect the current VPS rebuild worktree/runtime, and continue from `ACTIVE WORK — FULL VISUAL PIPELINE REWRITE` in the exact next-action order above.
