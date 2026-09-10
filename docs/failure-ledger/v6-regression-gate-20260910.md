# V6 regression gate failure — 2026-09-10

Branch: `rebuild/storyboard-editor-v6-20260910`
Base pushed checkpoint: `f7e03a39ce6897bc44fdbaeac98111a410ce71d0`
Production mutation: **none**.

The first full regression run against the uncommitted V6 architecture change failed before any deployment.

## Exact gate result

- workflow JSON parse: PASS (8/8)
- `git diff --check`: PASS
- Node regression files discovered: 71
- Node failures: 25
- Python regression files discovered: 13
- Python failures: 3

One Node file, `semantic_visual_real_provider_dry_run.mjs`, is an environment-driven manual/provider proof and failed because `JOB_CONTEXT_FILE` was intentionally absent; it is not a deterministic unit regression and must not be counted as a product-contract failure in the corrected runner.

## Failing Node regressions

- `editorial_shot_plan_contract_regression.mjs`
- `editorial_story_schema_contract_regression.mjs`
- `inventory_claim_visualizability_contract_regression.mjs`
- `inventory_observed_claim_contract_regression.mjs`
- `inventory_retrieval_query_contract_regression.mjs`
- `inventory_review_budget_regression.mjs`
- `inventory_unique_review_shortlist_regression.mjs`
- `inventory_visual_binding_priority_regression.mjs`
- `inventory_visual_target_review_contract_regression.mjs`
- `semantic_visual_real_provider_dry_run.mjs` (manual/provider fixture; missing env)
- `wf02_availability_first_visual_exploration_regression.mjs`
- `wf02_candidate_pool_filter_regression.mjs`
- `wf02_inventory_first_story_regression.mjs`
- `wf02_mechanism_visual_correspondence_regression.mjs`
- `wf02_observable_target_lexical_regression.mjs`
- `wf02_visual_review_serialization_regression.mjs`
- `wf04_code_node_runtime_regression.mjs`
- `wf04_download_dedupe_regression.mjs`
- `wf04_exact_phrase_exposure_regression.mjs`
- `wf04_global_no_repeat_recovery_regression.mjs`
- `wf04_perceptual_assignment_regression.mjs`
- `wf04_photo_relevance_gate_regression.mjs`
- `wf04_representation_relevance_regression.mjs`
- `wf05_visual_segments_regression.mjs`
- `workflow_reference_and_fingerprint_contract_regression.mjs`

## Failing Python regressions

- `wf02_grounded_ai_architecture_regression.py`
- `wf02_selected_language_source_regression.py`
- `wf02_wf03_exact_tts_gate_regression.py`

## Diagnosis before correction

The failures split into two classes and must not be treated the same:

1. **Retired-contract tests.** Several regressions assert that the removed second media-search/review loop exists (`Discover Pre-Script Visual Inventory`, `Prepare Inventory Review Batches`, `Select Verified Claim Inventory`, inventory fingerprint nodes), or require the old `inventory-first-story-v1` / exactly-two-shot contract. These tests must be replaced by V6 assertions that preserve the original quality invariant without resurrecting the retired architecture.
2. **Real V6 compatibility gaps.** Story fixtures, schema expectations, WF04 runtime fixtures and downstream render contracts still assume V5 fields or two-shot behavior. Those must be corrected in source and regression fixtures together, with no quality-gate weakening.

The corrective rule is: do not make old tests green by restoring V5 architecture, and do not delete a regression unless its safety/quality invariant is represented by an explicit V6 replacement regression.

## Additional source defect proven during regression triage

The first V6 implementation removed the old post-claim fingerprint loop but `Select Pre-Claim Visual Inventory` still passes discovery candidates that do not contain a deterministic `visual_hash`. `Validate Candidate Claims` then materializes `verified_visual_assets.visual_hash` from that missing field, while `Build Final Inventory Story` requires visual hashes to enforce no-repeat identity. This makes the current uncommitted V6 path internally inconsistent even if obsolete V5 tests were rewritten.

Correction must move deterministic preview fingerprinting into the single pre-story Visual Facts inventory path. It must not restore the retired second media-search/review loop. Pixel review remains single-pass; fingerprinting is deterministic media identity, not a second semantic review.

## Second deterministic gate

After moving preview fingerprinting into the single inline Visual Facts media pass and replacing retired V5 regressions with V6 invariants, the deterministic suite improved to:

- Node: **68/71 PASS**, 3 failures;
- Python: **13/13 PASS**;
- workflow JSON parse: PASS;
- `git diff --check`: PASS.

Remaining Node failures are regression-migration issues, not new production/runtime failures:

1. `inventory_unique_review_shortlist_regression.mjs` used one overly specific deep-candidate identity assertion even though the invariant is global unique round-robin exposure;
2. `wf02_candidate_pool_filter_regression.mjs` attempted to create a below-floor fixture but only rejected one additional candidate, leaving the pool at the accepted minimum;
3. `wf05_visual_segments_regression.mjs` still asserts the retired V5 `[1,2].includes(count)` / old render labels instead of the V6 1-3 storyboard contract.

No production mutation occurred.

## First V6 integration gate

After deterministic verification reached 71/71 Node and 13/13 Python PASS, the existing integration suite was run unchanged before any fixture migration.

Results:
- disposable n8n `2.37.10` import: **8/8 PASS**;
- fresh PostgreSQL contract: FAIL in the test fixture because it still submits `inventory-first-story-v1`; current V6 persist SQL correctly requires `visual-facts-story-v1`, so the fixture returned `inserted_evidence=0`, `job_updated=false`;
- structured model invocation contract: FAIL because the test hard-coded **6** structured calls while the V6 removal of the second semantic media-review loop intentionally leaves **5** structured calls.

These failures do not authorize restoring the retired second review loop or accepting the legacy V5 story package in the V6 persist path. Integration fixtures must be migrated to the V6 story contract while retaining staged-write, exact-TTS, binary MIME and structured-call reachability checks. Production mutation: none.

## Second V6 integration gate — real database contract defect

After migrating the integration fixture to submit `visual-facts-story-v1`, fresh PostgreSQL rejected the V6 row with `jobs_story_package_check`. The failing row contained a V6 `story_package`, proving the database bootstrap/check constraint still permits only the retired V5 story package shape/version. This is a real V6 source/schema incompatibility, not a test-only issue: WF02 V6 persist cannot succeed against the current database contract.

Correction must extend the durable PostgreSQL story-package constraint for the explicit `visual-facts-story-v1` / `storyboard-v1` contract while retaining V5 compatibility for existing immutable historical jobs. Existing constraints on JSON type, units/assets cardinality and durable state must remain fail-closed. Production mutation: none.

## Third V6 integration gate — bootstrap SQL syntax defect

The first implementation of V6 `jobs_story_package_check` used a manually rewritten pg_dump-style single-line CHECK expression in `db/init/001_init.sql`. Fresh PostgreSQL rejected the baseline at parse time with `syntax error at or near ','`, proving the hand-counted parenthesis form was malformed. Migration `024` itself was not applied to production; production mutation remains none.

Correction: replace the baseline constraint with a readable multiline CHECK expression matching migration `024`, then rerun the actual disposable PostgreSQL bootstrap instead of relying on text inspection.

## Fourth V6 integration gate — visual segment cardinality defect

After correcting the bootstrap story-package syntax, the real disposable PostgreSQL test successfully passed the V6 story-package persist and the existing 1-shot/2-shot staged visual writes, then failed the new 3-shot V6 write at `visual_segments_shot_count_check`. The durable schema still restricts `planned_shot_count` to the V5 range 1-2, while V6 explicitly supports 1-3 frozen storyboard shots per semantic unit.

This is a real schema/runtime incompatibility, not a reason to reduce V6 back to two shots. Correction must widen only this durable cardinality constraint from 1-2 to 1-3; global asset uniqueness, perceptual uniqueness, shot-duration limits, portrait safety and contiguous timing remain unchanged. Production mutation: none.
