# Current State

Updated: 2026-09-21

## Current authoritative status

Production M5 v98 / M8 v53. Last PL15 `12f1ac4f-b8dc-4f17-a191-06888fb7e8a4` failed in M5 9221 before final TTS because the strict 21-word target could not be formed from the last drafts. Tested fix reuses earlier measured, semantically validated scenes within the existing bounded selection; exact target remains strict. 110 tests PASS, not deployed. Next: M5-only deployment and fresh PL15, then M8 v53 runtime proof and final visual/audio QA. No EN30/HUMAN PASS. Latest details below; earlier sections historical.

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
- local whisper.cpp `ggml-small.bin` alignment passed on exact EN/PL/RU/UK TTS audio;
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
- historical snapshot after that milestone: publisher contained 23 workflows / 7 active: the original 22 protected MCP/ADMIN workflows plus the new M3 video workflow.

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
- historical snapshot after that milestone: publisher post-state was 24 workflows / 8 active: 22 protected MCP/ADMIN + M3 + M4.

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
- scene narrations are authoritative; the persisted continuous narration is canonicalized as those scene narrations joined in order;
- narration word range is validated against that canonical narration;
- current deterministic visual density is 5/9/13/17 scenes and shots for 15/30/45/60 seconds respectively;
- if the first Gemini JSON is structurally valid but fails deterministic storyboard validation, M5 allows exactly one repair-call inside the same immutable script run; the repair receives the same evidence plus the failed output and must return a complete replacement JSON object;
- every scene contains exactly one shot;
- every shot requires concrete visual intent, at least one must-show concept, 2–4 distinct English factual queries and an allowed media type;
- provider names, URLs and manual asset preselection are rejected;
- first live M5 test on job `198bb721-6c33-4b00-9268-930f5c34afcf` failed closed because Gemini produced only 5 shots against the required 7–10; the job is preserved terminal as `script_failed`;
- historical note: this earlier test required 7 scenes / 7 shots; the current production contract was later increased to 9 scenes / 9 shots for 30 seconds;
- fresh end-to-end M3→M4→M5 test job `e4bc4b8b-dcf5-4c81-9193-5db297c528d7` passed;
- successful M5 output: 64 narration words, 7 scenes, 7 shots, 7 scenes with evidence links, 0 invalid cross-job evidence links, 0 provider/URL preselection findings;
- Gemini usage stored for the successful run: 10,390 prompt tokens, 1,374 output tokens, 11,764 total tokens;
- M4 execution `7757` and M5 execution `7758` succeeded for the fresh job;
- successful job state is `storyboard_ready`;
- provider TTS ledger remained unchanged; M5 made no TTS call;
- later production hardening proved two recurring model-format failures without weakening the gate: one output returned 5 scenes instead of 7, and a repaired output returned a redundant root narration that differed from the scene narration join;
- M5 now repairs the first deterministic validation failure once, then canonicalizes the persisted narration from validated scene narrations rather than trusting the redundant root narration field;
- final successful M5 on job `6974c0e6-9261-495d-b885-0db5a2ae4cd6` produced 70 words / 7 scenes / 7 shots and execution `7820` succeeded;
- temporary M5 public test caller was backed up, deleted, and its random endpoint now returns 404;
- publisher M5 remains the same production workflow ID; no duplicate M5 workflow was created.

## M6
PASS on 2026-09-19.

Verified live:
- production workflow `VIDEO — M6 One Final Voiceover` ID `VideoM6Voiceover001` is published and active;
- M6 is an internal sub-workflow with input `job_id`;
- `factory.voiceover_runs` and `factory.voiceovers` are deployed;
- `begin_voiceover()`, `mark_tts_consumed()`, `complete_voiceover()`, and `fail_voiceover()` are deployed;
- only `storyboard_ready` jobs can start M6;
- each job and script version can have only one immutable voiceover run;
- locked voices are enforced by language in PostgreSQL:
  - EN `en-US-Chirp3-HD-Algenib`;
  - PL `pl-PL-Chirp3-HD-Enceladus`;
  - RU `ru-RU-Wavenet-D`;
  - UK `uk-UA-Chirp3-HD-Enceladus`;
- free-only provider usage is reserved before TTS using idempotency key `m6-tts:<job_id>`;
- a successful provider response commits the usage ledger before storage;
- pre-provider failures release the reservation; post-provider failures keep usage committed;
- media-worker atomically stores exactly one `final.mp3` and rejects a second create;
- current M6 may synthesize up to four independent TTS candidates inside the one immutable voiceover run; only a candidate that passes the measured-duration gate is persisted;
- successful M6 test used job `e4bc4b8b-dcf5-4c81-9193-5db297c528d7`;
- exact TTS input was the 418-character final M5 narration;
- one Google Cloud TTS request used `en-US-Chirp3-HD-Algenib`;
- M6 execution `7760` succeeded;
- output voiceover ID is `b0390ff7-2ec8-498f-8910-37fcdcf4c689`;
- exact stored file is `/data/voiceovers/e4bc4b8b-dcf5-4c81-9193-5db297c528d7/final.mp3`;
- stored file is 106,272 bytes, mono 24 kHz MP3;
- measured duration is 26,568 ms;
- exact SHA-256 is `5b9d89a80c1765a3bebd8b192fac267156a703ab298d40df4bfa549d4521e180`;
- independent container-side SHA-256 and ffprobe output match the persisted DB values;
- M6 usage ledger row is committed for exactly 418 Chirp3 HD characters;
- Chirp3 HD monthly internal allocation after M6 is 526 characters with 899,474 remaining under the 900,000 internal ceiling;
- job state is `voiceover_ready`;
- temporary M6 public test caller was backed up, deleted, and its random endpoint returns 404;
- historical snapshot after that milestone: publisher post-state was 26 workflows / 10 active: 22 protected MCP/ADMIN + M3 + M4 + M5 + M6.

## M7
PASS on 2026-09-19.

Verified live:
- production workflow `VIDEO — M7 Local Alignment` ID `VideoM7Alignment001` is published and active;
- M7 is an internal sub-workflow with input `job_id`;
- `factory.alignment_runs`, `factory.alignments`, and `factory.scene_timings` are deployed;
- `begin_alignment()`, `complete_alignment()`, and `fail_alignment()` are deployed;
- only `voiceover_ready` jobs can start alignment;
- the media-worker contains the pinned `whisper.cpp` binary copied from image digest `sha256:9cfbaf11ef5bec57ec9cade6af7ed991ab5e32b01a6e40db3380a12363336e11`;
- the exact multilingual model is mounted read-only and verified at startup with SHA-256 `1be3a9b2063867b937e64e2ec7483364a79917e157fa98c5d94b5c1fffea987b`;
- alignment input is only the immutable M6 file `/data/voiceovers/<job_id>/final.mp3`;
- media-worker verifies the exact audio SHA-256 and duration before alignment;
- MP3 is decoded only to temporary 16 kHz mono PCM for local Whisper analysis; the original MP3 is never modified;
- lexical Whisper tokens must reconstruct the Whisper transcript exactly;
- scene narrations must reconstruct the final M5 narration exactly;
- alignment uses `whisper_token_sequence_match`: global normalized character coverage must be at least 0.95 and every scene coverage at least 0.85;
- per-scene boundaries are derived only from real matching Whisper lexical token timestamps; no proportional timing fallback exists;
- successful product test used job `e4bc4b8b-dcf5-4c81-9193-5db297c528d7`;
- M7 execution `7762` succeeded;
- alignment ID is `6f34156f-216d-4abb-8937-9355745cd186`;
- global coverage is 1.000 and all 7 scene coverage values are 1.000;
- 72 lexical tokens were retained;
- lexical speech span is 40–26,260 ms within the immutable 26,568 ms audio;
- scene timings are:
  - S1 40–4,850 ms;
  - S2 5,000–8,480 ms;
  - S3 8,840–10,270 ms;
  - S4 10,500–13,330 ms;
  - S5 14,100–18,680 ms;
  - S6 19,230–22,220 ms;
  - S7 22,350–26,260 ms;
- immutable alignment artifacts exist at `/data/alignments/<job_id>/final.json` and `whisper.json`;
- stored audio/model/image hashes match the expected pinned values;
- TTS ledger remained unchanged and no new M6/TTS execution occurred;
- a later real TTS sample exposed a normal Whisper ASR substitution (`abscission` → `obsidian`): global coverage was 0.981675 and the lowest scene coverage was 0.883721;
- the original exact-string gate was therefore replaced by bounded lexical coverage without introducing proportional timing; the same failed terminal job was not reused;
- final successful product job `6974c0e6-9261-495d-b885-0db5a2ae4cd6` passed M7 with normalized_match=true, global coverage 1.000, 7/7 scene timings and execution `7822` success;
- job state is `alignment_ready` before M8;
- temporary M7 public test caller was backed up, deleted, and its random endpoint returns 404;
- publisher M7 remains the same production workflow ID; no duplicate M7 workflow was created.

## M8
PASS on 2026-09-19.

Verified live:
- production workflow `VIDEO — M8 Multi-Source Visuals` ID `VideoM8Visuals001` is published and active;
- M8 is an internal sub-workflow with input `job_id`;
- `factory.visual_runs`, `factory.visual_searches`, `factory.visual_candidates`, `factory.visual_selections`, `factory.visual_assets`, and the visual query cache are deployed;
- only `alignment_ready` jobs can start M8;
- every storyboard search query is executed against all three enabled providers: Pixabay, Pexels and Wikimedia Commons;
- candidates are normalized with provider/source/license metadata before deterministic ranking;
- Pixabay and Pexels license names are enforced exactly; Wikimedia accepts only the configured CC0 / CC BY / CC BY-SA / public-domain families;
- `must_not_show`, media-type compatibility, minimum relevance and per-run provider-asset reuse are fail-closed gates;
- Wikimedia Commons rate limiting was reproduced as HTTP 429 with `Retry-After` values around 23–27 seconds after ten requests;
- current M8 paces Wikimedia requests at 8 seconds per item and retries affected items through explicit 60-second wait nodes; successful runs may still complete from remaining providers when Wikimedia degrades;
- Wikimedia photos from Commons use the official `thumb.wikimedia.org` host while videos commonly use `upload.wikimedia.org`; media-worker allowlists both exact official hosts and still rejects arbitrary hosts;
- selected assets are downloaded atomically into `/data/visuals/<job_id>/<shot_id>/selected.<ext>` and persisted with SHA-256, bytes, dimensions, codec and video duration where applicable;
- successful product test job is `6974c0e6-9261-495d-b885-0db5a2ae4cd6`;
- M8 execution `7823` succeeded and the job state is `visuals_ready`;
- this 30-second storyboard contained 7 shots with 3 queries each, therefore expected provider-search coverage was 63 searches total;
- verified coverage was 21/21 Pixabay, 21/21 Pexels and 21/21 Wikimedia;
- provider result totals were 168 Pixabay, 168 Pexels and 71 Wikimedia candidate rows before normalization/ranking filters;
- exactly 7 selections were persisted and all 7 provider+asset identities were unique;
- exactly 7 local assets were persisted and all 7 SHA-256 hashes were distinct;
- total persisted visual bytes were 65,286,389;
- the selected set contained 3 videos and 4 photos from Pixabay/Pexels; no duplicate file hash was accepted;
- all persisted candidates passed the configured license policy;
- media-worker file-side SHA-256 and ffprobe checks independently confirmed all 7 files;
- failed product jobs from earlier M8/M7/M5 diagnostics remain terminal and were not reused;
- temporary M8 caller was backed up, deleted, and its random endpoint returns 404;
- historical snapshot after that milestone: publisher post-state was 28 workflows / 12 active: 22 protected MCP/ADMIN + M3 + M4 + M5 + M6 + M7 + M8.

## M9 render + machine QA — PASS

Verified live:
- production workflow `VIDEO — M9 Render + Machine QA` ID `VideoM9RenderQa001` is published and active;
- `factory.render_runs`, `factory.renders`, `factory.render_segments` and `factory.machine_qa` are deployed;
- only `visuals_ready` jobs can begin M9;
- render inputs are the exact immutable M6 voiceover, M7 scene timings and M8 selected local assets;
- render segments are contiguous from 0 ms through the immutable voiceover duration;
- source-video audio is always excluded; the only final audio stream is the M6 narration;
- photos and non-9:16 media preserve the full foreground and use a blurred fill background rather than a hard crop;
- machine QA requires exactly one H.264 video stream and one AAC audio stream, 1080×1920, yuv420p, 30 fps, <=100 ms duration delta, complete scene coverage and exact asset SHA-256 provenance;
- dedicated M9 integration fixture passed with 7/7 render segments and all machine gates true;
- normal product job `6974c0e6-9261-495d-b885-0db5a2ae4cd6` reached `machine_qa_passed`;
- product M9 execution `7837` succeeded;
- exact product render path is `/data/renders/6974c0e6-9261-495d-b885-0db5a2ae4cd6/final.mp4`;
- exact product render SHA-256 is `262941d27a00ac4fe5e8a754d3a459c29e3b75298928fc76322b149bd9e9b178`;
- exact product render size is 10,347,458 bytes;
- ffprobe independently confirms 1080×1920 H.264/yuv420p video at 30 fps plus AAC audio;
- rendered duration is 30.533333 s against immutable voiceover 30.528 s, delta 5 ms;
- exactly 7 render segments and one passed machine-QA row are persisted;
- temporary M9 caller was backed up, deleted, and its random endpoint returns 404;
- historical snapshot after that milestone: publisher post-state was 29 workflows / 13 active: 22 protected MCP/ADMIN + M3 + M4 + M5 + M6 + M7 + M8 + M9;
- `ai-short-form-n8n` restart-manager corruption was recovered by recreating only the stateless n8n container from the same image/env/networks; publisher DB, workflows and credentials remained intact; final restart count is 0.

## M10 delivery — HISTORICAL SINGLE-PRODUCT REVIEW

The earlier single-product review artifact is preserved as historical verification, not as the current acceptance target:
- external review bytes: 10,347,458;
- external review SHA-256: `262941d27a00ac4fe5e8a754d3a459c29e3b75298928fc76322b149bd9e9b178`;
- external ffprobe confirmed 1080×1920 H.264/yuv420p at 30 fps plus AAC audio, duration 30.533333 s;
- workflow `M10 TMP — Exact MP4 Review` ID `M10TempReview001` still exists in production.

Current acceptance is defined by the 2026-09-20 production update and docs/CODEX_HANDOFF.md: fresh sequential 4-case regression on M5 v81 / M8 v41, followed by inspection of the exact four resulting MP4s.

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


## Production update — 2026-09-20

The production implementation advanced substantially beyond the older M10 section above.

Current deployed core:
- M3 VideoM3Intake001: versionCounter 2;
- M4 VideoM4Research001: versionCounter 5;
- M5 VideoM5Storyboard001: versionCounter 81, versionId b548aee4-660f-4997-a17c-1d8fa24c38b3;
- M6 VideoM6Voiceover001: versionCounter 7;
- M7 VideoM7Alignment001: versionCounter 4;
- M8 VideoM8Visuals001: versionCounter 41, versionId d889cb1d-c808-4e19-889e-35b06648da19;
- M9 VideoM9RenderQa001: versionCounter 1;
- Self-Test VideoSelfTestApi001: versionCounter 3;
- media-worker image sha256:5cf02e01d9cfb693d266bedc2f77b866fcee5960bb0a0654923b79be144e1874;
- publisher and Studio HTTP 200 at the last production check;
- media-worker healthy with restart count 0.
- Current M5 density is 5/9/13/17 scenes+shots for 15/30/45/60 seconds.
- Current M6 may synthesize up to four candidates but persists exactly one final MP3.

On M5 v81 / M8 v40, the sequential acceptance matrix produced machine-QA PASS for PL15, EN30 and RU45. UK60 passed M4-M7 and failed only M8 shot S7-A because compound primary-subject matching was too literal. That scorer defect was fixed systemically, positive/negative regression-smoked, and deployed as M8 v41.

A fresh full 4/4 sequential acceptance matrix on M5 v81 / M8 v41 is still required before declaring final acceptance.

See docs/CODEX_HANDOFF.md for exact current job IDs, constraints and remaining steps.

## Acceptance continuation — 2026-09-20

Fresh PL15 passed machine QA and exact-file visual inspection. Fresh EN30 passed technical QA but failed visual inspection: Pixabay returned a text poster as `photo` and tag-only relevance admitted a honey jar for a bee scene. No final acceptance is claimed. Investigation and exact IDs are in `CODEX_HANDOFF.md`; a fresh four-case matrix must follow the systemic fix.

## Timing continuation — 2026-09-21

M8 v42 is published (`c6309bfc-4aa7-42c6-b5a9-49b187c134c1`), with other 31 workflow rows unchanged. The fresh PL15 failed before M8 in M5 v81 because repair interpolation reused a first TTS sample after a materially different median had been confirmed. The targeted fix passes 12 regression tests; deployment and a fresh full acceptance matrix remain next. See `CODEX_HANDOFF.md` for exact IDs and measurements.

## Subject-evidence continuation — 2026-09-21

PL15 on M5 v82/M8 v42 passed exact-file review. EN30 on the same versions reached machine PASS but was rejected after frame inspection (bee fly, wasp, dew substituted for the narrated subjects). The stronger subject-grounding correction and whole-subject storyboard prompt pass 18 tests plus a replay of 236 persisted candidates. They are not yet deployed at this checkpoint; no final four-case acceptance is claimed.

### Complete Commons query coverage — tested, not yet deployed

- Confirmed live public Commons probes: `hydroelectric penstock pipe` and `penstock pipe` each return 8 candidates including penstock photographs. The original long query returned a turbine and hydraulic-compressor diagram, both correctly rejected. This confirms a retrieval gap; it does not yet prove the complete storyboard passes.
- M8 now enumerates every storyboard query for Wikimedia, retaining query index, provenance, 8-second pacing and existing retry/quality gates. `factory.begin_visuals` expected count becomes 3 × total storyboard queries. Existing immutable run counts are untouched.
- Checks: 22/22 Node tests PASS; replacement SQL compiled and function definition asserted in a rolled-back production transaction; git diff check PASS. Production remains M5 v83 / M8 v43 until the following deployment checkpoint.
- Next: back up and replace only begin_visuals(uuid), publish M8, verify protected workflow rows and deployed count contract, then create a fresh PL15.

### M5 semantic-space repair tested — NOT DEPLOYED

- Execution 9039 trace proves original narration was complete and correct. First timing repair shortened it; robust measurement triggered another repair. `Build Timing Repair 2` imposed equalized counts `[5,5,4,4,4]`; its 24-word response failed the 22-word constraint. `Build Timing Precision Retry` then returned the damaged 22-word text and passed mechanical validation. The retry lacked original narration as its meaning reference.
- Repository correction distributes the unchanged total target proportionally to original scene lengths within unchanged 2–10/14 bounds, and supplies original scene narration to both precision builders. The retry explicitly treats its previous draft as unaccepted and preserves subjects, required objects and causal direction. Exact total/per-scene checks, duration gates, attempt counts and provider budgets remain unchanged.
- Validation: 24/24 Node tests PASS, including median propagation, bounded proportional allocation and preservation of original meaning context when the failed draft lost an object. These tests prove data/prompt contracts, not semantic quality of future model output. Production remains M5 v83 / M8 v44.
- Next: scoped M5 deployment with backups/protected-row comparison; resolve render crop and provider-label ambiguity before fresh acceptance. No new job is running. Do not claim semantic acceptance until actual new narration and all final frames are reviewed.

Render fit correction tested locally/in the existing worker via an isolated function, not deployed: preserve full source geometry with aspect-fit and black padding. Three real FFmpeg edge-landmark regressions pass. See CODEX_HANDOFF.md for active vs pending versions and latest rejected output.

Latest acceptance failed in M5: job `ccc91e49-8e19-404d-bf05-3ec4cab5d469`, execution 9047, 14,064 ms vs 15,000 ± 750 ms. v84 prompts did not prevent semantic drift; exact evidence and next repair scope are in CODEX_HANDOFF.md. Active: M5 v84, M8 v44, full-fit worker `sha256:11d5b351609b40f9e5c46362a59ff2c620a403503bbb8f6e8ae0f57c57eef7ec`. No current-version accepted matrix.


## Authoritative production update — 2026-09-21 after three-sample M5 gate deploy

This section supersedes older version snapshots above where they conflict.

- Git main: `786bf008593ae8c42e9ef6d580033eb035297206`.
- M5 `VideoM5Storyboard001`: active, versionCounter 97, activeVersionId `9cfd4e2d-883f-417c-933d-6b553c5b73c9`. The published graph forces every accepted timing-stability path through the third independent TTS synthesis and the existing 2-of-3 gate.
- M8 `VideoM8Visuals001`: active, versionCounter 50, activeVersionId `310816fc-fbf3-46e9-983b-b6f612ea009a`.
- Exact pre-deploy M5 backup: `.backups/m5-before-three-sample-gate-20260921-190126.json`.
- Other 31 workflow rows unchanged by the M5 publication; aggregate hash `99baea155409822fc83fa57cb2896c05`; workflow inventory 32 total / 15 active.
- Publisher HTTP 200; Studio HTTP 200; n8n restart count 0.
- media-worker healthy, restart count 0, image `sha256:11d5b351609b40f9e5c46362a59ff2c620a403503bbb8f6e8ae0f57c57eef7ec`.
- Last fresh PL15 `dfd72856-9480-44d4-9e07-f8decae7ae9f` is immutable `voiceover_failed`: M4 9179 PASS, M5 9180 PASS on the pre-fix v97 versionId `3ce4729e-1f30-4b32-ae99-88aa91109308`, M6 9181 FAIL after four out-of-window TTS candidates. M7-M9 did not run.
- Runtime proof for the newly published M5 version is still pending. Do not claim PL15 acceptance or start EN30 until a new fresh PL15 reaches machine PASS and passes exact-file manual review.


## Authoritative production update — 2026-09-21 after M8 v51 spatial-domain fix

This section supersedes older M8 snapshots above where they conflict.

- Git main before runtime verification: `ec6c2acc0335a9494040050fc54fd08f0a72a76d`.
- M5 `VideoM5Storyboard001`: active, versionCounter 97, activeVersionId `9cfd4e2d-883f-417c-933d-6b553c5b73c9`.
- M8 `VideoM8Visuals001`: active, versionCounter 51, activeVersionId `f242881a-d79e-449d-a8c8-68d65ec54cde`.
- M8 v51 excludes `outdoor/outdoors/indoor/indoors` only from singleton-machinery local operating-domain inference. Repeated-subject context and scorer thresholds are unchanged.
- Exact pre-deploy M8 backup: `.backups/m8-before-spatial-domain-fix-20260921-192246.json`.
- Other 31 workflow rows unchanged by publication; aggregate hash `8fbf6b2399f8dd92c1c391dcee4308cf`.
- Publisher HTTP 200; Studio HTTP 200; n8n restart count 0; media-worker healthy restart count 0.
- Last fresh PL15 `67a1e838-038e-45d6-aa95-16c4638bbebd` remains immutable `visuals_failed`; its exact S4 defect and v51 fix evidence are in `docs/acceptance/2026-09-21-pl15-v50-s4-spatial-domain-fix.json`.
- Runtime proof for M8 v51 is pending. Do not claim PL15 acceptance or start EN30 until a new fresh PL15 reaches machine PASS and passes exact-file manual review.


## Authoritative production update — 2026-09-21 after M5 v98 deploy

- Git main fix commit: `1ac2c948e6a44c11f11a51c59ccab41a7226a447`.
- M5: versionCounter 98, activeVersionId `ce78a67f-bce4-45fb-bbf8-2d421b3c3142`.
- M8: versionCounter 51, activeVersionId `f242881a-d79e-449d-a8c8-68d65ec54cde`.
- Exact M5 backup: `.backups/m5-before-late-semantic-retry-20260921-193037.json`.
- Other 31 workflow rows unchanged; aggregate hash `efd8e340d7b44dc59429062d4b1bda5f`.
- Publisher/Studio 200; n8n restart 0; media-worker healthy restart 0.
- Runtime verification of M5 v98 is pending.


## Runtime incident update — 2026-09-21 task-runner transient

- Job `64511f0b-16a1-40ba-9930-9499cf92d7f1` is terminal `script_failed` after reconciliation.
- M4 `9195` passed. M5 `9196` loaded active v98 `ce78a67f-bce4-45fb-bbf8-2d421b3c3142` but n8n task execution failed before normal workflow failure handling because task-runner offers expired.
- Project DB stale `scripting/running` state was reconciled through deployed `factory.fail_script()`; no manual row update was used.
- Production versions remain M5 v98 `ce78a67f-bce4-45fb-bbf8-2d421b3c3142` and M8 v51 `f242881a-d79e-449d-a8c8-68d65ec54cde`.


## Authoritative continuation — 2026-09-21 after PL15 M8 v51 S3 failure

- Git/production before the WIP checkpoint: M5 v98 `ce78a67f-bce4-45fb-bbf8-2d421b3c3142`; M8 v51 `f242881a-d79e-449d-a8c8-68d65ec54cde`.
- Fresh PL15 `9844d17f-1548-4ecb-97bf-6b9e56b0c7fe` passed M4-M7 and failed only M8 S3-A after all 45 provider searches completed. M9 did not run.
- The earlier n8n task-runner offer-expiry incident did not recur; M5 v98 executed successfully and the three-sample stability-B path was exercised.
- Exact M8 defect is now retrieval/semantic-context related: broad Commons fallback `hydroelectric electric generator` returned mostly station/building results while S3 requires a depicted generator inside hydroelectric power-station context.
- Repository contains a **WIP, not deployed** M8 scorer refinement:
  - `powerhouse` supplies `power station` semantic evidence in the specific-to-generic direction only;
  - secondary compound must-show context now uses full profile threshold rather than any single token.
- Existing suite remains 92/92 PASS and JSON/diff checks pass.
- Missing next implementation: generic bare-machinery fallback enrichment to add `equipment` only to effective `provider_query` while preserving original `query_text`.
- Do not treat this WIP commit as production parity: production M8 remains v51 until the completed fix is regression-tested and deployed.

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
