# Engineering History — Rebuild

Chronological durable record for material changes, failures, verified root causes, regressions, deploys and rollback facts. `docs/CURRENT_STATE.md` remains the operational source of truth.

Compacted on 2026-09-03 while preserving every material production failure, accepted result, systemic correction, rejected approach, deployment/rollback fact and diagnostic mistake that could otherwise cause a false PASS/FAIL after context reset. Exact code history remains recoverable from listed commits and rollback snapshots.

## 2026-09-02 — Old induction machine PASS invalidated

Job `13f64c50-8dd5-47e4-a88f-1411d258e7c4` reached `review_ready`, but human inspection showed only two effective visual states. Previous machine PASS is permanently invalidated. Root cause: acceptance counted scene/file presence rather than actual video-level perceptual sequence quality. Never reuse this job as acceptance evidence.

## 2026-09-02 — Visual-quality-v2 rewrite/deploy

Required visual path became:

`timed beat + evidence -> deterministic search intents -> multi-source discovery -> metadata/provenance eligibility -> local SigLIP ranking + perceptual identity -> global assignment -> sequence gate -> persist -> render -> post-render pixel-state gate -> review_ready`.

Six-beat contract: every beat truth-eligible; at least five perceptual clusters; zero adjacent duplicates; no cluster over `0.34` total duration share; non-finite metrics fail closed; rendered midpoint frames independently satisfy required state count.

Cross-topic dry-runs without threshold weakening: EN induction 6 clusters/max `0.1813`; PL combustion engine 5/max `0.3333`; RU refrigerator 6/max `0.1667`; UK volcano 6/max `0.1667`.

Commit `f7c4096503c9620910b387129a5a06cce4d26d42` — `redesign: enforce perceptual visual diversity`.
Rollback `/opt/ai-short-form-content-factory/rollback/20260902T175543Z-pre-visual-quality-v2`.
Migration 013 applied; WF04/WF05 published; exactly three project services and PostgreSQL healthy.

Diagnostic mistake preserved: an early compile harness treated a top-level-array workflow export as an object. A zero-count Code-node compile can never be accepted as PASS.

## 2026-09-02 — Reference-media lifecycle failure/fix

Fresh job `1afc307d-aaac-4eed-8387-b05e1b6721eb`, WF04 execution `9902`, failed after its one Edge synthesis because planner persisted fake `reference_media_kind=mixed` and violated the DB constraint.

Systemic correction: `visual_planned + technical_reference` keeps `reference_media_kind=NULL`; `visual_ready` persists actual `photo|diagram|animation`.

Commit `b83bf6d48f1df259c7c6fa0136748ca10d13f1af` — `fix: align reference media kind lifecycle`.
Rollback `/opt/ai-short-form-content-factory/rollback/20260902T181813Z-pre-reference-media-kind-lifecycle`.
Migration 014 live; WF04 live equality proved; runtime healthy.

## 2026-09-02 — M8 #2 induction MACHINE + HUMAN PASS

Accepted fresh job `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`, `How does induction heating work? / en / 15`.

Machine proof: `review_ready`; preflight `14.358 s`; execution `9926` exactly one successful Edge synthesis; measured voice `13.944 s`; six timed beats; 6/6 perceptual clusters, required 5; adjacent 0; max share `0.1813`; post-render six states; ffprobe H.264 1080x1920 30fps + AAC 48kHz stereo. User watched the exact video and said `мне нравится`. M8 accepted count became `2/10`.

## 2026-09-02/03 — WF02 multilingual retrieval failure and systemic correction

Observed failures:

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
- duration bands unchanged.

Final real-Wikipedia proof: RU-topic -> UK induction cooktop `60.106 s`; UK refrigerator `59.975 s`; PL popcorn `15.079 s`; EN induction `14.939 s`, all pre-TTS safe. Seven new regressions PASS; WF02 Code compile 8/8; staged pipeline PASS; retained duration audit 150 rows / 40 safe / 0 false-safe; CASE1 staged provenance PASS; CASE1 visual eligibility PASS.

Diagnostic harness mistake preserved: an initial CASE1 visual invocation passed `-e never` as Node input and produced `ReferenceError`; that result was invalid. Correct invocation passed.

Commit `e4e856093fa237dab9daaa56dcf443c3b6155f93` — `fix: make factual retrieval multilingual and explanation-aware`.
Rollback `/opt/ai-short-form-content-factory/rollback/20260903T055250Z-pre-wf02-multilingual`.
WF02-only production deploy PASS; live core SHA `0f5893ffba59b23d181c363b26b991450e3fc016a52016e1ec686797dbfe23c1`; no retry/maxTries; three services healthy.

## 2026-09-03 — Fresh UK/60 production failure exposes visual-unit mismatch

Fresh real intake job `4372be34-c417-415f-92f6-63481b3b5686`, topic `как работает индукционная плита`, output `uk`, target 60, returned HTTP 201.

It passed corrected WF02 and its single Edge synthesis: canonical factual title `Індукційна плита`; preflight `60.106 s`; measured voice `57.216 s`; voice `uk-UA-OstapNeural`; 18 timed beats.

Old WF04 then failed at visuals with exact error `perceptually unique truth-eligible assignment 11/12 [line 15]`. Final state `failed|visuals`. Never retry/reuse this job because its automatic Edge call was already consumed. M8 progression stopped.

## 2026-09-03 — Semantic visual segmentation selected

Broader review of multiple open-source short-video architectures led to the systemic correction: timed narration/subtitle beats are transport units and must not automatically become independent semantic media-search obligations.

Design document `docs/VISUAL_SEGMENTATION_DESIGN.md`, initial commit `d19ff9e66f47cbadf206141d4b51bbc3d7631abc`.

New path:

`accepted voice -> timed beats -> deterministic semantic visual segments -> visual shots -> truth eligibility -> local SigLIP -> perceptual sequence control -> render -> post-render frame gate -> human review`.

No generative visual planner, hosted semantic dependency, paid fallback or threshold weakening. WF01-WF03 and exactly-one-Edge remain unchanged. Additive durable entities: `visual_segments`, `visual_shots`, `media_library_assets`.

## 2026-09-03 — GitHub/VPS branch divergence discovered

VPS/local code and GitHub `rebuild/simple-pipeline` documentation history diverged from merge base `7d25bac1c4d1a90b2b29183d9ec3ca280d1acfc4`.

- VPS code HEAD `e4e856093fa237dab9daaa56dcf443c3b6155f93`.
- GitHub had a separate docs chain.
- `git merge --ff-only` correctly refused.
- VPS HTTPS push had no credentials; SSH authentication also failed.
- no force push/destructive rewrite attempted.

GitHub implementation branch `rebuild/semantic-visual-segments` was created from remote source-of-truth. VPS implementation branch `rebuild/semantic-visual-segments-local` was created from actual production-code HEAD. Final reconciliation must use GitHub connector writes while preserving remote documentation history.

## 2026-09-03 — Semantic-v3 local implementation

Local-only implementation, production not mutated:

- `services/media-worker/src/visual-segmentation.mjs` — deterministic semantic grouping;
- `db/migrations/015_visual_segments.sql` — additive `visual_segments`, `visual_shots`, `media_library_assets`;
- WF04 rewritten around semantic segments and shot assignment;
- media-worker adds `/visual/store-shot` and `/render-v3` while retaining legacy routes;
- WF05 reads independent subtitle-beat and visual-shot timelines;
- post-render midpoint frames independently verify actual states.

A Code-node mode defect was caught: `Require Visual Completion` was `runOnceForEachItem` while using `$input.first()`. It was corrected to use `$json`; mode regression passed.

Earlier regression-fixture mistakes preserved: one test incorrectly expected a rejected sequence evaluator to throw; another made a declared PASS impossible under `0.34`; another offered insufficient perceptual states. Fixtures were corrected; no production threshold changed.

## 2026-09-03 — Duration-driven shot cardinality rejected

First semantic implementation correctly reduced the `57.216 s` / 18-beat UK fixture to 9 semantic segments, but `planned_shot_count = ceil(segment_duration / 5.0)` expanded them back to 17 mandatory shots and assignment required unique asset IDs. Real-provider dry-run failed `No valid semantic visual shot assignment at shot 12/17`.

Verified root cause: the 5-second timer recreated the old cardinality problem in another form. It was rejected systemically. A semantic segment normally becomes one shot; another shot may exist only for a deterministic semantic/representation transition. File-ID uniqueness is not a proxy for product-visible diversity. Perceptual identity and post-render states remain authoritative.

No candidate-pool inflation, retries, topic mappings, threshold changes or production writes were used.

## 2026-09-03 — Corrected UK/60 real-provider semantic dry-run PASS

After removing elapsed-time shot multiplication and hard asset-uniqueness as a product gate, exact persisted job `4372be34-c417-415f-92f6-63481b3b5686` was replayed read-only through local semantic sourcing with real Wikimedia/Pixabay/Pexels plus existing local SigLIP.

PASS:

- 18 timed beats -> 10 content-derived semantic segments -> 10 shots;
- every segment had a 10-candidate truth-eligible pool in that run;
- clusters 9, required 5;
- adjacent duplicates 0;
- max cluster occurrence 2;
- max cluster duration share `0.245`;
- longest semantic shot `7.278 s`;
- provider errors 0;
- full `57.216 s` coverage;
- runtime remained exactly three production services.

A diagnostic harness initially hardcoded an expected 9 segments and falsely failed when exact persisted narration produced 10. That assertion was removed because segment count is content-derived, not fixture-hardcoded.

## 2026-09-03 — Short-video cross-topic failure exposes mathematical `0.34` conflict

Cross-topic real-provider testing on already accepted zipper job `227c8a50-ef1a-49e5-8d26-fdb40f663c83` initially failed `No valid semantic visual shot assignment at shot 1/3`.

Exact cause was not provider shortage. Voice duration is `15.480 s`, so unchanged `0.34` permits one perceptual state for at most `5.2632 s`. Initial semantic groups were:

- `5.546 s` = `35.83%`;
- `5.355 s` = `34.59%`;
- `4.579 s` = `29.58%`.

The first two segments were mathematically incapable of passing `0.34` even with perfect distinct assets.

Systemic correction: segmentation is now quality-constrained while remaining semantic and beat-boundary preserving:

`effective_max_segment_seconds = min(8.5, accepted_voice_duration * 0.34)`.

A timed beat itself is never split just to make visuals pass; if one beat exceeds the effective cap, fail closed. Elapsed time still does not create extra shots. Segmenter version is now `semantic-visual-segments-v3`.

Exact zipper regression now gives five semantic segments, each one shot, all below the unchanged `5.2632 s` cap. The UK/60 fixture remains nine segments/nine shots in the pure segmentation fixture because its quality cap is above the normal `8.5 s` semantic maximum.

## 2026-09-03 — Quality-constrained semantic-v3 focused suite PASS

After the correction, the focused/static suite PASSed:

- semantic segmentation: UK `9/9`, zipper five segments with cap `5.2632`, same-duration fixtures still produce different content-derived segment counts;
- visual-shot quality-v3 PASS, including legal non-adjacent asset reuse;
- WF05 visual-segments-v3 contract PASS;
- visual discovery compatibility PASS;
- legacy visual-quality-v2 regression PASS;
- WF04 Code-node runtime-v3 PASS;
- WF04 global assignment-v3 PASS;
- WF04 perceptual assignment-v3 PASS;
- WF04 download/store expansion-v3 PASS;
- rank-query contract PASS at 200 chars;
- representation relevance/truth-eligibility PASS;
- Code-node compile `41` PASS on Node v24.18.0;
- Studio inline JS compile PASS;
- Code-node mode regression PASS.

Runtime before/after remained exactly three project services, n8n/media HTTP 200 and PostgreSQL healthy.

Diagnostic execution mistakes preserved because they could otherwise be misread as product failures:

1. `docker exec ... node /project/tests/...` failed `MODULE_NOT_FOUND` because the repository is not mounted into the live n8n container.
2. A disposable n8n image was started without overriding its entrypoint, so `node` was interpreted as an n8n command and returned `Command "node" not found`.
3. First disposable real-provider harness mounted a mode-600 temp context file; container user got `EACCES`. Corrected to readable temp fixture.

None was product/runtime evidence.

## 2026-09-03 — Real-provider cross-topic semantic-v3 gate PASS

Reusable local harness `tests/semantic_visual_real_provider_dry_run.mjs` replays exact persisted contexts read-only through local discovery, current local WF04 Code nodes, real Wikimedia/Pixabay/Pexels and the existing local SigLIP endpoint.

PASS cases:

1. accepted zipper `227c8a50-ef1a-49e5-8d26-fdb40f663c83`: `15.480 s`, six timed beats -> five segments/shots; cap `5.2632`; max shot `4.579`; clusters 5/required 3; adjacent 0; max occurrence 1; max share `0.2958`; providers Pexels + Wikimedia; provider errors 0.
2. accepted induction `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`: `13.944 s`, six beats -> four segments/shots; cap `4.741`; max shot `4.705`; clusters 4/required 2; adjacent 0; max occurrence 1; max share `0.3374`; providers Wikimedia; provider errors 0.
3. failed old-visual UK induction `4372be34-c417-415f-92f6-63481b3b5686` used read-only as factual/timing fixture: `57.216 s`, 18 beats -> 10 segments/shots; effective cap `8.5`; max shot `7.278`; clusters 9/required 5; adjacent 0; max occurrence 2; max share `0.245`; providers Pexels + Pixabay + Wikimedia; provider errors 0.

No retry, threshold weakening, topic hack, candidate-pool inflation or production write occurred.

## 2026-09-03 — Disposable render-v3 long-semantic-shot proof

A disposable image built from current local media-worker code was tested with a temporary DATA_ROOT and did not replace production.

First synthetic attempt used flat solid-color images. Average-hash perceptual identity is primarily spatial/luminance-pattern based, so some flat colors collapsed into the same rendered state. `/render-v3` correctly returned 422: `Rendered shot states failed: states=3/2, adjacent=1, max_occurrence=2, max_share=0.5`. This was an invalid synthetic fixture, not product evidence.

The corrected fixture used four spatially distinct black/white patterns, a `24 s` WAV, six subtitle beats and four visual shots of exactly `6 s` each.

HTTP 200 PASS:

- H.264/yuv420p 1080x1920;
- AAC 48 kHz stereo;
- container/video/audio duration `24 s`;
- four 6-second shot timings accepted;
- pre-render clusters 4/required 2, adjacent 0, max share `0.25`;
- `max_shot_duration_seconds=6`, proving there is no artificial 5-second shot-duration gate;
- rendered states 4/required 2, adjacent 0, rendered max share `0.25`;
- output bytes `702968`;
- production service count remained exactly three before/after.

## 2026-09-03 — Semantic design documentation aligned

`docs/VISUAL_SEGMENTATION_DESIGN.md` was updated to the proven contract in commit `61cfb69f4f821154cc5a47f72b8c0634b250f74c`:

- one shot per semantic segment by default;
- additional shot only for deterministic semantic/representation transition;
- quality-constrained semantic maximum `min(8.5, T*0.34)` on existing timed-beat boundaries;
- no hard 5-second shot-duration rule;
- asset-file uniqueness is not product-visible diversity;
- perceptual adjacency/occurrence/duration-share and post-render state gates remain authoritative.

## Current deployment boundary

Semantic-v3 is **not deployed yet**. Migration 015 is not live; WF04/WF05 semantic versions are not published; production media-worker has not been replaced. Production remains on the existing visual-quality-v2 deployment with WF02 multilingual fix. M8 remains `2/10`.

Before deployment:

1. synchronize all semantic-v3 implementation/tests/migration to GitHub branch `rebuild/semantic-visual-segments` while preserving the documented branch divergence;
2. prove GitHub/local code equality;
3. take a bounded rollback snapshot of current live WF04/WF05/media-worker/DB state;
4. apply migration 015 and deploy only the intended semantic visual components;
5. verify live equality and exactly three healthy services;
6. create a completely fresh RU-topic -> UK/60 production job; never reuse `4372be34...`, `85fcc63b...` or `e1399581...`;
7. require exactly one Edge call, semantic-v3 machine gates, ffprobe and `review_ready`;
8. require user to watch the exact fresh video before changing M8 accepted count.

## 2026-09-03 — Semantic-v3 implementation synchronized to GitHub

The clean local rebuild is at `2405d0431ff2007b52825b273267d07fad9f68ce` (`redesign: separate semantic visual segments from timed beats`) on `rebuild/semantic-visual-segments-local`. No force push or history rewrite was used.

GitHub branch `rebuild/semantic-visual-segments` was completed through connector writes while preserving the remote documentation history. Material sync commits in this continuation include:

- `62fef92819b6093ec0f876e112ff44752feb9f8e` — align `visual-quality.mjs` with the local semantic-v3 evaluator;
- `c62fd62591db6c9594066fb82881da049437a7ce` — add semantic-v3 WF05;
- `bc1f6515eab5fc449af5b4ef6500530caca52232` — add semantic-v3 WF04;
- `602ab214035a051e41a47394d0b0db31b6e5cc1e` — add semantic-v3 `media-worker/server.mjs`.

Cross-check of all 17 semantic-v3 implementation/migration/test files against local `2405d04` found 16 exact Git blob matches. `services/media-worker/src/server.mjs` differs only by the final newline at EOF: remote blob `5898e7fb53c9c054e62c2cde0b4202be88efd2ba`; appending one `LF` to the remote bytes produces the exact local blob `a07fb3396602a0923fa081c022cd3739f6076caf`. `diff -u` reports no source-code difference beyond `No newline at end of file`.

This EOF normalization difference is not a semantic implementation difference and must not be mistaken for a code divergence. Production was not changed by this GitHub synchronization. Fresh runtime inspection still showed n8n `/healthz` OK and media-worker `/health` OK on its actual bound port `3001`.

Next boundary remains pre-deploy documentation alignment and bounded deployment gates; no fresh production job is allowed before those gates and rollback proof are complete.

## 2026-09-03 — Semantic-v3 source-of-truth documentation aligned

`docs/ARCHITECTURE.md` was updated in commit `b71ce862a606b1010625912c4ba07b8f600d8b56` to remove the obsolete `one visual per timed beat` contract and document the proven semantic-v3 architecture: timed beats remain subtitle/voice transport units; semantic visual segments are independent meaning-based visual obligations; visual shots have their own contiguous timeline; render-v3 validates actual post-render visual states.

`docs/CURRENT_STATE.md` was updated in commit `f0f80836a6666b83502f6b74163936ff1a83ad85` and now makes the deployment boundary explicit:

- clean local semantic-v3 implementation HEAD is `2405d04`;
- GitHub implementation synchronization is complete modulo the proven EOF newline normalization in `server.mjs`;
- semantic-v3 is not deployed yet;
- migration 015 is not live;
- production WF04/WF05/media-worker still use the old visual-quality-v2 path;
- M8 remains `2/10` human-accepted;
- no fresh M8 production job may start before pre-deploy proof and a bounded rollback snapshot.

Fresh runtime inspection after the documentation writes still returned n8n health OK, media-worker health OK and a clean rebuild worktree. The next boundary is pre-deploy diff/migration proof; no architecture rewrite is justified by current evidence.

## 2026-09-03 — Pre-deploy diff and migration 015 disposable proof

Full local diff review from production-code base `e4e856093fa237dab9daaa56dcf443c3b6155f93` to semantic-v3 `2405d0431ff2007b52825b273267d07fad9f68ce` found exactly the expected 17 semantic-v3 files. `git diff --check` returned 0. No `compose.yaml`, WF02 or WF03 changes are present in this implementation diff.

Migration `db/migrations/015_visual_segments.sql` was then tested against a disposable `postgres:18-alpine` container; production DB was not mutated.

The first disposable harness produced `psql: connection ... /var/run/postgresql/.s.PGSQL.5432 failed`. This was a diagnostic harness race, not a migration failure: the Unix-socket readiness probe could succeed against PostgreSQL's temporary init server, after which the entrypoint shuts that server down before starting the final TCP listener. The corrected harness waits for `pg_isready -h 127.0.0.1`, which cannot succeed against that temporary socket-only init server.

Corrected disposable proof PASS:

- migration 015 applied successfully;
- second application also completed successfully; `CREATE TABLE/INDEX IF NOT EXISTS` operations skipped existing objects as intended;
- `visual_segments`, `visual_shots`, `media_library_assets` all exist;
- 11 indexes were present across the three tables;
- valid job -> segment -> library asset -> shot insertion succeeded;
- deleting the job cascaded `visual_segments=0` and `visual_shots=0` while the reusable `media_library_assets` row remained `1`;
- invalid `planned_shot_count=3` was rejected with nonzero psql exit as required by the `BETWEEN 1 AND 2` constraint;
- disposable container was removed afterward;
- production project container count remained exactly three: media-worker, n8n, postgres;
- n8n and media-worker health remained OK.

This closes the missing migration 015 disposable proof. The next production boundary is the bounded rollback snapshot; no production mutation has occurred yet.

## 2026-09-03 — Bounded pre-semantic-v3 rollback snapshot complete

Rollback snapshot created at `/opt/ai-short-form-content-factory/rollback/20260903T134851Z-pre-semantic-v3` before any semantic-v3 production mutation.

Snapshot contains and SHA256-verifies:

- live published WF04 and WF05 exports;
- current production filesystem WF04/WF05 exports;
- current production media-worker Dockerfile, package manifests and complete source directory;
- `compose.yaml`;
- PostgreSQL schema-only dump;
- predeploy DB state showing `visual_segments`, `visual_shots`, and `media_library_assets` all absent;
- runtime image IDs and health metadata.

The pre-deploy media-worker image `sha256:4009376d074a271aced92aa0cde159ee46bb445af6998580e088a5d23137413d` was additionally tagged locally as `ai-short-form-content-factory-media-worker:rollback-20260903T134851Z` for direct rollback.

Snapshot verification passed for every file in `SHA256SUMS`. At snapshot time n8n and media-worker health were OK and PostgreSQL remained healthy.

Diagnostic notes: an initial direct Docker read through SentinelX failed on `/var/run/docker.sock` permissions; the allowed `sudo docker` path immediately proved the containers healthy. Two early snapshot-completion shell commands then stopped on quoting errors before any production mutation; the final structured script completed the same snapshot and verified all files. These were diagnostic/orchestration errors, not product failures.

The rollback requirement is now satisfied. The next allowed step is production migration 015, followed by bounded media-worker and WF04/WF05 deployment with live equality checks before any fresh M8 job.