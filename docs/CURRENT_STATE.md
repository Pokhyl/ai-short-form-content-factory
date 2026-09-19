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
Current publisher credential count: 10 after the user added `Gemini Text` on 2026-09-19.

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
PARTIAL on 2026-09-19.

Completed:
- `db/04-jobs.sql` created and applied to `shorts-v2` PostgreSQL;
- `factory.jobs` exists with DB-level constraints for topic, language and duration;
- `factory.create_job(text,text,integer)` inserts one job atomically and rejects invalid input;
- transactional DB smoke test: valid request creates exactly one row, rollback leaves zero rows;
- invalid DB input fails and leaves zero rows;
- production `publisher` container is connected to `shorts-v2_default`;
- real TCP connectivity from publisher to PostgreSQL 5432, media-worker 3001 and SearXNG 8080 is verified;
- existing legacy credential `Postgres - TikTok Pipeline v2` was inspected and deliberately not reused because it points to the old `tiktok_pipeline_v2` database;
- import-ready workflow file `workflows/VIDEO-M3-Intake.json` created for `POST /webhook/jobs`;
- intake validation test suite: 10/10 cases PASS;
- workflow contains no Gemini or TTS nodes.

Current blocker:
- production n8n still needs a dedicated `Video Factory Postgres` credential for `shorts-v2-postgres-1 / shorts_factory / shorts`;
- automated secret transfer into n8n credential storage is blocked by the execution safety layer, so the DB password must be entered manually in n8n;
- the workflow is intentionally not imported/activated with a missing credential.

## Immediate next work
1. Create `Video Factory Postgres` in `publisher.hodor.com.pl` using the existing `POSTGRES_PASSWORD` from the project-local `.env`.
2. Replace the workflow credential placeholder with the created credential ID.
3. Import/publish/activate `VIDEO — M3 Intake`.
4. Run live valid and invalid `POST /webhook/jobs` tests.
5. Verify valid request adds exactly one durable row, invalid requests add zero rows, and no Gemini/TTS executions occur.


## Production orchestration lock — 2026-09-19
- Production video workflows run in `publisher.hodor.com.pl`.
- `publisher.hodor.com.pl` is the single production n8n for both MCP/ADMIN and the video project.
- 22 existing MCP/ADMIN workflows are protected.
- 9 restored credentials stay in `publisher.hodor.com.pl` and are used by the video project there.
- No new public n8n domain.
- No second production n8n.
- `tiktok-n8n.hodor.com.pl` is not part of this project.
- `n8n.hodor.com.pl` is unrelated and must not be touched.
- Supporting PostgreSQL/media-worker/SearXNG remain separate.
- The bootstrap `shorts-v2` n8n container has been removed; no second n8n remains in the supporting stack.
