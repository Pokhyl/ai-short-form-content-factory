# Engineering History — Rebuild

Chronological durable record for material changes, failures, verified root causes, regressions, deploys and rollback facts. `docs/CURRENT_STATE.md` remains the operational source of truth.

This file was compacted on 2026-09-02 after the visual-quality-v2 production proof. The compaction preserves the material failures, decisions, commits, rollback locations, deployment facts and acceptance evidence from the earlier detailed log. Exact implementation history remains recoverable from the listed commits and rollback snapshots.

## 2026-09-02 — Previous induction machine PASS invalidated by human-visible failure

Job: `13f64c50-8dd5-47e4-a88f-1411d258e7c4`.

Observed product failure:

- the job had reached `review_ready` and all six scenes were `visual_ready`;
- human-visible inspection showed only two effective visual states across the ~14-second video;
- roughly the first four seconds used one image and most of the remaining video used another.

Verified systemic root cause:

- production acceptance checked per-scene asset presence, not video-level visual-sequence quality;
- the clean rebuild had effectively reduced sourcing to a small canonical/Wikimedia pool;
- different candidate/file IDs were incorrectly sufficient to count as different visuals.

Decision:

- the old induction machine PASS is permanently invalidated;
- M8 progression stopped;
- a sequence-level visual architecture was required instead of topic-specific matcher patches.

## 2026-09-02 — Visual-quality-v2 rewrite designed and regression-proven

New required visual path:

`timed beat + evidence -> deterministic search intents -> multi-source candidate discovery -> metadata/provenance eligibility -> local SigLIP ranking + perceptual identity -> global sequence assignment -> sequence quality gate -> persist -> render -> post-render visual-state gate -> review_ready`

Material implementation:

- `services/media-worker/src/visual-discovery.mjs` — bounded normalized discovery from canonical article media, Wikimedia Commons, Pixabay, and optional Pexels;
- `services/media-worker/src/visual-quality.mjs` — fail-closed sequence-quality contract;
- `/visual/rank` returns a 256-bit perceptual preview hash;
- WF04 assigns globally by perceptual clusters instead of candidate ID only;
- WF05 independently validates persisted visual quality before render;
- media-worker independently validates actual rendered midpoint-frame diversity after render;
- still photographs receive deterministic subtle motion; factual diagrams remain stable/readable;
- migration `013_visual_quality_gate.sql` adds durable `jobs.visual_quality`.

Current visual-quality-v2 sequence contract:

- every beat has one truth-eligible selected asset;
- 6 beats require at least 5 distinct perceptual clusters;
- adjacent duplicate clusters are forbidden;
- no cluster may occupy more than `0.34` of total beat duration;
- missing/NaN/non-finite metrics fail closed;
- post-render midpoint frames must independently satisfy the same required state count.

Negative regression fixture remains the old induction pattern: 6 beats but only 2 effective clusters, 4 adjacent repeats and ~68% duration share for one visual -> MUST FAIL.

Positive 6-beat fixture: at least 5 perceptual clusters, no adjacent duplicates, max share <= 0.34 -> PASS.

## 2026-09-02 — Diagnostic compile-harness false PASS/FAIL risk corrected

A diagnostic harness initially treated n8n workflow exports as objects even though rebuild exports are top-level arrays. That produced meaningless zero-count compile output.

Correction:

- workflow export shape is now validated/unwrapped before compiling Code nodes;
- verified counts: WF04 `14` Code nodes, WF05 `8` Code nodes;
- a zero-count compile result is never accepted as PASS.

## 2026-09-02 — WF04/media-worker visual-quality-v1/v2 mismatch corrected

Verified defect:

- WF04 had moved to perceptual `visual_cluster_key` diversity;
- media-worker pre-render logic still used file `asset_key` uniqueness;
- six different files representing only two perceptual states could therefore pass the renderer preflight.

Correction:

- perceptual cluster identity is authoritative for sequence diversity;
- file identity is retained only for audit/download identity;
- WF05 manifest carries both identities;
- media-worker requires both and validates visual-quality-v2;
- post-render frame clustering uses the same required state count.

Regression proof included:

- 6 distinct file IDs but only 2 clusters -> FAIL;
- 6 file IDs and 5 clusters -> PASS;
- malformed perceptual hashes fail closed;
- `WF04_PERCEPTUAL_ASSIGNMENT_REGRESSION_PASS`;
- `WF04_CODE_COMPILE_PASS 14`;
- `WF05_CODE_COMPILE_PASS 8`.

## 2026-09-02 — Media-worker provider-environment wiring defect corrected

Verified configuration defect:

- production `.env` had Pixabay/Pexels values, but the media-worker compose service did not receive them;
- a normal worker recreate therefore could not use those adapters.

Correction:

- compose now passes `PIXABAY_API_KEY` and `PEXELS_API_KEY` to media-worker without storing secret values in Git;
- Pexels remains optional and can never be required for success.

## 2026-09-02 — Cross-topic pre-deploy dry-runs PASS

Actual rewritten discovery/ranking/assignment was exercised on materially different topics/languages before production deployment.

EN induction:

- exact old induction context used only as immutable dry-run input;
- about 53-55 normalized candidates per beat in the final adapter run;
- truth eligibility reduced to bounded pools;
- actual local SigLIP returned valid 64-hex perceptual hashes;
- final assignment: 6 assets / 6 perceptual clusters, required 5, adjacent duplicates 0, max duration share `0.1813` -> PASS.

PL combustion engine:

- 5 perceptual clusters for 6 beats;
- one cluster reused non-adjacently;
- adjacent duplicates 0;
- max share `0.3333` -> PASS.

RU refrigerator:

- 6 assets / 6 perceptual clusters;
- adjacent duplicates 0;
- max share `0.1667` -> PASS.

UK volcano:

- 6 assets / 6 perceptual clusters;
- adjacent duplicates 0;
- max share `0.1667` -> PASS.

No threshold was lowered for any topic.

## 2026-09-02 — Visual rewrite pre-commit gate PASS

Broad proof before commit included:

- media-worker syntax PASS;
- WF04 Code compile PASS `14`;
- WF05 Code compile PASS `8`;
- visual discovery regression PASS;
- visual quality v2 regression PASS;
- perceptual assignment PASS;
- representation-relevance PASS;
- download-dedupe PASS;
- rank-query contract PASS at maximum 200 characters;
- deterministic cross-topic visual regression PASS;
- staged pipeline regression PASS on retained Edge corpus: 150 samples, safe count 40, false-safe 0;
- CASE1 staged/visual regressions PASS;
- migration 013 DDL transaction/rollback proof PASS;
- no provider secret value appeared in the staged patch.

The unrelated WF02 native-Wikipedia retrieval-query work was explicitly excluded.

## 2026-09-02 — Visual rewrite committed locally

Commit:

- `f7c4096503c9620910b387129a5a06cce4d26d42`
- `redesign: enforce perceptual visual diversity`

Selective commit contained compose, migration 013, WF04, WF05, media-worker visual/render modules and visual regression tests only. WF02 retrieval work and `.env` were excluded.

## 2026-09-02 — Pre-deploy visual-quality-v2 rollback snapshot

Rollback path:

`/opt/ai-short-form-content-factory/rollback/20260902T175543Z-pre-visual-quality-v2`

Snapshot captured production compose, media-worker source, WF04/WF05 file copies, exact live workflow exports, public schema/core-column metadata and runtime/container identities. `.env` was deliberately excluded.

## 2026-09-02 — Visual-quality-v2 deployed to production

Schema/media-worker phase:

- exact committed files from `f7c4096` were copied and byte-compared;
- migration 013 applied successfully;
- `jobs.visual_quality` and its object constraint are live;
- media-worker recreated with provider env present, values not exposed;
- `/health` PASS with local `Xenova/siglip-base-patch16-224`, dtype `q4`;
- direct `/visual/discover` returned Wikimedia/Pexels/Pixabay candidates;
- direct `/visual/rank` returned valid 64-hex perceptual hashes.

WF04/WF05 publication:

- WF04 `M6VisualSourcing1` and WF05 `M7VideoRender1` imported/published;
- n8n restarted exactly once after both publications;
- live workflow core equality PASS;
- WF04 live core SHA-256 at this checkpoint: `cc09f58e9ee74c346b1270bc7d014690fdcf4e163fa8a403d8839b152384cd5f`;
- WF05 live core SHA-256: `c8e5d25c7114af81ea8ea19bf41560f2d4393f5292c5416fd5b8a2455bc289e9`;
- exactly three persistent services remained running and PostgreSQL healthy.

## 2026-09-02 — Fresh induction exposed reference-media lifecycle mismatch

Fresh post-deploy job:

`1afc307d-aaac-4eed-8387-b05e1b6721eb`

WF04 execution: `9902`.

Upstream had already completed one Edge synthesis, measured duration `13.944 s` and six timed beats. WF04 then failed during visual-plan persistence.

Exact error:

`new row for relation "scenes" violates check constraint "scenes_reference_media_kind_check"`

Failing row semantics:

- `visual_evidence_type = technical_reference`;
- `reference_media_kind = mixed`;
- status `visual_planned`.

Verified systemic root cause:

- `mixed` was being used as a fake durable media kind to mean “not selected yet”;
- the database correctly only recognizes actual non-null kinds `diagram|animation|photo`;
- the staged lifecycle contract did not allow a technical reference to remain unset while still `visual_planned`.

The failed job was not reused because its one allowed Edge synthesis had already occurred.

## 2026-09-02 — Reference-media lifecycle fixed systemically

Correction:

- WF04 uses `reference_media_kind = NULL` while a technical reference is only `visual_planned`;
- after actual asset selection, `visual_ready` persists the concrete `photo|diagram|animation`;
- migration `014_reference_media_kind_lifecycle.sql` aligns the DB lifecycle with those semantics;
- invalid non-null media-kind values remain rejected.

Regression proof:

- `visual_planned + technical_reference + NULL` -> PASS;
- `visual_ready + technical_reference + NULL` -> expected check violation;
- `visual_ready + technical_reference + photo` -> PASS;
- WF04 Code compile PASS `14`;
- runtime planner regression PASS;
- assignment/perceptual assignment PASS;
- representation relevance PASS;
- download dedupe PASS;
- rank query contract PASS;
- visual quality/discovery regressions PASS.

Selective commit:

- `b83bf6d48f1df259c7c6fa0136748ca10d13f1af`
- `fix: align reference media kind lifecycle`

WF02 retrieval work remained excluded.

Rollback snapshot before this bounded deploy:

`/opt/ai-short-form-content-factory/rollback/20260902T181813Z-pre-reference-media-kind-lifecycle`

Production deploy proof:

- migration 014 is live;
- n8n readiness HTTP 200;
- WF04 active with 27 nodes;
- expected/live WF04 core SHA-256 both equal `66edb387d6e0ea6ae8a9961f40c8b06e3a5ef376ea19441375beaa0c5790ef75`;
- exactly three persistent services remained running and PostgreSQL healthy.

## 2026-09-02 — Fresh production induction machine PASS after visual rewrite

Fresh job:

`2c182ff8-ea9f-4ddf-a417-b49f796d23f5`

Topic: `How does induction heating work? / en / 15`.

This job is a MACHINE PASS only. Human-visible product acceptance remains pending.

Upstream/narration proof:

- deterministic evidence compiler produced evidence-backed narration;
- duration preflight predicted `14.358 s` and marked the candidate safe for the single-TTS boundary;
- execution `9926` run data was decoded from n8n `execution_data`;
- `Prepare Continuous Voiceover` ran exactly once;
- `Generate Natural Voiceover` ran exactly once and succeeded (`executionTimeMs = 1084`);
- `Require Natural Voiceover` ran exactly once;
- persisted provider `microsoft_edge_readaloud`, model `edge_neural`, voice `en-US-AndrewNeural`;
- measured voice duration `13.944 s` passed the unchanged 15-second ±10% gate;
- six timed beats were created.

Live WF03 proof:

- live published workflow `UHxvCZNqaLb1RKMM` was exported from n8n rather than trusting the stale filesystem export;
- it is active with 15 nodes;
- Gemini is absent from the live workflow;
- there is one synthesis HTTP node, `Generate Natural Voiceover`, using the media-worker Edge route;
- prepared request carries `max_automatic_synthesis_count: 1`.

Visual pre-render proof:

- 6 beats;
- 6 selected assets;
- 6 perceptual clusters;
- required clusters 5;
- adjacent duplicate clusters `0`;
- max visual-cluster duration share `0.1813`;
- durable `visual_quality.pre_render_pass = true`.

Selected assets were six different induction-related Wikimedia visuals:

1. `File:Induction heating of bar.jpg`;
2. `File:Stirling radioisotope generator head testing.jpg`;
3. `File:Induction heating apparatus 1927.jpg`;
4. `File:Silicon grown by Czochralski process 1956 closeup.jpg`;
5. `File:Northup induction furnace.jpg`;
6. `File:Induction heater.jpg`.

Render/post-render proof:

- final path `jobs/2c182ff8-ea9f-4ddf-a417-b49f796d23f5/render/final.mp4`;
- job reached `review_ready/review` with no `last_error`;
- persisted rendered clusters `[[1],[2],[3],[4],[5],[6]]`;
- rendered visual state count `6`, required `5`;
- adjacent rendered duplicate count `0`;
- max cluster duration share `0.1813`;
- independent midpoint-frame hashing at 1.1665, 3.395, 5.721, 8.145, 10.4975 and 12.817 seconds also produced six separate clusters;
- minimum pairwise Hamming distance between sampled states was far above the threshold 18, so the former two-state failure did not recur.

ffprobe proof:

- duration `14.000000 s`;
- H.264 video;
- 1080x1920;
- yuv420p;
- 30 fps;
- AAC audio;
- 48 kHz stereo;
- file size `3,767,544` bytes.

Runtime after proof:

- exactly `media-worker`, `n8n`, `postgres` are running;
- PostgreSQL is healthy;
- rebuild HEAD is `b83bf6d48f1df259c7c6fa0136748ca10d13f1af`;
- only the separate WF02 retrieval work remains dirty: modified `n8n/workflows/WF02-plan-script-and-scenes.json` and untracked `tests/wf02_fact_search_query_regression.mjs`.

Human gate:

- DO NOT mark this job as M8 induction PASS yet;
- exact fresh video must be viewed by the user in Studio;
- if accepted, M8 #2 becomes PASS and testing continues on materially different topics/languages;
- if rejected, progression stops and the visible defect is fixed systemically before generating further M8 videos.

## 2026-09-02 — Fresh induction human-visible PASS

Exact accepted job:

`2c182ff8-ea9f-4ddf-a417-b49f796d23f5`

Human acceptance:

- the user watched the exact fresh post-fix induction video in Studio;
- the user responded `мне нравится`;
- this is explicit acceptance of the visible product result after the visual-quality-v2 rewrite and reference-media lifecycle correction.

Decision:

- M8 #2 induction is now PASS, not merely machine PASS;
- accepted M8 count is `2/10`;
- the old two-state induction job remains permanently invalidated and is not reused as proof;
- the intermediate `mixed` lifecycle failure remains part of engineering history and is not erased by the later PASS.

Next independent technical task:

- finish the already-separated WF02 native-Wikipedia retrieval-query correction exposed by Polish popcorn;
- keep it in its own commit/deploy;
- after a fresh VPS/runtime check, regression-test and boundedly deploy WF02 only;
- then start a completely fresh Polish popcorn job as M8 #3 and require machine + human review.

Operational note:

- immediately after the human acceptance, fresh SentinelX runtime inspection was attempted twice;
- both attempts returned `agent_offline` because the SentinelX hub had restarted;
- no production mutation was performed while runtime verification was unavailable.