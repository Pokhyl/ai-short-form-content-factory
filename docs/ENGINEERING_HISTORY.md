# Engineering History — Rebuild

Chronological durable record for material changes, failures, verified root causes, rejected approaches, regressions, deployments and rollback facts. `docs/CURRENT_STATE.md` remains the operational source of truth. Exact code history is recoverable from the listed commits and rollback snapshots.

## 2026-09-02 — Old induction machine PASS invalidated

Job `13f64c50-8dd5-47e4-a88f-1411d258e7c4` reached `review_ready`, but human inspection showed only two effective visible states. The earlier machine PASS is permanently invalidated. Root cause: acceptance counted scene/file presence rather than actual video-level perceptual sequence quality. Never reuse this job as acceptance evidence.

## 2026-09-02 — Visual-quality-v2 rewrite/deploy

Visual path became:

`timed beat + evidence -> deterministic search intents -> multi-source discovery -> metadata/provenance eligibility -> local SigLIP ranking + perceptual identity -> global assignment -> sequence gate -> persist -> render -> post-render pixel-state gate -> review_ready`.

Six-beat contract: every beat truth-eligible; at least five perceptual clusters; zero adjacent duplicates; no cluster over `0.34` total duration share; non-finite metrics fail closed; rendered midpoint frames independently satisfy required state count.

Cross-topic dry-runs without threshold weakening: EN induction 6 clusters/max `0.1813`; PL combustion engine 5/max `0.3333`; RU refrigerator 6/max `0.1667`; UK volcano 6/max `0.1667`.

Commit `f7c4096503c9620910b387129a5a06cce4d26d42` — `redesign: enforce perceptual visual diversity`.
Rollback `/opt/ai-short-form-content-factory/rollback/20260902T175543Z-pre-visual-quality-v2`.
Migration 013 applied; WF04/WF05 published; exactly three project services and PostgreSQL healthy.

Diagnostic mistake: an early compile harness treated a top-level-array workflow export as an object. A zero-count Code-node compile can never be accepted as PASS.

## 2026-09-02 — Reference-media lifecycle failure/fix

Fresh job `1afc307d-aaac-4eed-8387-b05e1b6721eb`, WF04 execution `9902`, failed after its one Edge synthesis because planner persisted fake `reference_media_kind=mixed` and violated the DB constraint.

Systemic correction: `visual_planned + technical_reference` keeps `reference_media_kind=NULL`; `visual_ready` persists actual `photo|diagram|animation`.

Commit `b83bf6d48f1df259c7c6fa0136748ca10d13f1af` — `fix: align reference media kind lifecycle`.
Rollback `/opt/ai-short-form-content-factory/rollback/20260902T181813Z-pre-reference-media-kind-lifecycle`.
Migration 014 live; WF04 live equality proved; runtime healthy.

## 2026-09-02 — M8 #2 induction MACHINE + HUMAN PASS

Accepted fresh job `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`, `How does induction heating work? / en / 15`.

Machine proof: `review_ready`; preflight `14.358 s`; exactly one successful Edge synthesis; measured voice `13.944 s`; six timed beats; 6/6 perceptual clusters, required 5; adjacent 0; max share `0.1813`; post-render six states; ffprobe H.264 1080x1920 30fps + AAC 48kHz stereo. User watched the exact video and accepted it. M8 accepted count became `2/10`.

## 2026-09-02/03 — WF02 multilingual retrieval failure and systemic correction

Observed production failures:

- `Dlaczego popcorn pęka podczas podgrzewania? / pl / 15` failed because native Wikipedia query was over-constrained.
- job `85fcc63b-b89b-40d0-b253-6383b715f105`, topic `как работает индукционная плита`, output `uk`, 60 s, failed at script because the old path issued Russian subject text against Ukrainian Wikipedia without multilingual resolution.

Systemic contract after correction:

- preserve full factual tokens for relevance validation;
- bounded subject-leading discovery query;
- bounded probes exactly EN/PL/RU/UK, requested language first;
- one Wikipedia request per probe, no retry loop;
- official Wikipedia language link required for cross-language handoff;
- no topic mapping, generative translation, provider cascade, bypass or threshold weakening;
- how/why evidence prioritizes mechanism/principle/construction;
- narration remains extractive/provenance-preserving;
- duration gates unchanged.

Real-Wikipedia proof: RU-topic -> UK induction cooktop `60.106 s`; UK refrigerator `59.975 s`; PL popcorn `15.079 s`; EN induction `14.939 s`, all pre-TTS safe. Seven regressions PASS; WF02 Code compile 8/8; staged pipeline PASS; retained duration audit 150 rows / 40 safe / 0 false-safe; CASE1 provenance and visual eligibility PASS.

Diagnostic harness mistake: an initial CASE1 visual invocation accidentally passed `-e never` as Node input and produced `ReferenceError`; that result was invalid. Correct invocation passed.

Commit `e4e856093fa237dab9daaa56dcf443c3b6155f93` — `fix: make factual retrieval multilingual and explanation-aware`.
Rollback `/opt/ai-short-form-content-factory/rollback/20260903T055250Z-pre-wf02-multilingual`.
WF02-only production deploy PASS; live core SHA `0f5893ffba59b23d181c363b26b991450e3fc016a52016e1ec686797dbfe23c1`; no retry/maxTries; three services healthy.

## 2026-09-03 — Fresh UK/60 production failure exposes visual-unit mismatch

Fresh real intake job `4372be34-c417-415f-92f6-63481b3b5686`, topic `как работает индукционная плита`, output `uk`, target 60, returned HTTP 201.

It passed corrected WF02 and its single Edge synthesis: canonical title `Індукційна плита`; preflight `60.106 s`; measured voice `57.216 s`; voice `uk-UA-OstapNeural`; 18 timed beats.

Old WF04 then failed at visuals with `perceptually unique truth-eligible assignment 11/12`. Final state `failed|visuals`. Never retry/reuse this job because its automatic Edge call was already consumed. M8 progression stopped.

## 2026-09-03 — Semantic visual segmentation selected

Verified root cause: timed narration/subtitle beats are transport units and must not automatically become independent semantic media-search obligations.

Design document `docs/VISUAL_SEGMENTATION_DESIGN.md`, initial commit `d19ff9e66f47cbadf206141d4b51bbc3d7631abc`.

New path:

`accepted voice -> timed beats -> deterministic semantic visual segments -> visual shots -> truth eligibility -> local SigLIP -> perceptual sequence control -> render-v3 -> post-render frame gate -> human review`.

No generative visual planner, hosted semantic dependency, paid fallback or threshold weakening. WF01-WF03 and exactly-one-Edge remain unchanged. Additive durable entities: `visual_segments`, `visual_shots`, `media_library_assets`.

## 2026-09-03 — GitHub/VPS branch divergence discovered

VPS/local code and GitHub documentation history diverged from merge base `7d25bac1c4d1a90b2b29183d9ec3ca280d1acfc4`.

- VPS production-code HEAD `e4e856093fa237dab9daaa56dcf443c3b6155f93`.
- GitHub had a separate docs chain.
- `git merge --ff-only` correctly refused.
- VPS HTTPS push had no credentials; SSH authentication also failed.
- no force push/destructive rewrite attempted.

GitHub implementation branch `rebuild/semantic-visual-segments` was created from remote source-of-truth. VPS implementation branch `rebuild/semantic-visual-segments-local` was created from actual production-code HEAD. Reconciliation used GitHub connector writes while preserving remote documentation history.

## 2026-09-03 — Semantic-v3 local implementation

Local-only implementation before deployment:

- `services/media-worker/src/visual-segmentation.mjs` — deterministic semantic grouping;
- `db/migrations/015_visual_segments.sql` — additive semantic visual entities;
- WF04 rewritten around semantic segments and shot assignment;
- media-worker adds `/visual/store-shot` and `/render-v3` while retaining legacy routes;
- WF05 reads independent subtitle-beat and visual-shot timelines;
- post-render midpoint frames independently verify actual states.

A Code-node mode defect was caught: `Require Visual Completion` was `runOnceForEachItem` while using `$input.first()`. It was corrected to use `$json`; mode regression passed.

Regression-fixture mistakes were also caught: one test incorrectly expected a rejected sequence evaluator to throw; another declared a PASS impossible under `0.34`; another offered insufficient perceptual states. Fixtures were corrected; production thresholds were not changed.

## 2026-09-03 — Duration-driven shot cardinality rejected

First semantic implementation reduced the `57.216 s` / 18-beat UK fixture to 9 semantic segments, but `planned_shot_count = ceil(segment_duration / 5.0)` expanded them back to 17 mandatory shots and assignment required unique asset IDs. Real-provider dry-run failed `No valid semantic visual shot assignment at shot 12/17`.

Root cause: the 5-second timer recreated the old cardinality problem. Rejected systemically. A semantic segment normally becomes one shot; another shot may exist only for deterministic semantic/representation transition. File-ID uniqueness is not a proxy for product-visible diversity. Perceptual identity and post-render states remain authoritative.

No candidate-pool inflation, retries, topic mappings, threshold changes or production writes were used.

## 2026-09-03 — Corrected UK/60 real-provider semantic dry-run PASS

After removing elapsed-time shot multiplication and hard asset-uniqueness, persisted job `4372be34-c417-415f-92f6-63481b3b5686` was replayed read-only through local semantic sourcing with real Wikimedia/Pixabay/Pexels plus local SigLIP.

PASS: 18 timed beats -> 10 content-derived semantic segments -> 10 shots; clusters 9/required 5; adjacent duplicates 0; max occurrence 2; max duration share `0.245`; longest shot `7.278 s`; provider errors 0; full `57.216 s` coverage; runtime remained three production services.

Diagnostic harness mistake: it initially hardcoded an expected 9 segments and falsely failed when exact persisted narration produced 10. Assertion removed because segment count is content-derived, not fixture-hardcoded.

## 2026-09-03 — Short-video cross-topic failure exposes mathematical 0.34 conflict

Accepted zipper job `227c8a50-ef1a-49e5-8d26-fdb40f663c83` initially failed semantic dry-run because its `15.480 s` voice permits one perceptual state for at most `5.2632 s` under the unchanged `0.34` share gate. Initial semantic groups `5.546 s`, `5.355 s`, `4.579 s` made the first two mathematically incapable of passing.

Systemic correction:

`effective_max_segment_seconds = min(8.5, accepted_voice_duration * 0.34)`.

Boundaries remain existing timed-beat boundaries. A timed beat is never split just to pass visuals; if one beat exceeds the cap, fail closed. Elapsed time still does not create extra shots. Segmenter version became `semantic-visual-segments-v3`.

## 2026-09-03 — Quality-constrained semantic-v3 focused suite PASS

PASS included semantic segmentation, visual-shot quality including legal non-adjacent reuse, WF05 visual-segments contract, visual discovery compatibility, legacy visual-quality regression, WF04 Code-node runtime/global/perceptual/download regressions, rank-query contract, representation truth eligibility, Code-node compile `41` on Node v24.18.0, Studio inline JS compile and Code-node mode regression.

Runtime before/after remained exactly three project services; n8n/media HTTP 200 and PostgreSQL healthy.

Diagnostic execution mistakes preserved:

1. `docker exec ... node /project/tests/...` failed `MODULE_NOT_FOUND` because the repository is not mounted into live n8n.
2. A disposable n8n image was started without overriding entrypoint, so `node` was interpreted as an n8n command.
3. First disposable real-provider harness mounted a mode-600 temp context file and container user got `EACCES`; readable fixture corrected it.

None was product/runtime evidence.

## 2026-09-03 — Real-provider cross-topic semantic-v3 gate PASS

Reusable harness `tests/semantic_visual_real_provider_dry_run.mjs` replayed exact persisted contexts read-only through local discovery, current local WF04 Code nodes, real Wikimedia/Pixabay/Pexels and local SigLIP.

PASS cases:

1. zipper `227c8a50-ef1a-49e5-8d26-fdb40f663c83`: `15.480 s`, six beats -> five shots, clusters 5/required 3, max share `0.2958`;
2. EN induction `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`: `13.944 s`, six beats -> four shots, clusters 4/required 2, max share `0.3374`;
3. UK induction fixture `4372be34-c417-415f-92f6-63481b3b5686`: `57.216 s`, 18 beats -> 10 shots, clusters 9/required 5, max occurrence 2, max share `0.245`.

Provider errors 0 in all three. No retry, threshold weakening, topic hack, candidate-pool inflation or production write occurred.

## 2026-09-03 — Disposable render-v3 proof

First synthetic attempt used flat solid-color images. Average-hash perceptual identity collapsed some flat colors; `/render-v3` correctly returned 422. This was an invalid synthetic fixture, not product evidence.

Corrected fixture used four spatially distinct black/white patterns, 24-second WAV, six subtitle beats and four 6-second visual shots. HTTP 200 PASS: H.264/yuv420p 1080x1920, AAC 48 kHz stereo, all streams 24 s, pre-render clusters 4/required 2, adjacent 0, max share `0.25`, post-render states 4/required 2, adjacent 0, max share `0.25`. This also proved no artificial 5-second shot gate.

## 2026-09-03 — Semantic design documentation aligned

`docs/VISUAL_SEGMENTATION_DESIGN.md` aligned to the proven contract in commit `61cfb69f4f821154cc5a47f72b8c0634b250f74c`.

`docs/ARCHITECTURE.md` aligned in commit `b71ce862a606b1010625912c4ba07b8f600d8b56` to remove obsolete `one visual per timed beat` semantics and document independent timed-beat/semantic-segment/visual-shot timelines.

`docs/CURRENT_STATE.md` predeploy alignment commit was `f0f80836a6666b83502f6b74163936ff1a83ad85`.

Documentation correction: a later history transcription accidentally wrote this commit as `f0f80836a666b1010625912c4ba07b8f600d8b56`. That string was wrong and is explicitly corrected here; do not use it as a repository fact.

## 2026-09-03 — Semantic-v3 implementation synchronized to GitHub

Clean local rebuild implementation: `2405d0431ff2007b52825b273267d07fad9f68ce` (`redesign: separate semantic visual segments from timed beats`) on `rebuild/semantic-visual-segments-local`.

GitHub branch `rebuild/semantic-visual-segments` received the complete implementation/migration/test set without force push/history rewrite. Material connector commits included `62fef928...` visual quality, `c62fd625...` WF05, `bc1f6515...` WF04 and `602ab214...` media-worker server.

Cross-check of 17 semantic-v3 files: 16 exact Git blob matches. `server.mjs` differed only by final EOF newline; adding one LF to remote bytes yields exact local Git blob `a07fb3396602a0923fa081c022cd3739f6076caf`. `diff -u` reported no code difference beyond missing final newline.

## 2026-09-03 — Pre-deploy diff and migration 015 disposable proof

Full diff from production-code base `e4e856093fa237dab9daaa56dcf443c3b6155f93` to semantic-v3 `2405d0431ff2007b52825b273267d07fad9f68ce` contained exactly the expected 17 semantic-v3 files. `git diff --check` returned 0. No compose/WF02/WF03 changes.

Migration 015 disposable PostgreSQL 18 proof PASS: apply succeeded; second application succeeded; all three tables existed; valid job -> segment -> asset -> shot insert succeeded; job deletion cascaded segments/shots while reusable library asset remained; invalid `planned_shot_count=3` was rejected.

First disposable harness socket failure was a readiness race against PostgreSQL's temporary init server; corrected harness waited for TCP `127.0.0.1`. Not a migration failure.

## 2026-09-03 — Bounded pre-semantic-v3 rollback snapshot complete

Snapshot `/opt/ai-short-form-content-factory/rollback/20260903T134851Z-pre-semantic-v3` was created before semantic production mutation and SHA256-verified. It contains predeploy live published WF04/WF05, filesystem WF04/WF05, media-worker source/build inputs, compose, PostgreSQL schema-only dump/predeploy relation state, runtime image IDs and health metadata.

Predeploy media-worker image `sha256:4009376d074a271aced92aa0cde159ee46bb445af6998580e088a5d23137413d` tagged `ai-short-form-content-factory-media-worker:rollback-20260903T134851Z`.

Diagnostic notes: non-sudo Docker access through SentinelX failed on socket permission; allowed sudo path worked. Two snapshot shell quoting attempts stopped before product mutation; final structured script completed and verified the snapshot.

## 2026-09-03 — Production migration 015 + semantic-v3 media-worker deploy PASS

Immediately before mutation, n8n had zero running/new/waiting executions. Older August stale nonterminal application rows existed but had no live n8n execution.

Seven exact runtime files were staged from clean local `2405d04` and byte-compared before use: migration 015, four semantic media-worker sources, WF04 and WF05.

Migration 015 applied transactionally with `ON_ERROR_STOP=1`. Live PostgreSQL resolved all three new semantic relations.

`docker compose build media-worker` succeeded before replacement. Only media-worker was recreated with `docker compose up -d --no-deps media-worker`; n8n/postgres were not recreated. New media-worker health PASS with local SigLIP and one preview attempt. Three project containers remained.

## 2026-09-03 — Semantic-v3 WF04/WF05 production deploy PASS

First workflow import attempt used `--activeState=fromJson`; n8n 2.33.3 rejected it because regular mode does not support that flag. Immediate published re-export hashes matched the rollback snapshot, proving no published workflow mutation. Deployment-tooling error only.

Correct regular-mode path: `import:workflow` without activeState, then explicit `publish:workflow --id=...` for each workflow. Both imported/published successfully. Cleanup of root-owned temporary files initially failed but was corrected with root; n8n had not restarted yet.

After both publishes, n8n restarted exactly once. Post-restart proof:

- n8n health OK;
- WF04 active=true, 27 nodes; source/live canonical core SHA both `b6b08f21e0fe58b6661f7413e3389834b92c6142f65831a3afcae526a31b53ed`;
- WF05 active=true, 16 nodes; source/live canonical core SHA both `c5595719c63eecb2680c10dbe6a63e45bb7bc4f6d12308c3b62f5f2953f9a117`;
- WF04 `versionId=activeVersionId=12e0857b-3c3c-4640-b7f1-2861050038f1`;
- WF05 `versionId=activeVersionId=ae9d00c2-bd65-4d3f-a8f5-ec0bcf840a12`;
- all four semantic media-worker source files match running container source byte-for-byte;
- migration 015 relations exist;
- PostgreSQL healthy;
- exactly three project containers;
- media-worker health OK with local SigLIP and one preview attempt.

Semantic-v3 became fully deployed.

## 2026-09-03 — CURRENT_STATE updated to live deployed boundary

`docs/CURRENT_STATE.md` was updated in commit `6feae37a56fe121a514b15acf5affc1eccb813b4` to replace the stale predeploy boundary with the actual live semantic-v3 state, rollback location, workflow versions/core hashes, migration 015 status and the next fresh-production acceptance action. The incorrect historical CURRENT_STATE hash transcription is explicitly identified there as well.

## Current M8 state / next action

M8 remains `2/10` human-accepted. Never increment from machine-only evidence.

Next job must be completely fresh:

- topic `как работает индукционная плита`;
- output language `uk`;
- target duration `60`.

Never reuse consumed-Edge jobs `4372be34-c417-415f-92f6-63481b3b5686`, `85fcc63b-b89b-40d0-b253-6383b715f105`, or `e1399581-305b-4341-910e-b9477a04f499`.

Require full machine proof through `review_ready`, exactly one Edge synthesis, measured duration, timed-beat coverage, semantic visual segments/shots, truthful eligibility, SigLIP/perceptual gates, render-v3 post-render state gate and ffprobe. First real product failure stops progression and is fixed systemically. If machine PASS, user must watch the exact fresh video before PRODUCT PASS or M8 count changes.