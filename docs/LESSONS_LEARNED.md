# Lessons Learned

Updated: 2026-09-19

1. A restored DB is not automatically production-ready.
Verify owner/auth, project ownership, N8N_PATH, editor URL, webhook URL, and asset paths before cutover.

2. user-management:reset changes auth state.
It preserved workflows and credentials but returned the instance to owner setup. Only use it with an explicit owner re-creation plan.

3. Wrong N8N_PATH can produce a white UI.
Root HTML pointed to /recovery assets and the browser received wrong content for JavaScript. Production root must use N8N_PATH=/ and asset paths must be verified after changes.

4. Do not run duplicate n8n servers on one DB.
Recovery and root must never be active against the same restored single-instance database.

5. A foreign whole .env is not a fix.
The clean shorts-v2 compose was temporarily pointed at a recovery .env and inherited the wrong encryption-key state. shorts-v2 must use only its own .env.

6. n8n volume config can preserve a stale encryption key.
Even after compose was corrected, /home/node/.n8n/config still contained the key created under the bad recovery environment. Inspect the config first; do not blindly replace project secrets.

7. Exit code 0 is not proof of a DB mutation.
A heredoc sent to docker exec without -i did not reach psql. Always verify post-counts and exact IDs.

8. Do not touch unrelated n8n.
n8n.hodor.com.pl is unrelated. publisher.hodor.com.pl contains MCP/business workflows that must remain intact.

9. Google Cloud TTS historically worked, and restored OAuth status must be verified by a live provider call.
The August backup proves repeated successful Cloud TTS executions with the selected voices. On 2026-09-19 the restored OAuth initially failed live refresh despite the UI showing `Account connected`; reconnecting the same credential fixed it and all four locked voices passed.

10. Gemini TTS is not production TTS.
Production narration remains Google Cloud Text-to-Speech.

11. Historical visual failures were systemic.
Too few images and generic loosely related assets are unacceptable. Every shot needs visual intent, must-show/must-not-show, multiple search queries, multi-source discovery, deterministic ranking, and fail-closed relevance.

12. Human review is final.
Machine PASS is provisional. Only explicit HUMAN PASS accepts the exact final MP4.


13. Restoring credentials into the intended production n8n determines where orchestration belongs.
The 9 credentials were restored into `publisher.hodor.com.pl` so the video project could use them there. Creating another n8n afterward defeats that work and creates unnecessary OAuth, routing, authentication and encryption-key problems.

Prevention:
- production video orchestration stays in `publisher.hodor.com.pl`;
- MCP/ADMIN workflows remain protected by exact identity;
- supporting services may be isolated, but production n8n/credentials stay in publisher;
- no new n8n domain or second production n8n without a proven technical blocker and explicit user approval.


14. An encrypted n8n credential export is not a usable recovery source without its original encryption key.
The related recovery export still contains the old Google Gemini API credential metadata, but the source encryption key is not preserved in the project/recovery files and the available recovery key does not decrypt it.

Prevention:
- preserve the matching n8n encryption key whenever encrypted credential exports are retained;
- never treat credential presence in an encrypted export as proof that the secret is recoverable;
- do not copy encryption keys from unrelated n8n instances as a shortcut.


15. Do not double-escape executable strings when generating n8n workflow JSON.
The first M3 Postgres node stored literal `\\n` sequences inside SQL. n8n passed the backslashes to PostgreSQL, which failed with a syntax error near `\`.

Prevention:
- generate executable SQL/code as the actual runtime string, then JSON-serialize it exactly once;
- after importing a generated workflow, read the stored node parameter back from the n8n database before publishing;
- run a real workflow execution, not only a JSON/schema validation;
- treat a successful credential connection as separate from query correctness.

16. A Code node returning multiple items must use Run Once for All Items.
The first M4 execution used Run Once for Each Item but returned an array of items, so n8n rejected the output before search.

Prevention:
- when a Code node fan-outs one input into multiple items, use `runOnceForAllItems`;
- test node execution semantics, not only JavaScript syntax.

17. Prefer provider-parsed URL metadata over browser globals inside the n8n Code sandbox.
SearXNG already returns `parsed_url`. The first M4 candidate normalizer wrapped `new URL(...)` in a catch; every candidate was silently discarded in the Code sandbox. Rebuilding canonical URLs from SearXNG `parsed_url` produced the expected 10 independent candidates.

Prevention:
- use structured provider fields when available;
- never hide every parse failure behind a catch that converts the entire candidate pool to empty;
- unit-check candidate counts on retained real provider output before consuming another product test job.


18. A scene-count range plus a separate shot-count floor does not reliably produce the required visual density.
The first M5 live output was otherwise valid, but Gemini chose 5 scenes and one shot per scene, producing 5 shots when a 30-second job required at least 7. The validator correctly rejected it and the job remained immutable.

Prevention:
- do not weaken the visual-density gate after underproduction;
- use a deterministic generic density contract by duration;
- M5 now requires exactly 4/7/10/13 scenes and exactly one shot per scene for 15/30/45/60 seconds;
- test fixes only on a fresh job after a terminal failure.


19. Before modifying the next milestone, inspect existing local stage files and the live database state.
M6 already had a local migration, production workflow and applied DB schema from the immediately preceding work. Rebuilding the stage from memory would have duplicated or weakened already-established invariants.

Prevention:
- before creating a new milestone file, search the project for that milestone/workflow name;
- inspect live DB tables/functions and publisher workflow rows first;
- preserve stronger existing invariants instead of replacing them with a newly improvised contract;
- only apply a migration after confirming whether its objects already exist.


20. Never rely on the repository directory name for the Compose project identity.
During M7 a bare `docker compose` command briefly created a new empty `ai-short-form-content-factory-media-worker-1` and `ai-short-form-content-factory_media_data` instead of targeting the existing `shorts-v2` project. The accidental resources were identified as new/empty and deleted immediately; the production `shorts-v2_media_data` volume and container were not modified.

Prevention:
- `compose.yaml` now declares top-level `name: shorts-v2`;
- verify `docker compose config --format json` reports `name=shorts-v2` before service changes;
- inspect exact container/volume names before cleanup;
- never use `--remove-orphans` here because unrelated recovery containers can exist on the host.


21. Exact scene-density requirements need one bounded model repair path, not a weaker gate.
Gemini occasionally returned 5 scenes for a 30-second job even after the prompt explicitly required 7. A later repaired response produced the correct scene count but a redundant root narration field that did not exactly equal the joined scene narrations.

Prevention:
- keep the deterministic 4/7/10/13 scene+shot contract;
- allow exactly one Gemini repair-call inside the same immutable M5 script run;
- give the repair the same evidence, the failed output and the exact validation error;
- make validated scene narrations authoritative and derive the persisted continuous narration from their join;
- never lower the required scene/shot count just to make a model response pass.


22. Whisper transcription equality is too strict to be the alignment gate.
A real immutable TTS file was correctly spoken, but local Whisper transcribed `abscission` as `obsidian`. The normalized global match was 0.981675 and the lowest scene match was 0.883721, while token timing remained usable and monotonic.

Prevention:
- keep exact audio SHA/model/runtime checks;
- require Whisper lexical tokens to reconstruct the Whisper transcript exactly;
- use bounded sequence-match coverage: global >= 0.95 and every scene >= 0.85;
- derive scene boundaries only from real matching Whisper token timestamps;
- never substitute proportional timing when lexical coverage is inadequate.


23. Wikimedia Commons HTTP 429 must be handled from Retry-After, not by blindly slowing every request.
The provider consistently accepted the first ten requests and then returned 429 with Retry-After values around 23–27 seconds. Increasing the ordinary batch interval did not solve the burst limit.

Prevention:
- persist successful provider items immediately;
- retry only the affected Wikimedia 429 items;
- wait 35 seconds before each explicit retry;
- cap retries and fail closed if provider coverage remains incomplete;
- do not rerun successful Pixabay/Pexels/Wikimedia items just because another item was throttled.


24. Wikimedia Commons asset delivery uses more than one official hostname.
Commons video originals commonly use `upload.wikimedia.org`, while generated image thumbnails can use `thumb.wikimedia.org`. Restricting the downloader to only the upload hostname caused two otherwise valid selected Wikimedia photos to fail persistence.

Prevention:
- allowlist exact official hosts `upload.wikimedia.org` and `thumb.wikimedia.org`;
- continue rejecting arbitrary redirect/download hosts;
- validate the downloaded file with SHA-256 and ffprobe before DB persistence;
- test allowlist changes against an actual provider-returned URL, not a synthetic hostname.
