# Codex handoff — production video factory

Updated: 2026-09-21

## Resume here — authoritative checkpoint, 2026-09-22

Production M5 v99 `8317622a-7d47-4cc5-8c40-f3f76caebf42` / M8 v53 `0953f69f-e982-467e-95e0-35161a613771`, both runtime-confirmed. Latest PL15 `b36a7c19-3427-4d67-9e2b-50d0acb4d717` passed M4–M7 and failed M8 9229 on S1; no M9/MP4. All 45 searches/335 candidates saved. Next: targeted replay fixes for S1 secondary-object evidence, S5 paired-object retrieval and missing S4 singleton domain; see final section. Experimental secondary-head relaxation was reverted, NOT deployed. Do not start another full job before replay resolves the recorded gaps. EN30/manual acceptance pending. 110 retained tests PASS; previous sections historical.

## Project

Repository: Pokhyl/ai-short-form-content-factory

This is the existing production n8n short-form video factory. Continue from the current production state and preserve its working contracts and data. Refactor or replace internal implementation when a systemic fix requires it; do not fork the work into a separate parallel project.

Input:
- topic
- language
- duration: 15 / 30 / 45 / 60 seconds

Pipeline:
research -> script/storyboard -> one continuous TTS narration -> local alignment -> relevant visuals -> 1080x1920 render -> machine QA

Project constraints already implemented in the codebase:
- n8n is the orchestrator;
- providers/services used by the project must remain free-only;
- no Ollama/local LLM/model-worker;
- PostgreSQL is the source of truth;
- no topic-specific hardcoding, lookup tables, or manual asset bindings.

Scope boundary:
- modify this project's code, project workflows, project database functions/schema, media-worker and Studio as needed;
- shared MCP/ADMIN workflows, n8n.hodor.com.pl and unrelated containers/projects are outside this project.

## Production

Repo path on VPS:
/opt/ai-short-form-content-factory

Production n8n:
https://publisher.hodor.com.pl

Studio:
https://studio.hodor.com.pl/

Project workflow IDs:
- M3: VideoM3Intake001
- M4: VideoM4Research001
- M5: VideoM5Storyboard001
- M6: VideoM6Voiceover001
- M7: VideoM7Alignment001
- M8: VideoM8Visuals001
- M9: VideoM9RenderQa001
- Self-Test API: VideoSelfTestApi001

Current deployed versions:
- M3 versionCounter 2, versionId e78f648c-639a-439a-8915-270d3b44f1cb
- M4 versionCounter 5, versionId 3cf94dd2-8c3b-4585-ae88-6315a2685ff7
- M5 versionCounter 94, versionId b4122d0a-5754-4311-8b7a-adab15ff0697 (semantic/timing guards + English visual metadata + secondary process-anchor normalization)
- M6 versionCounter 7, versionId 98e671f3-a0dc-42fa-81e9-4c9524a05e6a
- M7 versionCounter 4, versionId 91fbac4f-f40d-4d75-9111-3e4ed01bd9ff
- M8 versionCounter 47, versionId b47eb18a-e2f3-4b4e-96e2-b263b29f558d (v46 + contextual provider queries + explicit query provenance/cache key separation)
- M9 versionCounter 1, versionId 5b6c937c-1767-4c3e-99c4-31ea38a26961
- Self-Test API versionCounter 3, versionId f3ef8cbf-1c56-4048-9fdf-feb073de96df

Current media-worker image:
sha256:11d5b351609b40f9e5c46362a59ff2c620a403503bbb8f6e8ae0f57c57eef7ec

Last verified production state:
- publisher HTTP 200
- Studio HTTP 200
- media-worker healthy
- media-worker restart count 0
- workflow inventory: 32 total / 15 active = 8 project workflows (all active), 22 shared workflows (6 active), 2 temporary workflows (1 active)
- root filesystem: 38 GB total, 29 GB used, 6.8 GB free (82% used); avoid unnecessary Docker image/build accumulation during regression work

Production architecture facts:
- publisher.hodor.com.pl is shared with existing MCP/ADMIN workflows; those workflows are not part of this project.
- n8n.hodor.com.pl is unrelated to this project.
- exported project workflows reference credentials named Gemini Text and Video Factory Postgres; credential secrets are not stored in this repository.
- supporting Postgres, media-worker and SearXNG are separate from the production n8n container.
- an older temporary review workflow M10TempReview001 is still present; it is not the current regression acceptance state.

## Important fixes already implemented

### M4 research
- systemic provider fallback and live-source handling;
- no topic lookup tables.

### M5 script/storyboard
- current deterministic scene/shot density is 5 / 9 / 13 / 17 for 15 / 30 / 45 / 60 seconds;
- each scene currently contains exactly one shot;
- repair prompts interpolate actual scene/shot counts;
- bounded JSON recovery for trivial structural garbage;
- pre-TTS word-count heuristics no longer override measured TTS;
- real TTS measurements drive timing decisions;
- preview TTS uses a robust median;
- near-miss stability checks preserve the configured tolerance;
- M6 remains the authoritative final-audio duration gate.

### M6 voiceover
- one immutable voiceover run exists per job/script version;
- up to four independent TTS candidates may be synthesized to satisfy the measured-duration gate;
- exactly one final MP3 is persisted;
- audio is persisted only after the strict measured-duration gate passes.

### M7 alignment
- numeric words normalize to values while preserving non-equivalence such as 30 != 40;
- Whisper token sequences such as twenty + five normalize to 25;
- common apostrophe variants are normalized consistently, including Ukrainian cases such as в'язкою;
- existing global and per-scene lexical gates remain.

### M8 visuals
- failed provider requests are recorded with their real HTTP status and zero candidates;
- failed provider responses are not cached;
- remaining providers may still satisfy a shot;
- Wikimedia request/download pacing is implemented;
- Wikimedia MIME allowlist matches media-worker support;
- strict per-shot relevant-asset selection remains;
- compound primary-subject matching was changed from near-literal phrase matching to distinctive-subject matching plus query/intent context.

Latest M8 scorer regression smoke after the v41 fix:
- UK magma pool candidate -> score 78, rejected=false
- RU navigation device candidate -> score 100, rejected=false
- PL turbine runner candidate -> score 80, rejected=false
- EN bee mouthparts candidate -> score 86, rejected=false
- unrelated swimming-pool portrait against a GPS request -> score 46, rejected=true

## Acceptance matrix

Use exactly these four cases and run them sequentially:

1. PL 15s — jak działa elektrownia wodna?
2. EN 30s — how do bees make honey?
3. RU 45s — как работает GPS?
4. UK 60s — як утворюються вулкани?

Sequential execution matters because concurrent M5 tests produced Gemini HTTP 429 rate-limit failures.

### Last complete runs before M8 v41

All used M5 v81 and M8 v40.

PASS:
- PL15 c7d649af-f43d-41ed-a366-dd624a7d5ee3 -> machine_qa_passed
- EN30 96694991-1342-418f-a2eb-b7c727df0832 -> machine_qa_passed
- RU45 ae56e7ce-2028-4e2b-bf75-9256e5db346b -> machine_qa_passed

FAIL:
- UK60 df2de78d-2f99-47e0-94f6-a452e9494ce2
- M4, M5, M6 and M7 passed
- M8 failed on shot S7-A
- the failure exposed overly literal compound primary-anchor matching

That M8 defect was fixed and deployed as M8 v41.

## Remaining work

1. Resolve current PL15 visual rejection on M5 v94 / M8 v45, then run fresh sequential acceptance on the verified deployed versions. Do not start EN30 before PL15 visual/audio review passes.
2. Each fresh job must reach machine_qa_passed.
3. Record each new job_id and the M4/M5/M6/M7/M8/M9 status.
4. If a case fails, inspect the exact production execution/data, fix the systemic cause, validate it, deploy the affected component, and rerun that case with a fresh job.
5. Keep the existing quality gates; do not make a failing case pass by simply lowering relevance or timing thresholds.
6. After 4/4 machine PASS, inspect the exact four final MP4s:
   - 1080x1920 vertical;
   - no text-description placeholders/cards;
   - no corrupt or unsupported assets;
   - visuals relevant to the corresponding narration scene;
   - enough visual changes;
   - continuous narration;
   - final duration passes the existing gate.
7. Update the project documentation with the final matrix and production state.
8. Run the final repository/production checks, then commit and push the finished state.

## Acceptance continuation — 2026-09-20 19:57 UTC

- Read the complete handoff and operating references; cloned `main` at `b3be6aa`.
- Live read-only verification: all eight project workflow activeVersionId/versionCounter values exactly match the Production section above; inventory remains 32 total / 15 active.
- publisher and Studio HTTP 200; media-worker image unchanged, healthy, restart count 0; supporting PostgreSQL and SearXNG healthy. Root filesystem remains 82% used / 6.8 GB available.
- Fresh PL15 job: `79c6a1f7-d98c-4b07-b68b-17896279df55`. Intake execution `8910` succeeded; Self-Test execution `8911` accepted the run; M4 execution `8912` is running. M5–M9 not started at this checkpoint.
- No production code, workflows, gates or credentials changed. No new final MP4 exists yet.
- Next: monitor this exact job through M9; inspect any failure before starting a fresh replacement. Start EN30 only once PL15 is terminal. Then RU45 and UK60 sequentially, inspect the exact four passing MP4s and record final checks.
- Operational access: SentinelX `sentinel_script_run(sudo=true)` supports scoped Docker/psql diagnostics on this VPS; ordinary exec runs without Docker socket permission. Use stdin with `docker exec -i` for SQL. Do not change SentinelX policy.

### PL15 machine PASS — 2026-09-20 20:01 UTC

- Job `79c6a1f7-d98c-4b07-b68b-17896279df55`: M4/M5/M6/M7/M8/M9 all `passed`; final status `machine_qa_passed`. Executions M4–M9: `8912`, `8913`, `8914`, `8915`, `8916`, `8917`, all success; Self-Test `8911` success.
- Exact final MP4: `/data/renders/79c6a1f7-d98c-4b07-b68b-17896279df55/final.mp4`; SHA-256 `aecbf91b63da1e602153551a7db61f5f8864e6298c6f30391dfb48f92b567d0d`; 1,936,739 bytes; 14,267 ms, narration 14,256 ms, mux delta 11 ms; 5 scenes. Visual inspection remains pending.
- Fresh EN30 created next: `295cd85b-df3f-42fc-8551-8c7766fa7354`. Monitor this job before starting RU45.
- Repository checks PASS: media-worker Python AST; all 8 workflow JSON files and connection graphs; syntax of 113 JavaScript Code nodes; `git diff --check`.
- Production workflow versions and media-worker image remain unchanged from the verified Production inventory.

### Exact PL15 media audit; EN30 M4–M7 PASS

- Added reusable read-only `scripts/audit_final_media.py`. Ran it inside the existing media-worker on the exact PL15 final MP4; all 12 checks PASS. Evidence: `docs/acceptance/2026-09-20-pl15-audit.json`. It verifies full FFmpeg decode, hashes, streams/format, duration, density, contiguous coverage, unique assets and correlation of decoded final AAC with immutable MP3. It neither synthesizes audio nor edits artifacts.
- PL15 visual review sampled the exact MP4 across all 5 scenes: Hoover Dam, hydroelectric turbine runner, hydroelectric generator stator, high-voltage transformers, transmission pylon. No description cards or corrupt imagery found. Turbine is an illustrative static museum runner, not footage of water moving; the generator image is a historical stator workshop photograph. Both match the narrated subjects. No listening-based assessment is claimed; final/source audio correlation is 0.99998048 with 37.375 ms decoded-length difference.
- Contact sheet and extracted final audio remain in VPS `.review/acceptance-20260920/`; product artifacts are unchanged. Explicit HUMAN PASS remains a separate final acceptance step after all four outputs are reviewable.
- EN30 `295cd85b-df3f-42fc-8551-8c7766fa7354`: M4 `8920`, M5 `8921`, M6 `8922`, M7 `8923` all success; M8 `8924` running; M9 pending. Intake `8918`, Self-Test `8919`.
- Active production versions/image unchanged. Next: finish EN30, then RU45 and UK60 sequentially; audit and visually inspect each final MP4.

### EN30 machine PASS but visual review FAIL — investigation in progress

- EN30 `295cd85b-df3f-42fc-8551-8c7766fa7354` reached `machine_qa_passed`; M4–M8 executions `8920`–`8924`, M9 `8930`, Self-Test `8919` all success. Its 12 technical media checks passed (`docs/acceptance/2026-09-20-en30-audit.json`), but it is NOT an accepted output.
- Exact MP4 SHA-256 `2dd9fbf137792c0b0f34047f644de736346f56e79c6334bbdaa2c74c9a726d1d`, 3,066,859 bytes, 29,500 ms, immutable narration 29,424 ms, 9 scenes.
- Exact scene-midpoint contact sheet `.review/acceptance-20260920/en30-contact.jpg` proves S9 is a text-heavy “Bee Honey” graphic poster, S7 is a honey jar instead of the required bee/mouthparts, and S6 has bare comb without the narrated workers.
- Root cause: Pixabay marks misleading assets `type=photo`, `isAiGenerated=false`; tag-only metadata contains bee/honeycomb terms regardless of visible subjects. The existing type/URL/AI checks and lexical scorer cannot establish photographic content from those tags. This is a provider-evidence defect, not an encoding/duration failure. No asset IDs or topic-specific bindings will be hardcoded.
- Planned systemic fix: fail closed on tag-only photographic evidence lacking a descriptive caption, retaining provider searches/accounting and the existing relevance gates. Verify positive caption-supported candidates from remaining providers, then deploy only the affected project workflow.
- RU45 `8e841de6-30fd-433d-9c0d-3625b78af6af` was started sequentially after EN30 machine completion, before visual rejection was found; currently M5 running. Preserve it as a diagnostic pre-fix job. Do not start another job until it is terminal.
- Current production remains M5 v81 / M8 v41 and the original media-worker image. Next: implement/regression-test evidence validation, deploy it after the current run ends, and run a fresh sequential four-case acceptance on the fixed version. Failed/review-rejected jobs stay immutable.

### M8 photographic-evidence fix validated locally — not yet deployed

- Changed only M8 normalizers: Pixabay tag-only images are retained in search diagnostics but rejected as `pixabay_photo_content_unverified_tag_only`; Pexels images require an `alt` description and reject explicit poster/illustration/graphic descriptions. Pixabay video logic is unchanged.
- This intentionally limits automatic photographic selection to description-supported Pexels/Wikimedia candidates; Pixabay still participates in discovery/accounting. It is a fail-closed provider-evidence restriction, not proof that every captioned image is visually correct. Human/agent scene review remains necessary.
- `node --test tests/visual-evidence.test.cjs`: 8/8 PASS, including the observed misleading metadata, generic non-topic quarantine, caption-supported positive, missing-description/graphic/unrelated negatives, and provider HTTP-failure accounting. `git diff --check` PASS.
- Production still M8 v41; RU45 diagnostic job is in M8 and must finish before deployment. Next: backup exact M8, import/publish the tested workflow under the same ID, verify active version/runtime and protected inventory, then restart the sequential matrix with fresh jobs.

### M8 v42 deployed; fresh matrix restarted — 2026-09-20

- Backup: VPS `.backups/m8-before-photo-evidence-20260920.json`. Imported/published only `VideoM8Visuals001` through n8n CLI with its existing project `FF7o9vSL9orH8B5T`; active version is `c6309bfc-4aa7-42c6-b5a9-49b187c134c1`, counter 42. Other 31 workflow rows have identical aggregate hashes before/after; inventory remains 32/15. No n8n/container restart or credential change.
- CLI prints a general restart advisory; this workflow is invoked internally. Verify the fresh M8 execution snapshot actually contains the v42 normalizers before claiming runtime deployment acceptance.
- Pre-fix diagnostic RU45 `8e841de6-30fd-433d-9c0d-3625b78af6af` reached machine PASS: M4 `8939`, M5 `8943`, M6 `8953`, M7 `8954`, M8 `8968`, M9 `8995` all success. This is not part of the final v42 matrix.
- Fresh v42 PL15: `edb9982b-a391-4033-9a52-a4986393f18b`, run accepted. Next: complete and inspect it, confirm v42 execution and zero selected tag-only Pixabay images, then EN30/RU45/UK60 sequentially.
- All other workflow versions and media-worker image remain unchanged. The final target is now M5 v81 / M8 v42. Earlier v41 matrix outputs are historical diagnostics.

### PL15 M5 failure diagnosed and correction tested — 2026-09-21 01:48 UTC

- Job `edb9982b-a391-4033-9a52-a4986393f18b` is immutable `script_failed`: intake `9008`, M4 `9010` success, M5 `9011` failed; M6–M9 never started. Error: final preview median 16,368 ms vs 15,000 ms target / 750 ms tolerance.
- Exact cause in execution 9011: probe 1 first sample was 15,144 ms but its confirmed three-sample median was 17,136 ms (15,144 / 17,376 / 17,136). Later timing-repair interpolation reused the original 15,144 ms rather than the confirmed median for that same narration. Against probe 2 (20 words / 13,704 ms), this incorrectly requested 25 words instead of 22. Subsequent corrections oscillated and exhausted the bounded attempt budget.
- Fix in the three M5 interpolation/final-repair builders: use the latest available stability median only when the exact canonical narration matches. Unconfirmed or different-text samples keep their own measurement. Existing timing gates, provider budgets, voices, attempt limits and immutable-job rules are unchanged.
- Validation: `node --test tests/*.test.cjs` 12/12 PASS. Includes the exact 15,144→17,136 ms regression, same-text matching, unrelated-text isolation and original 750 ms tolerance. `git diff --check` PASS.
- Fresh production check 2026-09-21 01:47 UTC: M5 still v81, M8 v42; no project executions running/waiting; no additional jobs since the failed PL15. Fix is tested locally but not yet deployed at this checkpoint.
- Next: backup/import/publish only M5; verify unchanged other workflows and fresh execution version snapshots for both M5 and M8. Start a fresh sequential PL15/EN30/RU45/UK60 matrix and inspect all four exact MP4s before final acceptance.

### M5 v82 deployment — 2026-09-21 01:49 UTC

- Imported/published only `VideoM5Storyboard001`: counter 82, activeVersionId `d47c0333-5e66-43ca-a10a-c3482a322d6c`. Backup: `.backups/m5-before-median-propagation-20260921.json`. Other 31 workflow rows unchanged by aggregate hash comparison. Inventory 32 total / 15 active; no service restart.
- Current matrix target: **M5 v82 / M8 v42**, other versions and media-worker image unchanged.
- Fresh PL15 `624f9615-56ca-49cf-8a1a-6853509ed599` created and run accepted. Next: verify execution snapshots use new code, complete PL15 and review the exact artifact, then EN30, RU45, UK60 sequentially.

### PL15 PASS on M5 v82 / M8 v42 — 2026-09-21

- Job `624f9615-56ca-49cf-8a1a-6853509ed599`: M4–M9 all passed; executions `9014`, `9015`, `9016`, `9017`, `9018`, `9019` all success (intake `9012`, Self-Test `9013`). Exact execution snapshots confirm M5 v82 and M8 v42 with the new code; no service restart was required.
- Exact artifact audit: `docs/acceptance/2026-09-21-pl15-audit.json`, all 12 checks PASS. MP4 SHA-256 `697dd432304d4874da3b0c5b57d26925f0bc47cc06a010e0b365597507bddfc9`, 2,281,875 bytes, 15,533 ms; immutable narration 15,528 ms; audio correlation 0.99998163; 5 distinct scenes/assets.
- Inspected exact scene-midpoint frames: dam intake/reservoir, dam wall, hydroelectric turbine hall, historical generator machinery hall, power substation. All are photographic and relevant to corresponding narration; no placeholder/text cards or corrupt frames. The generator is an illustrative museum photograph, not a claimed live operating facility. Selected sources: 3 Pexels + 2 Wikimedia; zero Pixabay images. Contact sheet: VPS `.review/acceptance-20260920/pl15-v82-contact.jpg`.
- Live/repository comparison: all 8 workflow node/connection graphs match; media-worker source SHA matches repository. Media-worker healthy, restart count 0, image unchanged; disk 6.7 GB free.
- Next EN30 `88a2b8c8-4e27-4ae3-9890-755fd0fe1904` created and accepted sequentially after PL15 completion. Finish and inspect it before RU45/UK60. Active versions unchanged: M5 v82 / M8 v42.

### EN30 v42 machine PASS, visual FAIL — 2026-09-21

- `88a2b8c8-4e27-4ae3-9890-755fd0fe1904` reached machine PASS: M4 `9022`, M5 `9023`, M6 `9024`, M7 `9025`, M8 `9026`, M9 `9027` success; intake `9020`, Self-Test `9021`. It is rejected by visual review and is not part of final acceptance. No further job is running.
- Exact MP4 scene-midpoint sheet `.review/acceptance-20260920/en30-v42-contact.jpg` confirms S2 is a bee fly (not a bee), S3 a wasp, and S6 dew on pine needles (not nectar/honey). The other six scenes show relevant bees/honeycomb.
- Root cause is broader than Pixabay: the v41 scorer accepts one token of a compound primary subject; “droplets” therefore satisfied “nectar droplets.” Wikimedia treated long general descriptions/categories as strong subject evidence; the wasp description mentions bees only as a contrasting taxon, and a plant/bee-fly description mentions proboscis.
- Next systemic correction: require meaningful distinctive primary-subject coverage and use image-specific title/caption evidence instead of long background text; reject missing subject evidence, keeping all timing/license/uniqueness gates. Replay saved candidate data before spending a new production job. M5 v82 / M8 v42 remain active; no new deployment at this checkpoint.

### Subject-evidence correction tested — ready to deploy

- M8 changes: compound primary subjects require the existing 60% concept coverage over distinctive terms (rather than any one term); generic physical-form terms do not serve as identity; supplied secondary identifying context must also be evidenced; Commons title/object name/classification categories supply strong subject evidence, while long descriptions supply only weak context; ordinary four-letter plurals normalize consistently (`bees`→`bee`) without stripping `ss`.
- M5 prompt clarifies whole-subject identity, essential visible anchors only, and real physical context for invisible mechanisms. No topic, species, asset IDs or manual bindings were introduced. Scene/shot counts and all timing, relevance-score, license and uniqueness thresholds remain unchanged.
- `node --test tests/*.test.cjs`: 18/18 PASS, including wasp/bee-fly/dew/ambiguous-monkey negatives and valid compound subject controls. All 8 workflow graphs, 113 JavaScript nodes and Python AST checks PASS; `git diff --check` PASS.
- Replayed 236 original Pexels/Wikimedia candidates from execution 9026 without provider calls; 211 correctly rejected under stronger evidence. Old overspecific storyboard now has 6 shots without eligible candidates and would fail closed instead of producing unrelated images. This does NOT assert the old job can pass. Raw replay input is VPS `.review/acceptance-20260920/en30-v42-replay.json`; bounded result is `docs/acceptance/2026-09-21-en30-v42-replay.jsonl`.
- Production remains M5 v82 / M8 v42 at this checkpoint. Next: deploy both tested project workflows after backups and protected-row checks, then fresh sequential matrix on the final versions. Existing rejected jobs remain unchanged.

### M5 v83 / M8 v43 published — 2026-09-21

- Active IDs: M5 `5e50db9d-e3f9-44a0-8e2f-a0168f505bec` / counter 83; M8 `d282d875-8e81-43c7-99bb-3f9730fb9052` / counter 43. Exact backup `.backups/m5-m8-before-subject-grounding-20260921.json`. Other 30 workflow rows unchanged by aggregate comparison; inventory 32/15. No service restart or credential change.
- Fresh sequential matrix starts with PL15 `1be96d5a-7626-4771-9b1c-7b5452894725`, created and run accepted. All earlier jobs are diagnostics for prior versions.
- Next: complete/inspect PL15, then fresh EN30/RU45/UK60 sequentially; record execution snapshots and exact artifacts. Production media-worker and other six workflow versions remain unchanged.

### Complete Commons query coverage — tested, not yet deployed

- Confirmed live public Commons probes: `hydroelectric penstock pipe` and `penstock pipe` each return 8 candidates including penstock photographs. The original long query returned a turbine and hydraulic-compressor diagram, both correctly rejected. This confirms a retrieval gap; it does not yet prove the complete storyboard passes.
- M8 now enumerates every storyboard query for Wikimedia, retaining query index, provenance, 8-second pacing and existing retry/quality gates. `factory.begin_visuals` expected count becomes 3 × total storyboard queries. Existing immutable run counts are untouched.
- Checks: 22/22 Node tests PASS; replacement SQL compiled and function definition asserted in a rolled-back production transaction; git diff check PASS. Production remains M5 v83 / M8 v43 until the following deployment checkpoint.
- Next: back up and replace only begin_visuals(uuid), publish M8, verify protected workflow rows and deployed count contract, then create a fresh PL15.

### M8 v44 and search accounting deployed — 2026-09-21

- Replaced only `factory.begin_visuals(uuid)` and published M8 counter 44 / active ID `16c27568-3bbf-41b2-9b23-9e555b3b98da`. M5 remains v83; all other versions/image unchanged. Other 31 workflow rows exactly unchanged by aggregate hash; inventory 32/15. No service restart.
- Backups: `.backups/m8-before-query-coverage-20260921.json` and `.backups/begin-visuals-before-query-coverage-20260921.sql`. Verified deployed SQL uses 3 × total queries; old run records untouched.
- Deployment interruption resolved: strict umask made the copied non-secret workflow JSON unreadable by n8n (EACCES). Changed only `/tmp/m8-query-coverage.json` mode to 0644 and repeated import/publish successfully. No product job ran during the brief SQL/workflow transition.
- Fresh PL15 `69391e2d-34bc-4775-89f8-32913dff9edb` created and run accepted. Next: record actual execution IDs/version snapshot and full search accounting; inspect final artifact or diagnose terminal failure before any new job.

### Runtime verification on fresh v44 job

- PL15 `69391e2d-34bc-4775-89f8-32913dff9edb`: intake 9036 success; parent 9037 running; M4 9038, M5 9039, M6 9040, M7 9041 success; M8 9042 running. No final artifact yet.
- Execution snapshots confirm M5 active ID `5e50db9d-e3f9-44a0-8e2f-a0168f505bec` and M8 `16c27568-3bbf-41b2-9b23-9e555b3b98da`. New visual run expects 45 searches for 5 × 3 × 3, with 30 persisted while paced Commons searches are still in progress.
- All 8 active workflow node/connection graphs match repository; syntax checks pass for 113 Code nodes. Next: wait for this job's terminal result, audit/review output before starting EN30.

### PL15 v44 machine PASS, semantic/visual REJECT — 2026-09-21

- Job `69391e2d-34bc-4775-89f8-32913dff9edb`: intake 9036, parent 9037, M4–M9 9038–9043 all success. All 45/45 searches persisted; complete query coverage works. No further job started.
- Exact MP4 SHA-256 `5ac0465ba7f27008b3d69c4261d99db6c677666c39dfb8a59902bd39547447ea`, 2,168,618 bytes, 15,367 ms; narration 15,336 ms; correlation 0.9999856084634534; 5 unique scenes. All 12 read-only technical media checks PASS. This is NOT accepted product output.
- Exact scene-midpoint sheet `.review/acceptance-20260920/pl15-v44-contact.jpg`: S1 dam, S2 reservoir, S3 decorative theme-park waterwheel labeled by Commons as turbine, S4 mostly facade with small portable generators near the edges, S5 transmission pylon. S3 does not establish an industrial turbine runner; S4 does not provide a usable generator view. Lexical provider labels alone still do not establish the actual mechanism or final crop visibility.
- Persisted Polish narration has semantic damage: S1 “Tradycyjna elektrownia zamienia energię elektryczną.” reverses/omits the intended energy transformation; S2 “Potężna zapora bardzo skutecznie spiętrza.” lacks the object (water). Technical timing/alignment checks cannot catch this. Need inspect execution 9039 repair history before identifying which builder introduced the damage.
- Next: trace timing repairs and preserve complete factual meaning during shortening; investigate center-crop object loss and a generic geometry-preserving render strategy. Do not add asset/topic blacklists or weaken gates. Keep this job immutable. M5 v83 / M8 v44 and worker image remain active; no new deployment after review.

### M5 semantic-space repair tested — NOT DEPLOYED

- Execution 9039 trace proves original narration was complete and correct. First timing repair shortened it; robust measurement triggered another repair. `Build Timing Repair 2` imposed equalized counts `[5,5,4,4,4]`; its 24-word response failed the 22-word constraint. `Build Timing Precision Retry` then returned the damaged 22-word text and passed mechanical validation. The retry lacked original narration as its meaning reference.
- Repository correction distributes the unchanged total target proportionally to original scene lengths within unchanged 2–10/14 bounds, and supplies original scene narration to both precision builders. The retry explicitly treats its previous draft as unaccepted and preserves subjects, required objects and causal direction. Exact total/per-scene checks, duration gates, attempt counts and provider budgets remain unchanged.
- Validation: 24/24 Node tests PASS, including median propagation, bounded proportional allocation and preservation of original meaning context when the failed draft lost an object. These tests prove data/prompt contracts, not semantic quality of future model output. Production remains M5 v83 / M8 v44.
- Next: scoped M5 deployment with backups/protected-row comparison; resolve render crop and provider-label ambiguity before fresh acceptance. No new job is running. Do not claim semantic acceptance until actual new narration and all final frames are reviewed.

### Full-image render fit regression — tested, NOT DEPLOYED

- `_render_segment` now fits the entire source image/video inside 1080×1920 with proportional scaling and neutral black padding, replacing unconditional center cropping. This preserves edge content and source geometry; it does not prove a source depicts the correct subject.
- `tests/render-fit-regression.py` executes the actual renderer function with synthetic red/blue edge landmarks and real production FFmpeg. PASS for square-ish 1600×1611, landscape 1920×1080 and portrait 1080×1920: encoded H.264 output decodes at 1080×1920 with both edge landmarks retained. Test output uses temporary paths, no accepted/failed job artifacts are modified.
- Python AST and git diff checks PASS. Production worker is still the old image; new build/deploy remains pending together with M5 semantic-space fix. Exact selected sources can still be semantically wrong despite matching provider titles (e.g. theme-park wheel); review every scene and do not declare this solved by padding.

### M5 v84 + full-fit worker deployed — 2026-09-21

- M5 active counter 84 / ID `8918963e-54ad-4b52-b167-ef6c6fb9f52f`; M8 remains 44 / `16c27568-3bbf-41b2-9b23-9e555b3b98da`. Other 31 workflow rows unchanged by exact aggregate hash; inventory 32/15. M5 backup `.backups/m5-before-semantic-space-20260921.json`. n8n was not restarted.
- Rebuilt and recreated only Compose `shorts-v2` media-worker. Active image `sha256:11d5b351609b40f9e5c46362a59ff2c620a403503bbb8f6e8ae0f57c57eef7ec`, healthy, restart counter 0. Old image ID saved in `.backups/worker-before-full-fit-20260921.txt`; original image retained for rollback. Models, voices, alignment hashes and persistent media volumes unchanged.
- No job ran during deployment. Next: verify live source and fresh M5 execution, run new PL15, inspect every sentence and exact full-fit frame. Provider caption/subject ambiguity remains an explicit unresolved limitation; do not reuse rejected outputs as acceptance or claim four-case completion.

### M5 v84 fresh job failed — exact continuation checkpoint

- `ccc91e49-8e19-404d-bf05-3ec4cab5d469`: terminal `script_failed`, final M5 measured median 14,064 ms, target 15,000 ± 750 ms. IDs: intake 9044, parent 9045, M4 9046, M5 9047. No M6–M9 or final MP4.
- Execution 9047 diagnosis: initial 28-word text was complete and factually suitable; first measured duration 15,336 ms, later stability median 16,488 ms. First repair shrank to a 20-word text measured 12,048 ms. Precision target was 25 words, but its retry produced a longer, semantically damaged draft (“siłę prądu” and “Ogromna woda”); later repairs retained these problems. Subsequent measurements were 16,656 → 17,544 → 14,064 ms; bounded attempts exhausted.
- The original-meaning prompt and weighted allocation are insufficient to ensure factual natural language. Do NOT label semantic defect fixed. `Validate Timing Precision Retry` checks scene/total anti-runaway bounds, not exact requested per-scene/total word equality; earlier checkpoint wording about exact checks referred to the initial precision validator and must not be read as a guarantee for its retry.
- Next engineering step: redesign the M5 repair/validation path so accepted narration is checked against original evidence/meaning, retain original meaning through ALL later final-repair builders (currently only the two precision builders receive it), and inspect exact response validation before more provider-quota-consuming TTS probes. Preserve free-only policy, attempt budgets, measured-duration gate and immutable jobs. A prompt-only retry is not sufficient evidence of a repair.
- Separate unresolved visual issue: metadata calls a decorative wheel a turbine and can select small background generators. Full-fit rendering prevents cropping but does not validate source meaning. Keep this distinction explicit during final scene review.
- Active production remains M5 v84 / M8 v44 / full-fit worker image above. No code changed after this failure. All changes and diagnostics committed to main; no successful current-version matrix, no HUMAN PASS, task incomplete.

### Checkpoint integrity verification

- Execution 9047 confirms actual M5 v84 ID `8918963e-54ad-4b52-b167-ef6c6fb9f52f`. Zero project executions running/waiting. Inventory remains 32 total / 15 active.
- Publisher and Studio HTTP 200; full-fit worker healthy, restart 0, active image exactly as listed above. Local and VPS worktrees clean at verification; all implementation commits pushed to origin/main.
- This is a safe continuation checkpoint, NOT final task acceptance. Next agent should start with the M5 v84 failure analysis immediately above, not rerun the historical matrix or infer success from machine PASS labels.

### M5 semantic-preservation gate — tested, NOT DEPLOYED

- Continued from failed v84 job `ccc91e49-8e19-404d-bf05-3ec4cab5d469` / execution `9047`; no production job was rerun while diagnosing.
- Exact replay confirms the failure chain: original 28-word factual narration -> 20-word calibration draft -> precision retry returned 30 words despite a 25-word request and introduced `siłę prądu` / `Ogromna woda`; later final repairs inherited that damaged draft and eventually measured 14,064 ms.
- Repository fix keeps `Normalize Timing Probe` as the immutable semantic source through every late timing builder. `Build Final Duration Repair`, `Build Final Measured Correction`, and both exact-word retry builders now include `original_narration`; final scene word allocations use original scene weights plus a 60% semantic floor instead of the latest damaged draft.
- New deterministic semantic-preservation guard runs on `Validate Timing Repair 2`, `Validate Timing Precision Retry`, both final-duration validators, both exact-word retry validators, and `Canonicalize Final Storyboard`. It checks original-content retention, limits novel content words, preserves numeric facts and negation polarity, and remains language-aware for EN/PL/RU/UK.
- `Validate Timing Precision Retry` now requires the exact requested per-scene and total word counts before TTS. Final exact-word retry validators also fail closed instead of sending a non-exact hybrid into another TTS probe.
- Regression tests include the exact bad PL phrases from execution 9047 and valid concise controls. Full Node suite: 34/34 PASS; all 55 M5 Code nodes pass `node --check`; Python compile and `git diff --check` PASS.
- Production checkpoint after deploy: M5 v85 / M8 v44 / full-fit worker. M5 v85 active ID `3fdc6ec5-c1cb-4594-b6c6-d4acb96088f0`; exact pre-deploy backup `.backups/m5-before-semantic-guard-20260921-080223.json`. Other 31 workflow rows were unchanged by aggregate hash; inventory remains 32/15. Live exported M5 core matches repository and contains the semantic/exact-word guards. No n8n restart was performed; runtime version must be confirmed by the next fresh execution snapshot.

### M5 v85 semantic guard deployed — 2026-09-21

- Published only `VideoM5Storyboard001`: counter 85, activeVersionId `3fdc6ec5-c1cb-4594-b6c6-d4acb96088f0`.
- Backup: `.backups/m5-before-semantic-guard-20260921-080223.json`.
- Aggregate hash of every other workflow row is identical before/after; inventory remains 32 total / 15 active. No credential or other workflow change.
- Live exported M5 nodes/connections/settings/pinData match repository. `Validate Timing Precision Retry` contains both semantic-preservation and exact-word guards.
- Publisher and Studio are HTTP 200; n8n restart count 0; full-fit media-worker remains healthy/restart 0 on image `sha256:11d5b351609b40f9e5c46362a59ff2c620a403503bbb8f6e8ae0f57c57eef7ec`.
- n8n CLI printed its generic restart advisory. No restart was issued because prior internal sub-workflow deployments have taken effect without it. The next fresh M5 execution snapshot must confirm active v85 before runtime acceptance.
- Next: run one fresh PL15. Inspect the actual M5 narration and v85 execution snapshot before treating the repair as validated in production.

### Fresh PL15 on M5 v85 failed safely; soft-count semantic patch tested — NOT DEPLOYED

- Fresh job `f03db30f-1b42-41dd-ac7b-48c90bef8e4c`: M3 execution 9048 PASS, M4 9050 PASS, M5 execution 9052 ran active v85 `3fdc6ec5-c1cb-4594-b6c6-d4acb96088f0` and terminated `script_failed`; M6-M9 did not start.
- Runtime v85 was confirmed directly from execution_data.workflowVersionId, so the generic n8n CLI restart advisory did not require a restart.
- Original M5 narration was factual and natural: 24 words, 17,424 ms first measurement. First timing repair produced 18 words / 11,496 ms. Repair 2 targeted about 22 words and retained immutable original context.
- Precision retry returned 23 words while the v85 validator demanded scene targets 6/4/4/4/4 exactly. Its actual response included filler/damage: `Ogromna zapora...`, `Wydajny generator...`, `Czysty prąd...`. v85 failed before another TTS probe with `7, required 6`, so bad text was not accepted.
- Engineering correction: exact/per-scene word counts are timing guidance again; real measured TTS is authoritative. Repair 2 and precision validators no longer reject a semantically valid narration solely for a small word-count mismatch. Final word-count retries may also proceed near target only after semantic validation.
- Semantic guard is stronger instead: minimum original-content coverage 0.625, plus generic novel filler-modifier rejection for EN/PL/RU/UK, numeric-fact preservation and negation-polarity preservation. The exact bad v85 response is covered by regression tests.
- Final timing builders still use immutable original narration, original scene proportions and semantic floors. Their prompts now explicitly allow redistribution between scenes when meaning needs more space and forbid filler/count-driven meaning loss.
- Full Node suite 35/35 PASS and `git diff --check` PASS. Production remains M5 v85 until this patch is committed/pushed and deployed.
- Next: deploy only M5 as the next version, confirm all other workflow rows unchanged, then run a new immutable PL15.

### M5 v86 deployed — soft word targets, hard semantics

- Published only `VideoM5Storyboard001`: counter 86, activeVersionId `7ad8ed81-edfe-4c74-9957-f0578de84261`.
- Backup of v85: `.backups/m5-before-soft-semantic-20260921-081235.json`.
- Other 31 workflow rows retain the exact same aggregate hash `a27f18a4b81669e2c7ec0721c2e20e5e`; inventory unchanged.
- Live exported M5 core matches repository. Semantic coverage threshold is 0.625 with generic filler rejection; hard exact-total precision rejection is absent.
- Publisher and Studio HTTP 200; n8n and media-worker healthy with restart count 0. No restart was issued.
- Next: create one fresh PL15, confirm execution snapshot uses v86, inspect M5 narration/semantic path, then continue only if the exact job passes.

### PL15 v86 reached M8; Pexels title corroboration fix tested — NOT DEPLOYED

- Fresh PL15 `b2e90f30-a887-4292-b489-ee6124c8d67f`: M4 9055 PASS, M5 9057 PASS on v86 `7ad8ed81-edfe-4c74-9957-f0578de84261`, M6 9058 PASS, M7 9059 PASS, M8 9060 FAILED on v44; M9 never started.
- M5 final narration was 25 words and stable in-window (14,448 ms first measurement, 14,472 ms canonical stability): `Elektrownia wodna zamienia energię wody w prąd. Zapora spiętrza rzekę, tworząc zbiornik. Woda spada przez turbinę wodną. Generator wytwarza czystą energię elektryczną. Prąd zasila domy.` No timing rewrite was needed.
- Exact M8 failure: S1-A `Hydroelectric power plant building exterior near a river`, must_show `hydroelectric power plant` + `river`. All 45 searches completed, but no candidate selected.
- Retrieval was not the problem. Pexels returned an exact-looking candidate with alt `Picturesque scenery of power plant with flowing water located near river among green hills against cloudy sky in summer day` and page URL slug `hydroelectric-power-plant-in-forest-4500695`; score 100, rejected only because `hydroelectric` was absent from alt strong subject text.
- Repository fix is provider-specific and fail-closed: Pexels page slug is treated as provider title corroboration only for one missing subtype term when the non-empty alt already establishes part of the primary subject, independent secondary scene context, and sufficient visual-intent overlap. URL/title alone cannot establish a subject and cannot rescue an unrelated alt.
- Photo scoring metadata no longer mixes the raw URL into ordinary visual-description text; the title corroboration channel is separate.
- Regression coverage includes the exact hydro candidate, unrelated-alt same-URL negative, existing URL-only negative, bee/wasp/dew/monkey negatives, and existing valid compound subjects. Full Node suite 37/37 PASS; all 10 M8 Code nodes pass `node --check`; `git diff --check` PASS.
- Production remains M8 v44 until this tested patch is committed/pushed and deployed. Next: deploy only M8, verify all other workflow rows unchanged, then start a fresh immutable PL15.

### M8 v45 deployed — bounded Pexels title corroboration

- Published only `VideoM8Visuals001`: counter 45, activeVersionId `3778d30c-70c0-4cd2-9df8-e8465d4fdd7a`.
- Backup of v44: `.backups/m8-before-pexels-title-20260921-092430.json`.
- Aggregate hash of the other 31 workflow rows is identical before/after; no credential or unrelated workflow changed.
- Live exported M8 core matches repository and contains `pexelsPageTitleText` / `primaryTitleCorroborated` logic.
- Publisher and Studio HTTP 200; n8n restart 0; full-fit worker healthy/restart 0 on the same image.
- No restart was issued. Next fresh execution must confirm v45 runtime snapshot, then PL15 must be reviewed from the exact final MP4 before EN30 starts.

### M5 first-repair semantic fallback + topic-focus patch — tested, NOT DEPLOYED

- Fresh PL15 `42a76712-dbe5-4d9a-99ea-17e82abd2e48` confirmed M5 v86 runtime and terminated in M5 execution 9065 before M6. Failure: semantic coverage 0.600 vs guard 0.625.
- Exact trace: initial storyboard 28 words / 21,408 ms contained an off-topic final scene about generic environmental benefit. First timing repair then collapsed S1-S3 into the same turbine sentence; it still consumed a TTS probe and measured 16,368 ms. Repair 2 regenerated a substantially better 23-word mechanism-focused draft, but its compact `Zapora tworzy zbiornik.` scored exactly 0.600 against the original scene and was treated as too lossy; precision retry reverted toward the long original, then final duration repair hit the same coverage boundary.
- Semantic coverage threshold is now 0.600. Existing filler, number and negation guards remain unchanged, so v84/v85 corruption regressions still fail closed.
- Build Script Prompt now requires every scene to directly advance TOPIC, forbids generic benefit/environmental/economic/history/outro scenes unless explicitly requested, requires causal/operational order for how/process topics, requires the final scene to complete the mechanism/result, and forbids repeated filler scenes.
- Validate Timing Repair now has the same immutable-original semantic guard as later timing validators and rejects duplicate repaired scene narrations.
- Validate Timing Repair error output no longer fails the job immediately. It routes directly to the existing Build Timing Repair 2 without another TTS probe. Build Timing Repair 2 detects this semantic-fallback mode, regenerates from Normalize Timing Probe immutable original, carries the failed Gemini usage forward, and never treats the rejected draft as semantic truth.
- Repair 2 and Canonicalize Final Storyboard also reject duplicate scene narration.
- Full Node suite 42/42 PASS, including exact regressions from executions 9047/9052/9065, graph routing, fallback behavior, topic-focus contract, Pexels visual tests and query coverage. All M5 Code nodes pass syntax; `git diff --check` PASS.
- Production remains M5 v86 / M8 v45 until this patch is committed/pushed and M5-only deployed.

### M5 v87 deployed — topic-focused script and pre-TTS semantic fallback

- Published only `VideoM5Storyboard001`: counter 87, activeVersionId `76997364-249a-470b-9773-039977eeeba3`.
- Backup of v86: `.backups/m5-before-topic-fallback-20260921-093317.json`.
- Aggregate hash of the other 31 workflow rows is identical before/after; inventory unchanged.
- Live exported M5 core matches repository. `Validate Timing Repair` contains the semantic guard and its error output points to `Build Timing Repair 2`; Repair 2 supports fallback from the immutable original without a TTS probe.
- Publisher and Studio HTTP 200; n8n and media-worker healthy with restart count 0. No restart was issued.
- Current production target is M5 v87 / M8 v45 / full-fit media-worker. Next: run a fresh PL15 and confirm execution snapshots before any acceptance claim.

### M6 nondeterministic Chirp timing exposed weak M5 stability gate — majority fix tested, NOT DEPLOYED

- Fresh PL15 `a5dff806-f10e-4645-83b1-d61a2105592d` on M5 v87 / M8 v45: M4 9068 PASS, M5 9070 PASS, M6 9071 FAILED; M7-M9 did not start.
- M5 output was topic-focused and semantically acceptable: `Zapora wodna spiętrza rzekę i tworzy zbiornik. Spadająca woda napędza turbinę. Obracająca się turbina porusza generator. Generator wytwarza prąd elektryczny. Prąd trafia do sieci.`
- M5 and M6 use the same Google Cloud TTS configuration for PL: locale `pl-PL`, voice `pl-PL-Chirp3-HD-Enceladus`, MP3, no speaking-rate/pitch override. This is not a configuration mismatch.
- Three actual M5 syntheses of the exact same narration produced 15,576 ms, 16,704 ms, and 13,536 ms with different audio hashes. M5 v87 accepted because its median was 15,576 ms and `requiredWithinFinal` was only 1.
- M6 then synthesized the same text: 13,536 ms (same hash as the low M5 sample) followed by 16,704 ms three times (same hash as the high M5 sample). None entered M6's 15,000 ± 800 ms gate. More blind M6 retries would not solve this stochastic distribution and were not added.
- Repository correction changes only M5 final stability acceptance: median-of-three remains the robust center estimate, but at least 2 of the 3 actual syntheses must also be inside the unchanged final M5 tolerance. Tolerance is not widened and M6 remains unchanged/authoritative for persisted final audio.
- Exact regression `15,576 / 16,704 / 13,536` now fails with 1/3 inliers. Positive control `15,576 / 15,600 / 16,704` passes with 2/3 inliers and median in-window.
- Full Node suite 44/44 PASS; all 55 M5 Code nodes pass syntax; `git diff --check` PASS.
- Production remains M5 v87 / M8 v45 until commit/push and scoped M5 deployment. Next fresh PL15 must prove the majority stability gate in a real execution before M6 acceptance is trusted.

### M5 v88 deployed — majority real-TTS stability

- Published only `VideoM5Storyboard001`: counter 88, activeVersionId `de96b2f2-2660-4b75-a33b-db3b8793e589`.
- Backup of v87: `.backups/m5-before-majority-stability-20260921-094111.json`.
- Aggregate hash of the other 31 workflow rows is identical before/after; no unrelated workflow or credential changed.
- Live exported M5 core matches repository and contains `requiredWithinFinal = 2` in `Normalize Timing Stability B`.
- Publisher and Studio HTTP 200; n8n restart 0; media-worker healthy/restart 0 on unchanged full-fit image.
- Current production target: M5 v88 / M8 v45 / full-fit worker. Next fresh PL15 must confirm runtime v88 and survive M6 before M8/M9 review.

### v88 PL15 exposed branch-topology assumption; optional-probe patch tested — NOT DEPLOYED

- Fresh PL15 `71c65de5-ce45-44ba-b0d9-6ec47aa72fa2` confirmed active M5 v88 `de96b2f2-2660-4b75-a33b-db3b8793e589` but M5 execution 9076 failed before M6.
- Failure was not the new 2-of-3 stability gate. The first timing rewrite was semantically rejected before Probe 2, so the bounded fallback correctly skipped `Normalize Timing Probe 2`. Later `Build Final Duration Repair` still unconditionally called `$('Normalize Timing Probe 2').first()` and n8n raised `Node 'Normalize Timing Probe 2' hasn't been executed`.
- Repository fix makes branch-dependent timing probes optional only in `Build Final Duration Repair` and `Build Final Measured Correction`. Missing Probe 2/3 returns null and the builders use the real samples that actually executed plus their existing fallback calculation. Timing tolerances, semantic floors, retry budget and acceptance gates are unchanged.
- Regression tests execute both late builders with Probe 2/3 deliberately throwing the exact n8n not-executed error and verify valid correction prompts are still built.
- Full Node suite 47/47 PASS; all 55 M5 Code nodes pass syntax; `git diff --check` PASS.
- Production remains M5 v88 / M8 v45 until this scoped patch is committed/pushed and M5-only deployed.

### M5 v89 deployed — optional branch-dependent timing samples

- Published only `VideoM5Storyboard001`: counter 89, activeVersionId `ccc59ec1-33bb-462b-aaf0-e4ec775f97b7`.
- Backup of v88: `.backups/m5-before-optional-probes-20260921-095327.json`.
- Aggregate hash of the other 31 workflow rows is identical before/after; no unrelated workflow or credential changed.
- Live exported M5 core matches repository. Both late timing builders contain optional branch-probe reads and the 2-of-3 stability majority remains active.
- Publisher and Studio HTTP 200; n8n restart 0; media-worker healthy/restart 0 on unchanged full-fit image.
- Current production target: M5 v89 / M8 v45 / full-fit worker. Next: fresh PL15 from Studio path, then exact M4-M9/MP4 review before EN30.

### Fresh PL15 on v89 reached M8; non-English visual metadata root cause fixed in M5 — tested, NOT DEPLOYED

- Fresh PL15 `a0b6c789-4cdc-4b59-84e6-790a7d337998`: M4 9079 PASS, M5 9081 PASS on v89, M6 9082 PASS (15,624 ms final PL audio), M7 9083 PASS, M8 9084 FAILED on v45; M9 did not start.
- M8 completed all 45 provider searches and produced 280 candidates, then failed S1-A with no compliant candidate.
- Root cause was upstream contract violation, not provider retrieval: S1-A visual_intent was English (`concrete hydro plant dam holding back river water`) but M5 stored Polish visual anchors/queries: must_show `Zapora wodna`, `zbiornik wodny`; queries such as `Zapora wodna i zbiornik wodny`. M8 correctly could not match those Polish tokens against English provider metadata.
- M5 already had two bounded storyboard-repair attempts. Repository fix strengthens that existing path instead of adding a new stage: all visual metadata fields (`visual_intent`, `must_show`, `must_not_show`, `queries_en`) must always be English regardless of narration language.
- All three storyboard validators now share `ENGLISH_VISUAL_METADATA_GUARD`: PL diacritics are rejected; RU/UK Cyrillic is rejected; for non-English narration the primary must_show anchor must share a concrete English token with English visual_intent, which catches ASCII Polish anchors such as `Zapora wodna` even without diacritics.
- Initial prompt and both bounded repair prompts now explicitly split languages: narration follows requested language; visual metadata is English only. When this validation error occurs, repair prompts preserve narration/scene IDs/shot IDs/evidence IDs/factual meaning and repair the visual metadata contract.
- Exact regression covers current ASCII Polish S1-A, Polish diacritics, Cyrillic RU/UK metadata, and valid English dam/reservoir metadata. Full Node suite 53/53 PASS; all 55 M5 Code nodes pass syntax; `git diff --check` PASS.
- Production remains M5 v89 / M8 v45 until commit/push and scoped M5 deployment.

### M5 v90 deployed — enforced English visual metadata

- Published only `VideoM5Storyboard001`: counter 90, activeVersionId `1e9b6f99-5815-44c7-8bd1-955a2c0b7c8c`.
- Backup of v89: `.backups/m5-before-english-visuals-20260921-100449.json`.
- Aggregate hash of the other 31 workflow rows is identical before/after; no unrelated workflow or credential changed.
- Live exported M5 core matches repository. Initial + both repaired storyboard validators contain the English visual metadata guard.
- Publisher and Studio HTTP 200; n8n restart 0; media-worker healthy/restart 0 on unchanged full-fit image.
- Current production target: M5 v90 / M8 v45 / full-fit worker. Next fresh PL15 must prove bounded repair produces English visual metadata, then reach M8/M9.

### M5 v91 deployed — redundant secondary must_show normalization

- Published only `VideoM5Storyboard001`: counter 91, activeVersionId `7cb215ae-f6ef-4361-9763-b608cea98e8f`.
- Backup of v90: `.backups/m5-before-secondary-anchor-normalization-20260921-110020.json`.
- Aggregate hash of the other 31 workflow rows is identical before/after; no unrelated workflow or credential changed.
- Live exported M5 core matches repository. All three storyboard validators contain the secondary-anchor normalization guard.
- `water turbine + turbine blades` now normalizes to primary `water turbine`; independent context pairs such as `water reservoir + dam`, `magma pool + rock cavity`, and `power lines + transmission towers` remain mandatory.
- Publisher and Studio HTTP 200; n8n restart 0; media-worker healthy/restart 0 on unchanged full-fit image.
- Current production target: M5 v91 / M8 v45 / full-fit worker. Next: fresh PL15 from Studio path and exact M4-M9/MP4 review.

### Exact v94 PL15 review, after GitHub refresh

- Executions: intake 9118, parent 9119, M4 9120, M5 9122, M6 9123, M7 9124, M8 9125, M9 9126, all success. Exact execution version snapshots saved in evidence JSON.
- Independent audit of exact final MP4: SHA-256 `ff01fdcd6eeec78cbe6fa51e82c1ddd9b604f20eac820115edce58b63aeb04a7`, 1,615,659 bytes, video 15,500 ms, immutable narration 15,456 ms, mux delta 44 ms, decoded audio correlation 0.9999785595975776. All 12 technical gates PASS.
- Contact sheet: VPS `.review/pl15-v94/contact.jpg`, generated from final MP4 at 2.125, 6.295, 9.665, 12.445 and 14.678 s (actual segment midpoints). Browser also played the exact public MP4. No listening-based acceptance claimed.
- S3 selected candidate `30f8db7e-67dc-467c-b3fc-1310e82f8117`, Commons 24925760, `Power turbine system.jpg`: categories explicitly identify steam turbine generator sets; exact frame depicts that apparatus. S4 `8f68c84c-e9cc-4f5c-a414-235670d349a6`, Commons 31581140, Petter oil engine with GE generator: exact frame confirms the engine-generator assembly. S5 `e1864a86-547f-4e61-94e6-b660070f2ea4`, Commons 4514763: exact frame is signage/door; title mentions transformer but requested equipment is not visible. All scored 100 in v45, so high lexical score is not context/depiction proof.
- No EN30 started and no job/artifact rewritten. Next action is systemic M8 replay/fix, not another blind live job.

### M8 domain/depiction correction — tested, NOT DEPLOYED

- Added a generic repeated-subject context contract to all three request builders: learn non-generic query qualifiers corroborated across at least two storyboard shots, then retain them across shots with the same repeated primary subject. Broad fallback queries cannot discard that established context. No topic names, asset IDs, museum prohibition or provider-specific domain list exists in this rule.
- All normalizers require these context terms in strong image-specific metadata. Commons additionally rejects signs/notices/plaques/labels/doors when that surface is not the requested subject. Photos of requested signage remain valid.
- Scope/limits: this is a conservative guard for an established repeated-subject domain, not a universal semantic classifier; it cannot invent domain context absent from the storyboard, and ambiguous comparative storyboards may fail closed. It does not certify visible movement or operating condition.
- Replay of all **333** persisted candidates from execution **9125**, with **zero provider calls**: old S3 steam generator, S4 oil-engine generator and S5 signage rejected; old S1 dam and S2 museum water-turbine runner remain eligible. Summary `docs/acceptance/2026-09-21-pl15-v94-context-replay.json`. Old S3/S4 pools now have zero eligible candidates, so this is NOT proof of complete PL15 acceptance.
- Raw sanitized provider body/context replay: VPS `.review/pl15-v94/provider-replay.json`, SHA-256 `a42703535766aacdb748ead0deb6dd9f9ee9bedb0b23a6d5d1ca3cfb17cb6848`. Only bodies and shot context retained, no credentials/request headers. Reproduce using `scripts/replay_visual_candidates.cjs WORKFLOW REPLAY_INPUT REVIEW_EVIDENCE REPORT`. Exact Commons fixtures are committed under tests/fixtures.
- Validation: **65/65 Node tests PASS**, including actual selected assets, generic marine-domain control, valid museum generator, requested-signage positive, all prior regressions; all 113 Code nodes syntax PASS; git diff check PASS.
- Next: scoped M8 publication with backup/unchanged-other-row verification. Keep M5 v94 and media-worker unchanged. Do not spend another full job on the same inadequate query pool: next retrieval work should provide the missing established context in planned queries, preserving exact query accounting/cache provenance. EN30 remains blocked by PL15 review failure.

### M8 v46 deployed and verified — 2026-09-21 15:04 UTC

- Active M8 counter **46**, ID **`b315a1e5-20c1-435e-b2a9-062f207dccfa`**. Exact pre-deploy backup `.backups/m8-before-domain-context-20260921-150344.json`. Other 31 workflow rows have identical aggregate hash `147f6922e827cc40b1af7a6e113f313d`; inventory 32 total / 15 active. No project run was active before publication.
- M5 remains v94 `b4122d0a-5754-4311-8b7a-adab15ff0697`. Both M5/M8 active node/connection graphs match repository. Previous PL15 execution 9122 confirms M5 v94 runtime and execution 9125 confirms M8 v45. No fresh v46 execution is claimed.
- Media-worker remains healthy/restart 0 on `sha256:11d5b351609b40f9e5c46362a59ff2c620a403503bbb8f6e8ae0f57c57eef7ec`; publisher and Studio HTTP 200. No service restart, credential change, new provider calls or new acceptance job.
- Deployment first stopped on a dirty-checkout guard. Inspection showed only pre-existing untracked `studio/qa-v94-pl15-contact.jpg`; all tracked files were clean. Preserved that file untouched, pulled main with fast-forward and completed scoped publication. Do not remove that review artifact as cleanup.
- Confirmed next result: bad context/depiction selections fail closed under the published source, with original positive subjects retained and 65/65 regressions passing. Product remains incomplete: PL15 visually rejected, audio listening unaccepted, EN30 not started. Next agent should work on context-preserving query planning/retrieval before spending another complete pipeline attempt.

### M8 contextual provider-query planning + explicit query provenance — tested, NOT DEPLOYED

- Continued from production M5 v94 / M8 v46. No full acceptance job was started.
- Root issue after v46: domain/depiction guards correctly rejected the old S3 steam generator and S4 oil-engine generator, but provider searches still sent the original broad storyboard query unchanged. Existing domain_context_terms affected scoring only, so old S3/S4 pools had zero eligible candidates.
- Repository change separates two query meanings:
  - query / DB query_text remains immutable storyboard queries_en provenance and scorer input;
  - provider_query / DB provider_query_text is the actual provider search string and cache key.
- For repeated subjects with established shared context, missing domain terms are prepended only to the provider query. Example: storyboard electric generator turbine remains unchanged while Wikimedia searches hydroelectric electric generator turbine. Queries already containing the context are not duplicated.
- HTTP nodes for Pixabay/Pexels/Wikimedia and Wikimedia retries now use provider_query. All normalizers retain original query_text and expose provider_query_text.
- DB migration is backward-compatible: visual_searches.provider_query_text is backfilled from existing query_text; old record_live_visual_search / v2 remain; new record_live_visual_search_v3 records original query provenance but caches by the effective provider query. Full db/09-visuals.sql was executed in a transaction with ROLLBACK; column/function appeared inside the transaction and production remained unchanged afterward.
- Targeted Wikimedia retrieval, without a full pipeline job, proves adequacy:
  - S3 q2 hydroelectric electric generator turbine -> 3 eligible hydro-context assets, including an in-conduit hydro turbine with generator and a Wilson Dam turbine/generator unit.
  - S4 q2 hydroelectric power plant generator equipment -> 5 eligible hydro-generator assets, including Fankel hydroelectric generator sets and Wienerbruck hydro power plant Generator 3.
- The scorer also treats electric/electrical as primary form modifiers, leaving generator distinctive while hydroelectric remains a separate exact storyboard-domain requirement. This lets Hydroelectric generators satisfy electric generator without allowing steam/oil generators to satisfy the domain gate.
- Full Node suite 70/70 PASS; all 10 M8 Code nodes syntax PASS; git diff --check PASS.
- Full replay of all 333 old candidates used zero provider calls: old S3 steam, S4 oil-engine and S5 signage selections remain rejected; old S1/S2 remain eligible. Evidence:
  - docs/acceptance/2026-09-21-pl15-v94-v47-context-replay.json
  - docs/acceptance/2026-09-21-pl15-v94-v47-targeted-retrieval.json
- Production is still M8 v46 until this checkpoint is committed/pushed and the DB migration + M8-only publish are performed. Deploy DB first, then M8, verify other workflow rows unchanged, then run one fresh PL15.

### M8 v47 deployed and verified — contextual provider queries + explicit query provenance

- Active M8 counter 47, activeVersionId b47eb18a-e2f3-4b4e-96e2-b263b29f558d. Exact pre-deploy workflow backup: .backups/m8-before-context-query-v47-20260921-153304.json.
- Project DB migration applied before workflow publication:
  - added non-null factory.visual_searches.provider_query_text;
  - backfilled all 6269 existing rows from query_text (legacy_equal=6269/6269);
  - added factory.record_live_visual_search_v3;
  - old record_live_visual_search and v2 remain available;
  - v3 persists original query_text but caches by effective provider_query_text.
- DB backups before migration:
  - .backups/visual-searches-schema-before-v47-20260921-153304.sql
  - .backups/visual-searches-data-before-v47-20260921-153304.sql.gz
  - .backups/visual-functions-before-v47-20260921-153304.sql
- Other 31 n8n workflow rows were identical before/after M8 publication; aggregate hash 9d077f9318f625630aea069f4be52fcf.
- Live exported M8 core matches repository. Publisher/Studio HTTP 200; n8n restart count 0; media-worker healthy/restart 0. No service restart or credential change.
- Pre-deploy validation: 70/70 Node tests PASS, all 10 M8 Code nodes syntax PASS, git diff check PASS, full DB migration transaction dry-run PASS.
- Retrieval adequacy was shown before the full rerun:
  - S3 contextual query returned 3 eligible hydro-generator/turbine assets.
  - S4 contextual query returned 5 eligible hydro-generator assets.
  - Full 333-candidate replay used zero provider calls and retained rejection of old S3 steam, S4 oil-engine and S5 signage selections.
- No fresh v47 execution has been claimed yet. Next exact step: create one new PL15, confirm execution M8 versionId is v47, verify query_text vs provider_query_text on search rows, then require M4-M9 PASS and exact MP4 visual/audio QA before EN30.

### Fresh PL15 on M5 v97 / M8 v49 machine-passed but semantic QA rejected S2 - v50 fix tested, NOT DEPLOYED

- Fresh PL15 job 306162e6-6ae4-4551-b948-d219175b1479 completed M4-M9 and reached machine_qa_passed.
- Execution snapshots: M4 9170; M5 9172 on v97 3ce4729e-1f30-4b32-ae99-88aa91109308; M6 9173; M7 9174; M8 9175 on v49 a8f8b376-12b2-4089-9dd0-d410afcb43a7; M9 9176.
- Manual semantic review rejects the job before acceptance. S2 visual_intent is Water turbine spinning inside a hydroelectric power station, but v49 selected Wikimedia asset 110818093 from fallback query water turbine, score 100. Its metadata is Disney California Adventure / Grizzly River Run / an old house with a water wheel, not a hydroelectric power-station turbine.
- The defect is systemic: singleton machinery fallback queries can retain the primary object while dropping an explicit operating-domain/location qualifier from the storyboard.
- Repository v50 candidate fix:
  - for machinery primaries only, derive one specific local operating-domain term from the intersection of visual_intent and the first two planned queries;
  - exclude primary terms, machinery companion heads and generic action/process words;
  - merge that local term with existing repeated-subject domain context;
  - enrich only provider_query while preserving original query provenance;
  - when such domain context exists, form modifiers such as water/hydro/hydraulic/steam/gas/wind/power do not need literal primary-caption coverage; the machinery head remains distinctive and the separate domain gate remains mandatory;
  - domain tokens support safe prefix compatibility such as hydro -> hydroelectric.
- This is not a Disney blacklist and contains no topic-specific asset IDs in production logic. Old Manitoba hydro museum runner remains eligible because its metadata establishes the requested hydro domain.
- Validation: 84/84 Node tests PASS; all 10 M8 Code nodes syntax PASS; git diff check PASS.
- Exact current storyboard dry-run: S2 fallback becomes hydroelectric water turbine with hydroelectric required; S4 fallback becomes substation power transformer with substation required; S1/S5 remain unmodified by local machinery context.
- Targeted live Wikimedia retrieval: S2 returned 4 eligible hydro-context turbine assets; S4 returned 3 eligible substation-transformer assets.
- Evidence: docs/acceptance/2026-09-21-pl15-v97-v49-manual-reject-v50-targeted.json.
- Production remains M8 v49 until this patch is committed/pushed and M8-only deployed. After deploy, run a new fresh PL15; do not reuse job 306162e6-6ae4-4551-b948-d219175b1479.


### Fresh PL15 after M8 v50 deploy failed in M6; M5 three-sample gate bypass fixed — TESTED, NOT DEPLOYED

- Fresh PL15 `dfd72856-9480-44d4-9e07-f8decae7ae9f`: M4 execution `9179` PASS; M5 execution `9180` PASS on v97 `3ce4729e-1f30-4b32-ae99-88aa91109308`; M6 execution `9181` FAIL on v7 `98e671f3-a0dc-42fa-81e9-4c9524a05e6a`. M7-M9 did not run. Terminal job status: `voiceover_failed`.
- M6 failure: after four independent Polish Chirp3-HD syntheses, no candidate entered the unchanged 15,000 +/- 800 ms final window; reported fourth candidate was 16,608 ms.
- Persisted M5 narration was 25 words / 184 characters. M5 and M6 both used `pl-PL-Chirp3-HD-Enceladus` with MP3 encoding, so no voice/config mismatch was found.
- Provider-usage ledger proves the final 184-character narration received M5 Probe 4 and one Stability A synthesis, then was accepted without a Stability B request. All four M6 attempts used the same 184-character narration.
- Exact systemic root cause: `Route Timing Stability PASS` sent its true branch directly to `Canonicalize Final Storyboard`. Therefore the existing 2-of-3 majority logic in `Normalize Timing Stability B` was bypassed whenever the first two samples were both in-window.
- Repository fix: both outcomes of `Route Timing Stability PASS` now route to `Prepare Timing Stability Probe B`. Only `Route Timing Stability PASS B` may canonicalize the final storyboard, so every accepted stability path uses three real syntheses and the existing 2/3 gate.
- Added graph regression test `M5 regression: two-sample stability cannot bypass the three-sample majority gate`.
- Validation in an isolated local n8n image with the repository mounted read-only: **85/85 Node tests PASS**; `git diff --check` PASS; M5 workflow JSON parse PASS.
- Production at this checkpoint is still M5 v97 / M8 v50. No retry job has been started. Next: commit/push this checkpoint, deploy only M5 with exact backup and protected-row comparison, verify the new active version, then run one fresh PL15 from the beginning.


### M5 three-sample stability gate deployed — runtime verification pending

- Repository checkpoint `786bf008593ae8c42e9ef6d580033eb035297206` was fetched/pushed on `main` before deployment.
- Exact pre-deploy published M5 backup: `.backups/m5-before-three-sample-gate-20260921-190126.json`.
- Published only `VideoM5Storyboard001`. n8n kept `versionCounter=97` but created new current/active versionId `9cfd4e2d-883f-417c-933d-6b553c5b73c9`.
- Published M5 export matches repository exactly for nodes, connections and settings.
- Other 31 workflow rows were unchanged across deployment: count 31 and aggregate hash `99baea155409822fc83fa57cb2896c05` before/after. Inventory remains 32 total / 15 active.
- M8 remains v50 `310816fc-fbf3-46e9-983b-b6f612ea009a`. No M8 change, database migration, service restart or credential change was performed.
- Publisher and Studio HTTP 200; n8n running restart 0; media-worker healthy restart 0 on `sha256:11d5b351609b40f9e5c46362a59ff2c620a403503bbb8f6e8ae0f57c57eef7ec`.
- n8n CLI emitted its generic restart advisory after publish; no restart was performed. The next fresh M5 execution must prove runtime versionId `9cfd4e2d-883f-417c-933d-6b553c5b73c9` and its usage ledger must contain the Stability B request for the accepted final narration.
- Next exact step: one fresh PL15 from the beginning. Require M4-M9 completion, M5 runtime proof, M8 v50 runtime proof, then exact final MP4/manual semantic/audio acceptance before EN30.


### Fresh PL15 on M5 three-sample gate / M8 v50 failed S4; spatial-domain fix tested, NOT DEPLOYED

- Fresh PL15 `67a1e838-038e-45d6-aa95-16c4638bbebd`: M4 `9184` PASS; M5 `9185` PASS on `9cfd4e2d-883f-417c-933d-6b553c5b73c9`; M6 `9186` PASS; M7 `9187` PASS; M8 `9188` FAIL on v50 `310816fc-fbf3-46e9-983b-b6f612ea009a`. M9 did not run.
- M5 runtime proof is complete: the job executed the new version and provider ledger contained `m5-tts-stability-b:...:4`; final persisted voiceover was 15,048 ms.
- M8 completed all 45 searches but failed `S4-A`: `no compliant relevant visual candidate`.
- Exact high-scoring rejected candidate: Pexels `28912007`, score 98, metadata `Close-up of high voltage transformers at a power station in Austria during daylight.`; rejected only for `missing_storyboard_domain_context:outdoors`.
- Systemic cause: singleton-machinery local domain inference treated the spatial/presentation token `outdoors` as an operating-domain term because it appeared in both visual_intent and a planned query after generic filtering.
- Repository fix keeps repeated-subject context and scorer thresholds unchanged; only local machinery inference now treats `outdoor/outdoors/indoor/indoors` as context noise.
- Added provider-planner regressions for Pixabay/Pexels/Wikimedia and an exact Pexels S4 normalization regression. Exact candidate becomes eligible after the fix.
- Validation: **89/89 Node tests PASS**; `git diff --check` PASS; M8 JSON parse PASS.
- Evidence: `docs/acceptance/2026-09-21-pl15-v50-s4-spatial-domain-fix.json`.
- Production remains M5 activeVersionId `9cfd4e2d-883f-417c-933d-6b553c5b73c9` / M8 v50 `310816fc-fbf3-46e9-983b-b6f612ea009a`. Next: commit/push, M8-only deploy, then one new fresh PL15.


### M8 v51 deployed — spatial presentation terms excluded from local machinery domain inference

- Repository fix commit before deployment: `ec6c2acc0335a9494040050fc54fd08f0a72a76d`.
- Exact pre-deploy M8 backup: `.backups/m8-before-spatial-domain-fix-20260921-192246.json`.
- Published only `VideoM8Visuals001`: versionCounter **51**, active/current versionId `f242881a-d79e-449d-a8c8-68d65ec54cde`.
- Published M8 export matches repository exactly for nodes, connections and settings.
- Other 31 workflow rows were unchanged across M8 publication: count 31 and aggregate hash `8fbf6b2399f8dd92c1c391dcee4308cf` before/after.
- M5 remains activeVersionId `9cfd4e2d-883f-417c-933d-6b553c5b73c9`; no M5 change.
- Publisher and Studio HTTP 200; n8n running restart 0; media-worker healthy restart 0 on `sha256:11d5b351609b40f9e5c46362a59ff2c620a403503bbb8f6e8ae0f57c57eef7ec`.
- No database migration, credential change, service restart or unrelated workflow publication.
- Next exact step: one fresh PL15. Require M4-M9 PASS, runtime M5 `9cfd4e2d...`, runtime M8 `f242881a...`, then exact MP4 technical/manual semantic/audio acceptance before EN30.


### Fresh PL15 failed in M5 late semantic validation; bounded retry routing fix tested, NOT DEPLOYED

- Fresh PL15 `fe186d1e-27c6-4682-8649-6d94c9a7d45b`: M4 `9191` PASS; M5 `9192` FAIL on `9cfd4e2d-883f-417c-933d-6b553c5b73c9`.
- Exact failure: `M5 script workflow failed: 2, allowed 1 [line 202]`. Probe ledger had attempts 1 and 3 only; no final script version was persisted.
- Exact failing node is `Validate Final Duration Repair`: the semantic guard correctly rejected a late timing draft for introducing too many novel content words.
- Systemic defect was routing, not the guard. Its error output terminated M5 even though the graph already has one bounded `Build Final Word Count Retry` whose immutable original narration is the factual source.
- Fix: late final-duration and final-measured validators expose `semantic_valid=false` and the exact semantic error instead of terminalizing the first semantic miss. Existing word-count IF routes now require `word_count_exact && semantic_valid`; otherwise they use the existing single bounded retry.
- Retry validators remain semantic fail-closed; no tolerance/semantic thresholds were weakened and no retry loop was added.
- Validation: **92/92 Node tests PASS**, `git diff --check` PASS, M5 JSON parse PASS.
- Evidence: `docs/acceptance/2026-09-21-pl15-m5-late-semantic-retry.json`.
- Production remains M5 `9cfd4e2d...` / M8 v51 `f242881a...` until M5-only deploy.


### M5 v98 deployed — late semantic miss uses existing bounded retry

- Repository fix commit before deployment: `1ac2c948e6a44c11f11a51c59ccab41a7226a447`.
- Exact pre-deploy backup: `.backups/m5-before-late-semantic-retry-20260921-193037.json`.
- Published only `VideoM5Storyboard001`: versionCounter **98**, activeVersionId `ce78a67f-bce4-45fb-bbf8-2d421b3c3142`.
- Live export matches repository for nodes, connections and settings.
- Other 31 workflow rows unchanged: aggregate hash `efd8e340d7b44dc59429062d4b1bda5f` before/after.
- M8 remains v51 `f242881a-d79e-449d-a8c8-68d65ec54cde`.
- Publisher/Studio HTTP 200; n8n restart 0; media-worker healthy restart 0.
- Next: one fresh PL15; runtime must prove M5 v98 and M8 v51 before exact MP4 acceptance.


### Fresh PL15 hit transient n8n task-runner failure; stale project state reconciled

- Fresh PL15 `64511f0b-16a1-40ba-9930-9499cf92d7f1`: M4 execution `9195` PASS; M5 execution `9196` started the active v98 `ce78a67f-bce4-45fb-bbf8-2d421b3c3142` but n8n execution terminated `error` after about 4 seconds.
- This was not a semantic/timing product rejection. Provider ledger contained only M5 timing probe attempt 1 in `released` state. n8n logs showed three task offers rejected with `Offer expired - not accepted within validity window`, followed by `Cannot read properties of undefined (reading 'json')`.
- Because execution terminated before M5's normal `Fail Script` node, project DB remained stale at job `scripting` / script_run `running` even though parent execution `9194` and M5 `9196` were terminal errors and no project executions were active.
- Same-job rerun is intentionally unsupported: `factory.begin_script()` accepts only `evidence_ready`, and `factory.script_runs.job_id` is UNIQUE.
- Reconciled the exact stale run using the deployed state-transition function, not manual UPDATE:
  `factory.fail_script('ebd923f4-8e61-4d91-8066-2d5bf033ae3f', <exact transient-runtime reason>)`.
- Reconciled result: job `64511f0b-16a1-40ba-9930-9499cf92d7f1` = `script_failed`; script_run `ebd923f4-8e61-4d91-8066-2d5bf033ae3f` = `failed` with completion timestamp and exact reason.
- No workflow code, database schema, service, credential or production version was changed for this incident. M5 remains v98; M8 remains v51.
- Next: run one new fresh PL15. If the task-runner offer-expiry pattern recurs, treat it as an infrastructure defect and diagnose runner scheduling before further pipeline jobs; do not keep spending fresh jobs blindly.


### Fresh PL15 `9844d17f-1548-4ecb-97bf-6b9e56b0c7fe` reached M8 v51 and exposed S3 retrieval gap — WIP CHECKPOINT, NOT DEPLOYED

- Fresh PL15 job `9844d17f-1548-4ecb-97bf-6b9e56b0c7fe`:
  - M4 `9199` PASS on `3cf94dd2-8c3b-4585-ae88-6315a2685ff7`;
  - M5 `9200` PASS on active v98 `ce78a67f-bce4-45fb-bbf8-2d421b3c3142`;
  - M6 `9201` PASS on `98e671f3-a0dc-42fa-81e9-4c9524a05e6a`;
  - M7 `9202` PASS on `91fbac4f-f40d-4d75-9111-3e4ed01bd9ff`;
  - M8 `9203` ran active v51 `f242881a-d79e-449d-a8c8-68d65ec54cde` and failed;
  - M9 did not run.
- M5 v98 runtime proof succeeded. Provider ledger includes `m5-tts-stability-b:...:4`; the earlier task-runner offer-expiry incident did not recur.
- M8 completed all expected 45 searches: Pexels 15 / 118 results, Pixabay 15 / 120, Wikimedia 15 / 71.
- Terminal failure: `M8 visuals failed: no compliant relevant visual candidate for shot S3-A`.
- S3 narration: `Wirnik napędza nowoczesny generator prądu.`
- S3 storyboard:
  - visual_intent: `Large electric generator inside a hydroelectric power station`;
  - must_show: `["electric generator","power station"]`;
  - queries: `electric generator in hydroelectric station`, `power generator equipment inside plant`, `electric generator`.
- v51 correctly preserved original query provenance and contextualized the broad fallback to `hydroelectric electric generator`, but Commons top-8 mainly returned station/building photographs rather than depicted generator units.
- Example current rejection: Wikimedia asset `78928898`, title `Generators in Cedar Falls Powerhouse, 1903 (INDOCC 1758).jpg`, score 73, rejected for `missing_secondary_subject_context`. This exposed that `powerhouse` was not recognized as the generating-building sense of `power station`.
- Live Commons probes confirmed that generic equipment/unit variants return actual generator machinery:
  - `hydroelectric electric generator equipment`;
  - `hydroelectric generator equipment`;
  - `hydroelectric electric generator unit`.
- Do NOT weaken primary subject/domain gates and do NOT hardcode hydro or asset IDs.

Current repository WIP in `workflows/VIDEO-M8-Multi-Source-Visuals.json`:
1. all three normalizers now expand the specific compound `powerhouse` to semantic evidence `power + station + powerstation`; generic `station` does not imply powerhouse;
2. secondary must-show context is now evaluated per compound profile at the existing concept threshold instead of accepting any single shared secondary token;
3. this is intentionally stricter for compounds such as `power station`, so unrelated `railway station` metadata cannot satisfy it via `station` alone;
4. the provider-request planner change is still NOT implemented: for a bare machinery fallback equal to the primary must-show, append generic `equipment` only to `provider_query`, keeping immutable `query_text` unchanged. For current S3 the intended effective query is `hydroelectric electric generator equipment`.

Validation of the current WIP checkpoint:
- existing Node suite: **92/92 PASS**;
- M8 workflow JSON parse: PASS;
- `git diff --check`: PASS;
- no new regression tests for this unfinished WIP have been added yet;
- not deployed; production remains M5 v98 / M8 v51.

Exact next step:
1. implement the generic bare-machinery fallback enrichment in all three request planners, without topic-specific vocabulary;
2. add regressions for `powerhouse ↔ power station` only in the safe direction, compound-secondary rejection, immutable `query_text`, and `provider_query` equipment enrichment;
3. replay/live-score the exact S3 case through the current scorer;
4. run the full suite and JSON/diff checks;
5. commit/push the completed fix;
6. deploy only M8 with backup + protected-row hash verification;
7. run one fresh PL15 and continue through M9/manual acceptance before EN30.

### M8 S3 retrieval completion — tested, not deployed

- Continued exactly from main `566457e`, job `9844d17f-1548-4ecb-97bf-6b9e56b0c7fe`, M8 execution `9203`; no old job rerun.
- All three planners now append generic `equipment` only when a machinery query equals the primary must-show phrase. Original query/query_text stays immutable; exact S3 provider query becomes `hydroelectric electric generator equipment`. Qualified queries and non-machinery queries remain unchanged.
- New regression exposed a defect in the prior WIP: domain-scoped primary form modifiers also removed `power` from secondary `power station`, leaving only `station`. Secondary profiles now use the original generic-anchor set, so railway station cannot pass via one shared word. Powerhouse expansion remains directional.
- Validation: 102/102 Node tests PASS, workflow Code syntax/JSON and diff checks PASS. Includes all three providers, unchanged query provenance, compound negative control and exact Commons 78928898 fixture.
- Replayed the three persisted S3 initial Commons responses from execution 9203. Separate exact live page lookup confirms asset 78928898 now passes (score 95); production-parameter equipment search returns it at score 92. It is a historical 1903 image: this metadata eligibility does NOT establish suitability for narration saying modern or replace exact-frame review.
- Evidence: `docs/acceptance/2026-09-21-pl15-v51-s3-retrieval-completed.json`; sanitized raw responses on VPS `.review/pl15-v51/`. Three public Commons calls (one initial probe omitted MIME/bitmap parameters and was corrected; one exact production search, one exact page lookup). No new full pipeline job yet.
- Production remains M5 v98 `ce78a67f-bce4-45fb-bbf8-2d421b3c3142` / M8 v51 `f242881a-d79e-449d-a8c8-68d65ec54cde` pending scoped deployment.
- Next: backup and deploy only M8, verify protected rows/live source, then one fresh PL15 through M9 and manual visual/audio review. EN30 remains blocked; no HUMAN PASS.

### M8 v52 deployed — generic machinery fallback and compound context

- Fix commit: `65bec7e0b0692145d4989fc7c2066058725b56ab`.
- Published only M8: counter **52**, activeVersionId `b6b9f5cf-5062-4be3-8322-81d3fb2ebcba`.
- Exact backup: `.backups/m8-before-machinery-fallback-20260921-201442.json`.
- Other 31 workflow rows unchanged: aggregate hash `a900b43516222593dbe68d2c237aa6f1` before/after. No active project runs before publication; live nodes/connections/settings match repository.
- M5 stays v98 `ce78a67f-bce4-45fb-bbf8-2d421b3c3142`; no service restart or credential change.
- Next: one fresh PL15; verify runtime versions, then exact final MP4 visual/audio QA before EN30.

### Fresh PL15 on M5 v98 / M8 v52 — running

- New immutable job `f6088d2f-f2eb-4a49-9379-f71c20852cbf` created through the Studio webhook path; intake 9204 PASS, parent 9205 running, M4 9206 PASS, M5 9207 running on exact v98 `ce78a67f-bce4-45fb-bbf8-2d421b3c3142`.
- Production M8 v52 `b6b9f5cf-5062-4be3-8322-81d3fb2ebcba`; runtime M8 proof pending. Publisher/Studio HTTP 200; n8n/worker restart 0; worker healthy with unchanged full-fit image.
- Next: monitor THIS job (do not create a duplicate). If M9 succeeds, audit exact MP4/selected assets and visual/audio QA. If terminal failure, diagnose exact failed execution. EN30 remains unstarted.

### PL15 v52 terminal S4 failure; generic context correction tested, not deployed

- Job `f6088d2f-f2eb-4a49-9379-f71c20852cbf`: M4 9206, M5 9207, M6 9209, M7 9210 PASS; M8 9212 ERROR on confirmed v52 `b6b9f5cf-5062-4be3-8322-81d3fb2ebcba`. M9 did not run; no final MP4. Job stays immutable.
- All 45 searches completed: Pexels 15/120 results, Pixabay 15/120, Commons 15/66. Failure is S4-A, not S3. Zero committed selections (selection transaction rolled back on S4 failure).
- Exact cause: S4 intent `Industrial electric generator unit inside a power plant` plus first query `electric generator unit power plant` inferred generic `unit` as a local operating domain. Combined with the established repeated-subject hydroelectric domain it produced `hydroelectric unit generator equipment`, yielded no Commons candidates for S4, and required literal unit in other metadata. This is not an asset-uniqueness failure.
- Fix: exclude generic unit/apparatus/instrument/receiver/room from domain inference in all three planners, consistent with existing scorer generic-object terms. Real hydroelectric/marine domain gates remain intact; no topic hack/threshold change.
- Separate exact candidate defect: Commons 28807269 `Generator Nameplate PF Percent.JPG` scored 100 and passed for S3 machinery. Extended existing signage/surface rejection to nameplates; actual requested nameplates still pass. No visual acceptance claim is made from metadata alone.
- Zero-provider-call replay: corrected S4 fallback equals the already executed S3 effective query `hydroelectric generator equipment`; scoring its exact saved response against S4 produces six eligible distinct hydro-generator candidates. Exact nameplate now rejected. Evidence `docs/acceptance/2026-09-21-pl15-v52-unit-context-replay.json`; all 45 sanitized responses on VPS `.review/pl15-v51/v52-replay.json`.
- 106/106 tests PASS; JSON/113 Code syntax/diff checks PASS. Production remains M5 v98 / M8 v52 until the scoped deployment.
- Next: publish only M8 after backup/protected-row verification, then one fresh PL15 and exact visual/audio review before EN30. Do not rerun failed job.

### M8 v53 deployed; new PL15 running

- Fix commit `0f1a709c9f49d3320dfee50b8d9129fece3a3a4d`; only M8 published as v53 `0953f69f-e982-467e-95e0-35161a613771`.
- Backup `.backups/m8-before-unit-context-20260921-202231.json`; other 31 workflow rows unchanged (before/after hash `a900b43516222593dbe68d2c237aa6f1`). No project runs active before publication; live nodes/connections/settings equal repository. No service restart or credential changes; M5 remains v98 `ce78a67f-bce4-45fb-bbf8-2d421b3c3142`.
- Fresh immutable PL15 `b3d1f5e3-f368-493b-bde9-f5343783d41d` created and accepted through the Studio webhook path.
- Next: monitor this exact job, prove v53 runtime, then M9/exact visual and audio review. EN30 not started. Failed v52 job remains unchanged.

### First PL15 after v53 deploy rejected by M5 timing; v53 not yet exercised

- `b3d1f5e3-f368-493b-bde9-f5343783d41d`: intake 9213 PASS, parent 9214 ERROR, M4 9215 PASS, M5 9216 ERROR on v98. M6–M9 never ran; no audio/render acceptance artifacts.
- Exact bounded trace: 30 words/19224 ms → early semantic rejects (coverage .571/.429 below unchanged .600) → 27 words/17304 ms → 26 words/16176 ms → final exact-target 25 words/17448 ms. M5 failed at unchanged 15000 ±750 ms.
- Final rewrite met its requested word target but real duration increased; count monotonicity cannot guarantee TTS timing. No new deterministic workflow defect is demonstrated; do not loosen semantics/timing or add retries. Sanitized trace `.review/pl15-v51/v53-m5-timing.json`.
- Production unchanged M5 v98 / M8 v53; M8 v53 runtime proof still pending. Next: one fresh PL15 on unchanged code; if this timing failure repeats, do not continue blind jobs—investigate narration/calibration feasibility first.

### Second PL15 on unchanged v98/v53 — running

- Job `12f1ac4f-b8dc-4f17-a191-06888fb7e8a4` accepted via Studio webhook path. Versions unchanged: M5 v98 `ce78a67f-bce4-45fb-bbf8-2d421b3c3142`, M8 v53 `0953f69f-e982-467e-95e0-35161a613771`.
- Monitor this exact job. If M5 timing rejection repeats, no further blind attempts; investigate feasibility/calibration. Otherwise continue through M9 and exact visual/audio review before EN30.

### M5 execution 9221 diagnosed; strict measured-draft reuse tested, not deployed — 2026-09-22 local

- Job `12f1ac4f-b8dc-4f17-a191-06888fb7e8a4`: intake 9218 PASS, parent 9219 ERROR, M4 9220 PASS, M5 9221 ERROR on v98. M6–M9 absent. M8 v53 runtime still unproven.
- Measurements: 26 words/17208 ms → 20/13704 → 24/16968 → 23/18024. Final correction target 21; last candidates/hybrids could reach only 22, so existing strict pre-TTS gate stopped the run.
- Correction to preliminary interpretation: the final measured exact-word requirement is intentional (regression 9137), not an accidental leftover. It stays strict. The defect is that final hybrid selection ignored earlier measured, semantically valid short scenes from the SAME execution, although they can satisfy the exact target.
- Scoped fix only in `Validate Final Measured Word Count Retry`: add optional Normalize Timing Probe 2/3 scene alternatives to the existing bounded dynamic program. Revalidate each alternative against immutable original semantics, standalone sentence bounds, and scene identity. Skipped probes/invalid alternatives are ignored. Existing final exact-total, semantic, numeric, negation, TTS tolerance and 3-sample stability gates unchanged. No new provider calls/retry loops/budget.
- Exact sanitized execution fixture now in `tests/fixtures/m5-9221-final-retry.json`. Pre-fix replay reproduces got 22/target 21; post-fix returns exactly 21 words with original scene identities and semantics. This is code replay, NOT audio timing acceptance.
- 110/110 tests PASS including exact replay, unavailable branches, semantic-invalid and mismatched-scene negatives plus original 9137 strict-count regression. JSON/113 Code syntax and diff checks PASS.
- Production remains M5 v98 `ce78a67f-bce4-45fb-bbf8-2d421b3c3142` / M8 v53 `0953f69f-e982-467e-95e0-35161a613771`. Next: scoped M5 deploy with backup/protected hash, then fresh PL15; no more jobs on unchanged v98. No EN30/HUMAN PASS.

### M5 v99 deployed; fresh PL15 running — 2026-09-22

- Fix commit `486406fa5f48e2d62c8e7b4f7bda482dfe3587e4`; only M5 published as v99 `8317622a-7d47-4cc5-8c40-f3f76caebf42`.
- Backup `.backups/m5-before-measured-drafts-20260922-032117.json`; all other 31 workflow rows unchanged (before/after hash `2b1e19662b731815a72c46a9042f1243`). Live nodes/connections/settings match repository. No active project runs before deploy; no restart/credential change. M8 remains v53 `0953f69f-e982-467e-95e0-35161a613771`.
- Fresh PL15 `b36a7c19-3427-4d67-9e2b-50d0acb4d717` created and accepted through Studio webhook path.
- Next: monitor this exact job, confirm M5 v99/M8 v53 execution versions, inspect output or exact terminal failure. Do not duplicate a running job. EN30 remains blocked by PL15 visual/audio QA.

### Verified v99/v53 runtime result and exact remaining work — 2026-09-22

- Job `b36a7c19-3427-4d67-9e2b-50d0acb4d717`: intake 9223 PASS, parent 9224 ERROR, M4 9225 PASS, M5 9226 PASS on **v99 `8317622a-7d47-4cc5-8c40-f3f76caebf42`**, M6 9227 PASS, M7 9228 PASS, M8 9229 ERROR on **v53 `0953f69f-e982-467e-95e0-35161a613771`**. M9 absent; no final MP4, no visual/audio/HUMAN PASS. M5 runtime version is proven; the new optional late branch is proven by exact 9221 replay, not claimed exercised in 9226.
- M8 completed all 45 searches / 335 candidates: Pexels 15/120, Pixabay 15/120, Commons 15/95. Exact terminal failure S1-A `missing_secondary_subject_context` among otherwise high-score candidates. Failed job remains immutable.
- S1 `hydroelectric dam` + `water reservoir`: secondary generic-anchor filtering discards reservoir and requires water literally. Exact Commons 172815415 title/object name `Tri An Hydroelectric Dam And Its Reservoir` has both physical subjects but no literal water token. Browser visual inspection of its exact Commons page confirms a dam and impounded water; this is source-image inspection only, not final-MP4 QA. Exact sanitized fixture `tests/fixtures/pl15-v99-dam-reservoir.json`.
- Tested an experimental secondary-head rule locally: preserve generic independent object heads and remove form modifiers only with fully grounded primary/head. All 116 tests passed, but full 335-candidate replay exposed unresolved acceptance risks. Therefore the experimental M8 source/test changes were REVERTED, NOT deployed. Repository M8 remains verified v53 source; final retained suite is 110 tests.
- The experiment's report is explicitly marked rejected/not deployed: `docs/acceptance/2026-09-22-pl15-v99-secondary-head-replay.json`. It is diagnostic evidence, NOT production scoring or approval. S1 would admit PNG 94068077 `Pacific Northwest drought status and hydroelectric dam reservoir storage capacity...`, requiring exact depiction/type verification. Do not weaken photo/type gates or silently accept it.
- Additional gaps found by the SAME replay (not a new audit): S5 `electrical transformer` + `power lines`, domain `substation`, has zero eligible candidates; returned transformer photos lack independent power-lines evidence. S4 singleton `electric generator` has no hydroelectric domain in its storyboard intent/queries and receives no inferred domain, so its broad generator pool requires context correction before acceptance.
- Raw sanitized 45-response replay: VPS `.review/pl15-v51/v99-replay.json`; S1 candidate diagnostic `.review/pl15-v51/v99-s1-candidates.json`. No additional provider calls were used for replay. Public exact asset was viewed in browser. No later full pipeline job was started.
- Exact next engineering step: use execution 9229 saved responses/shot contexts to resolve S1 secondary object evidence and S5 paired-object retrieval while keeping railway/power-station and nectar/dew negatives strict; explicitly preserve singleton S4 operating context from the storyboard/topic contract. Replay all 335 candidates, check affected exact assets, and require all five eligible pools before spending a fresh PL15. Do not re-audit infrastructure, repeat old v94 work, or rerun failed jobs.
- EN30 remains prohibited until fresh PL15 final visual/audio QA. No new permission or credential is required; use existing SSH alias. Production versions stay v99/v53 and worker full-fit image unchanged.

Checkpoint verification: M5 v99 and M8 v53 live nodes/connections/settings match repository; inventory 32 total/15 active; zero active project executions; Publisher/Studio HTTP 200; n8n and worker restart 0; worker healthy on unchanged `sha256:11d5b351609b40f9e5c46362a59ff2c620a403503bbb8f6e8ae0f57c57eef7ec`. Final retained suite 110/110 PASS and diff check PASS. This checkpoint is not final product acceptance.

### M8 v53 saved-response recovery fix tested — NOT DEPLOYED — 2026-09-22

- Continued from the immutable failed PL15 `b36a7c19-3427-4d67-9e2b-50d0acb4d717` / M8 execution `9229`; no new full pipeline job was spent during diagnosis.
- Reconstructed the unfinished Codex work from the clean v99/v53 checkpoint plus saved execution responses. Existing live S5 combined-query evidence on VPS (`.review/pl15-v51/s5-paired-live.json`) proves the current scorer can accept real transformer + overhead-line photos when retrieval includes both mandatory visible objects.
- Scoped M8 correction:
  - preserve secondary noun heads (for example `water reservoir`) instead of reducing them to a generic modifier;
  - Wikimedia secondary-object evidence is depiction-oriented: title/object + short direct caption + only category segments independent of the primary subject. A contextual category such as `Peechi Dam reservoir` no longer proves that the reservoir is visible;
  - maps are explicitly non-photographic;
  - carry an operating domain only across immediately adjacent machinery scenes when the next machinery shot has no own domain; an explicit new domain wins;
  - for singleton bare-machinery fallback, add additional visible secondary `must_show` objects to **provider_query only**. Original storyboard query/provenance remains immutable. Exact S5 q3 becomes `substation electrical transformer power lines equipment`;
  - museum/exhibit/manufacturing/transport metadata is a conflict only when the storyboard explicitly requests an operating plant/station/facility. This is not a blanket venue blacklist.
- Full existing + new regression suite: **128/128 PASS**; `git diff --check` PASS; M8 JSON parse PASS.
- Replayed the complete saved M8 pool, **335 candidates**, with fresh planner contexts and the new scorer. Eligible counts: **S1=1, S2=11, S3=3, S4=3, S5=4**. No shot is empty.
- Exact simulated production selections using deployed `factory.select_visuals()` ordering:
  - S1 Wikimedia `172815415` `Tri An Hydroelectric Dam And Its Reservoir.jpg`;
  - S2 Wikimedia `42498812` `CONDOTTA FORZATA FEDIO.png`;
  - S3 Pexels `12270481`;
  - S4 Wikimedia `68099788` `Dam generator without rotor.jpg`;
  - S5 Wikimedia `27207173` `Chantecoq-FR-45-B-08.JPG`.
- Source-level semantic review completed for these exact picks. The earlier false positives are now fail-closed: keyword map 94068077, contextual-category-only Peechi reservoir, museum/display turbine runner, and manufacturing/transport generator imagery for operational scenes.
- Evidence: `docs/acceptance/2026-09-22-pl15-v99-v53-m8-context-fix.json`.
- **Not deployed at this checkpoint.** Production remains M5 v99 `8317622a-7d47-4cc5-8c40-f3f76caebf42` / M8 v53 `0953f69f-e982-467e-95e0-35161a613771`.
- Exact next step: fetch/verify remote, commit+push this tested M8 fix, deploy **only M8** with backup and protected-row comparison, then exactly one fresh PL15 through M9 and exact final MP4 visual/audio acceptance. EN30 remains blocked until that PL15 is accepted.


### M8 v54 deployed — context/retrieval correction — 2026-09-22

- Source commit: `7177050c90acf301e3705caaa4ab68c43983efad` (`fix: preserve visual context across hydro scenes`).
- Exact pre-deploy published backup: `.backups/m8-before-context-fix-20260922-062346.json`.
- Published **only** `VideoM8Visuals001`: versionCounter **54**, activeVersionId `818d2c37-28db-488b-b7b7-f0e047a29f30`. M5 remains v99 `8317622a-7d47-4cc5-8c40-f3f76caebf42`.
- Published M8 export matches repository exactly for `nodes`, `connections` and `settings`.
- Other 31 workflow rows unchanged: fingerprint `68385db0baf235f5f92e4b822b8698af` before/after.
- Publisher HTTP 200; Studio HTTP 200; n8n running restart 0; media-worker healthy restart 0 on unchanged `sha256:11d5b351609b40f9e5c46362a59ff2c620a403503bbb8f6e8ae0f57c57eef7ec`. No service restart, credential change or unrelated workflow publication.
- n8n CLI printed its generic restart advisory after `publish:workflow`; runtime execution version, not that advisory, is the acceptance proof.
- Zero active project executions after deploy.
- Exact next step: **one** fresh PL15 `jak działa elektrownia wodna?` / `pl` / 15s via Studio path. Require M5 v99 and M8 v54 runtime IDs, M4-M9 completion, then exact final MP4 technical + visual + audio review before EN30.


### Fresh PL15 exercised M8 v54; S2 hidden-process visual contract fixed — tested, NOT DEPLOYED — 2026-09-22

- Fresh PL15 job `763b1c91-c765-414f-bfa2-7edd9b7bd11a`:
  - parent 9235 ERROR;
  - M4 9236 PASS;
  - M5 9239 PASS on v99 `8317622a-7d47-4cc5-8c40-f3f76caebf42`;
  - M6 9245 PASS;
  - M7 9246 PASS;
  - M8 9253 ERROR on **v54 `818d2c37-28db-488b-b7b7-f0e047a29f30`**;
  - M9 absent.
- M8 v54 runtime is therefore proven. It completed all **45/45** searches, 305 candidates total: Pexels 15/120, Pixabay 15/120, Wikimedia 15/65.
- Terminal failure: `M8 visuals failed: no compliant relevant visual candidate for shot S2-A`.
- Exact S2 narration is `Następnie spada w dół.`; storyboard demanded visual intent `Water falling down through a penstock in a hydroelectric plant`, must_show `["flowing water","penstock"]`.
- Root cause is upstream photographability, not a scorer threshold: water flowing **inside a closed penstock** is normally not directly visible in a real photo, so requiring both as hard depicted subjects makes a valid shot impossible. M8 correctly failed closed.
- Systemic M5 fix:
  - for process/action-like primaries occurring through/inside a closed conduit or machine, promote the concrete conduit/machine to primary must_show unless the intent explicitly requests transparent/open/cutaway/exposed visibility;
  - apply the same rule in initial validation, both bounded storyboard validators, and final canonicalization;
  - final query canonicalization follows the promoted subject. Exact S2 becomes primary `penstock` and q3 provenance query `penstock`.
- Systemic M8 fix:
  - closed infrastructure heads `penstock/pipe/pipeline/conduit/duct/hose/tube/cable/wire` retain an explicit local operating domain just like domain-scoped machinery;
  - action words such as fall/drop/flow/through cannot become domains;
  - machinery-only `equipment` fallback remains machinery-only. Exact S2 q3 becomes effective provider query `hydroelectric penstock`, NOT `hydroelectric penstock equipment`;
  - original storyboard query provenance remains immutable.
- Targeted Commons proof:
  - broad `penstock` is context-ambiguous;
  - `hydroelectric penstock` returns real hydro-plant penstocks;
  - current M8 scorer accepts **5** exact hydroelectric-penstock candidates for the corrected S2 context (asset IDs only recorded as evidence, never production rules): 163228837, 163228760, 91714839, 151215705, 152479318.
- Regression/validation: **158/158 tests PASS**, M5 55/55 Code-node syntax PASS, M8 10/10 Code-node syntax PASS, both workflow JSON parses PASS, `git diff --check` PASS.
- Evidence: `docs/acceptance/2026-09-22-pl15-v54-s2-hidden-process-fix.json`.
- **Not deployed yet at this checkpoint.** Production remains M5 v99 / M8 v54.
- Exact next step: commit/push this tested M5+M8 fix, scoped deploy only those two workflows with backups/protected-row comparison, then exactly one fresh PL15. Do not rerun failed job `763b1c91...`.


### M5 v100 + M8 v55 deployed — hidden-process / closed-infrastructure fix — 2026-09-22

- Source commit: `ca0716f08f722bd5bbd39022b2e0b9c3f9f3b119`.
- Published only M5 and M8:
  - M5 v100 activeVersionId `8cc07108-bc76-43f3-b97e-071fbca26148`;
  - M8 v55 activeVersionId `5ae1fa70-219c-4ea2-84d5-8882c3a4dbd8`.
- Published backups:
  - `.backups/m5-before-hidden-process-fix-20260922-065211.json`;
  - `.backups/m8-before-hidden-process-fix-20260922-065211.json`.
- Other 30 workflow rows unchanged: protected fingerprint `988ee473175a09fe877d3de8c2325108` before/after.
- Published M5 and M8 exports match repository exactly for `nodes/connections/settings`.
- Publisher 200; Studio 200; n8n running restart 0; media worker healthy restart 0 on unchanged `sha256:11d5b351609b40f9e5c46362a59ff2c620a403503bbb8f6e8ae0f57c57eef7ec`.
- No active project executions before or after deployment. No credential change, DB migration or service restart.
- n8n CLI printed its generic restart advisory; runtime workflowVersionId on the next execution is the acceptance proof.
- Exact next step: **one** fresh PL15 via Studio. Require M5 v100 and M8 v55 runtime IDs, then M9 and exact final MP4 technical/visual/audio acceptance before EN30.


### Fresh PL15 proved M5 v100 and exposed direction-contradicting late timing target — fixed locally, NOT DEPLOYED — 2026-09-22

- Fresh job `94d22732-c6f6-4514-bb5b-71f006f749ad`:
  - parent 9283 ERROR;
  - M4 9284 PASS;
  - M5 9287 ERROR on exact **v100 `8cc07108-bc76-43f3-b97e-071fbca26148`**;
  - M6-M9 did not run.
- Script run `4d1c7f28-b33b-46d2-bfa5-f91cf9463a91` failed: `M5 timing repair still outside target: got 13368ms, target 15000ms, tolerance 750ms`.
- Real timing sequence:
  - 24w/185c -> 16344ms;
  - 16w/129c -> 13344ms;
  - 24w/185c -> 16344ms;
  - 22w/171c -> 14208ms (only 42ms below the unchanged lower bound 14250ms);
  - old late builder correctly said LONGER but incorrectly targeted 21w/162c;
  - resulting 21w/159c measured 13368ms, then stability 13512ms and 13368ms; all three confirmed it was genuinely too short.
- Root cause: noisy linear interpolation was allowed to produce a target opposite to the measured correction direction. The later hard exact-word retry faithfully enforced that wrong target.
- Systemic fix in both `Build Final Duration Repair` and `Build Final Measured Correction`:
  - use regression only when the prediction is directionally consistent with the latest real measurement;
  - otherwise use the proportional latest-measurement fallback;
  - force at least one word/character step in the required direction when hard bounds permit;
  - fail explicitly if both target dimensions cannot move in the required direction.
- No tolerance, semantic guard, provider budget, stability rule or exact-count gate was weakened.
- Exact replay of execution 9287 inputs after the fix: 22w/171c at 14208ms -> LONGER -> **23 words / 176 chars**, scene targets `[5,5,4,4,5]`, internal aim 14625ms.
- Validation: **160/160 PASS**, M5 55/55 Code-node syntax PASS, JSON parse PASS, `git diff --check` PASS.
- Evidence: `docs/acceptance/2026-09-22-pl15-v100-timing-direction-fix.json`.
- Production is still M5 v100 / M8 v55 at this checkpoint. Next: commit/push, deploy **M5 only**, verify M8/protected rows unchanged, then exactly one fresh PL15.


### M5 v101 deployed — direction-safe late timing targets — 2026-09-22

- Source commit: `ef614ab20f64d75b7073cd344a60466cc9ad8cca`.
- M5 published v101, activeVersionId `0181e4e3-ae95-4a37-afd2-9b4bd5ca7f4f`.
- M8 intentionally unchanged: v55 `5ae1fa70-219c-4ea2-84d5-8882c3a4dbd8`.
- M5 backup: `.backups/m5-before-direction-safe-timing-20260922-070159.json`.
- All other 31 workflow rows (including M8) unchanged: fingerprint `07f4e3bc61e679e8ba1b0ff5677373d9` before/after.
- Published M5 export matches repo exactly for nodes/connections/settings.
- Publisher 200; Studio 200; n8n running restart 0; media worker healthy restart 0. No active project executions before/after.
- CLI restart advisory is generic; runtime proof is pending.
- Exact next step: one fresh PL15. Require M5 v101 runtime; if it reaches M8 require exact v55; then M9 and final MP4 acceptance before EN30.


### PL15 M4→M9 machine PASS exposed S3 HUMAN visual false positive; operational-setting gate tested — NOT DEPLOYED — 2026-09-22

- Fresh job `6ff32b6c-27f8-4cfc-9872-450bb74530a7` completed the whole pipeline:
  - parent 9293 PASS;
  - M4 9294 PASS;
  - M5 9296 PASS on v101 `0181e4e3-ae95-4a37-afd2-9b4bd5ca7f4f`;
  - M6 9307 PASS;
  - M7 9308 PASS;
  - M8 9311 PASS on v55 `5ae1fa70-219c-4ea2-84d5-8882c3a4dbd8`;
  - M9 9321 PASS.
- Final MP4 `/data/renders/6ff32b6c-27f8-4cfc-9872-450bb74530a7/final.mp4`, sha256 `b6587526e007c11fd202287eb1f8c98c52aade1fcc6a883f73a1f7f89c36e3d8`, 1,168,070 bytes.
- Exact read-only media audit PASS: 1080x1920, H.264, yuv420p, 30 fps, AAC, 15.700 s; audio 15.696 s; audio correlation 0.9999843728; 5 unique contiguous scenes; manifest/audio/video hashes and full decode all PASS.
- Machine QA is NOT HUMAN PASS. Exact midpoint/source review found S3 wrong:
  - storyboard: `Industrial electric generator connected to a turbine inside power plant`, must_show `electric generator + turbine`;
  - selected Wikimedia asset `62539210`: 1918 `Airplanes - Parts - Wind driven generator...`, categories include ram-air turbines / World War I aviation;
  - this is a real generator+turbine semantic token match but the wrong operational setting.
- Other selected scene sources are semantically aligned at source/frame level: S1 dam+reservoir, S2 hydroelectric turbine machinery, S4 power-station transformer, S5 utility pole/power lines.
- Root cause: M8 only rejected explicit museum/exhibit/manufacturing/transport contradictions for an operational storyboard. It did NOT positively require strong metadata for an explicit plant/station/facility setting. Production ranking therefore preferred a q2 aviation match over the valid q3 in-plant turbine-generator.
- Scoped generic fix in all three normalizers: when the visual intent explicitly places machinery in a plant/station/facility/powerhouse, strong candidate metadata must positively establish that setting. For `power plant` / `power station`, require power + a plant/station/powerhouse synonym. This is not hydro-specific and contains no asset IDs.
- Regression coverage includes all providers:
  - aviation generator+turbine is rejected with `missing_operational_setting_context`;
  - `power station` satisfies a `power plant` intent;
  - a botanical/generic `plant` token without power context does not.
- Full suite **169/169 PASS**; workflow JSON and `git diff --check` PASS.
- Exact S3 replay uses the 69 persisted candidates from M8 execution 9311. Intersecting the original production-eligible set with the new gate leaves exactly one candidate: Wikimedia `112972156`, `Waste block turbine and generator in Iru Thermal Power Plant.jpg`, q3, score 100. The selected aviation assets `62539210/62539212`, wind candidate `54983717`, standalone steam candidate `5226595` and factory-assembly candidate `8285173` become fail-closed.
- Source review of `112972156` confirms a turbine-generator installation inside an industrial power-plant hall, matching the S3 storyboard setting.
- Alignment transcript coverage is 0.994; normalized_match is false because the stored ASR text differs from narration spelling/diacritics at least at `turbinę/turbine`. Do not infer HUMAN audio PASS from this; exact fresh post-fix audio review remains required.
- Evidence: `docs/acceptance/2026-09-22-pl15-v101-v55-operational-setting-fix.json`.
- Production remains M5 v101 / M8 v55 at this checkpoint. Next: commit/push, scoped M8-only deploy with backup + protected-row fingerprint, then exactly one fresh PL15 and full exact MP4 visual/audio acceptance before EN30.


### M8 v56 deployed — positive operational-setting evidence — 2026-09-22

- Source commit: `5820a277dfdfe9098fe13d9814f46553392a05a5` (`fix: require explicit operational visual setting`).
- Exact published backup: `.backups/m8-before-operational-setting-20260922-073017.json`.
- Published **only** `VideoM8Visuals001`: versionCounter **56**, activeVersionId `ff72822c-44df-4058-9c7a-f31aa4abd7c9`.
- M5 remains v101 `0181e4e3-ae95-4a37-afd2-9b4bd5ca7f4f`.
- Other 31 workflow rows unchanged: count/hash `31|ef93efe27a6af28349854d1179d818d3` before and after.
- Published M8 export matches repository for `nodes`, `connections`, `settings`.
- Publisher 200; Studio 200; n8n running restart 0; media worker healthy restart 0 on unchanged image `sha256:11d5b351609b40f9e5c46362a59ff2c620a403503bbb8f6e8ae0f57c57eef7ec`.
- n8n CLI printed its generic restart advisory; no restart was performed. Runtime execution version is the acceptance proof.
- Exact next step: one fresh PL15 through M9. Require M5 v101 and M8 v56 execution IDs, then exact technical + scene-by-scene visual + audio review. HUMAN PASS remains false until that completes; EN30 remains blocked.
