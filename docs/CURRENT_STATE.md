# Current Project State — Rebuild

Last updated: 2026-09-03

This file is authoritative for branch `rebuild/simple-pipeline`. Repository/runtime state overrides chat memory. Detailed chronological proof is in `docs/ENGINEERING_HISTORY.md`.

## Mandatory protocol

Before EVERY technical response, diagnosis, recommendation, code/config change, deployment, or test:

1. Read `docs/PERMANENT_PROJECT_RULES.md` from GitHub.
2. Read this file from GitHub branch `rebuild/simple-pipeline`.
3. Architecture change: also read `docs/ARCHITECTURE.md`.
4. Milestone/acceptance/gate change: also read `docs/ROADMAP.md` and `docs/PROCESS_GATE.md`.
5. Upstream/provider change: also read `docs/UPSTREAM_DECISION.md`.
6. Inspect fresh VPS/runtime state before acting.
7. Before starting a new approach, read `docs/ENGINEERING_HISTORY.md` so rejected/broken approaches are not repeated.

## Hard invariants

- exactly three persistent services: `n8n`, `postgres`, `media-worker`;
- external API cost per generated video: `0 PLN`;
- no Gemini or other quota-limited hosted semantic AI in the required critical path;
- no general local generative LLM in the required critical path;
- no quota waits/retries, extra keys/accounts, paid fallback, topic-specific patches, acceptance bypasses, threshold weakening, or repeated fitting TTS;
- automatic production performs exactly ONE Edge synthesis per job.

Critical path:

`topic -> factual evidence -> deterministic evidence-backed narration -> local duration preflight -> one natural Edge voice -> timed beats -> deterministic truthful visual eligibility -> local SigLIP ranking + perceptual identity -> global sequence assignment -> pre-render visual gate -> render -> post-render visual-state gate -> human review`

## Runtime — current verified state

Production: `/opt/ai-short-form-content-factory`
Rebuild worktree: `/opt/ai-short-form-content-factory-rebuild`

Freshly verified after WF02 deployment:

- exactly `media-worker`, `n8n`, `postgres` running;
- PostgreSQL healthy;
- n8n `/healthz` HTTP 200;
- rebuild HEAD `e4e856093fa237dab9daaa56dcf443c3b6155f93`;
- rebuild worktree clean.

Published workflows:

- WF02 `TJfA4ZYUEKSTad6k` — multilingual deterministic factual retrieval + evidence-backed narration;
- WF03 `UHxvCZNqaLb1RKMM` — exactly one natural Edge voice + timed beats;
- WF04 `M6VisualSourcing1` — visual-quality-v2 sourcing/assignment;
- WF05 `M7VideoRender1` — visual-quality-v2 render acceptance;
- WF06 `R8ReviewApi1` — review API.

IMPORTANT: live n8n exports are authoritative for published workflow behavior when filesystem exports are stale.

## Deployed commits / migrations / rollback

Visual rewrite:

- `f7c4096503c9620910b387129a5a06cce4d26d42` — `redesign: enforce perceptual visual diversity`;
- migration `013_visual_quality_gate.sql` live;
- rollback `/opt/ai-short-form-content-factory/rollback/20260902T175543Z-pre-visual-quality-v2`.

Reference-media lifecycle:

- `b83bf6d48f1df259c7c6fa0136748ca10d13f1af` — `fix: align reference media kind lifecycle`;
- migration `014_reference_media_kind_lifecycle.sql` live;
- rollback `/opt/ai-short-form-content-factory/rollback/20260902T181813Z-pre-reference-media-kind-lifecycle`.

WF02 multilingual factual retrieval:

- `e4e856093fa237dab9daaa56dcf443c3b6155f93` — `fix: make factual retrieval multilingual and explanation-aware`;
- rollback `/opt/ai-short-form-content-factory/rollback/20260903T055250Z-pre-wf02-multilingual`;
- WF02 imported/published only; n8n restarted exactly once afterward;
- expected/live WF02 canonical core SHA-256 both `0f5893ffba59b23d181c363b26b991450e3fc016a52016e1ec686797dbfe23c1`;
- live WF02 active with 17 nodes;
- live `Search Wikipedia Facts` has no retry/maxTries and uses `continueRegularOutput` only for bounded per-probe aggregation; final source aggregation fails closed if no title-supported page survives.

## WF02 current factual contract

- normalize topic once;
- preserve up to 10 meaningful full topic tokens for relevance/evidence validation;
- discovery query uses at most first two meaningful subject-leading tokens;
- bounded factual probe languages are exactly EN/PL/RU/UK, requested language first;
- exactly one Wikipedia request per probe; no retry loop;
- request `langlinks` to target language;
- if best factual page is found in another language, require official Wikipedia language link into requested output language;
- no topic-specific mappings, generative translation, provider cascade, weaker factual gates, or duration-threshold changes;
- how/why narration favors mechanism/principle/construction evidence;
- extractive compiler remains provenance-preserving: every narration segment is a token subsequence of source evidence;
- already-safe explanation candidates prefer stronger causal/mechanism content.

Regression proof before deploy:

- all seven new WF02 regressions PASS;
- WF02 Code compile `8/8` PASS;
- real Wikipedia: RU-topic→UK induction cooktop 60s `60.106`, UK refrigerator 60s `59.975`, PL popcorn 15s `15.079`, EN induction 15s `14.939` — all safe;
- staged pipeline PASS, retained Edge audit 150 rows / 40 safe / 0 false-safe;
- CASE1 staged provenance PASS;
- CASE1 visual eligibility PASS;
- unchanged duration operating bands PASS.

## Visual-quality-v2 contract

For six beats:

- every beat has one truth-eligible selected asset;
- at least five perceptually distinct clusters;
- no adjacent duplicate cluster;
- no cluster over `0.34` of total beat duration;
- missing/NaN/non-finite values fail closed;
- WF05 independently validates durable visual quality;
- actual rendered midpoint frames independently satisfy required state count.

The old induction job `13f64c50-8dd5-47e4-a88f-1411d258e7c4` is a permanent PRODUCT FAIL fixture: six rows but only two visible states. Never reuse it as acceptance evidence.

## M8 Quality Run

Roadmap requires at least 10 materially different videos with human-visible review.

### M8 #1 — zipper — PASS

- `How does a zipper work? / en / 15`;
- accepted job `227c8a50-ef1a-49e5-8d26-fdb40f663c83`;
- machine + human review PASS.

### M8 #2 — induction heating — PASS

- accepted fresh job `2c182ff8-ea9f-4ddf-a417-b49f796d23f5`;
- `How does induction heating work? / en / 15`;
- exactly one Edge synthesis, measured voice `13.944 s`;
- 6 selected/perceptual/rendered states, adjacent 0, max share `0.1813`;
- ffprobe PASS;
- user watched exact fresh video and said `мне нравится`.

Current accepted count: `2/10`.

## Exact next action

1. Start a completely fresh production job for the previously failing cross-language case: `как работает индукционная плита / uk / 60`; never reuse jobs `85fcc63b-b89b-40d0-b253-6383b715f105` or `e1399581-305b-4341-910e-b9477a04f499`.
2. Require full machine proof through `review_ready`, including exactly one Edge synthesis, timing, six timed beats, visual-quality-v2 and ffprobe.
3. Human-review that fresh UK video; any real product failure stops progression and is fixed systemically.
4. Then run a completely fresh `Dlaczego popcorn pęka podczas podgrzewania? / pl / 15` as M8 #3 and require machine + human PASS.
5. Continue materially different topics/languages until at least `10/10` human-reviewed videos.

## Resume rule

If chat/context is lost, read fresh `PERMANENT_PROJECT_RULES.md`, this file, `ENGINEERING_HISTORY.md`, and fresh VPS/runtime. Current production is on WF02 commit `e4e8560`, visual rewrite `f7c4096` + lifecycle fix `b83bf6d`; M8 accepted count is `2/10`; immediate next action is a fresh production RU-topic→UK/60 induction-cooktop job.
