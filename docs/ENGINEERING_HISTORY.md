# Engineering History — Rebuild

Chronological durable record for material changes, failures, verified root causes, regressions, deploys and rollback facts. `docs/CURRENT_STATE.md` remains the operational source of truth.

This file was compacted again on 2026-09-03. The compaction preserves the material failures, decisions, commits, rollback locations, deployment facts, diagnostic mistakes and acceptance evidence needed to resume work without relying on chat memory. Exact code history remains recoverable from the listed commits and rollback snapshots.

## 2026-09-02 — Previous induction machine PASS invalidated by human-visible failure

Job `13f64c50-8dd5-47e4-a88f-1411d258e7c4` reached `review_ready`, but human inspection showed only two effective visual states. Root cause: acceptance counted scene/file presence rather than video-level perceptual sequence quality. The old machine PASS is permanently invalidated.

## 2026-09-02 — Visual-quality-v2 rewrite

Required visual path became:

`timed beat + evidence -> deterministic search intents -> multi-source discovery -> metadata/provenance eligibility -> local SigLIP ranking + perceptual identity -> global assignment -> sequence quality gate -> persist -> render -> post-render pixel-state gate -> review_ready`

Six-beat contract: every beat truth-eligible; at least five perceptual clusters; zero adjacent duplicates; no cluster over `0.34` duration share; non-finite metrics fail closed; actual rendered midpoint frames must independently satisfy the required state count.

Material fixes included perceptual hashing, global assignment, WF05 independent quality validation, post-render pixel clustering, deterministic still-image motion, provider environment wiring, and removal of file-ID-as-visual-identity semantics.

Cross-topic dry-runs without threshold weakening: EN induction 6 clusters/max `0.1813`; PL combustion engine 5/max `0.3333`; RU refrigerator 6/max `0.1667`; UK volcano 6/max `0.1667`.

Diagnostic compile-harness mistake where top-level-array workflow exports were treated as objects was invalidated; zero-count Code-node output is never accepted as PASS.

## 2026-09-02 — Visual rewrite committed/deployed

Commit `f7c4096503c9620910b387129a5a06cce4d26d42` — `redesign: enforce perceptual visual diversity`.

Rollback: `/opt/ai-short-form-content-factory/rollback/20260902T175543Z-pre-visual-quality-v2`.

Migration 013 live; media-worker recreated; local SigLIP health PASS; Wikimedia/Pexels/Pixabay discovery; valid perceptual hashes; WF04/WF05 published; live core equality PASS; exactly three services and PostgreSQL healthy.

## 2026-09-02 — Reference-media lifecycle failure/fix

Fresh job `1afc307d-aaac-4eed-8387-b05e1b6721eb`, WF04 execution `9902`, failed after its single Edge synthesis because planner persisted fake `reference_media_kind = mixed` and violated DB constraint.

Systemic correction: `visual_planned + technical_reference` keeps NULL; `visual_ready` requires actual `photo|diagram|animation`; migration 014 aligns DB lifecycle.

Commit `b83bf6d48f1df259c7c6fa0136748ca10d13f1af` — `fix: align reference media kind lifecycle`.
Rollback: `/opt/ai-short-form-content-factory/rollback/20260902T181813Z-pre-reference-media-kind-lifecycle`.

Production proof: migration 014 live; WF04 core SHA equality `66edb387d6e0ea6ae8a9961f40c8b06e3a5ef376ea19441375beaa0c5790ef75`; n8n ready; three services; PostgreSQL healthy.

## 2026-09-02 — Fresh induction MACHINE + HUMAN PASS

Accepted job `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`, `How does induction heating work? / en / 15`.

Machine proof: `review_ready`; preflight `14.358 s`; execution `9926` had exactly one successful Edge synthesis; measured voice `13.944 s`; six beats; 6/6 perceptual clusters, required 5; adjacent 0; max share `0.1813`; post-render six states; ffprobe 14.000 s H.264 1080x1920 30fps + AAC 48kHz stereo. Live WF03 contained no Gemini and exactly one Edge synthesis path.

User watched the exact fresh video and replied `мне нравится`; M8 #2 PASS. Old two-state induction remains invalidated.

## 2026-09-02 — Polish popcorn and RU-topic/UK-output WF02 failures

- `Dlaczego popcorn pęka podczas podgrzewania? / pl / 15` failed because native Wikipedia query was over-constrained and returned no full-text pages.
- job `85fcc63b-b89b-40d0-b253-6383b715f105`, topic `как работает индукционная плита`, requested `uk`, 60 s, failed at `script` with `Wikipedia native fact search returned no full-text pages` before voice/visual/render.
- runtime diagnosis confirmed the old live path issued Russian subject text against requested Ukrainian Wikipedia without multilingual resolution. This is one systemic retrieval class, not a topic-specific cooktop defect.

## 2026-09-03 — WF02 multilingual retrieval/explanation correction regression-proven

Systemic retrieval contract:

- preserve up to 10 full meaningful `fact_search_tokens` for relevance/evidence validation;
- discovery query uses at most first two meaningful subject-leading tokens;
- bounded probes exactly EN/PL/RU/UK, requested language first;
- one Wikipedia request per probe; old `retryOnFail=2` removed;
- requests include `langlinks` to target language;
- failed probes contribute no pages; complete lack of title-supported pages fails closed;
- cross-language source requires official Wikipedia language link into target language;
- no topic mapping, generative translation, retry loop, provider cascade, bypass or threshold weakening.

Evidence/narration correction:

- direct/compositional source coverage with full factual tokens preserved;
- `language_link` provenance not penalized as search-rank 9999;
- how/why mechanism/principle/construction evidence prioritized;
- Unicode-safe EN/PL/RU/UK section classification and wiki list-marker stripping;
- multiple strong explanatory passages allowed;
- deterministic extractive compiler supports provenance-preserving trailing result/purpose-clause reduction for long mechanism sentences;
- every segment remains a token subsequence of source evidence;
- duration operating bands unchanged;
- among already-safe explanation candidates, stronger causal/mechanism content wins before weaker duration-score ties.

Real Wikipedia final proof:

- RU-topic `как работает индукционная плита / uk / 60` -> `Індукційна плита`, predicted `60.106 s`, safe;
- UK refrigerator 60 s -> `59.975 s`, safe;
- PL popcorn 15 s -> `15.079 s`, safe;
- EN induction 15 s -> `14.939 s`, safe and direct alternating-magnetic-field mechanism selected.

WF02 tests: seven new regressions PASS; Code compile 8/8. Legacy proof: staged pipeline PASS; retained duration audit 150/40 safe/0 false-safe; CASE1 staged provenance PASS; CASE1 visual eligibility PASS; unchanged duration operating bands PASS.

Diagnostic harness mistake: first CASE1 visual invocation passed `-e never` as Node input and produced `ReferenceError`; invalid harness result. Correct invocation passed.

Semantic diff preserved 17 nodes/settings/meta/node names; functional changes limited to `Prepare Fact Searches`, `Search Wikipedia Facts`, `Prepare Full Fact Sources`, `Build Fact Brief`, `Build Deterministic Narration`. Search node no longer retries; bounded aggregation ends in fail-closed source validation.

## 2026-09-03 — WF02 fix selectively committed and deployed

Commit `e4e856093fa237dab9daaa56dcf443c3b6155f93` — `fix: make factual retrieval multilingual and explanation-aware`.

Commit contains exactly WF02 plus seven WF02 regression files; staging/check passed and worktree was clean.

Rollback snapshot: `/opt/ai-short-form-content-factory/rollback/20260903T055250Z-pre-wf02-multilingual`.

WF02-only deploy proof:

- exact committed file copied to production;
- workflow `TJfA4ZYUEKSTad6k` imported/published;
- n8n restarted exactly once;
- health HTTP 200;
- expected/live core SHA both `0f5893ffba59b23d181c363b26b991450e3fc016a52016e1ec686797dbfe23c1`;
- live active with 17 nodes, no retry/maxTries;
- three services remain running, PostgreSQL healthy;
- rebuild HEAD `e4e856093fa237dab9daaa56dcf443c3b6155f93`, worktree clean.

## 2026-09-03 — Fresh cross-language UK/60 production job reached visuals and failed sequence assignment

Fresh job was created through the real WF01 intake route `/webhook/jobs`, equivalent to Studio `POST /api/jobs` after Caddy rewrite:

- job `4372be34-c417-415f-92f6-63481b3b5686`;
- topic `как работает индукционная плита`;
- output language `uk`;
- target duration `60`;
- intake returned HTTP 201.

Observed production state progression:

- job reached `processing|visuals`, proving the prior WF02 script-retrieval blocker was passed in production;
- after about 100 seconds it failed at `visuals`;
- exact error: `perceptually unique truth-eligible assignment 11/12 [line 15]`;
- final state `failed|visuals`;
- runtime remained exactly `media-worker`, `n8n`, `postgres`; PostgreSQL healthy; n8n health 200.

This job must never be retried/reused because it already passed upstream voice processing and may have consumed the one allowed Edge synthesis. The failure is currently recorded as an unresolved general 60-second visual-assignment defect; root cause is not yet claimed. M8 progression remains stopped until exact WF04 execution/scene/candidate evidence identifies and fixes the systemic cause without weakening visual gates.
