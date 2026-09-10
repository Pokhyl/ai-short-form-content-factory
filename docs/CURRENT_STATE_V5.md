# Current State — V5 n8n Autonomous Video Orchestrator

Last updated: 2026-09-09

Branch: `rebuild/editorial-core-20260908`.


## 2026-09-09 assistant-visual mechanism/context mismatch — systemic WF02 correction verified, pending GitHub/deployment

New autonomous normal job `386d332c-e0f9-42e8-a4c0-f7d52915ac8b` (`How the Panama Canal locks work` / `ru` / `15`) completed WF01→WF05 and produced exact MP4 `jobs/386d332c-e0f9-42e8-a4c0-f7d52915ac8b/render/final.mp4`, SHA256 `f86dc120141cc54d431a59d8f47136760c5a0575546d55db9a2907e3b1b3514e`, H.264/AAC, 1080x1920, 30 fps, 15.421 s. Assistant visual inspection of the exact rendered artifact issued **ASSISTANT VISUAL FAIL**. Scene 1 narration described ship entry and gate closing while the inspected shots showed only a chamber/water/general lock view; scene 2 narration described valves opening, chamber filling and the ship rising while both inspected shots showed a container ship/general lock infrastructure with no visible valve, filling, level change, diagram or callout. Scene 3 locomotive imagery was materially aligned. The failed artifact is preserved unchanged at `/opt/ai-short-form-content-factory-runtime-backups/assistant-visual-fail-386d332c-20260909T123233Z/` with job/scenes/visual-shots/verdict evidence and SHA manifest. It must not be manually rescued or presented as a HUMAN candidate.

Source-proven systemic cause: WF02 contained a direct contradiction of the permanent HUMAN review contract. `Prepare Candidate Claims` allowed an explanatory hidden-mechanism fact to be paired with only apparatus/component/context imagery, and `Prepare Inventory Grounded Story` explicitly required the mechanism to remain in narration even when no visual actually explained it, while allowing context assets from another claim. The resulting `shot_intent` values for the failed run already showed the mismatch before rendering (for example container ship/general lock structures under narration about valves and water-level lift).

The current correction remains topic-generic and fail-closed. For explanatory `mechanism/detail` claims, `Validate Candidate Claims` now requires concrete distinctive visual-target anchors to be aligned with both the factual claim and the cited pixel-reviewed inventory. One weak/common lexical overlap is insufficient when the target contains multiple substantive anchors. Media/form words are not accepted as semantic anchors. Final explanatory mechanism/detail units additionally require at least one direct reviewer-bound asset for that exact claim; generic context-only substitution is no longer sufficient. The contradictory prompts that instructed the model to preserve hidden mechanism narration despite absent explanatory visuals were removed. No threshold relaxation, topic-specific vocabulary, manual asset choice, renderer change, extra recovery loop, paid dependency or speech-rate manipulation was introduced.

Verification on the corrected current tree is COMPLETE before deployment: **64/64 Node static regressions PASS** with the explicit real-provider dry run excluded; **13/13 Python static regressions PASS**; all **8** workflow JSON files parse; `git diff --check` PASS; fresh PostgreSQL contract PASS for **21 workflow SQL statements + staged writes**; exact `n8nio/n8n:2.37.10` import contract PASS for **8/8 workflows**; structured model invocation contract PASS for **6/6 calls** plus reserved-visual MIME contract PASS. A new cross-topic regression `wf02_mechanism_visual_correspondence_regression.mjs` proves the same failure class with a non-Panama physical mechanism fixture.

Next: preserve this exact verified tree in GitHub, verify target-branch parent/tree identity and zero active production executions, capture WF02 rollback/current/active parity, deploy/publish **WF02 only**, restart n8n once only if the CLI requires it, verify health and exact source/current/active parity, then submit exactly ONE completely NEW normal product job. Do not modify or resume `386d332c...` or any older failed/rejected job. If the new job reaches MP4, perform the exact-artifact assistant visual gate before any HUMAN review request.


## 2026-09-09 availability-first strategy switch — verified, pending GitHub/deployment

The narrow reviewer-wording correction at commit `6c06cfc7e1d77d657c788c9c4410047cb683f005` was deployed in production before the next normal product run. Production WF02 source/current/published parity against that exact commit was re-proven after the run. Exactly ONE later normal Panama/ru/15 job, `bc00ab62-e305-43ac-b8d8-9ed372456553`, failed closed in WF02 execution **16693** with `pre-script global reviewed visual inventory assets=2/6, claims=1/3`; model-gateway executions **16694–16697** all succeeded. The failed job is immutable and must not be resumed or repaired. This demonstrates that further prompt-level clarification of the old claim-first reviewer contract is not a productive direction.

Strategy is therefore changed at the architectural ordering level, while preserving n8n as orchestrator and all existing evidence/relevance/uniqueness gates: **real visual availability now precedes claim authoring**. After resolved-subject research, WF02 creates bounded topic-generic visual exploration hypotheses, queries the free licensed provider layer, fingerprints/deduplicates candidates, shows the actual images to the multimodal reviewer, and persists a pixel-reviewed `available_visual_assets` inventory. Only then may the claim model create grounded claims, and every claim must cite both research evidence and 1-3 IDs from that already-reviewed visual inventory. `visual_target` must describe only something actually present in the cited reviewed assets; hidden mechanism facts remain grounded by research, while their visuals may truthfully show the visible apparatus/component/context instead of pretending pixels prove the hidden operation. Final pre-script review, metadata/pixel consistency, perceptual uniqueness, minimum inventory, frozen story/asset bindings, exact natural-rate TTS, WF04/WF05 gates and HUMAN review remain in force.

Current source adds the explicit WF02 chain `Prepare Visual Exploration -> Draft Visual Exploration -> Validate Visual Exploration -> Discover Pre-Claim Visual Inventory -> Prepare Pre-Claim Review Batches -> Inline Pre-Claim Candidate Images -> Review Pre-Claim Visual Inventory -> Select Pre-Claim Visual Inventory -> Prepare Candidate Claims`. The media-worker discovery adapter accepts bounded `exploration_queries` before claim inventory exists and keeps named-subject identity filtering. No Panama-specific query, manual asset choice, topic whitelist, unreviewed fallback, quality-threshold relaxation, recovery loop, speech-rate manipulation or separate CLI product path was introduced.

Verification on the current tree is COMPLETE before deployment: **64/64 Node static regressions PASS** with only the explicit real-provider dry run excluded; **13/13 Python static regressions PASS**; all workflow JSON parse PASS; `git diff --check` PASS; fresh PostgreSQL contract PASS for **21 workflow SQL statements + staged writes**; exact `n8nio/n8n:2.37.10` import contract PASS for **8/8 workflows**; structured model invocation contract PASS for **6/6 calls** plus reserved-visual MIME contract PASS. Media-worker image build PASS: `sha256:f7157e8366052cbdd772523a4ecf7f7c2da4e73337c71468de7f2068ee9734cd`. Image/source SHA equality PASS for `visual-discovery.mjs` (`b9e5964d865e77ed3de041dc05839d09b96204b82bf868034d09309778d4848a`) and `visual-discovery-request.mjs` (`99ac3ceb42c9c137c6b07a882b9e8d993d06ff73d7cf163f644b4b0d0b33550e`).

Next: commit/push this exact verified tree, verify GitHub tree identity, verify production idle/no newer normal product job, capture rollback for WF02 + current media-worker image/source, deploy only WF02 + the exact prebuilt worker image above, verify source/current/published parity and worker source/health, then submit exactly ONE completely NEW normal Panama/ru/15 job through WF01. Follow that job to exact MP4 assistant visual gate or preserve the next demonstrated systemic failure. Do not resume `bc00ab62...`, `da025c06...`, or any older failed/rejected job.

## 2026-09-09 live visual-binding reviewer ambiguity — systemic correction verified, pending GitHub/deployment

After the WF03 sentence-completion correction was preserved on GitHub and deployed, exactly ONE new normal product job was submitted: `da025c06-dac9-45fc-8c10-78345b61100e` (`How the Panama Canal locks work` / `ru` / `15`). WF01 execution **16682** succeeded. WF02 execution **16683** failed closed before story generation with `pre-script global reviewed visual inventory assets=3/6, claims=1/3`. Model-gateway executions **16684–16688** all completed successfully. The failed product job is immutable and must not be resumed or repaired.

Exact raw evidence is preserved at `/opt/ai-short-form-content-factory-runtime-backups/failure-da025c06-20260909T063446Z/` with SHA256 manifests for execution entity/workflow/data rows **16683–16688** and the exact job row. Live visual review exposed **33** unique images in two normal bounded batches (**24 + 9**). The live reviewer marked **5/33** relevant, all bound only to `C1`, even though its own visible descriptions correctly identified multiple later targets, including water-control culverts and Gatun Lake/canal maps.

Systemic root cause was demonstrated without changing retrieval, images, thresholds, selector, metadata consistency, perceptual dedupe or the failed job. The live review contract still left `supported_claim_id` semantically ambiguous enough for the vision model to treat it as a second proof of the whole grounded FACT rather than as the intended visual TARGET/FORM binding. An exact component replay used the same **33 inline image bytes**, same claim inventory, same schema and same model gateway, changing only generic visual-binding wording. Replay result: **12** reviewer-relevant images across `C1/C3/C4/C5`; the unchanged deterministic metadata-consistency and perceptual-dedupe selector retained **11** unique assets across **4** claims, exceeding the unchanged **6 assets / 3 claims** gate. Proof file: `/opt/ai-short-form-content-factory-runtime-backups/failure-da025c06-20260909T063446Z/selector-proof-target-binding-variant.json`, SHA256 `c772a57375ebb8cc88a2425645a6ddf1ef9017fb01964c575172f2a1618fc937`.

Correction in the current source is deliberately narrow and topic-generic: WF02 `Prepare Inventory Review Batches` now states explicitly that `supported_claim_id` is a TARGET/FORM binding, not a second factual-proof verdict; grounded FACT truth remains research authority; a target-matching still must not be rejected merely because pixels cannot prove function/purpose/causality/result/quantity/operation; map/diagram identity may be established by visible labels/geometry; a physical component in authentic subject context is sufficient without showing its function occurring. Wrong subjects/forms, generic lookalikes without visible subject identity, screenshots, watermarks, logos, collages, text cards, target mismatch, reviewer relevance, metadata/pixel consistency, perceptual uniqueness and minimum inventory gates remain unchanged. No topic-specific example, manual content choice, recovery loop or quality-gate weakening was introduced.

Full verification on the corrected tree is COMPLETE: **61/61 Node static regressions PASS** with the explicit real-provider dry run excluded; **13/13 Python standalone regressions PASS**; fresh PostgreSQL contract PASS for **21 workflow SQL statements + staged writes**; structured model invocation **4/4 PASS** plus reserved-visual binary MIME contract PASS; real disposable `n8nio/n8n:2.37.10` import **8/8 workflows PASS**; all workflow JSON parse PASS; `git diff --check` PASS. The exact live-image component replay proof remains `selector-proof-target-binding-variant.json`, SHA256 `c772a57375ebb8cc88a2425645a6ddf1ef9017fb01964c575172f2a1618fc937`.

Next: preserve this exact verified tree on GitHub, verify production idle/no newer product job, capture WF02-only rollback, deploy/publish WF02 only, restart n8n once if required, verify source/current/published parity and health, then submit exactly ONE completely NEW normal Panama/ru/15 job. Do not resume `da025c06...` or any older failed/rejected job.

## 2026-09-08 pre-script visual inventory blocker — systemic correction verified, pending WF02 + media-worker deployment

After the WF03 hard duration-budget fix was deployed, exactly ONE new normal product job was submitted: `7927b142-545f-4251-93c0-f8173a0e6bfa` (`How the Panama Canal locks work` / `ru` / `15`). WF01 succeeded. WF02 execution **16482** failed closed before script generation with `pre-script verified two-photo claim inventory 0/3`. All model-gateway calls for that WF02 execution succeeded. WF03/WF04/WF05 never ran for this job. The failed job is immutable and must not be resumed.

Exact raw execution evidence: `/opt/ai-short-form-content-factory-runtime-backups/voice-budget-a839f94-20260908T080404Z/failure-7927b142-545f-4251-93c0-f8173a0e6bfa/execution-16482.json`, **649754 bytes**, SHA256 `caa70bdfb631c587fdd1f301ebdd664a5cec76aaaa41906443ab34f569d136a2`.

Systemic root cause was established by exact component replay, not by weakening the reviewer. The media providers had sufficient relevant assets, but the pre-script pipeline lost them through a combination of contract defects: candidate-claim targets could demand staged/non-visible actions instead of a minimum observable subject; short jobs exposed too few unique images to the visual reviewer; recovery queries could drop distinguishing target terms or reduce multi-token components too aggressively; candidate ranking followed incomplete `search_query_en` wording instead of the stronger `visual_target` acceptance criterion; canonical subject components were not combined with target details during bounded recovery; plural forms such as `gate/gates` were not treated as equivalent; and long contextual metadata could outrank concise visible-object metadata.

Systemic correction in the current verified tree:
1. The 15-second candidate stage now generates exactly **6 grounded reserve claims** before visual verification (30s=8, 45s=10, 60s=12). Final story cardinality is still chosen only from reviewer-verified claims; reserve claims do not become narration automatically.
2. `visual_target` is machine-validated as a compact observable noun phrase. Camera/action instructions such as close-up, showing, under load, during operation, before/after and side-by-side arrangements are rejected. Research evidence continues to prove the factual proposition; pixels only need to truthfully match the observable target.
3. Inventory retrieval derives detail relevance and recovery from the full `visual_target`, not only the model's possibly incomplete `search_query_en`. Target-only distinguishing terms can be recovered when the query omitted them.
4. Bounded recovery remains finite: exact query + one primary target-detail query + at most three generic fallbacks. Fallbacks combine canonical subject components with the first useful target details and stop as soon as enough detail-bearing inventory exists. No Panama-specific synonym table or topic hack was introduced.
5. Simple plural identity matching is normalized for retrieval anchors (`gate/gates`, `culvert/culverts`, `mule/mules` class). Grammatical/camera/style noise is excluded from retrieval anchors.
6. Ranking uses concise asset metadata for detail scoring; long page/book descriptions cannot promote a visually generic image merely because surrounding prose mentions the target. The named-subject identity gate remains fail-closed.
7. The reviewer inventory may expose up to **48 unique perceptually deduplicated assets**, still in bounded batches of at most **24 images per model call**. Reviewer relevance, subject identity, metadata/pixel consistency, two-distinct-assets-per-claim and perceptual uniqueness gates are unchanged.

Exact source-based proof used the immutable research context from execution 16482, then executed the current WF02 `Prepare Candidate Claims` / request builder / validator source, a real model-gateway call, the current patched discovery source, the normal media-worker fingerprint/inline-image endpoints, real visual-review gateway calls and the exact WF02 selector. The source-generated claim stage produced six reserve claims. Final review exposed **36 unique images** in two bounded batches (24 + 12). Reviewer-approved counts included C1=4, C2=4, C4=5 and C5=6 across the batches. The exact selector PASS selected **3 claims × 2 distinct assets** with no manual claim/image choice. Final proof: `/opt/ai-short-form-content-factory-runtime-backups/voice-budget-a839f94-20260908T080404Z/failure-7927b142-545f-4251-93c0-f8173a0e6bfa/component-replay/source-contract-proof/selector-proof-current.json`, SHA256 `cfb47fa92f42c9d6a6360e27f4daf12385d090cf66125be7ac5b5485c69f08cc`. Current discovery evidence SHA256 is `20a6706a505e16cb7ae93996d37daf7ce0697cf6cdf6939c1dc79a75abee59e5`.

Verification COMPLETE before deployment on the final tree: **56/56 Node static regressions PASS**, **13/13 Python static regressions PASS**, fresh PostgreSQL contract PASS (**21 workflow SQL statements + staged writes**), real n8n **2.37.10** import PASS (**8 workflows**), structured model invocation PASS (**4/4**) plus reserved-visual binary MIME contract PASS, workflow JSON and `git diff --check` PASS. Final isolated media-worker build: `sha256:fadbe4c7d9ad7f3f1ff4e2d79003a3ebfc0eb08db9ae0dbe4d2837f88489740e`; exact `visual-discovery.mjs` SHA256 inside image equals source: `3e5b65e92dca45d42e360b8ef96b2e7b31d531f6831821638559ee5eb60de427`.

GitHub preservation and production deployment are COMPLETE for this correction. The verified source is GitHub commit `866cfcb610f8d7463cbd03c2768e61ded5ca05ea`, parent `afc69ed90b67c3c83c700cb1f8c426d8cab5db0e`, exact tree `c5970616887d91344a49ab21d26c616633d0c266`; the VPS verification commit `354e953bb1869ee2c0ca55af6dee1caa6302a803` has the same exact tree. GitHub Actions materialization run **34234806907** independently reconstructed the exact verified patch from the exact parent, verified target blob SHAs and exact tree, and produced commit `866cfcb...` before main was fast-forwarded without force.

Production deployment changed **WF02 + media-worker only**. Rollback/evidence directory: `/opt/ai-short-form-content-factory-runtime-backups/inventory-visual-866cfcb-20260908T135744Z`. Pre-deploy active executions were **0**, latest product job remained immutable failed `7927b142...`, WF02 was active/current `d651aee0-bc60-4be7-92ff-cb8be9584138`, and worker image was `sha256:94668bb03228e8fb943ce3be55a666ddad7d1b899ab0e6e2a9900989ab440ddd`, preserved under rollback tag `ai-short-form-content-factory-media-worker:rollback-inventory-20260908T135744Z`.

Exact WF02 import created current version `4a430ba9-0823-4c34-9c75-a17b0093c29f`; source/current nodes+connections+settings parity passed before publication. `n8n publish:workflow --id=TJfA4ZYUEKSTad6k` explicitly required restart, so exactly one n8n restart was performed. Final WF02 is active with `versionId = activeVersionId = 4a430ba9-0823-4c34-9c75-a17b0093c29f`, **34 nodes**, canonical source/current core SHA256 `6f430559fc88941b1c3aee9a08037cc6c1b45c8e1a41800c7a2ff5437b9c2215`; current nodes/connections/settings equal source and active published-history nodes/connections equal source.

The media-worker was recreated without rebuild from the exact preverified image `sha256:fadbe4c7d9ad7f3f1ff4e2d79003a3ebfc0eb08db9ae0dbe4d2837f88489740e`. Running `/app/src/visual-discovery.mjs` SHA256 equals verified source: `3e5b65e92dca45d42e360b8ef96b2e7b31d531f6831821638559ee5eb60de427`. n8n `/healthz` and worker `/health` both returned status `ok`; Pexels, Pixabay and SearXNG are configured. PostgreSQL was not recreated or migrated. Final active/running/waiting/new execution count is **0**.

Next exact step after this deployment record is preserved in GitHub: reread the mandatory gate, verify zero active executions and that no newer normal job appeared, then submit exactly ONE completely NEW normal `{"topic":"How the Panama Canal locks work","language":"ru","duration":15}` job through WF01. Follow it autonomously through WF02→WF03→WF04→WF05 to exact MP4 HUMAN review or preserve/fix the next demonstrated systemic failure. Do not retry or resume `7927b142...`.

## 2026-09-08 fresh E2E — WF03 hard duration-budget defect corrected and deployed

After the HUMAN FAIL visual-cadence/framing correction was deployed, exactly ONE new normal product job was submitted through WF01: `f7401fa2-1b25-4af9-8835-a2add047cd91` (`How the Panama Canal locks work` / `ru` / `15`). WF01 execution **16470** succeeded. WF02 execution **16471** succeeded after model gateway executions **16472–16476** all succeeded. The job then entered `processing/voiceover`; WF03 execution **16477** failed closed with `Voiceover duration 17.708s is still outside target after 3 story rewrites`. Duration-rewrite gateway executions **16478–16480** all succeeded. WF04/WF05 never ran, `visual_segments=0`, `visual_shots=0`, and no MP4 exists. The failed job is immutable and must not be resumed.

Exact raw n8n execution evidence: `/opt/ai-short-form-content-factory-runtime-backups/humanfail-5716922-20260908T062414Z/failure-f7401fa2-20260908/execution-16477.json`, **228561 bytes**, SHA256 `396b598d4f9638ae80e6c41321bb74c2d8678719ebe70ebd8deea776a302740d`. Decoded duration summary: `duration-controller-summary.json`, SHA256 `1b43d50ace33442844e92d8f1b0e39cdcc735e57aeb3782a48251329c72c3964`.

Exact measured unchanged-speed Edge attempts were:
- pass 0: **45 words / 23.295333s**; controller requested **28–30** words (target 29);
- pass 1: model returned **34 words / 19.533333s**; controller requested **25–27** (target 26);
- pass 2: model returned **32 words / 18.858333s**; controller requested **24–26** (target 25);
- pass 3: model returned **31 words / 17.708333s**, still above the accepted max **16.533s**.

All four Edge results preserved `rate_percent=0` and `post_tempo_factor=1`. Provider-tail trimming was active and removed about **0.873–0.894s** after the last exact provider word cue on every attempt. Therefore this is not the earlier provider-tail defect and not speech-speed manipulation. The measured-duration controller itself computed progressively smaller budgets correctly.

Systemic root cause was source-proven in WF03 `Apply Duration Rewrite`: a rewrite was accepted when its actual word count fell inside `desired_word_min - 8` through `desired_word_max + 8`. Thus a **34-word** rewrite was accepted for a measured **28–30** request, and a **31-word** rewrite was accepted for **24–26**. The broad acceptance window consumed all three bounded rewrite passes on scripts that were already known before TTS to violate the controller's requested budget.

Systemic correction in the current verified tree:
1. `Apply Duration Rewrite` now treats the measured `desired_word_min..desired_word_max` as a hard machine-validated contract; the legacy `±8` window is removed. Invalid/missing budgets fail closed and an out-of-budget model result is rejected before another TTS call.
2. `Prepare Duration Rewrite` explicitly tells the model that the total word range is machine-validated and that output outside it is invalid; it also supplies per-unit target-word guidance proportional to the current frozen units, with a generic minimum of four words per frozen unit. Claim IDs, unit IDs, evidence, visual/asset bindings, unit count, language and natural-rate speech remain frozen.
3. No deterministic truncation, speech-rate manipulation, extra retry/sleep loop, topic-specific wording, gate weakening, WF02/WF04/WF05 change, media-worker change or database change was introduced.

Verification COMPLETE before deployment: **50/50 Node static regressions PASS**, including a regression that rejects the demonstrated `34 words for 28–30` class and accepts an in-budget 29-word rewrite; **13/13 Python static regressions PASS**; fresh PostgreSQL contract PASS (**21 workflow SQL statements + staged writes**); real n8n **2.37.10** import PASS (**8 workflows**); structured model invocation contract PASS (**4/4**) plus reserved-visual binary MIME contract PASS; workflow JSON and `git diff --check` PASS.

GitHub preservation and production deployment are COMPLETE for this WF03 correction. The verified source is GitHub commit `a839f9497bf794c1e74a395a155b83795ae8c5dc`, parent `dbfdbeef15cc8b7bcd14c0477375382a5f38baa2`, exact tree `c955d84ef1c0b788973cb5771b8d352c0622732d`; the local verification commit had the same exact tree. GitHub Actions materialization run **34202217683** independently applied the verified patch from the exact parent, checked all four target blob SHAs and the whole tree, and produced the GitHub commit before the main branch was fast-forwarded without force.

WF03-only production rollback/evidence directory: `/opt/ai-short-form-content-factory-runtime-backups/voice-budget-a839f94-20260908T080404Z`. It contains the verified source, pre-deploy current+published state, CLI export, SHA256 manifest, import/publish logs, health output and post-deploy parity evidence. Pre-deploy WF03 was active/current `165590b5-43f7-4e1d-b756-966fd1152292`, counter **120**. Import of the exact verified source created current version `18dc3a47-a144-4f7d-a599-6ca5427e1f93` and deactivated it pending publication. The first deploy helper stopped **after successful import and before publish** because cleanup of a root-owned temporary source file returned `Operation not permitted`; exact current/source parity was re-proven before continuing, so no second import was performed. This was an operator cleanup defect, not a workflow/product failure.

`n8n publish:workflow --id=UHxvCZNqaLb1RKMM` explicitly required restart, so exactly one n8n restart was performed. `/healthz` returned `{"status":"ok"}`. Final WF03 is active with `versionId = activeVersionId = 18dc3a47-a144-4f7d-a599-6ca5427e1f93`, counter **119**, **21 nodes**, canonical source/current core SHA256 `793cf8e40186f2d2cb542c192479ea606f73af6478bf0f92580ac902ef5fdbdd`; current nodes/connections/settings equal source and active published-history nodes/connections equal source. Final active/running/waiting/new execution count is **0**. WF02 remains `d651aee0-bc60-4be7-92ff-cb8be9584138`, WF04 `105c934f-235b-4ea7-8e2a-bbef8976bd70`, WF05 `95a87569-2e8f-457f-8563-03ff261b2d3b`, and media-worker remains exact image `sha256:94668bb03228e8fb943ce3be55a666ddad7d1b899ab0e6e2a9900989ab440ddd`; no DB schema or worker change was made.

Next exact step after this deployment record is preserved in GitHub: reread the mandatory gate, verify zero active executions and that no newer normal job appeared, then submit exactly ONE completely NEW normal `{"topic":"How the Panama Canal locks work","language":"ru","duration":15}` job through WF01. Follow it autonomously through WF02→WF03→WF04→WF05 to exact MP4 HUMAN review or preserve/fix the next demonstrated systemic failure. Do not retry or resume `f7401fa2...`.

## 2026-09-08 HUMAN FAIL correction — exact GitHub sync and production deployment complete

The verified HUMAN FAIL correction was preserved on GitHub as commit `5716922ced66e117d89effcb0228c956c25ca5a0`, parent `3e84e8a748b296a3fd40ac33517efd6004de8ee0`, exact tree `f8adb8744cb29be7692790ad14b3142ce78a5e6e`. The preserved VPS verification commit `8480682972bb52a43dfb301c700362fe2ee48d1c` has the same exact tree. GitHub and the clean VPS worktree were fetched and compared before production mutation.

Production deployment is COMPLETE for **WF02 + WF04 + WF05 + media-worker only**. Zero `new/running/waiting` n8n executions existed before mutation and after final verification. Rollback/evidence directory: `/opt/ai-short-form-content-factory-runtime-backups/humanfail-5716922-20260908T062414Z`. The prior worker image `sha256:fe5b0dc2da7fa8e1771ec032b9be77d31757b8e3b3af5909a6f4fcb3fe7a0aec` is retained under rollback tag `ai-short-form-content-factory-media-worker:rollback-humanfail-20260908T062414Z`.

Deployed runtime identities:
- WF02 `TJfA4ZYUEKSTad6k`: active/current version `d651aee0-bc60-4be7-92ff-cb8be9584138`, counter **106**, **34 nodes**, source/current core SHA256 `10ad0062b7a466314bb9a0752c25f86aeaa32f45b1cf3961bf7266482a3d51a2`; current parity PASS and published nodes/connections parity PASS.
- WF04 `M6VisualSourcing1`: active/current version `105c934f-235b-4ea7-8e2a-bbef8976bd70`, counter **214**, **19 nodes**, source/current core SHA256 `55ec302acc7556369ca9c7632b8ee75f256d45f73b78d3e36232964360c16a52`; current parity PASS and published nodes/connections parity PASS.
- WF05 `M7VideoRender1`: active/current version `95a87569-2e8f-457f-8563-03ff261b2d3b`, counter **6**, **16 nodes**, source/current core SHA256 `07064148dc1643ce8cf1ba613a85d89e513f5762fd263bf8f62faf8b093b1cea`; current parity PASS and published nodes/connections parity PASS.
- media-worker runs the exact pre-verified image `sha256:94668bb03228e8fb943ce3be55a666ddad7d1b899ab0e6e2a9900989ab440ddd`; no rebuild was performed during deployment. `/health` returned status `ok` with Pexels, Pixabay and SearXNG configured.
- n8n `2.37.10` publication explicitly required restart; all three workflows were published first and exactly one n8n restart was then performed. `/healthz` returned `{"status":"ok"}`.
- PostgreSQL was not recreated or migrated; its container start timestamp remained unchanged. WF03 and PostgreSQL schema were not modified.

Deployment operator note: the first deployment helper stopped after importing the three exact workflow sources because its parity checker incorrectly treated the one-element n8n workflow-export array as an object. This occurred **before publish, n8n restart, or worker recreation**. Active executions remained zero; a corrected read-only unwrap check proved all three imported current cores exactly matched source, after which the normal publish/restart/worker sequence completed. This was an operator verification-script defect, not a product-code failure.

No new product job has been submitted after this deployment checkpoint yet. Rejected job `515408f3-0f17-4ce4-aaf5-63d709998ee9` remains immutable and HUMAN FAIL. Next exact step: after this deployment record is preserved in GitHub and the mandatory pre-action gate is reread, verify zero active executions and submit exactly ONE new normal `{"topic":"How the Panama Canal locks work","language":"ru","duration":15}` job. Follow that new job autonomously to exact MP4 HUMAN review or preserve/fix the next demonstrated systemic failure; never resume a failed/rejected job.


## 2026-09-07 HUMAN FAIL — sparse visuals + landscape-card framing corrected, pending deployment

Exact autonomous job `515408f3-0f17-4ce4-aaf5-63d709998ee9` reached `review_ready` after WF01 **16438**, WF02 **16439**, WF03 **16445**, WF04 **16449** and WF05 **16450** completed. Exact MP4: `jobs/515408f3-0f17-4ce4-aaf5-63d709998ee9/render/final.mp4`, SHA256 `0f765192024fb2f3cbc241b3eeac3d41509cd54fe7fd6a3745235be7ec66dae6`, H.264 + AAC, 1080x1920, 30 fps, 16.434 s. The user watched this exact artifact and rejected it. The review decision is durably `rejected`: only **3 photos across the entire ~16 s video** is too sparse, and ordinary landscape source photos were displayed as landscape cards inside the phone canvas instead of being composed as native vertical shots. This artifact is **HUMAN FAIL** and must never be treated as accepted.

The defects were systemic and source-proven, not media scarcity:
- WF02's inventory selector reduced the reviewed pool to one image per accepted fact;
- `story_package` then carried one effective visual asset per story unit;
- WF04 hardcoded `planned_shot_count=1`, and WF05 required shot count to equal story-unit count;
- therefore a 3-unit story was structurally forced to contain exactly 3 visual shots;
- the shared visual cadence code already retained the prior rule `duration >= 3.2 s -> 2 shots`, and earlier verified product runs had materially denser unique-photo cadence;
- `services/media-worker/src/visual-framing.mjs` explicitly preserved ordinary landscape photos with a blurred 9:16 background plus a `force_original_aspect_ratio=decrease` foreground, causing the rejected horizontal-card appearance.

Systemic correction prepared in the current verified tree:
1. WF02 image review now binds each accepted image to an existing grounded `supported_claim_id`; freeform model-invented facts are not allowed. Each fact eligible for narration reserves **two distinct reviewer-approved, metadata-consistent, perceptually unique source photos before script generation**. `story_package.assets` remains one bundle per unit for compatibility, with `shot_assets[2]` inside each bundle. No post-freeze search is introduced.
2. WF04 uses exact TTS unit duration and the existing general cadence threshold: `<3.2 s -> 1 shot`, `>=3.2 s -> 2 shots`. Extra shots use only the pre-script `shot_assets`. Global shot numbering, per-segment shot numbering, timing, source-asset identity and perceptual uniqueness are persisted durably.
3. WF04 multi-shot SQL avoids modifying the same `visual_segments` row twice in one PostgreSQL statement. Existing segments are selected `FOR UPDATE`; new 1-shot segments are inserted directly `ready`, new 2-shot segments `planned`, and an existing 2-shot segment receives one completion UPDATE only after its second shot is inserted.
4. WF05 accepts 1-2 shots per story unit, requires the exact ordered shot assets to match the pre-script bundle, requires all rendered source assets/clusters unique, and validates shot timings against the actual visual-shot count rather than story-unit count.
5. Ordinary photos now use full-canvas portrait composition with overscan and restrained pan: `scale=1200:2134:force_original_aspect_ratio=increase` followed by a moving `crop=1080:1920`. They are no longer rendered as blurred landscape cards or static horizontal inserts. Factual diagrams/graphics retain full-image preservation over blurred fill so labels/edge information are not destructively cropped. New composition contract: `portrait-photo-frame-v1`, ordinary photo policy `fill-portrait-crop`, motion policy `portrait-pan-crop`, factual-graphic policy `fit-preserve-with-blurred-fill`.

Exact HUMAN FAIL regression replays the rejected unit durations **4.688 / 5.918 / 5.814 s** through the patched WF04 expansion and proves **6 visual shots**, global shot numbers 1-6, two shots per unit, six distinct pre-script provider assets and six distinct preview hashes, contiguous timing ending at 16.420 s, and no post-freeze media search. Real FFmpeg component proof on a 1920x1080 landscape source produced a 1080x1920 frame using portrait overscan + crop with no ordinary-photo blur/overlay path; the filter contract includes bounded per-frame pan inside the portrait crop.

Verification COMPLETE before deployment:
- Node static regressions: **50/50 PASS**;
- Python static regressions: **13/13 PASS**;
- fresh PostgreSQL contract: **21 workflow SQL statements + staged writes PASS**, including real 1-shot and two-call 2-shot segment lifecycle execution;
- real n8n **2.37.10** import: **8 workflows PASS**;
- structured model invocation: **4/4 PASS**;
- WF04 binary MIME expression PASS;
- workflow JSON parse, Node syntax and `git diff --check` PASS;
- isolated media-worker build PASS, image/source SHA equality PASS and isolated `/health` HTTP 200;
- final post-pan isolated worker image: `sha256:94668bb03228e8fb943ce3be55a666ddad7d1b899ab0e6e2a9900989ab440ddd`; source SHA equality and isolated `/health` HTTP 200 PASS; real FFmpeg landscape-to-portrait pan proof produced `1080x1920` PASS.

PRODUCTION has **not** been changed by this correction yet. Rejected job `515408f3...` is immutable except for its recorded HUMAN FAIL decision. Next exact step: preserve this verified tree in GitHub, verify zero active executions, capture rollback for WF02/WF04/WF05 and the current worker image/source/build inputs, deploy **WF02 + WF04 + WF05 + media-worker only**, verify n8n source/current/published parity and worker image/source/health, then submit exactly one NEW normal Panama/ru/15 job and follow it through exact MP4 HUMAN review. WF03 and PostgreSQL schema remain unchanged.



## 2026-09-07 SAFE LIMIT CHECKPOINT — verified WF02/WF04 fixes NOT YET DEPLOYED

Latest job `b978e057-ab76-413d-8839-bcec6512fbe1` is FAILED and immutable. No MP4.
WF01 **16426** succeeded. WF02 **16427** generated/persisted a 3-unit/3-asset story.
WF03 **16433** completed natural Edge synthesis after three bounded rewrites,
accepted **16.020333s**, mapped exact provider cues into all three story units and
persisted the voiceover. Thus deployed provider-cue fix passed its real product
stage. Child WF04 **16437** then failed at Store Reserved Visual. Upstream workflows
subsequently show error due to the child failure; do not mistake this for a fresh
TTS timing failure. Gateways **16428–16432**, **16434–16436** completed successfully.

Exact execution evidence directory:
`/opt/ai-short-form-content-factory-runtime-backups/fingerprint-b978e057-20260907`.
Raw SHA256s:
- execution-16427.json: `35539cd28731f6e526dcf35fd0614879767b92b574030077253caaa8e744389e`
- execution-16433.json: `65e82c8f764065911754b7074645d9d0ac329e38aa4ee8405ca02b36426cd84f`
- execution-16437.json: `5c88d37b5df8851f9f99c160a2f8361d19a09dec3d252d8a81dfbac493703467`
Decoded copies are saved alongside them as decoded-ID.json.

Three proven defects, corrected in this checkpoint:
1. WF04 Store Reserved Visual Content-Type referenced removed node
   `Prepare Selected Download`, causing `Referenced node doesn't exist` before
   storage. It now uses the actual downloaded binary MIME type directly.
2. WF02 preview fingerprint requests used full visual_target as the legacy rank
   API query. One target exceeded its 200-character limit and emitted a queued
   error, although other candidates advanced through review/story/TTS. Fingerprint
   requests now use the already-validated <=90-character search_query_en; full
   visual_target is preserved untouched as acceptance context. Hashing is not
   semantic authority and the worker itself is unchanged.
3. After WF04 recorded failed/visuals, WF02's delayed fingerprint error overwrote
   the job to failed/script/invalid_rank_query. Record Planner Failure now updates
   only nonfailed jobs and returns the existing failed row without mutation via a
   CTE fallback. First recorded failure, stage and timestamp remain immutable.

Verification COMPLETE before checkpoint: **62/62 static regressions PASS**;
fresh PostgreSQL contract PASS (**21 workflow SQL statements + staged writes**),
including execution of the actual planner failure SQL against an already failed
job and comparison of the whole row before/after; real n8n **2.37.10** import PASS
for all **8 workflows**; all **4 structured invocation contracts PASS**; actual
n8n evaluation of WF04 binary MIME header PASS for JPEG/PNG/MP4. New regression
scans literal node references across all source workflows and exercises a long
visual target with the bounded fingerprint query. JSON parse and git diff check
PASS. No service changes, so no new worker build/deploy is required.

Tested changed blobs (before documentation checkpoint):
- WF02: `719a20551ef9922451ffd16c1e72b8f8d9618902`
- WF04: `f7bb9775432c36f2a58f025e1b29a561fef7adbe`
- fresh_database_contract.py: `c76959cf4652baf13fa6931dd4c8a696ee05e4bc`
- model_invocation_contract.cjs: `a849130eadcc22026cd082f81c03e32df1d4c1fc`
Isolated VPS integration staging: `/tmp/short-form-reserved-contract-20260907`;
blob equality with the tested local files was verified before running the gate.

PRODUCTION STILL uses WF02 source `79e08a6` (flat verdicts), version
`1797c292-8fe2-42c3-a899-5e8f854c07eb`, plus the earlier unchanged WF04 with stale
Content-Type reference. WF03 cue fix `5829569` remains deployed, version
`165590b5-43f7-4e1d-b756-966fd1152292`. Worker remains exact image
`sha256:fe5b0dc2da7fa8e1771ec032b9be77d31757b8e3b3af5909a6f4fcb3fe7a0aec`.
Do NOT redeploy worker, WF03, WF05 or PostgreSQL for this checkpoint.

NEXT EXACT STEP after reading mandatory docs and fetching latest GitHub:
1. Verify checkpoint tree/blob identity and check active/running/waiting/new
   production executions are zero. Do not overwrite newer GitHub work.
2. With SentinelX sentinel_script_run(sudo=true), capture rollback current/
   published JSON + CLI export + source SHA256 for WF02 and WF04.
3. Import and publish ONLY WF02 `TJfA4ZYUEKSTad6k` and WF04 `M6VisualSourcing1`;
   verify current core before publication, restart n8n once if CLI requires it,
   then health and source/current/published nodes/connections/settings parity.
4. Commit/push deployment evidence. Submit ONE new normal
   `{"topic":"How the Panama Canal locks work","language":"ru","duration":15}`
   via POST localhost:5678/webhook/jobs inside the n8n container. On an uncertain
   response check PostgreSQL before considering another POST.
5. Follow the new job autonomously through WF05. If it fails, preserve exact
   execution evidence and fix only proven systemic defects; no manual job rescue.
   If MP4 exists, verify DB/path/SHA256/ffprobe and deliver that exact file for
   human review. Machine completion is not HUMAN PASS.

Reliable GitHub transport in this desktop session: local authenticated git push
works. Fetching native Git objects over SSH from the VPS also works and preserves
exact tree/blob SHAs; VPS HTTPS push credentials are not needed. Current local
checkout: `/Users/hodor/Documents/Codex/2026-09-06/production-github-pokhyl-ai-short-form/work/continuation`.
No running job was submitted after b978e057. No final MP4 or HUMAN PASS yet.

## 2026-09-07 flat image verdict identity — deployed, fresh normal job running

Job `2fac6817-43ad-416c-a205-8f7704048f08` failed/script in WF02 **16421**:
`pre-script verified visual inventory 1/3`. WF01 **16420** and gateways **16422–16425**
succeeded. Query validation correction worked. Exact execution backup:
`/opt/ai-short-form-content-factory-runtime-backups/inventory-2fac6817-20260907/execution-16421.json`,
SHA256 `41dab53ddb93f344f717ac80c9a52d939938672bd5d418d026ab0a6d711483eb`.
Decoded evidence is alongside it. No final story/TTS/MP4; failed job untouched.

The reviewer returned all 12 shown image verdicts within JSON claim_number 1,
including accepted C1-I3 and C3-I1. Selector still indexed decisions by origin
claim group despite global image review. Thus C3-I1 was silently ignored. Exact
read-only replay: as returned, only Pixabay 5024962 survives; regrouping the same
verdicts by their existing review_id yields two valid unique assets (also Commons
Miraflores Lock Panama Canal 2006 24.JPG), each passing metadata consistency with
3 hits. **This remains 2/3, not an accepted job or proof of sufficient inventory.**

Correction simplifies the model contract to flat `verdicts[]`, addressed solely
by the already-global `review_id`. Selector requires exactly one verdict for every
shown ID and rejects unknown, duplicate or missing IDs explicitly. Origin groups
remain audit data only. Structured schema and prompt match the flat contract.
No relevance, metadata, evidence, asset uniqueness or minimum-inventory gate changed.

Verification: **61/61 static regressions PASS**, including shuffled/global verdicts,
multiple observed facts per retrieval origin, and missing/duplicate/unknown ID
rejection; fresh PostgreSQL (21 statements plus staged writes) PASS; real n8n
2.37.10 import (8 workflows) PASS; actual structured invocation contracts (4) PASS.
VPS isolated gate source blob SHAs matched local tested files. Worker unchanged.
Next: push verified tree, back up/deploy WF02 only, verify current/published parity,
then one NEW normal job. Remaining uncertainty is semantic inventory sufficiency;
canonical article coverage is still zero for the unverified resolver phrase.
Deployed WF02 only from `79e08a6b210df9ccf69e48f5201012b713c9fae9`, exact
tree `e1257c1adabffacdd7b3960cffa6bc1d5f2c4d68`. Rollback:
`/opt/ai-short-form-content-factory-runtime-backups/flat-review-79e08a6-20260907T154602Z`.
Source/current/published parity PASS; active/current version
`1797c292-8fe2-42c3-a899-5e8f854c07eb`, 34 nodes, core SHA256
`80d52802870139c618a471e51284f388a7091bb52ae95b400a5f6f25b3786690`.
Health HTTP 200 after one CLI-requested n8n restart; zero active executions before
new intake. ONE new normal POST HTTP 201: `b978e057-ab76-413d-8839-bcec6512fbe1`,
Panama Canal / ru / 15. Next: follow this exact autonomous job to MP4 or capture the
next demonstrated failure. No MP4 or HUMAN PASS yet.

## 2026-09-07 provider query validation — deployed, fresh normal job running

New job `2497062e-6636-4247-8e3f-5a200eaa51fe` failed/script before reaching WF03.
WF01 **16415** succeeded; WF02 **16416** failed at Validate Candidate Claims:
`candidate claim C2 needs a compact search_query_en`. Gateways **16417–16419**
succeeded. Exact execution evidence is saved under
`/opt/ai-short-form-content-factory-runtime-backups/query-contract-2497062e-20260907`.
Execution 16416 SHA256: `76d0798d007eaa14921a40658fc39a3f33398fa557d00de764260e8e86aad613`;
16419: `09a44dd5095ec419aeb243cfffc5a9686c1b774ccef368abfd7c587cbe8515ee`.

Cause: the model returned a useful nine-word query, `Panama Canal lock chamber
water fill cross section illustration`, well within the provider's existing
90-character budget. An arbitrary eight-whitespace-word ceiling rejected the
whole job. No malformed JSON, missing query or provider failure occurred.
Correction removes the upper word-count restriction rather than raising it to
another arbitrary number. Queries still require at least two words and <=90
characters; the same maxLength is now explicit in the structured response schema.
No fact, evidence, semantic, relevance, uniqueness or duration gate changed.

Verification: **61/61 static regressions PASS**, including longer multiword queries
within the character budget and rejection of empty/single-word/>90-character
queries; fresh PostgreSQL PASS (21 workflow statements plus staged writes); actual
n8n **2.37.10** import PASS (8 workflows); 4 actual model invocation contracts PASS.
Integration gates used an isolated VPS staging copy whose changed blob SHAs equal
the local tested files. Worker and all other workflows are unchanged.
Next: push exact verified tree, back up and deploy WF02 only, verify active/current/
published parity, then create exactly one NEW normal job. Do not resume failed
2497062e or 66fda166. WF03 cue correction is already deployed and awaits E2E use.
Deployed WF02 only from GitHub `01da7cad49b42fded47dafbb18ef850332ceba91`,
exact tree `120d7337c2d8a04e722c4fff3dfa0744e673a137`. Rollback:
`/opt/ai-short-form-content-factory-runtime-backups/query-budget-01da7ca-20260907T153710Z`.
Source/current/published parity passed (34 nodes, connections, current settings);
active/current version `4e7af24c-f583-4c3f-903f-aaf07538a25d`, canonical core SHA256
`1b5aaf6173cb467d6c2f729808a14c52405166ffbae985a1fef7f1826a9985d3`.
One CLI-requested n8n restart, health HTTP 200, zero active executions before POST.
NEW normal job: `2fac6817-43ad-416c-a205-8f7704048f08`, Panama Canal / ru / 15,
HTTP 201; exact response saved in rollback directory. Next: follow this job E2E.
WF03 remains on verified cue mapping; worker remains unchanged. No MP4/HUMAN PASS.

## 2026-09-07 provider cue mapping — exact GitHub sync and WF03-only deployment

Verified VPS commit was transferred as native Git objects via SSH fetch and pushed
without force from the local authenticated checkout. GitHub now contains exact
commit `5829569857d7ab61ae1be85b34e1d958726a63ed`, parent
`a2b7c183e6c48abeef5e8f77410d700dd53c5724`, tree
`8d0aeaf5e05f3a0262b277d1d0a559418e4a0449`. All three changed blob SHAs matched;
post-push fetch confirmed the same parent/tree. The transport branch was not used.

WF03 ONLY deployed using SentinelX sudo scripts. Zero active/running/waiting/new
executions before mutation. Rollback current/published JSON, CLI export, verified
source and SHA256 manifest:
`/opt/ai-short-form-content-factory-runtime-backups/provider-cue-5829569-20260907T152925Z`.
Current import parity passed before publishing. n8n CLI requested restart; exactly
one restart performed. `/healthz` returned HTTP 200, status ok. WF03 active,
current version = activeVersionId = `165590b5-43f7-4e1d-b756-966fd1152292`.
All 21 nodes, connections and current settings equal source; published history
nodes/connections equal source (n8n history does not store a separate settings
field). Canonical source/current core SHA256 (sorted JSON, UTF-8, compact separators):
`6664b28af13aef018fab473cc4f912e58ba82c83774f9f9fd9ca1fb101d8286c`.
Zero active executions after restart. WF02/WF04/WF05, PostgreSQL and media-worker
were not redeployed; worker remains image `fe5b0dc2da7f...`.

ONE new normal WF01 POST returned HTTP 201: job
`2497062e-6636-4247-8e3f-5a200eaa51fe`, Panama Canal / ru / 15. Response persisted
in the rollback directory as `normal-job-response.json`. Next: follow WF01–WF05
and inspect exact output/failure. Do not modify failed `66fda166...`.
No MP4 or HUMAN PASS yet.

## 2026-09-07 provider multi-token cue unit-boundary defect — verified, pending WF03 deployment

The Edge provider-tail correction is deployed in production from GitHub commit `a2b7c183e6c48abeef5e8f77410d700dd53c5724`, exact tree `516979685b2b5fcd9a2c4aac076781e13f2a291c`. Media-worker-only deployment replaced image `sha256:30843256898826e6f59e719c1c55a820dafb6b50f910a3f6b1006e9eded90a9d` with `sha256:fe5b0dc2da7fa8e1771ec032b9be77d31757b8e3b3af5909a6f4fcb3fe7a0aec`; rollback snapshot is `/opt/ai-short-form-content-factory-runtime-backups/edge-tail-a2b7c18-20260907T144148Z`. Worker health returned HTTP 200 with Pexels, Pixabay and SearXNG configured; n8n/PostgreSQL were not recreated.

NEW normal job `66fda166-7768-46ed-b058-457ff43b7749` (How the Panama Canal locks work / ru / 15) was created once through WF01 HTTP 201. WF01 **16384** succeeded. WF02 **16385** progressed normally through model gateway executions **16386–16390**. WF03 **16391** synthesized three unchanged-speed Edge attempts after two bounded story rewrites. The final accepted-duration WAV was **16.383333s**, provider source WAV **17.208s**, final exact word cue ended at **16.350s**, provider-tail trim **0.824667s**, `rate_percent=0`, `post_tempo_factor=1`. WF03 then failed closed with `Provider timing diverges inside story unit 2 [line 13]`; no WF04/WF05 or MP4 was produced. The failed job remains immutable.

Exact WF03 execution data is preserved at `/opt/ai-short-form-content-factory-runtime-backups/provider-timing-66fda166-7768-46ed-b058-457ff43b7749-20260907/execution-16391.json`, SHA256 `0b0808a464622e0b8094983da7a0fc1f477f57656d48af0d1eced15c1e836d00`.

Systemic cause: `Build Exact Story Unit Timings` incorrectly assumed one Edge provider timing cue always equals one whitespace-delimited narration word. Edge can legitimately group multiple spoken words into one exact timing cue; in this execution unit 2 contained narration `...на 26 метров к...` while provider timing represented `26 метров` as one cue. The complete provider cue sequence still reconstructed the full final narration exactly, so the failure was a unit-boundary indexing defect, not a TTS/text divergence.

Correction: story-unit mapping now consumes whole provider cues until their normalized text exactly equals each complete story-unit narration. A partial accumulation must remain an exact word-boundary prefix of that unit; otherwise it still fails closed. Provider cues are never split and no synthetic timestamps are created. If one cue crosses an actual story-unit boundary, or the provider text does not reconstruct the unit exactly, the same divergence gate still rejects the run.

Verification: targeted story-unit timing regression now includes a multi-word provider cue (`26 meters`) and PASSes; the related exact-TTS/fit/word-timing regressions PASS. Full ordinary static suite: **48/48 Node + 13/13 Python = 61/61 PASS**; fresh PostgreSQL contract PASS (**21 workflow SQL statements + staged writes**); real n8n **2.37.10** import PASS for **8 workflows**; structured model invocation contract PASS for **4 calls**; workflow JSON parse and `git diff --check` PASS. Exact saved execution **16391** replay through the patched `Build Exact Story Unit Timings` node PASSes with duration **16.383333s** and exact unit ranges **0–5.300**, **5.300–11.149**, **11.149–16.383**.

Next: preserve this exact verified tree in GitHub, deploy **WF03 only** with rollback/source-current-published parity, then submit one completely NEW normal product job. Do not resume or edit `66fda166...`. No MP4 or HUMAN PASS yet.

## 2026-09-07 Edge provider tail silence — verified, pending worker deployment

The previous story-persist correction is deployed in production from GitHub commit `c6124f528a5798502567e8f4f7d7c108e46558ab`, exact tree `bfb26fd33828d327207cd0fb3260975081f3b28b`. WF02 current/active version is `750687ba-bc44-480d-b189-389029be41cf`; source/current/published core parity passed before the new run.

NEW normal job `0b025bcf-00b6-4548-8cc3-80d4e0eb982b` (How the Panama Canal locks work / ru / 15) was created through WF01 HTTP 201. WF01 **16356** succeeded. WF02 **16357** succeeded end-to-end through semantic resolution, research, verified global unique inventory and final story; Model Gateway executions **16358–16362** all succeeded. WF03 **16363** then failed closed in `voiceover`: `Voiceover duration 16.704s is still outside target after 3 story rewrites`. Duration-rewrite gateways **16364–16366** all succeeded. The failed job remains immutable; no WF04/WF05 or MP4 was produced.

Exact WF03 execution data is preserved at `/opt/ai-short-form-content-factory-runtime-backups/voice-duration-0b025bcf-20260907/execution-16363.json`, SHA256 `d0c8066d1393f7582bfd8d2f4c0bcaa3deeb606eb7c557339f19a6d1110b5267`. Exact execution replay showed four unchanged-speed Edge measurements: **41 words / 20.832s**, **34 / 17.784s**, **32 / 17.304s**, **32 / 16.704s**. The controller requested approximately 30, 29 and 28 words, but its broad rewrite acceptance allowed longer outputs. More importantly, every Edge synthesis contained a stable provider-added trailing gap of about **0.93–0.95s after the last exact word cue**. On the final 16.704s WAV, the last provider word ended at **15.775s**; counting the provider tail as spoken narration alone pushed the otherwise valid speech outside the existing 15s gate.

Systemic correction is in the media-worker only. Before the existing natural-tail pad and exact-duration gate, the worker now uses Edge's provider word cues to trim only audio after the final exact word boundary while preserving one 30fps frame of post-roll. Spoken samples, words and provider timing are untouched; `rate_percent=0` and `post_tempo_factor=1` remain mandatory. The existing short-narration tail pad, duration thresholds, story rewrite loop, WF02/WF03 semantic contracts and all reviewer/evidence gates are unchanged. This is not speech-speed manipulation and cannot rescue narration whose actual spoken span is too long or too short.

Verification: **48/48 ordinary Node static regressions PASS** (the separate real-provider dry-run intentionally requires `JOB_CONTEXT_FILE`) plus **13/13 Python regressions PASS**; fresh PostgreSQL contract PASS (**21 workflow SQL statements + staged writes**); real n8n **2.37.10** import PASS for **8 workflows**; structured model invocation contract PASS for **4 calls**; media-worker syntax, `git diff --check` and Docker build PASS. A real isolated Edge synthesis using the exact failed 32-word narration returned HTTP 200 with provider WAV **16.704s**, last word **15.775s**, provider-tail trim **0.895667s**, final WAV **15.808333s**, **32 exact word timings**, `rate_percent=0`, `post_tempo_factor=1`, and no synthetic tail pad.

Next: preserve this exact verified tree in GitHub, deploy **media-worker only** with rollback/image identity and health checks, then submit one completely NEW normal product job. Do not resume or edit `0b025bcf...`. No MP4 or HUMAN PASS yet.



## 2026-09-07 story persist return-value defect — verified, pending deployment

NEW normal job `99d20c0f-b7e4-4aac-8715-680e62794f6b` (How the Panama Canal locks work / ru / 15) ran against the deployed global-unique pre-review shortlist. WF01 **16349** succeeded. WF02 **16350** completed semantic resolution, research, candidate claims, global unique review, verified inventory and final story generation; Model Gateway executions **16351–16355** all succeeded. The database contains an `inventory-first-story-v1` story package with **3 units / 3 assets**, but WF02 then failed closed with `story package persisted null/3 units [line 1]`. The failed job remains untouched; no WF03/WF04/WF05 or MP4 was produced.

Exact execution data is preserved at `/opt/ai-short-form-content-factory-runtime-backups/unique-566366a-20260907T112245Z/execution-16350.json`, SHA256 `fa316ede8bbd70c24656584322d6adad2a306ede9f418275cfe6320c15e02911`.

Systemic cause: `Persist Inventory First Story` performs the job update inside a PostgreSQL data-modifying CTE `upd`, then its final SELECT re-read `public.jobs.story_package` in the same SQL statement. That read uses the statement snapshot and therefore observes the pre-update `story_package = NULL`, even though the UPDATE is persisted by statement completion. `Require Persisted Inventory Story` consequently produced a false failure. This is a persistence return-value contract defect, not a story-generation or inventory failure.

Correction: `upd` now returns `jsonb_array_length(j.story_package->'units')::int AS story_unit_count`, and the final SELECT reads `story_unit_count` from `upd` instead of re-reading `public.jobs`. The real fresh-PostgreSQL contract now executes this exact persist statement on a new eligible job and requires the returned row to report one inserted evidence item, `job_updated=true`, zero pre-TTS scenes and `story_unit_count=3`. Static regression also forbids the same-snapshot table re-read from returning.

Verification after correction: **60/60 static regressions PASS** (47 Node + 13 Python); fresh PostgreSQL contract PASS (**21 workflow SQL statements + staged writes**, including the actual persist return-value path); real n8n **2.37.10** import PASS for **8 workflows**; structured model invocation contract PASS for **4 calls**; workflow JSON parse and `git diff --check` PASS. Worker, reviewer, semantic/evidence gates and minimum inventory are unchanged.

Next: preserve the exact verified tree in GitHub, deploy **WF02 only** with rollback/source-current-published parity, then submit one NEW normal product job. Do not resume or edit `99d20c0f...`. No MP4 or HUMAN PASS yet.


## 2026-09-07 unique shortlist deployed — fresh job running

Source commit `566366a74b3202b668bcb34b5b38794bbf8ebf72`, exact verified tree `52a6009592a1b3bf9e0279190133220a06d9d192`, is now deployed to WF02 only. Current/published nodes and connections match source; active/current version `53b3f193-faf7-4b2e-94c5-2c00216d9d43`. No active/waiting executions existed before deployment. n8n 2.37.10 restarted; worker unchanged. Rollback: `/opt/ai-short-form-content-factory-runtime-backups/unique-566366a-20260907T112245Z`.

NEW normal job `99d20c0f-b7e4-4aac-8715-680e62794f6b` created through WF01 HTTP 201 with How the Panama Canal locks work / ru / 15. Earlier startup request returned 404 without creating a job. Next: follow exact execution through E2E; fix further demonstrated general defects autonomously, without manual rescue or gate weakening. No MP4/HUMAN PASS.

## 2026-09-07 global unique pre-review shortlist — verified, pending deployment

Continuation from `a2ce67803d578c898d3121c8f66b9b849820e470` in `/opt/ai-short-form-content-factory-unique-review-20260907`. WF02 now builds one ranked round-robin pool across all fingerprinted discovery buckets before image review. Provider identity and perceptual duplicates (existing distance <=18) cannot consume repeated review slots; remaining unique candidates fill slots up to the unchanged total budget of four images per original retrieval hypothesis, with at most 24 images per model batch. Origin fields remain available for audit, but proposed hypothesis text is no longer shown as an acceptance cue. Full research corpus and all reviewer/final metadata/evidence/uniqueness gates remain. Minimum inventory is counted in unique assets, not productive origin buckets.

Cross-topic clock/telescope regression verifies exposure diversity, budget, multi-batch splitting, one productive bucket, perceptual duplicates and target-anchor rejection. Exact failed execution 16344 replay yields **20 unique review images instead of 9**, with the same 20-slot budget; this is component evidence, not semantic/E2E acceptance. Unchanged selection replay confirms C3-I1 was rejected by metadata consistency and only C5-I4 survived, producing the recorded 1/3 failure.

Verification: **60/60 static regressions PASS**, fresh PostgreSQL contract PASS (21 SQL statements plus staged writes), isolated real n8n 2.37.10 import PASS (8 workflows), structured invocation contract PASS (4 calls), git diff check PASS. Worker unchanged. Last product job remains failed `87af4f4b-83d8-4bdc-b110-725f1a6d6f40`, WF02 16344. Next: preserve exact verified tree in GitHub, deploy WF02 only with rollback/parity, and submit a NEW normal product job. No MP4 or HUMAN PASS.

## 2026-09-07 fresh global-pool execution — failed, review shortlist defect confirmed

Latest job `87af4f4b-83d8-4bdc-b110-725f1a6d6f40` (How the Panama Canal locks work / ru / 15) failed/script in WF02 **16344**: `pre-script verified visual inventory 1/3`. Intake **16343** succeeded. Gateways **16345–16348** completed; candidate drafting **16347** succeeded through Kilo; actual-image reviewer **16348** fell back from Kilo length/empty output to successful Gemini JSON. No final story, voice or MP4 was produced. Failed jobs remain untouched.

Confirmed general defect from exact execution and source: review shortlisting is still bucket-local. `Prepare Inventory Review Batches` applies `fingerprinted_candidates.slice(0,4)` separately per origin claim, and global identity/perceptual dedupe occurs only AFTER model review. This execution had 40 fingerprinted occurrences representing **28 unique provider assets**, but **20 review image slots represented only 9 unique assets**. Three Pixabay identities occupied 14 slots (4/5/5 occurrences); **19 unique fingerprinted assets never reached the reviewer**. This proves wasted review exposure, not that omitted images would necessarily pass semantic review or provide the required three facts.

The reviewer approved two occurrences; deterministic selection retained one. Reviewer output also warrants semantic scrutiny: an aerial-lock description was paired with a causal claim about ocean-level differences and the choice of canal design, while a general route-map description was paired with six lock steps. Those descriptions alone do not establish that the claimed causal/quantitative details are visible. Do not loosen reviewer or metadata gates to increase acceptance.

Runtime evidence captured at `/opt/ai-short-form-content-factory-runtime-backups/global-11d8c6a-20260907T110915Z/execution-16344.json`. Deployed workflow source remains `11d8c6a4a2d6ad632c28443cc14519d9de645731`, exact tested tree `e0fbd278cf092c3735832ec1cc1e3a9a165d23e5`; deployment continuity commit `c6541a76818b5c4da0179d15c1dadf933702ab33`. No unverified product-code changes were made after this failure.

Next exact engineering step: implement a global unique pre-review shortlist from the fingerprinted pool, preserving origin metadata for audit and the existing total image budget, evidence grounding, actual-image authority and final uniqueness gates. Add cross-topic regression proving duplicate retrieval buckets cannot consume repeated review slots while unique candidates remain; test a single productive discovery bucket without requiring a minimum number of origin buckets. Inspect the exact two model-approved observations through the unchanged deterministic gates. Verify the full required contracts, commit through GitHub connector, deploy only verified changes with rollback/parity, then submit a NEW normal job. Current blocker is pre-review exposure diversity and unproven semantic inventory quality. No HUMAN PASS.

## 2026-09-07 global observed-pair pool — deployed, fresh job running

Verified VPS commit `b6acede19dd2c55400cdfa92e4e25436dd71235f` was preserved through the connected GitHub API as `11d8c6a4a2d6ad632c28443cc14519d9de645731`, fast-forward from `dbd1567145b64836b5ce4a610b3e9e16167bcab3`. All four blob SHAs and exact tree `e0fbd278cf092c3735832ec1cc1e3a9a165d23e5` match the tested VPS commit. The original checkout remains clean and preserved; HTTPS git push on VPS lacks credentials, so use the connected GitHub API for continuity writes.

WF02 only was imported and published on production n8n 2.37.10. Source/current/published nodes and connections match (34 nodes); current/active version `12549e8e-6fc6-4e10-9c0d-fdb5146be528`. No running/waiting executions existed before deployment/restart. Worker was unchanged. Rollback capture: `/opt/ai-short-form-content-factory-runtime-backups/global-11d8c6a-20260907T110915Z` (current and published WF02 plus exact deployed source). n8n restarted and logged activation of the product workflows.

NEW normal WF01 intake returned HTTP 201, job `87af4f4b-83d8-4bdc-b110-725f1a6d6f40`: How the Panama Canal locks work / ru / 15. An earlier request during startup returned HTTP 404 and did not create a job. Failed `908621d8...` remains untouched. Next: inspect new job execution and follow autonomous WF02–WF05 to exact MP4 or capture a systemic failure. No MP4/HUMAN PASS yet.

## 2026-09-07 global observed-pair pool — verified, pending deployment

The prior PostgreSQL-credential correction was committed as `dbd1567145b64836b5ce4a610b3e9e16167bcab3` and deployed to WF02 only. Production source/published parity passed with 34 nodes; n8n remained 2.37.10, worker provider health still reported Pexels, Pixabay and SearXNG configured, and rollback backup is `/opt/ai-short-form-content-factory-runtime-backups/story-persist-dbd156-20260907T050941Z`.

A NEW normal product job `908621d8-9c6f-45ab-9680-6f08852c76e7` (Panama Canal / ru / 15) then failed closed in WF02 execution **16333** with `pre-script verified visual inventory 1/3`. No story package, voice or MP4 was produced. Discovery itself was not empty: real provider inventory contained ships in Panama Canal locks, a historical lock cross-section, lock photographs, Gatun/expansion imagery and other candidates. The image reviewer correctly approved a ship in a lock and a technical lock cross-section, while rejecting many mismatches.

The remaining systemic defect was claim-local isolation after discovery. Each candidate image was reviewed only against the evidence IDs of the claim that happened to retrieve it, and the selector could reserve at most one approved asset from each discovery claim. Therefore a useful image retrieved under one hypothesis could not support a different research-backed fact, and two distinct truthful observed facts from one productive search bucket could not both enter the final story inventory. The discovery hypothesis had accidentally become a hard partition even after the architecture moved toward observed image/fact pairs.

Correction in the current clean checkout: the reviewer receives the full research corpus for every review batch and is explicitly told that the discovery claim/target is only the retrieval origin, not the factual acceptance boundary. A reviewed image may bind to any 1–3 valid global research evidence IDs when its visible content directly supports that fact and the resolved subject/user intent. Deterministic selection validates those IDs against the global research inventory, keeps the existing target-anchor gate and image/metadata consistency check, then flattens all approved observations into one global pool. More than one distinct observed pair may come from the same discovery hypothesis. Provider identity, exact supported-fact duplicates and perceptual duplicates remain forbidden; accepted observations receive fresh sequential story claim/asset IDs while the original discovery claim, target and evidence IDs are retained as audit fields. No relevance weakening, unreviewed fallback, topic-specific query, duplicate asset or post-script rescue is introduced.

Verification after the correction: **59/59 static regressions PASS** (46 Node + 13 Python); the observed-inventory regression explicitly proves cross-hypothesis evidence binding and multiple final observations from one discovery bucket while rejecting unknown/empty evidence; n8n **2.37.10** import contract PASS for all 8 workflows; fresh PostgreSQL contract PASS for 21 workflow SQL statements plus staged writes; all 4 structured model invocation contracts PASS; workflow JSON and `git diff --check` PASS. Worker code is unchanged.

Next: commit/push this verified WF02-only logical correction, deploy it with rollback capture and source/published parity, then submit a completely NEW normal `topic + language + duration` job. Failed jobs are not resumed. No MP4 or HUMAN PASS yet.


## 2026-09-07 story persistence credential contract — verified, pending deployment

New normal job `7dd0361a-916f-47d6-9263-e37f662ee443` (Panama Canal / ru / 15)
ran against deployed observed-inventory WF02. WF02 execution **16326** reached the
new causal path successfully: candidate claims, real provider discovery, image
review, observed facts/assets, and final inventory-grounded story all completed.
The selected package contained three distinct observed bindings (ship-in-lock,
visible culvert/tunnel opening, and Gatun Locks/Lake aerial view). Final story
model execution succeeded, but the job then failed/script with
`inventory-first story did not update job ...`.

Exact cause: `Persist Inventory First Story` was a new PostgreSQL node whose source
export omitted its `Application PostgreSQL` credential reference. n8n import and
fresh SQL preparation did not detect that runtime credential requirement; live
execution reported `Node does not have any credentials set`. Failure persistence
then correctly marked the job failed; the failed job is not resumed.

Systemic correction: every exported `n8n-nodes-base.postgres` node must carry an
explicit PostgreSQL credential reference. `Persist Inventory First Story` now uses
the same `Application PostgreSQL` credential as the existing WF02 DB nodes, and a
cross-workflow regression checks all PostgreSQL nodes for both credential id and
name so newly added DB nodes cannot silently import without runtime credentials.

Verification after correction: **59/59 static regressions PASS** (46 Node + 13
Python); n8n **2.37.10** import contract PASS for all 8 workflows; fresh PostgreSQL
contract PASS (21 workflow SQL statements plus staged writes). Worker code is
unchanged. Next: commit/push this verified logical stage, deploy WF02 only with
rollback capture and source/published parity, then submit a NEW normal job. No MP4
or HUMAN PASS yet.


## 2026-09-07 observed inventory contract — verified, pending deployment

Job `9705e087-e2ee-41db-b6d5-9d9d277a089c` failed/script in WF02 **16307**
with `pre-script verified visual inventory 0/3`. Gateways **16310** (claims) and
**16311** (review) succeeded. All five secondary detail queries ran, with no
provider errors. New closed-gate imagery was retrieved but rejected because the
hypothetical target additionally demanded a ship. Another target demanded hidden
culverts; others prescribed photographic states that the results did not show.
No final narration, voice or MP4 was generated; job remains untouched.

This demonstrates a deeper contract error than search length: exact hypothetical
composition remained frozen before inventory, so final story could not adapt to
what could truthfully be shown. Further keyword tuning alone is insufficient.

WF02 now establishes an observed image/fact pair before final narration. The
multimodal reviewer receives the cited research snippets and returns actual visible
content, a supported factual proposition (which may narrow the proposed claim),
and 1–3 supplied evidence IDs. It must reject merely thematic content and exterior
photos used to narrate invisible internals. Selection requires nonempty grounding,
IDs within the original claim's evidence, image/metadata consistency, subject
anchors and distinct perceptual hashes. The reserved claim and visual target use
this observed pair; original claim/target are retained as audit fields. Final story
can use only reserved facts/assets. This supersedes historical wording that the
unverified proposed visual target is an immutable acceptance criterion. No
post-script discovery, threshold reduction, duplicate visual or manual intervention.

Verification: 58/58 static regressions PASS (one prompt wording assertion corrected
in the prompt, then rechecked); fresh PostgreSQL and n8n 2.37.10 import of all 8
workflows PASS; actual structured invocation contracts PASS. Worker is unchanged
from the built/verified/deployed bcd0788 image. New causal tests reject unknown or
empty evidence, empty facts and rejected images; verify cited snippets reach review
and only the observed pair reaches final story. Semantic quality still requires
new autonomous execution and human inspection of the final MP4.
Next: deploy verified WF02 with backup/source-published parity; create a NEW normal
job. Do not resume any failed job. Canonical Wikipedia title resolution remains
an identified coverage limitation, not a proven global shortage of free media.

## 2026-09-07 detail retrieval — deployed, fresh job running

Latest completed product job `47c59975-2f39-46e4-9e54-f5816a944998`
(Panama Canal / ru / 15) failed/script in WF02 **16301**:
`pre-script verified visual inventory 1/3`. Candidate gateway **16304** and image
review **16305** succeeded. Short search queries reached providers correctly.
Only C1 gained Commons images; C2–C5 again received the same three Pixabay images.
No provider errors, zero secondary queries, zero canonical article media.
Canonical source title was `Panama Canal lock operational mechanism`, not a
verified Wikipedia page: this separate canonical-media coverage issue remains.

Verified system defect: generic subject-anchor matches satisfied the inventory
candidate-count condition and suppressed detail retrieval; provider order then
controlled the four-image review shortlist. Targets also prescribed unnecessary
camera arrangements, hidden internals and time-lapse photographs before inventory
existed. Reviewer rejected 15/16 candidates; acceptance was not bypassed.

Changes: pre-script inventory issues at most one shorter subject + detail query
in addition to the initial query, independent of generic hit count; ranks results
by distinguishing query terms before fingerprint/review. Existing semantic gates,
perceptual uniqueness and minimum inventory remain. Legacy timed discovery is
unchanged. Candidate instructions require minimal observable supporting content
and disallow invented composition or invisible processes in a still photograph.
This is a retrieval correction, not proof of end-to-end quality.

Verification: **57/57 static regressions PASS**, including independent clock and
radio telescope cases where generic photos cannot suppress detail retrieval;
fresh PostgreSQL contract PASS (21 statements plus writes); import of all 8
workflows into actual n8n **2.37.10 PASS**; 4 real expression invocation contracts
PASS; media-worker Docker build PASS. Next: back up and deploy this verified
WF02/worker change, verify published/source parity and provider health, submit a
NEW job via normal topic/language/duration. Both failed jobs remain untouched.
Deployed verified source `bcd0788`; WF02 current/published nodes and connections
match source. Worker image is
`sha256:30843256898826e6f59e719c1c55a820dafb6b50f910a3f6b1006e9eded90a9d`.
Backup: `/opt/ai-short-form-content-factory-runtime-backups/detail-bcd0788`, old
worker image tag `pre-detail-bcd0788`. Pexels/Pixabay/SearXNG health all configured.
n8n remains 2.37.10 and was restarted after publication with no running executions.
NEW normal product job (HTTP 201): `9705e087-e2ee-41db-b6d5-9d9d277a089c`,
How the Panama Canal locks work / ru / 15. Immediate next step: inspect this job's
autonomous execution and candidate/reviewer evidence. Do not rescue it manually.
No MP4 or HUMAN PASS yet.

## 2026-09-07 pre-script retrieval correction — deployed, fresh job running

New job `897293fa-9627-4f09-b7e0-fc9c49562ba2` failed/script in WF02 **16295**:
`pre-script verified visual inventory 1/3`. Invocation is proven fixed: candidate
claim gateway **16298** succeeded with valid JSON, then visual review **16299**
succeeded and rejected irrelevant imagery. No final story/TTS/MP4 was generated.

Exact execution inspection: five long visual descriptions became truncated
90-character provider queries; claims 1–4 received mostly the same 2–3 Pixabay
canal photos. Reviewer rejected those for diagram/gate/basin targets; only claim
1 retained a verified visual. This is retrieval/acceptance-contract conflation,
not a reason to weaken semantic verification or lower the required inventory.

Correction: candidate claims explicitly contain a validated 2–8 word, <=90 character
`search_query_en`; pre-script provider retrieval uses it while preserving the full
`visual_target` and every existing reviewer/uniqueness gate. No post-script search,
manual rescue, topic-specific query or asset reuse is introduced.

Verified: 56/56 static regressions PASS, fresh PostgreSQL (21 SQL statements) PASS,
real n8n 2.37.10 import of 8 workflows PASS, actual expression invocation regression
PASS for all four structured calls, worker build PASS.
Deployed source `077cc32` to WF02 and media-worker. Native VPS image:
`sha256:a3e84a103a8cc4ec8a51cd375f1643580a7f0526f4d92f58bc1a19ba69ca8e5a`.
WF02 current/published definitions match source; n8n remains 2.37.10.
The existing production Compose omitted SEARXNG_URL despite the configured old
container. Recreating worker exposed this drift before any job submission. Added
the already-committed default SEARXNG_URL to production Compose; health now reports
all three providers configured and a real research request returned HTTP 200 with
20 results. Backup/source staging: `/opt/ai-short-form-content-factory-runtime-backups/query-077cc32`;
old image retained as `ai-short-form-content-factory-media-worker:pre-query-077cc32`.

NEW normal WF01 job (HTTP 201): `47c59975-2f39-46e4-9e54-f5816a944998`,
How the Panama Canal locks work / ru / 15. Next: inspect its autonomous execution
and actual returned inventory, then continue to exact MP4 or a systemic failure.
Failed `897293fa...` remains untouched. Overall MP4 quality is unproven.

## 2026-09-06 invocation correction — deployed, fresh E2E running

Continuation base: `086830485d986aa64e77af980f6ef6a4b8206de5`, tree
`3cdf959ede9af8caec65b63016380a1bb5dc56c6`. Inventory-first is deployed; older
pre-production statements below are historical. Production n8n is **2.37.10**;
Compose and import tests are now pinned to that actual version, without downgrade.
WF02/WF03 runtime nodes/connections/settings matched this base before correction.

Latest product job `f7ef9f04-c6db-47af-b90f-1d6747ce6f2f` (Panama Canal locks,
ru, 15) failed/script at Draft Candidate Claims in WF02 execution **16291**.
Gateway 16292/16293 succeeded for topic resolution, but no gateway invocation
was created for the claim draft. The failed job is not retried or manually edited.

Exact cause reproduced with the live 2.37.10 Expression evaluator: compact nested
JSON schemas contain `}}`, which the expression parser treats as the expression
terminator. Normal JavaScript compilation and workflow import do not catch this.

The four structured model calls now build their payloads in Code nodes and pass
only `={{ $json.model_request }}` to HTTP Request. Claim generation, visual review,
final story and duration rewrite share this invocation contract. Error outputs
remain connected to their existing failure handlers. Inventory-first, reserved
assets, native Edge timing and no-manual-rescue rules remain in force.

Verification: 55/55 static regressions PASS; real 2.37.10 evaluator reproduces the old
syntax error and resolves all four corrected request bodies; fresh PostgreSQL
prepares 21 SQL statements and exercises staged writes; n8n 2.37.10 imported all 8 workflows; media-worker build PASS.
Correction committed/pushed as `fae27ad` and deployed to WF02/WF03 only.
Both current and published-history nodes/connections match that source; active
versions match. Product n8n was restarted after publication with no running jobs.
Worker was not replaced for this workflow-only correction.

A NEW normal WF01 job was submitted (HTTP 201):
`897293fa-9627-4f09-b7e0-fc9c49562ba2` — How the Panama Canal locks work / ru / 15.
It is running autonomously; no creative intervention or old-job retry is allowed.
Next: inspect its executions, confirm claim drafting invokes V4 Model Gateway,
then follow through to MP4 or capture/fix a systemic failure and submit a new job.
No final MP4 or human acceptance has been obtained for this correction yet.
Targeted rollback export:
`/opt/ai-short-form-content-factory-runtime-backups/pre-invocation-20260906T205157Z`.
Production inventory-first rollback backup remains
`/opt/ai-short-form-content-factory-runtime-backups/pre-inventory-first-20260906T194034Z`.

## 2026-09-06 inventory-first implementation — pre-production verified

The Codex audit direction has now been implemented in the existing n8n product path on preservation branch `continuation/codex-recovery-20260906`. This is not a new product or a V6 side architecture.

Current implemented causal order:

`topic -> evidence-grounded resolution/research -> candidate factual claims -> actual still-image discovery -> preview fingerprinting -> actual-image multimodal verification -> perceptual dedupe/reservation -> final supported story units -> one continuous Edge narration -> provider word timings -> frozen-unit duration rewrite if needed -> reserved-asset execution -> render -> exact artifact hash -> human review`

Systemic changes now present in source:

- WF02 reserves unique verified visual assets before final narration is authored and persists `story_package` version `inventory-first-story-v1` with explicit claim/evidence/unit/asset bindings;
- WF03 consumes native Edge word boundaries and preserves frozen claim/evidence/asset identity across bounded duration rewrites; late visual rebind is removed;
- WF04 no longer performs post-script visual discovery/recovery/beam assignment and instead downloads, stores and re-fingerprints only the assets reserved before narration;
- WF05/render accepts variable semantic-unit counts, preserves the whole still image in 9:16 composition instead of destructive central foreground crop, and persists SHA256 identity of the exact final MP4;
- media-worker exposes stored-visual fingerprint verification and inventory-first render/artifact contracts;
- JSON-producing model calls in candidate-claim generation, final story generation and duration rewrite now explicitly request structured JSON schemas;
- WF02 error-output routing is explicitly enabled and planner failure recovery can recover the job ID from stable upstream context, so model/validation failures must persist a failed job rather than leave `created/intake` stranded.

Verification after the latest structured-output/failure-persistence correction:

- 55/55 non-live static regressions PASS (13 Python + 42 Node; the explicit environment-dependent real-provider dry run is excluded from this count);
- fresh PostgreSQL contract PASS with all current workflow SQL statements prepared and staged writes exercised;
- actual n8n 2.33.3 import contract PASS for all 8 workflow exports;
- clean media-worker Docker build PASS; current pre-deploy image `sha256:8017fba74dadb5d0ccee338e358a2586a96a8ab088b8bd6de0bfbc5565e334b9`;
- component probes previously verified SearXNG research, pre-script inventory, stored-file perceptual identity and native Edge word timing.

The first clean isolated n8n product-input attempt exposed the general missing structured-output/failure-persistence contract described above; that defect is fixed and regression-covered. A second fully isolated n8n E2E is currently blocked by environment credential injection restrictions in the server control layer, not by a discovered product-code failure. Do not treat that harness limitation as product acceptance.

**Production has not yet been changed by this inventory-first implementation. Overall product quality remains unproven until a fresh normal production job is run with zero manual rescue and the exact resulting MP4 is watched by the user.**


## Current factual audit (2026-09-06; supersedes stale state claims below)

Read `docs/V5_SYSTEM_AUDIT_20260906.md` for the verified runtime, systemic causes,
completed engineering work and exact unfinished next steps. At audited HEAD
`b909a25`, the seven main workflows and running worker files match GitHub; WF01
is active. The actual pipeline is script-first with synthetic within-audio timing
and static central photo crops. The former ARCHITECTURE_V5 described an intended
asset-first path, not deployed behavior. Overall product quality remains unproven.

Current work has not changed production or submitted a new product job. Fresh DB
bootstrap, review API source and executable integration checks are being repaired
before implementing the inventory-first causal order. Historical entries below
are retained as evidence, not concurrent instructions or verified current state.


## 2026-09-06 recovered post-audit engineering state

The interrupted Codex session had pushed its reproducibility/word-timing foundation
as commit `36c76437...`, but later chat-described edits were not in GitHub. Those
missing edits have been reconstructed in an isolated worktree and verified: WF03
uses exact Edge provider word timestamps, media-worker receives Pexels/Pixabay
configuration, and research uses configured SearXNG rather than a Wikipedia-only
endpoint. Full details and verification evidence are in `docs/V5_SYSTEM_AUDIT_20260906.md`.
Production remains unchanged. The next systemic implementation target is still the
inventory-first story contract; do not resume late post-script visual recovery as
the product architecture.

## Mandatory pre-action gate

Before any meaningful action, code change, render, test, architecture decision, dependency addition, or direction change, **read `docs/OPERATOR_EXECUTION_RULES.md` first**, then read this file.

The current primary project risk is operator/assistant decision drift: changing direction without proof, handcrafting proofs, inventing blockers, or replacing the required n8n product with side architectures. Do not repeat those patterns.

## Product definition

The product is a **free/self-hosted n8n orchestrator**.

External input:

`topic + language + requested duration`

Required n8n-controlled path:

`input -> research -> free/licensed visual inventory -> visual verification/ranking -> story/script -> one continuous narration -> exact-audio timing -> autonomous edit plan -> render -> QA -> exact-artifact human review`

Supported durations: `15 / 30 / 45 / 60` seconds.

Output: vertical `9:16` short-form MP4.

No mandatory paid-per-video API dependency is allowed.

## Human-rejected baseline

First real n8n-orchestrated 60-second proof:

- job: `d23617c3-1311-43c1-97e0-c6504522bd77`;
- topic: `Почему листья меняют цвет осенью`;
- language: `ru`;
- requested duration: `60 s`;
- rendered duration: `59.064 s`;
- technical state: `review_ready`;
- human state: **HUMAN FAIL**.

General defects found:

1. **visual policy defect** — WF04/media-worker was biased toward stock video, producing long/generic moving footage instead of using the much larger relevant still-image inventory;
2. **narration defect** — current WF02 deterministic extractive narration can sound encyclopedic and expose source artifacts instead of producing natural spoken short-form text.

Neither defect may be repaired manually for one topic.

## Photo-first systemic correction

Durable records:

- `docs/V5_N8N_PHOTO_FIRST_MEDIA_POLICY_20260904.md`;
- `docs/V5_N8N_PHOTO_FIRST_PROOF_20260904.md`.

Default visual inventory is now still-image first:

- Pexels Photos;
- Wikimedia Commons / canonical Wikipedia media;
- Pixabay Images;
- additional free/publicly licensed image providers as they are integrated.

Still images are normal production assets and must be turned into dynamic video through purposeful crop/reframe, pan/zoom, detail crops, masks, layouts, callouts, parallax, maps/documents/diagrams or other motion treatment.

Video is optional and secondary. A clip may be selected only when the segment is genuinely motion-led, metadata matches both subject and segment target, local visual ranking says it is more relevant than the best still for that segment, and the selected clip is short (currently max four seconds).

Generic moving footage is a fail.

The first photo-first rerun, job `4f6816b2-38aa-4fe8-8e8d-fbf84a951818`, exposed a general DB schema mismatch: `visual_shots_kind_check` did not allow the new `factual_image` / `context_video` kinds. Migration `017_photo_first_visual_kinds.sql` fixed the shared schema contract.

## Current exact review artifact

Second photo-first n8n rerun:

- job: `8d82fc3e-b8ad-4ac0-8ef5-f61190e3a904`;
- same input: `Почему листья меняют цвет осенью`, `ru`, `60 s`;
- status: `review_ready`;
- rendered duration: `59.064 s`;
- format: 1080x1920, 30 fps, H.264 + AAC;
- exact review copy: `/opt/ai-short-form-content-factory/studio/bakeoff/n8n-photo-first-leaves-ru-60.mp4`;
- SHA256: `0b007fdde0a15994c7df7b1de0d7054fe136755d08c21a6a03f566c3c3e13850`.

Automatic selected-media composition:

- Pexels Photos: 4;
- Pixabay Images: 3;
- Wikimedia Commons images: 3;
- video clips: 0.

No clip/image was manually selected after submission.

Acceptance state: **machine_rendered / review_ready only**. This exact artifact is not `human_approved` until the user watches and explicitly accepts it.

## What counts as a valid proof

A proof starts by supplying only `topic + language + duration` to n8n.

After that there is zero manual creative intervention.

Invalid proof methods include:

- manual clip/image selection;
- manual query rescue for one topic;
- manual scene/edit-plan repair;
- looping/reusing assets to fill duration;
- speech-speed manipulation to force duration;
- bypassing n8n with a handcrafted direct/CLI path;
- calling machine success a product success before explicit HUMAN PASS.

## Immediate gate

1. user watches exact photo-first artifact `n8n-photo-first-leaves-ru-60.mp4`;
2. record HUMAN PASS/FAIL from that exact file;
3. if the visual direction passes, fix the separate general natural-narration defect in WF02 without topic-specific text;
4. rerun the same n8n path and repeat on materially different topics/languages after HUMAN PASS.

Do not create a separate product architecture. n8n remains the orchestrator.

## Topic-resolution HUMAN FAIL and systemic correction

Job `16c23aed-4370-46a4-b135-63f8b6af47c6` (`Ходор / ru / 30`) reached `review_ready` with `fact_primary_title=Mikhail Khodorkovsky` and measured voiceover `28.728 s`. This is HUMAN FAIL: the intended subject was the fictional character Hodor.

Production evidence identified a general WF02 ordering defect: one model guessed a canonical subject without candidates or search evidence, after which research queried only that guess. The resulting evidence set could confirm but never correct the initial mistake.

The corrected WF02 contract is now `candidate interpretations -> per-candidate discovery -> evidence-grounded comparison -> structured resolution -> resolved-subject factual research`. Migration 018 persists the structured result in `jobs.topic_resolution`. Durable record: `docs/V5_EVIDENCE_GROUNDED_TOPIC_RESOLUTION_20260904.md`.

WF03 continuous voice and exact measured-duration fit, WF04 photo-first policy, and WF05 rendering remain unchanged. The correction is not accepted until cross-topic regressions pass, fresh n8n E2E jobs complete where practical, and the user reviews the exact resulting MP4.

## 2026-09-04 systemic rebuild after cross-topic failures

The previous deterministic/extractive WF02 path is no longer the active narration architecture.

Current n8n-controlled narration path:

`topic in any input language -> semantic intent -> SearXNG research -> grounded AI narration strictly in selected output language -> structured validation -> one continuous natural-rate TTS -> exact measured duration -> bounded script rewrite/re-synthesis when needed`

General fixes completed:

- removed lexical/Wikipedia entity matching as the basis of topic understanding;
- removed deterministic encyclopedia-excerpt narration as the primary writer;
- selected output language is authoritative and independent of input-topic language;
- research evidence supports/audits narration instead of being concatenated into narration;
- exact TTS duration is authoritative; word-count duration prediction is advisory only;
- natural speech rate remains unchanged; timing is corrected by rewriting the script, not tempo manipulation;
- Edge Read Aloud transport budget was increased to a bounded 120-240 seconds and the n8n HTTP timeout aligned to 270 seconds;
- WF02 structured-output parsing now safely tolerates the model's bounded `used_source_ids: [S1,S2]` formatting defect without evaluating arbitrary text;
- visual candidate identity is provider-scoped (`provider + provider_asset_id`) across Pexels/Pixabay/Wikimedia-style inventories, preventing cross-provider numeric-ID collisions;
- photo-first policy remains mandatory; video remains secondary and is admitted only for motion-led, semantically stronger matches.

Latest autonomous end-to-end evidence, all launched only with `topic + language + duration`:

1. job `1bf8089f-eecf-4b93-83f4-a1a5862a4044`
   - topic input: `why is the sky blue`
   - selected output language: `ru`
   - requested: `30 s`
   - measured voiceover: `27.360 s`
   - status: `review_ready`
   - final MP4: `jobs/1bf8089f-eecf-4b93-83f4-a1a5862a4044/render/final.mp4`

2. job `6cf62378-51be-4694-9e4e-5f096a7f1769`
   - topic input: `how does a refrigerator work`
   - selected output language: `uk`
   - requested: `30 s`
   - measured voiceover: `31.152 s`
   - status: `review_ready`

3. job `656656f1-5f75-4a8e-a5ef-bf8bd1608e16`
   - topic input: `почему извергаются вулканы`
   - selected output language: `pl`
   - requested: `30 s`
   - measured voiceover: `29.160 s`
   - status: `review_ready`
   - final MP4: `jobs/656656f1-5f75-4a8e-a5ef-bf8bd1608e16/render/final.mp4`

These are machine-rendered cross-topic proofs only. None is `human_approved` until the user watches the exact artifact and explicitly accepts it.

## Current gate

The user should now test the current workflow from Studio with arbitrary topics/languages/durations. Any HUMAN FAIL must be handled as a general defect from the exact artifact; no topic-specific rescue or manual media selection is allowed.

## Regression gate

Static workflow regression suite: `10/10 PASS` after the systemic WF02/WF03/WF04 rebuild.

The suite covers cross-language semantic intake, selected output-language authority, grounded research-backed narration, advisory-only word budgeting, exact measured TTS duration, bounded natural-rate rewrite/re-synthesis, provider transport budget, short canonical titles, provider-scoped visual identity, and local media-worker module completeness. Node syntax checks also pass for the media-worker entry point and new support modules.

## Evidence-grounded topic-resolution production result

Fresh production regression after migration 018 and the WF02-only deployment resolved all seven required/diverse classes correctly and produced scripts in the selected output languages. Five jobs reached `review_ready`; Hodor and volcano were correctly rejected later by unchanged WF04 relevance/assignment gates. Topic resolution is machine-proven cross-topic; rendered files still require HUMAN PASS/FAIL.

The exact job matrix, consumed failures, decision contract, and deployment corrections are recorded in `docs/V5_EVIDENCE_GROUNDED_TOPIC_RESOLUTION_20260904.md`.

## 2026-09-05 visual relevance HUMAN FAIL

The user rejected all five topic-resolution `review_ready` MP4s. They are HUMAN FAIL, not quality proof. Inspection showed the runs were already image-first; the defect was acceptance of irrelevant images through metadata bonuses despite near-zero local visual scores, compounded by mixed-language visual queries because WF02's English visual concepts were not persisted.

Migration 019 and the WF02/WF04/media-worker correction persist and consume grounded English visual queries, rank against a concise English subject/target, reject sub-floor semantic matches before metadata utility, and keep video secondary to an eligible still. Missing relevant media must fail closed. Durable record: `docs/V5_PHOTO_RELEVANCE_HUMAN_FAIL_20260905.md`.

The correction is deployed. Fresh autonomous job
`e3d9016d-cefc-4158-aeca-075dab852c41` (`как работает холодильник`, `ru`, `30`)
failed closed at visual segment 6 because no candidate exceeded the `0.01`
semantic relevance floor. It produced no `visual_shots` and no MP4. This proves the
deployed gate blocks unrelated filler; it does not yet prove sufficient relevant-
photo coverage or human-acceptable output.

## 2026-09-05 visual selector rollback decision

The lexical-metadata plus local SigLIP selector is rejected as a production visual
quality authority. The exact Hodor render selected a random door, snow, an insect
micrograph, an unrelated portrait, and a scientific figure. Five of eight selected
shots had `target_metadata_overlap=0`; metadata utility overrode near-zero visual
scores. Subsequent absolute-threshold calibration alternated between irrelevant
media and incomplete jobs and is not a viable product mechanism.

WF01 intake is paused while WF04 is replaced by multimodal review of the actual
candidate previews. The local ranker may remain only for perceptual hashes and
ordering; it must not independently approve semantic relevance. Production intake
must not resume until the exact rendered MP4 is watched before delivery.


## 2026-09-05 final-narration visual rebind + bounded model recovery

Fresh production matrix after deploying WF02 commit c6a14a7:

- 4174878b-4662-433d-9ff2-ff090cf77ac5 — как работает гидроэлектростанция, ru, 15 s — WF03 failed during the second duration-fit rewrite;
- 4c864c59-20bf-41fe-b562-b20f5c3571a2 — How Alexander Fleming discovered penicillin, pl, 30 s — reached review_ready, measured voiceover 29.712 s;
- 75a41742-0e38-48c4-a9fb-d8f4320c89f6 — как образуются облака и дождь, uk, 60 s — WF03 failed during the first duration-fit rewrite.

Execution inspection proved the apparent duration rewrite model returned invalid JSON failure was masking upstream Gemini free-tier HTTP 429 responses. The model gateway had no bounded recovery and WF03 received an empty object after the child workflow failed. This is a general provider-availability defect, not a topic-specific script defect.

A second systemic defect was also proven: c6a14a7 correctly binds visual queries to the final WF02 validator narration, but WF03 may still rewrite narration after exact TTS measurement. Therefore any job with script_fit_passes > 0 can otherwise carry stale visual queries into WF04 even though they were valid for the pre-TTS script.

Current correction under test:

- V4 model gateway has one bounded retry (maxTries=2, waitBetweenTries=60000) and remains time-limited;
- callers that use the gateway have bounded timeouts long enough to accommodate that single retry;
- if a duration-fit model call remains unavailable and the narration is too long, WF03 can make a deterministic punctuation-boundary shortening from the already-grounded narration while preserving evidence provenance; no speech-speed manipulation is introduced;
- after exact TTS is accepted, any job whose narration changed in WF03 must regenerate exactly 6/10/14/18 English visual queries from the actual final timed narration beats, then persist those queries before WF04 starts;
- jobs with script_fit_passes = 0 keep the c6a14a7 validator-bound visual query inventory and do not spend an extra model call.

Regression coverage added for bounded model recovery, deterministic duration fallback, and final-narration visual rebinding. Production deployment is not allowed until the complete regression suite passes, changes are committed and pushed, then the exact new MP4s are inspected.

## 2026-09-05 production HUMAN FAIL: spoken slash + unreviewed visual fallback

Fresh production jobs after commit `3af1b99c2ccaf131920cb664f8ee0ab6215dc182` exposed two additional general defects.

1. Job `043c10a6-4d9d-4948-bc0d-64237429e749` (`как работает гидроэлектростанция`, `ru`, `15`) reached `review_ready`, but the persisted narration contained literal formatting separators such as `? /`, `, /` and ` / ` between words. The TTS therefore audibly pronounced the slash. The defect is not provider-specific: unsafe formatting was allowed to enter the spoken narration contract before TTS.

2. The same hydro render and job `cc1141d8-03a3-4825-ac96-281812737a7a` (`How Alexander Fleming discovered penicillin`, `pl`, `30`) showed apparently random second images inside semantic segments. Execution evidence proved the multimodal reviewer normally approved one visibly relevant candidate per segment while each segment requested two shots. `Require Multimodal Visual Selection` then appended `localFallback` candidates that the multimodal reviewer had not approved; because `visual_review_candidates` retained the full local pool, some fallback candidates had not even been shown to the reviewer. Examples include a multimeter for a hydroelectric generator beat and a newsroom/typewriter photo for an Alexander Fleming laboratory beat. This violated the requirement that each displayed image be specifically approved for the current narration.

Systemic correction now under regression:

- WF02 final narration removes whitespace-delimited formatting separators (`/`, `|`, arrows) before persistence and both writing/validation prompts explicitly forbid them in spoken prose;
- WF03 fails closed if unsafe spoken separators somehow reach TTS, and duration rewrites apply the same speech-safe normalization before rebuilding support provenance;
- WF04 exposes only candidates actually shown to the multimodal reviewer as eligible candidates;
- WF04 requires at least `planned_shot_count` model-approved images for every segment and forbids the previous unreviewed `localFallback` path;
- if the reviewer cannot approve enough relevant images, the segment now fails closed instead of silently filling the timeline with plausible/random media.

Regression status before GitHub sync/deploy: `20/20` Node tests + `11/11` Python tests PASS, JSON validation PASS, `git diff --check` PASS. Production has not yet been redeployed with this correction. Existing `review_ready` artifacts above remain HUMAN FAIL.

## 2026-09-05 exact-beat visual sourcing correction under final verification

Fresh production evidence from job `fd510f8e-21b3-4f2d-a992-2cc5f21e81a0` proved two independent general defects.

1. Narration formatting leakage: the model had emitted `/` as a visual/beat separator inside spoken Russian text and WF02 persisted it unchanged. TTS therefore literally pronounced the slash. The deployed speech-safety correction removes and rejects standalone slash/pipe-style formatting separators before TTS and after duration rewrites. The fresh 15 s rerun produced clean narration with no slash and measured `14.256 s`.
2. Timed visual discovery was not actually beat-authoritative. For a final beat whose exact query was `modern residential house exterior at night with glowing interior lights`, the media worker prefixed the canonical topic, producing an overlong provider query; Pixabay returned HTTP 400. The timed candidate pool then still contained generic topic-level hydroelectric imagery, which allowed topic-context pictures to be selected for a homes/electricity beat. In addition, semantic visual segmentation could merge multiple final narration beats and attach only the first beat query to the merged segment.

The new systemic correction keeps the final timed narration as the only visual chronology authority:

- one visual segment per accepted final narration beat (`narration-beat-visual-segments-v4`);
- query N binds one-to-one to final beat N;
- each beat >= 1.8 s plans two distinct full-screen stills, preserving the multiple-image-per-scene contract;
- timed searches use the exact English beat query without prefixing the overall topic;
- provider query length is bounded before transport;
- timed candidate pools do not mix generic topic-level Pixabay/Pexels/Commons stock or canonical-article media;
- Pexels uses the Photos API, not stock-video search;
- Commons, Pixabay and Pexels requests run concurrently per beat, with bounded concurrency across beats and existing per-provider timeouts;
- final multimodal review may select only images actually shown for that exact beat; topic anchors and unreviewed local fallback are forbidden; insufficient visible matches fail closed.

Regression coverage is updated and a new real-path discovery regression covers exact beat queries, provider query bounds, Pexels Photos, no topic-level timed stock and bounded concurrency.

Real-provider dry-run against the exact failed 60 s cloud/rain context (`18` final beats / `18` queries) completed in `5.726 s`, returned `18` beat-aligned visual segments / `36` planned still shots, and reported `0` provider errors. Every segment used its exact final beat query; topic-level base provider counts were all zero. This is discovery evidence only, not HUMAN PASS. The correction still requires GitHub sync, production deploy, fresh E2E renders and exact MP4 review.

### 2026-09-05 bounded multimodal review batching correction under test

Fresh post-deploy E2E matrix after exact-beat visual discovery exposed a separate bounded-review defect:

- `8dbc666c-3d00-4cfb-a15b-f168a6313895` — hydroelectric plant / ru / 15 — `review_ready`, measured voice `13.824 s`;
- `81394bf5-b345-4565-82a4-13d4cc16dd76` — Alexander Fleming / pl / 30 — failed because segment 1 received only `1/2` model-approved relevant stills;
- `4278786c-a243-4e0e-a37e-d3e2226b8434` — clouds/rain / uk / 60 — failed before review because the single multimodal request exceeded its bounded 80-item input budget.

The failures have one general cause: one whole-video multimodal request forced candidate exposure per segment to shrink as beat count grew, and at 18 beats the fixed lower bound of two candidates per segment made the request mathematically exceed the 80-item cap. The 30 s case was also starved to only three reviewed alternatives per beat, so failing closed after one relevant choice was expected even though more exact-query candidates existed upstream.

Correction under test: split final visual review into deterministic batches of at most six exact narration beats. A six-beat batch can show up to six actual still candidates per beat and remain within the 80-item request cap; smaller batches expose up to 7-10 candidates per beat. The model may approve up to four visibly exact candidates per beat, never fewer than the required shot count when enough exact matches exist. All approved alternatives remain model-reviewed and the global assignment still forbids asset reuse. No topic-level or unreviewed fallback is reintroduced.

Static Node regression now proves 18 beats => exactly three bounded review batches, complete segment coverage, <=80 inputs per model call, multi-batch response reconstruction, fail-closed behavior, and global no-repeat assignment compatibility. Production deployment remains blocked until the full regression suite, GitHub sync, and fresh E2E reruns pass.

### 2026-09-05 bounded visual-query recovery + measured duration controller under test

Fresh production matrix after `820fcb4d78ebb060fb4d938ab40d51661debb5f6` exposed two separate systemic gaps rather than a reason to weaken relevance gates:

- `3a4f8483-03b5-47a3-81dd-8844445157aa` (`How Alexander Fleming discovered penicillin`, `pl`, `30`) failed closed because exact stock search for `Alexander Fleming historical portrait` produced same-name but wrong entities; the actual-image reviewer correctly approved `0/2` for beat 1.
- `310f8fae-2d74-4f54-871e-f1375fa71ea1` (`как образуются облака и дождь`, `uk`, `60`) failed closed on beat 18 because `water cycle diagram showing evaporation condensation and precipitation` produced mostly generic rain/condensation photos instead of an explanatory water-cycle diagram.
- `c7cf63b2-3712-4c36-b375-613ad97aa8a2` (`как работает гидроэлектростанция`, `ru`, `15`) measured `20.808 s -> 11.568 s -> 13.272 s`; the final result missed the accepted lower bound by `0.195 s` and the old controller failed immediately after two rewrites.

Systemic correction now under regression/GitHub gate:

- timed visual discovery still searches the exact final-beat query first;
- when exact provider results do not supply enough query-anchored candidates, discovery may issue exactly one compact recovery query that preserves the named entity/mechanism and media cue; it may not fall back to the overall video topic;
- the recovery path remains bounded to the same free providers/timeouts and all recovered images still require actual-image multimodal approval;
- real provider evidence for the failed classes now exposes correct Wikimedia candidates such as Alexander Fleming portraits and water-cycle diagrams instead of accepting same-name stock noise;
- WF03 now preserves bounded measured TTS history and allows at most three rewrites;
- when measured attempts bracket the target duration, the next requested word count is computed by interpolation between the closest measured under-target and over-target attempts instead of another blind proportional jump;
- exact TTS measurement remains authoritative and speech rate remains unchanged;
- migration `021_expand_script_fit_pass_limit_to_three.sql` raises only the bounded persistence limit from two to three rewrites.

Current static regression gate: `23/23` Node + `11/11` Python PASS, workflow JSON PASS, `git diff --check` PASS. A real-provider discovery/rank dry-run on the failed 30 s and 60 s contexts also passes with 10 ranked candidates available per exact beat. These are engineering proofs only. GitHub sync, migration/deploy, fresh autonomous 15/30/60 renders, and exact MP4 review are still required.

### 2026-09-05 post-b6f299 production failures and bounded correction

Fresh autonomous production matrix on `b6f299ed1af3d9e7a39bb4dedfb9efa3f2681f81` exposed two remaining general defects:

- `4183cb81-c918-41a8-80ef-b68df92053d2` — hydroelectric plant / `ru` / `15`: WF03 measured `21.168 -> 13.248 -> 13.104 -> 12.816 s` and failed after the bounded third rewrite. The accepted lower floor is `13.467 s`; several attempts missed it by only fractions of a second.
- `b338430e-b371-4ca2-a1ce-0076641aa1f6` — Fleming / `pl` / `30`: after `39.336 -> 26.856 s`, the next duration-rewrite model call was unavailable. The current result was only `0.111 s` below the accepted lower floor `26.967 s`, but deterministic textual expansion is intentionally not used when the model is unavailable.
- `721b1fbc-226c-499c-95e1-d434dcddf13c` — clouds/rain / `uk` / `60`: voiceover passed at `58.656 s`; WF04 failed closed on beat 16. Execution evidence showed the multimodal model could identify correct `Water Cycle` diagrams, but the bounded pre-review exposure pool had shown it unrelated `cycle` matches instead because correct phrase-level candidates were displaced before review.

Systemic correction now under GitHub/deploy gate:

- normalized continuous voice audio may add only a bounded natural end pause, max `0.4 s`, and only when the measured narration is already within `0.4 s` below the accepted lower duration floor; speech rate/tempo remain unchanged and materially short narration still goes through rewrite/fail;
- both Gemini-stored and Edge-fallback continuous audio use the same bounded tail-normalization helper;
- compact visual recovery canonicalizes media cues such as `schematic` to `diagram`, so a target such as `schematic diagram of the global water cycle` reduces to a subject-preserving query such as `water cycle diagram`, never to the overall video topic;
- WF04 bounded exposure now prioritizes exact subject/target phrase matches before multimodal review, so correct candidates are not displaced by lexical coincidences such as unrelated uses of `cycle`;
- the actual-image reviewer remains authoritative and fail-closed; no unreviewed fallback or weakened relevance gate is reintroduced.

Verification before commit: `25/25` static Node tests + `11/11` Python tests PASS, workflow JSON PASS, `git diff --check` PASS. A real-provider discovery/rank dry-run on the previously failed Fleming and cloud/rain contexts also passes with `10` ranked candidates per beat and no provider errors. Production deployment and fresh autonomous 15/30/60 MP4 review are still required.

### 2026-09-05 production rank-timeout root cause + fingerprint-only correction

Fresh autonomous production matrix on commit `706d5badf7279010973506ef4705c4331e7cb715` reached exact-duration voiceover but all three jobs failed in WF04 before render:

- `f94e5fd5-1b6f-4551-8a38-c0f25d745853` — transformer / ru / 15 — voice `16.392 s`; rank segment 1 timed out;
- `d0cfdc93-508b-4490-a84f-c7ba25f735f6` — Marie Curie / pl / 30 — voice `29.808 s`; rank segments 4,6,7,8,9 timed out;
- `592c44ea-64d9-44c7-9bb0-347b21de05f2` — aurora / uk / 60 — voice `60.288 s`; rank segments 9,13,14,18 timed out.

Execution inspection proved the final `received=... expected=...` messages were secondary. `Rank Eligible Visuals` sent one HTTP request per exact beat while the media worker serialized every SigLIP inference behind one global promise chain. Later requests waited behind earlier segments until n8n's 120 s HTTP timeout. `Attach Rank Results` then routed failed items to its error output while successful items continued, so the main branch silently lost segments and only failed later with an incomplete timeline.

Systemic correction under test:

- local SigLIP is removed from the critical WF04 rank path; it had already been rejected as semantic relevance authority and is no longer needed there;
- `/visual/rank` now performs only bounded preview retrieval + perceptual hashing, preserving the planner's deterministic candidate order; actual-image multimodal review remains the sole semantic approval authority;
- preview transport has a maximum of two attempts for transient 429/5xx/transport failures, six global fetch slots, and the existing 10 s per-attempt timeout;
- WF04 preserves expected segment cardinality on every fingerprint item and turns any remaining fingerprint failure into one explicit pre-review failure instead of silently dropping that beat;
- the rank HTTP node itself has at most two attempts; there is no unbounded retry loop;
- selection provenance is renamed to `multimodal_exact_beat_shot_beam_v4`;
- the repository media-worker Docker/package build contract is synchronized with the actual production runtime so a GitHub checkout can build the worker reproducibly.

Real stress proof against the exact latest 15/30/60 contexts: discovery produced `6 + 10 + 18 = 34` exact-beat fingerprint requests. All 34 were fired concurrently at the patched worker and completed in `13.228 s` total; the slowest single request was `13.218 s`, all returned at least one fingerprinted candidate, and no request approached the 120 s n8n transport bound. This is engineering evidence only; fresh production E2E MP4s and exact-artifact review remain required.


### 2026-09-06 hosted provider failover + global no-repeat recovery under GitHub gate

Fresh runtime inspection after rollback HEAD `8ed8a080f8feacedc57c351f0b127d4847045b7b` reconfirmed that production contains only PostgreSQL, n8n and media-worker; there is no Ollama/model-worker runtime. The active V4 model gateway and WF04 runtime exports were semantically equal to the GitHub HEAD before this correction.

Production DB also reconfirmed the two independent blockers:

- `a1155771-4a8d-4a6d-8739-806ef557340c` and `fb1267de-a814-4dd7-b4e5-b0690c6e54b7` failed because the final visual-rebind model was unavailable;
- `7a9151e5-7064-49db-80dc-43e2ad1d8e79` reached a complete 18-beat visual review but global all-unique assignment failed at the final shot.

Hosted-provider research and live VPS probes show that Kilo Gateway free models are zero-cost but limited to 200 free requests/hour/IP, and individual upstream free routes can still return their own 429/503 capacity failures. `kilo-auto/free` is text-only in the current model catalog, so it cannot replace the required multimodal path. `stepfun/step-3.7-flash:free` currently advertises `text+image -> text` and has returned successful anonymous text and real-image responses from the VPS, but also exhibited intermittent upstream capacity failures. Therefore it is not accepted as a sole production provider.

Systemic provider correction now under GitHub gate:

- V4 Model Gateway keeps the existing n8n webhook contract;
- anonymous Kilo `stepfun/step-3.7-flash:free` is the first zero-cost text+vision provider;
- Kilo failure, empty output or upstream capacity failure falls through immediately to the existing independent Gemini provider;
- the previous 60-second sleep/retry behavior was removed; each provider attempt is time-bounded and the provider chain is finite;
- provider provenance/attempts are returned with the normalized result;
- no Ollama, model-worker, Mac model server or local LLM dependency is introduced.

Systemic WF04 correction now under GitHub gate:

- after actual-image review, a deterministic bipartite feasibility check detects whether globally unique perceptual-cluster assignment is possible before the final beam assignment;
- only beats in the proven conflicting component enter recovery;
- each conflicting beat receives exactly one additional exact-target provider search;
- every candidate already considered in the first actual-image review is excluded from that search;
- new candidates are perceptually fingerprinted, then their real images are shown to the same multimodal reviewer;
- only newly reviewer-approved candidates are merged into the approved pool;
- the existing global all-unique assignment is then attempted once more; if it is still impossible, WF04 fails closed;
- no image/cluster reuse, unreviewed fallback, topic-level rescue, or SigLIP semantic authority is reintroduced.

Verification before commit: workflow JSON parse PASS; Python regressions `11/11` PASS; static Node regressions `30/30` PASS including new exact conflict-search and global no-repeat recovery tests; `git diff --check` PASS; no tracked `work/`; modified runtime/workflow code contains no Ollama/model-worker dependency; media-worker builds reproducibly from this checkout; both modified workflows import successfully into a clean n8n `2.33.3` instance. The isolated built media-worker exposes `/visual/recover-conflict`; a real Wikimedia exact-target request for `Alexander Fleming portrait` returned 18 new candidates while keeping semantic approval outside discovery. Production deploy and fresh autonomous 15/30/60 E2E renders remain blocked until commit/push and GitHub-source verification complete.


### 2026-09-06 WF01 GitHub/runtime orchestration drift correction

Pre-E2E reconciliation found a pre-existing source/runtime drift in WF01. The active production WF01 and production filesystem both contain the same seven-node orchestration core: after the job row is inserted, `Start Script Planning` asynchronously invokes WF02 `TJfA4ZYUEKSTad6k` with only the persisted `job_id`, while the webhook returns HTTP 201 without waiting for the full generation chain. Their canonical core SHA is `065a372f16e865e502769d8bf0c344a5ad29cba1c29378bd406cbddee8239c3f`.

GitHub commit `a8ab5f2c984a517e9176b29dcc4bb101270355f9` still carried an older six-node WF01 core (`20d83db99524ea97550311095430c3746eee89fbe536c521b7ec4db777c73477`) that inserted and returned the job but did not invoke WF02. That GitHub file cannot represent the required autonomous `topic + language + duration` product path even though runtime had the correct handoff.

Correction under GitHub gate: synchronize the already-live generic WF01 orchestration contract into repository source and add a regression requiring exactly one asynchronous WF01 -> WF02 handoff with `job_id`. This is source/runtime reconciliation, not a topic-specific behavior change. Fresh E2E remains blocked until the corrected WF01 is committed, GitHub tree is verified, and production WF01 is republished from that GitHub source.


### 2026-09-06 fresh E2E provider completion-contract failure

After GitHub commit `a5bafcd96f69936f51439b0298c23dfc9705874e` restored WF01 source/runtime orchestration and WF01 was republished from that exact GitHub tree, fresh autonomous production testing resumed strictly through the WF01 `topic + language + duration` webhook.

Fresh RU/15 transformer job `a8ebade0-9657-46d5-9bfd-449ebfd6a7a9` completed autonomously to `review_ready`. Exact voiceover duration is 15.504 s. WF04 stored `visual_quality.pass=true` with 12 shots, 12 unique assets, 12 unique perceptual clusters, zero asset reuse and zero adjacent perceptual duplicates. WF05 rendered `jobs/a8ebade0-9657-46d5-9bfd-449ebfd6a7a9/render/final.mp4`; technical probe is H.264 + AAC, 1080x1920, 30 fps, 15.534 s, SHA256 `81d8b4134290ba888c80079f3e3a22cdb423b9efac71d4eacea01037f9566402`. This is machine completion only, not HUMAN PASS.

Fresh PL/30 Marie Curie/radium job `c2a91275-bf29-43c0-95f6-b0f2eeb9694d` exposed a new general provider-contract defect and failed closed at `script`: `evidence-grounded topic resolver returned invalid JSON [line 1]`. WF02 execution `15582` failed after V4 executions `15583` and `15584` were marked success. Exact execution-data inspection proved V4/Kilo execution `15584` returned `finish_reason=length`; `message.content` contained only an approximately 421-character prefix of the requested JSON while the model emitted a long reasoning payload. V4 incorrectly treated any non-empty Kilo content as success, so Gemini fallback was skipped and WF02 received truncated JSON.

Systemic correction under GitHub gate: Kilo output is usable only when text is non-empty and `finish_reason` is exactly `stop`. `length`, `content_filter`, tool-call or missing/nonterminal completion reasons are normalized as failed provider attempts and immediately use the existing independent Gemini fallback. The failed PL/30 job is not retried manually; a completely fresh job may be created only after this gateway correction passes regression/import/GitHub/deploy gates.


### 2026-09-06 fresh PL/30 reviewer-shortfall recovery gap

After V4 commit `c0492f97627d0d894276bebc1f14a018277d281e` was verified live (`active=true`, `versionId == activeVersionId`, and live/source canonical workflow SHA `ca2c17e99aabe2d4466f5f53952f551aa51e88e04951088e19216f72242ffe41`), fresh PL/30 job `ed6a58bb-f4a6-4dc8-a545-35c8795743d2` demonstrated the completion-contract correction on real production traffic. V4 execution `15588` received Kilo `finish_reason=length`, normalized the Kilo attempt as unsuccessful, then used Gemini successfully and returned complete valid resolver JSON. WF02 and WF03 subsequently advanced normally; exact voiceover duration reached 32.064 s.

The same fresh job then exposed a separate general WF04 defect and failed closed at visuals: `Multimodal reviewer approved 1/2 relevant images for segment 5; unreviewed fallback is forbidden`. Execution `15596` showed that the exact beat required two reviewed stills for `pure radium chloride crystals in glass vial`, while the first inventory mostly contained generic crystal/mineral representations. The reviewer correctly refused to pad the beat.

Source inspection identified the architectural gap: `Require Multimodal Visual Selection` threw immediately on any per-segment approved-count shortfall, while the existing single exact-target recovery path was reachable only after `Detect Global No-Repeat Conflict`. Therefore a segment with insufficient exact reviewer-approved images could never use the same bounded recovery already available for global uniqueness conflicts.

Systemic correction now under GitHub gate: initial multimodal review preserves only reviewer-approved candidates and records approved-count shortfall instead of admitting any fallback. Malformed or empty reviewer output remains an immediate failure. The global feasibility detector adds shortfall segments, including zero-approved pools, to the same bounded recovery set used for perceptual-cluster conflicts. Each affected segment receives one additional exact-target search excluding every candidate already shown to the reviewer; only newly fingerprinted and reviewer-approved candidates can be merged. After that one recovery round, merged reviewer-approved cardinality must meet `planned_shot_count` or WF04 fails closed. No shot-count relaxation, relevance-threshold relaxation, topic-specific query, asset reuse, unreviewed fallback, or second recovery round is introduced.

Targeted verification before the full gate: `WF04_PHOTO_RELEVANCE_GATE_REGRESSION_PASS`, `WF04_GLOBAL_NO_REPEAT_RECOVERY_REGRESSION_PASS`, and `VISUAL_CONFLICT_RECOVERY_EXACT_QUERY_REGRESSION_PASS`.

Full verification for this correction: workflow JSON parse PASS; Python regressions `11/11` PASS; Node static regressions `31/31` PASS; `git diff --check` PASS; clean n8n `2.33.3` import of WF04 PASS.

### 2026-09-06 PL/30 recovery proof + UK/60 structured-output failure

WF04 shortfall recovery was deployed from GitHub commit `5d0398b65d6c63764f24a9441c5785c190753b50` after immutable source verification. Production live/source canonical WF04 core SHA is `f8fe6b76bf92213d136ead92f2f40779fc6a25e1fc592e968e04eb968e454eef`; live workflow has 42 nodes and `active=true` with `versionId=activeVersionId=379a5d0e-b955-444e-8951-1f3297915bc8`.

Fresh PL/30 job `d278b778-4aea-468d-b78e-aa03e994fd46` (`How Marie Curie discovered radium`, `pl`, `30`) was created by one WF01 intake and completed autonomously to `review_ready`. Exact voiceover duration is 26.983 s. The original failure class reproduced on segment 4: initial multimodal review returned `visual_review_approved_count=1` for `visual_review_required_count=2`, so `visual_review_shortfall=true`. The new single recovery round then added four newly reviewer-approved exact-target candidates; the same segment finished with approved count 5, `visual_review_shortfall=false`, `visual_recovery_used=true`, and `global_conflict_recovery_attempted=true`. WF04 stored `visual_quality.pass=true` with 20 shots, 20 unique assets, 20 unique perceptual clusters and zero reuse. WF05 rendered `jobs/d278b778-4aea-468d-b78e-aa03e994fd46/render/final.mp4`; technical probe is H.264 + AAC, 1080x1920, 30 fps, 27.000 s, SHA256 `e6dae140d636d0d57c49d4fd90a6d4ba14f60909576bd487085d6d226ff2558c`. This is machine completion only, not HUMAN PASS.

Fresh UK/60 job `ff7c0237-dc9f-4709-bf16-5d2e69201852` (`как образуется северное сияние`, `uk`, `60`) was then created through WF01. WF02 and WF03 passed automatically; final continuous voiceover duration is 60.480 s with one script-fit pass and no speech-speed manipulation. WF04 execution `15665` failed closed at recovery review with `Global conflict recovery reviewer returned invalid JSON for batch 1 [line 3]`.

Exact V4 execution `15669` proved this is a separate structured-output contract defect. Kilo returned `finish_reason=length` and was correctly normalized as unsuccessful. Gemini fallback returned `status=completed` and was incorrectly marked provider success because the gateway only checked for non-empty text. The 1456-character Gemini response was syntactically invalid JSON: after the first segment object it emitted the next `segment_number` before closing the previous object. Therefore the transport/provider layer succeeded while the structured-content contract did not.

Systemic correction now under GitHub gate: V4 accepts an opt-in `response_format: "json"` plus `response_schema`. For structured calls, Kilo receives OpenAI-compatible `response_format: {type: "json_object"}` and Gemini Interactions receives `response_format: {type: "text", mime_type: "application/json", schema: ...}`. Both provider normalizers now require syntactically valid JSON whenever `expects_json=true`; malformed Kilo `stop` output falls through to Gemini, while malformed/incomplete Gemini output becomes provider-exhausted instead of usable text. Both WF04 actual-image reviewer calls — initial and recovery — send the same reviewer JSON schema. Semantic validation of segment numbers and candidate IDs remains in WF04. No JSON repair parser, retry loop, relevance weakening, shot-count relaxation or topic-specific exception is introduced.

Verification for this correction before commit: targeted structured-output and existing provider-failover regressions PASS; workflow JSON parse PASS; Python regressions `11/11` PASS; Node static regressions `32/32` PASS; `git diff --check` PASS; clean n8n `2.33.3` imports of both V4 Model Gateway and WF04 PASS. Production deploy and a completely fresh UK/60 E2E remain blocked until commit/push and GitHub tree verification complete.

### 2026-09-06 UK/60 reviewer payload overload correction

After structured-output commit `2e649032bab9a68cc1b3784cfd58dc80f3735230` was deployed, fresh autonomous UK/60 job `0a0eae4e-76d5-44b7-b929-2f1878bf2ce5` (`как образуется северное сияние`, `uk`, `60`) was created through one WF01 intake. WF02 and WF03 passed automatically. Final continuous voiceover duration is 55.728 s with one script-fit pass and no speech-speed manipulation. WF04 then failed closed on initial multimodal review batch 3 with `Multimodal visual reviewer unavailable for batch 3 [line 5]`.

Exact V4 execution `15740` proved the structured-output contract itself was working: `expects_json=true`; Kilo received `response_format: {type: "json_object"}` and Gemini received `mime_type: "application/json"` with the reviewer schema. Kilo returned `finish_reason=length` and was correctly rejected. Gemini then hit the existing bounded 90 s provider timeout, so V4 normalized the full provider chain as `provider_exhausted=true` instead of returning malformed text.

The overload is general and measurable. Initial visual-review executions `15738`, `15739`, and `15740` each carried 36 inlined images plus 43 text items. Batches 1 and 2 completed through Gemini; batch 3 timed out. The 36-image exposure came from six segments per batch times six candidates per segment even though the reviewer output contract permits at most four approved IDs per segment and production visual segments require only one or two shots.

Systemic correction now under GitHub gate: both initial and recovery review preparation cap exposure at four candidate images per segment while preserving the existing six-segment batch size, exact-target candidate ordering, actual-image review authority, one-shot recovery and fail-closed semantics. A six-segment reviewer batch is therefore bounded to at most 24 images / 55 total input items instead of 36 images / 79 items. Because durable `planned_shot_count` is restricted to 1..2, four reviewed alternatives retain at least 2x candidate slack per required shot; no shot-count relaxation, provider timeout increase, retry loop, topic-specific query or unreviewed fallback is introduced.

Verification before commit: initial-review and recovery-review exposure regressions PASS; Python regressions `11/11` PASS; Node static regressions `32/32` PASS; workflow JSON parse PASS; `git diff --check` PASS; clean n8n `2.33.3` import of WF04 PASS. Production deploy and a completely fresh UK/60 E2E remain blocked until commit/push and GitHub tree verification complete.

### 2026-09-06 global visual-semantic gate correction

A cross-topic production audit proved that the remaining visual failures were not isolated topic problems and that prior `review_ready` machine states were not sufficient evidence of visual correctness. Fresh job `4894fe3a-3626-4870-8112-6d1ec0032303` (`как возникла жизнь на земле?`, `uk`, `30`) failed closed at `No valid semantic visual shot assignment at shot 18/20`. Exact WF04 execution data showed that every segment had enough nominally model-approved candidates after recovery, but the approved pools still contained semantically wrong or overlapping assets, so the global unique assignment failure was downstream evidence rather than the primary defect.

The same cross-topic audit found false machine approvals in materially different successful/failed runs. Examples include a Cyprus school building approved for an early nuclear-physics laboratory beat in the Marie Curie job, steel wire approved as a copper transformer winding, DNA/blood-cell imagery approved for early-Earth/abiogenesis beats, generic molecules approved as self-replicating RNA, and a membrane/proton-gradient diagram approved for a hydrothermal-vent photography target. The fresh `4894fe3a...` job itself had correctly aligned narration-to-`visual_target` values, so the current root cause is below target generation.

Two general defects were verified in source. First, `candidateMatchesQueryAnchor()` previously allowed a long target to be represented by the first few weak semantic words; temporal/generic terms such as `early`, `20th`, `century`, `scientific`, `concept`, `equipment` could therefore admit unrelated stock. The bounded conflict-recovery function also returned newly searched candidates without the same target-anchor gate. Second, the multimodal reviewer was asked to select provider IDs directly after seeing filename/ID labels, so it could be biased by lexical cues and could hallucinate target content that was not present in the pixels.

Systemic correction in the current clean checkout: initial discovery and conflict recovery now use the same stronger target-anchor model. Media/low-signal words are removed from anchor keys; long targets require at least three grounded anchor hits; each candidate carries explicit target-anchor metrics; recovery filters candidates before reviewer exposure; canonical-article media can remain available only under the existing provenance path and is still subject to the final actual-image gate. WF04 now hides real provider IDs/filenames from the vision model and exposes opaque `review_id` values only. The model must return one candidate-by-candidate verdict with `relevant` plus a short `visible_description`. Deterministic code then requires both target eligibility and consistency between the model's visible description and the provider's real metadata before an asset can enter the approved pool. The identical contract is applied to initial and recovery review. Unreviewed fallback, relevance weakening and asset reuse remain forbidden.

A separate user-requested global editorial adjustment reduces photo-cut intensity without changing color or adding a renderer-specific trick. Ordinary images have no saturation/brightness/zoom treatment in the current renderer; the high perceived intensity came from shot cadence. The shared shot-count rule now uses the existing 3.2 s support-change boundary: normal shorter beats keep one still, and only beats at least 3.2 s receive a second still. The rule is centralized through `plannedShotCountForDuration()` and used by both segmentation and beat-aligned discovery. This is an editorial cadence change, not an assignment bypass; every planned shot must still use a unique reviewer-grounded asset and perceptual cluster.

Verification for this correction before commit: targeted semantic-anchor/discovery/recovery/reviewer regressions PASS; Node static regressions `33/33` PASS with the real-provider integration dry-run intentionally excluded; Python regressions `11/11` PASS; all workflow JSON parse PASS; `git diff --check` PASS before this documentation append; modified media-worker modules pass `node --check`; clean n8n `2.33.3` import of WF04 PASS; a clean media-worker Docker build from `services/media-worker` PASS with image SHA `41811d52bf3d08d565855ed6acd63c6da5328c7dbe402e216608803a38f3f07`. Production has not yet been changed by this semantic-gate correction.

### 2026-09-06 bounded visual recovery query specificity correction

Fresh autonomous production job `cd5a21dd-3b89-4254-a462-e131b5b95646` (`How a mechanical clock escapement works`, `ru`, `15`) was created through WF01 only. WF02/WF03 completed and produced one continuous natural-rate voiceover of `14.448 s`. WF04 then failed closed before reviewer/assignment with `Visual segment 3 discovery returned no candidates`; no MP4 was produced. Exact execution `16110` showed two beats with zero candidate inventory even though their exact final-beat targets were valid. The bounded recovery query had collapsed `cutaway technical diagram showing mainspring energy release in a clock` to `cutaway technical diagram`, and `motion blur photography of a swinging brass clock pendulum` to `motion blur photography`. The general defect was recovery-query prefix bias: media/style words could displace the actual subject/mechanism.

Systemic correction under GitHub/deploy gate:

- recovery retrieval separates recall from acceptance: it preserves canonical subject overlap first and then ranks concrete content anchors ahead of photographic style/action words;
- when the exact query needs recovery, the provider query is intentionally compact and broad enough for retrieval (for example `clock mainspring` or `clock pendulum`) rather than trying to encode the full acceptance test;
- the original full `visual_target` remains unchanged and every recovered candidate must still pass the same strict target-anchor metrics before it can be exposed to the actual-image reviewer;
- the actual-image reviewer and global uniqueness gates remain unchanged; no unreviewed fallback, topic-level fallback, threshold weakening, asset reuse or second recovery round is introduced.

Real-provider verification on the exact failed six-beat timeline returned zero provider errors. The previously empty mainspring beat now returns two strict Wikimedia candidates (`Clock Mainspring.png` and `Alarm clock mainspring.JPG`), each with `4/3` required target-anchor hits. The previously empty pendulum beat now returns two strict candidates with `3/3` anchor hits. Static verification after the final logic: `33/33` Node tests + `11/11` Python tests PASS, workflow JSON PASS, `git diff --check` PASS, and a clean media-worker Docker build succeeds with image SHA `bddaf1e7ff12da5fd50df4f0d823610d86a66948f6833f6485dee4d23f87a54a`. Production has not yet been changed by this correction.

### 2026-09-08 inventory-first causal-mechanism editorial correction

A product-level reference was taken from the previously user-approved HUMAN PASS induction-heating job `2c182ff8-ea9f-4ddf-a417-b49f796d23f5` (`How does induction heating work? / en / 15`). Its exact stored contact sheet was visually inspected. The accepted mechanism story used visibly different concrete apparatus/component photographs plus one explanatory diagram; invisible mechanism narration was not forced to have a literal diagram for every factual clause. This invalidates the later pre-script assumption that every grounded claim must own two direct reviewer-approved images before narration.

Systemic correction: factual grounding and visual grounding are now separate contracts. Every narration unit remains bound to an evidence-grounded claim. Every shot remains restricted to the frozen multimodal-reviewer-approved real visual pool. The pre-script reviewer and metadata/pixel consistency gates remain authoritative; no unreviewed fallback is admitted. A hidden/internal mechanism claim may use an already reviewer-approved apparatus/component/context visual from another grounded claim when the visible description genuinely supports the narration context. Asset reuse and preview-hash reuse remain forbidden.

Candidate planning now carries `editorial_role` and `visual_form`. For a real physical subject, the hook prefers a truthful real photo over a map/diagram when available. Explanatory topics must expose at least one real mechanism/detail photo option; maps/diagrams remain additional explanatory media rather than a universal mechanism requirement. The story package now carries `editorial_contract_version=shot-intent-v1`, `visual_binding_mode=global-reviewed-context-v1`, and an explicit two-shot `shot_plan` per selected narration unit. WF04 follows the frozen editorial asset order and persists `editorial_role`, `visual_form`, and `shot_intent`; WF05 validates that persisted order/intent before render.

A separate demonstrated editorial defect was then corrected without adding a retry or repair loop. On `How the Panama Canal locks work / ru / 15`, the model repeatedly preferred visually attractive gates/locomotives while omitting the hydraulic cause. For explanatory intent, when at least two grounded `mechanism` claims exist, the first two are now deterministic `required_claim_ids`; the model still writes the prose and chooses reviewed visuals, but it cannot replace core causal mechanism with peripheral detail. The structured story schema now also mirrors the existing story-unit bounds with dynamic `minItems/maxItems`, eliminating a mismatch where the prompt required 3-4 units but the provider could legally return only 2.

Exact frozen Panama component proof after the correction used the existing reviewed inventory only; no new visual search/reviewer round was added. `required_claim_ids` resolved to `C3,C4`. The provider returned `C3,C4,C1` and the final builder accepted all three: miter gates, gravity-fed water/culvert mechanism, and the lock lift result. Six frozen reviewer-approved shot assets were selected with zero repeated asset IDs: `A3,A4,A15,A13,A17,A2`. Exact final component JSON SHA256: `087140323d33841aecff2459d1129913ddd634da30c31f8243e698a7d57133c8`.

Verification on the final source tree before commit: Python static regressions `13/13 PASS`; Node static regressions `58/58 PASS` in the real n8n container runtime (real-provider integration dry-run intentionally excluded from the static count); all `8` workflow JSON files parse; `git diff --check PASS`; disposable exact-image `n8nio/n8n:2.37.10` imports of WF02, WF04 and WF05 all PASS. Production has not been changed by this correction yet. Next: commit/push this exact verified tree, verify GitHub identity, deploy only WF02/WF04/WF05 with rollback/live-source parity, then create exactly one completely NEW normal WF01 job for `How the Panama Canal locks work / ru / 15`. Failed product jobs remain immutable. Machine completion is not HUMAN PASS.

## 2026-09-09 exact-duration sentence-completion defect — verified, pending WF03-only deployment

After the grounded exact-duration WF02/WF03 deployment, exactly ONE new normal product job was created through WF01: `b494d95a-03a0-4503-805e-49076652dfc0` (`How the Panama Canal locks work` / `ru` / `15`). WF01 execution **16661** succeeded, WF02 **16662** completed normally through Model Gateway executions **16663–16667**, WF03 **16668** succeeded through duration-rewrite gateway **16669**, WF04 **16670** succeeded, and WF05/render **16671** succeeded. The job reached `review_ready/review` with exact MP4 `jobs/b494d95a-03a0-4503-805e-49076652dfc0/render/final.mp4`, database/file SHA256 `a5427cf5311597247a9286ae9620694da0750bb0d282eeac75d6c8e7095312dc`, H.264/AAC, `1080x1920`, `30 fps`, duration `13.484s`. Machine completion is NOT HUMAN PASS.

Assistant review found a demonstrated narration defect before delivery: U1 ended `Панамский канал поднимает суда на двадцать шесть метров шлюзами преодолевая континентальный`, an incomplete Russian clause. Exact execution **16669** proved the cause: the old WF03 duration rewrite hard-allocated a 32-word total as per-unit exact quotas `11/10/11`; Gemini satisfied the schema by ending U1 on `континентальный`. Job `b494d95a...` is preserved unchanged and must not be manually repaired/resumed.

The systemic WF03 correction removes pre-assigned per-unit quotas. There remains exactly ONE measured rewrite maximum (`max_fit_passes=1`). The controller now applies a `0.65` semantic-retention floor, minimum `6` words per unit, one exact TOTAL token budget, model-chosen contiguous unit allocation, and deterministic validation that every unit is a single complete declarative sentence ending with `.` and cannot terminate earlier inside the unit. Grounded unit identity/order/evidence/visual binding remain frozen; the prompt requires preservation of named subject, core action/relation, causal mechanism/result, numeric values, and directional relations, while allowing only redundant modifiers/intensifiers/examples to be removed. Speech rate remains untouched.

Frozen live-input component proof for the same Panama story used a 36-word semantic-floor rewrite: `Панамский канал поднимает суда шлюзами на двадцать шесть метров над уровнем моря. Внутренние водопропускные туннели направляют потоки воды в камеры и обратно регулируя уровень. Суда затем плавно опускаются шлюзами на другой стороне водораздела до уровня моря.` Exact natural Edge (`ru-RU-DmitryNeural`, `rate_percent=0`, `post_tempo_factor=1`) measured `16.183333s`, inside the existing 15s acceptance interval `13.467–16.533s`. Temporary proof artifacts under dummy job id were deleted after measurement.

Verification on the final source tree: **60/60 Node static regressions PASS** in the n8n `2.37.10` runtime with the explicit real-provider dry run excluded; **13/13 Python static regressions PASS**; structured model invocation **4/4 PASS** plus reserved-visual binary MIME contract PASS; fresh PostgreSQL contract PASS for **21 workflow SQL statements + staged writes**; disposable exact-image n8n import contract PASS for **8/8 workflows**; all workflow JSON parse PASS; `git diff --check PASS`. Production has NOT yet been changed by this sentence-completion correction. Next: preserve this exact verified tree in GitHub, capture rollback/live source for WF03 only, deploy/publish WF03 only, restart n8n once if CLI requires it, verify source/current/published parity and health, then submit exactly ONE completely NEW normal Panama/ru/15 job. Do not modify `b494d95a...`. Exact MP4 still requires assistant review and explicit user HUMAN PASS.

## 2026-09-10 WF02 multimodal review serialization — verified, pending WF02-only deployment

Production reconciliation showed that WF03 is already live on the exact current source core (`ad396b7c4ddc7da22dd73875851e0a6f54ae301a75d132ae972151d63904e6b5`, active/current version `e782fdae-8de3-4ceb-bf64-083a1275f45a`) and must not be redeployed for this checkpoint. Production WF02 exactly matched commit `66a1fdbdac008c35f85d56432a79db77d058f957` before the correction (`b0aa23d491936beea61e23aa28be27d56e5babb9d9d9bbf0c28d440ce2ec2171`, 44 nodes).

Exactly one later normal Panama/ru/15 job `ef5b9af0-6312-4e18-98e5-54b25ae96f96` failed/script in WF02 execution **16851** with `inventory reviewer returned invalid JSON for batch 1`. The job is failed and immutable. Exact decoded execution evidence shows that `Review Inventory Candidate Images` received two review batches in the same node run. Batch 1 exhausted the bounded provider chain: Kilo `stepfun/step-3.7-flash:free` returned `finish_reason=length` with empty usable output and Gemini `gemini-3.1-flash-lite` returned HTTP 500 high-demand, producing `provider_exhausted=true` and empty text. The second concurrently launched batch succeeded through Gemini. The earlier pre-claim review likewise processed two batch items together. The final `invalid JSON` message was therefore secondary: the selector attempted to parse an explicitly exhausted provider response as JSON.

Systemic correction in the current verified working tree:
- both WF02 multimodal review stages now pass their prepared batches through n8n `Split In Batches` v3 with `batchSize=1`; only one review request is in flight per review stage, and the successful response loops back to request the next batch;
- the loop done output continues to the existing deterministic selector only after all review responses have been collected;
- both selectors fail closed immediately on `provider_exhausted=true` or empty text with an explicit provider-unavailable error instead of misclassifying it as malformed JSON;
- model gateway bounded failover, actual-image semantic authority, reviewer schemas, candidate ordering, grounding, uniqueness, minimum inventory, shot counts and all product gates are unchanged; no sleep/retry loop, provider timeout increase, fallback asset or topic-specific exception was added.

Verification on this exact tree before commit: **65/65 Node static regressions PASS** in the production n8n `2.37.10` runtime with only the explicit real-provider dry run excluded; **13/13 Python static regressions PASS**; structured model invocation contract **6/6 PASS** plus reserved-visual MIME contract PASS; fresh PostgreSQL contract PASS for **21 workflow SQL statements + staged writes**; disposable exact-image n8n import contract PASS for **8/8 workflows**; all 8 workflow JSON files parse; `git diff --check PASS`. The new regression requires both review paths to be serialized, preserves each reviewer error branch, and forbids a direct builder-to-reviewer bypass.

Production has NOT yet been changed by this serialization correction. Next exact step: commit and preserve this exact tree in GitHub, verify zero active executions, capture WF02 rollback/current/published source, deploy and publish **WF02 only**, verify source/current/published parity and health, then submit exactly ONE completely NEW normal `How the Panama Canal locks work / ru / 15` job. Do not resume `ef5b9af0...` or any earlier failed/rejected job. Machine completion is not HUMAN PASS; exact MP4 still requires visual review and explicit user HUMAN PASS.


## 2026-09-10 WF02 serialization production proof + observable-target lexical false reject

GitHub commit `d719778b100ea24b6056a9271cdfed3c5bb7b156`, exact tree `91e2041067aa153a85815b74e4746c057e235c47`, was deployed to **WF02 only** after zero-active-execution preflight and rollback capture at `/opt/ai-short-form-content-factory-runtime-backups/wf02-serialization-d719778-20260910T072518Z`. Source/current/published WF02 parity passed at 46 nodes with canonical current core SHA256 `21c8fec6ddc872fa3453380fe36736613c81dc89d504d4daa915c5c48471355e`; current/active version is `2ce9a562-78e7-4718-99bb-b51f86f8b187`. Exactly one n8n restart was performed; `/healthz` returned status ok; WF03 remained unchanged at `e782fdae-8de3-4ceb-bf64-083a1275f45a`.

Exactly one new normal WF01 job `b5c0f36e-0524-4b02-b569-e74fa99bcdf2` (`How the Panama Canal locks work` / `ru` / `15`) was created with HTTP 201. The serialization correction received real production proof: multimodal gateway executions `17158` and `17159` ran strictly sequentially with no overlap and both succeeded, unlike the prior concurrent batch failure class. The job later failed closed in WF02 execution `17154` at `Validate Candidate Claims` with `candidate claim C6 needs a compact observable visual_target`. The failed job is immutable and must not be resumed or repaired.

Exact execution evidence from model-gateway execution `17160` shows a separate deterministic lexical false reject. Gemini returned complete structured JSON with C6 `visual_target="map showing canal path"`, `visual_form="map"`, `inventory_asset_ids=["V10"]`; V10 had already been pixel-reviewed as `Detailed map of the canal path`. The phrase is a four-word observable noun phrase and its form/inventory binding are valid. WF02 rejected it only because both observable-target validators blanket-forbade the token `show/showing/shows` anywhere in the phrase.

Systemic correction under verification: remove only the blanket `show/showing/shows` lexical ban from `Validate Candidate Claims` and `Validate Visual Exploration`. Existing bans on camera-direction/action constructions such as `close-up`, `under load`, `during operation/use`, `before/after`, and `side-by-side` remain. Length bounds, subject identity, evidence grounding, inventory binding, visual-form matching, mechanism-specific pixel alignment, actual-image reviewer authority, uniqueness, provider failover and all fail-closed gates remain unchanged. Add regression coverage proving an observable noun phrase containing `showing` is accepted by this lexical layer while the existing `close-up ... during operation` case remains rejected. No topic-specific exception, retry, fallback asset, threshold weakening or old-job rescue is introduced.

Verification on the exact corrected tree is COMPLETE before commit: **66/66 Node static regressions PASS** in exact `n8nio/n8n:2.37.10` with the explicit real-provider dry run excluded; **13/13 Python static regressions PASS**; all **8** workflow JSON files parse; `git diff --check` PASS; fresh PostgreSQL contract PASS for **21 workflow SQL statements + staged writes**; disposable n8n `2.37.10` import contract PASS for **8/8 workflows**; structured model invocation contract PASS for **6/6 calls** plus reserved-visual binary MIME contract PASS. The corrected tree is now deployed to **WF02 only** from GitHub commit `c85622874f1367b1cd114f46fdea29d02ef322bd`, exact tree `e2504d918d49b554ee861321dcb6bcb608337026`. Rollback snapshot: `/opt/ai-short-form-content-factory-runtime-backups/wf02-observable-target-c856228-20260910T093205Z`. Zero active executions existed before mutation and after final verification. Source/current WF02 core SHA256 is `ca21cb8deb158ae07ed003e817aa73b4aa55dc66066305577c526904dea15058`; source/published nodes+connections SHA256 is `7d155641f816332286917c05b679ee753d8ad9f44b2c74f8253f3858d97cb349`; source/current/published parity passed at 46 nodes. Current/active version is `81222921-9ce3-4683-89c5-f38acbbad954`. Exactly one n8n restart was performed and `/healthz` returned status ok. Failed job `b5c0f36e...` remained byte-state unchanged across deployment (`row_to_json` MD5 `c97f38dd8ae8365de8f3f784b354eead`), and WF03 remained unchanged at `e782fdae-8de3-4ceb-bf64-083a1275f45a`. Next: preserve this deployment evidence in GitHub, then create exactly one completely NEW normal Panama/ru/15 job. Machine completion still requires exact-artifact assistant visual review and explicit user HUMAN PASS.


## 2026-09-10 fresh WF02 structured-output enum violation after observable-target fix

The observable-target lexical correction was deployed to **WF02 only** from GitHub commit `c85622874f1367b1cd114f46fdea29d02ef322bd`, exact tree `e2504d918d49b554ee861321dcb6bcb608337026`, with rollback snapshot `/opt/ai-short-form-content-factory-runtime-backups/wf02-observable-target-c856228-20260910T093205Z`. Source/current/published parity passed at 46 nodes; current/active version is `81222921-9ce3-4683-89c5-f38acbbad954`; health returned status ok; WF03 remained unchanged. Deployment evidence is preserved in GitHub commit `085e7188b533c5c33fa6ab133bc507b0c2bbaf50`.

Exactly one new normal WF01 job `27915acb-2aa5-49ab-920b-f64b5b62de3b` (`How the Panama Canal locks work` / `ru` / `15`) was then created with HTTP 201. WF01 execution `17185` succeeded. WF02 execution `17186` ran through gateway executions `17187`-`17192`; the multimodal review calls remained serialized with no overlap. The job then failed closed at `Validate Candidate Claims` with `candidate claim 1 is incomplete`. The failed job is immutable and must not be resumed or repaired.

Exact decoded execution evidence shows that gateway execution `17192` returned `provider=kilo`, model `stepfun/step-3.7-flash`, `finish_reason=stop`, `provider_exhausted=false`, and syntactically valid JSON. However the response violated the request's explicit `editorial_role` enum. The supplied schema allows only `hook | establish | mechanism | detail | result | context`, while the model returned `component` for C1 and `process` for C3/C6. The deterministic WF02 validator therefore correctly failed closed.

The general contract defect is in V4 Model Gateway, not in the downstream validator: for structured requests the Kilo request currently asks only for `response_format={type:"json_object"}`, and `Normalize Kilo Response` treats any non-empty `finish_reason=stop` syntactically valid JSON as provider success. It does not validate the parsed payload against the supplied `response_schema`, so schema-invalid Kilo output suppresses the independent Gemini fallback. `Normalize Gemini Response` likewise only performs syntactic JSON validation after transport completion. No enum remapping, JSON repair, retry loop, topic-specific exception or validator weakening is acceptable. Next: verify current Kilo support for strict JSON Schema on the exact production route/model and enumerate every schema keyword used by the six structured product calls; then implement a provider-independent fail-closed schema contract in V4 Model Gateway, test it against all current schemas and the exact enum-failure class, preserve the verified tree in GitHub, deploy V4 only if warranted, and create a completely NEW normal job. Machine completion remains insufficient without exact-artifact assistant visual review and user HUMAN PASS.


### 2026-09-10 provider-independent structured schema enforcement — verified, pending V4-only deployment

Current public Kilo Gateway `/models` metadata was queried from the production VPS before changing source. The exact free route `stepfun/step-3.7-flash:free` is still free and multimodal, but its `supported_parameters` list contains `max_tokens`, `temperature`, `tools`, `reasoning`, and `include_reasoning` and does **not** list `response_format` or `structured_outputs`. The paid `stepfun/step-3.7-flash` route separately lists both `response_format` and `structured_outputs`. Kilo's current Gateway API documents a generic OpenAI-compatible `response_format` field but does not establish strict-schema support for this exact free route. Therefore strict schema compliance cannot be delegated to the free provider.

All six current product `response_schema` contracts were enumerated from the actual workflow builders. They use only `type`, `properties`, `required`, `items`, `enum`, `minItems`, `maxItems`, `minLength`, `maxLength`, and `pattern`; current value types are `object`, `array`, `string`, and `boolean`. V4 Model Gateway now carries the supplied `response_schema` in its internal request context under `schema_contract_version=gateway-json-schema-subset-v1`. Both Kilo and Gemini normalizers apply the same recursive deterministic validator after JSON parsing and before provider success is accepted. The validator covers the complete currently used schema subset and fails closed on an unknown schema keyword instead of silently ignoring it.

For Kilo, a syntactically valid but schema-invalid `finish_reason=stop` response is now recorded as an unsuccessful provider attempt with `schema validation failed: ...`, its text is discarded, and the existing one-shot independent Gemini fallback is used. For Gemini, schema-invalid completed JSON is likewise discarded and normalized as provider exhaustion. There is no JSON repair, enum remapping, retry, sleep, timeout increase, extra model call, paid route, topic-specific exception, or downstream validator weakening. The existing best-effort Kilo `json_object` request is unchanged; the new gateway-side validator is the authoritative acceptance contract.

Regression `model_gateway_schema_contract_regression.mjs` reproduces the exact production failure class (`editorial_role="component"` outside the allowed enum) and proves it falls through instead of being accepted. It also covers valid output, missing required property, regex pattern failure, array cardinality, unknown schema keyword fail-closed, valid Gemini fallback, and schema-invalid Gemini exhaustion. Existing bounded-provider-failover, structured-output, and serialized-review regressions remain green.

Verification on the exact corrected tree is COMPLETE before deployment: **67/67 Node static regressions PASS** in exact `n8nio/n8n:2.37.10` with the explicit real-provider dry run excluded; **13/13 Python static regressions PASS**; all **8** workflow JSON files parse; `git diff --check` PASS; fresh PostgreSQL contract PASS for **21 workflow SQL statements + staged writes**; disposable n8n `2.37.10` import contract PASS for **8/8 workflows**; structured model invocation contract PASS for **6/6 calls** plus reserved-visual binary MIME contract PASS. The V4 correction is now deployed to **V4 Model Gateway only** from GitHub commit `bd935e92e6e93def90e81bf97e42f916acb78310`, exact tree `2cb3017c21b862aca947b560c8df729a41563ecb`. Rollback snapshot: `/opt/ai-short-form-content-factory-runtime-backups/v4-schema-bd935e9-20260910T094942Z`. Zero active executions existed before mutation and after final verification. Source/current V4 core SHA256 is `e74b363d5e6666873e8665b9b245275512808f4d5e295bc1959b6462a9522265`; source/published nodes+connections SHA256 is `71e0c58921148bcc4f131db57809d230789deeb1dbb06cff2ca685ad4893938e`; source/current/published parity passed at 9 nodes. Current/active V4 version is `f2266973-0dd7-46ca-870a-ddc129d1e3b2`. Exactly one n8n restart was performed and `/healthz` returned status ok. WF02 remained unchanged at `81222921-9ce3-4683-89c5-f38acbbad954`; failed jobs `27915acb...` and `b5c0f36e...` remained byte-state unchanged across deployment. Next: preserve this deployment evidence in GitHub, then create exactly one completely NEW normal Panama/ru/15 job and follow it autonomously. Machine completion remains insufficient without exact-artifact assistant visual review and explicit user HUMAN PASS.


## 2026-09-10 fresh WF03 semantic-floor/verbose-draft duration conflict

After V4 schema enforcement was deployed, exactly one completely new normal WF01 job `70fe8dbc-dcf6-4793-8f20-d9007f9e1f79` (`How the Panama Canal locks work` / `ru` / `15`) was created with HTTP 201. WF01 execution `17199` succeeded. WF02 execution `17200` completed successfully through serialized V4 gateway executions `17201`-`17208`; the prior observable-target and schema-invalid-output failure classes did not recur. The job entered WF03/voiceover execution `17209`, proving the corrected WF02/V4 path reached persisted grounded story output.

The job failed closed in WF03 with `Voiceover duration 17.933s is still outside target after 1 bounded story rewrite`. The failed job is immutable and must not be resumed or repaired. Exact execution evidence: the initial Russian narration contained `61` lexical words and measured `28.220333s` with natural `ru-RU-DmitryNeural` (`rate_percent=0`, `post_tempo_factor=1`). The one allowed measured rewrite was forced to exactly `40` words because `Prepare Duration Rewrite` computed `semantic_word_floor=ceil(61*0.65)=40`, despite a proportional measured target near `32` words. The 40-word complete rewrite measured `17.933333s`, above the existing 15s upper acceptance bound `16.533s`.

The systemic conflict is that the `0.65` semantic floor is currently based on raw draft word count, so provider verbosity is treated as semantic information. WF02 already declares a 15s planned story budget of approximately `30-42` spoken words, but its broad deterministic acceptance window allowed this `61`-word draft. A draft that overshoots its own planned budget therefore raises the later semantic floor and can make the exact-duration contract mathematically unreachable even though the frozen claims themselves are compressible. The `0.65` guard remains useful for drafts that respect the planned budget; the defect is letting excess draft verbosity inflate its baseline.

An isolated natural-rate component proof used the same three frozen factual propositions in three complete Russian declarative sentences: `32` lexical words synthesized by the unchanged free Edge path (`ru-RU-DmitryNeural`, `rate_percent=0`, `post_tempo_factor=1`) measured `16.033333s`, inside the existing `13.467-16.533s` acceptance interval. The dummy id was confirmed absent from `public.jobs`; its temporary media directory was deleted immediately after measurement. This proves the current three-claim content can fit without speech-speed manipulation or dropping a story unit.

Next systemic correction: persist WF02's already-defined `target_word_min/target_word_max` in `duration_preflight` and carry that planned budget into WF03. In `Prepare Duration Rewrite`, keep the existing `0.65` ratio and 6-word-per-unit minimum, but compute the semantic-retention baseline as `min(actual_draft_words, planned_target_word_max)` when a valid planned budget is present. Thus a compliant draft behaves exactly as before, while words beyond the upstream planned maximum cannot make the later duration target impossible. Old contexts without the new budget retain the current fallback behavior. The measured proportional controller, one-rewrite maximum, complete-sentence validation, frozen unit/claim/evidence/visual identity, natural speech rate and all fail-closed gates remain unchanged. No extra retry/model call, truncation, topic exception or old-job repair is introduced.

Verification on the exact corrected duration-budget tree is COMPLETE before deployment: **68/68 Node static regressions PASS** in exact `n8nio/n8n:2.37.10` with the explicit real-provider dry run excluded; **13/13 Python static regressions PASS**; all **8** workflow JSON files parse; `git diff --check` PASS; fresh PostgreSQL contract PASS for **21 workflow SQL statements + staged writes**; disposable n8n `2.37.10` import contract PASS for **8/8 workflows**; structured model invocation contract PASS for **6/6 calls** plus reserved-visual binary MIME contract PASS. The new regression reproduces the exact `61 words / 28.220333s / planned max 42` production class and proves a fresh planned-budget context yields semantic baseline `42`, retained 0.65 floor `28`, and measured proportional rewrite target `32`, while a legacy context without the new budget retains baseline `61`, floor `40`, and the prior behavior. The prior 36-word sentence-completion proof remains PASS unchanged. Production has not yet been changed by this correction. Next: commit/push the exact verified tree, verify GitHub identity and zero active executions, capture rollback for **WF02 and WF03 only**, deploy/publish those two workflows, restart n8n once, verify source/current/published parity and failed-job immutability, then create exactly one completely NEW normal Panama/ru/15 job. Machine completion still requires exact MP4 review and explicit user HUMAN PASS.


### 2026-09-10 planned-budget duration correction deployed

GitHub commit `1fcc12ae2bf851039ac6c18cd69c7458529e8d5f`, exact tree `53463fb365dfa8a862d12c14180b9f678a84aa67`, was deployed to **WF02 and WF03 only** after zero-active-execution preflight. Rollback snapshot: `/opt/ai-short-form-content-factory-runtime-backups/wf02-wf03-duration-budget-1fcc12a-20260910T102112Z`. WF02 source/current core SHA256 `4213f0de22dd501c1dccf591115579e15aaf3a0cb4b2aa0018e6455c465dc8fe`, active/current version `fe213021-fba6-4753-9f68-6996efe7b420`, 46 nodes. WF03 source/current core SHA256 `488bb5d53ec6094219127f23ec66a4326411d9c4813ecc258f97aff97ef9f0c3`, active/current version `bccdbbba-8b8f-4424-8ed5-e7b76de4647a`, 21 nodes. One shared n8n restart was performed; `/healthz` returned status ok; active executions after verification were zero. V4 Model Gateway remained unchanged at `f2266973-0dd7-46ca-870a-ddc129d1e3b2`. Failed jobs `70fe8dbc...`, `27915acb...`, and `b5c0f36e...` remained row-state identical across deployment. The deploy script's only nonzero exit occurred after all parity/immutability gates passed, during cleanup of root-owned temporary `/tmp` staging files; rollback had already been disabled. Those files were then removed explicitly as root and the full post-deploy state/health check passed again. Next: preserve this deployment evidence in GitHub and create exactly one completely NEW normal Panama/ru/15 job. Machine completion is not HUMAN PASS.


## 2026-09-10 fresh WF02 candidate hypothesis all-or-nothing failure

After the planned-budget WF02/WF03 correction was deployed, exactly one new normal Panama/ru/15 job `d7bdcaec-1c36-4082-9105-e4f29efc8579` was created with HTTP 201. WF01 execution `17214` succeeded. WF02 execution `17215` failed closed at `Validate Candidate Claims` with `candidate claim C2 mechanism visual target is not claim-aligned`. The failed job is immutable and must not be resumed or repaired. V4 executions `17216`-`17221` were serialized and successful; the prior schema/serialization failure classes did not recur.

Exact decoded model output contained six candidate hypotheses. C2 claimed that freshwater from surrounding lakes fills/drains lock chambers by gravity while its cited target `water channel between concrete walls`/V20 showed only concrete walls and a narrow water channel; the existing mechanism alignment gate correctly rejected it because the hidden gravity/lake mechanism is not visually demonstrated. C5 similarly claimed communicating-vessels/valve water-flow mechanics while targeting only `bulk carrier inside lock chamber`. A diagnostic pass using the exact current per-candidate contract showed `C1,C3,C4,C6` PASS and `C2,C5` REJECT. Thus four fully valid candidates remained. For a 15-second product the downstream story bound is 3-4 units, so four candidates are sufficient for the existing downstream visual review and story planner.

The systemic defect is all-or-nothing behavior at a stage explicitly producing candidate hypotheses: one invalid hypothesis throws the entire job before the remaining valid hypotheses can be independently reviewed. The correction must NOT weaken mechanism/pixel/evidence gates or accept C2/C5. Instead each raw candidate will be deterministically validated and rejected with an audit reason; only accepted candidates continue. The raw model cardinality contract remains unchanged. The run will still fail closed unless the accepted pool is at least the maximum downstream story size for the requested duration (15s=4, 30s=6, 45s=8, 60s=9), retains at least three editorial roles, at least two research evidence rows, and retains an observable mechanism/detail photo option for explanatory intent. Duplicate and malformed hypotheses remain rejected. Accepted candidates retain original claim_id for traceability and receive compact sequential claim_number values for downstream inventory grouping. No model retry, repair loop, topic exception, visual gate weakening, fallback asset, or old-job rescue is introduced.

Next: implement this candidate-pool filtering contract in WF02, add a regression reproducing the exact four-pass/two-reject production class plus insufficient-pool fail-closed behavior, update existing negative regressions to assert rejection rather than accidental acceptance, run the full verification suite, preserve the exact tree in GitHub, deploy WF02 only if all gates pass and zero active product executions exist, then create exactly one completely new normal job. Machine completion is not HUMAN PASS.

Verification on the exact candidate-pool corrected tree is COMPLETE before deployment: **69/69 Node static regressions PASS** in exact `n8nio/n8n:2.37.10` with explicit real-provider dry runs excluded; **13/13 Python static regressions PASS**; all **8** workflow JSON files parse; `git diff --check` PASS; fresh PostgreSQL contract PASS for **21 workflow SQL statements + staged writes**; structured model invocation contract PASS for **6/6 calls** plus reserved-visual MIME contract PASS; disposable n8n `2.37.10` import contract PASS for **8/8 workflows**. The production-class regression proves exactly four valid hypotheses (`C1,C3,C4,C6`) survive while hidden-mechanism mismatches `C2,C5` are rejected and omitted from downstream inventory discovery. It also proves the workflow still fails closed when deterministic rejection leaves fewer than four candidates for a 15-second job. Existing visualizability and mechanism-correspondence negative regressions remain PASS, confirming the visual gate itself was not weakened. Production has not yet been changed by this correction. Next: preserve the exact verified tree in GitHub, verify zero active product executions, capture WF02 rollback/current/published source, deploy/publish **WF02 only**, verify parity/health/failed-job immutability, then create exactly one completely new normal Panama/ru/15 job. Machine completion remains insufficient without exact MP4 review and explicit user HUMAN PASS.


### 2026-09-10 candidate-pool correction deployed

GitHub commit `54742a8b5b415afdf945b6148fa2a3cba18ce32c`, exact tree `c2d86cfb48f3dbc972b62c650a9496b5f7a3f896`, was deployed to **WF02 only** after zero-active-execution preflight. Rollback snapshot: `/opt/ai-short-form-content-factory-runtime-backups/wf02-candidate-pool-54742a8-20260910T112051Z`. An initial deploy attempt published the corrected WF02 but used an overly aggressive fixed 2-second health probe; that probe failed before n8n had finished restarting and triggered the automatic rollback. The rollback completed and exact current/published rollback parity was verified at core SHA256 `4213f0de22dd501c1dccf591115579e15aaf3a0cb4b2aa0018e6455c465dc8fe`; health then returned status ok and active executions were zero. No product job ran during that interval.

The corrected deployment was then repeated with bounded health polling instead of a fixed 2-second sleep. Final source/current/published WF02 core SHA256 is `f3acbff4ca53250c4fbe2ae13a30a926ec51ffe38c50fd310d55dff787806f79`, 46 nodes, active/current version `a443df77-df76-49de-8c1c-aa0799059a22`. Health returned status ok and active executions after verification were zero. WF03 remained `bccdbbba-8b8f-4424-8ed5-e7b76de4647a`; V4 remained `f2266973-0dd7-46ca-870a-ddc129d1e3b2`. Failed jobs `d7bdcaec...` and `70fe8dbc...` remained row-state identical across deployment. Next: preserve this deployment evidence in GitHub and create exactly one completely new normal Panama/ru/15 job. Machine completion is not HUMAN PASS.


## 2026-09-10 fresh pre-claim exploration weak-detail coverage defect

After the candidate-pool correction deployment, exactly one new normal Panama/ru/15 job `477a7177-0651-4e86-bf1f-cd162b8844bd` was created. WF01 execution `17234` succeeded; WF02 execution `17235` failed closed after serialized V4 gateway executions `17236`-`17241` all succeeded. Exact replay of the active validator on the immutable execution input produced `candidate claim pool only 3/4 after deterministic rejection`: C2 and C3 were correctly rejected because their claimed mechanisms were not aligned with the cited pixel-reviewed targets, and C6 was correctly rejected as a duplicate visual target. The failed job must not be resumed or repaired.

The deeper systemic defect is upstream pre-claim exploration adequacy. Exact execution inventory shows mechanism-oriented exploration Q3 (`lock chamber water elevation schematic`) and Q4 (`water control valves and concrete conduits`) admitted generic Panama Canal photos and did not perform bounded recovery. In `visual-discovery.mjs`, exploration recovery currently stops when at least two subject-anchored candidates have any `inventory_detail_hits > 0`. A generic lock photo can therefore count as a detail hit merely through a weak word such as `lock`, allowing generic subject imagery to suppress recovery even when no candidate covers the distinguishing mechanism target. Q3/Q4 consequently exposed no actual elevation schematic, culvert, valve, or conduit image to claim planning.

Systemic direction: keep the strict candidate validator unchanged, but strengthen exploration recovery adequacy from any-detail count to strong target-detail coverage. A candidate should stop bounded recovery only when it covers at least `min(2, number of distinguishing target anchors)` rather than one weak token. Recovery remains bounded and uses the existing compact subject+detail query generator; reviewer authority and fail-closed gates remain unchanged. For explanatory intent, downstream claim quality must continue to require a genuine accepted `mechanism` claim so context/detail imagery cannot substitute for the causal explanation. No topic-specific query, manual asset selection, gate weakening, retry loop, paid provider, or old-job rescue is allowed.


### 2026-09-10 strong-detail visual recovery — verified, pending media-worker-only deployment

Fresh normal job `477a7177-0651-4e86-bf1f-cd162b8844bd` failed closed in WF02 execution `17235`. Exact replay of `Validate Candidate Claims` showed only three of six hypotheses survived: C2 and C3 were correctly rejected as mechanism/visual misalignment and C6 was correctly rejected as a duplicate target. Lowering the 15s accepted-candidate floor would have allowed a generic story that omitted the core hydraulic mechanism, so no quality gate was weakened.

The upstream systemic defect was in free-media exploration recovery. The pre-claim inventory for mechanism-oriented exploration queries contained many generic Panama Canal photos, while Q3 (`lock chamber water elevation schematic`) and Q4 (`water control valves and concrete conduits`) lacked strong target coverage. `rankInventoryCandidates()` exposed `inventory_detail_hits`, but exploration/inventory recovery stopped when two candidates had merely `detailHits > 0`; a common subject token such as `lock` therefore allowed generic subject photos to suppress bounded detail recovery.

The media-worker correction adds a topic-generic `inventory_detail_required` threshold based on the number of distinguishing target anchors and treats a candidate as strong detail coverage only when `inventory_detail_hits >= inventory_detail_required` (normally at least two anchors when two or more exist). Both pre-claim exploration recovery and post-claim inventory recovery use this strong-detail criterion. Generic subject assets remain available as context but can no longer stop bounded search for the requested apparatus/diagram/detail. Bounded fallback count is unchanged. One fallback slot also preserves a strong distinguishing source-query term that is absent from the target wording, preventing terms such as `culvert` from being lost when the target uses a related phrase such as `conduits`. No topic-specific synonym table, manual image choice, provider expansion, extra unbounded search loop, quality-gate relaxation, or old-job repair was added.

Real-provider isolated proof used the current source with the production worker's already configured free provider keys without changing the running service. Q3 now performs bounded recovery and returns strong target-specific Wikimedia results including `File:Panama Canal.gif` (3/2 detail anchors), a proposed lock-canal elevation map (2/2), and `1914 surface of water elevation diagram of the Panama Canal` (2/2). Q4 now performs bounded recovery through at most five provider queries and preserves `Panama Canal lock culvert` as a fallback; the current free providers still did not return a 2/2 culvert/valve asset, so such a hidden mechanism must remain unavailable/fail-closed rather than be represented by generic canal photos.

Verification on the exact current tree is COMPLETE before deployment: **70/70 Node static regressions PASS** with the explicit real-provider dry-run test excluded; **13/13 Python static regressions PASS**; all **8** workflow JSON files parse; `git diff --check` PASS; fresh PostgreSQL contract PASS for **21 workflow SQL statements + staged writes**; disposable exact `n8nio/n8n:2.37.10` import contract PASS for **8/8 workflows**; structured model invocation contract PASS for **6/6 calls** plus reserved-visual MIME contract PASS. New regression `visual_exploration_strong_detail_recovery_regression.mjs` proves that many weak one-anchor subject matches cannot suppress detail recovery. Existing inventory-detail, visual-exploration, and bounded-query-recovery regressions remain PASS.

Preverified media-worker image: `sha256:527c061fd7520ea2182fd9c5458d37ebc3a58686c79939bb40665a1f822b15e7`, tag `ai-short-form-content-factory-media-worker:preverify-strong-detail-3f536c34bdc9`. Exact `visual-discovery.mjs` SHA256 inside the image equals source: `3f536c34bdc998bc950f1febbe5293cb8cc658d153c0e518545ac24ab2382d8e`. Production has not yet been changed by this correction. Next: preserve this exact verified tree in GitHub, verify zero active product executions, capture current media-worker image/source/build-input rollback evidence, recreate **media-worker only** from the exact preverified image, verify worker source SHA and `/health`, then submit exactly one completely NEW normal product job and follow it to the next systemic failure or exact MP4 assistant visual gate. Failed job `477a7177...` remains immutable.


### 2026-09-10 strong-detail media-worker deployment complete

GitHub commit `7c26ac3b2c3cfa8d88da51525fe7c29099192ad7`, exact tree `8382b6eb361c30cd028180d7f8d8d80018cf7060`, was preserved before production mutation. GitHub API independently returned the same commit/tree identity.

Production preflight had zero `new/running/waiting` n8n executions and the newest product job was still immutable failed `477a7177-0651-4e86-bf1f-cd162b8844bd`. The prior media-worker image `sha256:f7157e8366052cbdd772523a4ecf7f7c2da4e73337c71468de7f2068ee9734cd` with running `visual-discovery.mjs` SHA256 `b9e5964d865e77ed3de041dc05839d09b96204b82bf868034d09309778d4848a` was preserved under rollback tag `ai-short-form-content-factory-media-worker:rollback-strong-detail-20260910T125351Z`. Rollback/evidence directory: `/opt/ai-short-form-content-factory-runtime-backups/media-worker-strong-detail-7c26ac3-20260910T125351Z`.

A first compose invocation from the source checkout correctly failed before touching the production worker because Docker Compose inferred the checkout-specific project name and therefore a non-production image name. It created only an unused checkout-scoped network and volume; the production container remained unchanged. Those unused objects were verified to have no containers and removed. The actual production compose labels identify project `ai-short-form-content-factory`, working directory `/opt/ai-short-form-content-factory`, config `/opt/ai-short-form-content-factory/compose.yaml`.

The corrected deployment then recreated **media-worker only** from the exact preverified image `sha256:527c061fd7520ea2182fd9c5458d37ebc3a58686c79939bb40665a1f822b15e7` with no rebuild. Running `/app/src/visual-discovery.mjs` SHA256 is exactly `3f536c34bdc998bc950f1febbe5293cb8cc658d153c0e518545ac24ab2382d8e`, equal to the verified source. Worker `/health` returns status `ok`; Pexels, Pixabay and SearXNG are configured; active n8n executions after verification are zero. No n8n workflow, database schema, failed job or prior artifact was modified.

Next: commit/push this deployment evidence, then submit exactly one completely NEW normal `How the Panama Canal locks work / ru / 15` job through WF01. Follow that job without manual repair. If it fails, preserve the immutable failed job and correct only a demonstrated topic-generic systemic cause. If it reaches MP4, perform exact-artifact assistant visual review; machine completion alone is not HUMAN PASS.


## 2026-09-10 HUMAN FAIL — visual subsystem regression breach on job 2e84dc84

Exact autonomous job `2e84dc84-edd9-4e27-b2b1-6bc7c4aea4b3` (`How the Panama Canal locks work` / `ru` / `15`) completed WF01→WF05 and produced exact MP4 `jobs/2e84dc84-edd9-4e27-b2b1-6bc7c4aea4b3/render/final.mp4`, SHA256 `b55620961fe031867dcde1d8f61f28d84565ddb0eeaa0eab715e1aeff103129e`, natural voiceover `15.470s`. Machine state was `review_ready`; user explicitly rejected the exact artifact on 2026-09-10 and ordered the visual subsystem reworked. Production review decision is now durably `rejected` with HUMAN FAIL notes; this job is immutable and must never be repaired/resumed.

Visible failure repeats permanent regressions already documented: ordinary stills read as landscape/static slideshow material inside a phone canvas instead of a coherent native short-form edit, and the central narration beat says lock chambers fill/empty to lift/lower vessels while the selected shots are only static lock/chamber views and do not visually explain the changing-water-level mechanism.

Source-proven systemic defects exist upstream and downstream of rendering. WF02 `Validate Candidate Claims` currently requires explanatory intent to retain a `mechanism/detail` candidate whose `visual_form` is specifically `photo`, which biases hidden/state-change mechanisms toward ordinary photographs even when diagram/illustration/map is the truthful explanatory form. The visual reviewer contract may accept a target-matching still even when it cannot communicate the operation described by the grounded claim, and final narration may still paraphrase that operation. Separately, media-worker render-v3 constructs `composition_quality` with `pass: true` unconditionally; it reports framing policy names but performs no actual fail-closed composition validation before publishing `review_ready`. Thus a known visible composition regression can pass machine QA.

Direction is a systemic visual-contract rebuild, not a Panama fix and not a cosmetic re-render of this job. The next implementation must: (1) decouple explanatory representation from a mandatory photo lane; (2) make actual-image review return whether an asset can *communicate* the grounded mechanism/state change, separately from factual truth; (3) freeze narration only when selected assets are explanation-capable for explanatory units; (4) reject ordinary photos that cannot survive deliberate 9:16 subject-preserving crop instead of turning them into cards; (5) make still-image motion/composition intentional rather than a static slideshow; and (6) replace unconditional composition PASS with deterministic post-render composition checks. No old-job rescue, topic-specific vocabulary, manual media selection, paid dependency, or quality-gate relaxation is allowed.


## 2026-09-10 V6 full approach reset — implementation branch created

User explicitly rejected continued patching and ordered the approach changed completely. The target V5 `inventory-first-story-v1 -> two reserved stills per unit -> FFmpeg render-v3` architecture is therefore retired for new development. Production remains unchanged as rollback/reference while new work proceeds on branch `rebuild/storyboard-editor-v6-20260910`.

Authoritative new direction: `docs/V6_STORYBOARD_EDITOR_REBUILD.md`. V6 keeps n8n as mandatory orchestrator, PostgreSQL durability, free/self-hosted dependency policy, one continuous natural-rate voice, exact-audio timing, 9:16 output, immutable failed jobs and HUMAN review. The critical path changes to research -> visual story director -> executable shot feasibility -> at most one bounded storyboard replan -> final speech freeze -> TTS -> exact timing -> shot-level exact/annotated/diagram/map/document/collage editor -> real pixel QA -> assistant visual review -> HUMAN review. The old requirement that an explanatory mechanism retain a photo lane is retired; a still that only belongs to the same subject is not sufficient to communicate a mechanism. Landscape media cannot silently become an ordinary portrait shot. Renderer composition PASS must be measured from rendered pixels, not hard-coded.

Production must not be switched to V6 until the new n8n-orchestrated path is verified cross-topic. Do not create more Panama Canal tuning or use the rejected `2e84dc84...` as anything except immutable regression evidence.

## 2026-09-10 V6 architecture reset — visual-facts-first, cross-topic

User explicitly rejected continued incremental repair and required a complete approach change after production showed repeated failures on materially different topics, including `как возникла жизнь на земле?` failing at `visual exploration Q1 lost resolved-subject identity` while the prior Panama artifact repeated known visual-quality failures. V5's accumulated claim/query/identity gates are no longer the target architecture.

New direction is documented in `docs/ARCHITECTURE_V6.md`: one pre-narration real-media discovery/review phase creates pixel-derived Visual Facts; story candidates are authored only from the intersection of research evidence and those Visual Facts; the duplicated post-claim search/review loop leaves the active path; concept/question/process topics use semantic facet relevance instead of literal canonical-subject identity; explanatory units require direct explanation-capable visuals but never a mandatory photo form; portrait-crop safety becomes an inventory property; final narration cannot change frozen evidence/assets; render composition PASS may not be an unconditional constant. Panama is retained only as a regression topic. Production remains unchanged until the V6 source passes full verification and active executions are zero.

### 2026-09-10 cross-topic failures force V6 reset

Two materially different production requests demonstrated that current V5 is not a stable general product. Job `e4dd9e69-830d-4caa-9caa-8d01609bf531` (`как возникла жизнь на земле?` / `ru` / `30`) failed in WF02/script with `visual exploration Q1 lost resolved-subject identity [line 1]`, proving the literal canonical-subject identity policy is invalid for concept/question/process topics. Job `2f0baeec-dbbd-49f4-b7fe-0608be2d7a3e` (`телескоп роман` / `ru` / `30`) later failed in voiceover with free fallback TTS timeout, proving cross-topic reliability also has an independent provider-path failure class. Both jobs are immutable and must not be resumed/repaired.

The production database snapshot now contains 303 exact failed/rejected records (297 status=`failed`, 6 explicit review rejections). They are preserved in `docs/failure-ledger/production-failures-20260910.jsonl`, with an engineering index in `docs/FAILURE_LEDGER.md`. `OPERATOR_EXECUTION_RULES.md` now makes GitHub preservation mandatory before any corrective code change, so a known failure cannot remain only in chat or shell history.

V6 architecture reset is documented in `docs/ARCHITECTURE_V6.md`. No production mutation is authorized merely by this documentation checkpoint. The old Panama topic is regression evidence only, not the sole proof topic.

## 2026-09-10 — V6 first full regression gate failed before deployment

On branch `rebuild/storyboard-editor-v6-20260910`, the first full deterministic regression run of the uncommitted Visual Facts / variable-storyboard change passed workflow JSON parsing and `git diff --check`, but failed **25/71 Node regression files** and **3/13 Python regression files**. No production mutation occurred. One of the 25 Node failures (`semantic_visual_real_provider_dry_run.mjs`) is a manual provider proof that requires `JOB_CONTEXT_FILE` and must be excluded from deterministic-suite counts in the corrected runner.

The failures are not being hidden by deleting tests. They are split into (a) regressions that explicitly encode now-retired V5 nodes/contracts, which require V6 replacement tests preserving the underlying quality invariant, and (b) genuine V6 compatibility gaps in story fixtures/downstream contracts. Exact failure list and policy are recorded in `docs/failure-ledger/v6-regression-gate-20260910.md`. Production V5 remains unchanged.

### V6 source defect found before test migration

Regression triage proved an internal V6 inconsistency: removal of the second post-claim media/fingerprint loop also removed the only guaranteed preview `visual_hash` production path. The new Visual Facts selector does not synthesize hashes, but downstream V6 story assembly already requires them for global no-repeat identity. Therefore test migration is paused until deterministic preview fingerprinting is moved into the single pre-story Visual Facts path. The retired second media search/review loop must not be restored.

### V6 second deterministic regression gate

After the single-pass preview fingerprint correction and V6 regression migration, deterministic verification is at **68/71 Node PASS and 13/13 Python PASS**, with workflow JSON parse and `git diff --check` passing. Three remaining Node failures are test-migration defects (over-specific shortlist identity fixture, an insufficient-pool fixture that did not actually fall below the V6 floor, and the still-unmigrated WF05 two-shot test). Production remains unchanged.

### V6 first integration gate

The deterministic suite is clean at 71/71 Node and 13/13 Python. The unchanged integration suite then produced: n8n 2.37.10 import **8/8 PASS**; fresh PostgreSQL fixture FAIL because it still supplies retired `inventory-first-story-v1` to V6 persist SQL; structured invocation fixture FAIL because it hard-codes 6 model calls while V6 intentionally removed the second semantic review and now has 5. These are integration-fixture migration failures, not permission to restore V5 behavior. Production remains unchanged.

### V6 PostgreSQL story-package incompatibility found before commit

Fresh-database integration with an actual `visual-facts-story-v1` payload failed at PostgreSQL constraint `jobs_story_package_check`. This proves the current DB bootstrap still encodes V5-only story-package acceptance and would make the V6 WF02 persist path impossible. The correction must explicitly support V6 `visual-facts-story-v1` / `storyboard-v1` while retaining V5 compatibility for immutable historical jobs and preserving units/assets/cardinality checks. Production remains unchanged.

### V6 fresh bootstrap syntax failure

The first baseline update for the V6 story-package constraint failed real PostgreSQL parsing because the manually rewritten pg_dump-style one-line CHECK expression had malformed parentheses. This is recorded before correction. The fix is to use a readable multiline CHECK expression matching migration `024` and prove it with the disposable PostgreSQL integration test. Production remains unchanged.

### V6 visual-segment 3-shot schema incompatibility

Fresh PostgreSQL now accepts the V6 story package and existing 1/2-shot staged writes, but rejects a V6 3-shot segment at `visual_segments_shot_count_check`. The durable DB schema still encodes the retired V5 1-2 shot limit. V6 requires an explicit 1-3 upgrade while all other visual quality/identity/timing gates remain unchanged. Production remains unchanged.
