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
- M5 versionCounter 81, versionId b548aee4-660f-4997-a17c-1d8fa24c38b3
- M6 versionCounter 7, versionId 98e671f3-a0dc-42fa-81e9-4c9524a05e6a
- M7 versionCounter 4, versionId 91fbac4f-f40d-4d75-9111-3e4ed01bd9ff
- M8 versionCounter 41, versionId d889cb1d-c808-4e19-889e-35b06648da19
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
