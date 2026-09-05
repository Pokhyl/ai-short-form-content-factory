# Engineering History — Rebuild

Chronological durable record for material changes, failures, verified root causes, rejected approaches, regressions, deployments and rollback facts. `docs/CURRENT_STATE.md` remains the operational source of truth. Exact code history is recoverable from listed commits and rollback snapshots.

## 2026-09-02 — Old induction machine PASS invalidated

Job `13f64c50-8dd5-47e4-a88f-1411d258e7c4` reached `review_ready`, but human inspection showed only two effective visible states. Earlier machine PASS is permanently invalidated. Root cause: acceptance counted scene/file presence rather than actual video-level perceptual sequence quality. Never reuse this job as acceptance evidence.

## 2026-09-02 — Visual-quality-v2 rewrite/deploy

Visual path became:

`timed beat + evidence -> deterministic search intents -> multi-source discovery -> metadata/provenance eligibility -> local SigLIP ranking + perceptual identity -> global assignment -> sequence gate -> persist -> render -> post-render pixel-state gate -> review_ready`.

Six-beat contract: every beat truth-eligible; at least five perceptual clusters; zero adjacent duplicates; no cluster over `0.34` total duration share; non-finite metrics fail closed; rendered midpoint frames independently satisfy required state count.

Cross-topic dry-runs without threshold weakening: EN induction 6 clusters/max `0.1813`; PL combustion engine 5/max `0.3333`; RU refrigerator 6/max `0.1667`; UK volcano 6/max `0.1667`.

Commit `f7c4096503c9620910b387129a5a06cce4d26d42`. Rollback `/opt/ai-short-form-content-factory/rollback/20260902T175543Z-pre-visual-quality-v2`. Migration 013 applied; WF04/WF05 published; exactly three project services and PostgreSQL healthy.

Diagnostic mistake: an early compile harness treated a top-level-array workflow export as an object. A zero-count Code-node compile can never be accepted as PASS.

## 2026-09-02 — Reference-media lifecycle failure/fix

Fresh job `1afc307d-aaac-4eed-8387-b05e1b6721eb`, WF04 execution `9902`, failed after its one Edge synthesis because planner persisted fake `reference_media_kind=mixed` and violated the DB constraint.

Systemic correction: `visual_planned + technical_reference` keeps `reference_media_kind=NULL`; `visual_ready` persists actual `photo|diagram|animation`.

Commit `b83bf6d48f1df259c7c6fa0136748ca10d13f1af`. Rollback `/opt/ai-short-form-content-factory/rollback/20260902T181813Z-pre-reference-media-kind-lifecycle`. Migration 014 live; WF04 live equality proved; runtime healthy.

## 2026-09-02 — M8 #2 induction MACHINE + HUMAN PASS

Accepted job `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`, `How does induction heating work? / en / 15`. Machine proof: `review_ready`; preflight `14.358 s`; exactly one successful Edge synthesis; measured voice `13.944 s`; six timed beats; 6/6 perceptual clusters, required 5; adjacent 0; max share `0.1813`; post-render six states; ffprobe H.264 1080x1920 30fps + AAC 48kHz stereo. User watched exact video and accepted it. M8 accepted count became `2/10`.

## 2026-09-02/03 — WF02 multilingual retrieval failure and systemic correction

Observed production failures:

- PL popcorn failed because native Wikipedia query was over-constrained.
- job `85fcc63b-b89b-40d0-b253-6383b715f105`, `как работает индукционная плита / uk / 60`, failed at script because old path issued Russian subject text against Ukrainian Wikipedia without multilingual resolution.

Systemic contract: preserve full factual tokens for relevance validation; bounded subject-leading discovery; bounded probes exactly EN/PL/RU/UK requested-first; one Wikipedia request per probe; official language link required for cross-language handoff; no topic mapping/generative translation/provider cascade/bypass/threshold weakening; explanation topics prioritize mechanism/principle/construction; narration remains extractive/provenance-preserving; duration gates unchanged.

Real-Wikipedia proof: RU-topic -> UK induction `60.106 s`; UK refrigerator `59.975 s`; PL popcorn `15.079 s`; EN induction `14.939 s`, all pre-TTS safe. Seven regressions PASS; WF02 Code compile 8/8; staged pipeline PASS; retained duration audit 150 rows / 40 safe / 0 false-safe; CASE1 provenance and visual eligibility PASS.

Diagnostic mistake: an initial CASE1 invocation accidentally passed `-e never` as Node input; invalid result. Correct invocation passed.

Commit `e4e856093fa237dab9daaa56dcf443c3b6155f93`. Rollback `/opt/ai-short-form-content-factory/rollback/20260903T055250Z-pre-wf02-multilingual`. WF02-only production deploy PASS; live core SHA `0f5893ffba59b23d181c363b26b991450e3fc016a52016e1ec686797dbfe23c1`; no retry/maxTries; three services healthy.

## 2026-09-03 — Fresh UK/60 old-visual production failure

Fresh job `4372be34-c417-415f-92f6-63481b3b5686`, `как работает индукционная плита / uk / 60`, HTTP 201. Corrected WF02 passed; one Edge synthesis produced `uk-UA-OstapNeural`, measured `57.216 s`, 18 timed beats. Old WF04 failed with `perceptually unique truth-eligible assignment 11/12`. Final `failed|visuals`. Never retry/reuse because Edge was consumed.

Verified root cause: timed narration/subtitle beats are transport units and must not automatically become independent semantic visual obligations.

## 2026-09-03 — Semantic visual segmentation selected

Design `docs/VISUAL_SEGMENTATION_DESIGN.md`, initial commit `d19ff9e66f47cbadf206141d4b51bbc3d7631abc`.

New path:

`accepted voice -> timed beats -> deterministic semantic visual segments -> visual shots -> truth eligibility -> local SigLIP -> perceptual sequence control -> render-v3 -> post-render frame gate -> human review`.

No generative visual planner, hosted semantic dependency, paid fallback or threshold weakening. WF01-WF03 and exactly-one-Edge unchanged. Additive entities: `visual_segments`, `visual_shots`, `media_library_assets`.

## 2026-09-03 — GitHub/VPS branch divergence

VPS/local code and GitHub docs diverged from merge base `7d25bac1c4d1a90b2b29183d9ec3ca280d1acfc4`. VPS production-code HEAD was `e4e856093fa237dab9daaa56dcf443c3b6155f93`; GitHub had separate docs chain. `git merge --ff-only` refused; VPS HTTPS/SSH push lacked auth. No force push or destructive rewrite. GitHub branch `rebuild/semantic-visual-segments` and VPS branch `rebuild/semantic-visual-segments-local` were reconciled through connector writes while preserving remote docs history.

## 2026-09-03 — Semantic-v3 local implementation

Local implementation added deterministic `visual-segmentation.mjs`, migration 015, semantic WF04, `/visual/store-shot`, `/render-v3`, independent WF05 subtitle/visual timelines, and post-render midpoint-state validation. A Code-node mode defect in `Require Visual Completion` was caught and corrected. Several impossible/mistaken regression fixtures were corrected without production threshold changes.

## 2026-09-03 — Duration-driven shot cardinality rejected

Initial semantic implementation reduced `57.216 s` / 18 beats to 9 semantic segments but `planned_shot_count = ceil(segment_duration / 5.0)` expanded them to 17 shots and forced unique asset IDs. Real-provider dry-run failed at shot 12/17. Root cause: fixed elapsed-time shot multiplication recreated old cardinality defect.

Systemic rule: one semantic segment normally equals one shot; extra shot only for deterministic semantic/representation transition. File-ID uniqueness is not product-visible diversity. No candidate-pool inflation, retries, topic mappings, threshold changes or production writes.

## 2026-09-03 — Corrected UK/60 semantic real-provider PASS

Read-only replay of `4372be34...` through real Wikimedia/Pixabay/Pexels + local SigLIP: 18 beats -> 10 semantic segments/shots; clusters 9/required 5; adjacent 0; max occurrence 2; max duration share `0.245`; longest shot `7.278 s`; provider errors 0; full `57.216 s` coverage. A hardcoded expected-9-segment test was removed because segment count is content-derived.

## 2026-09-03 — Short-video 0.34 mathematical conflict and systemic fix

Accepted zipper `227c8a50-ef1a-49e5-8d26-fdb40f663c83`, voice `15.480 s`, exposed that old semantic groups `5.546`, `5.355`, `4.579 s` made first two states mathematically impossible under unchanged `0.34` duration-share gate.

Systemic correction:

`effective_max_segment_seconds = min(8.5, accepted_voice_duration * 0.34)`.

Boundaries remain timed-beat boundaries. A beat is never split just to satisfy visuals; if it exceeds cap, fail closed. Elapsed time does not create extra shots. Segmenter version `semantic-visual-segments-v3`.

## 2026-09-03 — Semantic-v3 focused/static suite PASS

PASS: semantic segmentation; visual-shot quality including legal non-adjacent reuse; WF05 visual-segments contract; visual discovery compatibility; legacy visual-quality regression; WF04 runtime/global/perceptual/download regressions; rank-query contract; representation truth eligibility; 41 Code-node compiles on Node v24.18.0; Studio inline JS compile; Code-node mode regression. Runtime remained exactly three services; n8n/media HTTP 200 and PostgreSQL healthy.

Diagnostic mistakes preserved: live n8n container did not mount repo (`MODULE_NOT_FOUND`); disposable n8n image entrypoint interpreted `node` as n8n command; first provider harness temp context was mode-600 and caused EACCES. None were product evidence.

## 2026-09-03 — Real-provider cross-topic semantic-v3 PASS

Reusable `tests/semantic_visual_real_provider_dry_run.mjs` PASSed:

1. zipper `15.480 s`: six beats -> five shots; clusters 5/required 3; max share `0.2958`;
2. EN induction `13.944 s`: six beats -> four shots; clusters 4/required 2; max share `0.3374`;
3. UK induction `57.216 s`: 18 beats -> 10 shots; clusters 9/required 5; max occurrence 2; max share `0.245`.

Provider errors 0; no retry, threshold weakening, topic hack, candidate-pool inflation or production write.

## 2026-09-03 — Disposable render-v3 proof

Initial flat-color fixture correctly failed because average-hash collapsed visually similar spatial states. Corrected fixture used four spatially distinct black/white patterns, 24-second WAV, six subtitle beats and four 6-second shots. HTTP 200 PASS: H.264/yuv420p 1080x1920; AAC 48 kHz stereo; all streams 24 s; pre/post states 4/required 2; adjacent 0; max share `0.25`. Proved no artificial 5-second shot gate.

## 2026-09-03 — Documentation alignment and implementation sync

`VISUAL_SEGMENTATION_DESIGN.md` aligned in commit `61cfb69f4f821154cc5a47f72b8c0634b250f74c`; `ARCHITECTURE.md` aligned in `b71ce862a606b1010625912c4ba07b8f600d8b56`. Correct CURRENT_STATE predeploy alignment commit: `f0f80836a6666b83502f6b74163936ff1a83ad85`; a later hybrid hash transcription was wrong and must not be used.

Clean local semantic implementation HEAD: `2405d0431ff2007b52825b273267d07fad9f68ce`. GitHub branch received full implementation/migration/test set without force push. Cross-check: 16/17 exact Git blob matches; `server.mjs` differed only by final EOF LF normalization, no semantic code difference.

## 2026-09-03 — Predeploy proof + rollback

Full diff from `e4e8560` to `2405d04`: exactly expected 17 files; `git diff --check` PASS; no compose/WF02/WF03 changes. Migration 015 disposable PostgreSQL 18 proof PASS including repeat application, FK/cascade and invalid shot-count rejection. Initial Unix-socket readiness failure was a harness race, corrected with TCP readiness.

Bounded rollback snapshot `/opt/ai-short-form-content-factory/rollback/20260903T134851Z-pre-semantic-v3` SHA256-verifies old published WF04/WF05, filesystem workflows, media-worker source/build inputs, compose, DB schema/state and runtime metadata. Predeploy media image `sha256:4009376d074a271aced92aa0cde159ee46bb445af6998580e088a5d23137413d`, rollback tag `ai-short-form-content-factory-media-worker:rollback-20260903T134851Z`.

## 2026-09-03 — Semantic-v3 production deploy PASS

Migration 015 applied transactionally. Only media-worker recreated; health PASS with local SigLIP. WF04/WF05 import first attempted with unsupported `--activeState=fromJson` in regular n8n mode; immediate published re-export proved no-op. Correct path `import:workflow` then explicit `publish:workflow`, followed by exactly one n8n restart.

Post-restart: WF04 active 27 nodes, source/live core SHA `b6b08f21e0fe58b6661f7413e3389834b92c6142f65831a3afcae526a31b53ed`, version=activeVersion `12e0857b-3c3c-4640-b7f1-2861050038f1`; WF05 active 16 nodes, core SHA `c5595719c63eecb2680c10dbe6a63e45bb7bc4f6d12308c3b62f5f2953f9a117`, version=activeVersion `ae9d00c2-bd65-4d3f-a8f5-ec0bcf840a12`; semantic media-worker sources matched running container; migration 015 relations live; PostgreSQL healthy; exactly three project containers.

`CURRENT_STATE.md` updated to live deployed boundary in commit `6feae37a56fe121a514b15acf5affc1eccb813b4`.

## 2026-09-03 — Fresh semantic-v3 production PRODUCT FAIL: HTTP adapter dropped timed_beats

After full deployment, exactly one new intake was made for `как работает индукционная плита / uk / 60`.

- HTTP 201;
- job `cb98ad2b-1aaa-4117-918d-8fef22940945`;
- matching row count `3 -> 4`, proving one new row;
- WF01 execution `10796` success;
- one Edge synthesis only: `microsoft_edge_readaloud`, `edge_neural`, `uk-UA-OstapNeural`, measured `57.216 s`;
- WF04 execution `10799` failed;
- final state `failed|visuals`;
- `visual_segments=0`, `visual_shots=0`, no video;
- job is consumed and must never be retried/reused.

Visible error: `Segmented visual discovery returned no visual segments [line 26]`.

Execution data proved underlying `/visual/discover` HTTP 422: `Visual discovery failed: visual discovery requires timed_beats or beats`.

Verified general root cause:

- WF04 correctly builds and sends `discovery_request.timed_beats`;
- `visual-discovery.mjs::discoverVisualCandidates()` supports `timedBeats` and semantic segmented mode;
- `server.mjs::discoverVisuals()` forwarded only `beats: body?.beats` and discarded `body?.timed_beats`;
- function-level real-provider harnesses therefore passed while the actual HTTP boundary was untested.

This is an HTTP adapter wiring defect, not provider shortage, SigLIP, topic content, or acceptance-threshold failure. No threshold/provider change is justified. M8 remains stopped at `2/10`.

## 2026-09-03 — Engineering-history accidental overwrite detected and recovered

During logging of the adapter failure, a connector `update_file` call accidentally replaced `docs/ENGINEERING_HISTORY.md` with an empty file (blob `c235e237140413aeadb07484c698708cc199220f`). This was a process/tooling failure that could have destroyed durable context.

Recovery used the last complete pre-overwrite Git blob `d2f50deb811c80717c76126101b74856724ccfae`, then reconstructed this chronological history and appended the new production failure/root cause. The empty blob must never be treated as valid project history.

## 2026-09-03 — HTTP adapter fix locally proven and synchronized to GitHub

Systemic correction is isolated to the real HTTP boundary. Local commit `12533a3b241a2901a17bb25bbee18b091f9c6eb8` adds `services/media-worker/src/visual-discovery-request.mjs`, updates `server.mjs` to call `discoverVisualCandidates(buildVisualDiscoveryOptions(...))`, and adds `tests/media_worker_visual_discovery_adapter_regression.mjs`.

The adapter maps both contracts without changing discovery/provider/quality behavior:

- legacy `body.beats -> beats`;
- semantic `body.timed_beats -> timedBeats`.

Focused proof on the exact local commit PASSed using disposable Node 24 because the SentinelX non-login shell itself did not expose `node` in PATH. That PATH result was an execution-environment issue; the first command did not execute product tests. The corrected proof PASSed syntax checks plus adapter regression, legacy visual-discovery regression, semantic-segmentation regression, visual-shot-quality regression, WF05 semantic contract and `git diff --check`.

Disposable media-worker HTTP proof then exercised the actual `/visual/discover` route. The first synthetic request contained two `3.2 s` beats over total `6.4 s`; it reached semantic segmentation and correctly returned 422 because the unchanged `0.34` quality cap permits only `2.176 s` per visual state. This was an invalid fixture, not product failure; no gate was changed.

Corrected disposable HTTP fixture used four contiguous `2 s` timed beats over `8 s`. `/visual/discover` returned HTTP 200 with `segmentation_version`, four `visual_segments`, candidate counts `63/64/61/62`, and provider errors `0`. Marker: `HTTP_SEMANTIC_DISCOVERY_PASS`. No TTS and no production mutation occurred.

GitHub code synchronization used Git Data objects and a non-force fast-forward. Remote commit `3dbc3610f83e5d15466d6825218e0c3ad2b69f0f` contains the exact three local files. Verified remote/local Git blob equality:

- `server.mjs` = `4d2656e84a27d9e50f906d7360ca1c8de2c0ef30`;
- `visual-discovery-request.mjs` = `203ca6c39f553283cd84846b438cfbd294468218`;
- adapter regression = `a40c6b0fe6569791a3416ef2d2a9065f526667d9`.

No force push, provider change, threshold change, workflow change, DB change or production job occurred during this correction/proof stage.

## 2026-09-03 — HTTP adapter media-worker-only production deploy PASS

Before deployment, n8n active execution count was verified as `0`. A bounded media-worker-only rollback snapshot was created and SHA256-verified at:

`/opt/ai-short-form-content-factory/rollback/20260903T143542Z-pre-visual-discovery-adapter`

The snapshot contains the pre-fix media-worker source/build inputs, compose file and runtime metadata. Pre-fix running image was `sha256:36a810e87e8d62b0e24795c57be0affe43b68704a42cda24ea97143b85557a59`; rollback tag `ai-short-form-content-factory-media-worker:rollback-20260903T143542Z-pre-adapter`.

Only two production source files were changed from clean local `12533a3`:

- `services/media-worker/src/server.mjs`;
- `services/media-worker/src/visual-discovery-request.mjs`.

Both were byte-compared to local source before build. `docker compose build media-worker` succeeded; `docker compose up -d --no-deps media-worker` recreated only media-worker. n8n and PostgreSQL were not recreated.

Post-deploy proof:

- running media-worker image `sha256:1f231f47835ab95f0d5b96a8928a5a8a91f9d268758275724f952532fb560a80`;
- host/container SHA256 `server.mjs` both `3cae11aa4ee063743b7c696ce5c2cd9b06bff72c2e2bb442a7b75a0985bd16ba`;
- host/container SHA256 `visual-discovery-request.mjs` both `d400eeb4a0718dd1673961b44c477eb61acb9f24dd76373c92628fbe41cba45a`;
- media-worker health OK with local `Xenova/siglip-base-patch16-224`;
- n8n `/healthz` OK;
- PostgreSQL healthy;
- exactly the three project services remain running.

Live production HTTP boundary proof used four contiguous `2 s` semantic timed beats and no TTS/job creation. `POST http://127.0.0.1:3001/visual/discover` returned HTTP 200, `segmentation_version=semantic-visual-segments-v3`, four visual segments, candidate counts `62/62/61/62`, provider errors `0`. Marker `LIVE_HTTP_SEMANTIC_DISCOVERY_PASS`.

This closes the verified adapter root cause without provider changes, threshold weakening, workflow changes, DB changes or retries.

## Current boundary

M8 human accepted remains `2/10`. The HTTP adapter fix is saved in GitHub and deployed with rollback/live HTTP proof.

The next allowed action is exactly one completely fresh `как работает индукционная плита / uk / 60` production job. Never reuse `cb98ad2b-1aaa-4117-918d-8fef22940945` or any earlier consumed-Edge job. Require full machine proof through `review_ready`; any new consumed-Edge product failure stops M8 again. If machine PASS, give the exact video to the user and do not increment M8 until human acceptance.

## 2026-09-03 — Fresh UK/60 PRODUCT FAIL: visual_shots selection-score schema mismatch

Fresh production job `44101dd9-d7d6-4fa7-b62b-908ecfaf0f28`, `как работает индукционная плита / uk / 60`, was created by exactly one intake call (matching job count `4 -> 5`). It is consumed and must never be retried/reused.

Machine facts:

- HTTP intake `201`;
- exactly one Edge synthesis persisted: `microsoft_edge_readaloud`, `edge_neural`, `uk-UA-OstapNeural`, measured `57.216 s`;
- 18 timed beats persisted;
- semantic-v3 HTTP adapter correction was exercised successfully: 10 durable `visual_segments` were persisted, proving the earlier `timed_beats` adapter defect is closed;
- WF04 execution `10856` failed while persisting visual shots;
- final state `failed|visuals`;
- `visual_segments=10`, `visual_shots=0`, no final video.

Exact PostgreSQL failure from execution data:

`new row for relation "visual_shots" violates check constraint "visual_shots_score_check"`.

The failing shot 4 row had `selection_score=-0.006621`.

Verified systemic root cause is a schema/producer contract mismatch:

- migration 015 defines `visual_shots_score_check CHECK (selection_score >= 0 AND selection_score <= 2)`;
- WF04 intentionally persists `selection_score = selection_utility`;
- WF04 computes `selection_utility = local_rank_score + min(metadata_overlap,5)*0.018 - representation_preference_rank*0.025`;
- `local_rank_score` is validated in `[0,1]` and `representation_preference_rank` is in `[0,4]`, so the current deterministic utility domain can legitimately extend to `-0.10`; current theoretical upper bound is `1.09`;
- negative utility is therefore not an invalid SigLIP score and is not a visual-quality acceptance failure; it is a relative assignment utility after deterministic representation penalties;
- the assignment beam is allowed to select such a candidate when it is the best sequence-compatible choice under unchanged perceptual diversity constraints.

The DB lower bound is stale for the semantic-v3 selection-utility semantics. No provider change, candidate inflation, retry, topic hack, SigLIP threshold change, perceptual threshold weakening or reuse of this consumed job is justified.

M8 remains stopped at `2/10`.

Next action: add an additive migration 016 that aligns the `visual_shots.selection_score` constraint with the actual deterministic selection-utility domain; add regression covering a real negative-but-valid utility such as `-0.006621` plus out-of-domain rejection; prove migration on disposable PostgreSQL; record proof; deploy migration only with bounded rollback/schema proof; then and only then create one different fresh UK/60 job.


## 2026-09-03 — Migration 016 local/disposable proof PASS

Systemic schema correction was implemented without changing WF04 ranking, provider behavior, candidate pools, SigLIP thresholds or perceptual quality gates.

Local commit `ad657994f910f4d2797688d290bd94a83de96d09` adds:

- `db/migrations/016_visual_shot_selection_utility.sql`;
- `tests/visual_shot_selection_score_regression.mjs`.

Migration 016 replaces only `visual_shots_score_check` with the producer-aligned deterministic utility domain `selection_score >= -0.10 AND selection_score <= 1.09`, and documents the column semantics.

Static regression PASS: `VISUAL_SHOT_SELECTION_SCORE_REGRESSION_PASS`. It verifies the exact WF04 utility formula, persistence wiring, theoretical endpoints `-0.10` and `1.09`, the real failed-job value `-0.006621`, and out-of-domain examples. `git diff --cached --check` PASS.

Disposable PostgreSQL 18 proof applied `db/init/001_init.sql`, every migration 002..016 in order, and then reapplied 016. Final constraint definition was `CHECK (((selection_score >= '-0.10'::numeric) AND (selection_score <= 1.09)))`. A minimal valid semantic-v3 shot with `selection_score=-0.006621` inserted successfully and retained that value. Updates to `-0.100001` and `1.090001` were both rejected by the check constraint. Marker `VISUAL_SHOT_SELECTION_SCORE_PG18_PROOF_PASS`.

The first disposable attempt observed the temporary bootstrap Postgres server and then failed during the image's normal shutdown/restart initialization phase. That result was invalid harness evidence. Corrected readiness waited for `PostgreSQL init process complete; ready for start up.` and then a successful SQL probe before executing product migrations. No production mutation occurred during either disposable attempt.

GitHub synchronization preserved remote docs history via non-force fast-forward commit `3e648b5aa6f7d357e90e8e3284f5642e4c73b4da`. Exact remote blobs:

- migration 016 `f03b26d3daceb741258b3a8a5291984d69ef40fe`;
- regression `4742f563c2299a5f443971daae2602c570540cf7`.

Current boundary: migration 016 is code-proven and saved in GitHub but is not yet applied to production. No new production job is allowed before bounded schema rollback capture, active-execution check, migration-only deploy, live constraint proof and GitHub state update.


## 2026-09-03 — Migration 016 production deploy PASS

Before production mutation, active n8n execution count was `0`; exactly three project services were running and healthy. Bounded rollback snapshot was created and SHA256-verified at:

`/opt/ai-short-form-content-factory/rollback/20260903T150109Z-pre-visual-shot-score-016`

Snapshot records the exact old constraint `visual_shots_score_check = CHECK (selection_score >= 0 AND selection_score <= 2)`, an empty `visual_shots` score state (`0|NULL|NULL`), table schema, runtime state, migration SHA, and guarded rollback SQL that restores `[0,2]` only when no out-of-old-domain rows exist.

Production migration source SHA256 matched local: `8abdfd3e882a047784af05dc6fb91b2886c1b0f143de4c218629bfd4ef122317`. Only `db/migrations/016_visual_shot_selection_utility.sql` was staged into production and applied with `psql -v ON_ERROR_STOP=1`; transaction output was `BEGIN / ALTER TABLE / ALTER TABLE / COMMENT / COMMIT`. No n8n, media-worker or workflow restart/redeploy occurred.

Live post-deploy constraint:

`visual_shots_score_check|CHECK (((selection_score >= '-0.10'::numeric) AND (selection_score <= 1.09)))`

Live column comment states the deterministic semantic-v3 selection-utility semantics and domain `[-0.10,1.09]`. PostgreSQL remained healthy; n8n `/healthz` OK; media-worker `/health` OK with local SigLIP; exactly three project services remained running; active executions remained `0`.

This closes the verified `visual_shots.selection_score` schema/producer mismatch. No visual quality gate, provider behavior, candidate pool, SigLIP threshold or workflow logic changed. M8 remains `2/10` pending a completely fresh production job.


## 2026-09-03 — Fresh UK/60 PRODUCT FAIL: segment-ready CTE snapshot defect

Fresh production job `5cbe2459-291b-4aa7-b9e8-b1ed5cddac51`, `как работает индукционная плита / uk / 60`, was created by exactly one intake call (matching count `5 -> 6`). It is consumed and must never be retried/reused.

Machine facts:

- HTTP intake `201`;
- exactly one Edge synthesis: `microsoft_edge_readaloud`, `edge_neural`, `uk-UA-OstapNeural`, measured `57.216 s`;
- 18 timed beats persisted;
- 10 semantic visual segments persisted;
- migration 016 correction worked: all 10 visual shots persisted, including shot 4 `selection_score=-0.006621`;
- visual sequence metrics themselves passed: 9 clusters / required 5, 10 unique assets / 10 shots, adjacent duplicates 0, max cluster occurrence 2, max cluster duration share `0.24496644295302013423`, max shot `7.278 s`;
- WF04 execution `10881` failed at semantic completion with `segments=0/10`;
- all 10 durable `visual_segments.status` values remained `planned`;
- final state `failed|visuals`, no final video.

Verified systemic root cause is PostgreSQL data-modifying CTE snapshot semantics in WF04 `Persist Visual Result`, not a visual-quality failure.

The statement currently performs `inserted AS (INSERT INTO visual_shots ... RETURNING id)` followed by `completed AS (UPDATE visual_segments ... WHERE (SELECT count(*) FROM visual_shots WHERE visual_segment_id=vs.id)=planned_shot_count)`. The table scan inside the same statement uses the statement snapshot and does not see the row written by the sibling `inserted` CTE. Therefore for a one-shot segment the count is still `0`, the shot commits successfully, but the segment never becomes `ready`. `Require Persisted Visuals` checks shot persistence only; `Verify Visual Completion` later correctly detects `ready_segment_count=0/10` and fails closed.

Disposable PostgreSQL 18 proof reproduced the exact semantic behavior: first statement reported `inserted_cte_rows=1`, `table_scan_same_statement=0`, `completed_rows=0`, then after statement `status=planned` with one visible shot. A corrected form that counts pre-statement existing rows plus rows from the `inserted ... RETURNING` CTE reported `completed_rows=1` and `status=ready`. Marker `DATA_MODIFYING_CTE_SNAPSHOT_PROOF_PASS`.

Systemic correction must make `inserted` return `visual_segment_id` and mark completion only when the current insert exists and `existing snapshot rows + current inserted rows = planned_shot_count`. This also supports a future two-shot segment: first insert leaves it planned; second insert sees one prior row plus one current `RETURNING` row and marks it ready. No retry, provider change, quality-threshold change, topic hack or reuse of this consumed job is justified.

M8 remains stopped at `2/10`. Next action: correct the general WF04 persistence SQL, add a regression that covers one- and two-shot lifecycle semantics plus the data-modifying-CTE contract, prove on disposable PostgreSQL, save to GitHub, deploy WF04 only with rollback/live equality, then create a completely fresh job.


## 2026-09-03 — WF04 segment-completion fix local/GitHub proof PASS

Systemic correction for the verified data-modifying-CTE snapshot defect is implemented in local commit `ec07952d3b807656e0ef8b7fbcde85fa9d6450c2` and synchronized to GitHub non-force commit `02e1679285fb34d786a9aa3b677f3dd39bec7eea`.

Only two files changed:

- `n8n/workflows/WF04-visual-sourcing.json`;
- `tests/wf04_segment_completion_regression.mjs`.

`Persist Visual Result` now makes `inserted` return `visual_segment_id`, requires the current insert to exist, and marks a segment ready only when `pre-statement existing shot count + current inserted RETURNING count = planned_shot_count`. Ranking, providers, media discovery, SigLIP, perceptual quality gates, migration 016 and render behavior are unchanged.

Focused proof PASSed: `WF04_SEGMENT_COMPLETION_REGRESSION_PASS`, WF04 runtime-v3, assignment-v3, perceptual assignment-v3, download-v3, rank-query-v3, representation relevance-v3, final-design gate, and `git diff --check`. Explicit compile proof: `CODE_NODE_COMPILE_PASS 41 v24.20.0` and `STUDIO_JS_COMPILE_PASS`.

The exact SQL string extracted from the corrected WF04 was executed on disposable PostgreSQL 18 after applying init + migrations 002..016. Results:

- one-shot segment: insert `persisted=true`, `segment_completed=true`, durable state `ready|1`;
- duplicate same shot: `persisted=false`, `segment_completed=false`;
- two-shot segment first insert: `persisted=true`, `segment_completed=false`, durable state `planned|1`;
- second insert: `persisted=true`, `segment_completed=true`, durable state `ready|2`.

Marker: `WF04_EXACT_PERSIST_SQL_PG18_PASS`. An earlier diagnostic attempt used `PREPARE` and `EXECUTE` in separate psql sessions and failed with `prepared statement "persist" does not exist`; that was invalid harness evidence. Correct proof used one psql session.

Exact GitHub blobs equal local commit blobs:

- WF04 `9480840875fc15cff8b43a6c5e3fbf90586bec54`;
- regression `48a9957368751235ce2d470e3fbafe07a47e094e`.

No production workflow, DB, service or job was mutated during correction/proof. Active n8n executions were `0` at the predeploy boundary. Next action is bounded live-WF04 rollback capture, WF04-only publish, source/live equality and runtime proof; only after that may one completely fresh UK/60 production job be created.


## 2026-09-03 — WF04 segment-completion production deploy PASS

WF04-only deployment used the already proven path: active executions `0`, corrected source core verified, production filesystem WF04 replaced from local clean commit `ec07952d3b807656e0ef8b7fbcde85fa9d6450c2`, `n8n import:workflow`, current-core verification before publish, `n8n publish:workflow --id=M6VisualSourcing1`, then exactly one n8n restart because the CLI explicitly reported restart was required.

Post-deploy proof:

- production WF04 file SHA256 `62293e502318fab4b33895d009325632e0ca157ed3a6c963f6b8cc7a63d98442`;
- corrected source / production file / current export / published export canonical core SHA256 all `6dbbc0558d107d2facf9bb0a84c614b926df407eb8061ac9330776fe95d31a3e`;
- published/current workflow both active, 27 nodes, `versionId=activeVersionId=c6d2e89a-213d-4bd8-9d21-57640f066bb1`;
- WF05 remained active at `ae9d00c2-bd65-4d3f-a8f5-ec0bcf840a12`;
- WF02 remained active at `5885ad1b-7ce3-4244-9ac3-633fec020c73`;
- WF03 remained active at `010fb1d6-a8cd-4ccc-8094-d6f9e61bc28d`;
- WF06 remained active at `89d14a25-426f-47a1-832a-2a510b686144`;
- migration 016 constraint remained `selection_score >= -0.10 AND selection_score <= 1.09`;
- PostgreSQL healthy, n8n `/healthz` OK, media-worker `/health` OK, exactly three project services;
- active executions after deployment `0`.

Rollback remains `/opt/ai-short-form-content-factory/rollback/20260903T155712Z-pre-wf04-segment-completion`. No WF02/WF03/WF05/WF06, media-worker, PostgreSQL schema, provider, quality threshold or candidate-pool behavior was changed.

The verified CTE snapshot root cause is now closed in production. Next allowed action is exactly one completely fresh `как работает индукционная плита / uk / 60` job.

## 2026-09-05 — spoken-separator and unreviewed-visual fallback root cause

Production evidence from jobs `043c10a6-4d9d-4948-bc0d-64237429e749` and `cc1141d8-03a3-4825-ac96-281812737a7a` proved two general acceptance defects. First, model-written slash separators leaked into persisted narration and were pronounced by TTS. Second, WF04's multimodal reviewer approved fewer images than the planned shot count, after which `Require Multimodal Visual Selection` padded the segment with local candidates that were not model-approved; the stored recovery pool could include candidates that were never shown to the multimodal reviewer. This directly produced random-looking images despite a correct semantic target.

The correction removes formatting separators from spoken narration before persistence/rewrite, adds a WF03 fail-closed speech-safety gate, restricts WF04 eligibility to actually reviewed candidates, and removes unreviewed visual fallback. Insufficient multimodal approvals now fail closed. Regression gate: `20/20` Node + `11/11` Python PASS before deployment.

## 2026-09-05 — exact-beat visual sourcing root cause and correction

Production inspection of fresh 15 s hydro job `fd510f8e-21b3-4f2d-a992-2cc5f21e81a0` confirmed the user's report that visuals could appear random even though final visual queries existed. The final narration beat `Так сила воды питает наши дома.` had the correct stored query `modern residential house exterior at night with glowing interior lights`, but media discovery prefixed the overall canonical topic. Pixabay rejected the long combined request with HTTP 400. Because timed discovery still mixed generic topic-level candidates into each segment, hydroelectric-plant images survived into the exact homes beat and the multimodal reviewer accepted them as contextual filler.

A second ordering defect was confirmed in source: the 6/10/14/18 final narration queries were passed into semantic segmentation, but a merged segment used only `groundedQueries[first_scene_number - 1]`. Therefore later beats inside that segment had no independent search target even though c6a14a7/WF03 had correctly generated one query per final beat.

Systemic correction:

- production timed visual segmentation becomes one-to-one with accepted final narration beats (`narration-beat-visual-segments-v4`);
- each beat keeps its exact final English query and owns its candidate pool;
- beats >= 1.8 s plan two distinct still shots;
- exact beat query is sent directly to providers and bounded to a safe transport length;
- no generic topic-level stock/canonical-media fallback is mixed into timed pools;
- Pexels search is photo-first (`/v1/search`);
- provider searches execute concurrently with bounded cross-beat concurrency;
- multimodal review cannot use topic anchors or unreviewed recovery candidates and must approve the required exact-beat stills or fail closed.

Automated regression after the change: 21 Node tests + 11 Python tests PASS, workflow JSON PASS and `git diff --check` PASS. New `visual_discovery_exact_segment_query_regression.mjs` verifies exact query transport, <=90-character provider query bound, no canonical-topic prefix/base stock in timed mode, Pexels photo results and concurrent search execution.

A real-provider diagnostic using the exact failed 60 s cloud/rain context completed 18 Commons/Pixabay/Pexels beat searches in 5.726 s, with `narration-beat-visual-segments-v4`, 18 segments, 36 planned stills and zero provider errors. This replaces the earlier >120 s sequential discovery failure class with bounded concurrent discovery. No production workflow/service was changed by this diagnostic; deployment remains gated on GitHub synchronization and post-deploy E2E MP4 review.
