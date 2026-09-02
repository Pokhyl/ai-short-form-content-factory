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
- Pexels configured key returned HTTP 403 and therefore must remain optional;
- production compose and `.env` carry Pixabay/Pexels variables, but the currently running media-worker was created without them. Bounded deploy must recreate the container and verify the live environment without exposing secret values.

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
- production still has exactly three running services;
- next action is exact induction dry-run through the new perceptual hash/rank contract, followed by materially different cross-topic dry-runs before commit/deploy.
