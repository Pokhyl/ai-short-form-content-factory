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
