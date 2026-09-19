# Current State

Updated: 2026-09-19

## Repository
Repo: Pokhyl/ai-short-form-content-factory
Branch: main
Runtime path: /opt/ai-short-form-content-factory
Architecture source: PLAN.md

Mandatory operating references:
- docs/OPERATOR_EXECUTION_RULES.md
- docs/CURRENT_STATE.md
- docs/LESSONS_LEARNED.md

## Supporting runtime
Compose project: `shorts-v2`.

Production n8n is NOT part of this supporting runtime. Production orchestration runs in `publisher.hodor.com.pl`.

Supporting services:
- `shorts-v2-postgres-1`
- `shorts-v2-media-worker-1`
- `shorts-v2-searxng-1`

Current status:
- PostgreSQL healthy;
- media-worker healthy;
- SearXNG healthy;
- compose uses only project-local `.env`;
- accidental recovery `env_file` hack removed.

Bootstrap n8n cleanup completed 2026-09-19:
- temporary M2 workflows removed from shorts-v2;
- temporary shorts-v2 credentials removed;
- `shorts-v2-n8n-1` removed;
- `shorts-v2_n8n_data` volume removed;
- unused `n8n` PostgreSQL schema removed from shorts_factory after backup;
- supporting Compose stack now contains only PostgreSQL, media-worker and SearXNG.

## Publisher and MCP protection
publisher.hodor.com.pl uses restored DB n8n-publisher-restore-pg.

Legacy video workflow cleanup completed on 2026-09-19.
Deleted:
- Test Voice - Google All Available Voices v3
- WF00 - Sheet Intake Adapter
- WF01 - Topic Intake
- WF02 - Script and Scene Plan
- WF03 - Scene Voiceover
- WF04 - Visual Asset Sourcing
- WF05 - FFmpeg Render
- WF06 - Buffer TikTok Publish

Remaining workflow count: 22.
Remaining workflows are MCP/ADMIN business workflows only. Do not delete or repurpose them.

Rollback backup before cleanup:
.backups/publisher-before-video-cleanup-20260919.dump

Recovered credential count in restored publisher DB: 9.
Current publisher credential count: 11 after adding `Gemini Text` and `Video Factory Postgres` on 2026-09-19.

Owner/auth state verified live on 2026-09-19:
- user-management:reset had previously been run;
- workflows and credentials remained;
- owner setup is complete;
- sole owner email is pokhylvitalii.it@gmail.com;
- role is global:owner and the account is enabled;
- publisher root HTML returns HTTP 200;
- a referenced n8n JavaScript asset returns HTTP 200;
- all 9 restored credentials can be decrypted/exported by the running publisher n8n with its current encryption key;
- `Gemini Text` credential ID `zsRz2tvE57EKe8zy` exists as `googlePalmApi` and passed a live Gemini text call;
- credential secret values were not printed or stored in project files.

n8n.hodor.com.pl is unrelated and must not be touched.


## Free-only provider budget infrastructure
Implemented and verified on 2026-09-19:
- db/02-provider-budget.sql;
- db/03-provider-budget-policy.sql;
- monthly provider free-limit configuration;
- atomic/idempotent usage reservations;
- commit/release lifecycle;
- fail-closed behavior when a budget is not explicitly enabled;
- production internal ceilings enabled at 90% of the documented free limits:
  - Chirp 3 HD: 900,000 characters/month vs 1,000,000 provider free limit;
  - WaveNet: 3,600,000 characters/month vs 4,000,000 provider free limit;
- 90% is a project engineering safety setting, not a Google recommendation;
- live DB smoke test accepts an in-limit reservation, rejects an over-limit reservation, and persists no test rows after rollback.

A rollback copy of the budget rows exists at .backups/provider-budget-before-enable-20260919.sql.

## M1
PASS.

## M2
PASS on 2026-09-19. M3 is unblocked.

Passed:
- SearXNG broad web search;
- direct public source fetch;
- Wikimedia Commons API;
- Pixabay image search + video search + metadata + rate-limit headers + real image download;
- Pexels photo search + video search + metadata + rate-limit headers + real image download;
- visual-source gate with three independent sources;
- local FFmpeg 1080x1920 H.264/AAC render;
- fail-closed Google Cloud TTS monthly budget guard;
- `Gemini Text` live structured-JSON call with `gemini-3.5-flash-lite`;
- existing `Google account` OAuth reconnected and verified by real Cloud TTS calls;
- all four locked TTS voices returned real MP3 audio;
- local whisper.cpp `ggml-base.bin` alignment passed on exact EN/PL/RU/UK TTS audio;
- all four transcripts matched their input text after normalization;
- lexical token timestamps stayed inside the measured MP3 duration.

M2 TTS evidence:
- EN `en-US-Chirp3-HD-Algenib`: 9,696 bytes, 2.424 s, SHA256 `121d1a7ae38c7ee5797d1c5b1f659443172d4380dccc1b1c4124ba71ff63c3cf`;
- PL `pl-PL-Chirp3-HD-Enceladus`: 13,536 bytes, 3.384 s, SHA256 `aef1cf5874e15f54d1fc20e6ee913968d53af0c443c86945e337aaa5a34a0499`;
- RU `ru-RU-Wavenet-D`: 20,352 bytes, 2.544 s, SHA256 `b226835db6798969519418c6daa80cf888199bed2903b39808c847c80c866dde`;
- UK `uk-UA-Chirp3-HD-Enceladus`: 11,712 bytes, 2.928 s, SHA256 `57a503f03b41c36ec9c8c9c589fe24104168c07002836bd1717170e4fb16b2a6`.

Cleanup/accounting:
- successful M2 TTS usage is committed in the provider ledger using exact character counts;
- the earlier failed-auth reservations remain released;
- temporary M2 workflows were removed;
- publisher workflow count returned to 22 with 6 active protected workflows;
- Openverse remains disabled but is not required for the visual-source gate.

## M3
PASS on 2026-09-19.

Verified:
- `db/04-jobs.sql` created and applied to `shorts-v2` PostgreSQL;
- `factory.jobs` exists with DB-level constraints for topic, language and duration;
- `factory.create_job(text,text,integer)` inserts one job atomically and rejects invalid input;
- production `publisher` container is connected to `shorts-v2_default`;
- real TCP connectivity from publisher to PostgreSQL 5432, media-worker 3001 and SearXNG 8080 is verified;
- legacy `Postgres - TikTok Pipeline v2` was not reused because it points to the old `tiktok_pipeline_v2` database;
- dedicated `Video Factory Postgres` credential ID `gQ3TDSsTe7Tn2X8B` exists and its connection test succeeds;
- `VIDEO — M3 Intake` ID `VideoM3Intake001` is published and active;
- production endpoint is `POST /webhook/jobs`;
- validation suite: 10/10 local cases PASS;
- live valid request returned HTTP 201 and job ID `685031de-e7c8-48c1-a456-62b4ad66ae7e`;
- that valid request created exactly one durable `factory.jobs` row with topic `Why is the sky blue?`, language `en`, duration 15 and status `created`;
- four live invalid requests returned HTTP 400 for invalid language, invalid duration, string duration and unexpected field;
- invalid requests created zero additional job rows;
- provider usage ledger remained unchanged during intake testing;
- workflow node set contains only webhook, validation, routing, PostgreSQL and response nodes; no Gemini or TTS nodes are present;
- after deployment publisher contains 23 workflows / 7 active: the original 22 protected MCP/ADMIN workflows plus the new M3 video workflow.

Test note:
- direct VPS-to-public-domain self-call is blocked by Cloudflare with HTTP 403 / error code 1010;
- live webhook tests therefore used local Caddy with `publisher.hodor.com.pl` Host/SNI via 127.0.0.1, without changing production routing.

## M4
PASS on 2026-09-19.

Verified live:
- production workflow `VIDEO — M4 Research` ID `VideoM4Research001` is published and active;
- M4 is an internal sub-workflow with input `job_id`; no permanent public research webhook exists;
- SearXNG returned broad results from multiple engines;
- M4 selected up to 10 fetch candidates while maximizing independent domains and rejecting social/binary/private-address candidates;
- page fetch uses direct HTTP with bounded timeout and a project User-Agent;
- HTML extraction uses n8n's built-in HTML/Cheerio node, not regex page scraping;
- evidence is capped to 12,000 characters per source;
- `factory.research_runs`, `factory.evidence`, `begin_research()`, `store_evidence()`, `finalize_research()`, and `fail_research()` are deployed;
- `pgcrypto` is enabled for SHA-256 content hashes;
- URL and content-hash deduplication are enforced per job;
- PASS gate requires at least 3 evidence rows from 3 independent domains;
- live fresh-job test `198bb721-6c33-4b00-9268-930f5c34afcf` returned `passed` with 7 evidence rows / 7 domains;
- all 7 stored canonical URLs and all 7 content hashes are distinct;
- stored source text lengths ranged from 3,142 to 12,000 characters;
- successful sources included NOAA/NESDIS, SUNY ESF, Woodland Trust, Pacific Science Center, UNC, Wikipedia and Almanac;
- job state became `evidence_ready`;
- M4 execution `7750` succeeded;
- provider usage ledger remained unchanged; M4 did not invoke Gemini or TTS;
- temporary public test caller was backed up, deleted, and its random webhook now returns 404;
- publisher post-state is 24 workflows / 8 active: 22 protected MCP/ADMIN + M3 + M4.

Failed test jobs are preserved terminal and were not reused:
- `c189c00b-f055-44c5-b564-cc29e690afbf` → `research_failed`;
- `dd0946fb-046c-4480-9368-ca1fd94c17c6` → `research_failed`.

## M5
PASS on 2026-09-19.

Verified live:
- production workflow `VIDEO — M5 Script + Storyboard` ID `VideoM5Storyboard001` is published and active;
- M5 is an internal sub-workflow with input `job_id`;
- only `evidence_ready` jobs can start M5;
- `factory.script_runs`, `factory.script_versions`, `factory.scenes`, `factory.scene_evidence`, and `factory.shots` are deployed;
- `begin_script()`, `commit_storyboard()`, and `fail_script()` are deployed;
- each job gets only one immutable M5 attempt;
- Gemini model is `gemini-3.5-flash-lite` through credential `Gemini Text`;
- the request body contains no tools, Google Search, URL Context, code execution or TTS;
- Gemini receives only persisted M4 evidence, capped to 6,000 characters per evidence row for prompt construction;
- structured JSON is validated before DB commit;
- every scene requires 1–4 valid evidence IDs and those IDs are mapped to same-job evidence UUIDs before persistence;
- narration must equal scene narrations joined in order;
- narration word range is derived from target duration;
- deterministic visual density is 4/7/10/13 scenes and shots for 15/30/45/60 seconds respectively;
- every scene contains exactly one shot;
- every shot requires concrete visual intent, at least one must-show concept, 2–4 distinct English factual queries and an allowed media type;
- provider names, URLs and manual asset preselection are rejected;
- first live M5 test on job `198bb721-6c33-4b00-9268-930f5c34afcf` failed closed because Gemini produced only 5 shots against the required 7–10; the job is preserved terminal as `script_failed`;
- the contract was strengthened rather than weakening the gate: 30-second output now requires exactly 7 scenes / 7 shots;
- fresh end-to-end M3→M4→M5 test job `e4bc4b8b-dcf5-4c81-9193-5db297c528d7` passed;
- successful M5 output: 64 narration words, 7 scenes, 7 shots, 7 scenes with evidence links, 0 invalid cross-job evidence links, 0 provider/URL preselection findings;
- Gemini usage stored for the successful run: 10,390 prompt tokens, 1,374 output tokens, 11,764 total tokens;
- M4 execution `7757` and M5 execution `7758` succeeded for the fresh job;
- successful job state is `storyboard_ready`;
- provider TTS ledger remained unchanged; M5 made no TTS call;
- temporary M5 public test caller was backed up, deleted, and its random endpoint now returns 404;
- publisher post-state is 25 workflows / 9 active: 22 protected MCP/ADMIN + M3 + M4 + M5.

## Immediate next work
1. Implement M6 one-final-voiceover persistence and production workflow.
2. Load only `storyboard_ready` jobs.
3. Reserve the correct free-only Google Cloud TTS character budget before synthesis.
4. Perform exactly one final Google Cloud TTS synthesis using the locked language voice.
5. Store the exact MP3 durably, persist its SHA-256 and measured duration, then prohibit all later re-TTS.


## Production orchestration lock — 2026-09-19
- Production video workflows run in `publisher.hodor.com.pl`.
- `publisher.hodor.com.pl` is the single production n8n for both MCP/ADMIN and the video project.
- 22 existing MCP/ADMIN workflows are protected.
- the original 9 restored credentials remain in `publisher.hodor.com.pl`; video-specific credentials added afterward are `Gemini Text` and `Video Factory Postgres`.
- No new public n8n domain.
- No second production n8n.
- `tiktok-n8n.hodor.com.pl` is not part of this project.
- `n8n.hodor.com.pl` is unrelated and must not be touched.
- Supporting PostgreSQL/media-worker/SearXNG remain separate.
- The bootstrap `shorts-v2` n8n container has been removed; no second n8n remains in the supporting stack.
