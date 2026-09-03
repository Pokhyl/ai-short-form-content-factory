# Engineering History — Rebuild

Chronological durable record for material changes, failures, verified root causes, regressions, deploys and rollback facts. `docs/CURRENT_STATE.md` remains the operational source of truth.

Compacted on 2026-09-03 while preserving the material failures, decisions, commits, rollbacks, diagnostic mistakes and acceptance evidence needed to resume without chat memory. Exact code history remains recoverable from listed commits and rollback snapshots.

## 2026-09-02 — Old induction machine PASS invalidated

Job `13f64c50-8dd5-47e4-a88f-1411d258e7c4` reached `review_ready`, but human inspection showed only two effective visual states. Previous machine PASS is permanently invalidated. Root cause: old acceptance counted scene/file presence rather than actual video-level perceptual sequence quality.

## 2026-09-02 — Visual-quality-v2 rewrite and deployment

Required visual path became:

`timed beat + evidence -> deterministic search intents -> multi-source discovery -> metadata/provenance eligibility -> local SigLIP ranking + perceptual identity -> global assignment -> sequence gate -> persist -> render -> post-render pixel-state gate -> review_ready`.

Six-beat contract: every beat truth-eligible; at least five perceptual clusters; zero adjacent duplicates; no cluster over `0.34` duration share; non-finite metrics fail closed; rendered midpoint frames independently satisfy required state count.

Cross-topic dry-runs without threshold weakening: EN induction 6 clusters/max `0.1813`; PL combustion engine 5/max `0.3333`; RU refrigerator 6/max `0.1667`; UK volcano 6/max `0.1667`.

Commit `f7c4096503c9620910b387129a5a06cce4d26d42` — `redesign: enforce perceptual visual diversity`.
Rollback: `/opt/ai-short-form-content-factory/rollback/20260902T175543Z-pre-visual-quality-v2`.
Migration 013 applied; WF04/WF05 published; exactly three project services and PostgreSQL healthy.

Diagnostic compile-harness mistake where top-level-array workflow exports were treated as objects was invalidated; zero-count Code-node output is never accepted as PASS.

## 2026-09-02 — Reference-media lifecycle failure/fix

Fresh job `1afc307d-aaac-4eed-8387-b05e1b6721eb`, WF04 execution `9902`, failed after its single Edge synthesis because planner persisted fake `reference_media_kind=mixed` and violated DB constraint.

Systemic correction: `visual_planned + technical_reference` keeps `reference_media_kind=NULL`; `visual_ready` requires actual `photo|diagram|animation`.

Commit `b83bf6d48f1df259c7c6fa0136748ca10d13f1af` — `fix: align reference media kind lifecycle`.
Rollback: `/opt/ai-short-form-content-factory/rollback/20260902T181813Z-pre-reference-media-kind-lifecycle`.
Migration 014 live; WF04 core equality proved; runtime healthy.

## 2026-09-02 — M8 #2 induction MACHINE + HUMAN PASS

Accepted job `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`, `How does induction heating work? / en / 15`.

Machine proof: `review_ready`; preflight `14.358 s`; execution `9926` exactly one successful Edge synthesis; measured voice `13.944 s`; 6 beats; 6/6 perceptual clusters, required 5; adjacent 0; max share `0.1813`; post-render six states; ffprobe 14.000 s H.264 1080x1920 30fps + AAC 48kHz stereo. User watched exact fresh video and replied `мне нравится`. M8 accepted count became 2/10. Old two-state induction remains invalidated.

## 2026-09-02/03 — WF02 multilingual retrieval failure and systemic correction

Observed failures:

- `Dlaczego popcorn pęka podczas podgrzewania? / pl / 15` failed because native Wikipedia query was over-constrained.
- job `85fcc63b-b89b-40d0-b253-6383b715f105`, topic `как работает индукционная плита`, requested `uk`, 60 s, failed at `script` before voice because old live path issued Russian subject text against Ukrainian Wikipedia without multilingual resolution.

Systemic contract after correction:

- preserve full meaningful factual tokens for relevance validation;
- bounded subject-leading discovery query;
- bounded probes exactly EN/PL/RU/UK, requested language first;
- one Wikipedia request per probe, no retry loop;
- official Wikipedia language link required for cross-language source handoff;
- no topic mapping, generative translation, provider cascade, bypass or threshold weakening;
- how/why evidence prioritizes mechanism/principle/construction;
- extractive narration remains exact-source/provenance preserving;
- duration operating bands unchanged.

Final real-Wikipedia proof: RU-topic→UK induction cooktop `60.106 s`; UK refrigerator `59.975 s`; PL popcorn `15.079 s`; EN induction `14.939 s`, all pre-TTS safe. Seven new WF02 regressions PASS; Code compile 8/8; staged pipeline PASS; retained duration audit 150 rows / 40 safe / 0 false-safe; CASE1 staged provenance PASS; CASE1 visual eligibility PASS.

Diagnostic harness mistake: initial CASE1 visual invocation passed `-e never` as Node input and produced `ReferenceError`; invalid harness result. Correct invocation passed.

Commit `e4e856093fa237dab9daaa56dcf443c3b6155f93` — `fix: make factual retrieval multilingual and explanation-aware`.
Rollback: `/opt/ai-short-form-content-factory/rollback/20260903T055250Z-pre-wf02-multilingual`.
WF02-only production deploy PASS; live canonical core SHA `0f5893ffba59b23d181c363b26b991450e3fc016a52016e1ec686797dbfe23c1`; workflow active; no retry/maxTries; three project services healthy.

## 2026-09-03 — Fresh UK/60 production failure exposes visual-unit mismatch

Fresh real intake job `4372be34-c417-415f-92f6-63481b3b5686`, topic `как работает индукционная плита`, output `uk`, target 60, returned HTTP 201.

It passed corrected WF02 and the single Edge synthesis. Canonical factual title `Індукційна плита`; preflight `60.106 s`; measured voice `57.216 s`; voice `uk-UA-OstapNeural`; 18 timed beats.

WF04 then failed at visuals with exact error `perceptually unique truth-eligible assignment 11/12 [line 15]`. Final state `failed|visuals`. This job must never be retried/reused because its one automatic Edge synthesis was already consumed.

The failure stopped M8 progression as required.

## 2026-09-03 — Semantic visual segmentation selected instead of further matcher tuning

After broader comparison with multiple open-source short-video architectures, the architectural correction was selected: timed narration/subtitle beats are transport units and must not automatically become independent semantic media-search obligations.

New contract is documented in `docs/VISUAL_SEGMENTATION_DESIGN.md`, initial design commit `d19ff9e66f47cbadf206141d4b51bbc3d7631abc`:

`accepted voice -> timed beats -> deterministic semantic visual segments -> one or more visual shots per segment -> truth eligibility -> local SigLIP ranking -> perceptual duplicate control -> render timeline -> post-render frame gate -> human review`.

No generative visual planner, hosted semantic dependency or threshold weakening is introduced. WF01-WF03 and one-shot Edge remain unchanged. Planned durable entities are `visual_segments`, `visual_shots`, and reusable `media_library_assets`; legacy scene visual columns remain for historical compatibility.

## 2026-09-03 — GitHub/VPS branch divergence discovered before rewrite

Fresh inspection found a material repository-state defect: current VPS/local code history and GitHub `rebuild/simple-pipeline` documentation history diverge from merge base `7d25bac1c4d1a90b2b29183d9ec3ca280d1acfc4`.

- VPS current code HEAD: `e4e856093fa237dab9daaa56dcf443c3b6155f93`.
- GitHub branch had a separate docs chain ending at the semantic design commit.
- `git merge --ff-only` correctly refused the divergent histories.
- VPS HTTPS push dry-run failed because no GitHub credentials are available there; SSH authentication also failed.
- GitHub Contents API could not resolve local code commit `e4e8560`, proving it is not merely a stale ref display.

No force push or destructive branch rewrite was attempted. GitHub implementation branch `rebuild/semantic-visual-segments` was created from the current remote source-of-truth. Local implementation branch `rebuild/semantic-visual-segments-local` was created from the actual current production-code HEAD. Final reconciliation must use GitHub connector git-object writes/PR while preserving the newer remote docs history and synchronizing the current production-critical code snapshot.

## 2026-09-03 — Semantic segmentation first local proof

Local implementation started without production mutation:

- `services/media-worker/src/visual-segmentation.mjs` — deterministic semantic grouping of adjacent timed beats using timing, punctuation and evidence-support boundaries; no fixed duration→segment-count mapping.
- `db/migrations/015_visual_segments.sql` — additive tables `visual_segments`, `visual_shots`, `media_library_assets`.
- `tests/visual_segmentation_regression.mjs` — includes the actual 57.216 s / 18-beat failed Ukrainian induction fixture.

Correct runtime test executed inside the existing n8n container because host Node is absent. PASS:

`{"pass":true,"uk_segments":9,"uk_shots":17,"punctuation_segments":6,"continuous_segments":2}`

This proves the failed 57.216 s fixture becomes 9 semantic search segments rather than 18 independent search obligations, while preserving gapless full-duration coverage; same-duration 15 s fixtures can produce different segment counts from content, proving segment count is not duration-hardcoded.

## 2026-09-03 — visual-quality-v3 work and invalid regression assertions

Local-only work extended visual discovery to segmented mode and added a separate `visual-segments-v3` shot-sequence evaluator while preserving legacy v2.

Three test-only defects were exposed and corrected before accepting the regression gate:

- the first `visual_shot_quality_regression.mjs` incorrectly expected `evaluateVisualShotSequence()` to throw on an adjacent duplicate; the evaluator intentionally returns `pass=false` for that valid-but-rejected sequence rather than throw;
- an initial `wf04_assignment_regression.mjs` 10-second fixture had a single 4-second shot, which by construction exceeded the unchanged `0.34` cluster-duration share even when every asset/cluster was unique; the fixture was corrected to a 12-second / three-4-second-shot case rather than weakening the gate;
- an initial `wf04_perceptual_assignment_regression.mjs` offered only three perceptual states for four equal-duration shots. Under the unchanged `0.34` duration-share rule no state could legally occur twice, making the declared PASS fixture mathematically impossible; a fourth genuinely distinct candidate cluster was added to the fixture.

None of these failures were production failures and no acceptance threshold was changed.

## 2026-09-03 — Semantic visual v3 focused regression gate PASS

WF04 and WF05 were locally rewritten around separate semantic visual segments and shot timelines. Production was not mutated.

Current local contract:

- timed `scenes` remain subtitle/timing beats and stay `timed`;
- WF04 derives semantic `visual_segments`, ranks truth-eligible provider candidates per segment and assigns one or two actual `visual_shots`;
- shot assignment uses bounded global beam search, globally unique asset IDs, no adjacent perceptual duplicate, max perceptual-cluster occurrence 2, max perceptual-cluster duration share `0.34`, and max shot duration 5 seconds;
- migration 015 persists `visual_segments`, `visual_shots`, and `media_library_assets`;
- media-worker adds `/visual/store-shot` and `/render-v3` while retaining legacy routes;
- WF05 reads two independent timelines: timed beats for subtitles and visual shots for the video track;
- render-v3 independently checks pre-render shot identity/timing/diversity and post-render midpoint-frame perceptual state diversity.

A real Code-node mode defect was also caught by `code_node_mode_regression.py`: `Require Visual Completion` was configured `runOnceForEachItem` while using `$input.first()`. The implementation was corrected to use `$json` in per-item mode; the mode gate then passed.

Focused/static suite now PASS in the existing n8n container (Node v24.18.0):

- semantic segmentation regression PASS, including actual UK/60 57.216 s fixture -> 9 segments / 17 planned shots;
- visual-shot-quality-v3 PASS;
- WF05 visual-segments-v3 structural contract PASS (`/render-v3`);
- visual discovery compatibility PASS;
- legacy visual-quality-v2 regression remains PASS;
- WF04 Code-node runtime-v3 PASS;
- WF04 global assignment-v3 PASS;
- WF04 perceptual assignment-v3 PASS;
- WF04 download/store expansion-v3 PASS;
- rank-query contract PASS at 200 chars;
- representation relevance/truth-eligibility PASS;
- Code-node compile `41` PASS;
- Studio inline JS compile PASS;
- Code-node mode regression PASS.

Fresh runtime during the gate remained exactly three project containers; n8n `/healthz` 200, media-worker `/health` 200, PostgreSQL healthy. No migration, workflow publish, container recreate, or production job was performed.

Exact next stage: transactionally validate migration 015 and build/run a disposable semantic-v3 media-worker/render integration without replacing production. Only after database/render/cross-topic real-provider dry-runs pass may the implementation be synchronized to GitHub, snapshotted and deployed.

## 2026-09-03 — Real-provider UK/60 dry-run invalidates duration-driven shot cardinality

After migration 015 and disposable `/render-v3` validation passed, the actual failed Ukrainian induction fixture was run through the local semantic-v3 path with real provider discovery and local SigLIP ranking. Production was not mutated.

The semantic segmentation itself behaved as intended: the 57.216 s / 18-timed-beat narration became 9 semantic visual segments. However, `planned_shot_count = ceil(segment_duration / 5.0)` expanded those 9 semantic segments into 17 mandatory shot slots, and `Choose Visual Assignment` additionally required globally unique candidate asset IDs. The real-provider dry-run then failed with exact error `No valid semantic visual shot assignment at shot 12/17`.

This is a systemic architecture defect, not a provider shortage to patch around. The 5-second timer recreated almost the same cardinality pressure that semantic segmentation was introduced to remove: long semantic intervals again implied many nearly unique media files regardless of whether the narration meaning changed.

The correction must not enlarge candidate pools, add retries, weaken the `0.34` perceptual-duration gate, or add topic-specific assets. Shot cardinality must instead be content/representation-driven. A semantic segment should normally remain one visual shot; additional shots are allowed only when a deterministic semantic/representation reason exists. Asset-file uniqueness must not be used as a proxy for product-visible diversity; perceptual cluster identity and post-render visual-state verification remain the authoritative diversity controls.

Fresh runtime at this failure point remained exactly three production containers with n8n/media-worker HTTP 200 and PostgreSQL healthy. No production migration, workflow publish, container replacement, or fresh production job was performed.

## 2026-09-03 — Real-context dry-run harness fixed after false segment-count FAIL

After the duration-driven shot-cardinality correction, the first real-context rerun loaded the exact persisted job `4372be34-c417-415f-92f6-63481b3b5686` read-only: 18 timed beats, 8 persisted evidence rows, accepted voice duration `57.216 s`, canonical source `uk / Індукційна плита`.

The harness then stopped before ranking because it incorrectly asserted that the exact database narration must produce exactly 9 semantic segments. The current deterministic segmenter produced 10 segments from the actual persisted text/timing. This was a diagnostic harness defect and a false FAIL, not a product/runtime failure: the architecture explicitly requires segment count to be content-derived rather than fixed by duration or by an approximate regression fixture.

The corrected real-provider harness must therefore require structural properties instead of an exact count: semantic segment count is positive and lower than the 18 timed-beat count for this case; default shot count equals semantic segment count after removal of elapsed-time shot multiplication; the segment/shot timelines cover the full `57.216 s`; all truth-eligibility, SigLIP, perceptual adjacency/occurrence, `0.34` duration-share and post-render gates remain unchanged. No production mutation or threshold change occurred.

## 2026-09-03 — Corrected UK/60 real-provider semantic-v3 dry-run PASS

The corrected local-only real-provider dry-run reloaded exact persisted job `4372be34-c417-415f-92f6-63481b3b5686` read-only and executed the current local semantic-v3 discovery/planning/ranking/assignment path with real Wikimedia, Pixabay and Pexels candidates plus the existing local SigLIP rank endpoint. Production was not mutated.

PASS proof:

- 18 timed beats -> 10 content-derived semantic visual segments;
- 10 semantic segments -> exactly 10 visual shots; elapsed time no longer multiplies shot obligations;
- every segment retained a 10-candidate truth-eligible pool containing Wikimedia, Pixabay and Pexels;
- all 10 shot slots were assigned successfully;
- unique assets `10/10` in this specific run, but asset uniqueness is not a required product gate;
- perceptual visual clusters `9`, required `5`;
- adjacent perceptual duplicates `0`;
- maximum perceptual-cluster occurrence `2`;
- maximum perceptual-cluster duration share `0.245`, below unchanged `0.34`;
- longest semantic shot `7.278 s`, proving removal of the artificial 5-second file-change timer without weakening video-level diversity;
- provider errors `0` for this run;
- the full shot timeline covered the persisted `57.216 s` accepted voiceover;
- runtime after the dry-run remained exactly three project containers.

The selected sequence included Wikimedia, Pixabay and Pexels assets and passed without retries, candidate-pool inflation, topic-specific mappings, threshold changes, provider fallbacks outside the existing bounded multi-source contract, or production writes. This validates the systemic shot-cardinality correction for the original UK/60 failure fixture. Next gate is cross-topic real-provider dry-runs before any deployment.
