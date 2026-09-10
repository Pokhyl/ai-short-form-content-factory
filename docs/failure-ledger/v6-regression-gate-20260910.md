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
