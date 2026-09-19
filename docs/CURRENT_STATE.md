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

Owner/auth state verified live on 2026-09-19:
- user-management:reset had previously been run;
- workflows and credentials remained;
- owner setup is complete;
- sole owner email is pokhylvitalii.it@gmail.com;
- role is global:owner and the account is enabled;
- publisher root HTML returns HTTP 200;
- a referenced n8n JavaScript asset returns HTTP 200;
- all 9 restored credentials can be decrypted/exported by the running publisher n8n with its current encryption key;
- credential secret values were not printed or stored in project files.

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
- Pixabay image search + video search + metadata + rate-limit headers + real image download
- Pexels photo search + video search + metadata + rate-limit headers + real image download
- visual-source gate: PASS with three independent sources
- local FFmpeg 1080x1920 H.264/AAC render
- local whisper.cpp CPU runtime and token timestamps
- fail-closed Google Cloud TTS monthly budget guard

Historical proof:
- Google Cloud TTS worked in August with all four selected voices.

Current blockers:
- restored `Google account` OAuth in `publisher.hodor.com.pl` returns 401 and needs reconnect;
- all-four-voice Google Cloud TTS live proof is pending immediately after reconnect;
- no Gemini credential currently exists in `publisher.hodor.com.pl`;
- Gemini free-tier structured-output live proof is pending after that credential is added;
- four-language alignment quality must be tested against exact Google Cloud TTS output after TTS passes;
- Openverse remains disabled but is not required for the visual-source gate.

Do not start M3 until mandatory M2 gates in PLAN.md pass.

## Immediate next work
1. Reconnect the restored `Google account` credential in `publisher.hodor.com.pl`.
2. Add a Gemini API credential to `publisher.hodor.com.pl` for the approved free-tier text model.
3. Immediately run all four locked Cloud TTS voices.
4. Run Gemini structured-output live proof.
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
