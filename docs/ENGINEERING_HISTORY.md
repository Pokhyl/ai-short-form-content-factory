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

- bounded canonical-article/Wikimedia/Pixabay/optional-Pexels discovery;
- fail-closed perceptual sequence quality;
- `/visual/rank` returns a 256-bit perceptual preview hash;
- WF04 assigns globally by perceptual clusters rather than file IDs;
- WF05 independently validates persisted visual quality before render;
- media-worker independently validates actual rendered midpoint-frame diversity;
- still photos receive deterministic subtle motion while factual diagrams remain stable/readable;
- migration `013_visual_quality_gate.sql` adds durable `jobs.visual_quality`.

Six-beat contract: all beats truth-eligible; at least five perceptual clusters; zero adjacent duplicates; no cluster above `0.34` duration share; missing/NaN fails closed; post-render pixels independently meet required state count.

Permanent negative fixture: old induction with six rows but two effective states, four adjacent repeats and about 68% share -> MUST FAIL.

## 2026-09-02 — Visual rewrite diagnostic/configuration corrections

- diagnostic compile harness initially treated top-level-array workflow exports as objects; zero-count Code-node output was invalidated and harness fixed;
- WF04/media-worker `visual_cluster_key` vs `asset_key` mismatch corrected so perceptual cluster identity is authoritative;
- media-worker compose provider env wiring corrected for Pixabay/Pexels without committing secret values; Pexels remains optional.

Cross-topic dry-runs passed without threshold weakening: EN induction 6 clusters/max `0.1813`; PL combustion engine 5 clusters/max `0.3333`; RU refrigerator 6/max `0.1667`; UK volcano 6/max `0.1667`.

Pre-commit proof included visual discovery/quality/assignment/relevance/dedupe/rank-query regressions, WF04 compile 14, WF05 compile 8, retained staged corpus 150 rows/40 safe/0 false-safe, CASE1 staged/visual PASS and migration-013 rollback PASS.

## 2026-09-02 — Visual rewrite committed/deployed

Commit `f7c4096503c9620910b387129a5a06cce4d26d42` — `redesign: enforce perceptual visual diversity`.

Rollback: `/opt/ai-short-form-content-factory/rollback/20260902T175543Z-pre-visual-quality-v2`.

Deployment proof: migration 013 live; media-worker recreated; local SigLIP health PASS; Wikimedia/Pexels/Pixabay discovery; valid perceptual hashes; WF04/WF05 published; live core equality PASS; exactly three services and PostgreSQL healthy.

## 2026-09-02 — Reference-media lifecycle production failure and fix

Failed fresh job `1afc307d-aaac-4eed-8387-b05e1b6721eb`, WF04 execution `9902`, after its single Edge synthesis. Exact error: `scenes_reference_media_kind_check` because planner persisted fake `reference_media_kind = mixed`.

Systemic correction: `visual_planned + technical_reference` keeps NULL; `visual_ready` requires actual `photo|diagram|animation`; migration 014 aligns DB lifecycle; invalid non-null kinds remain rejected.

Commit `b83bf6d48f1df259c7c6fa0136748ca10d13f1af` — `fix: align reference media kind lifecycle`.
Rollback: `/opt/ai-short-form-content-factory/rollback/20260902T181813Z-pre-reference-media-kind-lifecycle`.

Production proof: migration 014 live; WF04 core SHA equality `66edb387d6e0ea6ae8a9961f40c8b06e3a5ef376ea19441375beaa0c5790ef75`; n8n ready; three services; PostgreSQL healthy.

## 2026-09-02 — Fresh post-fix induction MACHINE + HUMAN PASS

Accepted job `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`, `How does induction heating work? / en / 15`.

Machine proof: `review_ready`; preflight `14.358 s`; execution `9926` had exactly one successful `Generate Natural Voiceover`; measured Edge voice `13.944 s`; six beats; 6/6 perceptual clusters, required 5; adjacent 0; max share `0.1813`; post-render six states; ffprobe 14.000 s H.264 1080x1920 30fps + AAC 48kHz stereo. Live WF03 contained no Gemini and exactly one Edge synthesis path with max automatic synthesis count 1.

User watched the exact fresh video and replied `мне нравится`; M8 #2 PASS; accepted count became `2/10`. Old two-state induction remains invalidated.

## 2026-09-02 — Polish popcorn and RU-topic/UK-output WF02 failures

- `Dlaczego popcorn pęka podczas podgrzewania? / pl / 15` failed because native Wikipedia search query was over-constrained and returned no full-text pages.
- job `85fcc63b-b89b-40d0-b253-6383b715f105`, topic `как работает индукционная плита`, requested `uk`, 60 s, failed at `script` with `Wikipedia native fact search returned no full-text pages` before voice/visual/render.
- runtime diagnosis confirmed the live path issued Russian subject text against requested Ukrainian Wikipedia without multilingual resolution; this is one systemic retrieval class, not an induction-cooktop special case.

## 2026-09-03 — WF02 multilingual retrieval/explanation correction regression-proven

Systemic retrieval correction:

- preserves up to 10 full meaningful `fact_search_tokens` for relevance/evidence validation;
- discovery query uses at most first two meaningful subject-leading tokens;
- bounded probes are exactly EN/PL/RU/UK with requested language first;
- one Wikipedia request per probe; old `retryOnFail=2` removed;
- requests include `langlinks` to target language;
- a failed probe contributes no pages; complete lack of title-supported pages fails closed;
- cross-language source requires official Wikipedia language link into target language;
- no topic mapping, generative translation, retry loop, provider cascade, bypass or threshold weakening.

Evidence/narration correction:

- direct/compositional source coverage with full factual tokens preserved;
- `language_link` provenance is not penalized as search-rank 9999;
- how/why mechanism/principle/construction evidence prioritized ahead of history/culture/advantages;
- Unicode-safe EN/PL/RU/UK section classification and wiki list-marker stripping;
- explanation packet can use multiple strong passages;
- deterministic extractive compiler gained provenance-preserving trailing result/purpose-clause reduction for long mechanism sentences;
- every segment remains a token subsequence of source evidence;
- duration operating bands unchanged;
- among already-safe explanation candidates, stronger causal/mechanism content wins before weaker duration-score ties.

Real Wikipedia final proof:

- `как работает индукционная плита / uk / 60` -> `Індукційна плита`, cross-language PASS, predicted `60.106 s`;
- `Як працює холодильник? / uk / 60` -> `Холодильник`, `59.975 s`;
- `Dlaczego popcorn pęka podczas podgrzewania? / pl / 15` -> `Popcorn`, `15.079 s`;
- `How does induction heating work? / en / 15` -> `Induction heating`, `14.939 s`, now selecting direct alternating-magnetic-field mechanism instead of weak comparison/frequency text.

WF02 regression proof: fact-search-query PASS; multilingual-source-resolution PASS; cross-language-contract PASS; explanation-evidence-priority PASS; compiler-flexibility PASS; long-mechanism-span PASS; explanation-candidate-ranking PASS; Code compile 8/8.

Legacy/core proof: staged pipeline PASS; retained duration audit 150 rows/40 safe/0 false-safe; CASE1 staged provenance PASS; CASE1 deterministic visual eligibility PASS; unchanged duration operating bands PASS; runtime stayed exactly media-worker+n8n+postgres with PostgreSQL healthy.

Diagnostic harness mistake: first CASE1 visual invocation passed `-e never` as a Node argument, causing `ReferenceError`; this was not a project FAIL. Correct invocation passed `CASE1_DETERMINISTIC_VISUAL_ELIGIBILITY_PASS`.

Semantic diff: 17 nodes preserved; settings/meta/node names preserved; functional changes limited to `Prepare Fact Searches`, `Search Wikipedia Facts`, `Prepare Full Fact Sources`, `Build Fact Brief`, `Build Deterministic Narration`; Search Wikipedia Facts no longer retries and its former error branch is replaced by bounded aggregation with final fail-closed source validation.

## 2026-09-03 — WF02 fix selectively committed

Selective local commit:

- `e4e856093fa237dab9daaa56dcf443c3b6155f93`
- `fix: make factual retrieval multilingual and explanation-aware`

Commit contains exactly WF02 plus seven WF02 regression files. `git diff --cached --check` passed; no unrelated files were staged; worktree is clean after commit.

Production at this checkpoint is still on the previous published WF02. Next action is a bounded live-WF02 rollback snapshot, WF02-only deploy/live equality proof, then completely fresh production cross-language UK/60 and Polish popcorn M8 #3 jobs.
