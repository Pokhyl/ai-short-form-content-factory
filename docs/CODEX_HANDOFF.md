# Codex handoff — production video factory

Updated: 2026-09-20

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
- M5 versionCounter 82, versionId d47c0333-5e66-43ca-a10a-c3482a322d6c (confirmed TTS median propagation)
- M6 versionCounter 7, versionId 98e671f3-a0dc-42fa-81e9-4c9524a05e6a
- M7 versionCounter 4, versionId 91fbac4f-f40d-4d75-9111-3e4ed01bd9ff
- M8 versionCounter 42, versionId c6309bfc-4aa7-42c6-b5a9-49b187c134c1 (photographic-evidence fix)
- M9 versionCounter 1, versionId 5b6c937c-1767-4c3e-99c4-31ea38a26961
- Self-Test API versionCounter 3, versionId f3ef8cbf-1c56-4048-9fdf-feb073de96df

Current media-worker image:
sha256:5cf02e01d9cfb693d266bedc2f77b866fcee5960bb0a0654923b79be144e1874

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

1. Run a fresh sequential 4-case acceptance matrix on the currently deployed M5 v81 / M8 v41.
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
