# Factual architecture audit — 2026-09-06

## Scope and verified baseline

This is a new end-to-end audit, not acceptance of the earlier design. The user's
current instruction supersedes historical architecture gates that would stop
systemic work pending review of an already rejected approach.

- Repository: `Pokhyl/ai-short-form-content-factory`, working branch
  `rebuild/agentic-editor-v5`, audited HEAD `b909a25`.
- The previously available local checkout was 32 commits behind. Work uses a
  separate worktree of the same repository; no new project was created.
- VPS SSH alias: `hodor-vps`. Product directory:
  `/opt/ai-short-form-content-factory`.
- VPS Git checkout reports old branch `feat/m6-visual-sourcing`, HEAD `7657c9e`,
  many modified/untracked files. This Git status is **not** deployed provenance.
- Direct SQL comparison found all seven generation/provider workflows' `nodes`,
  `connections`, and `settings` exactly equal to audited GitHub source. All are
  active with equal versionId/activeVersionId. WF01 is **active**, contrary to an
  earlier paragraph in CURRENT_STATE_V5.
- All nine running media-worker source modules plus package.json/package-lock.json
  match audited GitHub source byte for byte. Runtime image:
  `sha256:4ba45a125df67d9da18287da02535ae8b648f36c44843b4dabe49d9df057ebc6`.
- PostgreSQL: 18.6; n8n: 2.33.3. Worker is Node 22/FFmpeg. SearXNG runs separately.
  The documented `/opt/ai-short-form-v5-runtime/.venv/bin/python` is absent.
- Product DB contains jobs, job_evidence, scenes, assets, media_library_assets,
  visual_segments, visual_shots, publications. MCP audit is a separate integration.
- 23 workflows are stored: seven generation/provider workflows, WF06 review API,
  nine MCP integrations, two old director gateways, four inactive diagnostic/
  recovery workflows. No main generation node calls those old director/diagnostic
  workflows. They were inventoried, not deleted.
- WF06 was live but missing from source. Its source is now restored, deactivated
  in the export by default; no live workflow has been changed.
- VPS resources at inspection: 3.8 GiB RAM, about 1.8 GiB available, 2 GiB swap,
  about 6.1 GiB free disk. Unrelated n8n/Caddy/application containers also run here.

## Observed outcomes

The latest 35 job rows contain 27 failures and 8 review_ready results. This is an
operational sample across changing revisions, not a controlled success-rate
estimate. All review_decision values in this sample are null; machine readiness
is not human acceptance. Existing documented human rejections still apply.

Latest job `d3ed2258-68ca-49d3-b389-4ff49deb54c6` (mechanical escapement, ru, 15)
failed in WF04 execution 16160, after continuous Edge narration measured 14.112 s.
WF02 16112 and WF03 16117 were inspected as well. Discovery returned no candidates
for beats 1 and 6, with zero provider errors. The narration includes fragments
`толкая шестерни. Этот ритм` and `обеспечивая точность хода и`. Provider recovery
queries collapsed to `mechanical clock`; stronger acceptance requirements still
could not be met. Do not rescue this job or tune a clock-specific query.

Earlier execution 16031 (abiogenesis job 4894fe3a...) was inspected through initial
review, bounded recovery and failed global assignment. Previous human-failure
records describe nominal approvals of wrong scientific/historical images.

A frame contact sheet from the exact existing Curie MP4
`jobs/d278b778-4aea-468d-b78e-aa03e994fd46/render/final.mp4` shows a food-filled
mortar at the ore-processing narration and staged laboratory imagery at historical
claims. This is model frame inspection, **not a human viewing or HUMAN PASS**.

## Systemic causes in executable code

1. **Inventory is too late.** WF02 writes and freezes a script before any visual
   search. WF03 synthesizes it and WF04 then attempts to satisfy its invented
   photographic obligations. The old architecture document described the opposite
   order. Relevance tightening can reject false images, but cannot make an
   unavailable exact shot exist or rewrite the frozen story responsibly.
2. **Fixed counts replace editorial structure.** Duration maps to 6/10/14/18 beats
   throughout prompts, partitioning and SQL. Token-weight partitioning cuts natural
   statements into fragments. Each beat receives one or two unique images, creating
   an avoidable scarcity/assignment problem. Count is not proof of story quality.
3. **Timing is synthetic.** `WF03 / Prepare Beat Timings / buildTimedBeats` allocates
   measured total duration by token weights. No real-audio alignment is used.
   Measuring the total WAV does not validate the time of an individual phrase.
4. **Provenance is fabricated structurally.** WF02 fills missing source IDs using
   the first two search rows and distributes evidence over sentences modulo source
   count. A valid source foreign key does not establish support for that sentence.
   Duration rewrites must also preserve explicit claim/support relationships.
5. **Review remains a weak semantic oracle.** A small, target-conditioned vision
   response plus metadata overlap is treated as approval. Obscuring provider IDs
   helps presentation bias but does not establish person/material/event identity.
   The candidate description, source provenance, narrated assertion and visible
   composition must be checked together before a claim is authored.
6. **Selection complexity compensates for late commitment.** There are exact-query
   lexical gates, query rewriting, exposure ranking, batched review, perceptual
   matching, conflict search/review, and beam assignment after voice freeze.
   Global uniqueness belongs before final story commitment; it cannot compensate
   for semantically unsuitable approved pools.
7. **Final composition is not reviewed.** The actual default is custom FFmpeg in
   media-worker, not OpenNolan. Photo framing is a static central 9:16 crop; a
   diagram can lose its subject/labels, and source-preview approval does not approve
   the rendered crop. Diversity hashes establish difference, not relevance.
8. **Tests overstate confidence.** Baseline 44 static Python/Node regressions pass.
   Many assert code strings or accept mocked model judgments. They do not prove
   supported claims, heard-word alignment, actual crop, or fresh SQL bootstrapping.
9. **Source cannot recreate the DB.** Fresh init + historical migrations fails in
   020 because script_fit_passes does not exist. Other required columns and
   job_evidence are also missing. Two distinct files use migration number 021.
10. **Optional/free service availability is a separate risk.** The text/vision
    gateway uses Kilo stepfun/step-3.7-flash:free then Gemini 3.1 Flash Lite; both
    have bounded 90 s calls. TTS tries Gemini then Edge. This is no mandatory
    per-video purchase, but not unlimited guaranteed capacity. Provider exhaustion
    must be observable; it is not evidence that a visual story is impossible.

## Preserve, change, remove

Keep n8n orchestration and product input, PostgreSQL durable jobs/atomic writes,
free media adapters/provenance, one continuous natural-rate narration, real media
hashes, FFmpeg encoding, and explicit human acceptance of exact artifacts.

Change the causal order to researched claims -> actual visual inventory and
verified identity/visible content -> unique available visual story -> supported
natural narration -> exact speech boundaries -> composition -> rendered-artifact
QA. The story editor must omit an unshowable claim or choose a truthful showable
angle **before** narration is finalized, without changing the user's subject.

Replace synthetic beat timing and invented source assignments. Let semantic units
and actual available support determine the edit, within bounded duration/readability
constraints. Do not impose a new arbitrary number of workflows or services.

Remove late search-recovery/beam machinery from the critical path once inventory-
first selection is integrated and proven. Do not simply lower thresholds or allow
repeats. Keep old behavior isolated until the replacement is tested; do not deploy
an unfinished architecture.

## Completed engineering changes in this work session

- Complete fresh-database schema baseline reconciled to production product schema.
  This is a new-volume bootstrap, not an in-place production migration.
- Restored existing WF06 review API source.
- Added actual PostgreSQL bootstrap + PREPARE of all 22 workflow SQL statements +
  staged job/evidence/scene/visual writes test.
- Added executable workflow graph, Code-node syntax, child-reference and webhook
  contract checks.
- Added real n8n 2.33.3 import test asserting all eight workflows are imported.
  Important finding: --separate with these array-wrapped exports prints success
  while importing **zero** workflows. The test normalizes one combined array and
  checks cardinality, not exit status alone.
- Added capture/validation of native Edge word-boundary metadata, persisted beside
  the final WAV with SHA256 of the exact audio and normalized script. This is
  groundwork: existing WF03 still uses its old synthetic planner until replaced.
  Missing/mismatched word data must not be manufactured from duration.
- Component-only native Edge probes in en/pl/ru/uk returned real word boundaries
  including sentence pauses. They are not product E2E proofs.

No production files, DB rows, workflow versions or services were changed. No new
product job was submitted in this session, and no existing job was repaired.

## Recovery after Codex usage-limit interruption

The Codex session stopped after commit `36c76437e3460641bcd49a106ee69d8ffebf6142`.
The chat transcript described later work that was not present in that commit. A fresh
checkout of that exact commit confirmed the missing tail instead of assuming it had
been saved.

Recovered systemic work, still outside production:

- WF03 now uses the existing Edge continuous synthesis endpoint as the exact timing
  authority. The old Gemini TTS / wait / retry / store branch is removed from the
  product path. The final WAV must return `provider-word-timing-v1`, and beat
  boundaries are derived from observed provider word timestamps rather than weighted
  division of total audio duration. Speech rate remains unchanged.
- `compose.yaml` now passes the already-existing production Pexels/Pixabay keys to
  media-worker and attaches media-worker to the shared `n8n_default` edge network.
  Previously the keys existed in `.env` but were absent from the running worker.
- `/research/search` now uses the configured SearXNG JSON endpoint instead of silently
  querying only English Wikipedia. Missing/invalid SearXNG configuration fails
  explicitly. `/health` reports whether Pexels, Pixabay and SearXNG are configured
  without exposing credentials.
- `.env.example` documents the three runtime variables without real secrets.

Verification of this recovered state:

- 48/48 non-live static regressions PASS;
- fresh PostgreSQL contract PASS: 22 workflow SQL statements plus staged writes;
- actual n8n 2.33.3 import contract PASS: 8 workflows;
- clean media-worker image build PASS;
- isolated worker health shows Pexels/Pixabay/SearXNG configured;
- isolated `/research/search` returned 20 SearXNG results for a mechanical-clock query;
- isolated legacy visual-discovery probe returned provider errors `[]` and candidates
  from Wikimedia, Pexels and Pixabay (44/15/18 appearances in the returned structure).

No production workflow, container, database row or product job was changed by this
recovery. The primary unfinished product change remains inventory-first story
construction before final narration freeze.

## Exact continuation

1. Foundation verification is complete: 46/46 static regressions, fresh PostgreSQL
   baseline with 22 prepared statements and staged writes, actual 8-workflow n8n
   2.33.3 import, and worker build all PASS. Real local worker endpoint probes
   pass for en/pl/ru/uk, including matching final WAV SHA256 and unchanged rate.
   The local worker image is
   `sha256:49f4a0dd558dc0a3ec4e2bd24045e93601eb743afe7added8866cfdfce551f7b`.
   These are component/reproducibility results, not final product acceptance.
2. Implement the inventory-first story contract in the existing n8n product path:
   retain evidence/asset IDs per complete authored semantic unit; validate actual
   available image and source identity before freeze; reserve unique assets before
   TTS. Replace the source-ID modulo fallback and fixed-count requirements together
   with their persistence contracts, not with another patch to failed jobs.
3. Consume exact word timings in WF03 for the final accepted narration, preserving
   explicit script/asset/evidence units across bounded duration rewrites. The
   existing Edge dependency can supply timings without a new service. Gemini
   audio cannot enter this contract without an equivalent measured aligner.
4. Replace WF04's post-freeze creative recovery with execution/verification of the
   approved inventory; validate crop-aware composition and final audiovisual QA.
5. Run static regressions, fresh DB tests, actual n8n import and worker build. Use
   an isolated n8n/DB/worker environment for full new product-input tests before
   changing production; preserve normal orchestrator execution and no manual rescue.
6. After verified deployment, submit fresh varied topics and all language/duration
   contracts. Inspect final audiovisual artifacts; obtain explicit human viewing
   and PASS/FAIL for exact MP4 hashes. Never mark this overall project complete
   because bootstrap tests pass or a job reaches review_ready.

Local evidence and temporary scripts are in the task workspace `work/audit/`,
outside the repository; they are not deliverables or tracked runtime data. The
working tree is `work/repository` in the same task workspace. SSH access works.
Docker Desktop was started for local isolated tests. No credentials were printed,
exported decrypted, or committed.

## Inventory-first implementation continuation after the audit

The audit recommendation has now been implemented in the existing WF02-WF05 path on preservation branch `continuation/codex-recovery-20260906`; production remains unchanged at this checkpoint.

Implemented contracts:

1. WF02 now derives candidate claims from explicit research evidence, discovers actual still-image candidates before script freeze, fingerprints and reviews actual candidate images, removes perceptual duplicates, and writes the final story only from claims with a reserved verified asset. `jobs.story_package` freezes explicit claim/evidence/unit/asset identity.
2. WF03 now uses native Edge provider word timestamps for final semantic-unit timing. Duration correction may rewrite spoken wording inside the same frozen units but cannot change unit/claim/evidence/asset identity and never changes speech rate.
3. WF04 is now reserved-asset execution rather than post-freeze creative search. It downloads only pre-reserved assets and verifies the stored normalized file against the pre-script perceptual fingerprint before durable visual rows are accepted.
4. WF05/render now consumes variable semantic units, requires the inventory-first reserved-visual contract, preserves complete still-image foregrounds in a 9:16 composition, and returns/persists the SHA256 of the exact rendered artifact.
5. Candidate-claim generation, final inventory-grounded story generation and duration rewrite now request structured JSON schemas from the existing bounded model gateway. Deterministic validators remain authoritative after model output.
6. WF02 failure branches now explicitly emit error output into the common persistence handler, which can recover `job_id` from stable upstream planner context. This fixes the observed isolated-E2E defect where an invalid model JSON response could leave a job stranded as `created/intake`.

Latest verification gate after those changes:

- 55/55 non-live static regressions PASS (13 Python, 42 Node);
- fresh PostgreSQL contract PASS;
- all 8 workflow exports import successfully into n8n 2.33.3;
- clean media-worker Docker build PASS, image `sha256:8017fba74dadb5d0ccee338e358a2586a96a8ab088b8bd6de0bfbc5565e334b9`.

The first isolated full n8n attempt used only normal product input (`How a mechanical clock escapement works`, `en`, `15`) and exposed the missing structured-output/error-persistence contract above. No manual creative rescue was performed. After the systemic fix, a second clean isolated n8n attempt could not be completed because the server-management safety layer blocks injecting an application credential into a disposable n8n instance. Static/import/fresh-DB/build verification is complete, but this harness restriction is not an E2E product PASS.

Next controlled step is to preserve/push this exact source state, then deploy with an explicit production rollback capture and submit a fresh normal product job. `review_ready` is not success; the exact MP4 hash requires human viewing.
