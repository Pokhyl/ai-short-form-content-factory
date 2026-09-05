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
