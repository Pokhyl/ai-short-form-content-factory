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

36. A supported fact can still be wrong for the user's question, and a timing rewrite must preserve scene identity before TTS.
Execution 9065 showed both failure modes: a generic environmental benefit was evidence-supported but did not answer the mechanism topic, and the first timing rewrite duplicated one turbine sentence across multiple scenes.

Prevention:
- require every scene to directly advance the user topic, not merely cite supporting evidence;
- for how/process topics, keep the scene sequence causal and use the final scene for the mechanism/output, not generic benefits;
- validate each timing-rewritten scene against its own immutable original scene before another TTS call;
- reject duplicate scene narration;
- route semantic failure into an existing bounded regeneration step before consuming another TTS probe.

37. A median timing estimate is not enough when identical Chirp3-HD syntheses are multimodal.
One PL narration produced 13.536 s, 15.576 s, and 16.704 s with the same voice/config. Accepting because the median and only one sample were in-window allowed M5 to pass a script that M6 could not reliably synthesize inside its final gate.

Prevention:
- keep the median of multiple real syntheses for a robust center estimate;
- additionally require a majority of the real samples to be inside the unchanged final tolerance;
- do not widen timing gates to hide stochastic TTS behavior;
- do not add blind retries when repeated candidates return identical out-of-window audio hashes;
- compare exact audio hashes and request configuration before blaming workflow configuration.

38. Optional workflow branches must not be read as mandatory execution history.
After first-repair semantic fallback intentionally skipped Probe 2, a later builder crashed because it still assumed that node had executed.

Prevention:
- distinguish immutable required sources from branch-dependent diagnostic/timing samples;
- read branch-dependent nodes with bounded optional access;
- if an optional sample is absent, use only the samples that actually executed and the existing fallback estimator;
- add tests that throw the exact n8n `hasn't been executed` error for skipped branches.

39. Visual metadata language is an executable contract, not presentation text.
A Polish narration job reached M8 with Polish `must_show` and `queries_en` even though the scorer/provider metadata path is English-oriented. Retrieval found relevant dam assets, but the required anchors could not match.

Prevention:
- narration uses the requested user language; visual metadata always uses English;
- enforce the split in deterministic validators, not prompt wording alone;
- reject Cyrillic/Polish-language leakage and mixed-language primary anchors before TTS/visual retrieval;
- use the existing bounded storyboard repair attempts to correct metadata while preserving narration/evidence/IDs.

40. A generic object name does not establish its mechanism context, and a title may name equipment absent from the photograph.
Execution 9125 selected a steam turbine, oil-engine generator and transformer signage for hydroelectric narration; exact final frames confirmed the mismatch.

Prevention:
- retain an established storyboard domain across repeated primary subjects and broad fallback queries;
- derive context from storyboard evidence, never hardcode acceptance topics or rejected asset IDs;
- distinguish a photograph of signage/doors from the equipment named by the title;
- do not blanket-reject museum images: an actual hydroelectric runner is valid static illustration;
- replay the complete original candidate pool and report newly empty pools honestly before another live job.

40. A relevance guard cannot improve retrieval if its context never reaches the provider query.
M8 v46 learned repeated-subject domain context and correctly rejected off-domain assets, but HTTP searches still used the broad original storyboard query. This produced safe failures rather than useful replacements.

Prevention:
- preserve storyboard query provenance separately from the effective provider search string;
- use established context to enrich only the actual provider query;
- store the effective provider query explicitly and use it as the cache key;
- keep scorer evaluation against the original query plus explicit domain context;
- prove retrieval adequacy with targeted provider calls before spending a full pipeline job.

41. A singleton machinery subject can still need an explicit local operating domain.
A fallback query can preserve the primary noun (water turbine) while losing the scene-defining location/domain (inside a hydroelectric power station). That allowed a theme-park water turbine to score 100.

Prevention:
- for machinery primaries, retain a specific local domain/location qualifier when it is supported by both visual_intent and planned queries;
- enrich provider search without overwriting original query provenance;
- keep the domain gate independent from primary form modifiers;
- do not blacklist venues such as museums or theme parks; accept them only when metadata establishes the requested operating domain;
- prove the new query still returns eligible candidates before spending another full pipeline job.


42. A correct three-sample timing rule is ineffective if the workflow graph can bypass it.
A fresh PL15 passed M5 but failed M6 after four independent TTS candidates. The final narration had received only the original M5 timing sample plus one stability confirmation; the graph sent that two-sample success directly to canonicalization, so the existing 2-of-3 majority code in Stability B never ran.

Prevention:
- every accepted final narration must traverse the third independent stability synthesis;
- only the three-sample majority gate may route to final storyboard canonicalization;
- test workflow connections as well as Code-node logic, because correct code in an unreachable/bypassable branch is not an enforced contract;
- keep M6 as the strict immutable final-audio gate and do not widen its duration tolerance.


43. Spatial presentation words are not machinery operating domains.
A singleton machinery shot can legitimately say that equipment is outdoors or indoors without requiring provider metadata to contain that literal presentation word. Treating such words as domain gates rejected a strong transformer-at-power-station photo solely because its caption did not say `outdoors`.

Prevention:
- local operating-domain inference must exclude generic spatial/presentation terms such as outdoor/outdoors/indoor/indoors;
- preserve real semantic domains such as hydroelectric, marine or substation when they are established;
- do not weaken scorer thresholds to recover candidates that were rejected by a bad inferred constraint;
- regression-test both planner output and exact candidate normalization.


44. A fail-closed semantic guard still needs a bounded recovery path when one already exists.
The first late timing repair can be semantically rejected without meaning the immutable source is unusable. Sending that first rejection directly to terminal failure wasted the existing single retry designed to regenerate from immutable original narration.

Prevention:
- keep semantic thresholds unchanged;
- first late semantic miss may use the already-bounded regeneration path from immutable original text;
- the retry validator remains terminal fail-closed;
- never turn this into an unbounded retry loop.

45. Primary machinery form modifiers must not erase independent secondary compound meaning.
The S3 WIP used the same mutable generic-anchor set for primary and secondary profiles; adding power as a primary modifier reduced power station to station. Preserve the baseline secondary set and test an unrelated railway station negative across all providers. Bare machinery retrieval may append generic equipment to the effective provider query while keeping storyboard provenance immutable. Metadata acceptance, especially of historical imagery, still requires final visual/narration review.

46. Domain inference must exclude generic object/form words consistently with scoring.
Execution 9212 inferred unit as a machinery domain and sent hydroelectric unit generator equipment, emptying the S4 Commons pool. Reuse generic-object semantics for planner exclusions and test repeated-subject context remains present. Nameplates are signage, not evidence that the named machinery is depicted; extend the existing surface guard and retain requested-nameplate positives.

47. Before weakening a late exact-count guard, check the existing regression and candidate history.
Execution 9221 had useful measured short scene alternatives, but the final dynamic program saw only recent longer drafts. Reuse a bounded set of same-execution measured scenes, verifying immutable semantics and scene identity again. Keep the intentional final exact-total guard (9137), provider budget, actual TTS gate and stability rules unchanged; successful code replay does not establish audio duration.

48. A local scorer regression fix needs whole-run replay before another live job.
Execution 9229 stopped at S1, but replay of all 335 candidates also found an empty S5 pool and a singleton S4 domain omission. A secondary-head experiment made the exact S1 source eligible but also admitted an unverified PNG summary. It was reverted without deployment. Keep experiments explicitly separate from production evidence and avoid spending a new complete job when later known pools remain empty.

49. Provider taxonomy is context, not proof that every named object is depicted.
A Commons category can correctly classify a file under both a dam and its reservoir even when the frame shows only the dam face/spillway. Using that category as direct evidence for an independent secondary `must_show` produced a semantic false positive.

Prevention:
- keep primary classification evidence separate from secondary depicted-object evidence;
- for a secondary visible object, prefer title/object/direct short caption and only taxonomy segments independent of the primary subject;
- preserve meaningful secondary noun heads instead of discarding them as generic anchors;
- non-photo maps/summary graphics remain fail-closed even when every topic keyword matches;
- when a storyboard explicitly requires an operating plant/station, museum/manufacturing/transport context may be treated as a contradiction, but never as a global blacklist;
- before another full job, replay the entire saved candidate pool and simulate the actual database selection ordering, not just candidate eligibility.


50. A hidden process inside a closed object is not a hard depicted subject.
A fresh PL15 asked M8 to prove both flowing water and a penstock in one real photograph even though the storyboard explicitly placed the water flow inside the closed penstock. The scorer correctly failed; weakening it or merely broadening retrieval would have converted an unphotographable contract into false acceptance.

Prevention:
- when a process/current/flow occurs inside or through a closed conduit or machine, use the concrete enclosure/equipment as the primary visible subject unless transparent/open/cutaway/exposed visibility is explicit;
- apply the rule before final storyboard persistence, including bounded repair and final canonicalization paths;
- when the visible enclosure has a meaningful operating domain, retain that domain on broad fallback retrieval so a generic conduit/cable/penstock does not drift into unrelated contexts;
- keep query provenance separate from effective provider query;
- do not add machinery-specific retrieval suffixes to generic infrastructure unless evidence proves they improve results.


51. A timing regression must never contradict the direction implied by the latest real measurement.
Execution 9287 measured a 22-word narration at 14208ms, slightly below the unchanged final window, so the correction had to be longer. A noisy multi-sample linear fit nevertheless returned a 21-word target. The hard retry then correctly enforced the wrong target, and three TTS samples confirmed the result was much too short.

Prevention:
- derive LONGER/SHORTER from the latest accepted measurement and unchanged target window;
- accept regression estimates only when they move words/characters in that direction;
- otherwise fall back to proportional scaling from the latest real TTS sample;
- keep semantic floors, exact-count validation, stability majority and duration tolerance unchanged;
- regression/prediction is guidance only; measured TTS remains the acceptance authority.


### 45. An operational-setting intent needs positive evidence, not only absence of contradictions
A candidate can contain every requested machine noun and still depict the wrong world (for example an aircraft wind-driven generator instead of a generator inside a power plant). If the storyboard explicitly requires plant/station/facility/powerhouse context, scorer acceptance must positively establish that setting from strong metadata. Negative museum/manufacturing filters alone are insufficient. Keep this generic and compound-aware: `power plant` may be satisfied by `power station`, but an unrelated bare `plant` token is not enough.


52. Retrieval failures can hide behind an earlier zero-pool shot; inspect all scene pools before another live job.
A v56 PL15 stopped on S3, but the same persisted run already showed S5 had zero eligible candidates too. Spending another full job after fixing only S3 would have reproduced a different terminal failure.

Prevention:
- after any M8 failure, inspect eligible counts for every shot in that same completed 45-search run;
- machine components such as shaft/stator/armature/impeller/bearing/coupling are not operating domains;
- compound negative subtypes such as `coal power plant` require the distinctive forbidden modifier, not only generic head overlap;
- if a multi-object fallback query omits a required subject, enrich only the effective provider query and preserve storyboard provenance;
- small lexical retrieval equivalences such as home/house are acceptable when scorer semantics remain strict and independent required subjects are still enforced;
- provider MIME policy must reflect the actual bytes downloaded: a TIFF original may be usable when Commons supplies a safe JPEG/PNG/WebP thumbnail, but the original TIFF must remain excluded from the media path;
- validate all affected shot pools and simulate real selection ordering before deploying.


53. Canonicalize harmless leading visual modifiers before rejecting a concrete short anchor.
A bounded repair can legitimately return a four-token noun phrase such as `high voltage power lines`. Rejecting it solely on raw token count wastes the existing repair budget even though the searchable physical subject is simply `power lines`.

Prevention:
- keep the 1–3 word hard anchor contract after canonicalization;
- strip only a tightly controlled set of leading modifier pairs or generic leading visual modifiers;
- never truncate arbitrary trailing words or descriptive prose to force acceptance;
- preserve richer context in visual_intent and queries while keeping must_show concise;
- replay the exact failed provider response through the validator before another live job.


54. Hidden contents of closed infrastructure are not independent visible requirements or operating domains.
A storyboard can correctly describe water flowing through a penstock while the image can only prove the closed penstock itself. Treating `flowing water` as a hard secondary must_show, or `water` as the penstock's operating domain, makes valid infrastructure photography impossible.

Prevention:
- if the primary is a closed conduit/machine, remove secondary process/action anchors unless the visual intent explicitly requests transparent/open/cutaway/exposed visibility;
- transported media such as water/steam/oil/gas/air/fuel/liquid/fluid may remain useful retrieval words but must not automatically become hard domain context for closed infrastructure;
- do not apply that medium filter globally to machinery forms such as gas/steam turbines; scope it to closed infrastructure;
- after an M8 failure, inspect every shot pool in the completed run before spending another job;
- prove a corrected fallback against persisted/cache candidates before deploy.


55. Do not let one stochastic Chirp synthesis dictate late word-count correction.
The same text/voice/config can vary by more than a second. A late single timing sample can therefore be an outlier and must not directly force a new word target.

Prevention:
- use the same bounded near-miss stability candidate logic on late Probe 4 that already exists on Probe 5;
- route failed origin-4 stability to measured correction, not directly to terminal failure;
- keep exact word count as a preferred heuristic, not the final timing truth;
- a close semantic hybrid may reach the real final TTS probe only inside a tight bounded delta; farther hybrids stay fail-closed;
- the final timing decision remains based on actual multi-sample TTS duration, not word count.


56. A bad timing rewrite in one scene should not force acceptance or terminate the whole precision stage when a safe same-scene fallback exists.
The semantic guard correctly rejected `potężnie`; weakening that guard would be wrong. The reusable recovery is scene-local: preserve valid precision scenes, and for only the failing scene reuse a previous narration if it independently passes the immutable semantic reference, otherwise use the immutable original.

Prevention:
- never sanitize prohibited filler into acceptance by lowering semantic thresholds;
- validate fallback scenes independently against immutable original meaning;
- never borrow narration from a different scene identity;
- recompute total word/safety envelopes after hybridization;
- let subsequent real TTS probes decide duration.


55. A visual regression must be replayed against immutable provider responses, and changed retrieval must be captured separately.
Re-running a whole job while scorer/query logic is still changing hides whether a fix came from scoring, provider search variability, or a new storyboard. Execution 9229 demonstrated a better acceptance pattern.

Prevention:
- freeze the exact workflow version, storyboard, must_show/must_not_show and raw provider responses from the failing execution;
- replay old and new scoring on those exact inputs without project DB writes;
- when provider_query changes, capture only those new searches into a separate immutable overlay;
- apply the overlay only to matching provider/shot/query/provider_query keys and fail if any overlay row is stale or unused;
- reproduce production selection ordering, not an ad-hoc score sort;
- inspect the final selected image for every scene manually before any full pipeline rerun;
- reject candidates whose metadata explicitly says the requested primary is only background unless background composition is requested.


56. n8n retryOnFail can be bypassed by continueErrorOutput for HTTP nodes.
In n8n 2.37.10, workflow execution retry detection inspects `main[0][0].json.error`. An HTTP node configured with `onError=continueErrorOutput` can therefore report a 503 in output 2 while the node execution itself is considered successful, bypassing `retryOnFail`.

Prevention:
- for transient external HTTP providers that must use n8n node retries, expose terminal request errors on the main output with `continueRegularOutput`;
- keep `retryOnFail` bounded and use the actual runtime cap for `waitBetweenTries`;
- immediately detect top-level `json.error` in the downstream validator and preserve the provider message;
- keep existing semantic/timing recovery budgets independent from transport retries;
- verify live published node configuration against repository before blaming provider behavior.


56. A transient provider failure inside a bounded repair must not erase the last usable deterministic draft.
When a repair API call fails after retries, the next repair stage should recover from the latest usable model output and the deterministic validation error that actually needs fixing. Treating the failed provider response as the only source can turn a recoverable provider outage into a false empty-output terminal failure.

Prevention:
- keep the original successful draft addressable through later bounded repair stages;
- prefer the most recent usable repair output, but fall back to the original draft when the repair call produced no candidate text;
- preserve deterministic validation errors separately from provider transport errors;
- provider outages may add context, but must not replace the actual content-repair reason.


57. A deterministic hybrid must validate every candidate option before optimization, not only the final combination.
If dynamic programming can choose from retry/base/pre-final/measured scene variants, any unvalidated source can reintroduce a line that an earlier semantic gate already rejected.

Prevention:
- apply the immutable semantic guard to every line before adding it to the candidate option set;
- exclude invalid options rather than relying only on a final whole-output check;
- treat retry/base/pre-final/measured variants uniformly;
- fail closed when a scene has no semantic-valid candidate.


58. Do not predict a future stochastic TTS synthesis when a real accepted synthesis already exists.
Repeated Chirp3-HD calls for identical text can differ by several seconds. A script-stage majority/median gate cannot guarantee that a later independently synthesized M6 file will have the same duration.

Prevention:
- treat an actual in-window MP3 as the artifact, not merely as a timing sample;
- persist its exact SHA, duration, audio metadata, narration and committed provider-usage ledger;
- reuse that exact file downstream rather than re-synthesizing the same narration;
- keep the final M6 persistence/duration/SHA checks fail-closed;
- use a new TTS call only when no persisted accepted candidate exists.


59. Operational scene context is a set of compatible locations, not a requirement that every location phrase appear literally.
A storyboard may describe an electrical transformer as being in a substation near a power plant. If the candidate directly proves the requested substation and transformer, requiring the metadata to also repeat `power plant` creates a false rejection.

Prevention:
- preserve strict `power + plant/station` evidence when the only proved setting is a generic plant/station;
- allow an explicitly requested concrete grid setting such as substation or switchyard to independently satisfy the operational-setting gate;
- do not make presentation words such as outdoors into domains;
- for Wikimedia, allow concrete category segments to prove a machinery class only when the requested primary is machinery and the category itself satisfies that machinery concept;
- do not extend category-only depiction proof to reservoirs, people, animals or other contextual taxonomy.


60. Visual scene boundaries are not sentence boundaries.
A short-form video can require five visual changes while the natural continuous voiceover contains only two or three sentences. Requiring every scene narration to be a standalone sentence forces unnatural text or repeatedly rejects otherwise valid continuous narration.

Prevention:
- define each scene narration as an exact contiguous segment of the continuous voiceover;
- allow visual cuts inside sentences;
- enforce scene-level word bounds, evidence and semantic preservation without requiring per-scene terminal punctuation;
- require the joined narration, not each segment, to have a normal beginning and complete terminal punctuation;
- keep alignment token-based so mid-sentence visual cuts remain precisely timeable.


60. A broad primary subject is not enough when the storyboard requests a visually distinctive component.
A candidate can correctly depict a water stream or water turbine while still being wrong for a shot that specifically requires a penstock, runner blades, or an operating shaft.

Prevention:
- keep `must_show` as the broad visible subject contract;
- derive a separate hard detail gate only for concrete component terms shared by the visual intent and the most-specific query;
- never promote arbitrary adjectives, action words, locations, or topic terms into hard detail gates;
- add missing detail terms to provider retrieval without rewriting original query provenance;
- if no saved/provider candidate proves the required detail, fail closed rather than selecting a generic subject image.


61. An anaphoric scene cut does not always mean the visual primary must remain unchanged.
A continuation such as `która wprawia w ruch generator` inherits the turbine as grammatical subject but also explicitly introduces the generator as a concrete visible object. Rejecting every primary change forces valid continuous narration into artificial scene wording.

Prevention:
- allow the inherited previous primary;
- allow a changed primary only when its concrete noun is explicitly grounded in the current narration segment;
- keep unmentioned object switches fail-closed;
- make prompts and validators use the same rule.

62. Per-scene semantic validity does not guarantee continuous narration after mixing drafts.
Execution 9788 moved “continuously” across a visual cut in one draft. Combining that draft with the older preceding scene duplicated the word. Validate scene boundaries during hybrid assembly and after joining; preserve intentional original repeats. Regression fixtures must be tracked in Git, not only in ignored operator review folders.
