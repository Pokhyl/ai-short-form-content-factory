# Current State — V5 n8n Autonomous Video Orchestrator

Last updated: 2026-09-07

Branch: `rebuild/agentic-editor-v5`.


## 2026-09-07 provider cue mapping — exact GitHub sync and WF03-only deployment

Verified VPS commit was transferred as native Git objects via SSH fetch and pushed
without force from the local authenticated checkout. GitHub now contains exact
commit `5829569857d7ab61ae1be85b34e1d958726a63ed`, parent
`a2b7c183e6c48abeef5e8f77410d700dd53c5724`, tree
`8d0aeaf5e05f3a0262b277d1d0a559418e4a0449`. All three changed blob SHAs matched;
post-push fetch confirmed the same parent/tree. The transport branch was not used.

WF03 ONLY deployed using SentinelX sudo scripts. Zero active/running/waiting/new
executions before mutation. Rollback current/published JSON, CLI export, verified
source and SHA256 manifest:
`/opt/ai-short-form-content-factory-runtime-backups/provider-cue-5829569-20260907T152925Z`.
Current import parity passed before publishing. n8n CLI requested restart; exactly
one restart performed. `/healthz` returned HTTP 200, status ok. WF03 active,
current version = activeVersionId = `165590b5-43f7-4e1d-b756-966fd1152292`.
All 21 nodes, connections and current settings equal source; published history
nodes/connections equal source (n8n history does not store a separate settings
field). Canonical source/current core SHA256 (sorted JSON, UTF-8, compact separators):
`6664b28af13aef018fab473cc4f912e58ba82c83774f9f9fd9ca1fb101d8286c`.
Zero active executions after restart. WF02/WF04/WF05, PostgreSQL and media-worker
were not redeployed; worker remains image `fe5b0dc2da7f...`.

Next exact step: submit ONE new normal Panama Canal / ru / 15 job through WF01,
capture HTTP response, then follow WF01–WF05. Do not modify failed `66fda166...`.
No MP4 or HUMAN PASS yet.

## 2026-09-07 provider multi-token cue unit-boundary defect — verified, pending WF03 deployment

The Edge provider-tail correction is deployed in production from GitHub commit `a2b7c183e6c48abeef5e8f77410d700dd53c5724`, exact tree `516979685b2b5fcd9a2c4aac076781e13f2a291c`. Media-worker-only deployment replaced image `sha256:30843256898826e6f59e719c1c55a820dafb6b50f910a3f6b1006e9eded90a9d` with `sha256:fe5b0dc2da7fa8e1771ec032b9be77d31757b8e3b3af5909a6f4fcb3fe7a0aec`; rollback snapshot is `/opt/ai-short-form-content-factory-runtime-backups/edge-tail-a2b7c18-20260907T144148Z`. Worker health returned HTTP 200 with Pexels, Pixabay and SearXNG configured; n8n/PostgreSQL were not recreated.

NEW normal job `66fda166-7768-46ed-b058-457ff43b7749` (How the Panama Canal locks work / ru / 15) was created once through WF01 HTTP 201. WF01 **16384** succeeded. WF02 **16385** progressed normally through model gateway executions **16386–16390**. WF03 **16391** synthesized three unchanged-speed Edge attempts after two bounded story rewrites. The final accepted-duration WAV was **16.383333s**, provider source WAV **17.208s**, final exact word cue ended at **16.350s**, provider-tail trim **0.824667s**, `rate_percent=0`, `post_tempo_factor=1`. WF03 then failed closed with `Provider timing diverges inside story unit 2 [line 13]`; no WF04/WF05 or MP4 was produced. The failed job remains immutable.

Exact WF03 execution data is preserved at `/opt/ai-short-form-content-factory-runtime-backups/provider-timing-66fda166-7768-46ed-b058-457ff43b7749-20260907/execution-16391.json`, SHA256 `0b0808a464622e0b8094983da7a0fc1f477f57656d48af0d1eced15c1e836d00`.

Systemic cause: `Build Exact Story Unit Timings` incorrectly assumed one Edge provider timing cue always equals one whitespace-delimited narration word. Edge can legitimately group multiple spoken words into one exact timing cue; in this execution unit 2 contained narration `...на 26 метров к...` while provider timing represented `26 метров` as one cue. The complete provider cue sequence still reconstructed the full final narration exactly, so the failure was a unit-boundary indexing defect, not a TTS/text divergence.

Correction: story-unit mapping now consumes whole provider cues until their normalized text exactly equals each complete story-unit narration. A partial accumulation must remain an exact word-boundary prefix of that unit; otherwise it still fails closed. Provider cues are never split and no synthetic timestamps are created. If one cue crosses an actual story-unit boundary, or the provider text does not reconstruct the unit exactly, the same divergence gate still rejects the run.

Verification: targeted story-unit timing regression now includes a multi-word provider cue (`26 meters`) and PASSes; the related exact-TTS/fit/word-timing regressions PASS. Full ordinary static suite: **48/48 Node + 13/13 Python = 61/61 PASS**; fresh PostgreSQL contract PASS (**21 workflow SQL statements + staged writes**); real n8n **2.37.10** import PASS for **8 workflows**; structured model invocation contract PASS for **4 calls**; workflow JSON parse and `git diff --check` PASS. Exact saved execution **16391** replay through the patched `Build Exact Story Unit Timings` node PASSes with duration **16.383333s** and exact unit ranges **0–5.300**, **5.300–11.149**, **11.149–16.383**.

Next: preserve this exact verified tree in GitHub, deploy **WF03 only** with rollback/source-current-published parity, then submit one completely NEW normal product job. Do not resume or edit `66fda166...`. No MP4 or HUMAN PASS yet.

## 2026-09-07 Edge provider tail silence — verified, pending worker deployment

The previous story-persist correction is deployed in production from GitHub commit `c6124f528a5798502567e8f4f7d7c108e46558ab`, exact tree `bfb26fd33828d327207cd0fb3260975081f3b28b`. WF02 current/active version is `750687ba-bc44-480d-b189-389029be41cf`; source/current/published core parity passed before the new run.

NEW normal job `0b025bcf-00b6-4548-8cc3-80d4e0eb982b` (How the Panama Canal locks work / ru / 15) was created through WF01 HTTP 201. WF01 **16356** succeeded. WF02 **16357** succeeded end-to-end through semantic resolution, research, verified global unique inventory and final story; Model Gateway executions **16358–16362** all succeeded. WF03 **16363** then failed closed in `voiceover`: `Voiceover duration 16.704s is still outside target after 3 story rewrites`. Duration-rewrite gateways **16364–16366** all succeeded. The failed job remains immutable; no WF04/WF05 or MP4 was produced.

Exact WF03 execution data is preserved at `/opt/ai-short-form-content-factory-runtime-backups/voice-duration-0b025bcf-20260907/execution-16363.json`, SHA256 `d0c8066d1393f7582bfd8d2f4c0bcaa3deeb606eb7c557339f19a6d1110b5267`. Exact execution replay showed four unchanged-speed Edge measurements: **41 words / 20.832s**, **34 / 17.784s**, **32 / 17.304s**, **32 / 16.704s**. The controller requested approximately 30, 29 and 28 words, but its broad rewrite acceptance allowed longer outputs. More importantly, every Edge synthesis contained a stable provider-added trailing gap of about **0.93–0.95s after the last exact word cue**. On the final 16.704s WAV, the last provider word ended at **15.775s**; counting the provider tail as spoken narration alone pushed the otherwise valid speech outside the existing 15s gate.

Systemic correction is in the media-worker only. Before the existing natural-tail pad and exact-duration gate, the worker now uses Edge's provider word cues to trim only audio after the final exact word boundary while preserving one 30fps frame of post-roll. Spoken samples, words and provider timing are untouched; `rate_percent=0` and `post_tempo_factor=1` remain mandatory. The existing short-narration tail pad, duration thresholds, story rewrite loop, WF02/WF03 semantic contracts and all reviewer/evidence gates are unchanged. This is not speech-speed manipulation and cannot rescue narration whose actual spoken span is too long or too short.

Verification: **48/48 ordinary Node static regressions PASS** (the separate real-provider dry-run intentionally requires `JOB_CONTEXT_FILE`) plus **13/13 Python regressions PASS**; fresh PostgreSQL contract PASS (**21 workflow SQL statements + staged writes**); real n8n **2.37.10** import PASS for **8 workflows**; structured model invocation contract PASS for **4 calls**; media-worker syntax, `git diff --check` and Docker build PASS. A real isolated Edge synthesis using the exact failed 32-word narration returned HTTP 200 with provider WAV **16.704s**, last word **15.775s**, provider-tail trim **0.895667s**, final WAV **15.808333s**, **32 exact word timings**, `rate_percent=0`, `post_tempo_factor=1`, and no synthetic tail pad.

Next: preserve this exact verified tree in GitHub, deploy **media-worker only** with rollback/image identity and health checks, then submit one completely NEW normal product job. Do not resume or edit `0b025bcf...`. No MP4 or HUMAN PASS yet.



## 2026-09-07 story persist return-value defect — verified, pending deployment

NEW normal job `99d20c0f-b7e4-4aac-8715-680e62794f6b` (How the Panama Canal locks work / ru / 15) ran against the deployed global-unique pre-review shortlist. WF01 **16349** succeeded. WF02 **16350** completed semantic resolution, research, candidate claims, global unique review, verified inventory and final story generation; Model Gateway executions **16351–16355** all succeeded. The database contains an `inventory-first-story-v1` story package with **3 units / 3 assets**, but WF02 then failed closed with `story package persisted null/3 units [line 1]`. The failed job remains untouched; no WF03/WF04/WF05 or MP4 was produced.

Exact execution data is preserved at `/opt/ai-short-form-content-factory-runtime-backups/unique-566366a-20260907T112245Z/execution-16350.json`, SHA256 `fa316ede8bbd70c24656584322d6adad2a306ede9f418275cfe6320c15e02911`.

Systemic cause: `Persist Inventory First Story` performs the job update inside a PostgreSQL data-modifying CTE `upd`, then its final SELECT re-read `public.jobs.story_package` in the same SQL statement. That read uses the statement snapshot and therefore observes the pre-update `story_package = NULL`, even though the UPDATE is persisted by statement completion. `Require Persisted Inventory Story` consequently produced a false failure. This is a persistence return-value contract defect, not a story-generation or inventory failure.

Correction: `upd` now returns `jsonb_array_length(j.story_package->'units')::int AS story_unit_count`, and the final SELECT reads `story_unit_count` from `upd` instead of re-reading `public.jobs`. The real fresh-PostgreSQL contract now executes this exact persist statement on a new eligible job and requires the returned row to report one inserted evidence item, `job_updated=true`, zero pre-TTS scenes and `story_unit_count=3`. Static regression also forbids the same-snapshot table re-read from returning.

Verification after correction: **60/60 static regressions PASS** (47 Node + 13 Python); fresh PostgreSQL contract PASS (**21 workflow SQL statements + staged writes**, including the actual persist return-value path); real n8n **2.37.10** import PASS for **8 workflows**; structured model invocation contract PASS for **4 calls**; workflow JSON parse and `git diff --check` PASS. Worker, reviewer, semantic/evidence gates and minimum inventory are unchanged.

Next: preserve the exact verified tree in GitHub, deploy **WF02 only** with rollback/source-current-published parity, then submit one NEW normal product job. Do not resume or edit `99d20c0f...`. No MP4 or HUMAN PASS yet.


## 2026-09-07 unique shortlist deployed — fresh job running

Source commit `566366a74b3202b668bcb34b5b38794bbf8ebf72`, exact verified tree `52a6009592a1b3bf9e0279190133220a06d9d192`, is now deployed to WF02 only. Current/published nodes and connections match source; active/current version `53b3f193-faf7-4b2e-94c5-2c00216d9d43`. No active/waiting executions existed before deployment. n8n 2.37.10 restarted; worker unchanged. Rollback: `/opt/ai-short-form-content-factory-runtime-backups/unique-566366a-20260907T112245Z`.

NEW normal job `99d20c0f-b7e4-4aac-8715-680e62794f6b` created through WF01 HTTP 201 with How the Panama Canal locks work / ru / 15. Earlier startup request returned 404 without creating a job. Next: follow exact execution through E2E; fix further demonstrated general defects autonomously, without manual rescue or gate weakening. No MP4/HUMAN PASS.

## 2026-09-07 global unique pre-review shortlist — verified, pending deployment

Continuation from `a2ce67803d578c898d3121c8f66b9b849820e470` in `/opt/ai-short-form-content-factory-unique-review-20260907`. WF02 now builds one ranked round-robin pool across all fingerprinted discovery buckets before image review. Provider identity and perceptual duplicates (existing distance <=18) cannot consume repeated review slots; remaining unique candidates fill slots up to the unchanged total budget of four images per original retrieval hypothesis, with at most 24 images per model batch. Origin fields remain available for audit, but proposed hypothesis text is no longer shown as an acceptance cue. Full research corpus and all reviewer/final metadata/evidence/uniqueness gates remain. Minimum inventory is counted in unique assets, not productive origin buckets.

Cross-topic clock/telescope regression verifies exposure diversity, budget, multi-batch splitting, one productive bucket, perceptual duplicates and target-anchor rejection. Exact failed execution 16344 replay yields **20 unique review images instead of 9**, with the same 20-slot budget; this is component evidence, not semantic/E2E acceptance. Unchanged selection replay confirms C3-I1 was rejected by metadata consistency and only C5-I4 survived, producing the recorded 1/3 failure.

Verification: **60/60 static regressions PASS**, fresh PostgreSQL contract PASS (21 SQL statements plus staged writes), isolated real n8n 2.37.10 import PASS (8 workflows), structured invocation contract PASS (4 calls), git diff check PASS. Worker unchanged. Last product job remains failed `87af4f4b-83d8-4bdc-b110-725f1a6d6f40`, WF02 16344. Next: preserve exact verified tree in GitHub, deploy WF02 only with rollback/parity, and submit a NEW normal product job. No MP4 or HUMAN PASS.

## 2026-09-07 fresh global-pool execution — failed, review shortlist defect confirmed

Latest job `87af4f4b-83d8-4bdc-b110-725f1a6d6f40` (How the Panama Canal locks work / ru / 15) failed/script in WF02 **16344**: `pre-script verified visual inventory 1/3`. Intake **16343** succeeded. Gateways **16345–16348** completed; candidate drafting **16347** succeeded through Kilo; actual-image reviewer **16348** fell back from Kilo length/empty output to successful Gemini JSON. No final story, voice or MP4 was produced. Failed jobs remain untouched.

Confirmed general defect from exact execution and source: review shortlisting is still bucket-local. `Prepare Inventory Review Batches` applies `fingerprinted_candidates.slice(0,4)` separately per origin claim, and global identity/perceptual dedupe occurs only AFTER model review. This execution had 40 fingerprinted occurrences representing **28 unique provider assets**, but **20 review image slots represented only 9 unique assets**. Three Pixabay identities occupied 14 slots (4/5/5 occurrences); **19 unique fingerprinted assets never reached the reviewer**. This proves wasted review exposure, not that omitted images would necessarily pass semantic review or provide the required three facts.

The reviewer approved two occurrences; deterministic selection retained one. Reviewer output also warrants semantic scrutiny: an aerial-lock description was paired with a causal claim about ocean-level differences and the choice of canal design, while a general route-map description was paired with six lock steps. Those descriptions alone do not establish that the claimed causal/quantitative details are visible. Do not loosen reviewer or metadata gates to increase acceptance.

Runtime evidence captured at `/opt/ai-short-form-content-factory-runtime-backups/global-11d8c6a-20260907T110915Z/execution-16344.json`. Deployed workflow source remains `11d8c6a4a2d6ad632c28443cc14519d9de645731`, exact tested tree `e0fbd278cf092c3735832ec1cc1e3a9a165d23e5`; deployment continuity commit `c6541a76818b5c4da0179d15c1dadf933702ab33`. No unverified product-code changes were made after this failure.

Next exact engineering step: implement a global unique pre-review shortlist from the fingerprinted pool, preserving origin metadata for audit and the existing total image budget, evidence grounding, actual-image authority and final uniqueness gates. Add cross-topic regression proving duplicate retrieval buckets cannot consume repeated review slots while unique candidates remain; test a single productive discovery bucket without requiring a minimum number of origin buckets. Inspect the exact two model-approved observations through the unchanged deterministic gates. Verify the full required contracts, commit through GitHub connector, deploy only verified changes with rollback/parity, then submit a NEW normal job. Current blocker is pre-review exposure diversity and unproven semantic inventory quality. No HUMAN PASS.

## 2026-09-07 global observed-pair pool — deployed, fresh job running

Verified VPS commit `b6acede19dd2c55400cdfa92e4e25436dd71235f` was preserved through the connected GitHub API as `11d8c6a4a2d6ad632c28443cc14519d9de645731`, fast-forward from `dbd1567145b64836b5ce4a610b3e9e16167bcab3`. All four blob SHAs and exact tree `e0fbd278cf092c3735832ec1cc1e3a9a165d23e5` match the tested VPS commit. The original checkout remains clean and preserved; HTTPS git push on VPS lacks credentials, so use the connected GitHub API for continuity writes.

WF02 only was imported and published on production n8n 2.37.10. Source/current/published nodes and connections match (34 nodes); current/active version `12549e8e-6fc6-4e10-9c0d-fdb5146be528`. No running/waiting executions existed before deployment/restart. Worker was unchanged. Rollback capture: `/opt/ai-short-form-content-factory-runtime-backups/global-11d8c6a-20260907T110915Z` (current and published WF02 plus exact deployed source). n8n restarted and logged activation of the product workflows.

NEW normal WF01 intake returned HTTP 201, job `87af4f4b-83d8-4bdc-b110-725f1a6d6f40`: How the Panama Canal locks work / ru / 15. An earlier request during startup returned HTTP 404 and did not create a job. Failed `908621d8...` remains untouched. Next: inspect new job execution and follow autonomous WF02–WF05 to exact MP4 or capture a systemic failure. No MP4/HUMAN PASS yet.

## 2026-09-07 global observed-pair pool — verified, pending deployment

The prior PostgreSQL-credential correction was committed as `dbd1567145b64836b5ce4a610b3e9e16167bcab3` and deployed to WF02 only. Production source/published parity passed with 34 nodes; n8n remained 2.37.10, worker provider health still reported Pexels, Pixabay and SearXNG configured, and rollback backup is `/opt/ai-short-form-content-factory-runtime-backups/story-persist-dbd156-20260907T050941Z`.

A NEW normal product job `908621d8-9c6f-45ab-9680-6f08852c76e7` (Panama Canal / ru / 15) then failed closed in WF02 execution **16333** with `pre-script verified visual inventory 1/3`. No story package, voice or MP4 was produced. Discovery itself was not empty: real provider inventory contained ships in Panama Canal locks, a historical lock cross-section, lock photographs, Gatun/expansion imagery and other candidates. The image reviewer correctly approved a ship in a lock and a technical lock cross-section, while rejecting many mismatches.

The remaining systemic defect was claim-local isolation after discovery. Each candidate image was reviewed only against the evidence IDs of the claim that happened to retrieve it, and the selector could reserve at most one approved asset from each discovery claim. Therefore a useful image retrieved under one hypothesis could not support a different research-backed fact, and two distinct truthful observed facts from one productive search bucket could not both enter the final story inventory. The discovery hypothesis had accidentally become a hard partition even after the architecture moved toward observed image/fact pairs.

Correction in the current clean checkout: the reviewer receives the full research corpus for every review batch and is explicitly told that the discovery claim/target is only the retrieval origin, not the factual acceptance boundary. A reviewed image may bind to any 1–3 valid global research evidence IDs when its visible content directly supports that fact and the resolved subject/user intent. Deterministic selection validates those IDs against the global research inventory, keeps the existing target-anchor gate and image/metadata consistency check, then flattens all approved observations into one global pool. More than one distinct observed pair may come from the same discovery hypothesis. Provider identity, exact supported-fact duplicates and perceptual duplicates remain forbidden; accepted observations receive fresh sequential story claim/asset IDs while the original discovery claim, target and evidence IDs are retained as audit fields. No relevance weakening, unreviewed fallback, topic-specific query, duplicate asset or post-script rescue is introduced.

Verification after the correction: **59/59 static regressions PASS** (46 Node + 13 Python); the observed-inventory regression explicitly proves cross-hypothesis evidence binding and multiple final observations from one discovery bucket while rejecting unknown/empty evidence; n8n **2.37.10** import contract PASS for all 8 workflows; fresh PostgreSQL contract PASS for 21 workflow SQL statements plus staged writes; all 4 structured model invocation contracts PASS; workflow JSON and `git diff --check` PASS. Worker code is unchanged.

Next: commit/push this verified WF02-only logical correction, deploy it with rollback capture and source/published parity, then submit a completely NEW normal `topic + language + duration` job. Failed jobs are not resumed. No MP4 or HUMAN PASS yet.


## 2026-09-07 story persistence credential contract — verified, pending deployment

New normal job `7dd0361a-916f-47d6-9263-e37f662ee443` (Panama Canal / ru / 15)
ran against deployed observed-inventory WF02. WF02 execution **16326** reached the
new causal path successfully: candidate claims, real provider discovery, image
review, observed facts/assets, and final inventory-grounded story all completed.
The selected package contained three distinct observed bindings (ship-in-lock,
visible culvert/tunnel opening, and Gatun Locks/Lake aerial view). Final story
model execution succeeded, but the job then failed/script with
`inventory-first story did not update job ...`.

Exact cause: `Persist Inventory First Story` was a new PostgreSQL node whose source
export omitted its `Application PostgreSQL` credential reference. n8n import and
fresh SQL preparation did not detect that runtime credential requirement; live
execution reported `Node does not have any credentials set`. Failure persistence
then correctly marked the job failed; the failed job is not resumed.

Systemic correction: every exported `n8n-nodes-base.postgres` node must carry an
explicit PostgreSQL credential reference. `Persist Inventory First Story` now uses
the same `Application PostgreSQL` credential as the existing WF02 DB nodes, and a
cross-workflow regression checks all PostgreSQL nodes for both credential id and
name so newly added DB nodes cannot silently import without runtime credentials.

Verification after correction: **59/59 static regressions PASS** (46 Node + 13
Python); n8n **2.37.10** import contract PASS for all 8 workflows; fresh PostgreSQL
contract PASS (21 workflow SQL statements plus staged writes). Worker code is
unchanged. Next: commit/push this verified logical stage, deploy WF02 only with
rollback capture and source/published parity, then submit a NEW normal job. No MP4
or HUMAN PASS yet.


## 2026-09-07 observed inventory contract — verified, pending deployment

Job `9705e087-e2ee-41db-b6d5-9d9d277a089c` failed/script in WF02 **16307**
with `pre-script verified visual inventory 0/3`. Gateways **16310** (claims) and
**16311** (review) succeeded. All five secondary detail queries ran, with no
provider errors. New closed-gate imagery was retrieved but rejected because the
hypothetical target additionally demanded a ship. Another target demanded hidden
culverts; others prescribed photographic states that the results did not show.
No final narration, voice or MP4 was generated; job remains untouched.

This demonstrates a deeper contract error than search length: exact hypothetical
composition remained frozen before inventory, so final story could not adapt to
what could truthfully be shown. Further keyword tuning alone is insufficient.

WF02 now establishes an observed image/fact pair before final narration. The
multimodal reviewer receives the cited research snippets and returns actual visible
content, a supported factual proposition (which may narrow the proposed claim),
and 1–3 supplied evidence IDs. It must reject merely thematic content and exterior
photos used to narrate invisible internals. Selection requires nonempty grounding,
IDs within the original claim's evidence, image/metadata consistency, subject
anchors and distinct perceptual hashes. The reserved claim and visual target use
this observed pair; original claim/target are retained as audit fields. Final story
can use only reserved facts/assets. This supersedes historical wording that the
unverified proposed visual target is an immutable acceptance criterion. No
post-script discovery, threshold reduction, duplicate visual or manual intervention.

Verification: 58/58 static regressions PASS (one prompt wording assertion corrected
in the prompt, then rechecked); fresh PostgreSQL and n8n 2.37.10 import of all 8
workflows PASS; actual structured invocation contracts PASS. Worker is unchanged
from the built/verified/deployed bcd0788 image. New causal tests reject unknown or
empty evidence, empty facts and rejected images; verify cited snippets reach review
and only the observed pair reaches final story. Semantic quality still requires
new autonomous execution and human inspection of the final MP4.
Next: deploy verified WF02 with backup/source-published parity; create a NEW normal
job. Do not resume any failed job. Canonical Wikipedia title resolution remains
an identified coverage limitation, not a proven global shortage of free media.

## 2026-09-07 detail retrieval — deployed, fresh job running

Latest completed product job `47c59975-2f39-46e4-9e54-f5816a944998`
(Panama Canal / ru / 15) failed/script in WF02 **16301**:
`pre-script verified visual inventory 1/3`. Candidate gateway **16304** and image
review **16305** succeeded. Short search queries reached providers correctly.
Only C1 gained Commons images; C2–C5 again received the same three Pixabay images.
No provider errors, zero secondary queries, zero canonical article media.
Canonical source title was `Panama Canal lock operational mechanism`, not a
verified Wikipedia page: this separate canonical-media coverage issue remains.

Verified system defect: generic subject-anchor matches satisfied the inventory
candidate-count condition and suppressed detail retrieval; provider order then
controlled the four-image review shortlist. Targets also prescribed unnecessary
camera arrangements, hidden internals and time-lapse photographs before inventory
existed. Reviewer rejected 15/16 candidates; acceptance was not bypassed.

Changes: pre-script inventory issues at most one shorter subject + detail query
in addition to the initial query, independent of generic hit count; ranks results
by distinguishing query terms before fingerprint/review. Existing semantic gates,
perceptual uniqueness and minimum inventory remain. Legacy timed discovery is
unchanged. Candidate instructions require minimal observable supporting content
and disallow invented composition or invisible processes in a still photograph.
This is a retrieval correction, not proof of end-to-end quality.

Verification: **57/57 static regressions PASS**, including independent clock and
radio telescope cases where generic photos cannot suppress detail retrieval;
fresh PostgreSQL contract PASS (21 statements plus writes); import of all 8
workflows into actual n8n **2.37.10 PASS**; 4 real expression invocation contracts
PASS; media-worker Docker build PASS. Next: back up and deploy this verified
WF02/worker change, verify published/source parity and provider health, submit a
NEW job via normal topic/language/duration. Both failed jobs remain untouched.
Deployed verified source `bcd0788`; WF02 current/published nodes and connections
match source. Worker image is
`sha256:30843256898826e6f59e719c1c55a820dafb6b50f910a3f6b1006e9eded90a9d`.
Backup: `/opt/ai-short-form-content-factory-runtime-backups/detail-bcd0788`, old
worker image tag `pre-detail-bcd0788`. Pexels/Pixabay/SearXNG health all configured.
n8n remains 2.37.10 and was restarted after publication with no running executions.
NEW normal product job (HTTP 201): `9705e087-e2ee-41db-b6d5-9d9d277a089c`,
How the Panama Canal locks work / ru / 15. Immediate next step: inspect this job's
autonomous execution and candidate/reviewer evidence. Do not rescue it manually.
No MP4 or HUMAN PASS yet.

## 2026-09-07 pre-script retrieval correction — deployed, fresh job running

New job `897293fa-9627-4f09-b7e0-fc9c49562ba2` failed/script in WF02 **16295**:
`pre-script verified visual inventory 1/3`. Invocation is proven fixed: candidate
claim gateway **16298** succeeded with valid JSON, then visual review **16299**
succeeded and rejected irrelevant imagery. No final story/TTS/MP4 was generated.

Exact execution inspection: five long visual descriptions became truncated
90-character provider queries; claims 1–4 received mostly the same 2–3 Pixabay
canal photos. Reviewer rejected those for diagram/gate/basin targets; only claim
1 retained a verified visual. This is retrieval/acceptance-contract conflation,
not a reason to weaken semantic verification or lower the required inventory.

Correction: candidate claims explicitly contain a validated 2–8 word, <=90 character
`search_query_en`; pre-script provider retrieval uses it while preserving the full
`visual_target` and every existing reviewer/uniqueness gate. No post-script search,
manual rescue, topic-specific query or asset reuse is introduced.

Verified: 56/56 static regressions PASS, fresh PostgreSQL (21 SQL statements) PASS,
real n8n 2.37.10 import of 8 workflows PASS, actual expression invocation regression
PASS for all four structured calls, worker build PASS.
Deployed source `077cc32` to WF02 and media-worker. Native VPS image:
`sha256:a3e84a103a8cc4ec8a51cd375f1643580a7f0526f4d92f58bc1a19ba69ca8e5a`.
WF02 current/published definitions match source; n8n remains 2.37.10.
The existing production Compose omitted SEARXNG_URL despite the configured old
container. Recreating worker exposed this drift before any job submission. Added
the already-committed default SEARXNG_URL to production Compose; health now reports
all three providers configured and a real research request returned HTTP 200 with
20 results. Backup/source staging: `/opt/ai-short-form-content-factory-runtime-backups/query-077cc32`;
old image retained as `ai-short-form-content-factory-media-worker:pre-query-077cc32`.

NEW normal WF01 job (HTTP 201): `47c59975-2f39-46e4-9e54-f5816a944998`,
How the Panama Canal locks work / ru / 15. Next: inspect its autonomous execution
and actual returned inventory, then continue to exact MP4 or a systemic failure.
Failed `897293fa...` remains untouched. Overall MP4 quality is unproven.

## 2026-09-06 invocation correction — deployed, fresh E2E running

Continuation base: `086830485d986aa64e77af980f6ef6a4b8206de5`, tree
`3cdf959ede9af8caec65b63016380a1bb5dc56c6`. Inventory-first is deployed; older
pre-production statements below are historical. Production n8n is **2.37.10**;
Compose and import tests are now pinned to that actual version, without downgrade.
WF02/WF03 runtime nodes/connections/settings matched this base before correction.

Latest product job `f7ef9f04-c6db-47af-b90f-1d6747ce6f2f` (Panama Canal locks,
ru, 15) failed/script at Draft Candidate Claims in WF02 execution **16291**.
Gateway 16292/16293 succeeded for topic resolution, but no gateway invocation
was created for the claim draft. The failed job is not retried or manually edited.

Exact cause reproduced with the live 2.37.10 Expression evaluator: compact nested
JSON schemas contain `}}`, which the expression parser treats as the expression
terminator. Normal JavaScript compilation and workflow import do not catch this.

The four structured model calls now build their payloads in Code nodes and pass
only `={{ $json.model_request }}` to HTTP Request. Claim generation, visual review,
final story and duration rewrite share this invocation contract. Error outputs
remain connected to their existing failure handlers. Inventory-first, reserved
assets, native Edge timing and no-manual-rescue rules remain in force.

Verification: 55/55 static regressions PASS; real 2.37.10 evaluator reproduces the old
syntax error and resolves all four corrected request bodies; fresh PostgreSQL
prepares 21 SQL statements and exercises staged writes; n8n 2.37.10 imported all 8 workflows; media-worker build PASS.
Correction committed/pushed as `fae27ad` and deployed to WF02/WF03 only.
Both current and published-history nodes/connections match that source; active
versions match. Product n8n was restarted after publication with no running jobs.
Worker was not replaced for this workflow-only correction.

A NEW normal WF01 job was submitted (HTTP 201):
`897293fa-9627-4f09-b7e0-fc9c49562ba2` — How the Panama Canal locks work / ru / 15.
It is running autonomously; no creative intervention or old-job retry is allowed.
Next: inspect its executions, confirm claim drafting invokes V4 Model Gateway,
then follow through to MP4 or capture/fix a systemic failure and submit a new job.
No final MP4 or human acceptance has been obtained for this correction yet.
Targeted rollback export:
`/opt/ai-short-form-content-factory-runtime-backups/pre-invocation-20260906T205157Z`.
Production inventory-first rollback backup remains
`/opt/ai-short-form-content-factory-runtime-backups/pre-inventory-first-20260906T194034Z`.

## 2026-09-06 inventory-first implementation — pre-production verified

The Codex audit direction has now been implemented in the existing n8n product path on preservation branch `continuation/codex-recovery-20260906`. This is not a new product or a V6 side architecture.

Current implemented causal order:

`topic -> evidence-grounded resolution/research -> candidate factual claims -> actual still-image discovery -> preview fingerprinting -> actual-image multimodal verification -> perceptual dedupe/reservation -> final supported story units -> one continuous Edge narration -> provider word timings -> frozen-unit duration rewrite if needed -> reserved-asset execution -> render -> exact artifact hash -> human review`

Systemic changes now present in source:

- WF02 reserves unique verified visual assets before final narration is authored and persists `story_package` version `inventory-first-story-v1` with explicit claim/evidence/unit/asset bindings;
- WF03 consumes native Edge word boundaries and preserves frozen claim/evidence/asset identity across bounded duration rewrites; late visual rebind is removed;
- WF04 no longer performs post-script visual discovery/recovery/beam assignment and instead downloads, stores and re-fingerprints only the assets reserved before narration;
- WF05/render accepts variable semantic-unit counts, preserves the whole still image in 9:16 composition instead of destructive central foreground crop, and persists SHA256 identity of the exact final MP4;
- media-worker exposes stored-visual fingerprint verification and inventory-first render/artifact contracts;
- JSON-producing model calls in candidate-claim generation, final story generation and duration rewrite now explicitly request structured JSON schemas;
- WF02 error-output routing is explicitly enabled and planner failure recovery can recover the job ID from stable upstream context, so model/validation failures must persist a failed job rather than leave `created/intake` stranded.

Verification after the latest structured-output/failure-persistence correction:

- 55/55 non-live static regressions PASS (13 Python + 42 Node; the explicit environment-dependent real-provider dry run is excluded from this count);
- fresh PostgreSQL contract PASS with all current workflow SQL statements prepared and staged writes exercised;
- actual n8n 2.33.3 import contract PASS for all 8 workflow exports;
- clean media-worker Docker build PASS; current pre-deploy image `sha256:8017fba74dadb5d0ccee338e358a2586a96a8ab088b8bd6de0bfbc5565e334b9`;
- component probes previously verified SearXNG research, pre-script inventory, stored-file perceptual identity and native Edge word timing.

The first clean isolated n8n product-input attempt exposed the general missing structured-output/failure-persistence contract described above; that defect is fixed and regression-covered. A second fully isolated n8n E2E is currently blocked by environment credential injection restrictions in the server control layer, not by a discovered product-code failure. Do not treat that harness limitation as product acceptance.

**Production has not yet been changed by this inventory-first implementation. Overall product quality remains unproven until a fresh normal production job is run with zero manual rescue and the exact resulting MP4 is watched by the user.**


## Current factual audit (2026-09-06; supersedes stale state claims below)

Read `docs/V5_SYSTEM_AUDIT_20260906.md` for the verified runtime, systemic causes,
completed engineering work and exact unfinished next steps. At audited HEAD
`b909a25`, the seven main workflows and running worker files match GitHub; WF01
is active. The actual pipeline is script-first with synthetic within-audio timing
and static central photo crops. The former ARCHITECTURE_V5 described an intended
asset-first path, not deployed behavior. Overall product quality remains unproven.

Current work has not changed production or submitted a new product job. Fresh DB
bootstrap, review API source and executable integration checks are being repaired
before implementing the inventory-first causal order. Historical entries below
are retained as evidence, not concurrent instructions or verified current state.


## 2026-09-06 recovered post-audit engineering state

The interrupted Codex session had pushed its reproducibility/word-timing foundation
as commit `36c76437...`, but later chat-described edits were not in GitHub. Those
missing edits have been reconstructed in an isolated worktree and verified: WF03
uses exact Edge provider word timestamps, media-worker receives Pexels/Pixabay
configuration, and research uses configured SearXNG rather than a Wikipedia-only
endpoint. Full details and verification evidence are in `docs/V5_SYSTEM_AUDIT_20260906.md`.
Production remains unchanged. The next systemic implementation target is still the
inventory-first story contract; do not resume late post-script visual recovery as
the product architecture.

## Mandatory pre-action gate

Before any meaningful action, code change, render, test, architecture decision, dependency addition, or direction change, **read `docs/OPERATOR_EXECUTION_RULES.md` first**, then read this file.

The current primary project risk is operator/assistant decision drift: changing direction without proof, handcrafting proofs, inventing blockers, or replacing the required n8n product with side architectures. Do not repeat those patterns.

## Product definition

The product is a **free/self-hosted n8n orchestrator**.

External input:

`topic + language + requested duration`

Required n8n-controlled path:

`input -> research -> free/licensed visual inventory -> visual verification/ranking -> story/script -> one continuous narration -> exact-audio timing -> autonomous edit plan -> render -> QA -> exact-artifact human review`

Supported durations: `15 / 30 / 45 / 60` seconds.

Output: vertical `9:16` short-form MP4.

No mandatory paid-per-video API dependency is allowed.

## Human-rejected baseline

First real n8n-orchestrated 60-second proof:

- job: `d23617c3-1311-43c1-97e0-c6504522bd77`;
- topic: `Почему листья меняют цвет осенью`;
- language: `ru`;
- requested duration: `60 s`;
- rendered duration: `59.064 s`;
- technical state: `review_ready`;
- human state: **HUMAN FAIL**.

General defects found:

1. **visual policy defect** — WF04/media-worker was biased toward stock video, producing long/generic moving footage instead of using the much larger relevant still-image inventory;
2. **narration defect** — current WF02 deterministic extractive narration can sound encyclopedic and expose source artifacts instead of producing natural spoken short-form text.

Neither defect may be repaired manually for one topic.

## Photo-first systemic correction

Durable records:

- `docs/V5_N8N_PHOTO_FIRST_MEDIA_POLICY_20260904.md`;
- `docs/V5_N8N_PHOTO_FIRST_PROOF_20260904.md`.

Default visual inventory is now still-image first:

- Pexels Photos;
- Wikimedia Commons / canonical Wikipedia media;
- Pixabay Images;
- additional free/publicly licensed image providers as they are integrated.

Still images are normal production assets and must be turned into dynamic video through purposeful crop/reframe, pan/zoom, detail crops, masks, layouts, callouts, parallax, maps/documents/diagrams or other motion treatment.

Video is optional and secondary. A clip may be selected only when the segment is genuinely motion-led, metadata matches both subject and segment target, local visual ranking says it is more relevant than the best still for that segment, and the selected clip is short (currently max four seconds).

Generic moving footage is a fail.

The first photo-first rerun, job `4f6816b2-38aa-4fe8-8e8d-fbf84a951818`, exposed a general DB schema mismatch: `visual_shots_kind_check` did not allow the new `factual_image` / `context_video` kinds. Migration `017_photo_first_visual_kinds.sql` fixed the shared schema contract.

## Current exact review artifact

Second photo-first n8n rerun:

- job: `8d82fc3e-b8ad-4ac0-8ef5-f61190e3a904`;
- same input: `Почему листья меняют цвет осенью`, `ru`, `60 s`;
- status: `review_ready`;
- rendered duration: `59.064 s`;
- format: 1080x1920, 30 fps, H.264 + AAC;
- exact review copy: `/opt/ai-short-form-content-factory/studio/bakeoff/n8n-photo-first-leaves-ru-60.mp4`;
- SHA256: `0b007fdde0a15994c7df7b1de0d7054fe136755d08c21a6a03f566c3c3e13850`.

Automatic selected-media composition:

- Pexels Photos: 4;
- Pixabay Images: 3;
- Wikimedia Commons images: 3;
- video clips: 0.

No clip/image was manually selected after submission.

Acceptance state: **machine_rendered / review_ready only**. This exact artifact is not `human_approved` until the user watches and explicitly accepts it.

## What counts as a valid proof

A proof starts by supplying only `topic + language + duration` to n8n.

After that there is zero manual creative intervention.

Invalid proof methods include:

- manual clip/image selection;
- manual query rescue for one topic;
- manual scene/edit-plan repair;
- looping/reusing assets to fill duration;
- speech-speed manipulation to force duration;
- bypassing n8n with a handcrafted direct/CLI path;
- calling machine success a product success before explicit HUMAN PASS.

## Immediate gate

1. user watches exact photo-first artifact `n8n-photo-first-leaves-ru-60.mp4`;
2. record HUMAN PASS/FAIL from that exact file;
3. if the visual direction passes, fix the separate general natural-narration defect in WF02 without topic-specific text;
4. rerun the same n8n path and repeat on materially different topics/languages after HUMAN PASS.

Do not create a separate product architecture. n8n remains the orchestrator.

## Topic-resolution HUMAN FAIL and systemic correction

Job `16c23aed-4370-46a4-b135-63f8b6af47c6` (`Ходор / ru / 30`) reached `review_ready` with `fact_primary_title=Mikhail Khodorkovsky` and measured voiceover `28.728 s`. This is HUMAN FAIL: the intended subject was the fictional character Hodor.

Production evidence identified a general WF02 ordering defect: one model guessed a canonical subject without candidates or search evidence, after which research queried only that guess. The resulting evidence set could confirm but never correct the initial mistake.

The corrected WF02 contract is now `candidate interpretations -> per-candidate discovery -> evidence-grounded comparison -> structured resolution -> resolved-subject factual research`. Migration 018 persists the structured result in `jobs.topic_resolution`. Durable record: `docs/V5_EVIDENCE_GROUNDED_TOPIC_RESOLUTION_20260904.md`.

WF03 continuous voice and exact measured-duration fit, WF04 photo-first policy, and WF05 rendering remain unchanged. The correction is not accepted until cross-topic regressions pass, fresh n8n E2E jobs complete where practical, and the user reviews the exact resulting MP4.

## 2026-09-04 systemic rebuild after cross-topic failures

The previous deterministic/extractive WF02 path is no longer the active narration architecture.

Current n8n-controlled narration path:

`topic in any input language -> semantic intent -> SearXNG research -> grounded AI narration strictly in selected output language -> structured validation -> one continuous natural-rate TTS -> exact measured duration -> bounded script rewrite/re-synthesis when needed`

General fixes completed:

- removed lexical/Wikipedia entity matching as the basis of topic understanding;
- removed deterministic encyclopedia-excerpt narration as the primary writer;
- selected output language is authoritative and independent of input-topic language;
- research evidence supports/audits narration instead of being concatenated into narration;
- exact TTS duration is authoritative; word-count duration prediction is advisory only;
- natural speech rate remains unchanged; timing is corrected by rewriting the script, not tempo manipulation;
- Edge Read Aloud transport budget was increased to a bounded 120-240 seconds and the n8n HTTP timeout aligned to 270 seconds;
- WF02 structured-output parsing now safely tolerates the model's bounded `used_source_ids: [S1,S2]` formatting defect without evaluating arbitrary text;
- visual candidate identity is provider-scoped (`provider + provider_asset_id`) across Pexels/Pixabay/Wikimedia-style inventories, preventing cross-provider numeric-ID collisions;
- photo-first policy remains mandatory; video remains secondary and is admitted only for motion-led, semantically stronger matches.

Latest autonomous end-to-end evidence, all launched only with `topic + language + duration`:

1. job `1bf8089f-eecf-4b93-83f4-a1a5862a4044`
   - topic input: `why is the sky blue`
   - selected output language: `ru`
   - requested: `30 s`
   - measured voiceover: `27.360 s`
   - status: `review_ready`
   - final MP4: `jobs/1bf8089f-eecf-4b93-83f4-a1a5862a4044/render/final.mp4`

2. job `6cf62378-51be-4694-9e4e-5f096a7f1769`
   - topic input: `how does a refrigerator work`
   - selected output language: `uk`
   - requested: `30 s`
   - measured voiceover: `31.152 s`
   - status: `review_ready`

3. job `656656f1-5f75-4a8e-a5ef-bf8bd1608e16`
   - topic input: `почему извергаются вулканы`
   - selected output language: `pl`
   - requested: `30 s`
   - measured voiceover: `29.160 s`
   - status: `review_ready`
   - final MP4: `jobs/656656f1-5f75-4a8e-a5ef-bf8bd1608e16/render/final.mp4`

These are machine-rendered cross-topic proofs only. None is `human_approved` until the user watches the exact artifact and explicitly accepts it.

## Current gate

The user should now test the current workflow from Studio with arbitrary topics/languages/durations. Any HUMAN FAIL must be handled as a general defect from the exact artifact; no topic-specific rescue or manual media selection is allowed.

## Regression gate

Static workflow regression suite: `10/10 PASS` after the systemic WF02/WF03/WF04 rebuild.

The suite covers cross-language semantic intake, selected output-language authority, grounded research-backed narration, advisory-only word budgeting, exact measured TTS duration, bounded natural-rate rewrite/re-synthesis, provider transport budget, short canonical titles, provider-scoped visual identity, and local media-worker module completeness. Node syntax checks also pass for the media-worker entry point and new support modules.

## Evidence-grounded topic-resolution production result

Fresh production regression after migration 018 and the WF02-only deployment resolved all seven required/diverse classes correctly and produced scripts in the selected output languages. Five jobs reached `review_ready`; Hodor and volcano were correctly rejected later by unchanged WF04 relevance/assignment gates. Topic resolution is machine-proven cross-topic; rendered files still require HUMAN PASS/FAIL.

The exact job matrix, consumed failures, decision contract, and deployment corrections are recorded in `docs/V5_EVIDENCE_GROUNDED_TOPIC_RESOLUTION_20260904.md`.

## 2026-09-05 visual relevance HUMAN FAIL

The user rejected all five topic-resolution `review_ready` MP4s. They are HUMAN FAIL, not quality proof. Inspection showed the runs were already image-first; the defect was acceptance of irrelevant images through metadata bonuses despite near-zero local visual scores, compounded by mixed-language visual queries because WF02's English visual concepts were not persisted.

Migration 019 and the WF02/WF04/media-worker correction persist and consume grounded English visual queries, rank against a concise English subject/target, reject sub-floor semantic matches before metadata utility, and keep video secondary to an eligible still. Missing relevant media must fail closed. Durable record: `docs/V5_PHOTO_RELEVANCE_HUMAN_FAIL_20260905.md`.

The correction is deployed. Fresh autonomous job
`e3d9016d-cefc-4158-aeca-075dab852c41` (`как работает холодильник`, `ru`, `30`)
failed closed at visual segment 6 because no candidate exceeded the `0.01`
semantic relevance floor. It produced no `visual_shots` and no MP4. This proves the
deployed gate blocks unrelated filler; it does not yet prove sufficient relevant-
photo coverage or human-acceptable output.

## 2026-09-05 visual selector rollback decision

The lexical-metadata plus local SigLIP selector is rejected as a production visual
quality authority. The exact Hodor render selected a random door, snow, an insect
micrograph, an unrelated portrait, and a scientific figure. Five of eight selected
shots had `target_metadata_overlap=0`; metadata utility overrode near-zero visual
scores. Subsequent absolute-threshold calibration alternated between irrelevant
media and incomplete jobs and is not a viable product mechanism.

WF01 intake is paused while WF04 is replaced by multimodal review of the actual
candidate previews. The local ranker may remain only for perceptual hashes and
ordering; it must not independently approve semantic relevance. Production intake
must not resume until the exact rendered MP4 is watched before delivery.


## 2026-09-05 final-narration visual rebind + bounded model recovery

Fresh production matrix after deploying WF02 commit c6a14a7:

- 4174878b-4662-433d-9ff2-ff090cf77ac5 — как работает гидроэлектростанция, ru, 15 s — WF03 failed during the second duration-fit rewrite;
- 4c864c59-20bf-41fe-b562-b20f5c3571a2 — How Alexander Fleming discovered penicillin, pl, 30 s — reached review_ready, measured voiceover 29.712 s;
- 75a41742-0e38-48c4-a9fb-d8f4320c89f6 — как образуются облака и дождь, uk, 60 s — WF03 failed during the first duration-fit rewrite.

Execution inspection proved the apparent duration rewrite model returned invalid JSON failure was masking upstream Gemini free-tier HTTP 429 responses. The model gateway had no bounded recovery and WF03 received an empty object after the child workflow failed. This is a general provider-availability defect, not a topic-specific script defect.

A second systemic defect was also proven: c6a14a7 correctly binds visual queries to the final WF02 validator narration, but WF03 may still rewrite narration after exact TTS measurement. Therefore any job with script_fit_passes > 0 can otherwise carry stale visual queries into WF04 even though they were valid for the pre-TTS script.

Current correction under test:

- V4 model gateway has one bounded retry (maxTries=2, waitBetweenTries=60000) and remains time-limited;
- callers that use the gateway have bounded timeouts long enough to accommodate that single retry;
- if a duration-fit model call remains unavailable and the narration is too long, WF03 can make a deterministic punctuation-boundary shortening from the already-grounded narration while preserving evidence provenance; no speech-speed manipulation is introduced;
- after exact TTS is accepted, any job whose narration changed in WF03 must regenerate exactly 6/10/14/18 English visual queries from the actual final timed narration beats, then persist those queries before WF04 starts;
- jobs with script_fit_passes = 0 keep the c6a14a7 validator-bound visual query inventory and do not spend an extra model call.

Regression coverage added for bounded model recovery, deterministic duration fallback, and final-narration visual rebinding. Production deployment is not allowed until the complete regression suite passes, changes are committed and pushed, then the exact new MP4s are inspected.

## 2026-09-05 production HUMAN FAIL: spoken slash + unreviewed visual fallback

Fresh production jobs after commit `3af1b99c2ccaf131920cb664f8ee0ab6215dc182` exposed two additional general defects.

1. Job `043c10a6-4d9d-4948-bc0d-64237429e749` (`как работает гидроэлектростанция`, `ru`, `15`) reached `review_ready`, but the persisted narration contained literal formatting separators such as `? /`, `, /` and ` / ` between words. The TTS therefore audibly pronounced the slash. The defect is not provider-specific: unsafe formatting was allowed to enter the spoken narration contract before TTS.

2. The same hydro render and job `cc1141d8-03a3-4825-ac96-281812737a7a` (`How Alexander Fleming discovered penicillin`, `pl`, `30`) showed apparently random second images inside semantic segments. Execution evidence proved the multimodal reviewer normally approved one visibly relevant candidate per segment while each segment requested two shots. `Require Multimodal Visual Selection` then appended `localFallback` candidates that the multimodal reviewer had not approved; because `visual_review_candidates` retained the full local pool, some fallback candidates had not even been shown to the reviewer. Examples include a multimeter for a hydroelectric generator beat and a newsroom/typewriter photo for an Alexander Fleming laboratory beat. This violated the requirement that each displayed image be specifically approved for the current narration.

Systemic correction now under regression:

- WF02 final narration removes whitespace-delimited formatting separators (`/`, `|`, arrows) before persistence and both writing/validation prompts explicitly forbid them in spoken prose;
- WF03 fails closed if unsafe spoken separators somehow reach TTS, and duration rewrites apply the same speech-safe normalization before rebuilding support provenance;
- WF04 exposes only candidates actually shown to the multimodal reviewer as eligible candidates;
- WF04 requires at least `planned_shot_count` model-approved images for every segment and forbids the previous unreviewed `localFallback` path;
- if the reviewer cannot approve enough relevant images, the segment now fails closed instead of silently filling the timeline with plausible/random media.

Regression status before GitHub sync/deploy: `20/20` Node tests + `11/11` Python tests PASS, JSON validation PASS, `git diff --check` PASS. Production has not yet been redeployed with this correction. Existing `review_ready` artifacts above remain HUMAN FAIL.

## 2026-09-05 exact-beat visual sourcing correction under final verification

Fresh production evidence from job `fd510f8e-21b3-4f2d-a992-2cc5f21e81a0` proved two independent general defects.

1. Narration formatting leakage: the model had emitted `/` as a visual/beat separator inside spoken Russian text and WF02 persisted it unchanged. TTS therefore literally pronounced the slash. The deployed speech-safety correction removes and rejects standalone slash/pipe-style formatting separators before TTS and after duration rewrites. The fresh 15 s rerun produced clean narration with no slash and measured `14.256 s`.
2. Timed visual discovery was not actually beat-authoritative. For a final beat whose exact query was `modern residential house exterior at night with glowing interior lights`, the media worker prefixed the canonical topic, producing an overlong provider query; Pixabay returned HTTP 400. The timed candidate pool then still contained generic topic-level hydroelectric imagery, which allowed topic-context pictures to be selected for a homes/electricity beat. In addition, semantic visual segmentation could merge multiple final narration beats and attach only the first beat query to the merged segment.

The new systemic correction keeps the final timed narration as the only visual chronology authority:

- one visual segment per accepted final narration beat (`narration-beat-visual-segments-v4`);
- query N binds one-to-one to final beat N;
- each beat >= 1.8 s plans two distinct full-screen stills, preserving the multiple-image-per-scene contract;
- timed searches use the exact English beat query without prefixing the overall topic;
- provider query length is bounded before transport;
- timed candidate pools do not mix generic topic-level Pixabay/Pexels/Commons stock or canonical-article media;
- Pexels uses the Photos API, not stock-video search;
- Commons, Pixabay and Pexels requests run concurrently per beat, with bounded concurrency across beats and existing per-provider timeouts;
- final multimodal review may select only images actually shown for that exact beat; topic anchors and unreviewed local fallback are forbidden; insufficient visible matches fail closed.

Regression coverage is updated and a new real-path discovery regression covers exact beat queries, provider query bounds, Pexels Photos, no topic-level timed stock and bounded concurrency.

Real-provider dry-run against the exact failed 60 s cloud/rain context (`18` final beats / `18` queries) completed in `5.726 s`, returned `18` beat-aligned visual segments / `36` planned still shots, and reported `0` provider errors. Every segment used its exact final beat query; topic-level base provider counts were all zero. This is discovery evidence only, not HUMAN PASS. The correction still requires GitHub sync, production deploy, fresh E2E renders and exact MP4 review.

### 2026-09-05 bounded multimodal review batching correction under test

Fresh post-deploy E2E matrix after exact-beat visual discovery exposed a separate bounded-review defect:

- `8dbc666c-3d00-4cfb-a15b-f168a6313895` — hydroelectric plant / ru / 15 — `review_ready`, measured voice `13.824 s`;
- `81394bf5-b345-4565-82a4-13d4cc16dd76` — Alexander Fleming / pl / 30 — failed because segment 1 received only `1/2` model-approved relevant stills;
- `4278786c-a243-4e0e-a37e-d3e2226b8434` — clouds/rain / uk / 60 — failed before review because the single multimodal request exceeded its bounded 80-item input budget.

The failures have one general cause: one whole-video multimodal request forced candidate exposure per segment to shrink as beat count grew, and at 18 beats the fixed lower bound of two candidates per segment made the request mathematically exceed the 80-item cap. The 30 s case was also starved to only three reviewed alternatives per beat, so failing closed after one relevant choice was expected even though more exact-query candidates existed upstream.

Correction under test: split final visual review into deterministic batches of at most six exact narration beats. A six-beat batch can show up to six actual still candidates per beat and remain within the 80-item request cap; smaller batches expose up to 7-10 candidates per beat. The model may approve up to four visibly exact candidates per beat, never fewer than the required shot count when enough exact matches exist. All approved alternatives remain model-reviewed and the global assignment still forbids asset reuse. No topic-level or unreviewed fallback is reintroduced.

Static Node regression now proves 18 beats => exactly three bounded review batches, complete segment coverage, <=80 inputs per model call, multi-batch response reconstruction, fail-closed behavior, and global no-repeat assignment compatibility. Production deployment remains blocked until the full regression suite, GitHub sync, and fresh E2E reruns pass.

### 2026-09-05 bounded visual-query recovery + measured duration controller under test

Fresh production matrix after `820fcb4d78ebb060fb4d938ab40d51661debb5f6` exposed two separate systemic gaps rather than a reason to weaken relevance gates:

- `3a4f8483-03b5-47a3-81dd-8844445157aa` (`How Alexander Fleming discovered penicillin`, `pl`, `30`) failed closed because exact stock search for `Alexander Fleming historical portrait` produced same-name but wrong entities; the actual-image reviewer correctly approved `0/2` for beat 1.
- `310f8fae-2d74-4f54-871e-f1375fa71ea1` (`как образуются облака и дождь`, `uk`, `60`) failed closed on beat 18 because `water cycle diagram showing evaporation condensation and precipitation` produced mostly generic rain/condensation photos instead of an explanatory water-cycle diagram.
- `c7cf63b2-3712-4c36-b375-613ad97aa8a2` (`как работает гидроэлектростанция`, `ru`, `15`) measured `20.808 s -> 11.568 s -> 13.272 s`; the final result missed the accepted lower bound by `0.195 s` and the old controller failed immediately after two rewrites.

Systemic correction now under regression/GitHub gate:

- timed visual discovery still searches the exact final-beat query first;
- when exact provider results do not supply enough query-anchored candidates, discovery may issue exactly one compact recovery query that preserves the named entity/mechanism and media cue; it may not fall back to the overall video topic;
- the recovery path remains bounded to the same free providers/timeouts and all recovered images still require actual-image multimodal approval;
- real provider evidence for the failed classes now exposes correct Wikimedia candidates such as Alexander Fleming portraits and water-cycle diagrams instead of accepting same-name stock noise;
- WF03 now preserves bounded measured TTS history and allows at most three rewrites;
- when measured attempts bracket the target duration, the next requested word count is computed by interpolation between the closest measured under-target and over-target attempts instead of another blind proportional jump;
- exact TTS measurement remains authoritative and speech rate remains unchanged;
- migration `021_expand_script_fit_pass_limit_to_three.sql` raises only the bounded persistence limit from two to three rewrites.

Current static regression gate: `23/23` Node + `11/11` Python PASS, workflow JSON PASS, `git diff --check` PASS. A real-provider discovery/rank dry-run on the failed 30 s and 60 s contexts also passes with 10 ranked candidates available per exact beat. These are engineering proofs only. GitHub sync, migration/deploy, fresh autonomous 15/30/60 renders, and exact MP4 review are still required.

### 2026-09-05 post-b6f299 production failures and bounded correction

Fresh autonomous production matrix on `b6f299ed1af3d9e7a39bb4dedfb9efa3f2681f81` exposed two remaining general defects:

- `4183cb81-c918-41a8-80ef-b68df92053d2` — hydroelectric plant / `ru` / `15`: WF03 measured `21.168 -> 13.248 -> 13.104 -> 12.816 s` and failed after the bounded third rewrite. The accepted lower floor is `13.467 s`; several attempts missed it by only fractions of a second.
- `b338430e-b371-4ca2-a1ce-0076641aa1f6` — Fleming / `pl` / `30`: after `39.336 -> 26.856 s`, the next duration-rewrite model call was unavailable. The current result was only `0.111 s` below the accepted lower floor `26.967 s`, but deterministic textual expansion is intentionally not used when the model is unavailable.
- `721b1fbc-226c-499c-95e1-d434dcddf13c` — clouds/rain / `uk` / `60`: voiceover passed at `58.656 s`; WF04 failed closed on beat 16. Execution evidence showed the multimodal model could identify correct `Water Cycle` diagrams, but the bounded pre-review exposure pool had shown it unrelated `cycle` matches instead because correct phrase-level candidates were displaced before review.

Systemic correction now under GitHub/deploy gate:

- normalized continuous voice audio may add only a bounded natural end pause, max `0.4 s`, and only when the measured narration is already within `0.4 s` below the accepted lower duration floor; speech rate/tempo remain unchanged and materially short narration still goes through rewrite/fail;
- both Gemini-stored and Edge-fallback continuous audio use the same bounded tail-normalization helper;
- compact visual recovery canonicalizes media cues such as `schematic` to `diagram`, so a target such as `schematic diagram of the global water cycle` reduces to a subject-preserving query such as `water cycle diagram`, never to the overall video topic;
- WF04 bounded exposure now prioritizes exact subject/target phrase matches before multimodal review, so correct candidates are not displaced by lexical coincidences such as unrelated uses of `cycle`;
- the actual-image reviewer remains authoritative and fail-closed; no unreviewed fallback or weakened relevance gate is reintroduced.

Verification before commit: `25/25` static Node tests + `11/11` Python tests PASS, workflow JSON PASS, `git diff --check` PASS. A real-provider discovery/rank dry-run on the previously failed Fleming and cloud/rain contexts also passes with `10` ranked candidates per beat and no provider errors. Production deployment and fresh autonomous 15/30/60 MP4 review are still required.

### 2026-09-05 production rank-timeout root cause + fingerprint-only correction

Fresh autonomous production matrix on commit `706d5badf7279010973506ef4705c4331e7cb715` reached exact-duration voiceover but all three jobs failed in WF04 before render:

- `f94e5fd5-1b6f-4551-8a38-c0f25d745853` — transformer / ru / 15 — voice `16.392 s`; rank segment 1 timed out;
- `d0cfdc93-508b-4490-a84f-c7ba25f735f6` — Marie Curie / pl / 30 — voice `29.808 s`; rank segments 4,6,7,8,9 timed out;
- `592c44ea-64d9-44c7-9bb0-347b21de05f2` — aurora / uk / 60 — voice `60.288 s`; rank segments 9,13,14,18 timed out.

Execution inspection proved the final `received=... expected=...` messages were secondary. `Rank Eligible Visuals` sent one HTTP request per exact beat while the media worker serialized every SigLIP inference behind one global promise chain. Later requests waited behind earlier segments until n8n's 120 s HTTP timeout. `Attach Rank Results` then routed failed items to its error output while successful items continued, so the main branch silently lost segments and only failed later with an incomplete timeline.

Systemic correction under test:

- local SigLIP is removed from the critical WF04 rank path; it had already been rejected as semantic relevance authority and is no longer needed there;
- `/visual/rank` now performs only bounded preview retrieval + perceptual hashing, preserving the planner's deterministic candidate order; actual-image multimodal review remains the sole semantic approval authority;
- preview transport has a maximum of two attempts for transient 429/5xx/transport failures, six global fetch slots, and the existing 10 s per-attempt timeout;
- WF04 preserves expected segment cardinality on every fingerprint item and turns any remaining fingerprint failure into one explicit pre-review failure instead of silently dropping that beat;
- the rank HTTP node itself has at most two attempts; there is no unbounded retry loop;
- selection provenance is renamed to `multimodal_exact_beat_shot_beam_v4`;
- the repository media-worker Docker/package build contract is synchronized with the actual production runtime so a GitHub checkout can build the worker reproducibly.

Real stress proof against the exact latest 15/30/60 contexts: discovery produced `6 + 10 + 18 = 34` exact-beat fingerprint requests. All 34 were fired concurrently at the patched worker and completed in `13.228 s` total; the slowest single request was `13.218 s`, all returned at least one fingerprinted candidate, and no request approached the 120 s n8n transport bound. This is engineering evidence only; fresh production E2E MP4s and exact-artifact review remain required.


### 2026-09-06 hosted provider failover + global no-repeat recovery under GitHub gate

Fresh runtime inspection after rollback HEAD `8ed8a080f8feacedc57c351f0b127d4847045b7b` reconfirmed that production contains only PostgreSQL, n8n and media-worker; there is no Ollama/model-worker runtime. The active V4 model gateway and WF04 runtime exports were semantically equal to the GitHub HEAD before this correction.

Production DB also reconfirmed the two independent blockers:

- `a1155771-4a8d-4a6d-8739-806ef557340c` and `fb1267de-a814-4dd7-b4e5-b0690c6e54b7` failed because the final visual-rebind model was unavailable;
- `7a9151e5-7064-49db-80dc-43e2ad1d8e79` reached a complete 18-beat visual review but global all-unique assignment failed at the final shot.

Hosted-provider research and live VPS probes show that Kilo Gateway free models are zero-cost but limited to 200 free requests/hour/IP, and individual upstream free routes can still return their own 429/503 capacity failures. `kilo-auto/free` is text-only in the current model catalog, so it cannot replace the required multimodal path. `stepfun/step-3.7-flash:free` currently advertises `text+image -> text` and has returned successful anonymous text and real-image responses from the VPS, but also exhibited intermittent upstream capacity failures. Therefore it is not accepted as a sole production provider.

Systemic provider correction now under GitHub gate:

- V4 Model Gateway keeps the existing n8n webhook contract;
- anonymous Kilo `stepfun/step-3.7-flash:free` is the first zero-cost text+vision provider;
- Kilo failure, empty output or upstream capacity failure falls through immediately to the existing independent Gemini provider;
- the previous 60-second sleep/retry behavior was removed; each provider attempt is time-bounded and the provider chain is finite;
- provider provenance/attempts are returned with the normalized result;
- no Ollama, model-worker, Mac model server or local LLM dependency is introduced.

Systemic WF04 correction now under GitHub gate:

- after actual-image review, a deterministic bipartite feasibility check detects whether globally unique perceptual-cluster assignment is possible before the final beam assignment;
- only beats in the proven conflicting component enter recovery;
- each conflicting beat receives exactly one additional exact-target provider search;
- every candidate already considered in the first actual-image review is excluded from that search;
- new candidates are perceptually fingerprinted, then their real images are shown to the same multimodal reviewer;
- only newly reviewer-approved candidates are merged into the approved pool;
- the existing global all-unique assignment is then attempted once more; if it is still impossible, WF04 fails closed;
- no image/cluster reuse, unreviewed fallback, topic-level rescue, or SigLIP semantic authority is reintroduced.

Verification before commit: workflow JSON parse PASS; Python regressions `11/11` PASS; static Node regressions `30/30` PASS including new exact conflict-search and global no-repeat recovery tests; `git diff --check` PASS; no tracked `work/`; modified runtime/workflow code contains no Ollama/model-worker dependency; media-worker builds reproducibly from this checkout; both modified workflows import successfully into a clean n8n `2.33.3` instance. The isolated built media-worker exposes `/visual/recover-conflict`; a real Wikimedia exact-target request for `Alexander Fleming portrait` returned 18 new candidates while keeping semantic approval outside discovery. Production deploy and fresh autonomous 15/30/60 E2E renders remain blocked until commit/push and GitHub-source verification complete.


### 2026-09-06 WF01 GitHub/runtime orchestration drift correction

Pre-E2E reconciliation found a pre-existing source/runtime drift in WF01. The active production WF01 and production filesystem both contain the same seven-node orchestration core: after the job row is inserted, `Start Script Planning` asynchronously invokes WF02 `TJfA4ZYUEKSTad6k` with only the persisted `job_id`, while the webhook returns HTTP 201 without waiting for the full generation chain. Their canonical core SHA is `065a372f16e865e502769d8bf0c344a5ad29cba1c29378bd406cbddee8239c3f`.

GitHub commit `a8ab5f2c984a517e9176b29dcc4bb101270355f9` still carried an older six-node WF01 core (`20d83db99524ea97550311095430c3746eee89fbe536c521b7ec4db777c73477`) that inserted and returned the job but did not invoke WF02. That GitHub file cannot represent the required autonomous `topic + language + duration` product path even though runtime had the correct handoff.

Correction under GitHub gate: synchronize the already-live generic WF01 orchestration contract into repository source and add a regression requiring exactly one asynchronous WF01 -> WF02 handoff with `job_id`. This is source/runtime reconciliation, not a topic-specific behavior change. Fresh E2E remains blocked until the corrected WF01 is committed, GitHub tree is verified, and production WF01 is republished from that GitHub source.


### 2026-09-06 fresh E2E provider completion-contract failure

After GitHub commit `a5bafcd96f69936f51439b0298c23dfc9705874e` restored WF01 source/runtime orchestration and WF01 was republished from that exact GitHub tree, fresh autonomous production testing resumed strictly through the WF01 `topic + language + duration` webhook.

Fresh RU/15 transformer job `a8ebade0-9657-46d5-9bfd-449ebfd6a7a9` completed autonomously to `review_ready`. Exact voiceover duration is 15.504 s. WF04 stored `visual_quality.pass=true` with 12 shots, 12 unique assets, 12 unique perceptual clusters, zero asset reuse and zero adjacent perceptual duplicates. WF05 rendered `jobs/a8ebade0-9657-46d5-9bfd-449ebfd6a7a9/render/final.mp4`; technical probe is H.264 + AAC, 1080x1920, 30 fps, 15.534 s, SHA256 `81d8b4134290ba888c80079f3e3a22cdb423b9efac71d4eacea01037f9566402`. This is machine completion only, not HUMAN PASS.

Fresh PL/30 Marie Curie/radium job `c2a91275-bf29-43c0-95f6-b0f2eeb9694d` exposed a new general provider-contract defect and failed closed at `script`: `evidence-grounded topic resolver returned invalid JSON [line 1]`. WF02 execution `15582` failed after V4 executions `15583` and `15584` were marked success. Exact execution-data inspection proved V4/Kilo execution `15584` returned `finish_reason=length`; `message.content` contained only an approximately 421-character prefix of the requested JSON while the model emitted a long reasoning payload. V4 incorrectly treated any non-empty Kilo content as success, so Gemini fallback was skipped and WF02 received truncated JSON.

Systemic correction under GitHub gate: Kilo output is usable only when text is non-empty and `finish_reason` is exactly `stop`. `length`, `content_filter`, tool-call or missing/nonterminal completion reasons are normalized as failed provider attempts and immediately use the existing independent Gemini fallback. The failed PL/30 job is not retried manually; a completely fresh job may be created only after this gateway correction passes regression/import/GitHub/deploy gates.


### 2026-09-06 fresh PL/30 reviewer-shortfall recovery gap

After V4 commit `c0492f97627d0d894276bebc1f14a018277d281e` was verified live (`active=true`, `versionId == activeVersionId`, and live/source canonical workflow SHA `ca2c17e99aabe2d4466f5f53952f551aa51e88e04951088e19216f72242ffe41`), fresh PL/30 job `ed6a58bb-f4a6-4dc8-a545-35c8795743d2` demonstrated the completion-contract correction on real production traffic. V4 execution `15588` received Kilo `finish_reason=length`, normalized the Kilo attempt as unsuccessful, then used Gemini successfully and returned complete valid resolver JSON. WF02 and WF03 subsequently advanced normally; exact voiceover duration reached 32.064 s.

The same fresh job then exposed a separate general WF04 defect and failed closed at visuals: `Multimodal reviewer approved 1/2 relevant images for segment 5; unreviewed fallback is forbidden`. Execution `15596` showed that the exact beat required two reviewed stills for `pure radium chloride crystals in glass vial`, while the first inventory mostly contained generic crystal/mineral representations. The reviewer correctly refused to pad the beat.

Source inspection identified the architectural gap: `Require Multimodal Visual Selection` threw immediately on any per-segment approved-count shortfall, while the existing single exact-target recovery path was reachable only after `Detect Global No-Repeat Conflict`. Therefore a segment with insufficient exact reviewer-approved images could never use the same bounded recovery already available for global uniqueness conflicts.

Systemic correction now under GitHub gate: initial multimodal review preserves only reviewer-approved candidates and records approved-count shortfall instead of admitting any fallback. Malformed or empty reviewer output remains an immediate failure. The global feasibility detector adds shortfall segments, including zero-approved pools, to the same bounded recovery set used for perceptual-cluster conflicts. Each affected segment receives one additional exact-target search excluding every candidate already shown to the reviewer; only newly fingerprinted and reviewer-approved candidates can be merged. After that one recovery round, merged reviewer-approved cardinality must meet `planned_shot_count` or WF04 fails closed. No shot-count relaxation, relevance-threshold relaxation, topic-specific query, asset reuse, unreviewed fallback, or second recovery round is introduced.

Targeted verification before the full gate: `WF04_PHOTO_RELEVANCE_GATE_REGRESSION_PASS`, `WF04_GLOBAL_NO_REPEAT_RECOVERY_REGRESSION_PASS`, and `VISUAL_CONFLICT_RECOVERY_EXACT_QUERY_REGRESSION_PASS`.

Full verification for this correction: workflow JSON parse PASS; Python regressions `11/11` PASS; Node static regressions `31/31` PASS; `git diff --check` PASS; clean n8n `2.33.3` import of WF04 PASS.

### 2026-09-06 PL/30 recovery proof + UK/60 structured-output failure

WF04 shortfall recovery was deployed from GitHub commit `5d0398b65d6c63764f24a9441c5785c190753b50` after immutable source verification. Production live/source canonical WF04 core SHA is `f8fe6b76bf92213d136ead92f2f40779fc6a25e1fc592e968e04eb968e454eef`; live workflow has 42 nodes and `active=true` with `versionId=activeVersionId=379a5d0e-b955-444e-8951-1f3297915bc8`.

Fresh PL/30 job `d278b778-4aea-468d-b78e-aa03e994fd46` (`How Marie Curie discovered radium`, `pl`, `30`) was created by one WF01 intake and completed autonomously to `review_ready`. Exact voiceover duration is 26.983 s. The original failure class reproduced on segment 4: initial multimodal review returned `visual_review_approved_count=1` for `visual_review_required_count=2`, so `visual_review_shortfall=true`. The new single recovery round then added four newly reviewer-approved exact-target candidates; the same segment finished with approved count 5, `visual_review_shortfall=false`, `visual_recovery_used=true`, and `global_conflict_recovery_attempted=true`. WF04 stored `visual_quality.pass=true` with 20 shots, 20 unique assets, 20 unique perceptual clusters and zero reuse. WF05 rendered `jobs/d278b778-4aea-468d-b78e-aa03e994fd46/render/final.mp4`; technical probe is H.264 + AAC, 1080x1920, 30 fps, 27.000 s, SHA256 `e6dae140d636d0d57c49d4fd90a6d4ba14f60909576bd487085d6d226ff2558c`. This is machine completion only, not HUMAN PASS.

Fresh UK/60 job `ff7c0237-dc9f-4709-bf16-5d2e69201852` (`как образуется северное сияние`, `uk`, `60`) was then created through WF01. WF02 and WF03 passed automatically; final continuous voiceover duration is 60.480 s with one script-fit pass and no speech-speed manipulation. WF04 execution `15665` failed closed at recovery review with `Global conflict recovery reviewer returned invalid JSON for batch 1 [line 3]`.

Exact V4 execution `15669` proved this is a separate structured-output contract defect. Kilo returned `finish_reason=length` and was correctly normalized as unsuccessful. Gemini fallback returned `status=completed` and was incorrectly marked provider success because the gateway only checked for non-empty text. The 1456-character Gemini response was syntactically invalid JSON: after the first segment object it emitted the next `segment_number` before closing the previous object. Therefore the transport/provider layer succeeded while the structured-content contract did not.

Systemic correction now under GitHub gate: V4 accepts an opt-in `response_format: "json"` plus `response_schema`. For structured calls, Kilo receives OpenAI-compatible `response_format: {type: "json_object"}` and Gemini Interactions receives `response_format: {type: "text", mime_type: "application/json", schema: ...}`. Both provider normalizers now require syntactically valid JSON whenever `expects_json=true`; malformed Kilo `stop` output falls through to Gemini, while malformed/incomplete Gemini output becomes provider-exhausted instead of usable text. Both WF04 actual-image reviewer calls — initial and recovery — send the same reviewer JSON schema. Semantic validation of segment numbers and candidate IDs remains in WF04. No JSON repair parser, retry loop, relevance weakening, shot-count relaxation or topic-specific exception is introduced.

Verification for this correction before commit: targeted structured-output and existing provider-failover regressions PASS; workflow JSON parse PASS; Python regressions `11/11` PASS; Node static regressions `32/32` PASS; `git diff --check` PASS; clean n8n `2.33.3` imports of both V4 Model Gateway and WF04 PASS. Production deploy and a completely fresh UK/60 E2E remain blocked until commit/push and GitHub tree verification complete.

### 2026-09-06 UK/60 reviewer payload overload correction

After structured-output commit `2e649032bab9a68cc1b3784cfd58dc80f3735230` was deployed, fresh autonomous UK/60 job `0a0eae4e-76d5-44b7-b929-2f1878bf2ce5` (`как образуется северное сияние`, `uk`, `60`) was created through one WF01 intake. WF02 and WF03 passed automatically. Final continuous voiceover duration is 55.728 s with one script-fit pass and no speech-speed manipulation. WF04 then failed closed on initial multimodal review batch 3 with `Multimodal visual reviewer unavailable for batch 3 [line 5]`.

Exact V4 execution `15740` proved the structured-output contract itself was working: `expects_json=true`; Kilo received `response_format: {type: "json_object"}` and Gemini received `mime_type: "application/json"` with the reviewer schema. Kilo returned `finish_reason=length` and was correctly rejected. Gemini then hit the existing bounded 90 s provider timeout, so V4 normalized the full provider chain as `provider_exhausted=true` instead of returning malformed text.

The overload is general and measurable. Initial visual-review executions `15738`, `15739`, and `15740` each carried 36 inlined images plus 43 text items. Batches 1 and 2 completed through Gemini; batch 3 timed out. The 36-image exposure came from six segments per batch times six candidates per segment even though the reviewer output contract permits at most four approved IDs per segment and production visual segments require only one or two shots.

Systemic correction now under GitHub gate: both initial and recovery review preparation cap exposure at four candidate images per segment while preserving the existing six-segment batch size, exact-target candidate ordering, actual-image review authority, one-shot recovery and fail-closed semantics. A six-segment reviewer batch is therefore bounded to at most 24 images / 55 total input items instead of 36 images / 79 items. Because durable `planned_shot_count` is restricted to 1..2, four reviewed alternatives retain at least 2x candidate slack per required shot; no shot-count relaxation, provider timeout increase, retry loop, topic-specific query or unreviewed fallback is introduced.

Verification before commit: initial-review and recovery-review exposure regressions PASS; Python regressions `11/11` PASS; Node static regressions `32/32` PASS; workflow JSON parse PASS; `git diff --check` PASS; clean n8n `2.33.3` import of WF04 PASS. Production deploy and a completely fresh UK/60 E2E remain blocked until commit/push and GitHub tree verification complete.

### 2026-09-06 global visual-semantic gate correction

A cross-topic production audit proved that the remaining visual failures were not isolated topic problems and that prior `review_ready` machine states were not sufficient evidence of visual correctness. Fresh job `4894fe3a-3626-4870-8112-6d1ec0032303` (`как возникла жизнь на земле?`, `uk`, `30`) failed closed at `No valid semantic visual shot assignment at shot 18/20`. Exact WF04 execution data showed that every segment had enough nominally model-approved candidates after recovery, but the approved pools still contained semantically wrong or overlapping assets, so the global unique assignment failure was downstream evidence rather than the primary defect.

The same cross-topic audit found false machine approvals in materially different successful/failed runs. Examples include a Cyprus school building approved for an early nuclear-physics laboratory beat in the Marie Curie job, steel wire approved as a copper transformer winding, DNA/blood-cell imagery approved for early-Earth/abiogenesis beats, generic molecules approved as self-replicating RNA, and a membrane/proton-gradient diagram approved for a hydrothermal-vent photography target. The fresh `4894fe3a...` job itself had correctly aligned narration-to-`visual_target` values, so the current root cause is below target generation.

Two general defects were verified in source. First, `candidateMatchesQueryAnchor()` previously allowed a long target to be represented by the first few weak semantic words; temporal/generic terms such as `early`, `20th`, `century`, `scientific`, `concept`, `equipment` could therefore admit unrelated stock. The bounded conflict-recovery function also returned newly searched candidates without the same target-anchor gate. Second, the multimodal reviewer was asked to select provider IDs directly after seeing filename/ID labels, so it could be biased by lexical cues and could hallucinate target content that was not present in the pixels.

Systemic correction in the current clean checkout: initial discovery and conflict recovery now use the same stronger target-anchor model. Media/low-signal words are removed from anchor keys; long targets require at least three grounded anchor hits; each candidate carries explicit target-anchor metrics; recovery filters candidates before reviewer exposure; canonical-article media can remain available only under the existing provenance path and is still subject to the final actual-image gate. WF04 now hides real provider IDs/filenames from the vision model and exposes opaque `review_id` values only. The model must return one candidate-by-candidate verdict with `relevant` plus a short `visible_description`. Deterministic code then requires both target eligibility and consistency between the model's visible description and the provider's real metadata before an asset can enter the approved pool. The identical contract is applied to initial and recovery review. Unreviewed fallback, relevance weakening and asset reuse remain forbidden.

A separate user-requested global editorial adjustment reduces photo-cut intensity without changing color or adding a renderer-specific trick. Ordinary images have no saturation/brightness/zoom treatment in the current renderer; the high perceived intensity came from shot cadence. The shared shot-count rule now uses the existing 3.2 s support-change boundary: normal shorter beats keep one still, and only beats at least 3.2 s receive a second still. The rule is centralized through `plannedShotCountForDuration()` and used by both segmentation and beat-aligned discovery. This is an editorial cadence change, not an assignment bypass; every planned shot must still use a unique reviewer-grounded asset and perceptual cluster.

Verification for this correction before commit: targeted semantic-anchor/discovery/recovery/reviewer regressions PASS; Node static regressions `33/33` PASS with the real-provider integration dry-run intentionally excluded; Python regressions `11/11` PASS; all workflow JSON parse PASS; `git diff --check` PASS before this documentation append; modified media-worker modules pass `node --check`; clean n8n `2.33.3` import of WF04 PASS; a clean media-worker Docker build from `services/media-worker` PASS with image SHA `41811d52bf3d08d565855ed6acd63c6da5328c7dbe402e216608803a38f3f07`. Production has not yet been changed by this semantic-gate correction.

### 2026-09-06 bounded visual recovery query specificity correction

Fresh autonomous production job `cd5a21dd-3b89-4254-a462-e131b5b95646` (`How a mechanical clock escapement works`, `ru`, `15`) was created through WF01 only. WF02/WF03 completed and produced one continuous natural-rate voiceover of `14.448 s`. WF04 then failed closed before reviewer/assignment with `Visual segment 3 discovery returned no candidates`; no MP4 was produced. Exact execution `16110` showed two beats with zero candidate inventory even though their exact final-beat targets were valid. The bounded recovery query had collapsed `cutaway technical diagram showing mainspring energy release in a clock` to `cutaway technical diagram`, and `motion blur photography of a swinging brass clock pendulum` to `motion blur photography`. The general defect was recovery-query prefix bias: media/style words could displace the actual subject/mechanism.

Systemic correction under GitHub/deploy gate:

- recovery retrieval separates recall from acceptance: it preserves canonical subject overlap first and then ranks concrete content anchors ahead of photographic style/action words;
- when the exact query needs recovery, the provider query is intentionally compact and broad enough for retrieval (for example `clock mainspring` or `clock pendulum`) rather than trying to encode the full acceptance test;
- the original full `visual_target` remains unchanged and every recovered candidate must still pass the same strict target-anchor metrics before it can be exposed to the actual-image reviewer;
- the actual-image reviewer and global uniqueness gates remain unchanged; no unreviewed fallback, topic-level fallback, threshold weakening, asset reuse or second recovery round is introduced.

Real-provider verification on the exact failed six-beat timeline returned zero provider errors. The previously empty mainspring beat now returns two strict Wikimedia candidates (`Clock Mainspring.png` and `Alarm clock mainspring.JPG`), each with `4/3` required target-anchor hits. The previously empty pendulum beat now returns two strict candidates with `3/3` anchor hits. Static verification after the final logic: `33/33` Node tests + `11/11` Python tests PASS, workflow JSON PASS, `git diff --check` PASS, and a clean media-worker Docker build succeeds with image SHA `bddaf1e7ff12da5fd50df4f0d823610d86a66948f6833f6485dee4d23f87a54a`. Production has not yet been changed by this correction.
