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

Owner state:
- user-management:reset was run;
- workflows and credentials remained;
- UI requires owner setup;
- intended owner email is pokhylvitalii.it@gmail.com;
- password must be chosen by the user in the UI and must never be stored in project files.

n8n.hodor.com.pl is unrelated and must not be touched.


## Free-only provider budget infrastructure
Implemented and verified on 2026-09-19:
- db/02-provider-budget.sql;
- monthly provider free-limit configuration;
- disabled-by-default internal safety limits;
- atomic/idempotent usage reservations;
- commit/release lifecycle;
- fail-closed behavior when a budget is not explicitly enabled.

No production Google Cloud TTS call is allowed until an explicit internal safety ceiling is configured below the provider free limit.

## M1
PASS.

## M2
PARTIAL. M3 remains blocked.

Passed:
- SearXNG broad web search
- direct public source fetch
- Wikimedia Commons API
- local FFmpeg 1080x1920 H.264/AAC render
- local whisper.cpp CPU runtime and token timestamps

Historical proof:
- Google Cloud TTS worked in August with all four selected voices.

Current blockers:
- restored Google OAuth in `publisher.hodor.com.pl` requires reconnect;
- live all-four-voice Google Cloud TTS proof through `publisher.hodor.com.pl` is pending;
- exact current approved Gemini text free-tier live proof through `publisher.hodor.com.pl` is pending;
- Pixabay live API proof through the restored publisher credential is pending;
- Pexels live API proof through the restored publisher credential is pending;
- at least two independent production-ready visual sources must be live;
- Openverse is disabled while the official API returns a Cloudflare challenge from this VPS;
- four-language alignment quality must be tested against exact Google Cloud TTS output.

Do not start M3 until mandatory M2 gates in PLAN.md pass.

## Immediate next work
1. Use `publisher.hodor.com.pl` as the production n8n for all provider tests.
2. Reconnect the restored Google OAuth there and test all four locked Cloud TTS voices.
3. Validate Gemini text through `publisher.hodor.com.pl` using the approved free-tier model.
4. Validate restored Pixabay and Pexels credentials with live API calls and metadata/rate-limit capture.
5. Run four-language local alignment quality tests on the exact TTS audio.
6. Update M2 evidence.
7. Only then implement M3 intake as new video workflows in `publisher.hodor.com.pl`.


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
