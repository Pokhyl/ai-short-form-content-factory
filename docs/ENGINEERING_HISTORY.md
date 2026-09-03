# Engineering History — Rebuild

Durable chronological record for material failures, root causes, rejected approaches, regressions, deploys and rollback facts. `docs/CURRENT_STATE.md` is the operational source of truth. Exact code history remains recoverable from the listed commits and rollback snapshots.

## 2026-09-02 — Old induction machine PASS invalidated

Job `13f64c50-8dd5-47e4-a88f-1411d258e7c4` reached `review_ready`, but human inspection showed only two effective visible states. Earlier machine PASS is permanently invalidated. Root cause: acceptance counted scene/file presence rather than actual video-level perceptual sequence quality. Never reuse as acceptance evidence.

## 2026-09-02 — Visual-quality-v2 rewrite/deploy

Visual path became `timed beat + evidence -> deterministic search -> eligibility -> local SigLIP + perceptual identity -> global assignment -> pre-render gate -> render -> post-render pixel-state gate -> review_ready`.

Six-beat contract: every beat truth-eligible; >=5 perceptual clusters; no adjacent duplicate; max cluster duration share `0.34`; non-finite metrics fail closed; rendered midpoint frames independently satisfy required state count.

Commit `f7c4096503c9620910b387129a5a06cce4d26d42`; rollback `/opt/ai-short-form-content-factory/rollback/20260902T175543Z-pre-visual-quality-v2`; migration 013 live; WF04/WF05 published; three services healthy.

Diagnostic mistake: an early compile harness treated a top-level-array workflow export as an object. Zero Code-node compiles can never be called PASS.

## 2026-09-02 — Reference-media lifecycle failure/fix

Job `1afc307d-aaac-4eed-8387-b05e1b6721eb`, WF04 execution `9902`, failed after its one Edge call because planner persisted fake `reference_media_kind=mixed` and violated DB constraints.

Correction: `visual_planned + technical_reference` keeps `reference_media_kind=NULL`; `visual_ready` persists actual `photo|diagram|animation`.

Commit `b83bf6d48f1df259c7c6fa0136748ca10d13f1af`; rollback `/opt/ai-short-form-content-factory/rollback/20260902T181813Z-pre-reference-media-kind-lifecycle`; migration 014 live.

## 2026-09-02 — M8 #2 induction MACHINE + HUMAN PASS

Job `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`, `How does induction heating work? / en / 15`: exactly one Edge, measured `13.944 s`, six timed beats, six perceptual/rendered states, adjacent 0, max share `0.1813`, ffprobe H.264 1080x1920 30fps + AAC 48kHz stereo. User watched and accepted exact video. M8 became `2/10`.

## 2026-09-02/03 — WF02 multilingual retrieval failure/fix

Observed failures: PL popcorn query over-constrained; job `85fcc63b-b89b-40d0-b253-6383b715f105` RU-topic -> UK/60 failed because old path queried Ukrainian Wikipedia with Russian subject text.

Systemic contract: bounded discovery tokens; probe languages exactly EN/PL/RU/UK requested-first; one Wikipedia request/probe, no retries; official language link for cross-language handoff; no topic mappings/generative translation/provider cascade/gate weakening; mechanism evidence preferred; narration extractive/provenance-preserving; duration gates unchanged.

Real-Wikipedia proof: RU-topic->UK induction `60.106 s`, UK refrigerator `59.975 s`, PL popcorn `15.079 s`, EN induction `14.939 s`; seven regressions PASS; WF02 compile 8/8; retained duration audit 150 rows / 40 safe / 0 false-safe.

Commit `e4e856093fa237dab9daaa56dcf443c3b6155f93`; rollback `/opt/ai-short-form-content-factory/rollback/20260903T055250Z-pre-wf02-multilingual`; live core SHA `0f5893ffba59b23d181c363b26b991450e3fc016a52016e1ec686797dbfe23c1`.

Diagnostic harness mistake: initial CASE1 visual invocation accidentally passed `-e never` as Node input; invalid result, corrected invocation PASS.

## 2026-09-03 — Old WF04 UK/60 failure exposes visual-unit mismatch

Fresh job `4372be34-c417-415f-92f6-63481b3b5686`, `как работает индукционная плита / uk / 60`, passed corrected WF02 and exactly one Edge (`57.216 s`, 18 beats), then old WF04 failed `perceptually unique truth-eligible assignment 11/12`. Never retry/reuse consumed job.

Root cause: timed narration/subtitle beats are transport units and must not automatically be independent visual-search obligations.

## 2026-09-03 — Semantic visual segmentation selected and implemented

Design `docs/VISUAL_SEGMENTATION_DESIGN.md`, initial commit `d19ff9e66f47cbadf206141d4b51bbc3d7631abc`.

New path: `accepted voice -> timed beats -> deterministic semantic visual segments -> visual shots -> truth eligibility -> local SigLIP -> perceptual sequence gate -> render-v3 -> post-render frame gate -> human review`.

Additive durable entities: `visual_segments`, `visual_shots`, `media_library_assets`. WF01-WF03 and exactly-one-Edge unchanged.

Code-node mode bug caught: `Require Visual Completion` used per-item mode with `$input.first()`; corrected to `$json`. Other regression fixture errors were corrected without threshold changes.

## 2026-09-03 — Duration-driven shot cardinality rejected

Initial semantic path turned 9 segments into 17 shots through `ceil(segment_duration / 5.0)` and required unique asset IDs; real-provider run failed at shot 12/17. Rejected because elapsed-time multiplication recreated the same cardinality defect.

One semantic segment now normally means one shot; extra shot only for deterministic semantic/representation transition. File-ID uniqueness is not product-visible diversity.

## 2026-09-03 — Quality-constrained semantic-v3

Zipper `15.480 s` exposed a mathematical conflict with unchanged `0.34`: initial groups `5.546`, `5.355`, `4.579` meant first two could never pass.

Correction: `effective_max_segment_seconds = min(8.5, accepted_voice_duration * 0.34)` on existing timed-beat boundaries. A beat itself is never split just to pass visuals; if one beat exceeds cap, fail closed. No time-driven extra shots.

Focused suite PASS: segmentation, visual-shot quality, WF05 contract, visual discovery compatibility, legacy visual-quality, WF04 runtime/global/perceptual/download regressions, rank-query, representation truth eligibility, 41 Code-node compiles, Studio JS compile, mode regression.

Real-provider read-only PASS:

- zipper `15.480 s`: 5 shots, clusters 5/required 3, max share `0.2958`;
- EN induction `13.944 s`: 4 shots, clusters 4/required 2, max share `0.3374`;
- UK induction fixture `57.216 s`: 10 shots, clusters 9/required 5, max occurrence 2, max share `0.245`.

Provider errors 0. No retry, threshold weakening, topic hack or production write.

Diagnostic mistakes preserved: repository not mounted into live n8n; disposable n8n entrypoint misused; mode-600 fixture caused EACCES; a harness briefly hardcoded expected segment count. None was product evidence.

## 2026-09-03 — Disposable render-v3 proof

Flat-color synthetic images correctly failed post-render perceptual gate. Corrected spatially distinct patterns with 24 s WAV, six subtitles and four 6 s shots PASSed: H.264/yuv420p 1080x1920, AAC 48k stereo, pre/post states 4/required 2, adjacent 0, max share `0.25`. Proved no artificial 5 s shot gate.

## 2026-09-03 — GitHub/VPS divergence and reconciliation

VPS code and GitHub docs diverged from merge base `7d25bac1c4d1a90b2b29183d9ec3ca280d1acfc4`; ff-only merge correctly refused; VPS HTTPS/SSH push unavailable; no force push.

GitHub branch `rebuild/semantic-visual-segments` preserved remote docs history; local implementation branch `rebuild/semantic-visual-segments-local` came from production-code HEAD. Clean local semantic commit: `2405d0431ff2007b52825b273267d07fad9f68ce`.

GitHub semantic sync completed via connector writes. Of 17 implementation files, 16 exact blob matches; `server.mjs` differed only final EOF LF, with no semantic code diff.

Design doc aligned commit `61cfb69f4f821154cc5a47f72b8c0634b250f74c`; architecture aligned commit `b71ce862a606b1010625912c4ba07b8f600d8b56`.

Correct predeploy CURRENT_STATE alignment commit is `f0f80836a6666b83502f6b74163936ff1a83ad85`. A later history transcription wrote a wrong hybrid hash; that transcription is explicitly invalidated here.

## 2026-09-03 — Migration 015 disposable proof

Full diff `e4e8560 -> 2405d04`: exactly expected 17 files, `git diff --check` 0, no compose/WF02/WF03 changes.

Disposable PostgreSQL 18: migration applies twice; three tables exist; valid job->segment->asset->shot works; deleting job cascades segments/shots but retains library asset; invalid `planned_shot_count=3` rejected.

First socket-readiness harness hit PostgreSQL temporary init server and then lost the socket; corrected to TCP readiness. Not a migration failure.

## 2026-09-03 — Bounded rollback snapshot

Snapshot `/opt/ai-short-form-content-factory/rollback/20260903T134851Z-pre-semantic-v3` created before semantic production mutation and SHA256-verified. Contains predeploy live/filesystem WF04/WF05, media-worker source/build inputs, compose, DB schema/state and runtime image metadata.

Predeploy media image `sha256:4009376d074a271aced92aa0cde159ee46bb445af6998580e088a5d23137413d`, rollback tag `ai-short-form-content-factory-media-worker:rollback-20260903T134851Z`.

Non-sudo Docker socket denial and two snapshot shell-quoting failures were diagnostic only; final structured script completed before mutation.

## 2026-09-03 — Semantic-v3 production deployment PASS

Seven exact runtime files staged from clean `2405d04` and byte-compared. Migration 015 applied transactionally with `ON_ERROR_STOP=1`. Media-worker built successfully and only media-worker was recreated; health PASS with local SigLIP and one preview attempt.

First n8n import attempt used unsupported regular-mode `--activeState=fromJson`; published re-exports matched rollback snapshot, proving no-op. Correct path was `import:workflow` then explicit `publish:workflow`; temporary root-owned cleanup issue corrected before restart. After both publishes, n8n restarted exactly once.

Post-restart:

- WF04 active=true, 27 nodes, source/live core SHA `b6b08f21e0fe58b6661f7413e3389834b92c6142f65831a3afcae526a31b53ed`, version/activeVersion `12e0857b-3c3c-4640-b7f1-2861050038f1`;
- WF05 active=true, 16 nodes, source/live core SHA `c5595719c63eecb2680c10dbe6a63e45bb7bc4f6d12308c3b62f5f2953f9a117`, version/activeVersion `ae9d00c2-bd65-4d3f-a8f5-ec0bcf840a12`;
- four media source files host/container byte-equal;
- migration 015 live;
- three project services healthy.

CURRENT_STATE moved to live deployment boundary in commit `6feae37a56fe121a514b15acf5affc1eccb813b4`. History was re-compacted/corrected in commit `afa366fd10aaf997693582d6c8287305965973ec`.

## 2026-09-03 — Fresh semantic-v3 production job fails at HTTP discovery adapter

Exactly one new intake call was made for `как работает индукционная плита / uk / 60`.

- HTTP 201;
- fresh job `cb98ad2b-1aaa-4117-918d-8fef22940945`;
- matching topic/language/duration job count changed `3 -> 4`, proving one new row;
- WF01 execution `10796` success;
- WF02 execution `10797` and WF03 `10798` propagated downstream error;
- exactly one Edge output persisted: provider `microsoft_edge_readaloud`, model `edge_neural`, voice `uk-UA-OstapNeural`, measured `57.216 s`;
- WF04 execution `10799` failed;
- final job state `failed|visuals`;
- `visual_segments=0`, `visual_shots=0`;
- no final video;
- this job is consumed and must never be retried/reused.

Concrete WF04 error: `Segmented visual discovery returned no visual segments [line 26]`.

Execution-data inspection proved the upstream HTTP error first: WF04 `Prepare Canonical Media Request` correctly produced `discovery_request.canonical_source` plus `discovery_request.timed_beats` covering the accepted voice. `Fetch Canonical Media` POSTed that exact object to `/visual/discover`. Media-worker returned HTTP 422: `Visual discovery failed: visual discovery requires timed_beats or beats`.

Verified root cause is a general HTTP adapter wiring defect, not provider shortage, SigLIP, topic content, or thresholds:

- WF04 correctly sends JSON field `timed_beats`;
- `visual-discovery.mjs` correctly supports function argument `timedBeats` and enters segmented mode when it is present;
- `server.mjs::discoverVisuals()` forwarded only `beats: body?.beats` and never forwarded `body?.timed_beats` as `timedBeats`;
- therefore real HTTP semantic-v3 requests discarded the new timed-beat payload before calling the already-proven discovery function;
- local real-provider dry-runs bypassed this HTTP adapter and therefore did not cover the defect.

No retry of the consumed job is allowed. M8 remains `2/10`. Required correction is systemic: fix the media-worker HTTP adapter to forward both legacy `beats` and semantic `timed_beats`, add a regression that covers the adapter contract, prove it before bounded media-worker redeploy, then create a different completely fresh job only after that deploy.