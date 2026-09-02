# Engineering History — Rebuild

Chronological durable record for material changes, failures, verified root causes, regressions, deploys and rollback facts. `docs/CURRENT_STATE.md` remains the operational source of truth.

## 2026-09-02 — Induction visual quality invalidated previous machine PASS

Job: `13f64c50-8dd5-47e4-a88f-1411d258e7c4`

Observed product failure:

- job was previously marked `review_ready`;
- six scenes were marked `visual_ready`;
- human-visible inspection showed only two effective visual states across the ~14-second video;
- roughly the first four seconds used one image and most of the remainder used another.

Verified systemic root cause:

- production acceptance checked per-scene asset presence, not video-level visual sequence quality;
- the clean rebuild had effectively reduced sourcing to a small canonical/Wikimedia pool;
- max-unique assignment by candidate/file ID could not guarantee perceptual diversity.

Decision:

- previous induction machine PASS is invalidated;
- full visual-pipeline rewrite is active;
- no further M8 progression until new sequence-level gates are regression-tested and boundedly deployed.

## 2026-09-02 — Multi-source visual rewrite started locally

Local rebuild work includes:

- `services/media-worker/src/visual-discovery.mjs`;
- `services/media-worker/src/visual-quality.mjs`;
- `db/migrations/013_visual_quality_gate.sql`;
- rewritten `n8n/workflows/WF04-visual-sourcing.json`;
- strengthened `n8n/workflows/WF05-video-render.json`;
- still-image motion in `services/media-worker/src/visual-framing.mjs`;
- pre-render and post-render visual-state checks in `services/media-worker/src/server.mjs`.

Provider facts:

- Wikimedia Commons expanded search is usable;
- Pixabay direct provider check works with the configured key;
- an earlier standalone Pexels check returned HTTP 403, so Pexels remains optional and may never be required for pipeline success.

Real induction dry-run before perceptual clustering:

- about 20–22 Wikimedia candidates discovered per beat;
- up to 10 truth-eligible candidates per beat;
- six different induction-related assets could be assigned instead of two repeated assets.

The dry-run also exposed missing `duration_seconds` propagation, which produced `NaN` in one quality metric. The propagation was corrected locally and non-finite diversity metrics are fail-closed.

## 2026-09-02 — Perceptual identity added to ranking and assignment

Material change:

- `/visual/rank` locally computes a 256-bit average-hash fingerprint from the ranked preview;
- WF04 validates the returned 64-hex-character `visual_hash`;
- global assignment clusters candidates by Hamming distance rather than treating different candidate IDs as automatically different visuals;
- current clustering threshold is 18 bits out of 256;
- assignment requires 75% unique perceptual states, minimum 3, capped by beat count; for 6 beats this is 5 states;
- adjacent duplicate clusters are forbidden;
- a cluster may occupy at most 34% of total duration.

This is a systemic sequence-level rule, not a topic-specific induction patch.

## 2026-09-02 — Diagnostic compile harness false result

Diagnostic mistake:

- an initial compile harness treated n8n workflow export JSON as an object;
- the actual rebuild exports are top-level arrays containing one workflow object;
- the broken harness therefore reported `WF04_CODE_COMPILE_PASS 0` and `WF05_CODE_COMPILE_PASS 0` without compiling the Code nodes.

Correction:

- harness now unwraps the first array element before iterating nodes;
- verified actual node counts are WF04 `14` Code nodes and WF05 `8` Code nodes;
- corrected compile run: `WF04_CODE_COMPILE_PASS 14`, `WF05_CODE_COMPILE_PASS 8`.

Rule:

- never use a zero-count compile result as PASS;
- workflow-export shape must be validated before Code-node compilation.

## 2026-09-02 — Visual quality v1/v2 contract mismatch found and fixed locally

Verified defect:

- WF04 pre-render logic had already moved to `visual_cluster_key` perceptual diversity;
- media-worker render preflight still called old `visual-quality-v1` using only `asset_key`;
- therefore six different files that were perceptually only two states could pass the renderer's pre-render sequence check and rely only on post-render detection.

Systemic correction:

- `services/media-worker/src/visual-quality.mjs` now exposes `evaluateVisualSequence` with `visual-quality-v2` semantics;
- perceptual `visual_cluster_key` is authoritative for sequence diversity;
- `asset_key` is retained for file identity/audit only;
- WF05 manifest now carries both `asset_key` and `visual_cluster_key`;
- media-worker requires both identities before rendering;
- WF05 independently validates v2 cluster metrics and returned beat cluster identity;
- post-render frame-state validation uses the same required perceptual state count.

Regression proof after the correction:

- `VISUAL_QUALITY_V2_REGRESSION_PASS`;
- fixture with 6 unique file IDs but only 2 perceptual clusters: FAIL;
- fixture with 6 file IDs and 5 perceptual clusters, no adjacent duplicate, max cluster share 0.3333: PASS;
- near-identical synthetic 256-bit hashes cluster together;
- malformed hash size fails closed;
- `WF04_PERCEPTUAL_ASSIGNMENT_REGRESSION_PASS` proves six different candidate IDs can collapse to five perceptual states and a four-state fixture fails with `4/5`;
- media-worker module syntax PASS;
- `WF04_CODE_COMPILE_PASS 14`;
- `WF05_CODE_COMPILE_PASS 8`.

Production status at this point:

- none of these rewrite changes are deployed yet;
- production still has exactly three running services.

## 2026-09-02 — Media-worker provider environment wiring defect

Verified configuration error:

- earlier diagnostics had incorrectly described rebuild compose as already passing `PIXABAY_API_KEY` and `PEXELS_API_KEY` into `media-worker`;
- fresh exact compose inspection showed those variables existed only in the `n8n` service environment;
- the `media-worker` service had only `PORT`, so the new discovery adapter could never use Pixabay/Pexels after a normal rebuild/deploy even though keys existed in `.env`.

Systemic correction made locally:

- `compose.yaml` media-worker environment now includes `PIXABAY_API_KEY: ${PIXABAY_API_KEY}` and `PEXELS_API_KEY: ${PEXELS_API_KEY}`;
- no secret values are stored in Git;
- Pexels remains optional regardless of current health;
- Pixabay can now be actually available to the worker after container recreation.

Production is not changed yet. Current production still has exactly three running services.

## 2026-09-02 — Exact induction perceptual dry-run PASS

The rewrite was tested without deploying by building a temporary rewrite media-worker image and running the actual WF04 Code-node bodies against the persisted old induction job context. The three production services remained unchanged before and after the test.

Exact source job used only as immutable dry-run input:

- `13f64c50-8dd5-47e4-a88f-1411d258e7c4`;
- topic `How does induction heating work?`;
- language `en`;
- target `15`;
- 6 persisted timed beats and 6 persisted evidence rows.

Temporary worker proof:

- `/health` PASS with `Xenova/siglip-base-patch16-224`, dtype `q4`;
- `PIXABAY_API_KEY` and `PEXELS_API_KEY` were both actually present in the temporary worker environment without exposing values;
- discovery provider counts: canonical article `5`, Pexels `15`, Pixabay `18`;
- this exact adapter request reported no provider errors, so the older standalone Pexels HTTP 403 result must not be generalized into a claim that the current discovery adapter is always unhealthy; Pexels nevertheless remains optional by architecture;
- every induction beat discovered `53–55` normalized candidates from Wikimedia/Pexels/Pixabay;
- truth eligibility reduced each beat to a bounded pool of `10` candidates; the selected eligible pools contained Pixabay and Wikimedia candidates.

Actual local SigLIP/perceptual proof:

- every ranked candidate returned a valid 64-hex-character `visual_hash`;
- the actual `Attach Rank Results` and `Choose Visual Assignment` Code-node logic executed successfully;
- selected assets were six different induction-related Wikimedia visuals, including `Induction heating of bar`, `Stirling radioisotope generator head testing`, `Induction heating apparatus 1927`, `Silicon grown by Czochralski process 1956 closeup`, `Northup induction furnace`, and `Induction heater`;
- final pre-render quality: version `visual-quality-v2`, 6 assets, 6 perceptual clusters, required 5, adjacent duplicate clusters `0`, max cluster-duration share `0.1813`, PASS;
- all quality values were finite;
- proof marker: `INDUCTION_PERCEPTUAL_DRYRUN_PASS`.

This is a dry-run proof of the new sourcing/ranking/assignment contract, not a human-visible production PASS. No production workflow/container/schema was changed.

## 2026-09-02 — Cross-topic PL combustion-engine dry-run PASS

Cross-topic fixture:

- language `pl`;
- topic `Jak działa silnik spalinowy?`;
- canonical source `pl:Silnik spalinowy`;
- six factual beat fragments derived from the Polish Wikipedia introduction;
- no TTS and no production job mutation.

Actual rewrite behavior:

- discovery returned `52–53` normalized candidates per beat;
- provider discovery was active, but strict truth eligibility reduced the per-beat pools to `3–4` Wikimedia candidates for this source;
- the canonical source did not resolve an English langlink in the tested API response, so the case also exercises the non-English canonical-title fallback;
- the actual SigLIP/perceptual/global assignment selected 5 unique assets forming 5 perceptual clusters for 6 beats;
- one visual cluster was reused non-adjacently;
- quality: `visual-quality-v2`, required clusters `5`, actual clusters `5`, adjacent duplicates `0`, max cluster-duration share `0.3333`, PASS;
- proof marker: `PL_COMBUSTION_ENGINE_DRYRUN_PASS`;
- production still had exactly `media-worker`, `n8n`, `postgres` running after the test.

## 2026-09-02 — Cross-topic RU refrigerator dry-run PASS

Cross-topic fixture:

- language `ru`;
- topic `Как работает холодильник?`;
- canonical source `ru:Холодильник`, resolved English title `Refrigerator`;
- six factual beat fragments derived from the Russian Wikipedia introduction;
- no TTS and no production job mutation.

Actual rewrite behavior:

- discovery returned `69–72` normalized candidates per beat;
- provider discovery counts: canonical article `19`, Pexels `15`, Pixabay `18`, with no provider errors in this request;
- every truth-eligible pool contained the bounded maximum `10` candidates and included candidates from Pexels, Pixabay and Wikimedia;
- actual assignment used Wikimedia and Pexels assets;
- quality: `visual-quality-v2`, 6 assets, 6 perceptual clusters, required `5`, adjacent duplicates `0`, max cluster-duration share `0.1667`, PASS;
- proof marker: `RU_REFRIGERATOR_DRYRUN_PASS`;
- production still had exactly `media-worker`, `n8n`, `postgres` running after the test.

## 2026-09-02 — Cross-topic UK volcano dry-run PASS

Cross-topic fixture:

- language `uk`;
- topic about how a volcano works;
- canonical source `uk:Вулкан`, resolved English title `Volcano`;
- six factual beat fragments derived from the Ukrainian Wikipedia introduction;
- no TTS and no production job mutation.

Actual rewrite behavior:

- an initial attempt was interrupted by a SentinelX agent disconnect and was not counted;
- recovery check confirmed no temporary rewrite container remained and production still had exactly `media-worker`, `n8n`, `postgres` running;
- the repeated clean dry-run discovered `95–112` normalized candidates per beat;
- provider discovery counts: canonical article `44`, Pexels `15`, Pixabay `18`, with no provider errors;
- all six truth-eligible pools contained the bounded maximum `10` candidates and included Pexels, Pixabay and Wikimedia;
- actual assignment used Wikimedia and Pexels assets;
- quality: `visual-quality-v2`, 6 assets, 6 perceptual clusters, required `5`, adjacent duplicates `0`, max cluster-duration share `0.1667`, PASS;
- proof marker: `UK_VOLCANO_DRYRUN_PASS`;
- production still had exactly `media-worker`, `n8n`, `postgres` running after the test.

Cross-topic pre-deploy evidence is now complete across EN induction, PL combustion engine, RU refrigerator and UK volcano.

## 2026-09-02 — Visual rewrite pre-commit gate PASS

The first broad pre-commit run exposed test-harness problems rather than product failures:

- `staged_pipeline_regression`, `case1_staged_regression`, and `case1_visual_regression` were invoked in a disposable container without their historical `/tmp` fixture mounts;
- `wf04_code_node_runtime_regression` and `wf04_download_dedupe_regression` were invoked without their required external fixture environment variables;
- `wf04_assignment_regression` still encoded the obsolete `candidate_id == unique visual` matcher and did not provide the now-required `visual_hash`;
- `wf04_representation_relevance_regression` extracted helpers from the old canonical-only planner and no longer represented the actual WF04 runtime contract.

Correction without weakening product gates:

- historical CASE1/staged tests were rerun with their preserved real fixtures and passed unchanged;
- `wf04_assignment_regression` now tests perceptual-cluster assignment and fail-closed insufficient diversity;
- `wf04_representation_relevance_regression` now executes the actual current planner and verifies that metadata-irrelevant media is excluded before ranking;
- `wf04_code_node_runtime_regression` is self-contained and executes the actual current Prepare + Build Code nodes with a multi-source truth-eligibility fixture;
- `wf04_download_dedupe_regression` is self-contained and proves non-adjacent reuse dedupes one download while preserving `visual-quality-v2` metadata;
- no diversity threshold, factual eligibility rule, duration gate, or provider requirement was weakened.

Final full pre-commit proof:

- media-worker syntax PASS for `server.mjs`, `visual-discovery.mjs`, `visual-quality.mjs`, `visual-framing.mjs`;
- WF04 Code compile PASS `14` nodes; WF05 Code compile PASS `8` nodes;
- `visual_discovery_regression` PASS;
- `visual_quality_regression` PASS;
- `wf04_perceptual_assignment_regression` PASS;
- updated `wf04_assignment_regression` PASS;
- updated `wf04_code_node_runtime_regression` PASS with eligible Pexels/Pixabay/Wikimedia candidates;
- updated `wf04_download_dedupe_regression` PASS;
- `wf04_rank_query_contract_regression` PASS, max query `200`;
- updated `wf04_representation_relevance_regression` PASS;
- `deterministic_visual_cross_topic_regression` PASS;
- `r4v_visual_integrity_regression` PASS;
- `staged_pipeline_regression` PASS, retained Edge corpus `150`, safe count `40`, false-safe `0`;
- `case1_staged_regression` PASS;
- `case1_visual_regression` PASS;
- `wf04_final_design_gate.py` PASS;
- migration 013 DDL executed inside an explicit transaction and rolled back; `jobs.visual_quality` count was `0` before and `0` after rollback;
- production `.env` resolves non-empty `PIXABAY_API_KEY` and `PEXELS_API_KEY` for the corrected media-worker compose contract; secret values were not printed;
- production remained exactly `media-worker`, `n8n`, `postgres`; PostgreSQL stayed healthy.

The visual rewrite is now eligible for a coherent local commit. The unrelated WF02 fact-search-query change and its regression must remain outside that commit and be handled separately after the visual rewrite is deployed and proven.