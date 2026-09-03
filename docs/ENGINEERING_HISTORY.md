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

Diagnostic harness mistake: an initial CASE1 invocation accidentally passed `-e never` as Node input; invalid result. Correct invocation passed.

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

Boundaries remain timed-beat boundaries. A beat is never split just to satisfy visuals; if a beat itself exceeds cap, fail closed. Elapsed time does not create extra shots. Segmenter version `semantic-visual-segments-v3`.

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