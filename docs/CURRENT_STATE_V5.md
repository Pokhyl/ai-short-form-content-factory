# Current State — V5 n8n Autonomous Video Orchestrator

Last updated: 2026-09-04

Branch: `rebuild/agentic-editor-v5`.

## Mandatory pre-action gate

Before any meaningful action, code change, render, test, architecture decision, dependency addition, or direction change, **read `docs/OPERATOR_EXECUTION_RULES.md` first**, then read this file.

The current primary project risk is operator/assistant decision drift: changing direction without proof, handcrafting proofs, inventing blockers, or replacing the required n8n product with side architectures. Do not repeat those patterns.

## Product definition

The product is a **free/self-hosted n8n orchestrator**.

External input:

`topic + language + requested duration`

Required n8n-controlled path:

`input -> research -> free/licensed visual inventory -> visual verification/ranking -> story/script -> one continuous narration -> exact-audio timing -> autonomous edit plan -> render -> QA -> exact-artifact human review`

Supported durations: `15 / 30 / 45 / 60` seconds.

Output: vertical `9:16` short-form MP4.

No mandatory paid-per-video API dependency is allowed.

## Human-rejected baseline

First real n8n-orchestrated 60-second proof:

- job: `d23617c3-1311-43c1-97e0-c6504522bd77`;
- topic: `Почему листья меняют цвет осенью`;
- language: `ru`;
- requested duration: `60 s`;
- rendered duration: `59.064 s`;
- technical state: `review_ready`;
- human state: **HUMAN FAIL**.

General defects found:

1. **visual policy defect** — WF04/media-worker was biased toward stock video, producing long/generic moving footage instead of using the much larger relevant still-image inventory;
2. **narration defect** — current WF02 deterministic extractive narration can sound encyclopedic and expose source artifacts instead of producing natural spoken short-form text.

Neither defect may be repaired manually for one topic.

## Photo-first systemic correction

Durable records:

- `docs/V5_N8N_PHOTO_FIRST_MEDIA_POLICY_20260904.md`;
- `docs/V5_N8N_PHOTO_FIRST_PROOF_20260904.md`.

Default visual inventory is now still-image first:

- Pexels Photos;
- Wikimedia Commons / canonical Wikipedia media;
- Pixabay Images;
- additional free/publicly licensed image providers as they are integrated.

Still images are normal production assets and must be turned into dynamic video through purposeful crop/reframe, pan/zoom, detail crops, masks, layouts, callouts, parallax, maps/documents/diagrams or other motion treatment.

Video is optional and secondary. A clip may be selected only when the segment is genuinely motion-led, metadata matches both subject and segment target, local visual ranking says it is more relevant than the best still for that segment, and the selected clip is short (currently max four seconds).

Generic moving footage is a fail.

The first photo-first rerun, job `4f6816b2-38aa-4fe8-8e8d-fbf84a951818`, exposed a general DB schema mismatch: `visual_shots_kind_check` did not allow the new `factual_image` / `context_video` kinds. Migration `017_photo_first_visual_kinds.sql` fixed the shared schema contract.

## Current exact review artifact

Second photo-first n8n rerun:

- job: `8d82fc3e-b8ad-4ac0-8ef5-f61190e3a904`;
- same input: `Почему листья меняют цвет осенью`, `ru`, `60 s`;
- status: `review_ready`;
- rendered duration: `59.064 s`;
- format: 1080x1920, 30 fps, H.264 + AAC;
- exact review copy: `/opt/ai-short-form-content-factory/studio/bakeoff/n8n-photo-first-leaves-ru-60.mp4`;
- SHA256: `0b007fdde0a15994c7df7b1de0d7054fe136755d08c21a6a03f566c3c3e13850`.

Automatic selected-media composition:

- Pexels Photos: 4;
- Pixabay Images: 3;
- Wikimedia Commons images: 3;
- video clips: 0.

No clip/image was manually selected after submission.

Acceptance state: **machine_rendered / review_ready only**. This exact artifact is not `human_approved` until the user watches and explicitly accepts it.

## What counts as a valid proof

A proof starts by supplying only `topic + language + duration` to n8n.

After that there is zero manual creative intervention.

Invalid proof methods include:

- manual clip/image selection;
- manual query rescue for one topic;
- manual scene/edit-plan repair;
- looping/reusing assets to fill duration;
- speech-speed manipulation to force duration;
- bypassing n8n with a handcrafted direct/CLI path;
- calling machine success a product success before explicit HUMAN PASS.

## Immediate gate

1. user watches exact photo-first artifact `n8n-photo-first-leaves-ru-60.mp4`;
2. record HUMAN PASS/FAIL from that exact file;
3. if the visual direction passes, fix the separate general natural-narration defect in WF02 without topic-specific text;
4. rerun the same n8n path and repeat on materially different topics/languages after HUMAN PASS.

Do not create a separate product architecture. n8n remains the orchestrator.

## Topic-resolution HUMAN FAIL and systemic correction

Job `16c23aed-4370-46a4-b135-63f8b6af47c6` (`Ходор / ru / 30`) reached `review_ready` with `fact_primary_title=Mikhail Khodorkovsky` and measured voiceover `28.728 s`. This is HUMAN FAIL: the intended subject was the fictional character Hodor.

Production evidence identified a general WF02 ordering defect: one model guessed a canonical subject without candidates or search evidence, after which research queried only that guess. The resulting evidence set could confirm but never correct the initial mistake.

The corrected WF02 contract is now `candidate interpretations -> per-candidate discovery -> evidence-grounded comparison -> structured resolution -> resolved-subject factual research`. Migration 018 persists the structured result in `jobs.topic_resolution`. Durable record: `docs/V5_EVIDENCE_GROUNDED_TOPIC_RESOLUTION_20260904.md`.

WF03 continuous voice and exact measured-duration fit, WF04 photo-first policy, and WF05 rendering remain unchanged. The correction is not accepted until cross-topic regressions pass, fresh n8n E2E jobs complete where practical, and the user reviews the exact resulting MP4.

## 2026-09-04 systemic rebuild after cross-topic failures

The previous deterministic/extractive WF02 path is no longer the active narration architecture.

Current n8n-controlled narration path:

`topic in any input language -> semantic intent -> SearXNG research -> grounded AI narration strictly in selected output language -> structured validation -> one continuous natural-rate TTS -> exact measured duration -> bounded script rewrite/re-synthesis when needed`

General fixes completed:

- removed lexical/Wikipedia entity matching as the basis of topic understanding;
- removed deterministic encyclopedia-excerpt narration as the primary writer;
- selected output language is authoritative and independent of input-topic language;
- research evidence supports/audits narration instead of being concatenated into narration;
- exact TTS duration is authoritative; word-count duration prediction is advisory only;
- natural speech rate remains unchanged; timing is corrected by rewriting the script, not tempo manipulation;
- Edge Read Aloud transport budget was increased to a bounded 120-240 seconds and the n8n HTTP timeout aligned to 270 seconds;
- WF02 structured-output parsing now safely tolerates the model's bounded `used_source_ids: [S1,S2]` formatting defect without evaluating arbitrary text;
- visual candidate identity is provider-scoped (`provider + provider_asset_id`) across Pexels/Pixabay/Wikimedia-style inventories, preventing cross-provider numeric-ID collisions;
- photo-first policy remains mandatory; video remains secondary and is admitted only for motion-led, semantically stronger matches.

Latest autonomous end-to-end evidence, all launched only with `topic + language + duration`:

1. job `1bf8089f-eecf-4b93-83f4-a1a5862a4044`
   - topic input: `why is the sky blue`
   - selected output language: `ru`
   - requested: `30 s`
   - measured voiceover: `27.360 s`
   - status: `review_ready`
   - final MP4: `jobs/1bf8089f-eecf-4b93-83f4-a1a5862a4044/render/final.mp4`

2. job `6cf62378-51be-4694-9e4e-5f096a7f1769`
   - topic input: `how does a refrigerator work`
   - selected output language: `uk`
   - requested: `30 s`
   - measured voiceover: `31.152 s`
   - status: `review_ready`

3. job `656656f1-5f75-4a8e-a5ef-bf8bd1608e16`
   - topic input: `почему извергаются вулканы`
   - selected output language: `pl`
   - requested: `30 s`
   - measured voiceover: `29.160 s`
   - status: `review_ready`
   - final MP4: `jobs/656656f1-5f75-4a8e-a5ef-bf8bd1608e16/render/final.mp4`

These are machine-rendered cross-topic proofs only. None is `human_approved` until the user watches the exact artifact and explicitly accepts it.

## Current gate

The user should now test the current workflow from Studio with arbitrary topics/languages/durations. Any HUMAN FAIL must be handled as a general defect from the exact artifact; no topic-specific rescue or manual media selection is allowed.

## Regression gate

Static workflow regression suite: `10/10 PASS` after the systemic WF02/WF03/WF04 rebuild.

The suite covers cross-language semantic intake, selected output-language authority, grounded research-backed narration, advisory-only word budgeting, exact measured TTS duration, bounded natural-rate rewrite/re-synthesis, provider transport budget, short canonical titles, provider-scoped visual identity, and local media-worker module completeness. Node syntax checks also pass for the media-worker entry point and new support modules.

## Evidence-grounded topic-resolution production result

Fresh production regression after migration 018 and the WF02-only deployment resolved all seven required/diverse classes correctly and produced scripts in the selected output languages. Five jobs reached `review_ready`; Hodor and volcano were correctly rejected later by unchanged WF04 relevance/assignment gates. Topic resolution is machine-proven cross-topic; rendered files still require HUMAN PASS/FAIL.

The exact job matrix, consumed failures, decision contract, and deployment corrections are recorded in `docs/V5_EVIDENCE_GROUNDED_TOPIC_RESOLUTION_20260904.md`.

## 2026-09-05 visual relevance HUMAN FAIL

The user rejected all five topic-resolution `review_ready` MP4s. They are HUMAN FAIL, not quality proof. Inspection showed the runs were already image-first; the defect was acceptance of irrelevant images through metadata bonuses despite near-zero local visual scores, compounded by mixed-language visual queries because WF02's English visual concepts were not persisted.

Migration 019 and the WF02/WF04/media-worker correction persist and consume grounded English visual queries, rank against a concise English subject/target, reject sub-floor semantic matches before metadata utility, and keep video secondary to an eligible still. Missing relevant media must fail closed. Durable record: `docs/V5_PHOTO_RELEVANCE_HUMAN_FAIL_20260905.md`.

The correction is deployed. Fresh autonomous job
`e3d9016d-cefc-4158-aeca-075dab852c41` (`как работает холодильник`, `ru`, `30`)
failed closed at visual segment 6 because no candidate exceeded the `0.01`
semantic relevance floor. It produced no `visual_shots` and no MP4. This proves the
deployed gate blocks unrelated filler; it does not yet prove sufficient relevant-
photo coverage or human-acceptable output.

## 2026-09-05 visual selector rollback decision

The lexical-metadata plus local SigLIP selector is rejected as a production visual
quality authority. The exact Hodor render selected a random door, snow, an insect
micrograph, an unrelated portrait, and a scientific figure. Five of eight selected
shots had `target_metadata_overlap=0`; metadata utility overrode near-zero visual
scores. Subsequent absolute-threshold calibration alternated between irrelevant
media and incomplete jobs and is not a viable product mechanism.

WF01 intake is paused while WF04 is replaced by multimodal review of the actual
candidate previews. The local ranker may remain only for perceptual hashes and
ordering; it must not independently approve semantic relevance. Production intake
must not resume until the exact rendered MP4 is watched before delivery.


## 2026-09-05 final-narration visual rebind + bounded model recovery

Fresh production matrix after deploying WF02 commit c6a14a7:

- 4174878b-4662-433d-9ff2-ff090cf77ac5 — как работает гидроэлектростанция, ru, 15 s — WF03 failed during the second duration-fit rewrite;
- 4c864c59-20bf-41fe-b562-b20f5c3571a2 — How Alexander Fleming discovered penicillin, pl, 30 s — reached review_ready, measured voiceover 29.712 s;
- 75a41742-0e38-48c4-a9fb-d8f4320c89f6 — как образуются облака и дождь, uk, 60 s — WF03 failed during the first duration-fit rewrite.

Execution inspection proved the apparent duration rewrite model returned invalid JSON failure was masking upstream Gemini free-tier HTTP 429 responses. The model gateway had no bounded recovery and WF03 received an empty object after the child workflow failed. This is a general provider-availability defect, not a topic-specific script defect.

A second systemic defect was also proven: c6a14a7 correctly binds visual queries to the final WF02 validator narration, but WF03 may still rewrite narration after exact TTS measurement. Therefore any job with script_fit_passes > 0 can otherwise carry stale visual queries into WF04 even though they were valid for the pre-TTS script.

Current correction under test:

- V4 model gateway has one bounded retry (maxTries=2, waitBetweenTries=60000) and remains time-limited;
- callers that use the gateway have bounded timeouts long enough to accommodate that single retry;
- if a duration-fit model call remains unavailable and the narration is too long, WF03 can make a deterministic punctuation-boundary shortening from the already-grounded narration while preserving evidence provenance; no speech-speed manipulation is introduced;
- after exact TTS is accepted, any job whose narration changed in WF03 must regenerate exactly 6/10/14/18 English visual queries from the actual final timed narration beats, then persist those queries before WF04 starts;
- jobs with script_fit_passes = 0 keep the c6a14a7 validator-bound visual query inventory and do not spend an extra model call.

Regression coverage added for bounded model recovery, deterministic duration fallback, and final-narration visual rebinding. Production deployment is not allowed until the complete regression suite passes, changes are committed and pushed, then the exact new MP4s are inspected.

## 2026-09-05 production HUMAN FAIL: spoken slash + unreviewed visual fallback

Fresh production jobs after commit `3af1b99c2ccaf131920cb664f8ee0ab6215dc182` exposed two additional general defects.

1. Job `043c10a6-4d9d-4948-bc0d-64237429e749` (`как работает гидроэлектростанция`, `ru`, `15`) reached `review_ready`, but the persisted narration contained literal formatting separators such as `? /`, `, /` and ` / ` between words. The TTS therefore audibly pronounced the slash. The defect is not provider-specific: unsafe formatting was allowed to enter the spoken narration contract before TTS.

2. The same hydro render and job `cc1141d8-03a3-4825-ac96-281812737a7a` (`How Alexander Fleming discovered penicillin`, `pl`, `30`) showed apparently random second images inside semantic segments. Execution evidence proved the multimodal reviewer normally approved one visibly relevant candidate per segment while each segment requested two shots. `Require Multimodal Visual Selection` then appended `localFallback` candidates that the multimodal reviewer had not approved; because `visual_review_candidates` retained the full local pool, some fallback candidates had not even been shown to the reviewer. Examples include a multimeter for a hydroelectric generator beat and a newsroom/typewriter photo for an Alexander Fleming laboratory beat. This violated the requirement that each displayed image be specifically approved for the current narration.

Systemic correction now under regression:

- WF02 final narration removes whitespace-delimited formatting separators (`/`, `|`, arrows) before persistence and both writing/validation prompts explicitly forbid them in spoken prose;
- WF03 fails closed if unsafe spoken separators somehow reach TTS, and duration rewrites apply the same speech-safe normalization before rebuilding support provenance;
- WF04 exposes only candidates actually shown to the multimodal reviewer as eligible candidates;
- WF04 requires at least `planned_shot_count` model-approved images for every segment and forbids the previous unreviewed `localFallback` path;
- if the reviewer cannot approve enough relevant images, the segment now fails closed instead of silently filling the timeline with plausible/random media.

Regression status before GitHub sync/deploy: `20/20` Node tests + `11/11` Python tests PASS, JSON validation PASS, `git diff --check` PASS. Production has not yet been redeployed with this correction. Existing `review_ready` artifacts above remain HUMAN FAIL.

## 2026-09-05 exact-beat visual sourcing correction under final verification

Fresh production evidence from job `fd510f8e-21b3-4f2d-a992-2cc5f21e81a0` proved two independent general defects.

1. Narration formatting leakage: the model had emitted `/` as a visual/beat separator inside spoken Russian text and WF02 persisted it unchanged. TTS therefore literally pronounced the slash. The deployed speech-safety correction removes and rejects standalone slash/pipe-style formatting separators before TTS and after duration rewrites. The fresh 15 s rerun produced clean narration with no slash and measured `14.256 s`.
2. Timed visual discovery was not actually beat-authoritative. For a final beat whose exact query was `modern residential house exterior at night with glowing interior lights`, the media worker prefixed the canonical topic, producing an overlong provider query; Pixabay returned HTTP 400. The timed candidate pool then still contained generic topic-level hydroelectric imagery, which allowed topic-context pictures to be selected for a homes/electricity beat. In addition, semantic visual segmentation could merge multiple final narration beats and attach only the first beat query to the merged segment.

The new systemic correction keeps the final timed narration as the only visual chronology authority:

- one visual segment per accepted final narration beat (`narration-beat-visual-segments-v4`);
- query N binds one-to-one to final beat N;
- each beat >= 1.8 s plans two distinct full-screen stills, preserving the multiple-image-per-scene contract;
- timed searches use the exact English beat query without prefixing the overall topic;
- provider query length is bounded before transport;
- timed candidate pools do not mix generic topic-level Pixabay/Pexels/Commons stock or canonical-article media;
- Pexels uses the Photos API, not stock-video search;
- Commons, Pixabay and Pexels requests run concurrently per beat, with bounded concurrency across beats and existing per-provider timeouts;
- final multimodal review may select only images actually shown for that exact beat; topic anchors and unreviewed local fallback are forbidden; insufficient visible matches fail closed.

Regression coverage is updated and a new real-path discovery regression covers exact beat queries, provider query bounds, Pexels Photos, no topic-level timed stock and bounded concurrency.

Real-provider dry-run against the exact failed 60 s cloud/rain context (`18` final beats / `18` queries) completed in `5.726 s`, returned `18` beat-aligned visual segments / `36` planned still shots, and reported `0` provider errors. Every segment used its exact final beat query; topic-level base provider counts were all zero. This is discovery evidence only, not HUMAN PASS. The correction still requires GitHub sync, production deploy, fresh E2E renders and exact MP4 review.

### 2026-09-05 bounded multimodal review batching correction under test

Fresh post-deploy E2E matrix after exact-beat visual discovery exposed a separate bounded-review defect:

- `8dbc666c-3d00-4cfb-a15b-f168a6313895` — hydroelectric plant / ru / 15 — `review_ready`, measured voice `13.824 s`;
- `81394bf5-b345-4565-82a4-13d4cc16dd76` — Alexander Fleming / pl / 30 — failed because segment 1 received only `1/2` model-approved relevant stills;
- `4278786c-a243-4e0e-a37e-d3e2226b8434` — clouds/rain / uk / 60 — failed before review because the single multimodal request exceeded its bounded 80-item input budget.

The failures have one general cause: one whole-video multimodal request forced candidate exposure per segment to shrink as beat count grew, and at 18 beats the fixed lower bound of two candidates per segment made the request mathematically exceed the 80-item cap. The 30 s case was also starved to only three reviewed alternatives per beat, so failing closed after one relevant choice was expected even though more exact-query candidates existed upstream.

Correction under test: split final visual review into deterministic batches of at most six exact narration beats. A six-beat batch can show up to six actual still candidates per beat and remain within the 80-item request cap; smaller batches expose up to 7-10 candidates per beat. The model may approve up to four visibly exact candidates per beat, never fewer than the required shot count when enough exact matches exist. All approved alternatives remain model-reviewed and the global assignment still forbids asset reuse. No topic-level or unreviewed fallback is reintroduced.

Static Node regression now proves 18 beats => exactly three bounded review batches, complete segment coverage, <=80 inputs per model call, multi-batch response reconstruction, fail-closed behavior, and global no-repeat assignment compatibility. Production deployment remains blocked until the full regression suite, GitHub sync, and fresh E2E reruns pass.

### 2026-09-05 bounded visual-query recovery + measured duration controller under test

Fresh production matrix after `820fcb4d78ebb060fb4d938ab40d51661debb5f6` exposed two separate systemic gaps rather than a reason to weaken relevance gates:

- `3a4f8483-03b5-47a3-81dd-8844445157aa` (`How Alexander Fleming discovered penicillin`, `pl`, `30`) failed closed because exact stock search for `Alexander Fleming historical portrait` produced same-name but wrong entities; the actual-image reviewer correctly approved `0/2` for beat 1.
- `310f8fae-2d74-4f54-871e-f1375fa71ea1` (`как образуются облака и дождь`, `uk`, `60`) failed closed on beat 18 because `water cycle diagram showing evaporation condensation and precipitation` produced mostly generic rain/condensation photos instead of an explanatory water-cycle diagram.
- `c7cf63b2-3712-4c36-b375-613ad97aa8a2` (`как работает гидроэлектростанция`, `ru`, `15`) measured `20.808 s -> 11.568 s -> 13.272 s`; the final result missed the accepted lower bound by `0.195 s` and the old controller failed immediately after two rewrites.

Systemic correction now under regression/GitHub gate:

- timed visual discovery still searches the exact final-beat query first;
- when exact provider results do not supply enough query-anchored candidates, discovery may issue exactly one compact recovery query that preserves the named entity/mechanism and media cue; it may not fall back to the overall video topic;
- the recovery path remains bounded to the same free providers/timeouts and all recovered images still require actual-image multimodal approval;
- real provider evidence for the failed classes now exposes correct Wikimedia candidates such as Alexander Fleming portraits and water-cycle diagrams instead of accepting same-name stock noise;
- WF03 now preserves bounded measured TTS history and allows at most three rewrites;
- when measured attempts bracket the target duration, the next requested word count is computed by interpolation between the closest measured under-target and over-target attempts instead of another blind proportional jump;
- exact TTS measurement remains authoritative and speech rate remains unchanged;
- migration `021_expand_script_fit_pass_limit_to_three.sql` raises only the bounded persistence limit from two to three rewrites.

Current static regression gate: `23/23` Node + `11/11` Python PASS, workflow JSON PASS, `git diff --check` PASS. A real-provider discovery/rank dry-run on the failed 30 s and 60 s contexts also passes with 10 ranked candidates available per exact beat. These are engineering proofs only. GitHub sync, migration/deploy, fresh autonomous 15/30/60 renders, and exact MP4 review are still required.

### 2026-09-05 post-b6f299 production failures and bounded correction

Fresh autonomous production matrix on `b6f299ed1af3d9e7a39bb4dedfb9efa3f2681f81` exposed two remaining general defects:

- `4183cb81-c918-41a8-80ef-b68df92053d2` — hydroelectric plant / `ru` / `15`: WF03 measured `21.168 -> 13.248 -> 13.104 -> 12.816 s` and failed after the bounded third rewrite. The accepted lower floor is `13.467 s`; several attempts missed it by only fractions of a second.
- `b338430e-b371-4ca2-a1ce-0076641aa1f6` — Fleming / `pl` / `30`: after `39.336 -> 26.856 s`, the next duration-rewrite model call was unavailable. The current result was only `0.111 s` below the accepted lower floor `26.967 s`, but deterministic textual expansion is intentionally not used when the model is unavailable.
- `721b1fbc-226c-499c-95e1-d434dcddf13c` — clouds/rain / `uk` / `60`: voiceover passed at `58.656 s`; WF04 failed closed on beat 16. Execution evidence showed the multimodal model could identify correct `Water Cycle` diagrams, but the bounded pre-review exposure pool had shown it unrelated `cycle` matches instead because correct phrase-level candidates were displaced before review.

Systemic correction now under GitHub/deploy gate:

- normalized continuous voice audio may add only a bounded natural end pause, max `0.4 s`, and only when the measured narration is already within `0.4 s` below the accepted lower duration floor; speech rate/tempo remain unchanged and materially short narration still goes through rewrite/fail;
- both Gemini-stored and Edge-fallback continuous audio use the same bounded tail-normalization helper;
- compact visual recovery canonicalizes media cues such as `schematic` to `diagram`, so a target such as `schematic diagram of the global water cycle` reduces to a subject-preserving query such as `water cycle diagram`, never to the overall video topic;
- WF04 bounded exposure now prioritizes exact subject/target phrase matches before multimodal review, so correct candidates are not displaced by lexical coincidences such as unrelated uses of `cycle`;
- the actual-image reviewer remains authoritative and fail-closed; no unreviewed fallback or weakened relevance gate is reintroduced.

Verification before commit: `25/25` static Node tests + `11/11` Python tests PASS, workflow JSON PASS, `git diff --check` PASS. A real-provider discovery/rank dry-run on the previously failed Fleming and cloud/rain contexts also passes with `10` ranked candidates per beat and no provider errors. Production deployment and fresh autonomous 15/30/60 MP4 review are still required.

### 2026-09-05 production rank-timeout root cause + fingerprint-only correction

Fresh autonomous production matrix on commit `706d5badf7279010973506ef4705c4331e7cb715` reached exact-duration voiceover but all three jobs failed in WF04 before render:

- `f94e5fd5-1b6f-4551-8a38-c0f25d745853` — transformer / ru / 15 — voice `16.392 s`; rank segment 1 timed out;
- `d0cfdc93-508b-4490-a84f-c7ba25f735f6` — Marie Curie / pl / 30 — voice `29.808 s`; rank segments 4,6,7,8,9 timed out;
- `592c44ea-64d9-44c7-9bb0-347b21de05f2` — aurora / uk / 60 — voice `60.288 s`; rank segments 9,13,14,18 timed out.

Execution inspection proved the final `received=... expected=...` messages were secondary. `Rank Eligible Visuals` sent one HTTP request per exact beat while the media worker serialized every SigLIP inference behind one global promise chain. Later requests waited behind earlier segments until n8n's 120 s HTTP timeout. `Attach Rank Results` then routed failed items to its error output while successful items continued, so the main branch silently lost segments and only failed later with an incomplete timeline.

Systemic correction under test:

- local SigLIP is removed from the critical WF04 rank path; it had already been rejected as semantic relevance authority and is no longer needed there;
- `/visual/rank` now performs only bounded preview retrieval + perceptual hashing, preserving the planner's deterministic candidate order; actual-image multimodal review remains the sole semantic approval authority;
- preview transport has a maximum of two attempts for transient 429/5xx/transport failures, six global fetch slots, and the existing 10 s per-attempt timeout;
- WF04 preserves expected segment cardinality on every fingerprint item and turns any remaining fingerprint failure into one explicit pre-review failure instead of silently dropping that beat;
- the rank HTTP node itself has at most two attempts; there is no unbounded retry loop;
- selection provenance is renamed to `multimodal_exact_beat_shot_beam_v4`;
- the repository media-worker Docker/package build contract is synchronized with the actual production runtime so a GitHub checkout can build the worker reproducibly.

Real stress proof against the exact latest 15/30/60 contexts: discovery produced `6 + 10 + 18 = 34` exact-beat fingerprint requests. All 34 were fired concurrently at the patched worker and completed in `13.228 s` total; the slowest single request was `13.218 s`, all returned at least one fingerprinted candidate, and no request approached the 120 s n8n transport bound. This is engineering evidence only; fresh production E2E MP4s and exact-artifact review remain required.


### 2026-09-06 hosted provider failover + global no-repeat recovery under GitHub gate

Fresh runtime inspection after rollback HEAD `8ed8a080f8feacedc57c351f0b127d4847045b7b` reconfirmed that production contains only PostgreSQL, n8n and media-worker; there is no Ollama/model-worker runtime. The active V4 model gateway and WF04 runtime exports were semantically equal to the GitHub HEAD before this correction.

Production DB also reconfirmed the two independent blockers:

- `a1155771-4a8d-4a6d-8739-806ef557340c` and `fb1267de-a814-4dd7-b4e5-b0690c6e54b7` failed because the final visual-rebind model was unavailable;
- `7a9151e5-7064-49db-80dc-43e2ad1d8e79` reached a complete 18-beat visual review but global all-unique assignment failed at the final shot.

Hosted-provider research and live VPS probes show that Kilo Gateway free models are zero-cost but limited to 200 free requests/hour/IP, and individual upstream free routes can still return their own 429/503 capacity failures. `kilo-auto/free` is text-only in the current model catalog, so it cannot replace the required multimodal path. `stepfun/step-3.7-flash:free` currently advertises `text+image -> text` and has returned successful anonymous text and real-image responses from the VPS, but also exhibited intermittent upstream capacity failures. Therefore it is not accepted as a sole production provider.

Systemic provider correction now under GitHub gate:

- V4 Model Gateway keeps the existing n8n webhook contract;
- anonymous Kilo `stepfun/step-3.7-flash:free` is the first zero-cost text+vision provider;
- Kilo failure, empty output or upstream capacity failure falls through immediately to the existing independent Gemini provider;
- the previous 60-second sleep/retry behavior was removed; each provider attempt is time-bounded and the provider chain is finite;
- provider provenance/attempts are returned with the normalized result;
- no Ollama, model-worker, Mac model server or local LLM dependency is introduced.

Systemic WF04 correction now under GitHub gate:

- after actual-image review, a deterministic bipartite feasibility check detects whether globally unique perceptual-cluster assignment is possible before the final beam assignment;
- only beats in the proven conflicting component enter recovery;
- each conflicting beat receives exactly one additional exact-target provider search;
- every candidate already considered in the first actual-image review is excluded from that search;
- new candidates are perceptually fingerprinted, then their real images are shown to the same multimodal reviewer;
- only newly reviewer-approved candidates are merged into the approved pool;
- the existing global all-unique assignment is then attempted once more; if it is still impossible, WF04 fails closed;
- no image/cluster reuse, unreviewed fallback, topic-level rescue, or SigLIP semantic authority is reintroduced.

Verification before commit: workflow JSON parse PASS; Python regressions `11/11` PASS; static Node regressions `30/30` PASS including new exact conflict-search and global no-repeat recovery tests; `git diff --check` PASS; no tracked `work/`; modified runtime/workflow code contains no Ollama/model-worker dependency; media-worker builds reproducibly from this checkout; both modified workflows import successfully into a clean n8n `2.33.3` instance. The isolated built media-worker exposes `/visual/recover-conflict`; a real Wikimedia exact-target request for `Alexander Fleming portrait` returned 18 new candidates while keeping semantic approval outside discovery. Production deploy and fresh autonomous 15/30/60 E2E renders remain blocked until commit/push and GitHub-source verification complete.


### 2026-09-06 WF01 GitHub/runtime orchestration drift correction

Pre-E2E reconciliation found a pre-existing source/runtime drift in WF01. The active production WF01 and production filesystem both contain the same seven-node orchestration core: after the job row is inserted, `Start Script Planning` asynchronously invokes WF02 `TJfA4ZYUEKSTad6k` with only the persisted `job_id`, while the webhook returns HTTP 201 without waiting for the full generation chain. Their canonical core SHA is `065a372f16e865e502769d8bf0c344a5ad29cba1c29378bd406cbddee8239c3f`.

GitHub commit `a8ab5f2c984a517e9176b29dcc4bb101270355f9` still carried an older six-node WF01 core (`20d83db99524ea97550311095430c3746eee89fbe536c521b7ec4db777c73477`) that inserted and returned the job but did not invoke WF02. That GitHub file cannot represent the required autonomous `topic + language + duration` product path even though runtime had the correct handoff.

Correction under GitHub gate: synchronize the already-live generic WF01 orchestration contract into repository source and add a regression requiring exactly one asynchronous WF01 -> WF02 handoff with `job_id`. This is source/runtime reconciliation, not a topic-specific behavior change. Fresh E2E remains blocked until the corrected WF01 is committed, GitHub tree is verified, and production WF01 is republished from that GitHub source.


### 2026-09-06 fresh E2E provider completion-contract failure

After GitHub commit `a5bafcd96f69936f51439b0298c23dfc9705874e` restored WF01 source/runtime orchestration and WF01 was republished from that exact GitHub tree, fresh autonomous production testing resumed strictly through the WF01 `topic + language + duration` webhook.

Fresh RU/15 transformer job `a8ebade0-9657-46d5-9bfd-449ebfd6a7a9` completed autonomously to `review_ready`. Exact voiceover duration is 15.504 s. WF04 stored `visual_quality.pass=true` with 12 shots, 12 unique assets, 12 unique perceptual clusters, zero asset reuse and zero adjacent perceptual duplicates. WF05 rendered `jobs/a8ebade0-9657-46d5-9bfd-449ebfd6a7a9/render/final.mp4`; technical probe is H.264 + AAC, 1080x1920, 30 fps, 15.534 s, SHA256 `81d8b4134290ba888c80079f3e3a22cdb423b9efac71d4eacea01037f9566402`. This is machine completion only, not HUMAN PASS.

Fresh PL/30 Marie Curie/radium job `c2a91275-bf29-43c0-95f6-b0f2eeb9694d` exposed a new general provider-contract defect and failed closed at `script`: `evidence-grounded topic resolver returned invalid JSON [line 1]`. WF02 execution `15582` failed after V4 executions `15583` and `15584` were marked success. Exact execution-data inspection proved V4/Kilo execution `15584` returned `finish_reason=length`; `message.content` contained only an approximately 421-character prefix of the requested JSON while the model emitted a long reasoning payload. V4 incorrectly treated any non-empty Kilo content as success, so Gemini fallback was skipped and WF02 received truncated JSON.

Systemic correction under GitHub gate: Kilo output is usable only when text is non-empty and `finish_reason` is exactly `stop`. `length`, `content_filter`, tool-call or missing/nonterminal completion reasons are normalized as failed provider attempts and immediately use the existing independent Gemini fallback. The failed PL/30 job is not retried manually; a completely fresh job may be created only after this gateway correction passes regression/import/GitHub/deploy gates.


### 2026-09-06 fresh PL/30 reviewer-shortfall recovery gap

After V4 commit `c0492f97627d0d894276bebc1f14a018277d281e` was verified live (`active=true`, `versionId == activeVersionId`, and live/source canonical workflow SHA `ca2c17e99aabe2d4466f5f53952f551aa51e88e04951088e19216f72242ffe41`), fresh PL/30 job `ed6a58bb-f4a6-4dc8-a545-35c8795743d2` demonstrated the completion-contract correction on real production traffic. V4 execution `15588` received Kilo `finish_reason=length`, normalized the Kilo attempt as unsuccessful, then used Gemini successfully and returned complete valid resolver JSON. WF02 and WF03 subsequently advanced normally; exact voiceover duration reached 32.064 s.

The same fresh job then exposed a separate general WF04 defect and failed closed at visuals: `Multimodal reviewer approved 1/2 relevant images for segment 5; unreviewed fallback is forbidden`. Execution `15596` showed that the exact beat required two reviewed stills for `pure radium chloride crystals in glass vial`, while the first inventory mostly contained generic crystal/mineral representations. The reviewer correctly refused to pad the beat.

Source inspection identified the architectural gap: `Require Multimodal Visual Selection` threw immediately on any per-segment approved-count shortfall, while the existing single exact-target recovery path was reachable only after `Detect Global No-Repeat Conflict`. Therefore a segment with insufficient exact reviewer-approved images could never use the same bounded recovery already available for global uniqueness conflicts.

Systemic correction now under GitHub gate: initial multimodal review preserves only reviewer-approved candidates and records approved-count shortfall instead of admitting any fallback. Malformed or empty reviewer output remains an immediate failure. The global feasibility detector adds shortfall segments, including zero-approved pools, to the same bounded recovery set used for perceptual-cluster conflicts. Each affected segment receives one additional exact-target search excluding every candidate already shown to the reviewer; only newly fingerprinted and reviewer-approved candidates can be merged. After that one recovery round, merged reviewer-approved cardinality must meet `planned_shot_count` or WF04 fails closed. No shot-count relaxation, relevance-threshold relaxation, topic-specific query, asset reuse, unreviewed fallback, or second recovery round is introduced.

Targeted verification before the full gate: `WF04_PHOTO_RELEVANCE_GATE_REGRESSION_PASS`, `WF04_GLOBAL_NO_REPEAT_RECOVERY_REGRESSION_PASS`, and `VISUAL_CONFLICT_RECOVERY_EXACT_QUERY_REGRESSION_PASS`.

Full verification for this correction: workflow JSON parse PASS; Python regressions `11/11` PASS; Node static regressions `31/31` PASS; `git diff --check` PASS; clean n8n `2.33.3` import of WF04 PASS.

### 2026-09-06 PL/30 recovery proof + UK/60 structured-output failure

WF04 shortfall recovery was deployed from GitHub commit `5d0398b65d6c63764f24a9441c5785c190753b50` after immutable source verification. Production live/source canonical WF04 core SHA is `f8fe6b76bf92213d136ead92f2f40779fc6a25e1fc592e968e04eb968e454eef`; live workflow has 42 nodes and `active=true` with `versionId=activeVersionId=379a5d0e-b955-444e-8951-1f3297915bc8`.

Fresh PL/30 job `d278b778-4aea-468d-b78e-aa03e994fd46` (`How Marie Curie discovered radium`, `pl`, `30`) was created by one WF01 intake and completed autonomously to `review_ready`. Exact voiceover duration is 26.983 s. The original failure class reproduced on segment 4: initial multimodal review returned `visual_review_approved_count=1` for `visual_review_required_count=2`, so `visual_review_shortfall=true`. The new single recovery round then added four newly reviewer-approved exact-target candidates; the same segment finished with approved count 5, `visual_review_shortfall=false`, `visual_recovery_used=true`, and `global_conflict_recovery_attempted=true`. WF04 stored `visual_quality.pass=true` with 20 shots, 20 unique assets, 20 unique perceptual clusters and zero reuse. WF05 rendered `jobs/d278b778-4aea-468d-b78e-aa03e994fd46/render/final.mp4`; technical probe is H.264 + AAC, 1080x1920, 30 fps, 27.000 s, SHA256 `e6dae140d636d0d57c49d4fd90a6d4ba14f60909576bd487085d6d226ff2558c`. This is machine completion only, not HUMAN PASS.

Fresh UK/60 job `ff7c0237-dc9f-4709-bf16-5d2e69201852` (`как образуется северное сияние`, `uk`, `60`) was then created through WF01. WF02 and WF03 passed automatically; final continuous voiceover duration is 60.480 s with one script-fit pass and no speech-speed manipulation. WF04 execution `15665` failed closed at recovery review with `Global conflict recovery reviewer returned invalid JSON for batch 1 [line 3]`.

Exact V4 execution `15669` proved this is a separate structured-output contract defect. Kilo returned `finish_reason=length` and was correctly normalized as unsuccessful. Gemini fallback returned `status=completed` and was incorrectly marked provider success because the gateway only checked for non-empty text. The 1456-character Gemini response was syntactically invalid JSON: after the first segment object it emitted the next `segment_number` before closing the previous object. Therefore the transport/provider layer succeeded while the structured-content contract did not.

Systemic correction now under GitHub gate: V4 accepts an opt-in `response_format: "json"` plus `response_schema`. For structured calls, Kilo receives OpenAI-compatible `response_format: {type: "json_object"}` and Gemini Interactions receives `response_format: {type: "text", mime_type: "application/json", schema: ...}`. Both provider normalizers now require syntactically valid JSON whenever `expects_json=true`; malformed Kilo `stop` output falls through to Gemini, while malformed/incomplete Gemini output becomes provider-exhausted instead of usable text. Both WF04 actual-image reviewer calls — initial and recovery — send the same reviewer JSON schema. Semantic validation of segment numbers and candidate IDs remains in WF04. No JSON repair parser, retry loop, relevance weakening, shot-count relaxation or topic-specific exception is introduced.

Verification for this correction before commit: targeted structured-output and existing provider-failover regressions PASS; workflow JSON parse PASS; Python regressions `11/11` PASS; Node static regressions `32/32` PASS; `git diff --check` PASS; clean n8n `2.33.3` imports of both V4 Model Gateway and WF04 PASS. Production deploy and a completely fresh UK/60 E2E remain blocked until commit/push and GitHub tree verification complete.

### 2026-09-06 UK/60 reviewer payload overload correction

After structured-output commit `2e649032bab9a68cc1b3784cfd58dc80f3735230` was deployed, fresh autonomous UK/60 job `0a0eae4e-76d5-44b7-b929-2f1878bf2ce5` (`как образуется северное сияние`, `uk`, `60`) was created through one WF01 intake. WF02 and WF03 passed automatically. Final continuous voiceover duration is 55.728 s with one script-fit pass and no speech-speed manipulation. WF04 then failed closed on initial multimodal review batch 3 with `Multimodal visual reviewer unavailable for batch 3 [line 5]`.

Exact V4 execution `15740` proved the structured-output contract itself was working: `expects_json=true`; Kilo received `response_format: {type: "json_object"}` and Gemini received `mime_type: "application/json"` with the reviewer schema. Kilo returned `finish_reason=length` and was correctly rejected. Gemini then hit the existing bounded 90 s provider timeout, so V4 normalized the full provider chain as `provider_exhausted=true` instead of returning malformed text.

The overload is general and measurable. Initial visual-review executions `15738`, `15739`, and `15740` each carried 36 inlined images plus 43 text items. Batches 1 and 2 completed through Gemini; batch 3 timed out. The 36-image exposure came from six segments per batch times six candidates per segment even though the reviewer output contract permits at most four approved IDs per segment and production visual segments require only one or two shots.

Systemic correction now under GitHub gate: both initial and recovery review preparation cap exposure at four candidate images per segment while preserving the existing six-segment batch size, exact-target candidate ordering, actual-image review authority, one-shot recovery and fail-closed semantics. A six-segment reviewer batch is therefore bounded to at most 24 images / 55 total input items instead of 36 images / 79 items. Because durable `planned_shot_count` is restricted to 1..2, four reviewed alternatives retain at least 2x candidate slack per required shot; no shot-count relaxation, provider timeout increase, retry loop, topic-specific query or unreviewed fallback is introduced.

Verification before commit: initial-review and recovery-review exposure regressions PASS; Python regressions `11/11` PASS; Node static regressions `32/32` PASS; workflow JSON parse PASS; `git diff --check` PASS; clean n8n `2.33.3` import of WF04 PASS. Production deploy and a completely fresh UK/60 E2E remain blocked until commit/push and GitHub tree verification complete.

### 2026-09-06 global visual-semantic gate correction

A cross-topic production audit proved that the remaining visual failures were not isolated topic problems and that prior `review_ready` machine states were not sufficient evidence of visual correctness. Fresh job `4894fe3a-3626-4870-8112-6d1ec0032303` (`как возникла жизнь на земле?`, `uk`, `30`) failed closed at `No valid semantic visual shot assignment at shot 18/20`. Exact WF04 execution data showed that every segment had enough nominally model-approved candidates after recovery, but the approved pools still contained semantically wrong or overlapping assets, so the global unique assignment failure was downstream evidence rather than the primary defect.

The same cross-topic audit found false machine approvals in materially different successful/failed runs. Examples include a Cyprus school building approved for an early nuclear-physics laboratory beat in the Marie Curie job, steel wire approved as a copper transformer winding, DNA/blood-cell imagery approved for early-Earth/abiogenesis beats, generic molecules approved as self-replicating RNA, and a membrane/proton-gradient diagram approved for a hydrothermal-vent photography target. The fresh `4894fe3a...` job itself had correctly aligned narration-to-`visual_target` values, so the current root cause is below target generation.

Two general defects were verified in source. First, `candidateMatchesQueryAnchor()` previously allowed a long target to be represented by the first few weak semantic words; temporal/generic terms such as `early`, `20th`, `century`, `scientific`, `concept`, `equipment` could therefore admit unrelated stock. The bounded conflict-recovery function also returned newly searched candidates without the same target-anchor gate. Second, the multimodal reviewer was asked to select provider IDs directly after seeing filename/ID labels, so it could be biased by lexical cues and could hallucinate target content that was not present in the pixels.

Systemic correction in the current clean checkout: initial discovery and conflict recovery now use the same stronger target-anchor model. Media/low-signal words are removed from anchor keys; long targets require at least three grounded anchor hits; each candidate carries explicit target-anchor metrics; recovery filters candidates before reviewer exposure; canonical-article media can remain available only under the existing provenance path and is still subject to the final actual-image gate. WF04 now hides real provider IDs/filenames from the vision model and exposes opaque `review_id` values only. The model must return one candidate-by-candidate verdict with `relevant` plus a short `visible_description`. Deterministic code then requires both target eligibility and consistency between the model's visible description and the provider's real metadata before an asset can enter the approved pool. The identical contract is applied to initial and recovery review. Unreviewed fallback, relevance weakening and asset reuse remain forbidden.

A separate user-requested global editorial adjustment reduces photo-cut intensity without changing color or adding a renderer-specific trick. Ordinary images have no saturation/brightness/zoom treatment in the current renderer; the high perceived intensity came from shot cadence. The shared shot-count rule now uses the existing 3.2 s support-change boundary: normal shorter beats keep one still, and only beats at least 3.2 s receive a second still. The rule is centralized through `plannedShotCountForDuration()` and used by both segmentation and beat-aligned discovery. This is an editorial cadence change, not an assignment bypass; every planned shot must still use a unique reviewer-grounded asset and perceptual cluster.

Verification for this correction before commit: targeted semantic-anchor/discovery/recovery/reviewer regressions PASS; Node static regressions `33/33` PASS with the real-provider integration dry-run intentionally excluded; Python regressions `11/11` PASS; all workflow JSON parse PASS; `git diff --check` PASS before this documentation append; modified media-worker modules pass `node --check`; clean n8n `2.33.3` import of WF04 PASS; a clean media-worker Docker build from `services/media-worker` PASS with image SHA `41811d52bf3d08d565855ed6acd63c6da5328c7dbe402e216608803a38f3f07`. Production has not yet been changed by this semantic-gate correction.

### 2026-09-06 bounded visual recovery query specificity correction

Fresh autonomous production job `cd5a21dd-3b89-4254-a462-e131b5b95646` (`How a mechanical clock escapement works`, `ru`, `15`) was created through WF01 only. WF02/WF03 completed and produced one continuous natural-rate voiceover of `14.448 s`. WF04 then failed closed before reviewer/assignment with `Visual segment 3 discovery returned no candidates`; no MP4 was produced. Exact execution `16110` showed two beats with zero candidate inventory even though their exact final-beat targets were valid. The bounded recovery query had collapsed `cutaway technical diagram showing mainspring energy release in a clock` to `cutaway technical diagram`, and `motion blur photography of a swinging brass clock pendulum` to `motion blur photography`. The general defect was recovery-query prefix bias: media/style words could displace the actual subject/mechanism.

Systemic correction under GitHub/deploy gate:

- recovery retrieval separates recall from acceptance: it preserves canonical subject overlap first and then ranks concrete content anchors ahead of photographic style/action words;
- when the exact query needs recovery, the provider query is intentionally compact and broad enough for retrieval (for example `clock mainspring` or `clock pendulum`) rather than trying to encode the full acceptance test;
- the original full `visual_target` remains unchanged and every recovered candidate must still pass the same strict target-anchor metrics before it can be exposed to the actual-image reviewer;
- the actual-image reviewer and global uniqueness gates remain unchanged; no unreviewed fallback, topic-level fallback, threshold weakening, asset reuse or second recovery round is introduced.

Real-provider verification on the exact failed six-beat timeline returned zero provider errors. The previously empty mainspring beat now returns two strict Wikimedia candidates (`Clock Mainspring.png` and `Alarm clock mainspring.JPG`), each with `4/3` required target-anchor hits. The previously empty pendulum beat now returns two strict candidates with `3/3` anchor hits. Static verification after the final logic: `33/33` Node tests + `11/11` Python tests PASS, workflow JSON PASS, `git diff --check` PASS, and a clean media-worker Docker build succeeds with image SHA `bddaf1e7ff12da5fd50df4f0d823610d86a66948f6833f6485dee4d23f87a54a`. Production has not yet been changed by this correction.
