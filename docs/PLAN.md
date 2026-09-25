# AI Short-Form Content Factory — Production Plan

## Current uk45 verification job — 2026-09-25

Created `521324af-81b4-4848-b008-8d1b4616804a` for the user's exact RAM topic, Ukrainian45s, Gemini visual mode. Active M5v136 `6b396630-13f8-4bf2-9435-87af2d052cc4`, M8v72 `ecc2d163-8090-4094-947d-03b84747ba40`, M6v8. ID persisted before launch. NEXT: run once and trace this job; no other smoke while unresolved. Old failed86f9735d is immutable.

## M5 v136 deployed — 2026-09-25

Published source67022f3 to M5 only: v136 activeVersionId `6b396630-13f8-4bf2-9435-87af2d052cc4`. Zero active executions before deploy; current published nodes/connections match Git; all non-M5 workflow fingerprint unchanged `4cafa3fb1f7bc03f09b0d3b20001cd9e`. Backup/hash in `acceptance/2026-09-25-m5-v136-deploy.json`. Publisher restarted as CLI requires; health OK. M6v8/M8v72/worker unchanged.

Live schema replay initial validators: pl30/uk45 PASS; en15/ru60 correctly reject generic/non-photographic visual requests (semantic repair still required). All four provider requests accepted; do not call this four completed videos. NEXT: one new uk45 RAM smoke on v136, persist ID then run once.

## M5 10033 fix verified in source — 2026-09-25

- Exact uk45 request reproducibly returns Gemini400 INVALID_ARGUMENT with the old nested bounded-array schema. Grouping scene alternatives or using one scene shape while retaining nested array bounds still returns400. Same prompt/model/credential with one scene shape and only the outer scene count returns200. This localizes the failure to provider schema admission; Gemini does not expose the internal limit.
- Changed the provider schema for ALL durations/languages to one scene shape without nested array bounds. Exact scene/word allocations and existing local shot/query/evidence/semantic gates remain authoritative and unchanged. No topic-specific branch, model switch or local gate relaxation.
- Initial repair now preserves the original provider error. Second repair preserves it when no usable draft exists, while retaining the already-tested original-draft fallback after a transient repair failure. HTTP retry settings unchanged.
- Live schema admission: en15/pl30/uk45/ru60 all HTTP200. Offline all16 language/duration contracts plus existing regressions:394/394 PASS. Evidence `acceptance/2026-09-25-m5-10033-schema-replay.json`. This is NOT four E2E passes.
- Production still M5v135/M8v72. NEXT: zero-active check, backup/publish M5 only, compare published source and non-target versions, then one fresh RAM uk45 job. Failed job86f9735d remains immutable.

## ACTIVE BLOCKER — user uk45 RAM job, 2026-09-25

The en15 lighthouse acceptance below is a single-case result, NOT factory completion. User job `86f9735d-08ec-47e7-bb25-00bce7e4070c` (RAM, Ukrainian,45s) failed in M5 execution `10033`. Exact Generate Storyboard error is Gemini HTTP400 INVALID_ARGUMENT: “Request contains an invalid argument.” Repair handling masks it as “first Gemini output is empty [line53]”. Exact invalid request field is not yet diagnosed; do not claim a language or duration root cause without replay evidence. M8 never ran for this job.

NEXT: inspect this exact M5 request/schema, reproduce the request validation failure, fix generically and verify across supported language/duration contracts. Preserve failed job immutable. Do not use another lighthouse success as factory acceptance. Production unchanged M5v135/M8v72. Evidence: `acceptance/2026-09-25-uk45-10033-failure.json`.

## Latest verified result — 2026-09-25: E2E + visual QA PASS

This section supersedes all historical NEXT instructions below. The current smoke is complete; do not relaunch it or start another smoke automatically.

- Job `4b6a5e27-7409-4075-8699-408e0ef5b16f`, “how does a lighthouse work?”, en15, Gemini. All executions success: M3 `9991`, coordinator `9992`, M4 `9993`, M5 `9994`, M6 `9995`, M7 `9996`, M8 `9997`, M9 `10013`.
- Active production: M5 **v135** / `f33831c7-34f5-42f4-b634-7ba4ea64b4fc`; M6 **v8** / `0bcabe39-ae90-42fe-842b-8a56ad238709`; M8 **v72** / `ecc2d163-8090-4094-947d-03b84747ba40`. M5/M8 published nodes/connections verified equal to Git; publisher health OK. Worker unchanged.
- Real MP4: 1080×1920, H.264/yuv420p, 30fps, AAC; video14.833333s, audio14.808s, delta25ms; SHA256 `dda23d3858b55a62c09d9d20686e0f15b1f205fd59aef8a61e38c42dc2314dfd`. All machine QA gates pass.
- Manual actual-MP4 visual QA **5/5 PASS**: S1 coastal tower at1.303856s; S2 interior Fresnel lens at3.504114s; S3 lens with mechanical rotating base at7.355424s; S4 visible lighthouse beams at9.349156s; S5 rocky coast/breaking waves at13.201805s. S3 is a still photograph of apparatus, not observed motion.
- Audio technical/ASR PASS: exact normalized transcript, coverage1.000; decode successful, mean−25.0dB, peak−6.2dB, no silence ≥0.4s at−45dB. **Subjective listening was not performed.** Do not describe it as listened-to approval.
- Final regression: Node376/376, alignment DTW7/7, live worker render-fit3/3 PASS. Full manifest, exact selected asset URLs/IDs, per-concept Vision evidence, execution correlation, production versions, ffprobe and audio measurements: `acceptance/2026-09-25-v72-e2e-4b6a5e27.json`.
- Root cause resolved: old aggregate Vision PASS could contradict missing-required-concept evidence. M8v72 requires complete per-concept checks and computes visibility in code; exact old S3 replay rejected, fresh E2E passed. Prior `b372ee5e-a9a5-45ad-9381-e3bff004d9d9` remains machine-PASS/manual-FAIL, immutable.
- Review: https://publisher.hodor.com.pl/webhook/factory/review?job_id=4b6a5e27-7409-4075-8699-408e0ef5b16f
- Continuation: no unresolved code defect from this smoke. If subjective audio approval is required, listen to this existing MP4; do not regenerate. This single en15 result does not certify every topic or earlier PL15/EN30 acceptance.

## Historical checkpoints (superseded by the result above)

## Current v72 smoke — 2026-09-25

Created job `4b6a5e27-7409-4075-8699-408e0ef5b16f`: how does a lighthouse work?, en15, gemini. Active M5v135 f33831c7-34f5-42f4-b634-7ba4ea64b4fc / M6v8 / M8v72 ecc2d163-8090-4094-947d-03b84747ba40. Run accepted exactly once. Exact job correlation: M3 9991 PASS; coordinator9992 RUNNING; M4 9993 PASS; M5 9994 PASS; M6 9995 PASS; M7 9996 RUNNING at checkpoint. Other executions9957–9990 belong to different jobs and must not be treated as this smoke. NEXT: trace this exact job; do not relaunch or create another job while unresolved.


## M8 v72 deployed — 2026-09-25

- Published per-concept source26fd735 (verified replay/tests acf4c3d) to M8 only: v72 activeVersionId ecc2d163-8090-4094-947d-03b84747ba40. Current/published source matches Git; non-M8 fingerprint unchanged01742d9a61643a402f66f71ffbe47227. Publisher restarted as required; health OK.
- Zero active executions before deploy. Backup .backups/m8-before-9955-per-concept.json SHA25640db9b8b7dfec626a669a2e249cd31c1e331d9f765d2ba9fb0fc018671b8ac4d. M5v135/M6v8/worker unchanged.
- Node376 PASS; exact-image S3 Gemini replay rejects missing beam as required. NEXT: one new en15 Gemini smoke, persist ID before launch, inspect every required-concept result and final MP4. Prior b372ee5e remains machine-PASS/manual-FAIL.


## Exact S3 Vision replay PASS for rejection — 2026-09-25

- Revised request26fd735 on the exact9955 S3 preview bytes returned HTTP200 in2.862s, responseId Dwy2aubHN7KexN8PgYXnOQ. Both candidates explicitly mark Fresnel lens=true, light beam=false, intent=false, score50. The previously false-positive Wikimedia153722322 is now rejected. No image replacement, scene relaxation or model change.
- Saved response and preview SHA256 in acceptance/2026-09-25-m8-9955-per-concept-replay.json. Current parser replay rejects both candidates; full Node376/376 PASS; diff-check PASS. This is regression proof, NOT full-job acceptance.
- Production still M8v71 / M5v135. NEXT: zero-active/backup M8-only deploy, published-source/non-target verification, then one fresh smoke. Existing machine-pass/manual-FAIL job remains immutable.


## M8 per-concept Vision fix — source tested, 2026-09-25

- Provider must return indexed visible/evidence checks for EACH must_show concept. M8 derives aggregate visibility from all checks instead of trusting the model's aggregate boolean. Missing/duplicate/out-of-range/nonboolean/empty checks fail closed. Selected and evaluated-candidate evidence preserves each concept check. Score70, intent, exclusions, uniqueness and three-image limit unchanged.
- Prompt explicitly distinguishes a visible effect from apparatus capability. Output token cap4096 accommodates bounded per-concept evidence; no extra requests/models/providers. Old aggregate-only9955 response now rejected; missing-beam evidence rejects despite aggregate true/score90.
- Full Node375/375 PASS; diff-check PASS. Production still M8v71, M5v135. NEXT: bounded exact S3 image-request replay with new schema on existing credential; persist result, then safe M8-only deploy if verified. Existing b372ee5e job remains machine-pass/manual-FAIL.


## Manual S3 QA FAIL confirmed — 2026-09-25

- Existing machine-passed job b372ee5e-a9a5-45ad-9381-e3bff004d9d9 is NOT semantically accepted. Actual final MP4 inspected in browser at6.96826s: Fresnel lens rings and lamp bulbs visible, no emitted focused beam. Exact asset Wikimedia153722322, segment3 5340–8400ms. The scene explicitly requires both Fresnel lens and light beam.
- Gemini9955 gave aggregate must_show_visible=true/PASS90 while its own reason says “lacks a clearly visible focused light beam”. This confirms a false-positive aggregate Vision check, not a retrieval timeout or technical render failure. Saved exact scene contracts/evaluations in acceptance/2026-09-25-m8-9955-per-concept-gap.json.
- NEXT: replace model-generated aggregate must_show visibility with indexed checks for every required concept; derive aggregate/pass in code, reject missing/duplicate/malformed checks. Preserve the scene requirements, score threshold and uniqueness gate. Replay exact S3 with revised schema before targeted M8 deploy/new smoke.
- M3–M9 machine success and existing MP4 remain valid technical evidence; do not alter/relabel the immutable run. Manual audio listening not claimed. Active M5v135/M8v71 unchanged; Git source d1707a8.


## E2E machine PASS; manual QA pending — 2026-09-25

- Job b372ee5e-a9a5-45ad-9381-e3bff004d9d9 completed all stages: M3 9949 / coordinator9950 / M4 9951 / M5 9952 / M6 9953 / M7 9954 / M8 9955 / M9 9956 success. Real final MP4 exists. Do not rerun or create a new job before finishing this review.
- MP4 manifest saved acceptance/2026-09-25-b372ee5e-render-manifest.json:1080x1920,H.264,yuv420p,30fps,AAC,14976ms,5 photo segments,all machine gates true; SHA2567c9f837f5eadca55e75aaa06fbfee8471465500c09d0868f711e84551b2d164b. Path /data/renders/b372ee5e-a9a5-45ad-9381-e3bff004d9d9/final.mp4.
- Review https://publisher.hodor.com.pl/webhook/factory/review?job_id=b372ee5e-a9a5-45ad-9381-e3bff004d9d9 opened in in-app browser. Native player seekable range is0..0; playback completed but click-seeking did not change currentTime. Do not claim intermediate frames inspected from a failed seek.
- Selected assets: S1 Pexels12069451; S2 Wikimedia76004366; S3 Wikimedia153722322; S4 Pexels36345402; S5 Pexels35767035. S3 Gemini score90/PASS but reason explicitly says a clearly visible focused light beam is absent, despite required light beam. Manual exact S3 frame/asset inspection is next; final semantic acceptance NOT yet claimed. S5 observed final frame is a navigation buoy with a distant ship, consistent with its beacon/coastal-water contract.
- Active M5v135 f33831c7-34f5-42f4-b634-7ba4ea64b4fc / M6v8 / M8v71 8f894dcd-b852-4388-af7e-2dbafac73cbf. Latest371 Node +7DTW PASS. NEXT: inspect exact S3 plus remaining frames and audio evidence, resolve any confirmed defect, save acceptance and final checks. Never claim manual listening from ASR alone.


## Current v135/v71 smoke — 2026-09-24

Created job `b372ee5e-a9a5-45ad-9381-e3bff004d9d9`: how does a lighthouse work?, en15, gemini. Active M5v135 f33831c7-34f5-42f4-b634-7ba4ea64b4fc / M6v8 / M8v71 8f894dcd-b852-4388-af7e-2dbafac73cbf. Creation persisted before launch. NEXT: run once then trace; query actual state before resuming. No other job while unresolved.


## M5 v135 / M8 v71 deployed — 2026-09-24

- Source d1707a8 deployed only to M5 and M8. M5v135 activeVersionId f33831c7-34f5-42f4-b634-7ba4ea64b4fc; M8v71 activeVersionId8f894dcd-b852-4388-af7e-2dbafac73cbf. Both current/published sources match Git. Other workflow fingerprint unchanged c0d31621cc8a6462fb91459a29090869. Publisher restarted once as required, health OK.
- Zero active executions before deploy. Backups: .backups/m5-before-9948-contract.json SHA256b1731c67a4dfae19cf4de53440a7fe42c9006e12a29cbc63ab27823fdfabef7b; .backups/m8-before-9948-contract.json SHA256cd71b7691227d1884766668a2d203ab302363bd5f0046b4723fb0d499a28250c. M6v8/worker unchanged.
- Validation371 Node +7 DTW PASS. NEXT: one fresh en15 Gemini smoke; persist ID before launch. No successful MP4 acceptance yet.


## M8 9948 intent-subject / M5 ambient exclusion fix — source verified, 2026-09-24

- All three M8 request builders now preserve a simple explicitly stated leading subject from visual_intent when absent from must_show. It feeds the existing domain/context query and metadata gate. Exact S4 adds ship to all requests; exact S5 adds lighthouse, including the broad fallback. Planned query provenance remains unchanged. No topic/asset mappings; ambiguous action/context is not inferred from the topic.
- Saved Pexels replay confirms exact rock-only37438538 no longer passes the lighthouse-intent metadata gate. This is not a claim of a new Vision-approved selection. Requests/responses saved in tests/fixtures/m8-9948-*.json; no headers/credentials.
- M5 extends its existing diffuse-context normalizer to bare darkness/brightness/shadow(s). It preserves concrete unlit lamp, daytime scene, night scene, broken glass constraints. Generation + both repair prompts match. Existing visual_intent and Vision criteria remain unchanged.
- Node371/371 PASS; DTW7/7 PASS; diff-check PASS. Generic train/platform and already represented subject regressions prevent topic-specific behavior and added decorative requirements.
- Not deployed yet: M5v134 / M8v70. NEXT: zero-active, backup both changed workflows, deploy only M5+M8, exact-source/non-target verification, then one new smoke. Latest failed job566f4716-888e-46ab-a12d-810c9742fcd2 remains immutable.


## M8 9948 terminal semantic evidence — 2026-09-24

- Job566f4716-888e-46ab-a12d-810c9742fcd2 terminal at M8 9948. M3 9942/M4 9944/M5 9945/M6 9946/M7 9947 PASS; no M9. 45 searches,316 candidates,0 committed selections. Do not relaunch.
- M8 v70 loop parsed all five scenes correctly. S1 approved3; S2 approved0; S3 approved1; S4 approved0; S5 approved0. Thus provider recovery and five-scene loop proven; semantic acceptance still FAIL.
- Saved exact sets/evaluations in acceptance/2026-09-24-m8-9948-vision-evidence.json. S4 intent requires a ship near a lighthouse, but all planned queries omit ship and must_show only navigational beacon. S5 intent requires a lighthouse near rocks; must_show only coastal rocks; generic rock fallbacks outrank the explicit subject. S2 forbids generic darkness, excluding a lamp against a dark background; two other lamps were correctly rejected as unlit.
- NEXT: carry explicitly stated intent subject into M8 query/context relevance when absent from must_show, generically without topic mappings; preserve full intent/Vision gates. Extend M5 diffuse-context exclusion rule for bare lighting/background states, preserving explicit conflicting scene states. Replay saved contracts/provider evidence and full regressions before targeted deploy.
- Active M5 v134 a03f1e50-e829-49e7-836a-dc59c1dd192d / M6 v8 / M8 v70 abc02f16-0754-49cd-8d32-1adbe439e0aa. Latest audio14736ms passed; no MP4 acceptance yet.


## Current provider-recovery smoke — 2026-09-24

Created job `566f4716-888e-46ab-a12d-810c9742fcd2`: how does a lighthouse work?, en15, gemini. Active M5 v134 a03f1e50-e829-49e7-836a-dc59c1dd192d / M6 v8 / M8 v70 abc02f16-0754-49cd-8d32-1adbe439e0aa. Run accepted exactly once. M3 9942 PASS; coordinator9943 RUNNING; M4 9944 PASS; M5 9945 PASS; M6 9946 PASS; M7 9947 PASS; M8 9948 RUNNING. Searches45/candidates316/selections0 at checkpoint. Voiceover0b37edaa-526a-425b-a07c-b7c2a5d7375c,14736ms,SHA256780cdf92a837331f61182cd0a9c5aa29f13827d5c60b30b89b6422d653c1479b. NEXT: trace this exact job; query actual state before resuming. Do not relaunch or create another job while unresolved.


## Provider recovery confirmed — 2026-09-24

- One direct diagnostic request with exact saved M8 9940 S1-A payload, same existing Gemini credential/model, returned HTTP200 in1.358s. Payload41569bytes, responseId B4m1aq6CNsXfnsEPmbKQuQk, three evaluations scores90/95/90, all required booleans true. Usage1284tokens. No credentials or image payload persisted to repository; evidence acceptance/2026-09-24-m8-9940-direct-recovery.json.
- This establishes that the exact payload is valid and provider responds now. It does NOT turn failed job f868467c-6d25-4db1-ad49-9bcd28654d9d into a passing run or prove full pipeline recovery.
- Source/production unchanged: M5 v134 / M6 v8 / M8 v70. NEXT: one fresh controlled smoke, persist ID before launch. No source change/deploy needed for a recovered transient provider outage.


## M8 9940 terminal provider failure — 2026-09-24

- Job f868467c-6d25-4db1-ad49-9bcd28654d9d terminal: M3 9934 / M4 9936 / M5 9937 / M6 9938 / M7 9939 PASS; M8 9940 ERROR; no M9. Failed job remains immutable.
- New single-scene loop reached Gemini request; first scene exhausted bounded HTTP retry and parsing failed with exact “The connection was aborted, perhaps the server is offline”. Collector did not execute on partial results: previous count-mismatch masking is fixed. HTTP node total time147434ms. No scene Vision PASS claimed.
- VPS can reach Google API normally: unauthenticated models request returned expected403 in0.10s. This rules out a general DNS/TLS outage, not a model-specific overload. Prior M8 9932 had three explicit high-demand503 failures plus one aborted connection.
- Active M5 v134 a03f1e50-e829-49e7-836a-dc59c1dd192d / M6 v8 / M8 v70 abc02f16-0754-49cd-8d32-1adbe439e0aa; unchanged worker. Full Node363/native loop PASS.
- NEXT: diagnose provider availability with a bounded direct request using the existing credential before another costly full smoke. Do not change model, weaken Vision, or repeatedly launch jobs during the same provider outage. No successful MP4 yet.


## Current v70 smoke — 2026-09-24

Created job `f868467c-6d25-4db1-ad49-9bcd28654d9d`: how does a lighthouse work?, en15, gemini. Active M5 v134 a03f1e50-e829-49e7-836a-dc59c1dd192d / M6 v8 / M8 v70 abc02f16-0754-49cd-8d32-1adbe439e0aa. Run accepted exactly once. M3 9934 PASS; coordinator 9935 RUNNING; M4 9936 PASS; M5 9937 PASS; M6 9938 PASS; M7 9939 PASS; M8 9940 RUNNING. M5 passed probe1; final word-slot branch not exercised. Script run 15d2da37-9e44-485c-a4ca-d7719272e93c; TTS ledgers1076–1078. Voiceover 9e4391e0-2c75-4a1b-92a3-21a788282f3b, 15288ms, SHA256 37844c7f5f69d2ed23ce404dfb743d7c775577635daec6ec906080d284548109. NEXT: trace this exact job; query actual state before resuming. Do not relaunch or create another job while unresolved.


## M8 v70 deployed — 2026-09-24

- Source 7e189fc published only to M8: v70 activeVersionId `abc02f16-0754-49cd-8d32-1adbe439e0aa`. Current/published source matches Git; non-M8 fingerprint unchanged 5d4b9927849111bd94e5f29b09bc75dc. Publisher restarted as CLI required; health OK.
- Zero active executions before deployment. Backup `.backups/m8-before-9932-scene-retry.json`, SHA256 30bba1b6d5af7bd89fce40618073f072921e0b2a84b0c6306994bdf3b9689b82. M5 v134 / M6 v8 and worker unchanged.
- Full Node 363 PASS and native n8n loop runtime PASS. NEXT: one fresh en15 Gemini smoke, persist ID before launch and trace it. No successful MP4 acceptance yet.


## M8 9932 transient retry — source verified, 2026-09-24

- Gemini Vision HTTP now surfaces non-2xx errors (`neverError=false`) and has bounded 5-attempt retry, 5000ms delay. Same provider/model/credential, <=3 images per scene, unchanged parser and Vision gates.
- Installed n8n engine checks only first returned item's error for retry, and caps waitBetweenTries at 5000ms. Therefore added native splitInBatches v3, batchSize1: each scene independently requests/retries/parses; success loops to next scene; done collects all parsed results. Exhausted errors go to existing failure branch, avoiding misleading partial-collection count errors. No reset or retry cycle was added around the loop.
- Full Node 363/363 PASS; DTW 7/7 last PASS; worker unchanged. Installed native loop runtime regression PASS (five single-scene iterations, exact five-result collection), without provider calls or importing test workflows. Regression source tests/n8n-gemini-loop-runtime.cjs.
- Not deployed yet. M5 v134 / M6 v8 / M8 v69 unchanged. NEXT: zero-active/backup, deploy only M8, verify published source + non-M8 fingerprint, then one fresh smoke. Latest failed job 950862ca-2b65-4a6b-8603-a355980a36fb remains immutable.


## v134 smoke terminal at M8 9932 — 2026-09-24

- Job 950862ca-2b65-4a6b-8603-a355980a36fb terminal: M3 9924 PASS, M4 9926 PASS, M5 9928 PASS, M6 9930 PASS, M7 9931 PASS, M8 9932 ERROR; no M9. Do not relaunch.
- M8 completed 45 searches / 327 candidates / 0 committed selections. Vision S3-A returned two evaluations: candidate1 PASS95; candidate2 FAIL30 because exterior coastline violated its explicit constraint. Other four scenes failed provider calls: three high-demand errors, one connection aborted. Collector reported generic scene-validation-count mismatch; this is not evidence of four semantic rejections.
- Confirmed configuration gap: Gemini Validate Visuals has no retryOnFail and neverError=true, so transient provider responses reach parsing without retry. M5 already has bounded transient retry. NEXT: implement bounded M8 transient request retries with accurate failure propagation, regression/full tests, targeted M8 deployment, then one fresh job.
- Audio passed correctly: selected M6 voiceover 60ae4c5f-0ca5-49a5-bff0-56d78685e717 is 14304ms, SHA256 b296bfab5c236c7c44c66297bd6a7998f57654acc4b72e1f86eacbcbb701b31c. M5 diagnostic 13416ms is the median, NOT the selected artifact duration. No duration-gate defect established.
- Active M5 v134 a03f1e50-e829-49e7-836a-dc59c1dd192d / M6 v8 / M8 v69 d073d7d8-3490-468a-bb6a-79771d367059. Worker unchanged. No MP4 acceptance yet.


## Current v134 smoke — 2026-09-24

Created job `950862ca-2b65-4a6b-8603-a355980a36fb`: how does a lighthouse work?, en15, gemini. M5 v134 `a03f1e50-e829-49e7-836a-dc59c1dd192d`; M6 v8; M8 v69. Run accepted exactly once. M3 9924 PASS; coordinator 9925 RUNNING; M4 9926 PASS; M5 9928 PASS; M6 9930 PASS; M7 9931 PASS; M8 9932 RUNNING. M5 passed on probe3; new final word-slot branch was not exercised in this job. Script run 1d6765ea-5c03-4d2e-8047-7df70f667292; TTS ledgers 1070–1075 committed. NEXT: trace this exact job through remaining stages; query actual state before resuming. Do not relaunch it or create another job while unresolved.


## M5 v134 deployed — 2026-09-24

- Source 7770993 published to M5 only: v134 activeVersionId `a03f1e50-e829-49e7-836a-dc59c1dd192d`. Current nodes/connections/settings and published nodes/connections match Git. Non-M5 fingerprint unchanged c6d5e86eab4558051e8b77d36bbfd7da. Publisher restarted as CLI required; health OK.
- Zero active executions before deploy; backup `.backups/m5-before-9923-word-slots.json`, SHA256 d64a419f15c7015cf344fb1da2a010ac7373cef1033c0710520d0b6f1a14075e. M6 v8 / M8 v69 and worker unchanged.
- Full regression 361 Node + 7 DTW PASS; no new MP4 acceptance yet. NEXT: one fresh Gemini en15 smoke, persist ID before run, then trace exact job to terminal.


## M5 9923 correction — source verified, 2026-09-24

- The two existing final measured exact-count calls now emit `narration_words` keyed by scene, with schema-enforced per-scene array sizes. Adapters reject missing slots, embedded sentences and punctuation-only padding, then join words before unchanged semantic/hybrid/timing checks. No added calls or retries.
- Existing single compliance branch also handles malformed word slots. Its diagnostics can read the new representation. Known failing narration comparison now ignores punctuation/case, so a comma-only edit cannot consume another probe.
- Regression covers exact 9923 41-word comma-only draft and measured 13944ms, structural target [9,9,9,8,8], valid string reconstruction, invalid slots and bounded routing. Full Node 361/361 PASS; DTW 7/7 PASS; diff-check PASS. Worker/render unchanged (last render-fit 3/3 PASS).
- Not deployed yet: active M5 v133 872d0329-8c5d-4302-aaf1-8b041388c5e8; M6 v8; M8 v69. NEXT: zero-active/backup M5-only deployment, exact published-source/other-workflow verification, one fresh smoke. Failed job a872e916-6143-44c6-b68c-515860415f03 remains immutable.


## M5 9923 terminal — 2026-09-24

- Job `a872e916-6143-44c6-b68c-515860415f03` failed: M3 9920 PASS, coordinator 9921 ERROR, M4 9922 PASS, M5 9923 ERROR; no M6–M9. Do not relaunch.
- M5 v133 `872d0329-8c5d-4302-aaf1-8b041388c5e8`; M6 v8; M8 v69 `d073d7d8-3490-468a-bb6a-79771d367059` unchanged.
- Initial structural word-array contract worked: 38 words, probe 12048ms. Early timing drafts added unsupported descriptive terms and were rejected by existing semantic guards.
- Later exact-count repairs still use unconstrained strings: requested 43 words ([9,9,9,8,8]), returned 41. Probe4 stayed 13944ms. Final retry returned original38 and hybrid/no-op guard rejected it; compliance changed only a comma, retained41 and reached probe5 12528/12828/13128ms. Final target 15000±800ms failed.
- Confirmed defects: late provider representation does not enforce its count contract; punctuation-only changes bypass the no-op guard. Neither duration nor semantic tolerance should change.
- NEXT: structural count contract for existing late exact-count repairs plus lexical no-op detection; saved-response regressions, full tests, M5-only safe deploy, then exactly one fresh smoke. No successful MP4/visual acceptance yet.


## Current v133 smoke — 2026-09-24

Created job a872e916-6143-44c6-b68c-515860415f03 (how does a lighthouse work?, en15, gemini). M5 v133 active 872d0329-8c5d-4302-aaf1-8b041388c5e8; M6 v8; M8 v69. Creation checkpoint precedes run request. NEXT: launch once and trace this exact job; query live state before resuming. No additional jobs while unresolved.

## M5 v133 word-array contract deployed — 2026-09-24

- Source a0f12fa deployed only to M5: v133 activeVersionId 872d0329-8c5d-4302-aaf1-8b041388c5e8. Published/current source matches Git; non-M5 fingerprint unchanged c6d5e86eab4558051e8b77d36bbfd7da. Publisher healthy after required restart.
- Zero active executions before deployment. VPS backup .backups/m5-before-9919-word-arrays.json SHA256 36ec22b3f0c3c5824db35ac416582057812e46fd921bd721c5763eaf8d9d6c2a.
- M6 v8 and M8 v69 unchanged. Validation 355 Node + 7 DTW PASS; render-fit 3/3 on unchanged worker. NEXT: one controlled Gemini en15 lighthouse smoke, persist its ID before run and inspect exact generation/QA results. No successful E2E claimed yet.

## M5 word-array output contract — source verified, 2026-09-24

- Changed provider representation rather than adding another count prompt/retry: each scene emits narration_words with exactly its schema-allocated item count (en15 target38 => [8,8,8,7,7]). Each item must be one whitespace-free lexical word with attached punctuation.
- Provider schema alternatives bind each scene_id to its exact cardinality. Three existing validators deterministically join arrays into the established narration strings, then execute unchanged evidence, language, semantic, word-range, scene and pacing checks. Missing words, embedded sentences, and punctuation-only padding fail closed. INSUFFICIENT_EVIDENCE remains a schema alternative.
- Only initial storyboard generation/its two existing repairs use this representation. DB contract, timing-repair interfaces, narration semantics, TTS and quality thresholds are unchanged.
- Regression: all three adapters preserve an existing valid production narration exactly and reject malformed token arrays; schema allocates the calibrated target exactly. Node 355/355 PASS; DTW 7/7 PASS; render-fit 3/3 passed earlier this turn on unchanged worker; diff-check PASS.
- Current production still M5 v132 active 35e707f8-53e3-41c2-8aeb-cea85730701a / M8 v69. Job 959ccc58-868c-439f-8cb1-5bdc03b37158 terminal M5 9919.
- NEXT: commit/push, idle/backup M5-only deploy, exact source/non-M5 verification, then one Gemini smoke. Runtime provider-schema acceptance and completed smoke not yet claimed.

## v132 smoke terminal / change of repair strategy — 2026-09-24

- Job 959ccc58-868c-439f-8cb1-5bdc03b37158 terminal script_failed: M3 9916 PASS, M4 9918 PASS, M5 9919 ERROR, script run 61fa6ad7-e6c6-4cdd-8814-45f818df96d7. Exact final 34 words vs required 36-42. No TTS/M6-M9.
- Schema requests returned HTTP 200; structural fields are now present. Remaining failure is word-count/segmentation compliance: initial long scenes were repaired by shortening the narration; second repair ended at 34 total words despite explicit total diagnostics.
- Two prompt/string-count attempts did not solve this class. NEXT strategy: schema-constrained per-scene word arrays with exact dynamically allocated cardinalities, converted deterministically to existing narration strings before the unchanged semantic/word/duration validators. No invented padding, relaxed bounds or extra retries.
- Active production M5 v132 35e707f8-53e3-41c2-8aeb-cea85730701a / M8 v69 d073d7d8-3490-468a-bb6a-79771d367059. No active smoke; do not relaunch the failed job.

## Current v132 smoke — 2026-09-24

Created job 959ccc58-868c-439f-8cb1-5bdc03b37158 (how does a lighthouse work?, en, 15s, gemini). M5 v132 active 35e707f8-53e3-41c2-8aeb-cea85730701a; M6 v8; M8 v69. Creation checkpoint precedes run request. NEXT: launch once and trace this exact job; query actual state before resuming, do not create another job while unresolved.

## M5 v132 deployed — 2026-09-24

- Source 56d6d1d published only to M5 as v132 activeVersionId 35e707f8-53e3-41c2-8aeb-cea85730701a. Published nodes/connections and current nodes/connections/settings match Git. Other workflows unchanged (fingerprint c6d5e86eab4558051e8b77d36bbfd7da); publisher health OK after required restart.
- Zero active executions before deployment. VPS backup .backups/m5-before-9910-schema.json SHA256 82e663cf17cdcbfd50d6e6c930db17766313311d4a09922418dc4d68a6891cc5.
- M6 v8 / M8 v69 d073d7d8-3490-468a-bb6a-79771d367059 unchanged. Full validation 348 Node, 7 DTW, 3 render-fit PASS.
- NEXT: one controlled Gemini en15 lighthouse smoke. Previous job debbf9ba-f15b-471f-8e96-c0b198e70b77 is terminal, not a resumable active job.

## M5 9910 structured-output/repair fix — verified source, 2026-09-24

- Saved output confirms preferred_media_type was MISSING in all five shots in both generation and first repair; only second repair added photo, leaving 34 total words. This consumed the bounded repairs on structural omissions while the total-count violation stayed hidden.
- M5 initial and both repair HTTP requests now send responseJsonSchema, using the same supported API field already active in M8. Schema requires storyboard fields, exact scene/shot/query counts, photo-only enum and existing array bounds. The alternative INSUFFICIENT_EVIDENCE response remains supported. Semantic, word-count and duration validators are unchanged.
- Both repair builders additionally report total words, requested min/max, target, delta and validity from ALL scene narrations; 9910 explicitly reports 34 / 36-42, target 38, delta +4, invalid even when the first reported error is missing media type.
- Saved fixture tests/fixtures/m5-9910-storyboard-repair.json. Regression 3/3 PASS; full Node 348/348 PASS; DTW 7/7 PASS; render-fit 3/3 PASS in existing media-worker (local FFmpeg unavailable); diff-check PASS.
- Evidence: acceptance/2026-09-24-m5-9910-structured-repair.json. No change to providers, retries, quality gates or current M8.
- NOT deployed yet: M5 v131 active 0b4ba2f6-708d-4fe6-a194-13b2002fb338; M8 v69 d073d7d8-3490-468a-bb6a-79771d367059. NEXT: idle check/backup, deploy only M5, compare published source and other-workflow fingerprint, then one controlled Gemini smoke.

## Resume 2026-09-24 — M5 9910 terminal confirmed

- Refreshed clean main to 3a9096157b3439752d4c3a5032926f544ed849c3. Actual production confirmed M5 v131 0b4ba2f6-708d-4fe6-a194-13b2002fb338, M6 v8 0bcabe39-ae90-42fe-842b-8a56ad238709, M8 v69 d073d7d8-3490-468a-bb6a-79771d367059.
- Existing job debbf9ba-f15b-471f-8e96-c0b198e70b77 is terminal script_failed; M5 execution 9910 ERROR, script_run a62a18cb-c496-4533-80e0-af7049597887. Never relaunch this job.
- Exact final failure: “34, required 36-42 [line 860]”. No M6-M9. Initial scene exceeded 10 words; first repair corrected that but retained invalid preferred_media_type; second repair fixed that while preserving the underfilled 34-word narration.
- Repair diagnostics currently expose per-scene counts but not total requested-range violations hidden behind first-error validation. M5 HTTP requests enforce JSON MIME only, unlike M8's explicit responseJsonSchema, so invalid photo enum also consumes bounded repairs.
- NEXT: add complete total-count diagnostics and schema-constrained storyboard structure/photo enum to initial+repair requests, preserve INSUFFICIENT_EVIDENCE branch and all validators, regression-test saved 9910 data, then full suite/targeted M5 deploy/one smoke. No current active job; no new job created during refresh.

## Current M5 v131 / M8 v69 smoke — 2026-09-24

Job debbf9ba-f15b-471f-8e96-c0b198e70b77 created via M3 (how does a lighthouse work?, en, 15s, Gemini visual validation), HTTP 201. Production targets: M5 v131 / 0b4ba2f6-708d-4fe6-a194-13b2002fb338; M6 v8; M8 v69 / d073d7d8-3490-468a-bb6a-79771d367059. NEXT: launch this exact job once via /factory/run and trace it to terminal. Do not create another job while unresolved.

## M5 v131 diffuse-context fix deployed — 2026-09-24

- Source 405673c published only to VideoM5Storyboard001 as v131, activeVersionId 0b4ba2f6-708d-4fe6-a194-13b2002fb338.
- Backup .backups/m5-before-9892-context.json SHA256 42473c19842dc3288f9d8134181232c79e911c440861c352c3f7ca81bd9d9840.
- Zero active executions before deploy. Publisher restart completed; healthz 200, restart count 0.
- Published M5 nodes/connections/settings equal Git. Non-M5 fingerprint remains e01dde3463a9ea3f5b5c693865ab3726. M8 remains v69 d073d7d8-3490-468a-bb6a-79771d367059.
- NEXT: create exactly one controlled en15 lighthouse Gemini smoke and trace it to terminal.

## M8 9892 diffuse-context false exclusion — M5 source fix verified, 2026-09-24

- Job 6f41542b-b6db-46c5-9342-0f98435a08ca passed M3 9879, M4 9881, M5 9884, M6 9888 and M7 9889. M8 9892 failed; M9 did not run.
- Exact M8 terminal: `no Gemini-approved unique visual candidate for shot S2-A`.
- S2-A requested `lighthouse lamp room` with visual intent `Inside the lighthouse lamp room showing lighting equipment.` but M5 also emitted `must_not_show: ["exterior landscape"]`.
- Candidate Pexels 14199476 visibly contained the required lighthouse lamp equipment inside. Gemini rejected it only because large windows also showed exterior landscape: must_show_visible=true, must_not_show_clear=false, intent_match=false, score 40.
- Root cause is M5 storyboard metadata, not M8 Vision: incidental background/context visible through windows was encoded as a hard conflict.
- Fix: initial and both bounded storyboard-repair prompts restrict must_not_show to concrete conflicting subjects or truly mutually exclusive scene states and forbid generic background/landscape/scenery exclusions. Final storyboard canonicalization additionally removes exclusions headed by background, landscape, or scenery before commit.
- Real exclusions remain intact, including wind turbine, daytime scene, exterior tower. M8 v69, Gemini threshold, uniqueness and providers are unchanged.
- Validation: focused 3/3 PASS; full Node 345/345 PASS; DTW 7/7 PASS; render-fit 3/3 PASS; git diff --check PASS.
- Evidence: acceptance/2026-09-24-m8-9892-diffuse-context.json.
- NOT deployed yet. NEXT: commit/push, verify zero active executions, back up/deploy only M5, verify source, then one controlled en15 Gemini smoke.

## Current M5 v130 / M8 v69 smoke — 2026-09-24

Job 6f41542b-b6db-46c5-9342-0f98435a08ca created via M3 (how does a lighthouse work?, en, 15s, Gemini visual validation), HTTP 201. Production targets: M5 v130 / f6e328cd-707b-48ef-b8f4-7ce7cc19c17d; M6 v8; M8 v69 / d073d7d8-3490-468a-bb6a-79771d367059. NEXT: launch this exact job once via /factory/run and trace it to terminal. Do not create another job while unresolved.

## M5 v130 requested-range gate deployed — 2026-09-24

- Source bb2bcb2 published only to VideoM5Storyboard001 as v130, activeVersionId f6e328cd-707b-48ef-b8f4-7ce7cc19c17d.
- Backup .backups/m5-before-9864-gate.json SHA256 240f83d624d36761182d4cb3663935ebab8a2584485b48d0faa4c5bec791ccde.
- Zero active executions before deploy. Publisher restart completed; healthz 200, restart count 0.
- Published M5 nodes/connections/settings equal Git. Non-M5 fingerprint remains e01dde3463a9ea3f5b5c693865ab3726. Active executions after verification: 0.
- NEXT: create exactly one controlled en15 lighthouse Gemini smoke and trace it to terminal.

## M5 9864 initial requested-range gate — source fix verified, 2026-09-24

- v129 smoke job d320d5cb-962e-4a23-8862-552bae58d09a reached M5 execution 9864 and failed after final Probe 5 at 13344ms versus 15000ms ±800ms.
- The new English calibration was active: Build Script Prompt produced word_min 36, word_max 42, target 38. Gemini nevertheless returned only 30 words, and the initial validator accepted it.
- Root cause: Validate Storyboard / Validate Repaired Storyboard / Validate Repaired Storyboard 2 still enforced the legacy 70%-135% anti-runaway envelope rather than the requested narration range. That allowed an underfilled draft into TTS and froze too little evidence-grounded semantic content.
- Fix: all three initial storyboard validators now require the actual requested word_min-word_max (subject only to structural scene capacity). Underfilled/overfilled text is sent through the already-existing two bounded storyboard repairs; no new retry was added.
- No TTS speed, timing tolerance, semantic threshold, scene cap, or provider was changed.
- Validation: focused 3/3 PASS; full Node 342/342 PASS; DTW 7/7 PASS; render-fit 3/3 PASS; git diff --check PASS.
- Evidence: acceptance/2026-09-24-m5-9864-initial-word-gate.json.
- NOT deployed yet. NEXT: commit/push, verify zero active executions, back up/deploy only M5, verify published source, then one controlled en15 Gemini smoke.

## Current M5 v129 / M8 v69 smoke — 2026-09-24

Job d320d5cb-962e-4a23-8862-552bae58d09a created via M3 (how does a lighthouse work?, en, 15s, Gemini visual validation), HTTP 201. Production targets: M5 v129 / 04764504-c7e8-41bc-9bbe-3b3895333245; M6 v8; M8 v69 / d073d7d8-3490-468a-bb6a-79771d367059. NEXT: launch this exact job once via /factory/run and trace it to terminal. Do not create another job while unresolved.

## M5 v129 English budget fix deployed — 2026-09-24

- Source d4f1bb9 published only to VideoM5Storyboard001 as v129, activeVersionId 04764504-c7e8-41bc-9bbe-3b3895333245.
- Backup .backups/m5-before-9847-budget.json SHA256 8f55bf27c48511dc935fc5e0c85bdbe7fd9fe1dc305d87593ffffdc55b559650.
- Zero active executions before deploy. Publisher restart completed; healthz 200, restart count 0.
- Published M5 nodes/connections/settings equal Git. Non-M5 fingerprint remains e01dde3463a9ea3f5b5c693865ab3726. Active executions after verification: 0.
- NEXT: create exactly one controlled en15 lighthouse Gemini smoke and trace it to terminal.

## M5 9847 English speech-budget calibration — source fix verified, 2026-09-24

- Job 3a181937-0ece-4338-b200-582eebea358a is terminal script_failed in M5 execution 9847; M6-M9 did not run.
- Exact terminal: `got 34, target 38, allowed delta 2` in the final measured word-count compliance path.
- Production evidence shows the failure is upstream calibration, not absence of late repair: initial 29 words measured 10248ms; latest semantic-valid 34 words measured 13224ms against 15000ms with unchanged 800ms tolerance. The late 38-word target could not be reached without semantic padding.
- Same en15 lighthouse production history (execution 9813) measured 31 words at 12456ms and 36 words at 14016ms. Therefore the previous English prompt target 2.2 words/sec materially underfilled the current TTS voice before semantic freezing.
- Fix changes only English initial speech budget from min/max/target 1.8/2.6/2.2 to 2.4/2.8/2.55 words/sec. For 15s this means 36-42 words, target 38, so additional content must be evidence-grounded during initial script generation instead of invented during timing repair.
- Added floating-point-safe integer bounds so exact limits such as 45*2.8 resolve to 126 rather than 125. Polish/Russian/Ukrainian budgets are explicitly regression-tested unchanged.
- No timing tolerance, semantic threshold, TTS speed, retry count, or scene word cap was relaxed.
- Validation: focused budget 2/2 PASS; full Node 341/341 PASS; DTW 7/7 PASS; render-fit 3/3 PASS; git diff --check PASS.
- Evidence: acceptance/2026-09-24-m5-9847-english-budget.json.
- NOT deployed yet. NEXT: commit/push, verify zero active executions, back up/deploy only M5, verify source, then one controlled en15 Gemini smoke.

## Current M5 v128 / M8 v69 smoke — 2026-09-23

Job 3a181937-0ece-4338-b200-582eebea358a created via M3 (how does a lighthouse work?, en, 15s, Gemini visual validation), HTTP 201. Production targets: M5 v128 / 18e33555-e7e7-4ed4-8c86-d87752a42f69; M6 v8; M8 v69 / d073d7d8-3490-468a-bb6a-79771d367059. NEXT: launch this exact job once via /factory/run and trace it to terminal. Do not create another job while unresolved.

## M5 v128 structural-routing fix deployed — 2026-09-23

- Source 79d3103 published only to VideoM5Storyboard001 as v128, activeVersionId 18e33555-e7e7-4ed4-8c86-d87752a42f69.
- Backup .backups/m5-before-9833-fix.json SHA256 346395894958caf263989f82ca41970617c3dddbd50a9e39a3729b1f96aaed74.
- Zero active executions before deploy. Publisher restart completed; healthz 200, restart count 0.
- Published M5 nodes/connections/settings equal Git. Non-M5 fingerprint remains e01dde3463a9ea3f5b5c693865ab3726. Active executions after verification: 0.
- NEXT: create exactly one controlled en15 lighthouse Gemini smoke and trace it to terminal.

## M5 9833 structural-repair routing — source fix verified, 2026-09-23

- Job 39ccba65-a380-4d1b-86f7-98c862307ecb is terminal script_failed: M3 9828 PASS, M4 9830 PASS, M5 9833 ERROR; no M6/M7/M8/M9.
- Exact failure: after a real 12288ms measurement against 15000ms ±800ms, Final Duration Repair targeted about 37 words with scene guidance [5,5,8,9,10]. Gemini returned [5,5,8,9,13]; S5 exceeded the unchanged 10-word hard bound and added timing filler such as swiftly/dark/safely. Validate Final Duration Repair immediately threw `13 [line 251]`.
- The workflow already had the correct bounded recovery route: Route Final Duration Word Count false branch -> Build Final Word Count Retry. The structural throw happened before that route, so it was a routing defect rather than absence of a repair mechanism.
- Fix: Final Duration/Measured builders now explicitly forbid factual/descriptive timing padding and prefer grammatical glue/function words. Validate Final Duration Repair and Validate Final Measured Correction now return `structural_valid=false` / `semantic_valid=false` for invalid model text, which sends it to the existing bounded repair; provider/HTTP/JSON/context failures still throw and invalid drafts never reach TTS. Validate Final Word Count Retry also excludes over-bound provider options before its existing semantic DP.
- No retry count, TTS speed, timing tolerance, semantic threshold or 2-10 scene bound was relaxed.
- Regression covers both final timing branches and confirms an over-limit draft routes to the existing repair. Focused 28/28 PASS; full Node 339/339 PASS; DTW 7/7 PASS; render-fit 3/3 PASS; git diff --check PASS.
- Evidence: acceptance/2026-09-23-m5-9833-structural-routing.json.
- NOT deployed yet. NEXT: commit/push, verify zero active executions, back up/deploy only M5, verify source, then one controlled Gemini smoke.

## Current M5 v127 / M8 v69 smoke — 2026-09-23

Job 39ccba65-a380-4d1b-86f7-98c862307ecb created via M3 (how does a lighthouse work?, en, 15s, Gemini visual validation), HTTP 201. Production targets: M5 v127 / 726a4c13-e945-4e9d-983f-6775e8dc1191; M6 v8; M8 v69 / d073d7d8-3490-468a-bb6a-79771d367059. NEXT: launch this exact job once via /factory/run and trace it to terminal. Do not create another job while unresolved.

## M5 v127 timing-expansion fix deployed — 2026-09-23

- Source 1939e57 published only to VideoM5Storyboard001 as v127, activeVersionId 726a4c13-e945-4e9d-983f-6775e8dc1191.
- Backup .backups/m5-before-9822-fix.json SHA256 d0325f1578d78fb05ac788a400091292cbfb38b5fcc6dfbf0683f96b6ed4e809.
- Zero active executions before deploy. Publisher restarted once as required by n8n CLI; healthz 200, restart count 0.
- Published M5 nodes/connections/settings equal Git. Non-M5 fingerprint remained e01dde3463a9ea3f5b5c693865ab3726. Active executions after verification: 0.
- NEXT: create exactly one controlled en15 lighthouse Gemini smoke and trace that exact job to terminal.

## M5 9822 final word-count compliance — source fix verified, 2026-09-23

- v69 smoke job 19044bf3-ba7f-43e3-85cc-87a70463e249 is terminal script_failed before M6: M3 9818 PASS, M4 9820 PASS, M5 9822 ERROR. It did not exercise M8 v69.
- Exact failure: final word-count compliance target was 36 words with per-scene targets [10,5,4,7,10]. The latest semantic-valid 32-word draft measured 13128ms. Gemini compliance returned scene counts [10,5,4,8,11]; scene 5 violated the hard 10-word cap and padded with unsupported descriptive/quantity content. n8n surfaced only `11 [line 259]`.
- Source fix keeps the same single bounded compliance branch. Expansion prompts now require preserving semantic-valid content and using grammar-only connector/function words before any new content word; invented properties, materials, quantities, intensifiers, locations and objects are explicitly forbidden.
- Validators no longer terminal-fail merely because the model returned an out-of-bound scene. That model option is excluded from the existing deterministic semantic hybrid; only 2-10 word, lexical, semantic-valid options can enter the DP. Timing, semantic, scene-bound and no-repeat gates remain unchanged.
- Regression reproduces an 11-word returned scene and proves it is excluded while a valid exact-count hybrid is recovered. Focused 6/6 PASS; full Node 337/337 PASS; DTW 7/7 PASS; render-fit 3/3 PASS; git diff --check PASS.
- Evidence: acceptance/2026-09-23-m5-9822-word-count.json.
- NOT deployed yet. NEXT: commit/push, verify zero active publisher executions, back up and deploy only M5, verify published source, then one controlled en15 lighthouse Gemini smoke.

## Current v69 smoke job — 2026-09-23

Job 19044bf3-ba7f-43e3-85cc-87a70463e249 created via M3 (topic how does a lighthouse work?, en, 15s, visual_validation_mode gemini). M8 v69 active d073d7d8-3490-468a-bb6a-79771d367059. Creation returned HTTP 201. NEXT: launch this exact job once via /factory/run and trace it to terminal. Do not create another job while unresolved.

## M8 v69 structured-output fix deployed — 2026-09-23

- Source commit c6f0445 is published only to VideoM8Visuals001 as v69, activeVersionId d073d7d8-3490-468a-bb6a-79771d367059.
- Predeploy published backup: .backups/m8-before-9816-schema.json, SHA256 7c653e16a852e6354a180f61aaf341ace038c07f6d91ac07fcfc32c2e875fc1a.
- Zero active executions before deploy. Publisher restarted once as required by n8n CLI; healthz 200, container restart count 0.
- Published M8 nodes/connections/settings equal Git. Non-M8 workflow fingerprint stayed 69a9cde4d28611881f2cbf64d21958b3. Active executions after verification: 0.
- NEXT: create exactly one controlled en15 lighthouse Gemini smoke and trace that exact job to terminal. Do not create a second job while unresolved.

## M8 9816 malformed Gemini JSON — source fix verified, 2026-09-23

- Controlled job ec85da0d-3947-4b02-b29d-a666094e2009 is terminal: M3 9810 PASS, M4 9812 PASS, M5 9813 PASS, M6 9814 PASS, M7 9815 PASS, M8 9816 ERROR; no M9.
- Exact M8 failure was not a visual-quality rejection. Gemini returned HTTP 200 but one scene response contained malformed JSON: `{"candidate_index_3,...}`. Parse Gemini Vision Result correctly failed closed; the missing parsed scene then surfaced as `Gemini scene validation count mismatch`.
- Source fix adds `generationConfig.responseJsonSchema` to the existing Gemini Vision request. The schema constrains the evaluations envelope and candidate_index/boolean evidence/match_score/reason fields. Existing parser validation, 70 score floor, uniqueness, metadata evidence and fail-closed behavior remain unchanged. No topic-specific rule, JSON string repair, blind retry loop or visual-gate relaxation.
- Validation: focused Gemini 15/15 PASS; full Node 336/336 PASS; DTW Python 7/7 PASS; render-fit 3/3 PASS; git diff --check PASS.
- Evidence: acceptance/2026-09-23-m8-9816-schema-contract.json.
- NOT deployed yet. Production remains M5 v126 / M6 v8 / M8 v68 4f9709cb-b819-417f-8991-fc2c3a4eaebc. NEXT: commit/push this tested source, verify zero active publisher executions, back up/deploy only M8, verify published source, then run exactly one controlled Gemini smoke.

## Current M8 v68 smoke — 2026-09-23

Job ec85da0d-3947-4b02-b29d-a666094e2009 created (en15 lighthouse, gemini). M5 v126 / M6 v8 / M8 v68 active 4f9709cb-b819-417f-8991-fc2c3a4eaebc; worker image 4118f3f06c98. Run accepted. M3 9810 PASS; coordinator 9811; M4 9812 PASS; M5 9813 PASS; M6 9814 PASS; M7 9815 PASS; M8 9816 RUNNING at this checkpoint. NEXT: trace M8 9816 to terminal and inspect Gemini evidence; do not launch this job again or create another job while unresolved.

## M8 v68 deployed — 2026-09-23

- Published source be0db87 only to M8: v68 activeVersionId 4f9709cb-b819-417f-8991-fc2c3a4eaebc. Published/current source verified equal Git; non-M8 workflow fingerprint unchanged eab3729c9a1c9f3a5e7bb0a870f96473.
- Zero active executions before deploy. VPS backup /opt/ai-short-form-content-factory/.backups/m8-before-9809-setting.json SHA256 c26f166c7f883f29e00bcb58cc24a472d41ae36c46c2c2d90e92d9bdc05aef2d. Only publisher restarted; health OK.
- M5 v126 / M6 v8 and worker image 4118f3f06c98 unchanged. Tests 336 Node + 7 Python PASS. NEXT: one controlled Gemini en15 lighthouse smoke; do not claim new assets validated until its actual Vision result.

## M8 explicit setting fix — source verified, 2026-09-23

- Actual 9809 S2/S3 request contexts had empty domain_context_terms despite explicit lighthouse settings. Request builders now derive explicitly stated locations (inside/within/interior-of/room-of/hall-of) for any subject and corroborate terms against existing planned queries. Original query provenance remains unchanged; provider queries retain the setting.
- No lighthouse-specific mapping or expanded subject whitelist. Regression also verifies hospital/microscope setting and excludes unsupported decoration terms.
- Replayed saved Pexels responses: exact household assets 3324439, 18109261, 15664927 now receive metadata rejection rather than accepted ranking. Gemini soft-review policy remains unchanged: metadata rejection alone is not claimed as permanent exclusion from Vision.
- Seven focused tests PASS; full Node suite 336/336 PASS. Saved public provider fixture tests/fixtures/m8-9809-pexels-context.json contains no headers/credentials. Existing Python DTW 7/7 PASS.
- NOT deployed yet. Active M8 v67 21599d8f-f0c9-48c8-af86-ba9e297cdd5a, M5 v126, M6 v8. Latest job 360aba8c-ce92-499e-8f01-504726d352dd terminal at M8 9809. NEXT: backup/verify idle, deploy only tested M8, verify exact source and run one controlled Gemini smoke. A valid replacement asset is not yet proven.

## Gemini smoke 9809 — all five scenes visually reviewed, 2026-09-23

- Job 360aba8c-ce92-499e-8f01-504726d352dd terminal visual failure. M4 9805, M5 9806, M6 9807, M7 9808 PASS; M8 9809 FAIL; no M9. Visual run 52eaa0a4-36a1-4d39-ae6f-b5af9ceda46a: 45 searches, 322 candidates, 0 committed selections.
- Gemini actually reviewed 3 images for EACH of 5 scenes (15 images total). Approved counts S1=1, S2=0, S3=0, S4=3, S5=3. First failure “no Gemini-approved unique visual candidate for shot S2-A”. Exact assets, preview hashes and reasons saved in acceptance/2026-09-23-m8-9809-gemini-evidence.json.
- S2 top candidates were household pipe lamp, defective unlit bulb, and bulb icon; none showed a glowing lamp inside a lighthouse lantern room. S3 top candidates were household floor/desk lamps and an exterior lamp; none satisfied lighthouse interior machinery. Gemini rejected them; do not weaken that gate.
- M7 this run used standard alignment (DTW not needed): audio 15336ms, global coverage 1.0, lexical end 15000ms, overrun 0. The DTW-specific proof remains the exact-file replay of 9802.
- NEXT: fix pre-Vision retrieval/context ranking for explicitly requested settings. M8 currently scopes domain extraction to a head whitelist; bulb/fixture fail to carry lighthouse context into broad searches/metadata gates. Derive explicitly stated setting from scene intent plus planned query evidence, not a lighthouse-specific rule. Replay saved S2/S3 requests/candidates before any new job.
- Active production remains M5 v126 205d2b88-026c-4597-815a-74eeadcd7a9f / M6 v8 0bcabe39-ae90-42fe-842b-8a56ad238709 / M8 v67 21599d8f-f0c9-48c8-af86-ba9e297cdd5a; media-worker image 4118f3f06c98. No visual acceptance yet.

## Post-DTW smoke in M8 — 2026-09-23

Job 360aba8c-ce92-499e-8f01-504726d352dd: M3 9803 PASS; coordinator 9804; M4 9805 PASS; M5 9806 PASS; M6 9807 PASS; M7 9808 PASS; M8 9809 RUNNING at this checkpoint. Production M5 v126 / M6 v8 / M8 v67; worker image 4118f3f06c98. NEXT: trace existing M8 9809 to terminal and inspect actual Gemini evidence. Do not create another job. M7 success alone does not prove that the new DTW branch was exercised; inspect saved alignment metadata before claiming that.

## Current post-DTW smoke — 2026-09-23

Job 360aba8c-ce92-499e-8f01-504726d352dd created: en15 lighthouse, visual_validation_mode gemini. Media-worker health verified healthy; image 4118f3f06c98; M5 v126 / M6 v8 / M8 v67. Creation persisted before run request. NEXT: run this exact job once and trace it; query actual state before resuming. No additional jobs while unresolved.

## DTW media-worker deployed — 2026-09-23

- Deployed source 1f45ad3 only to shorts-v2 media-worker. Live /worker/server.py equals Git; SHA256 e672e125a10115581acf748bfa8477d9a84d1eac253566f5d8e0191961099da1. New image sha256:4118f3f06c98cb37cf1985bfb97b56d1c1ec7088d8e7c76726d7e209e2393ec2.
- Zero active n8n executions before deploy. Backup /opt/ai-short-form-content-factory/.backups/media-worker-before-9802-dtw.py SHA256 a3d07f116c32f251bc6191cb7452a74a53c89d052ad7c53bf9812b965ee14714; previous image sha256:64e96a07a1d5438cbe8ffea28c815a36e4be1480ad3ded270c7839e75ab4d0d8 retained for rollback.
- Container running, restart count 0. M5 v126 / M6 v8 / M8 v67 unchanged. Exact-audio replay already passed; 7 Python + 329 Node regressions passed.
- NEXT: verify healthy, then create exactly one fresh Gemini en15 lighthouse smoke and trace it. Failed prior job remains immutable. No complete-pipeline acceptance yet.

## M7 9802 exact-audio replay PASS — source fix, 2026-09-23

- Artifact integrity confirmed: voiceover 796f8592-7a94-4de4-bbb6-1d26fc3ba070, 14736ms, SHA256 35a8fa2dd2b3e1f6e2f68dc2038867b7599508857cbc4c15bb829e89aa9f174a. No M5/M6 artifact mismatch. Default Whisper final lexical end is 16350ms (1614ms overrun).
- Diagnostic word segmentation (-ml 1) did not fix the default offsets. DTW on the same installed model/audio produced in-range token emission points; default offsets remain wrong even with DTW enabled, so simply adding a CLI flag is insufficient.
- Source fix: one DTW fallback only for the specific terminal-overrun failure. Convert monotonic DTW emission points (10ms units) into contiguous token intervals ending at each point; preserve heuristic offsets and original-pass evidence. Reject missing/nonmonotonic/out-of-audio DTW values and changed recognized transcript. Existing lexical-coverage and scene-timing gates remain mandatory. No timestamp scaling, forced clipping, model/provider switch, or job mutation.
- Actual candidate-code replay inside the current media-worker container on the exact production MP3 PASS: 5 scenes, global coverage 0.989899, S3 coverage 0.947368, lexical end 14380ms, overrun 0. ASR still recognizes Fresnel as Fresno; this passes existing coverage policy, not exact transcription. Manual audio/visual acceptance remains pending.
- Evidence: acceptance/2026-09-23-m7-9802-dtw-replay.json and tracked tests/fixtures/m7-9802-alignment.json. Python DTW regression 7/7 PASS; Node 329/329 PASS; py_compile/diff-check PASS.
- DTW interpretation source: https://github.com/ggml-org/whisper.cpp/blob/master/include/whisper.h (t_dtw token emission point) and src/whisper.cpp (10ms units). Installed CLI supports -dtw small -nfa; same pinned ggml-small model used.
- NOT deployed yet. Production M5 v126 active 205d2b88-026c-4597-815a-74eeadcd7a9f / M6 v8 / M8 v67 unchanged. Job 7b5ed96e-36f0-4b19-84b9-bebcf5520138 remains failed at M7 9802.
- NEXT: back up current media-worker source/image, verify no active runs, deploy only media-worker and verify source/health. Then one fresh controlled Gemini smoke; do not mutate/restart the failed job.

## v126 smoke terminal — M5/M6 PASS, M7 FAIL, 2026-09-23

- Job 7b5ed96e-36f0-4b19-84b9-bebcf5520138: M3 9797 PASS; coordinator 9798; M4 9799 PASS; M5 9800 PASS on v126 205d2b88-026c-4597-815a-74eeadcd7a9f; M6 9801 PASS; M7 9802 ERROR. No M8/M9.
- M5 produced a 35-word repaired narration. Probe 3 measured 15288ms; stability measurements 14976/14736ms. This run passed via timing probe 3; it did not exercise the new final measured compliance branch.
- M6 run d0169f12-e797-4689-9379-629f259a65c1 reused M5 TTS usage key m5-tts-stability-b:f32ce056-73af-4d53-a856-180c94b99c66:3, ledger 1000. Voiceover ID 796f8592-7a94-4de4-bbb6-1d26fc3ba070.
- M7 alignment run 13d76b67-193b-4554-8e3f-31bca8a2d1c4 failed: “whisper lexical timing exceeds audio duration beyond tolerance: 1614ms”.
- NEXT: inspect exact stored voiceover artifact/duration and Whisper timing evidence to distinguish artifact mismatch from aligner overrun. Do not weaken tolerance or launch another full job. Production M5 v126 / M6 v8 / M8 v67 unchanged; 329 tests last PASS.

## Current smoke — M5 v126, 2026-09-23

Created job 7b5ed96e-36f0-4b19-84b9-bebcf5520138 (en15 lighthouse, gemini). Run this exact job once, then trace terminal status. Creation was persisted before /factory/run: check stage/execution state before resuming. M5 active 205d2b88-026c-4597-815a-74eeadcd7a9f; M6 v8; M8 v67. Do not create another job while this one is unresolved.

## M5 v126 deployed — 2026-09-23

- Published c264500 to M5 only: v126 activeVersionId 205d2b88-026c-4597-815a-74eeadcd7a9f. Published nodes/connections and current nodes/connections/settings verified equal Git. Other workflows unchanged; publisher health OK after required restart.
- Zero active executions before deploy. VPS backup /opt/ai-short-form-content-factory/.backups/m5-before-9796-fix-20260923-192313.json SHA256 709f498f7619389745b98cebdfb9d6087fb072cee0c69d3c7c0ed72dd9f9625f.
- Full tests 329/329 PASS. M6 v8 / M8 v67 unchanged. NEXT: exactly one controlled Gemini en15 lighthouse smoke; preserve job ID immediately, then trace to terminal. No passing smoke claimed yet.

## Execution 9796 repair diagnostics — source verified, 2026-09-23

- Both storyboard repair prompts now recompute every scene's word count from the candidate JSON and include scene_id, actual count, min/max, valid flag. Explicitly request repair of every invalid count even if the first error concerned metadata. This preserves scene identity when n8n strips the exception prefix and exposes latent violations before the next bounded retry.
- Regression reproduces S5=11, max=10 from execution 9796 in both repair builders. Full suite 329/329 PASS; git diff --check PASS. No extra retries, model changes, or relaxed gates.
- Production still M5 v125 / 9d92b100-7739-4eed-9bf4-093395c3db32; latest job 03ca6223-29b4-4782-95b3-e968a5ced556 failed M5 9796 before TTS. NEXT: deploy tested M5 repair-diagnostics change with backup/zero-active/exact-source verification, then one controlled smoke.

## Smoke 03ca6223 — terminal result, 2026-09-23

- Job 03ca6223-29b4-4782-95b3-e968a5ced556 is script_failed. M3 9793 PASS, coordinator 9794 ERROR, M4 9795 PASS, M5 9796 ERROR on active v125 / 9d92b100-7739-4eed-9bf4-093395c3db32. Script run 6ec11461-fd82-4660-869c-680964c320f7.
- Initial storyboard failed S1-A preferred_media_type; first repair then exposed S5 length 11 words against maximum 10. Both repairs retained identical narrations. n8n reduced the second validator error to “11, maximum 10 [line 499]”, losing scene identity/context.
- The smoke never reached timing correction, M6, or M8, so it does not validate the v125 timing routing fix end-to-end.
- NEXT: make both storyboard repair prompts report all per-scene word-count violations from the saved candidate, with exact scene IDs and bounds; reproduce execution 9796. Do not just create another job or weaken the 10-word scene bound. Production remains v125; no further deployment yet.

## Active smoke job — 2026-09-23

- Created job 03ca6223-29b4-4782-95b3-e968a5ced556 via M3: topic how does a lighthouse work?, en, 15s, visual_validation_mode gemini.
- Target production M5 v125 / 9d92b100-7739-4eed-9bf4-093395c3db32, M6 v8, M8 v67.
- NEXT: launch/trace this exact job via /factory/run and stored executions. Do not create another job. This creation checkpoint precedes the run request; query job/stage state before resuming to avoid duplicate launch.

## M5 v125 deployed — 2026-09-23

- Source 6c0e7d0 deployed only to VideoM5Storyboard001. Active M5 v125: 9d92b100-7739-4eed-9bf4-093395c3db32. Published nodes/connections and current nodes/connections/settings equal Git.
- Zero active n8n executions before deployment. Backup on VPS: /opt/ai-short-form-content-factory/.backups/m5-before-9788-fix-20260923-191758.json; SHA256 5fb99fc323a2fec845fe3f4f353464496131ecbdd30af871be5ddc230f427cb7.
- Non-M5 workflow fingerprint unchanged: fe751e1fbffc4e8a6668b648bdf2af4e. M6 v8 / M8 v67 unchanged. Only publisher n8n restarted, as required by publish CLI.
- Full regression 327/327 PASS. NEXT: one controlled en15 lighthouse Gemini smoke on v125; trace exact new job to terminal state. No acceptance claim yet.

## Execution 9788 — bounded timing correction fix, 2026-09-23

- Confirmed routing defect: nearest-word fallback could reuse the exact already-measured failing narration, report success, bypass the existing bounded compliance retry, and spend another TTS call without a text correction.
- Fixed final measured retry/compliance validators: compare joined candidate with saved Probe 4 narration and out-of-window measurement. An unchanged failing draft now raises M5_UNCHANGED_TIMING_DRAFT. The first validator routes that marker to the existing one-shot compliance branch; the compliance validator fails closed if still unchanged. New candidate text still requires actual TTS measurement. No added loop or timing/semantic relaxation.
- Focused execution-9788 regressions 6/6 PASS; full Node suite 327/327 PASS; git diff --check PASS.
- Source includes the previous boundary-duplication fix. Production still M5 v124 active 945c1dd0-900c-4aca-9fbb-b1333a56b0fb; M6 v8 and M8 v67 unchanged. Neither M5 fix deployed yet.
- NEXT: verify zero active publisher executions, back up published M5, deploy only VideoM5Storyboard001 and verify published source; then one controlled Gemini-mode smoke. A passing smoke is not yet claimed.

## Execution 9788 — verified source fix, 2026-09-23

- Confirmed separate narration defect: final measured hybrid combined S4 ending “rotates continuously” from one draft with S5 starting “continuously to guide” from another. Each scene passed its semantic guard, but the joined text repeated “continuously continuously”. This is NOT proof that duplication caused the duration miss.
- Fixed all three exact-word hybrid validators: exclude newly repeated words across scene boundaries during option assembly and reject them in the final joined result; repetitions present at the same original boundary remain permitted. No topic-specific rule, text padding, speech-rate change, or weaker duration gate.
- Saved-data regression: all 3 tests fail on pre-fix HEAD with the exact duplicated phrase and pass after the fix. Full regression now 324/324 PASS; git diff --check PASS.
- Reproducibility defect also fixed: a visual regression depended on ignored .review/pl15-v54/penstock-domain-live.json. Retrieved the existing public Wikimedia query data from VPS, committed it as tests/fixtures/wikimedia-hydroelectric-penstock.json, and pointed the test there. No new provider request or secret copied.
- Duration investigation: original 29-word probe 13224ms; initial stability 12600/12408ms; later 30-word probes 13344/13704/13344ms. Final correction targets were 33 then 32 words; fallback continued with 30. Both provider exact-count retries returned 29 words. Existing nearest-word fallback permitted another under-target synthesis. No accepted audio for this job.
- Production is UNCHANGED: M5 v124 active 945c1dd0-900c-4aca-9fbb-b1333a56b0fb; M6 v8 active 0bcabe39-ae90-42fe-842b-8a56ad238709; M8 v67 active 21599d8f-f0c9-48c8-af86-ba9e297cdd5a. This source fix is NOT deployed. No new job was started.
- NEXT: continue from saved execution 9788; determine why the provider repeats 29 words and why the bounded compliance branch was bypassed by the nearest-word fallback. Reproduce and fix that duration-repair failure without weakening semantic/timing gates or adding blind retry loops. Then deploy tested M5 changes with existing safeguards and run one controlled Gemini smoke. Do not resume old M8 v53 work or repeat the boundary diagnosis.

## Earlier live refresh — production baseline, 2026-09-23

This baseline is superseded by the execution 9788 source-fix checkpoint above.
Refreshed local main from origin/main at 4ae5c3f335166f6b0609b1e102b24c0b89923f01; verified production read-only on 2026-09-23.

- Active production: M5 v124 / 945c1dd0-900c-4aca-9fbb-b1333a56b0fb; M6 v8 / 0bcabe39-ae90-42fe-842b-8a56ad238709; M8 v67 / 21599d8f-f0c9-48c8-af86-ba9e297cdd5a. These counters/activeVersionIds were read directly from n8n.
- Latest controlled Gemini smoke: job 8cd3ffb3-1439-4d21-a0fe-9298f043e4c7, topic “how does a lighthouse work?”, en, 15s. It is TERMINAL script_failed, not still running.
- M3 execution 9785 PASS; M4 9787 PASS; M5 9788 ERROR. Script run 6a4849f6-2548-4ddb-b3f1-f217f22b58cf completed 2026-09-23T20:27:33.165278+02:00.
- Exact failure: “M5 script workflow failed: M5 timing repair still outside target: got 13344ms, target 15000ms, tolerance 800ms”. Execution reached timing probe 5 and Prepare Final Timing Failure 5, then Raise Script Failure. Final audio is 1656ms short (856ms beyond tolerance). The measured duration gate rejected it; the underlying repair/convergence cause is NOT yet diagnosed. No runtime fix made in this checkpoint.
- This job never reached M6–M9; it provides no Gemini pixel-validation or final-media acceptance evidence. The previous precision-count mismatch fix must not be called the cause without inspecting execution 9788.
- NEXT: inspect saved M5 execution 9788 timing/repair outputs, compare accepted narration and measurements across probes, and reproduce the specific failure before changing the duration-repair logic. Use stored evidence first; do not launch another smoke job merely to replace this failed result. After a verified fix, follow targeted deployment safeguards and run one controlled Gemini smoke through M8. Acceptance sequence remains pending.
- Existing implementation includes metadata/gemini visual modes, per-candidate preview failure handling, and exact accepted M5 audio reuse in M6. Preserve these changes. Last recorded full regression: 321/321 PASS before this smoke; not rerun for this documentation-only refresh.
- Old local pre-refresh M8 v53 work was preserved in local stash 103e61a5cf870b25c43f4c51d21b09fb17ff8d31 (“preserve obsolete local M8 v53 WIP before 2026-09-23 main refresh”). It is obsolete, not applied/deployed, and is NOT required to resume from GitHub. Do not apply it over current main.
- Evidence: [live resume checkpoint](acceptance/2026-09-23-resume-smoke-9788.json). No new job, workflow deployment, or production mutation in this checkpoint.

Updated: 2026-09-23

## Source of truth and execution rules

- Repository: `Pokhyl/ai-short-form-content-factory`.
- Branch: `main`.
- VPS path: `/opt/ai-short-form-content-factory`.
- Production n8n: `https://publisher.hodor.com.pl`.
- Studio: `https://studio.hodor.com.pl/`.
- GitHub + actual production state are the source of truth.
- Before every substantive action, read this PLAN and verify that the action matches the current next step.
- After every substantive finding, fix, test result, deploy, acceptance result, or change of direction:
  1. update this PLAN if current state or next step changed;
  2. update detailed handoff/evidence where applicable;
  3. commit and push immediately.
- A change that is not committed/pushed is not a durable project checkpoint.
- Never create a fresh acceptance job while another project execution is active.
- If a tool times out, inspect actual state before retrying.
- Do not touch unrelated workflows, credentials, n8n instances, domains, containers, or jobs.
- User disagreement is not new evidence. Change a technical conclusion only because of new evidence, a new test/tool result, or a specific identified error in the prior reasoning.
- Never claim fixed/deployed/passing without verifying the actual state.

## Product goal

Fully automatic n8n short-form video factory:

topic + language + duration
-> research
-> continuous narration/storyboard
-> exact accepted TTS audio
-> alignment
-> visual retrieval/selection
-> render
-> machine QA
-> final vertical MP4.

Inputs:
- topic
- language: PL / EN / RU / UK
- duration: 15 / 30 / 45 / 60 seconds

Constraints:
- n8n is the mandatory orchestrator.
- Free-only production path.
- No hacks or topic-specific production rules.
- No hardcoded visual asset IDs.
- Draft/inbox publishing only.
- Do not weaken semantic, visual, timing, or QA gates merely to pass acceptance.

## Current production state

Current verified production versions:
- M5 Script/Storyboard: v117
  - activeVersionId: `e368d875-ebae-4c7b-ab38-6683c218a1d4`
- M6 Voiceover: v8
  - activeVersionId: `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 Visuals: v62
  - activeVersionId: `90329f54-40fd-4382-92fd-2fd1e9ecea01`

M5 v111 deployment verification:
- published backup: `.backups/m5-before-anaphoric-20260922-210414.json`
- non-M5 workflow fingerprint unchanged: `31|f28cd4244a334ea2ea539357a3302585`
- live M5 nodes/connections/settings == Git: PASS
- Publisher: 200
- Studio: 200
- n8n restart count: 0
- media worker: healthy, restart count 0

The anaphoric/cross-scene visual fix is now deployed and verified live.

## Proven architecture decisions

### Exact audio handoff M5 -> M6
M5 preserves the exact synthesized MP3 that passed the final duration gate.
M6 reuses that exact file instead of independently synthesizing the same narration again.
This avoids stochastic TTS-duration drift.

### Continuous narration
Narration is continuous.
Scene boundaries are visual/timing cuts and may occur inside a sentence.
Do not require every scene narration segment to be a standalone sentence.

### Visual selection
Visual gates remain fail-closed:
- primary subject must be grounded;
- operational setting must be grounded when required;
- unrelated/museum/component/background false positives remain rejected;
- no topic-specific asset exceptions.

## Latest accepted technical result

Job:
- `345adac7-105e-461b-97ff-1a66789704ba`

Result:
- reached `machine_qa_passed`;
- rendered technically valid MP4:
  - 1080x1920
  - H.264
  - AAC
  - 30 fps
  - 14.800 s

Manual review identified a real cross-scene grounding defect:
- S5 narration `Który wytwarza prąd.` inherited its grammatical subject from the previous generator scene;
- storyboard visual primary incorrectly switched to transformer/substation imagery;
- malformed boundary punctuation such as `turbiny,.` / `generator,.` also appeared.

Evidence:
- `docs/acceptance/2026-09-22-pl15-machine-pass-manual-reject-anaphoric-visual-fix.json`

## Current Git-only fix

The latest M5 fix in Git:
- keeps one continuous narration contract across initial and repair prompts;
- detects relative/personal anaphoric scene starts and requires them to retain the previous concrete visual primary;
- excludes demonstratives that can legitimately introduce a new explicitly named subject;
- normalizes conflicting visual-cut punctuation without changing words or semantic content.

Validation recorded in Git:
- focused scene-segment tests: 9/9 PASS;
- full suite: 260/260 PASS;
- JSON/diff checks: PASS.

This fix is not considered production-complete until deployment and live verification succeed.

## Latest fresh PL15

Job: `8ce87adb-3952-43cb-ab1d-7a1b2d549651`

Verified pipeline state before SentinelX disconnected:
- M5 v111: PASS
- M6 v8: PASS
- M8 v61: PASS
- visual_run `cfb7a60e-ed47-408f-85f9-3bbaa7626648`: PASS
- visual searches: 45/45
- provider results collected: 288
- job status: `machine_qa_passed`

No new acceptance job may be created. This exact PL15 remains the active acceptance artifact until its final MP4 has been manually reviewed.

## Manual acceptance result for current PL15

Job: `8ce87adb-3952-43cb-ab1d-7a1b2d549651`

Technical MP4 checks: PASS
- render execution: `9602`
- render id: `fa9dc976-a76d-40fb-977e-135af4c38e47`
- 1080x1920
- H.264 / yuv420p / 30 fps
- AAC mono 24 kHz
- video duration: 14.933 s
- audio duration: 14.904 s
- duration delta: 29 ms
- full decode: PASS
- render SHA256: `e43b6e1a9e1fa07b84e8675665c2394e09e9b0390c4a71897c04ba66f1b78a66`

Audio/narration checks: PASS
- Whisper transcript matched canonical narration with `global_coverage=1.000`
- alignment method: `whisper_token_sequence_match`
- lexical coverage: 25 tokens
- audio SHA256: `45602fa3cd7d6228d39b862288f3893e7548ca0b24b48e1db23316659869b90c`

Manual visual checks: FAIL
- S1 PASS: dam/reservoir image matches narration.
- S2 FAIL: narration describes a large falling water stream / penstock context; selected frame is a small rocky brook with a thin blue pipe.
- S3 FAIL: narration says water strikes turbine blades directly; selected frame is a general generator/turbine hall and does not show turbine blades.
- S4 FAIL: narration describes the turbine in rapid rotation; selected frame is a static old/museum-like turbine exhibit rather than an operating turbine.
- S5 PASS: electric generator image matches narration.

This PL15 is NOT accepted despite machine QA passing.

## M8 visual-detail fix tested locally

Source evidence:
- job `8ce87adb-3952-43cb-ab1d-7a1b2d549651`
- M8 execution `9601`
- visual_run `cfb7a60e-ed47-408f-85f9-3bbaa7626648`

Demonstrated selection defects:
- S2 selected Pexels `12496885`: generic rocky brook + thin blue tube; intent required powerful falling water through penstock pipes.
- S3 selected Pexels `12270481`: generic turbine/generator hall; intent required turbine runner blades.
- S4 selected Wikimedia `19189428`: Deutsches Museum 1840 turbine; intent required rotating water-turbine shaft in operation.

Root cause:
- `must_show` correctly described the broad primary object, but M8 did not require the specific visible component/detail that distinguished the requested shot from generic subject imagery.

Tested fix:
- infer hard visual-detail anchors only from component terms shared by `visual_intent` and the most-specific first query;
- preserve existing domain/must_show semantics;
- add missing component anchors to effective provider queries without rewriting original query provenance;
- require the same component evidence in scorer metadata;
- treat explicit `in operation` intent as operational context so museum/exhibit imagery conflicts;
- keep generic shots unaffected when no specific component detail is present.

Exact current anchors:
- S2: `penstock + pipe`
- S3: `blade + runner`
- S4: `shaft`

Validation:
- exact 9601 regression tests: PASS;
- focused M8 compatibility tests: 47/47 PASS;
- full suite: 265/265 PASS;
- old deterministic 9229 replay: terminal PASS, provider calls 0, selected assets unchanged:
  - S1 Wikimedia 172815415
  - S2 Wikimedia 39943534
  - S3 Pexels 12270481
  - S4 Wikimedia 34396499
  - S5 Wikimedia 27207173
- old 9229 eligible pool counts unchanged: 1 / 5 / 5 / 8 / 4.

The M8 visual-detail fix is now deployed and verified live.

Production after deploy:
- M5 v111: `31eaa7a9-98d1-44b6-bec6-416ef388753b`
- M6 v8: `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 v62: `90329f54-40fd-4382-92fd-2fd1e9ecea01`

M8 v62 deploy verification:
- published backup: `.backups/m8-before-detail-anchor-20260922-222108.json`
- non-M8 workflow fingerprint before/after: `31|18aedb2a006c96e8033db6f0770b6bee`
- live M8 nodes/connections/settings == Git: PASS
- Publisher 200
- Studio 200
- n8n restart count 0
- media worker healthy, restart count 0

## M5 9617 branch-safe precision fallback deployed

Production:
- M5 v114: `34b07b1f-2b22-4c6c-a68e-54e5e05fab22`
- M6 v8: `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 v62: `90329f54-40fd-4382-92fd-2fd1e9ecea01`

Deploy verification:
- published backup: `.backups/m5-before-branch-safe-20260923-040114.json`
- non-M5 workflow fingerprint before/after: `31|6d5bcd9e4ad7e94f6f9907f52426c741`
- live M5 nodes/connections/settings == Git: PASS
- Publisher 200
- Studio 200
- n8n restart count 0
- media worker healthy, restart count 0

Validation before deploy:
- focused timing 16/16 PASS;
- full suite 268/268 PASS;
- exact 9617 missing-branch regression PASS.

## Latest fresh PL15 result

Job: `94f5e4ff-b6b3-4ebf-b161-98deb3c7bbe7`

Pipeline:
- M4 PASS
- M5 v114 FAIL, execution `9621`
- M6/M8/M9 did not run
- script_run `9279883f-70e2-4d8c-88d8-c40452eddb00`
- terminal reason: `candidate provider usage is not a committed matching M5 TTS call`

Exact root cause:
- accepted MP3 came from probe 3 with usage key `m5-tts-probe:9279883f-70e2-4d8c-88d8-c40452eddb00:3`;
- ledger row 875 for that key is committed and otherwise valid, with `amount=189` characters;
- exact probe-3 TTS narration was 189 characters and contained three malformed visual-cut endings `,.`;
- after TTS, `Canonicalize Final Storyboard` removed those three extra periods and produced a 186-character final narration;
- `register_voiceover_candidate` correctly requires committed usage amount to equal `char_length(final narration)`, so it rejected the 189-character provider usage for the 186-character final text;
- therefore the defect was post-TTS narration mutation, not the ledger or DB validation.

## M5 9621 pre-TTS punctuation canonicalization tested locally

Fix:
- all five `Prepare Timing Probe` nodes clone the storyboard and apply the same deterministic `normalizeVisualCutPunctuation` used by final canonicalization before TTS;
- top-level narration is rebuilt from the normalized scene narrations before `character_count`, usage reservation, and Google TTS;
- stability probes inherit the already-normalized storyboard;
- final canonicalization becomes idempotent with respect to visual-cut punctuation;
- DB candidate/usage validation is unchanged and remains fail-closed.

Exact regression:
- 9621 malformed narration: 189 chars before cleanup;
- normalized narration: 186 chars before TTS;
- every Prepare Timing Probe 1–5 outputs exactly the 186-char canonical narration;
- every `character_count` equals the actual normalized narration length;
- no `,.`, `;.`, or `:.` artifact reaches TTS.

Validation:
- focused exact-audio tests: 8/8 PASS;
- full suite: 269/269 PASS;
- `git diff --check`: PASS;
- workflow JSON parse: PASS.

## M5 v115 pre-TTS punctuation fix deployed and verified

Production:
- M5 v115: `4ec491e1-fb68-4c5e-8125-c6d501e7d48d`
- M6 v8 unchanged
- M8 v62 unchanged
- M9 v1 unchanged

Deployment verification:
- published backup: `.backups/m5-before-pretts-punct-20260923-041956.json`
- non-M5 workflow fingerprint: `31|6d5bcd9e4ad7e94f6f9907f52426c741`, unchanged from v114 checkpoint
- live M5 nodes/connections/settings == Git: PASS
- Publisher 200
- Studio 200
- n8n restart count 0
- media worker healthy, restart count 0
- active project executions after verification: 0

## Latest fresh PL15 result

Job: `fd7d4a16-cb18-4871-b5ba-c53ef2126c63`

Pipeline:
- M4 PASS
- M5 v115 FAIL, execution `9629`
- M6/M8/M9 did not run
- script_run `2a2f9f43-4fd6-4f0b-af2e-6a7cfbcf500b`
- terminal reason: `M5 script workflow failed: 2, allowed 1 [line 216]`

Exact root cause:
- `Repair Final Word Count` returned the immutable original narration exactly;
- that retry itself is semantically valid;
- `Validate Final Word Count Retry` then builds a deterministic word-count hybrid from `retry`, `base`, and `pre_final` scene options;
- those options are inserted into the DP before per-option immutable semantic validation;
- the DP can therefore select a numerically attractive but semantically invalid scene option;
- only after hybrid selection does the node run `assertSemanticPreservation`, which rejected the chosen hybrid with `2, allowed 1`;
- word-count remains guidance; real TTS is the acceptance authority, so semantically invalid options must be excluded before DP rather than poisoning the whole retry.

## M5 9629 semantic-filtered exact-word hybrid tested locally

Fix:
- changed ONLY `Validate Final Word Count Retry`;
- every retry/base/pre_final scene option is validated against the immutable `Normalize Timing Probe` scene before entering deterministic DP;
- semantic-invalid options are excluded before numeric word-count optimization;
- a scene with no semantic-valid option fails closed;
- semantic thresholds, word-count guidance, and real-TTS timing gates are unchanged.

Exact regression:
- job `fd7d4a16-cb18-4871-b5ba-c53ef2126c63`;
- execution `9629`;
- provider retry equal to immutable original remains eligible;
- invalid filler variants cannot re-enter through base/pre_final hybrid choices.

Validation:
- exact 9629 tests: 2/2 PASS;
- full suite: 271/271 PASS;
- workflow JSON parse: PASS;
- `git diff --check`: PASS.

## M5 v116 semantic-filtered exact-word hybrid deployed and verified

Production:
- M5 v116: `64654d56-c7c8-481f-8bd3-37e37cc27289`
- M6 v8 unchanged
- M8 v62 unchanged
- M9 v1 unchanged

Deployment verification:
- published backup: `.backups/m5-before-9629-20260923-052246.json`
- non-M5 workflow fingerprint before/after: `31|6d5bcd9e4ad7e94f6f9907f52426c741`
- live M5 nodes/connections/settings == Git: PASS
- Publisher 200
- Studio 200
- n8n restart count 0
- media worker healthy, restart count 0

## Latest fresh PL15 result

Job: `72af62de-3c64-4b48-bf6b-c1395e07abed`

Pipeline:
- M4 PASS
- M5 v116 FAIL, execution `9633`
- M6/M8/M9 did not run
- script_run `b43017d9-d18f-49ae-9396-9f80ee389826`
- terminal reason: `water reservoir -> penstock pipe [line 696]`

Exact root cause:
- S1 narration ended `... gromadzi wodę,`;
- S2 began `która spada z wysokości.`;
- Polish relative pronoun `która` refers to terminal noun `wodę`, not to the S1 visual primary `water reservoir`;
- `previousVisualPrimaryIsLikelyTerminalAntecedent` tries to locate the English visual primary inside non-English narration;
- when no lexical match is found it currently returns `true` (fail-closed), which incorrectly asserts that the previous visual primary is the antecedent;
- this falsely rejects a legitimate visual transition to falling water / penstock pipe;
- the original generator-anaphora regression remains detectable because `generator` is a real cognate and is positively found at the end of the previous narration.

## M5 9633 cross-language antecedent fix tested locally

Fix:
- changed only the three storyboard validators containing `previousVisualPrimaryIsLikelyTerminalAntecedent`;
- no lexical match between English visual primary and non-English narration now means no inherited-primary restriction;
- positive terminal lexical matches remain fail-closed exactly as before;
- no topic-specific vocabulary or translation table was added.

Exact regression:
- `... gromadzi wodę,` + `która spada...` may move from reservoir visual to penstock/falling-water visual;
- existing generator `Który...` subject-drift regression still rejects visual-primary drift.

Validation:
- focused scene-segment tests: 13/13 PASS;
- full suite: 273/273 PASS;
- workflow JSON parse: PASS;
- `git diff --check`: PASS.

## M5 v117 cross-language antecedent fix deployed and verified

Production:
- M5 v117: `e368d875-ebae-4c7b-ab38-6683c218a1d4`
- M6 v8 unchanged
- M8 v62 unchanged
- M9 v1 unchanged

Deployment verification:
- published backup: `.backups/m5-before-9633-20260923-053041.json`
- non-M5 workflow fingerprint before/after: `31|6d5bcd9e4ad7e94f6f9907f52426c741`
- live M5 nodes/connections/settings == Git: PASS
- Publisher 200
- Studio 200
- n8n restart count 0
- media worker healthy, restart count 0

## Latest fresh PL15 result

Job: `835c8fc3-7d0b-425f-ab9e-62c19788c8a3`

Pipeline:
- M5 v117 PASS
- M6 v8 PASS
- M8 v62 FAIL, execution `9640`
- M9 did not run
- visual_run `27cf596d-0c2f-4e3c-a021-41f6db8a6217`
- terminal: `no compliant relevant visual candidate for shot S3-A`

Observed M8 pools:
- S1: 8 eligible
- S2: 6 eligible
- S3: 0 eligible
- S4: 0 eligible
- S5: 10 eligible

S3 contract:
- narration: `Turbina napędza generator,`
- primary: `electric generator`
- secondary: `turbine machine`
- intent: generator connected to turbine in a power station

S4 contract:
- narration: `Który produkuje prąd.`
- primary: `electrical generator`
- intent: electrical generator/equipment generating electricity inside a plant

Confirmed retrieval root causes:
1. repeated machinery domain inference promotes output/process words such as `electricity` into `domain_context_terms`; this creates a hard metadata gate even though `electricity` is not the machinery domain;
2. provider queries omit structural retrieval terms already implied by the storyboard:
   - two mandatory machinery subjects need a combined `... unit` retrieval form;
   - `inside ... plant/station` needs an `... interior` retrieval form;
3. scorer behavior is correct to reject the currently returned weak/museum/diagram/context-only results.

Live diagnostic evidence (no production mutation):
- generic query `hydroelectric generator turbine unit interior` immediately returned real turbine-generator-unit interiors;
- `hydroelectric generator turbine unit power station` returned turbine-generator units;
- `hydroelectric plant interior generator` returned real generator installations/interiors;
- `hydroelectric power station interior generator` returned generator-room images.
Therefore fix retrieval planning, not QA thresholds.

## M8 9640 retrieval-planning fix validated locally

Scope:
- request planners only;
- scorer and eligibility thresholds unchanged.

Changes:
- generic output/process words `electricity`, `energy`, `current`, `voltage`, `output` are no longer promoted into hard machinery domain context;
- when a shot has 2+ machinery heads, retrieval keeps those machinery heads and adds `unit` as provider-query structure only;
- for a repeated output-focused machinery scene explicitly inside/interior an operating location, retrieval prefixes the location plus `interior`; these are not hard scorer domains;
- original storyboard `query` provenance is unchanged.

Exact 9640 generated queries:
- S3 q3: `hydroelectric generator turbine unit`
- S4 q3: `hydroelectric plant interior electrical generator`

Validation:
- focused 9640 planner regressions: 10/10 PASS;
- full suite: 283/283 PASS;
- deterministic M8 execution 9229 replay: PASS with the same five accepted assets;
- live non-mutating Wikimedia + current scorer:
  - S3 q3: 2 eligible assets, IDs `33715545`, `33715543`;
  - S4 q3: 2 eligible assets, IDs `33760010`, `34186551`.
- no production mutation has occurred yet.

## M8 v63 deployed and verified

- M8 v63 activeVersionId `7256ee89-8b9a-47df-bdc9-66bd2136df35`.
- M5 v117 / M6 v8 / M9 v1 unchanged.
- Published backup: `.backups/m8-before-9640-20260923-060948.json`.
- Non-M8 workflow fingerprint unchanged:
  `31|32241746eba2f4470b60db4bebbf74f3`.
- Live M8 nodes/connections/settings == Git: PASS.
- Publisher 200; Studio 200.
- n8n running, restart 0.
- media worker healthy, restart 0.

## Latest fresh PL15 failure — M5 execution 9660

Job: `6aa86246-ec15-4514-a688-d150129d35ad`

- M5 production version: v117 / `e368d875-ebae-4c7b-ab38-6683c218a1d4`.
- M5 execution: `9660`.
- script_run: `a5985b2f-c8b6-4342-9ea9-57b00f9a2f35`.
- Terminal job state: `script_failed`.
- Failure: `final measured word-count retry too far from target before TTS: got 26, target 29, allowed delta 2`.

Verified timing evidence for the final 26-word narration:
- Probe 4: 12.984 s
- Stability A: 13.200 s
- Stability B: 13.128 s
- PL15 final M6 lower timing bound is approximately 14.2 s, so allowing 26 words through would be an invalid weakening of the gate.

Verified provider-contract failure:
- measured correction correctly requested LONGER / about 29 words;
- hard exact retry required total 29 with scene targets `[10,6,4,4,5]`;
- Gemini 3.5 Flash Lite returned only 22 words with counts `[8,4,3,3,4]`;
- deterministic semantic hybrid could recover only 26 words, still 3 short;
- therefore current validator correctly failed closed.

Current blocker is not TTS stochasticity and not the timing tolerance. It is non-compliance of the bounded final exact-word Gemini retry.

## M5 execution 9660 fix implemented and tested

Implemented:
- existing final exact-word validator still fails closed when the semantic-valid nearest total is too far from target;
- only that exact `too far from target before TTS` error is classified for one extra bounded compliance retry;
- all provider/parse/semantic errors continue to script failure;
- compliance retry receives previous returned total/per-scene counts, immutable original narration, current semantic-valid narration, exact hard total and exact hard per-scene counts;
- compliance retry cannot loop: its validator success goes to existing Probe 5 and its error goes directly to script failure.

Execution 9660 deterministic regression:
- previous Gemini response detected as 22 words with [8,4,3,3,4];
- required counts [10,6,4,4,5], total 29;
- semantic-valid exact 29-word response passes the same final validator;
- repeated noncompliant 22-word response still fails closed.

Validation:
- focused compliance/provider tests: 10/10 PASS;
- full project suite: 288/288 PASS;
- M5 graph validation: PASS, 132 nodes;
- M5 Code-node syntax: 59/59 PASS;
- `git diff --check`: PASS;
- M5 JSON parse: PASS.

## M5 v118 compliance fix deployed and verified

Production:
- M5: v118 / `346ad9c2-1cc2-4c8d-ac37-6ae540b1fff1`
- M6: v8 / `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8: v63 / `7256ee89-8b9a-47df-bdc9-66bd2136df35`
- M9: v1 / `5b6c937c-1767-4c3e-99c4-31ea38a26961`

Deploy verification:
- published backup: `.backups/m5-before-9660-compliance-20260923-083302.json`
- non-M5 fingerprint before/after: `31|c27d87623ffd8872701cef34695d8265`
- live M5 nodes/connections/settings == Git: PASS
- Publisher 200
- Studio 200
- n8n running, restart count 0
- media worker healthy, restart count 0

## Fresh PL15 manual acceptance failure — execution 9672

Job: `ab79e346-a7d7-45c4-9bc9-a82212bab1c4`

Pipeline:
- M4 execution 9671: PASS
- M5 execution 9672 on v118 `346ad9c2-1cc2-4c8d-ac37-6ae540b1fff1`: PASS
- M6 execution 9673 on v8: PASS
- M7 execution 9674: PASS
- M8 execution 9675 on v63: PASS
- M9 execution 9676 on v1: PASS
- job status: `machine_qa_passed`

Technical render: PASS
- 1080x1920
- H.264 / yuv420p / 30 fps
- AAC mono 24 kHz
- duration 15.066667 s
- full decode clean

Lexical alignment: PASS
- global coverage 1.000
- 23 lexical tokens
- audio duration 15.048 s
- alignment method `whisper_token_sequence_match`

Manual narration/audio continuity: FAIL
- final canonical narration contains artificial sentence breaks at visual cuts:
  - `Spadająca masa cieczy napędza. Turbinę wodną...`
  - `...która następnie. Porusza generator...`
- silence detection on the actual final MP3 found internal pauses including approximately 0.776 s, 0.458 s and 0.992 s around these scene boundaries.

Exact root cause from M5 execution 9672:
- `Validate Storyboard` and `Normalize Timing Probe` preserved one natural continuous narration with mid-sentence visual cuts.
- Gemini `Repair Timing Precision Retry` also returned the correct segment surfaces without added periods:
  - `Elektrownia wodna gromadzi wodę`
  - `w wielkim zbiorniku za tamą.`
  - `Spadająca masa cieczy napędza`
  - `turbinę wodną, która następnie`
  - `porusza generator wytwarzający czysty prąd elektryczny.`
- `Validate Timing Precision Retry` then called `normalizeSentenceSurface`, which uppercased every segment start and appended a terminal period to every segment.
- This validator behavior contradicts the continuous-narration/visual-cut contract.
- Search of current M5 code found this forced sentence-surface normalization only in `Validate Timing Precision Retry`.

## M5 execution 9672 continuity fix implemented and tested

Implemented only in `Validate Timing Precision Retry`:
- removed forced capitalization of every visual segment start;
- removed forced terminal punctuation on every visual segment;
- each segment now receives whitespace normalization only;
- existing semantic fallback/anti-runaway checks remain unchanged;
- existing joined narration completeness gate remains unchanged.

Exact execution 9672 regression proves:
- Gemini precision response keeps mid-sentence visual cuts:
  - `Elektrownia wodna gromadzi wodę`
  - `w wielkim zbiorniku za tamą.`
  - `Spadająca masa cieczy napędza`
  - `turbinę wodną, która następnie`
  - `porusza generator wytwarzający czysty prąd elektryczny.`
- validator output preserves these exact surfaces;
- joined narration equals the original continuous narration;
- artificial `napędza. Turbinę` and `następnie. Porusza` breaks are absent.

Validation:
- focused continuity/precision/scene tests: 18/18 PASS;
- full project suite: 290/290 PASS;
- M5 graph: PASS, 132 nodes;
- M5 Code-node syntax: 59/59 PASS;
- diff/JSON checks: PASS.

## M5 v119 continuity fix deployed and verified

Production:
- M5: v119 / `bad8d367-3399-4ada-87c4-3a6d6c044b62`
- M6: v8 / `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8: v63 / `7256ee89-8b9a-47df-bdc9-66bd2136df35`
- M9: v1 / `5b6c937c-1767-4c3e-99c4-31ea38a26961`

Deploy verification:
- published backup: `.backups/m5-before-9672-continuity-20260923-085258.json`
- non-M5 fingerprint before/after: `31|c27d87623ffd8872701cef34695d8265`
- live M5 nodes/connections/settings == Git: PASS
- Publisher 200
- Studio 200
- n8n restart count 0
- media worker healthy, restart count 0

## Immediate next step

1. Read PLAN before the next production action.
2. Verify Git clean and active project executions = 0.
3. Run exactly ONE fresh PL15 on M5 v119 / M6 v8 / M8 v63 / M9 v1.
4. Follow only that job to terminal state.
5. If machine QA passes:
   - inspect actual final MP4 technically;
   - verify canonical narration remains continuous;
   - inspect actual audio silence/pause structure;
   - review every visual scene against narration.
6. If PL15 passes manual acceptance, checkpoint GitHub and proceed to EN30.
7. If it fails, record and fix only the exact demonstrated blocker; no parallel job.

## Acceptance sequence after PL15

Only after PL15 passes full manual acceptance:

1. EN30 — `how do bees make honey?`
2. RU45 — `как работает GPS?`
3. UK60 — `як утворюються вулкани?`

Run sequentially, never in parallel.

For each:
- complete production path must pass;
- technical MP4 checks must pass;
- actual final output must be manually reviewed;
- only demonstrated defects may be fixed.

## Definition of done

The project is done only when PL15 + EN30 + RU45 + UK60 all pass the complete production path and actual rendered outputs pass:

- requested timing window;
- 1080x1920 vertical output;
- H.264 / yuv420p / 30 fps;
- AAC audio;
- successful full decode;
- continuous natural narration;
- scene/visual semantic match;
- no missing/broken visual;
- no invalid-domain imagery;
- no semantic subject drift across scene cuts;
- actual final MP4 manually reviewed.

After all four pass:
- freeze M5/M6/M8/M9 production versions;
- record final evidence;
- create final Git checkpoint/tag;
- stop development.

## Fresh PL15 v119/v63 failure — M8 execution 9683

Job: `a6d8d4dc-c30c-41ef-b816-0301fdfd1cda`

Pipeline:
- M4 PASS
- M5 execution 9680 on v119: PASS
- M6 execution 9681 on v8: PASS
- M7 execution 9682: PASS
- M8 execution 9683 on v63: FAIL
- M9 did not run
- visual_run: `02a9de5e-17f1-49b1-b51b-e575ef1d0bc4`

Eligible pools:
- S1: 10
- S2: 2
- S3: 2
- S4: 0
- S5: 3

Exact S4:
- narration: `który produkuje prąd,`
- visual intent: `electric power generation equipment in hydro plant`
- must_show: `electric generator`
- provider searches completed 9/9 for S4.

Demonstrated valid-context candidate:
- Wikimedia `135264822`
- direct caption states Wienerbruck hydro power plant / Generator 2 / `in working condition`
- category includes `Hydroelectric generators`
- current scorer: 81, rejected only for `missing_operational_setting_context`.

Confirmed code defect:
- Wikimedia intentionally exposes a short direct caption through secondary/context metadata;
- operational-setting validation checks only `strongSet` (title/object/categories);
- therefore explicit plant/working-condition context in the direct caption is ignored.
- Primary depiction gates are not the problem and must not be weakened.

Next:
1. Add exact 9683 positive regression and a `disused` negative.
2. Use combined strong + secondary metadata only for operational location/lifecycle evidence.
3. Keep primary subject, must_show, domain, thresholds and retrieval unchanged.
4. Focused tests -> full suite -> deterministic 9229 replay -> diff/JSON checks.
5. No new PL15 before fix is tested, checkpointed and deployed.


## M8 execution 9683 operational-context fix validated

Scoped fix:
- operational context/lifecycle checks now use an explicit `contextSet`;
- Pixabay and Pexels keep their previous operational-context evidence source (`strongSet`);
- Wikimedia alone combines `strongSet` with the already-existing concise direct-caption/secondary metadata;
- primary depiction, must_show, domain context, visual-detail and relevance thresholds are unchanged;
- `disused/decommissioned/abandoned/inactive/retired` are explicit non-operational lifecycle conflicts.

Exact regression:
- Wikimedia `135264822` with direct caption `hydro power plant ... in working condition` now satisfies the S4 operational setting;
- equivalent metadata marked `disused` is rejected;
- caption-only mention of a generator still cannot prove the primary depicted subject.

Validation:
- focused operational/context + 9601 + 9640 tests: 42/42 PASS;
- full suite: 293/293 PASS;
- deterministic 9229 replay: 12/12 PASS;
- selected 9229 assets unchanged: 172815415 / 39943534 / Pexels 12270481 / 34396499 / 27207173;
- 9229 eligible counts unchanged: 1 / 5 / 5 / 8 / 4;
- M8 Code nodes: 10/10 syntax PASS;
- workflow JSON parse: PASS;
- `git diff --check`: PASS.

Next:
1. Commit/push this tested M8 fix.
2. Verify active project executions = 0.
3. Export published M8 backup and capture non-M8 fingerprint.
4. Deploy only M8; version must increment exactly once.
5. Verify live M8 == Git, non-M8 fingerprint unchanged, Publisher/Studio 200, containers healthy, no restart.
6. Then run exactly one fresh PL15.


## M8 v64 operational-context fix deployed and verified

Production:
- M5 v119 / `bad8d367-3399-4ada-87c4-3a6d6c044b62`
- M6 v8 / `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 v64 / `88b9f81a-6d41-452b-8a35-082b7c088006`
- M9 v1 / `5b6c937c-1767-4c3e-99c4-31ea38a26961`

Deploy verification:
- M8 version incremented exactly once: v63 -> v64.
- Published backup: `.backups/m8-before-9683-context-20260923-123042.json`.
- Backup SHA256: `f535079c5f3ff6f538fc29c20c4a3635a106707227e76a7d3567c28d6ae5fd47`.
- non-M8 fingerprint before/after unchanged: `31|935f3b89581cc695b22bca91b315f846`.
- live M8 nodes/connections/settings == Git: PASS.
- Publisher 200; Studio 200.
- n8n running, restart count 0.
- media worker running/healthy, restart count 0.
- Postgres and SearXNG healthy.
- active project executions after verification: 0.
- no unrelated workflow, credential, service or container changed.

## Immediate next step after M8 v64

1. Verify Git clean and active project executions = 0.
2. Run exactly ONE fresh PL15:
   - topic: `jak działa elektrownia wodna?`
   - language: `pl`
   - duration: 15
3. Follow only that job to terminal state.
4. If it reaches machine QA, inspect the exact final MP4 technically, audio/narration continuity and S1-S5 visual correspondence.
5. If PL15 passes manual acceptance, checkpoint and proceed to EN30.
6. If it fails, checkpoint the exact blocker before any new fix; do not start another PL15.


## Fresh PL15 on M5 v119 / M8 v64 — M5 execution 9687 failed

Job: `bfac49a7-bde2-4ec0-85fc-7dd9b6afbc36`

Pipeline:
- M4 PASS
- M5 v119 execution `9687`: FAIL
- M6/M7/M8/M9 did not run
- script_run: `e0bed2f3-7cce-4004-83b9-ced1db6b75de`
- terminal job status: `script_failed`

Exact failure:
- `got 27, target 31, allowed delta 2 [line 431]`.

Execution-tail evidence:
- final measured correction ran;
- final measured word-count retry ran;
- `Classify Final Measured Word Count Retry Failure` ran;
- `Route Final Measured Word Count Compliance Retry` ran;
- no Build/Repair/Validate compliance-retry node executed;
- execution routed to Prepare Script Failure -> Fail Script -> Raise Script Failure.

No root cause is claimed yet.

Immediate next step:
1. Inspect exact 9687 classifier/router data and the v119 classifier conditions.
2. Prove why the bounded compliance retry was not entered for 27 vs target 31.
3. Record the proven root cause before changing M5.
4. Do not start another PL15.


## M5 execution 9687 — root cause proven

Production evidence:
- classifier input carried `$json.error` as the string:
  `got 27, target 31, allowed delta 2 [line 431]`;
- raw execution ref for that value: `1684`;
- `Classify Final Measured Word Count Retry Failure` output:
  - `compliance_retry=false`
  - `compliance_retry_error_message=""` (raw ref `857`).

Confirmed code defect:
- classifier only treats `$json.error` as usable when it is an object;
- string-form n8n errors are discarded before classification;
- therefore the existing bounded compliance retry was skipped even though the failure came from the final measured word-count retry path.

Fix scope:
1. Normalize string-form and object-form `$json.error`.
2. Keep the existing retry class narrow; do not retry arbitrary M5 failures.
3. Add exact regression for execution 9687 string-form error.
4. Focused tests, full suite, diff/JSON/Code-node checks.
5. Checkpoint before M5-only deploy.
6. No new PL15 until fix is tested and deployed.


## M5 execution 9687 classifier fix validated

Change:
- `Classify Final Measured Word Count Retry Failure` now normalizes both object-form and string-form `$json.error`;
- the old full retry message still qualifies;
- n8n's stripped string form qualifies only when it exactly matches `got <N>, target <N>, allowed delta <N> [line <N>]`;
- unrelated string errors such as provider 503 remain non-retry failures;
- no retry loop was added and no timing/semantic validator was weakened.

Validation:
- focused compliance/provider tests: 10/10 PASS;
- full suite: 293/293 PASS;
- M5 Code nodes: 59/59 syntax PASS;
- workflow JSON parse: PASS;
- `git diff --check`: PASS.

Next:
1. Commit/push this tested M5 fix.
2. Verify active project executions = 0.
3. Export published M5 v119 backup and capture non-M5 workflow fingerprint.
4. Deploy only M5 and publish current version; expect exactly v120.
5. Verify live M5 nodes/connections/settings == Git; non-M5 fingerprint unchanged; Publisher/Studio 200; no container restart.
6. Run exactly one fresh PL15 and follow it to terminal state.


## M5 v120 classifier fix deployed and verified

Production:
- M5 v120 / `28f7440c-9410-4143-8962-352f967cfe1f`
- M6 v8 / `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 v64 / `88b9f81a-6d41-452b-8a35-082b7c088006`
- M9 v1 / `5b6c937c-1767-4c3e-99c4-31ea38a26961`

Deploy verification:
- M5 incremented exactly once: v119 -> v120.
- Published backup: `.backups/m5-before-9687-classifier-20260923-131636.json`.
- Backup SHA256: `4a512505d75848a7f432cf4dc328bd0f5113c502f877ff0d19cbd6661402c50e`.
- non-M5 fingerprint unchanged: `31|cfacbe4e094739b106490c3c93ec2506`.
- live M5 nodes/connections/settings == Git: PASS.
- Publisher 200; Studio 200.
- n8n running, restart 0.
- media worker running/healthy, restart 0.
- Postgres and SearXNG healthy.
- active project executions = 0.

Immediate next step:
1. Verify Git clean and active project executions = 0.
2. Run exactly ONE fresh PL15 on v120/v64.
3. Follow only that job to terminal state.
4. If it reaches M9 machine PASS, perform exact MP4 technical/audio/visual review before EN30.
5. If it fails, checkpoint the exact new blocker before any new fix or retry.


## Fresh PL15 on M5 v120 — execution 9692 failed; root cause proven

Job: `4dc1af7d-0ec9-4af5-8557-e926beef4cac`

Pipeline:
- M4 PASS
- M5 v120 execution `9692`: FAIL
- M6/M7/M8/M9 did not run
- script_run: `50024835-3e15-4405-b33c-6fa5ef2cec3a`
- terminal error: `11 [line 251]`

Exact final-duration evidence:
- measured TTS: 12096 ms
- target: 15000 ms
- internal repair aim: 14600 ms
- current narration: 22 words
- target narration: about 27 words
- builder target scene counts: `[10,5,4,3,5]`
- validator PL15 hard scene bound: 2-10 words
- Gemini returned scene counts: `[11,7,5,7,6]`
- S1 response had 11 words.

Confirmed contract defect:
- `Build Final Duration Repair` correctly clamps calculated scene targets to max 10;
- its prompt then says every per-scene `target_words` is only a preference and does not state the hard 2-10 scene bound;
- Gemini therefore produced S1 with 11 words;
- `Validate Final Duration Repair` correctly rejected it at the hard max check.

Fix scope:
1. Keep per-scene target_words as soft timing guidance.
2. Add explicit HARD structural rule: every returned scene must remain within 2-`maxSceneWords` words.
3. Do not weaken validator, semantic preservation, timing or sentence-continuity gates.
4. Add exact 9692 regression.
5. Focused/full tests, JSON/diff/Code-node checks.
6. Checkpoint before M5-only deploy; no new PL15 before deploy.


## M5 execution 9692 late-timing scene-bound fix validated

Change:
- `Build Final Duration Repair` and `Build Final Measured Correction` now explicitly state a HARD per-scene structural bound;
- for PL15 every returned narration segment must remain within 2-10 whitespace-separated words;
- per-scene `target_words` remain soft timing guidance inside that hard bound;
- validator, semantic preservation, timing acceptance and narration-continuity rules are unchanged.

Validation:
- focused late-timing + semantic tests: 37/37 PASS;
- full suite: 294/294 PASS;
- M5 Code nodes: 59/59 syntax PASS;
- workflow JSON parse: PASS;
- `git diff --check`: PASS.

Next:
1. Commit/push this tested M5 fix.
2. Verify active project executions = 0.
3. Export published M5 v120 backup and capture non-M5 fingerprint.
4. Deploy only M5; expect exactly v121.
5. Verify live M5 == Git, non-M5 fingerprint unchanged, Publisher/Studio 200, no restart.
6. Run exactly one fresh PL15 and follow it to terminal state.


## M5 v121 late-timing scene-bound fix deployed and verified

Production:
- M5 v121 / `692ceedd-a51c-45c5-bf1e-c85814129e4d`
- M6 v8 / `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 v64 / `88b9f81a-6d41-452b-8a35-082b7c088006`
- M9 v1 / `5b6c937c-1767-4c3e-99c4-31ea38a26961`

Deploy verification:
- M5 incremented exactly once: v120 -> v121.
- Backup: `.backups/m5-before-9692-scene-bound-20260923-133216.json`.
- Backup SHA256: `92098a8015c357dfb373dba9f2f84899e22f0913e85401369c12f238183e9f51`.
- non-M5 fingerprint unchanged: `31|cfacbe4e094739b106490c3c93ec2506`.
- live M5 nodes/connections/settings == Git: PASS.
- Publisher 200; Studio 200.
- n8n restart 0; media worker healthy restart 0.
- Postgres/SearXNG healthy.
- active project executions = 0.

Immediate next step:
1. Verify Git clean and active project executions = 0.
2. Run exactly ONE fresh PL15 on v121/v64.
3. Follow only that job to terminal state.
4. If machine QA passes, inspect exact MP4 technically and manually before EN30.
5. If it fails, checkpoint the exact blocker before any new change.


## Fresh PL15 on M5 v121 — execution 9699 blocker checkpoint

Job: `d0d127b8-c70a-4cef-b3ae-1dc2cc43e104`

Pipeline:
- M4 PASS
- M5 v121 execution `9699`: FAIL
- M6/M7/M8/M9 did not run
- script_run: `b97c46b5-0b89-47de-a14d-1879eaffe669`

Exact sequence:
- initial storyboard rejected: `electric generator -> power lines [line 698]`
- first repair rejected: `electric generator -> transformer station [line 698]`
- second repair rejected: `electric generator -> electrical substation [line 698]`
- final failing node: `Validate Repaired Storyboard 2`

Scene context:
- S4 narration: `Obracający się wirnik porusza generator,`
- S4 primary: `electric generator`
- S5 narration: `który wytwarza czystą energię elektryczną.`
- S5 does not explicitly name a new concrete visual primary.
- The validator is correct: the likely inherited primary is the generator.

Confirmed repair-path defect:
- all three model attempts violate the existing anaphoric visual-primary contract;
- Repair 2 received only the stripped diagnostic `electric generator -> transformer station [line 698]`;
- n8n removed the descriptive validator prefix, leaving an opaque `A -> B [line N]` message;
- the validator must remain fail-closed.

Candidate fix scope:
- normalize stripped `A -> B [line N]` errors in both storyboard repair builders into an explicit generic anaphoric visual-primary diagnosis;
- no generator/substation/hydropower hardcoding;
- no validator weakening.

Shared working-tree note:
- a parallel process has already placed an uncommitted candidate implementation and regression test in the working tree;
- do not overwrite it;
- validate it before fix commit/deploy.

Next:
1. Commit this docs/evidence blocker checkpoint only.
2. Run focused regression tests on the existing candidate fix.
3. Run full suite, JSON/diff/M5 Code-node checks.
4. If all PASS, record tested fix, commit/push code+test+docs.
5. M5-only deploy after zero-active check/backup/fingerprint.
6. No new PL15 before verified deploy.


## M5 execution 9699 repair-error normalization validated

Implemented only in `Build Storyboard Repair` and `Build Storyboard Repair 2`:
- stripped anaphoric validator diagnostics are expanded into an explicit antecedent-preservation repair instruction;
- unrelated validation errors pass through unchanged;
- no topic-specific vocabulary;
- storyboard validators and fail-closed gates are unchanged.

Validation:
- focused scene/visual tests: 35/35 PASS;
- full suite: 295/295 PASS;
- M5 Code nodes: 59/59 syntax PASS;
- workflow JSON parse: PASS;
- `git diff --check`: PASS.

Next: commit/push the tested fix, then M5-only deploy with zero-active check, backup and non-M5 fingerprint. No new PL15 before verified deploy.


## M5 v122 repair-error normalization deployed and verified

Production:
- M5 v122 / `4a9a48fd-985c-4f77-b592-44a0945377dd`
- M6 v8 / `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 v64 / `88b9f81a-6d41-452b-8a35-082b7c088006`
- M9 v1 / `5b6c937c-1767-4c3e-99c4-31ea38a26961`

Deploy verification:
- M5 incremented exactly once: v121 -> v122.
- Equivalent published predeploy backups:
  - `.backups/m5-before-9699-repair-error-20260923-135152.json`
  - `.backups/m5-before-9699-anaphoric-20260923-135204.json`
- Both backups SHA256: `a7ff82d9608b05cd8648d856dd9f2023adcd7208dd47d55f1f4cb814a4f20628`.
- live M5 nodes/connections/settings == Git: PASS.
- non-M5 fingerprint unchanged: `31|cfacbe4e094739b106490c3c93ec2506`.
- Publisher 200; Studio 200.
- n8n running, restart 0.
- media worker running/healthy, restart 0.
- Postgres/SearXNG healthy.
- active project executions = 0.

Immediate next step:
1. Verify Git clean and active project executions = 0.
2. Run exactly ONE fresh PL15 on v122/v64.
3. Follow only that job to terminal state.
4. If machine QA passes, inspect the exact MP4 technically and manually before EN30.
5. If it fails, checkpoint the exact new blocker before any new change.


## Fresh PL15 v122/v64 — machine PASS, manual visual FAIL

Job: `e8d662c9-cd28-4228-9169-6ac875ff0d16`

Pipeline:
- M4 execution 9702 PASS
- M5 v122 execution 9703 PASS
- M6 v8 execution 9704 PASS
- M7 execution 9705 PASS
- M8 v64 execution 9706 PASS
- M9 v1 execution 9707 PASS
- job status: `machine_qa_passed`

Final MP4:
- `/data/renders/e8d662c9-cd28-4228-9169-6ac875ff0d16/final.mp4`
- SHA256 `c5c889531ab2f90a7ec57b6be2eeed4439aa3ae32f0ad297a18d793755781e4f`
- 1080x1920, H.264 + AAC, 30 fps
- video/audio duration: 14496 ms / 14496 ms
- Whisper review matches the intended continuous Polish narration.

Manual visual review:
- S1 dam/reservoir: relevant.
- S2 concrete dam: relevant.
- S3 hydro machinery/turbine hall: relevant.
- S4 hydro generator: relevant.
- S5 power grid: relevant.
- BUT all five still images are letterboxed vertically instead of filling the 9:16 frame.

Measured content crops from the actual rendered MP4:
- S1: `crop=1080:1620:0:150`
- S2: `crop=1080:1384:0:268`
- S3: `crop=1080:1698:0:110`
- S4: `crop=1080:720:0:600`
- S5: `crop=1080:1820:0:50`

S4 is the clearest failure: only 720 of 1920 vertical pixels contain the photo; the rest is black bars.

Manual acceptance: FAIL.

Next:
1. Inspect M9/media-worker still-image scaling.
2. Fix generic still-image rendering to fill 1080x1920 without distortion, using safe crop rather than black-bar contain.
3. Keep all existing machine QA and semantic/visual gates.
4. Add regression for landscape/square stills rendered to 9:16.
5. Full tests + deterministic render check.
6. Deploy only the responsible render component/workflow.
7. Then run exactly one fresh PL15.


## Render letterbox root cause and safe fill strategy

Confirmed current renderer:
- `_render_segment` uses proportional `force_original_aspect_ratio=decrease`;
- then pads to 1080x1920 with `color=black`;
- this exactly explains the manual cropdetect/letterbox failure.

Do NOT simply restore hard center crop:
- historical PL15 v44 manual review already documented that center-crop removed important edge content from selected visuals;
- commit `fbce953` intentionally switched from center crop to full-source fit for that reason.

Updated fix strategy:
1. Preserve the complete source as a proportional foreground.
2. Fill the entire 1080x1920 background with a center-cropped copy of the same source.
3. Blur the fill background so it does not compete with the foreground.
4. No black padding and no foreground distortion.
5. Update `render-fit-regression.py` to require both edge-landmark preservation and non-black full-frame fill.
6. Keep machine QA, provenance, audio and semantic/visual gates unchanged.


## Blurred-fill still-image renderer fix validated

Implemented:
- still-image foreground remains complete and proportional;
- the same source fills 1080x1920 behind it using cover + center crop + Gaussian blur;
- black padding is removed;
- hard foreground crop is not reintroduced;
- video-media branch is unchanged in this scoped fix.

Regression:
- real FFmpeg `render-fit-regression.py`: 3/3 PASS for 1600x1611, 1920x1080 and 1080x1920;
- synthetic left/right edge landmarks remain visible;
- top/bottom fill probes are non-black.

Exact failed PL15 assets rendered offline with the candidate:
- S1 `crop=1080:1920:0:0`
- S2 `crop=1080:1920:0:0`
- S3 `crop=1080:1920:0:0`
- S4 `crop=1080:1920:0:0`
- S5 `crop=1080:1920:0:0`
- manual S2/S4 spot-check confirms complete foreground preserved with blurred fill and no black bars.

Validation:
- Python compile PASS;
- render-fit regression PASS;
- full Node suite 295/295 PASS;
- `git diff --check` PASS.

Next:
1. Commit/push tested renderer + regression + evidence.
2. Capture current media-worker image/health and build only media-worker.
3. Recreate only `shorts-v2-media-worker-1`.
4. Verify running/healthy, restart count, image/source match, supporting services unchanged.
5. Run exactly one fresh PL15 and manually review the actual final MP4.


## Blurred-fill media-worker deployed and verified

Deployment:
- only Compose service `media-worker` rebuilt/recreated;
- old image: `sha256:74433bc72ce63976434949c8c5144bf6f79596adb689d381db4155191b741220`;
- new image: `sha256:40d31f96de302b8bf0f69bd07e5d9dac2d82a8ed8e102fc0a1c383ea4129fd3c`;
- rollback image recorded in `.backups/worker-before-blurred-fill-20260923-141837.txt`.

Verification:
- worker running / healthy / restart 0;
- live `/worker/server.py` SHA256 matches Git exactly: `c6ee183981d45283f99f52a835906a9546af9bdba9fdf2b71ca672c97a2fae91`;
- Postgres, SearXNG and n8n container IDs unchanged;
- active project executions = 0;
- Publisher 200; Studio 200;
- Git clean and HEAD == origin/main.

Immediate next:
1. Commit/push this deploy checkpoint.
2. Run exactly ONE fresh PL15.
3. Follow only that job to terminal state.
4. If machine QA passes, inspect exact final MP4 frames, cropdetect and audio before deciding acceptance.
5. If PL15 passes manual acceptance, checkpoint and proceed to EN30.


## Fresh PL15 after blurred-fill deploy — machine PASS, manual visual FAIL

Job: `33aa659d-e6b6-4529-8e41-8dd830f3b920`

Pipeline:
- M3 9708 PASS
- M4 9710 PASS
- M5 v122 9711 PASS
- M6 v8 9712 PASS
- M7 9713 PASS
- M8 v64 9714 PASS
- M9 v1 9715 PASS
- status: `machine_qa_passed`

Final MP4:
- SHA256 `f042e93193ad9a64b97299bc095d4e1b94388658a0143bb7519ec90570749379`
- 1080x1920 H.264/AAC, 30 fps
- duration/audio: 14784 / 14784 ms.

Renderer/manual format check:
- blurred-fill fix works on the actual production MP4;
- cropdetect: S1 1080x1900, S2-S5 1080x1920;
- S1's remaining dark edge is embedded in the historical source itself, not renderer black padding;
- no previous top/bottom letterbox behavior remains.

Audio manual check: PASS.
Whisper:
`Woda gromadzona jest w wielkim zbiorniku za tamą. Następnie spada z dużej wysokości, uderzając bezpośrednio w turbinę wodną, która napędza nowoczesny generator wytwarzający czysty prąd elektryczny.`

Visual manual check:
- S1 Wikimedia 124944982: FAIL. Historical small dam/weir scene does not visibly establish the requested large reservoir behind the dam.
- S2 Wikimedia 81510447: PASS. Clear hydro penstock pipes.
- S3 Pexels 12270481: PASS. Industrial hydro machinery.
- S4 Wikimedia 34522651: PASS. Hydroelectric generator bay / turbine-generator shaft.
- S5 Wikimedia 136934049: FAIL. Actual photo shows a forest clearing/survey tripod; no transformer or transformer station is visibly depicted. Transformer/substation/transmission terms are catalog/contract context, not the photographed subject.

Manual acceptance: FAIL.

Confirmed progress:
- render letterboxing is fixed in production;
- remaining blocker is M8 depiction grounding for contextual Wikimedia catalog metadata.

Next:
1. Inspect exact Wikimedia M8 strong/secondary metadata construction for selected 124944982 and 136934049.
2. Prove why contextual title/catalog terms satisfy primary subject.
3. Tighten generic depiction grounding only; no asset IDs, hydro terms or topic-specific blacklists.
4. Add exact regressions for contextual/catalog title false positives while preserving direct descriptive title/photo positives.
5. Full tests + deterministic 9229 and current regressions.
6. M8-only deploy, then one fresh PL15.


## 2026-09-23 — selectable visual validation mode

Product decision:
- Studio exposes a user-selectable visual validation mode for each job.
- `metadata` mode keeps the current deterministic M8 metadata/scoring path and does not call Gemini Vision.
- `gemini` mode adds pixel-level validation of selected visual candidates before they become final scene assets.
- Do not intentionally degrade `metadata` mode; it is the lower-cost path with less semantic assurance.
- Gemini must validate still frames/images, not the complete rendered video.
- Gemini validation input is limited to the candidate image plus the scene contract (`visual_intent`, `must_show`, and relevant exclusions).
- Gemini mode is bounded to at most 3 candidate images per scene and validates them in one Gemini request per scene. This reduces request-rate usage while still allowing deterministic fallback among approved candidates; no unbounded retries.
- Existing deterministic metadata/scoring remains the retrieval/pre-filter layer in both modes.
- The mode must persist with the job from Studio/intake through M8 so behavior is explicit and reproducible.
- No new acceptance job until implementation, regression tests, deployment, and live verification are complete.

Implementation order:
1. Persist `visual_validation_mode = metadata | gemini` on the job and expose it in Studio/intake.
2. Extend M8 selection so Gemini mode can evaluate up to the top 3 eligible candidates per scene instead of committing the first metadata winner immediately.
3. Reuse the existing n8n Gemini credential; do not introduce another secret.
4. Parse Gemini response fail-closed and persist validation evidence with the selected asset.
5. Preserve the existing metadata-only route unchanged when `visual_validation_mode=metadata`.
6. Add deterministic tests for routing, call bound, PASS/FAIL/fallback, malformed Gemini response, and no-Gemini behavior.
7. Deploy only the components changed by this feature, verify live state, then run one controlled comparison job per mode.


Implementation checkpoint:
- Decision is committed in Git as `398738e`.
- Phase 1 source implementation is complete locally:
  - jobs persist `visual_validation_mode` with default `metadata`;
  - intake accepts explicit `metadata|gemini` while remaining backward-compatible when the field is omitted;
  - Studio exposes the selector and submits it;
  - latest-job API returns the saved mode.
- Focused tests: 7/7 PASS.
- Workflow JSON parse: PASS.
- `git diff --check`: PASS.
- Phase 1 is not deployed yet; next step is the M8 Gemini branch and bounded 3-candidate validation before any deployment.


Phase 2 implementation checkpoint:
- M8 now routes by the persisted job mode after visual search collection.
- `metadata` continues through the existing deterministic `factory.select_visuals` path.
- `gemini` obtains up to 3 deduplicated eligible candidates per shot, fetches bounded image previews through media-worker, and sends all candidates for one scene in a single Gemini request.
- Gemini image parts explicitly use `MEDIA_RESOLUTION_LOW` to reduce media-token usage.
- Gemini output is parsed fail-closed. A candidate passes only when required concepts are visible, forbidden concepts are clear, intent matches, and score is at least 70.
- Cross-scene provider-asset reuse is prevented; the collector falls back to another Gemini-approved candidate when available.
- Final Gemini validation evidence is persisted on `visual_selections`.
- Existing Gemini credential is reused; no new secret was introduced.
- Media-worker preview endpoint accepts 1-3 images, image MIME types only, max 3 MiB each / 8 MiB total.
- SQL migration/function syntax was verified inside a rollback-only transaction against the production PostgreSQL engine: PASS.
- media-worker `py_compile`: PASS.
- focused Node regressions including the existing Wikimedia depiction work: 63/63 PASS.
- `git diff --check`: PASS.
- Full regression suite is the next gate; nothing from Phase 2 is deployed yet.


Full regression checkpoint:
- Full Node suite: 316/316 PASS.
- media-worker `py_compile`: PASS.
- `git diff --check`: PASS.
- Source checkpoint before deployment: `d5bde05`.
- Next gate: isolated n8n workflow import/schema check, then production migration + targeted M3/M8/API/Studio/media-worker deployment and live verification. No acceptance job before those checks pass.


Isolated n8n validation checkpoint:
- The current M8 workflow imported successfully into a clean isolated n8n 2.37.10 SQLite instance.
- This validates the exported workflow shape/new node definitions without touching production.
- Production check immediately before deployment: no active `new/running/waiting` publisher executions; target workflow IDs remain `VideoM3Intake001`, `VideoM8Visuals001`, and `VideoSelfTestApi001`.
- Studio is bind-mounted read-only from this repository into the live Caddy container, so the committed Studio selector source is already the file served by Caddy; no Caddy restart is required.
- Next: production DB migrations, media-worker rebuild/recreate, then publish only M3/M8/Self-Test-API and verify exact live source/state before any job.

Production deployment checkpoint — selectable Gemini visual validation:
- Production DB migration applied successfully: jobs now persist `visual_validation_mode`; visual selections persist `validation_mode` and `validation_evidence`; Gemini candidate/commit functions are live.
- media-worker rebuilt and recreated only for the bounded `/visual-previews` endpoint. Live image: `sha256:d24abec8545dbdbfe3d75bec7d370b728e043d4373e6d39544569d10a77cc54a`; restart count 0; health `healthy`; live `/worker/server.py` SHA matches Git source.
- Live preview endpoint was exercised against a real Pexels preview and returned one bounded WebP preview successfully.
- Published only target n8n workflows:
  - M3 Intake v3;
  - M8 Multi-Source Visuals v65;
  - Self Test API v4.
- Published exports for all three match Git exactly for nodes/connections/settings.
- Non-target workflow fingerprint remained unchanged: `29|57e0fed4a6d13bed63ef6fb752071d64`.
- Publisher n8n was restarted once only after CLI publish because production webhooks were not registered until restart. After restart:
  - POST `/webhook/jobs` accepts `visual_validation_mode=gemini`;
  - invalid mode rejects with the exact validation error;
  - GET `/webhook/factory/latest` returns persisted `visual_validation_mode`.
- Studio live HTML is serving the new visual-quality selector.
- Active publisher executions after deployment: 0.
- Next: one controlled non-acceptance Gemini-mode test job to exercise the actual M8 Gemini credential/request/selection path. Poll in short verified steps; no long blind wait.


Controlled Gemini-mode smoke-test blocker — 2026-09-23:
- Job `21e30e0c-2ee2-491e-bd57-2eebb92e25e3` failed before M8, in M5 execution `9724`.
- Exact provider failure: Gemini HTTP 503 `This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.`
- `Generate Storyboard` already had n8n transient retry enabled (`retryOnFail=true`, `maxTries=3`, `waitBetweenTries=5000`), so the provider remained unavailable through all existing attempts.
- This is not a Gemini visual-validation/M8 failure. Do not change M8 for this blocker.
- Next gate: harden M5 transient-provider retry without adding a new paid service/model, run focused regression tests, deploy only M5 if clean, then rerun one controlled Gemini-mode smoke job.

M5 transient-provider hardening checkpoint:
- All 11 Gemini HTTP nodes in M5 keep the same model/credential/error routing but now use `maxTries=5` and `waitBetweenTries=10000` instead of 3/5000.
- No new model, credential, provider, or paid dependency was introduced.
- Focused M5 regression suite: 14/14 PASS.
- Next gate: full Node regression suite + diff check. Deploy only M5 if clean.

M5 retry hardening full-regression checkpoint:
- Full Node regression suite after the retry change: 316/316 PASS.
- `git diff --check`: PASS.
- Source checkpoint: `324be11`.
- Next gate: verify zero active publisher executions, back up the currently published M5, deploy/publish only M5, verify published nodes/connections/settings match Git, then rerun one controlled Gemini-mode smoke job.

M5 retry hardening production deployment checkpoint:
- Pre-deploy active publisher executions: 0.
- Backed up the previously published M5 to `.backups/m5-before-retry-hardening-20260923-172916.json` (SHA256 `6a65810d4bf204036520a96a058c2c299788fae904ba00d7514eba5036c34492`).
- Imported/published only `VideoM5Storyboard001`; new active version ID is `b54a2f65-7fd7-40f0-a803-12106aa408f7`.
- Restarted only `ai-short-form-n8n` because the CLI explicitly required restart for published changes to take effect.
- Post-restart published M5 matches Git exactly for `nodes`, `connections`, and `settings`; container state is running.
- Next gate: rerun one controlled `gemini` visual-validation smoke job and confirm it passes M5 and reaches the M8 Gemini pixel-validation path.

Gemini visual smoke blocker — job `00a38d43-1086-4b6c-abb6-da9762f6cc66`:
- M4 `9728`, M5 `9733`, M6 `9744`, and M7 `9745` all completed successfully; M8 execution `9746` failed.
- Exact M8 failure: `no Gemini-previewable relevant visual candidate for shot S2-A`.
- S2 storyboard intent: lamp fixture inside the lighthouse lantern room. Searches returned 24 Pexels + 24 Pixabay candidates; Wikimedia returned 0 for all three queries.
- Every S2 candidate was metadata-rejected before Gemini could inspect pixels. Several otherwise plausible Pexels lighthouse-lamp candidates were rejected by `missing_primary_subject_anchor:lamp fixture` / `insufficient_must_show_concept_coverage`.
- Root architectural issue: Gemini mode currently inherits the metadata-mode `rejected=false` gate, so metadata false negatives can prevent Vision from seeing any candidate. The fix must keep hard safety/media rejects but allow bounded semantic-review candidates into Gemini; do not weaken the metadata-mode selection path.
- Next gate: implement/test a Gemini-only candidate eligibility policy in `get_gemini_visual_candidate_sets`, then deploy M8/DB only and rerun one post-fix controlled Gemini job.

Gemini candidate-review implementation checkpoint:
- Added `factory.gemini_visual_review_bucket(...)` for Gemini mode only: metadata-accepted candidates rank first; explicit semantic metadata misses are reviewable by Vision; unknown/hard rejects fail closed with bucket 99.
- Hard rejects such as `must_not_show:*`, non-photographic assets, invalid/unknown future rejection reasons remain ineligible.
- `get_gemini_visual_candidate_sets` and `commit_gemini_visual_selections` use the same review policy; metadata-mode `factory.select_visuals` is unchanged.
- Candidate JSON now carries `metadata_rejected`, `metadata_rejection_reason`, and `review_bucket`; final Gemini validation evidence persists whether Vision rescued a metadata-rejected candidate.
- Focused Gemini tests: 13/13 PASS.
- Rollback-only production-engine replay of failed visual run `60514425-ca72-491c-bfd1-e0c4288bd300`: helper buckets were accepted=0, semantic-soft=1, must-not=99, non-photo=99, unknown=99; S2-A now produced 3 bounded Pexels candidates for actual Vision review instead of failing before Gemini.
- Next gate: full regression + diff check, then DB/M8-only deploy and one post-fix controlled Gemini job.

Gemini candidate-review full-regression checkpoint:
- Full Node regression suite after the Gemini-only review policy change: 318/318 PASS.
- `git diff --check`: PASS; working tree was clean before this documentation update.
- Source checkpoint: `5d6604c`.
- Next gate: verify zero active publisher executions and current M8 production version, back up published M8 and current DB functions/schema, deploy only `db/09-visuals.sql` + `VideoM8Visuals001`, verify exact live state, then run one post-fix Gemini smoke job.

Gemini candidate-review production deployment checkpoint:
- Pre-deploy active publisher executions: 0.
- Backups created: `.backups/m8-before-gemini-review-20260923-175157.json` (SHA256 `46482f42900ce0f4a1313d51945af28c13061ad21ec6e8836a3d3b3d25b70a4e`) and `.backups/factory-schema-before-gemini-review-20260923-175157.sql` (SHA256 `17baaddf71ae9ce05ab8e5c80eb52421688affec2b0bfc8b7f78e3fee94deff5`).
- Applied current `db/09-visuals.sql` and published only `VideoM8Visuals001`; active version is `271d4c60-29b3-4ec9-b0e1-cf4f48baade3`.
- Restarted only `ai-short-form-n8n` because n8n CLI required restart for published changes to take effect.
- Published M8 matches Git exactly for nodes/connections/settings. Live review helper returns accepted=0, semantic-soft=1, hard must-not=99, non-photographic=99.
- Started one controlled post-fix Gemini smoke job: `dba2ef8f-84f6-4676-b75e-12d5b7d96dab` (`how does a lighthouse work?`, en, 15s, gemini). M3 succeeded; M4 is currently running. Continue with short state checks only; no additional test job.

Post-deploy Gemini smoke failure — job `dba2ef8f-84f6-4676-b75e-12d5b7d96dab`:
- M5 `9754`, M6 `9755`, M7 `9756` succeeded; M8 execution `9757` failed.
- Exact failure: `Gemini scene validation count mismatch`.
- Execution replay shows 5 candidate sets entered preview fetch, but only 3 reached Gemini validation. `Build Gemini Vision Request` routed 2 items to error because `/visual-previews` returned 422 wrapping upstream HTTP 429 `Too Many Requests (015d12c)`.
- Affected shots were S2-A and S3-A. Each had usable fallback candidates, but the media-worker aborted the whole scene preview request on the first candidate download error, so Gemini never saw the remaining candidates.
- Root fix: preview fetching must be per-candidate fail-soft while remaining fail-closed at scene level: continue after an individual preview download failure, pass only successfully fetched candidates to Gemini, and fail the scene only when zero previews remain. Candidate indices must be renumbered consistently after pruning. No weakening of Gemini pass criteria or metadata-mode selection.

Gemini preview 429 fix checkpoint:
- media-worker `/visual-previews` now records individual candidate download failures and continues; it returns success when at least one bounded preview remains and fails only when all previews fail.
- M8 `Build Gemini Vision Request` prunes missing previews, renumbers surviving candidate indices consistently, and sends only successfully fetched pixels to Gemini. Gemini pass threshold/booleans remain unchanged.
- Focused Gemini tests: 15/15 PASS. media-worker `py_compile`: PASS. `git diff --check`: PASS.
- Next gate: full Node regression suite, then targeted media-worker + M8 deploy and one controlled post-fix smoke job. Do not reuse the failed job as acceptance evidence.

Gemini preview 429 full-regression checkpoint:
- Full Node regression suite after the partial-preview fix: 320/320 PASS.
- `git diff --check`: PASS.
- Source checkpoint: `0e79080`.
- Next gate: verify zero active publisher executions, back up current M8 and media-worker image/source, deploy only media-worker + `VideoM8Visuals001`, verify exact live source/state, then run one controlled Gemini smoke job.

Gemini preview 429 production deployment checkpoint:
- Pre-deploy active publisher executions: 0.
- Backups: `.backups/m8-before-partial-preview-20260923-181146.json` SHA256 `538046898905fb193afa4429f2a7c8a62b73e64c1d437bc803acb3f6e805e7b1`; `.backups/media-worker-server-before-partial-preview-20260923-181146.py` SHA256 `c52093c18f6292d14554a31ade79f12dd6502cccf1a40381d41035413717d062`.
- media-worker rebuilt/recreated only for the per-candidate preview fail-soft behavior; live source SHA256 `a3d07f116c32f251bc6191cb7452a74a53c89d052ad7c53bf9812b965ee14714`, image `sha256:64e96a07a1d5438cbe8ffea28c815a36e4be1480ad3ded270c7839e75ab4d0d8`, health `healthy`, restart count 0.
- Published only `VideoM8Visuals001`; active version `21599d8f-f0c9-48c8-af86-ba9e297cdd5a`. Restarted only publisher n8n because CLI required it.
- Published M8 matches Git exactly for nodes/connections/settings.
- Next gate: start one controlled Gemini smoke job and verify it reaches actual Gemini pixel validation without the previous 429 scene-drop failure. No acceptance sequence yet.

M5 execution 9783 precision-count fix checkpoint:
- Exact failure was a malformed precision response shape: Gemini returned 2 complete narration strings for a 5-scene visual-cut storyboard (`precision narration count mismatch: 2, target 5`).
- M5 now discards ambiguous partial precision mappings when response count differs from scene count and falls back per scene only to the already validated base scene or immutable original scene; semantic guards remain mandatory and no new text is invented.
- Added regression for execution 9783 lighthouse output. Focused precision fallback tests: 4/4 PASS. `git diff --check`: PASS.
- Next gate: full Node regression suite, commit/push, then deploy only M5 and run one controlled Gemini smoke job through M8.

M5 execution 9783 full-regression checkpoint:
- Full Node regression suite after precision count-mismatch fallback: 321/321 PASS.
- `git diff --check`: PASS.
- Next gate: commit/push, verify zero active publisher executions, back up current published M5, deploy/publish only M5, verify live workflow matches Git, then run one controlled Gemini smoke job.

M5 execution 9783 production deployment checkpoint:
- Pre-deploy active publisher executions: 0.
- Backup: `.backups/m5-before-precision-count-fix-20260923-182436.json` SHA256 `3a1337530511ef641cc00bd8792d86e1232c56bc62a378a753963db0724599be`.
- Published only `VideoM5Storyboard001`; active version `945c1dd0-900c-4aca-9fbb-b1333a56b0fb`.
- Restarted only publisher n8n because CLI required it.
- Published M5 matches Git exactly for nodes/connections/settings; n8n is running.
- Next gate: one controlled Gemini smoke job through M5→M8. No additional test jobs until its result is known.

Controlled post-M5-fix Gemini smoke job:
- Started job `8cd3ffb3-1439-4d21-a0fe-9298f043e4c7` (`how does a lighthouse work?`, en, 15s, `gemini`).
- M3 execution `9785` succeeded; M4 execution `9787` is currently running. Do not create another job; continue tracing this exact job.
