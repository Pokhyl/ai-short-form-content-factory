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
- historical contract at that point required exactly 4/7/10/13 scenes and one shot per scene; current production later increased this to 5/9/13/17 for 15/30/45/60 seconds;
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
- keep the deterministic scene+shot contract strict; the historical 4/7/10/13 values were later superseded by the current 5/9/13/17 production contract;
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


23. Wikimedia Commons HTTP 429 needs bounded pacing and isolated retries.
Earlier production tests observed bursts of HTTP 429 with Retry-After values around 23–27 seconds. The current implementation later evolved to explicit 8-second per-item pacing plus isolated retry branches.

Prevention:
- persist successful provider items immediately;
- retry only the affected Wikimedia 429 items;
- current production waits 60 seconds before each explicit Wikimedia retry and uses 8-second request batching;
- cap retries and fail closed if provider coverage remains incomplete;
- do not rerun successful Pixabay/Pexels/Wikimedia items just because another item was throttled.


24. Wikimedia Commons asset delivery uses more than one official hostname.
Commons video originals commonly use `upload.wikimedia.org`, while generated image thumbnails can use `thumb.wikimedia.org`. Restricting the downloader to only the upload hostname caused two otherwise valid selected Wikimedia photos to fail persistence.

Prevention:
- allowlist exact official hosts `upload.wikimedia.org` and `thumb.wikimedia.org`;
- continue rejecting arbitrary redirect/download hosts;
- validate the downloaded file with SHA-256 and ffprobe before DB persistence;
- test allowlist changes against an actual provider-returned URL, not a synthetic hostname.

25. Still-image full-range pixel formats must be normalized explicitly for the final H.264 contract.
JPEG inputs produced `yuvj420p` even when the encoder was given `-pix_fmt yuv420p`. The machine gate correctly rejected the segment.

Prevention:
- for still-image inputs, convert full-range to TV-range explicitly before `format=yuv420p`;
- do not apply the same forced range conversion blindly to source videos that may already be limited-range;
- keep the final QA gate strict at `yuv420p` rather than weakening it to accept `yuvj420p`;
- verify the exact encoded segment with ffprobe before final concatenation.

26. Generate FFmpeg concat lists with real newline bytes, not escaped backslash-n text.
The first M9 unit render created all seven valid segments but could not create `video-only.mp4` because `concat.txt` contained literal `\\n` characters.

Prevention:
- write actual newline characters to concat manifests;
- inspect the manifest bytes when concat fails after successful segment encoding;
- test concat and final mux separately before consuming a normal product render attempt.

27. Repeated manual Docker restarts can corrupt a container restart-manager/rootfs state even when application data is external.
`ai-short-form-n8n` entered a restart loop with exit 137 while kernel logs showed no OOM. Docker reported `invalid call on an active restart manager` and a missing overlayfs rootfs path.

Prevention:
- avoid stacking `docker restart` calls after timed-out control commands;
- verify container state before issuing another lifecycle action;
- if the stateless n8n container rootfs/restart manager is corrupted, preserve `docker inspect`, confirm PostgreSQL is external, then recreate only that container from the exact image/env/networks;
- never recreate or modify the publisher PostgreSQL as part of this recovery;
- after recovery verify protected workflows, credentials, publisher HTTP and restart count before resuming project work.


28. Planning word-count heuristics must never overrule measured TTS.
Word count was useful for bounding runaway scripts but repeatedly rejected narrations whose real TTS duration was acceptable.

Prevention:
- use word counts only as structural/anti-runaway bounds;
- use real TTS measurements for timing decisions;
- let M6 remain the strict final-audio duration gate.

29. Preview TTS is stochastic enough that median matters more than single-sample spread.
Identical Chirp-style synthesis requests produced materially different durations for the same narration.

Prevention:
- use multiple real preview syntheses;
- use the median as M5's robust estimate;
- do not loosen the configured timing tolerance;
- require M6's independently synthesized final audio to pass the strict measured-duration gate.

30. Provider availability must degrade independently from visual quality.
A Pexels HTTP 403 from the VPS previously failed the whole visual stage before Pixabay/Wikimedia could satisfy the same shot.

Prevention:
- persist real provider HTTP failures as failed search rows with zero candidates;
- never pretend a failed search was HTTP 200;
- do not cache failed provider responses;
- keep the final per-shot compliant/relevant selection gate strict.

31. Provider MIME declarations must be checked against downloader support before selection.
A Wikimedia GIF was classified broadly as an image/photo candidate and selected, then failed in the media-worker.

Prevention:
- maintain an explicit MIME allowlist aligned with media-worker support;
- reject unsupported formats before ranking/selection.

32. Compound visual anchors cannot require every descriptive token literally in provider metadata.
Real photos used correct domain subjects while omitting generic form/function words such as receiver, navigator, runner, chamber, pool or mouthparts.

Prevention:
- distinguish true domain-subject terms from generic form/function descriptors;
- when distinctive terms exist, require a real distinctive subject match plus query/intent context;
- keep zero-distinctive-match cases fail-closed;
- regression-test known positive candidates and an unrelated negative control.

33. Free-tier LLM acceptance tests should be sequential when concurrent calls exceed provider RPM.
Running all four matrix rows concurrently caused Gemini HTTP 429 failures unrelated to factory correctness.

Prevention:
- run the acceptance matrix sequentially;
- preserve the exact same topics/languages/durations;
- treat rate-limit failures separately from product-quality failures.

34. Provider `photo` and `isAiGenerated=false` flags plus keyword tags do not verify visible content.
Fresh EN30 passed machine QA, but exact scene review found a graphic poster and a honey jar selected for photographic bee scenes. Pixabay returned both as ordinary photos, and their tags matched the narration.

Prevention:
- keep Pixabay searches and their real response/candidate accounting, but reject tag-only image candidates with `pixabay_photo_content_unverified_tag_only` until independent content evidence is implemented; this deliberately reduces selectable source coverage to description-supported Pexels/Wikimedia images;
- require Pexels `alt` descriptions and reject explicitly described posters/illustrations/digital graphics;
- preserve all score, timing, license and uniqueness thresholds; never blacklist the observed asset IDs or hardcode the test topic;
- technical media PASS does not imply visual acceptance; inspect scene-midpoint frames of the exact final MP4.

35. Confirming TTS with a median is insufficient if later repair models reuse the original sample.
M5 execution 9011 confirmed probe 1 at a 17,136 ms median but later interpolated using its stale 15,144 ms first synthesis. The correction overshot, causing bounded repair exhaustion.

Prevention:
- all interpolation/final-correction builders reuse available medians keyed by the exact narration text;
- never transfer a median between different scripts;
- keep the original strict timing acceptance gates and final M6 measurement;
- regression-test the measured failed sequence, not just syntax.

36. Lexical overlap must establish the pictured subject, not just mention it.
Execution 9026 selected a wasp for a bee because its background taxonomy mentioned bees, and dew for nectar because the primary compound matched only “droplets.” A replay also found proboscis monkeys for a detached anatomical fallback.

Prevention:
- primary compound identity and supplied secondary subject context must be supported by strong image-specific metadata;
- Commons long prose is weak context, not primary identity evidence;
- generic form words alone cannot establish the material/object;
- normalize ordinary plurals consistently;
- storyboard anchors name the complete visible main subject, keeping internal mechanisms in narration and using relevant real physical context;
- replay original provider responses, including negative controls, before consuming more live acceptance jobs.

Complete query coverage and accounting must change together. Restricting Commons to only the longest first query discards concise fallback searches that retrieve the actual subject. Keep paced complete retrieval and persist expected search counts per new run; do not rewrite failed runs or loosen relevance to compensate for missing searches.

Equal per-scene word quotas can remove the grammatical object from one sentence while adding filler to another. Allocate timing targets using original scene lengths and retain original narration through retries; successive drafts are not a semantic source of truth. Mechanical word-count validation does not validate factual meaning.

A relevance-approved source can lose its subject during unconditional portrait center cropping. Preserve the full source geometry unless a verified subject location supports cropping; test edge landmarks in the encoded output, not just filter-string syntax. Source semantic relevance remains a separate gate.

34. Timing retries need an immutable semantic source and fail-closed validation, not only stronger prompts.
Execution 9047 showed that an exact-word prompt can still return the wrong word count and semantic damage; later repairs then treat the damaged draft as truth.

Prevention:
- keep the first validated narration as the immutable meaning reference through all later timing branches;
- allocate later scene word targets from original scene proportions, not from a damaged intermediate draft;
- validate semantic-content retention before consuming another TTS probe;
- treat word counts as timing guidance only; semantic validation must pass first, then real measured TTS decides timing acceptance;
- preserve numeric facts and negation polarity;
- use prompt instructions and word-count targets as guidance, never as proof that meaning or timing was preserved.

35. Provider page titles can corroborate, but must never substitute for, visual description evidence.
Pexels may describe a hydroelectric plant photo as a generic `power plant with flowing water near river` while the canonical page title carries the missing subtype word.

Prevention:
- keep raw URL/title metadata separate from visible-description evidence;
- require non-empty visual description before title corroboration is considered;
- allow title metadata to fill only a bounded missing subtype gap;
- require independently matched scene context and intent overlap;
- retain negative tests proving URL-only or unrelated descriptions cannot pass.
