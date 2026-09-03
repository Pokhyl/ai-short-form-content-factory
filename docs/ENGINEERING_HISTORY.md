# Engineering History — Rebuild

Chronological durable record for material changes, failures, verified root causes, regressions, deploys and rollback facts. `docs/CURRENT_STATE.md` remains the operational source of truth.

This file was compacted again on 2026-09-03. The compaction preserves the material failures, decisions, commits, rollback locations, deployment facts, diagnostic mistakes and acceptance evidence needed to resume work without relying on chat memory. Exact code history remains recoverable from the listed commits and rollback snapshots.

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

## 2026-09-02 — Visual-quality-v2 rewrite

Required visual path:

`timed beat + evidence -> deterministic search intents -> multi-source candidate discovery -> metadata/provenance eligibility -> local SigLIP ranking + perceptual identity -> global sequence assignment -> sequence quality gate -> persist -> render -> post-render visual-state gate -> review_ready`

Material implementation:

- `services/media-worker/src/visual-discovery.mjs` provides bounded canonical-article/Wikimedia/Pixabay/optional-Pexels discovery;
- `services/media-worker/src/visual-quality.mjs` provides fail-closed perceptual sequence quality;
- `/visual/rank` returns a 256-bit perceptual preview hash;
- WF04 assigns globally by perceptual clusters rather than file IDs;
- WF05 independently validates persisted visual quality before render;
- media-worker independently validates actual rendered midpoint-frame diversity after render;
- still photos receive deterministic subtle motion while factual diagrams remain stable/readable;
- migration `013_visual_quality_gate.sql` adds durable `jobs.visual_quality`.

Visual-quality-v2 contract for six beats:

- all beats require truth-eligible selected assets;
- at least five perceptual clusters;
- zero adjacent perceptual duplicates;
- no cluster above `0.34` of total beat duration;
- missing/NaN/non-finite metrics fail closed;
- post-render pixels must independently satisfy the required state count.

Permanent negative fixture: old induction pattern with six scene rows but two effective clusters, four adjacent repeats and about 68% duration share for one state -> MUST FAIL.

## 2026-09-02 — Visual rewrite diagnostic and configuration corrections

Diagnostic compile-harness mistake:

- n8n workflow exports were initially treated as objects although rebuild exports are top-level arrays;
- this produced meaningless zero-count Code-node output;
- harness was corrected to unwrap/validate workflow shape and zero-count compilation is never accepted as PASS.

WF04/media-worker mismatch:

- WF04 had moved to `visual_cluster_key` while media-worker pre-render still counted `asset_key`;
- corrected so perceptual cluster identity is authoritative and file identity is audit/download identity only.

Provider environment defect:

- production `.env` had Pixabay/Pexels credentials but media-worker compose did not receive them;
- compose now passes `PIXABAY_API_KEY` and `PEXELS_API_KEY` without committing values;
- Pexels remains optional and can never be required for success.

Cross-topic pre-deploy dry-runs all passed without threshold weakening:

- EN induction: 6/6 perceptual clusters, adjacent 0, max share `0.1813`;
- PL combustion engine: 5 clusters for 6 beats, adjacent 0, max share `0.3333`;
- RU refrigerator: 6 clusters, adjacent 0, max share `0.1667`;
- UK volcano: 6 clusters, adjacent 0, max share `0.1667`.

Pre-commit proof included visual discovery/quality/assignment/relevance/dedupe/rank-query regressions, WF04 Code compile 14, WF05 Code compile 8, retained staged corpus 150 rows with 40 safe and zero false-safe, CASE1 staged/visual PASS and migration-013 transaction/rollback PASS.

## 2026-09-02 — Visual rewrite commit and production deployment

Commit:

- `f7c4096503c9620910b387129a5a06cce4d26d42`
- `redesign: enforce perceptual visual diversity`

Rollback snapshot:

`/opt/ai-short-form-content-factory/rollback/20260902T175543Z-pre-visual-quality-v2`

Deployment proof:

- migration 013 applied;
- media-worker recreated with provider env present;
- `/health` PASS with local SigLIP;
- live discovery returned Wikimedia/Pexels/Pixabay candidates;
- live rank returned valid 64-hex perceptual hashes;
- WF04 `M6VisualSourcing1` and WF05 `M7VideoRender1` imported/published;
- one n8n restart after both publications;
- live workflow core equality PASS;
- exactly three persistent services remained and PostgreSQL healthy.

## 2026-09-02 — Fresh induction exposed reference-media lifecycle mismatch

Fresh job: `1afc307d-aaac-4eed-8387-b05e1b6721eb`.
WF04 execution: `9902`.

Upstream had already consumed the one allowed Edge synthesis and produced six timed beats. WF04 then failed with:

`new row for relation "scenes" violates check constraint "scenes_reference_media_kind_check"`

Verified root cause:

- planner persisted fake `reference_media_kind = mixed` to mean “not selected yet”;
- DB correctly only recognizes actual non-null `diagram|animation|photo`;
- staged lifecycle did not allow technical reference media kind to remain unset while `visual_planned`.

The failed job was not reused because its one automatic Edge synthesis had already occurred.

## 2026-09-02 — Reference-media lifecycle fixed

Correction:

- `visual_planned + technical_reference` keeps `reference_media_kind = NULL`;
- after actual asset selection, `visual_ready` requires concrete `photo|diagram|animation`;
- migration `014_reference_media_kind_lifecycle.sql` aligns DB lifecycle;
- invalid non-null kinds remain rejected.

Commit:

- `b83bf6d48f1df259c7c6fa0136748ca10d13f1af`
- `fix: align reference media kind lifecycle`

Rollback snapshot:

`/opt/ai-short-form-content-factory/rollback/20260902T181813Z-pre-reference-media-kind-lifecycle`

Deployment proof:

- migration 014 live;
- WF04 active with 27 nodes;
- expected/live WF04 core SHA both `66edb387d6e0ea6ae8a9961f40c8b06e3a5ef376ea19441375beaa0c5790ef75`;
- n8n ready;
- exactly three persistent services and PostgreSQL healthy.

## 2026-09-02 — Fresh post-fix induction MACHINE + HUMAN PASS

Accepted job: `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`.
Topic: `How does induction heating work? / en / 15`.

Machine proof:

- `review_ready/review`, no `last_error`;
- duration preflight `14.358 s`;
- n8n execution `9926`: `Generate Natural Voiceover` ran exactly once and succeeded;
- voice `en-US-AndrewNeural`;
- measured voice duration `13.944 s`;
- six timed beats;
- 6 selected assets / 6 perceptual clusters, required 5;
- adjacent duplicate clusters 0;
- max cluster share `0.1813`;
- post-render rendered-state count 6, required 5;
- independent midpoint-frame hashing also produced six states;
- ffprobe: 14.000 s, H.264 1080x1920 yuv420p 30 fps + AAC 48 kHz stereo.

Live WF03 was exported directly from n8n and contained no Gemini path; it had one Edge synthesis node and `max_automatic_synthesis_count: 1`.

Human proof:

- user watched this exact fresh video and responded `мне нравится`;
- M8 #2 induction is PASS;
- accepted M8 count became `2/10`.

Old two-state induction remains permanently invalidated.

## 2026-09-02 — Polish popcorn and RU-topic/UK-output WF02 failures

Original retrieval regression:

- `Dlaczego popcorn pęka podczas podgrzewania? / pl / 15` failed because native Wikipedia search used an over-constrained query and returned no full-text pages.

User-run cross-language failure:

- job `85fcc63b-b89b-40d0-b253-6383b715f105`;
- topic `как работает индукционная плита`;
- requested language `uk`;
- duration 60 s;
- failed at `script` with `Wikipedia native fact search returned no full-text pages` before voice/visual/render.

Subsequent runtime diagnosis confirmed the live path was issuing the Russian subject query against the requested Ukrainian Wikipedia without a multilingual resolution stage. This belongs to the same systemic retrieval class, not a topic-specific induction-cooktop defect.

## 2026-09-03 — WF02 multilingual factual retrieval and explanation quality correction regression-proven locally

Scope remains a separate WF02 change; production was not mutated during development/regression.

Systemic retrieval correction:

- topic is normalized once and keeps up to 10 full meaningful `fact_search_tokens` for downstream relevance/evidence checks;
- discovery query is bounded to the first two meaningful subject-leading tokens;
- supported factual probe languages are bounded to `en`, `pl`, `ru`, `uk`, with requested output language first;
- each probe performs one Wikipedia request only; old `retryOnFail=2` was removed;
- request also asks for `langlinks` to the requested output language;
- one probe failure contributes no pages, while total absence of title-supported pages fails closed;
- if the strongest page is found in another supported language, WF02 requires an official Wikipedia `langlink` into the requested language and then fetches the target-language canonical page;
- no topic mapping, generative translation, retry loop, provider cascade, acceptance bypass or threshold weakening was introduced.

Evidence/source correction:

- native/source title matching supports direct and compositional coverage while full factual tokens remain available for validation;
- `language_link` provenance is not penalized as if it had search rank 9999;
- explanatory mechanism/principle/construction sections are prioritized ahead of history/culture/advantages for how/why intents;
- Unicode-safe EN/PL/RU/UK section classification is used;
- wiki list markers are stripped from evidence prose;
- bounded evidence packets can draw from multiple strong explanatory passages rather than locking to the first three sentences of one passage.

Deterministic extractive narration correction:

- no generative rewriting was added;
- long source sentences may use provenance-preserving, grammar-checked extractive reductions such as dropping a trailing result clause and then a trailing infinitive purpose clause;
- every emitted segment still has to be a token subsequence of its source evidence;
- duration operating bands and one-Edge boundary are unchanged;
- among candidates that already satisfy the unchanged duration gate, explanation candidates now rank stronger causal/mechanism content ahead of weaker ties on compiler duration score.

Important real-Wikipedia proof after the final ranking/reducer changes:

- `как работает индукционная плита / uk / 60` -> canonical `Індукційна плита`, cross-language resolution PASS, predicted `60.106 s`, safe;
- `Як працює холодильник? / uk / 60` -> canonical `Холодильник`, predicted `59.975 s`, safe;
- `Dlaczego popcorn pęka podczas podgrzewania? / pl / 15` -> canonical `Popcorn`, predicted `15.079 s`, safe;
- `How does induction heating work? / en / 15` -> canonical `Induction heating`, predicted `14.939 s`, safe and now includes the direct mechanism span `induction heating systems work by applying an alternating magnetic field...` rather than the previously selected weak comparison/frequency text.

WF02 regression proof:

- `WF02_FACT_SEARCH_QUERY_PASS`;
- `WF02_MULTILINGUAL_SOURCE_RESOLUTION_PASS`;
- `WF02_CROSS_LANGUAGE_CONTRACT_PASS`;
- `WF02_EXPLANATION_EVIDENCE_PRIORITY_PASS`;
- `WF02_EXPLANATION_COMPILER_FLEXIBILITY_PASS`;
- `WF02_LONG_MECHANISM_SPAN_PASS`;
- `WF02_EXPLANATION_CANDIDATE_RANKING_PASS`;
- WF02 Code compile PASS `8/8`.

Legacy/core regression proof after the WF02 changes:

- staged pipeline regression PASS on retained corpus;
- duration retained audit: 150 rows, 40 safe, zero false-safe;
- CASE1 staged provenance PASS;
- CASE1 deterministic visual eligibility PASS;
- unchanged duration operating bands PASS for retained zipper/induction cases;
- runtime before/after tests remained exactly `media-worker`, `n8n`, `postgres`, PostgreSQL healthy.

Diagnostic mistake recorded:

- an initial CASE1 visual regression invocation accidentally passed `-e never` as a Node argument, producing `ReferenceError: never is not defined`;
- this was a harness invocation error, not a project failure;
- the test was rerun with the correct environment variables and passed `CASE1_DETERMINISTIC_VISUAL_ELIGIBILITY_PASS`.

Semantic workflow diff proof:

- node count remains 17 and node names/settings/meta are preserved;
- changed functional nodes are `Prepare Fact Searches`, `Search Wikipedia Facts`, `Prepare Full Fact Sources`, `Build Fact Brief`, `Build Deterministic Narration`;
- `Search Wikipedia Facts` no longer retries and uses bounded per-language probe input;
- its former error branch was removed because per-probe HTTP errors are intentionally aggregated as empty probe results, while `Prepare Full Fact Sources` fails closed if no title-supported page survives.

Current state at this history checkpoint:

- WF02 changes are regression-proven locally but NOT YET deployed;
- rebuild HEAD is still `b83bf6d48f1df259c7c6fa0136748ca10d13f1af` before the pending WF02 selective commit;
- production remains on the previous published WF02;
- exactly three persistent services are running and PostgreSQL is healthy;
- next action: selective WF02+tests commit, bounded rollback snapshot, WF02-only deployment/live equality, then a completely fresh production cross-language UK/60 job and Polish popcorn M8 #3 proof.
