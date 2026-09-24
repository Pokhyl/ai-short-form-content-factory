# Current State

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

### M5 v99 deployed; fresh PL15 running — 2026-09-22

- Fix commit `486406fa5f48e2d62c8e7b4f7bda482dfe3587e4`; only M5 published as v99 `8317622a-7d47-4cc5-8c40-f3f76caebf42`.
- Backup `.backups/m5-before-measured-drafts-20260922-032117.json`; all other 31 workflow rows unchanged (before/after hash `2b1e19662b731815a72c46a9042f1243`). Live nodes/connections/settings match repository. No active project runs before deploy; no restart/credential change. M8 remains v53 `0953f69f-e982-467e-95e0-35161a613771`.
- Fresh PL15 `b36a7c19-3427-4d67-9e2b-50d0acb4d717` created and accepted through Studio webhook path.
- Next: monitor this exact job, confirm M5 v99/M8 v53 execution versions, inspect output or exact terminal failure. Do not duplicate a running job. EN30 remains blocked by PL15 visual/audio QA.

### Verified v99/v53 runtime result and exact remaining work — 2026-09-22

- Job `b36a7c19-3427-4d67-9e2b-50d0acb4d717`: intake 9223 PASS, parent 9224 ERROR, M4 9225 PASS, M5 9226 PASS on **v99 `8317622a-7d47-4cc5-8c40-f3f76caebf42`**, M6 9227 PASS, M7 9228 PASS, M8 9229 ERROR on **v53 `0953f69f-e982-467e-95e0-35161a613771`**. M9 absent; no final MP4, no visual/audio/HUMAN PASS. M5 runtime version is proven; the new optional late branch is proven by exact 9221 replay, not claimed exercised in 9226.
- M8 completed all 45 searches / 335 candidates: Pexels 15/120, Pixabay 15/120, Commons 15/95. Exact terminal failure S1-A `missing_secondary_subject_context` among otherwise high-score candidates. Failed job remains immutable.
- S1 `hydroelectric dam` + `water reservoir`: secondary generic-anchor filtering discards reservoir and requires water literally. Exact Commons 172815415 title/object name `Tri An Hydroelectric Dam And Its Reservoir` has both physical subjects but no literal water token. Browser visual inspection of its exact Commons page confirms a dam and impounded water; this is source-image inspection only, not final-MP4 QA. Exact sanitized fixture `tests/fixtures/pl15-v99-dam-reservoir.json`.
- Tested an experimental secondary-head rule locally: preserve generic independent object heads and remove form modifiers only with fully grounded primary/head. All 116 tests passed, but full 335-candidate replay exposed unresolved acceptance risks. Therefore the experimental M8 source/test changes were REVERTED, NOT deployed. Repository M8 remains verified v53 source; final retained suite is 110 tests.
- The experiment's report is explicitly marked rejected/not deployed: `docs/acceptance/2026-09-22-pl15-v99-secondary-head-replay.json`. It is diagnostic evidence, NOT production scoring or approval. S1 would admit PNG 94068077 `Pacific Northwest drought status and hydroelectric dam reservoir storage capacity...`, requiring exact depiction/type verification. Do not weaken photo/type gates or silently accept it.
- Additional gaps found by the SAME replay (not a new audit): S5 `electrical transformer` + `power lines`, domain `substation`, has zero eligible candidates; returned transformer photos lack independent power-lines evidence. S4 singleton `electric generator` has no hydroelectric domain in its storyboard intent/queries and receives no inferred domain, so its broad generator pool requires context correction before acceptance.
- Raw sanitized 45-response replay: VPS `.review/pl15-v51/v99-replay.json`; S1 candidate diagnostic `.review/pl15-v51/v99-s1-candidates.json`. No additional provider calls were used for replay. Public exact asset was viewed in browser. No later full pipeline job was started.
- Exact next engineering step: use execution 9229 saved responses/shot contexts to resolve S1 secondary object evidence and S5 paired-object retrieval while keeping railway/power-station and nectar/dew negatives strict; explicitly preserve singleton S4 operating context from the storyboard/topic contract. Replay all 335 candidates, check affected exact assets, and require all five eligible pools before spending a fresh PL15. Do not re-audit infrastructure, repeat old v94 work, or rerun failed jobs.
- EN30 remains prohibited until fresh PL15 final visual/audio QA. No new permission or credential is required; use existing SSH alias. Production versions stay v99/v53 and worker full-fit image unchanged.

Checkpoint verification: M5 v99 and M8 v53 live nodes/connections/settings match repository; inventory 32 total/15 active; zero active project executions; Publisher/Studio HTTP 200; n8n and worker restart 0; worker healthy on unchanged `sha256:11d5b351609b40f9e5c46362a59ff2c620a403503bbb8f6e8ae0f57c57eef7ec`. Final retained suite 110/110 PASS and diff check PASS. This checkpoint is not final product acceptance.

## M8 saved-response context/retrieval fix — tested, not deployed — 2026-09-22

- Source job `b36a7c19-3427-4d67-9e2b-50d0acb4d717`, M8 execution `9229`, remains the immutable diagnostic source: 45 searches / 335 candidates / terminal S1-A.
- The retained M8 correction resolves the three known saved-run gaps without weakening score thresholds: S1 depicted secondary evidence, S4 adjacent machinery operating context, and S5 paired-object retrieval.
- Full suite **128/128 PASS**; full saved-response replay now has eligible counts S1=1, S2=11, S3=3, S4=3, S5=4.
- Exact simulated selections were source-reviewed; contextual-category-only reservoir, non-photo map, museum/display machinery and manufacturing/transport substitutions are fail-closed for the relevant operational scenes.
- Evidence: `docs/acceptance/2026-09-22-pl15-v99-v53-m8-context-fix.json`.
- Production is still M5 v99 / M8 v53 until the following scoped M8 deployment checkpoint. No fresh PL15 has been spent on this tested source state yet.


## M8 v54 deployment checkpoint — 2026-09-22

- `VideoM8Visuals001` is now published as v54, activeVersionId `818d2c37-28db-488b-b7b7-f0e047a29f30`, from commit `7177050c90acf301e3705caaa4ab68c43983efad`.
- M5 remains v99 `8317622a-7d47-4cc5-8c40-f3f76caebf42`.
- M8 live export matches repo `nodes/connections/settings`; other 31 workflow rows unchanged by fingerprint.
- No restart/credential change; Publisher/Studio 200, n8n restart 0, worker healthy restart 0.
- Runtime proof of v54 is still pending. Exactly one fresh PL15 is next; final product acceptance is still blocked until its exact MP4 passes technical, semantic visual and audio review.


## PL15 v54 runtime failure and hidden-process fix — tested, not deployed — 2026-09-22

- Fresh job `763b1c91-c765-414f-bfa2-7edd9b7bd11a` proves M5 v99 and M8 v54 runtime. M4-M7 passed; M8 execution 9253 on v54 failed S2-A after all 45 searches; M9 did not run.
- S2 had an impossible hard visual contract: `flowing water` + `penstock` while the intent places the flow inside a closed penstock. M8 correctly rejected all candidates.
- Tested M5 correction promotes a closed conduit/machine to the primary visible subject when a hidden process occurs inside/through it, unless transparent/open/cutaway/exposed visibility is explicit.
- Tested M8 correction preserves explicit local operating-domain context for closed infrastructure, so corrected S2 q3 keeps provenance `penstock` but searches `hydroelectric penstock`.
- Current targeted live/scorer evidence yields 5 compliant hydroelectric penstock candidates. No scorer threshold or semantic gate was weakened.
- Validation: 158/158 tests PASS; M5 55 and M8 10 Code-node syntax checks PASS; JSON/diff checks PASS.
- Production remains M5 v99 `8317622a-7d47-4cc5-8c40-f3f76caebf42` / M8 v54 `818d2c37-28db-488b-b7b7-f0e047a29f30` until scoped deployment.


## M5 v100 / M8 v55 deployment checkpoint — 2026-09-22

- M5 active: v100 `8cc07108-bc76-43f3-b97e-071fbca26148`.
- M8 active: v55 `5ae1fa70-219c-4ea2-84d5-8882c3a4dbd8`.
- Source commit `ca0716f08f722bd5bbd39022b2e0b9c3f9f3b119`.
- Exact backups: `.backups/m5-before-hidden-process-fix-20260922-065211.json`, `.backups/m8-before-hidden-process-fix-20260922-065211.json`.
- Other 30 workflow fingerprint unchanged: `988ee473175a09fe877d3de8c2325108`.
- Live published exports match repo nodes/connections/settings. Publisher/Studio 200. n8n restart 0. Worker healthy restart 0. Zero active project executions.
- Runtime proof is pending; next action is exactly one fresh PL15, not a rerun of the failed v54 job.


## M5 v100 runtime timing-direction defect — tested fix, not deployed — 2026-09-22

- Fresh PL15 `94d22732-c6f6-4514-bb5b-71f006f749ad` proved M5 v100 runtime and failed in M5 execution 9287 before M6.
- 22-word narration measured 14208ms against unchanged valid window 14250-15750ms. The late builder requested LONGER but old regression returned a smaller 21-word / 162-character target, which produced a confirmed too-short 21-word narration (13368/13512/13368ms).
- Tested fix makes both late timing builders direction-safe. Exact replay now produces 23 words / 176 chars, scene targets [5,5,4,4,5], for the same 14208ms input.
- Validation: 160/160 tests PASS; M5 55/55 Code-node syntax PASS; JSON/diff checks PASS. No timing tolerance or acceptance gate changed.
- Production remains M5 v100 `8cc07108-bc76-43f3-b97e-071fbca26148` and M8 v55 `5ae1fa70-219c-4ea2-84d5-8882c3a4dbd8` until M5-only deploy.


## M5 v101 deployment checkpoint — 2026-09-22

- M5 active v101 `0181e4e3-ae95-4a37-afd2-9b4bd5ca7f4f`; M8 remains v55 `5ae1fa70-219c-4ea2-84d5-8882c3a4dbd8`.
- M5 backup: `.backups/m5-before-direction-safe-timing-20260922-070159.json`.
- Protected 31-workflow fingerprint unchanged: `07f4e3bc61e679e8ba1b0ff5677373d9`.
- Live M5 nodes/connections/settings match repo. Publisher/Studio 200; n8n restart 0; worker healthy restart 0; zero active executions.
- Next: exactly one fresh PL15 for runtime proof and continuation through M8/M9.


## PL15 v101/v55 full machine pass is NOT human visual pass — 2026-09-22

- Job `6ff32b6c-27f8-4cfc-9872-450bb74530a7` reached M9 successfully on M5 v101 / M8 v55 and produced a technically valid 15.700 s 1080x1920 MP4.
- Exact technical audit passes every gate, including full decode and 0.999984 audio correlation.
- Manual/source visual review rejects S3: production selected a 1918 aircraft wind-driven generator for an intent requiring generator+turbine inside a power plant.
- Local M8 WIP now requires positive strong-metadata evidence for explicit operational plant/station/facility settings. This is generic, not topic- or asset-specific.
- 169/169 tests PASS. Exact 69-candidate S3 replay leaves one old-production eligible candidate with the requested setting: Wikimedia 112972156, turbine+generator inside Iru Thermal Power Plant.
- This WIP is not yet deployed. Production remains M5 v101 `0181e4e3-ae95-4a37-afd2-9b4bd5ca7f4f` / M8 v55 `5ae1fa70-219c-4ea2-84d5-8882c3a4dbd8`.
- HUMAN PASS remains false; EN30 remains blocked.


## M8 v56 production checkpoint — 2026-09-22

- M8 v56 activeVersionId `ff72822c-44df-4058-9c7a-f31aa4abd7c9`, source commit `5820a277dfdfe9098fe13d9814f46553392a05a5`.
- M5 remains v101 `0181e4e3-ae95-4a37-afd2-9b4bd5ca7f4f`.
- Backup `.backups/m8-before-operational-setting-20260922-073017.json`.
- Other 31 workflows unchanged by exact fingerprint; live M8 core matches repository; Publisher/Studio healthy; no restart/credential change.
- Runtime proof and HUMAN acceptance are still pending. One fresh PL15 is the next action.


## PL15 v56 S3/S5 retrieval fix tested — 2026-09-22

- Job `fe1acef0-c956-441a-94ad-92b56f08902e` proves M5 v101 and M8 v56 runtime; M8 9344 failed after 45/45 searches.
- Persisted eligible pools: S1=13, S2=7, S3=0, S4=28, S5=0.
- Retained M8 WIP fixes false component-domain inference, compound forbidden-subtype matching, missing-primary fallback retrieval, home/house lexical equivalence, and Commons TIFF-origin/JPEG-thumbnail handling.
- Validation: 189/189 tests PASS; targeted live scorer gives S3=4 eligible and S5=3 eligible with exact provider-query provenance preserved.
- Production is still M5 v101 `0181e4e3-ae95-4a37-afd2-9b4bd5ca7f4f` / M8 v56 `ff72822c-44df-4058-9c7a-f31aa4abd7c9`.
- Not deployed yet. HUMAN PASS remains false; EN30 remains blocked.


## M8 v57 production checkpoint — 2026-09-22

- M8 active v57 `ecb6889c-b8b7-4a01-8f30-8e9a41f8213b` from commit `e00eee0f1fb664cdc28e4f061a2ed53f49e4e17d`.
- M5 remains v101 `0181e4e3-ae95-4a37-afd2-9b4bd5ca7f4f`.
- Backup `.backups/m8-before-s3-s5-retrieval-20260922-083029.json`.
- Other 31 workflow fingerprint unchanged; live core matches repo; Publisher/Studio healthy; no restart/credential change.
- Runtime proof and HUMAN acceptance still pending. One fresh PL15 is next.


## M5 short-anchor canonicalization fix tested — 2026-09-22

- Fresh job `2b528909-1b80-430a-86a7-ee84e7753353` stopped in M5 execution 9361 on v101 because `high voltage power lines` exceeded the raw 3-word must_show limit.
- Exact saved-response replay now canonicalizes that concrete anchor to `power lines`; descriptive 4+ word prose remains fail-closed.
- Validation: 193/193 tests PASS; M5 55/55 Code-node syntax PASS; JSON/diff checks PASS.
- Production still M5 v101 `0181e4e3-ae95-4a37-afd2-9b4bd5ca7f4f` / M8 v57 `ecb6889c-b8b7-4a01-8f30-8e9a41f8213b`.
- M8 v57 runtime proof remains pending because the job never reached M8. HUMAN PASS false; EN30 blocked.


## M5 v102 production checkpoint — 2026-09-22

- M5 active v102 `fd54c08f-7bd4-480d-9959-27d882ca7c63` from commit `b587b9851a35d69f5821efc6a3c5f1a6c1567ffb`.
- M8 remains v57 `ecb6889c-b8b7-4a01-8f30-8e9a41f8213b`.
- Backup `.backups/m5-before-short-anchor-20260922-084041.json`.
- Other 31 workflows unchanged by exact fingerprint; live M5 core matches repo; Publisher/Studio healthy; no restart/credential change.
- One fresh PL15 is next. HUMAN PASS false; EN30 blocked.


## PL15 v102/v57 hidden-process/domain fix tested — 2026-09-22

- Job `6a6cd336-2c31-4d75-8b5b-f252c5d00ce0`: M5 v102 PASS, M8 v57 execution 9406 FAIL after all 45 searches.
- Eligible pools S1=10, S2=0, S3=10, S4=2, S5=3.
- S2 failure was caused by hidden `flowing water` being retained as must_show for a closed penstock plus false hard `water` domain inference.
- Local WIP:
  - M5 removes hidden process/action secondary anchors for closed conduits/machines unless explicitly visible;
  - M8 excludes transported medium/content terms from hard domain inference for closed infrastructure.
- Corrected S2 has must_show `penstock pipe`, no hard domain terms, and cached Wikimedia q3 already has 2 eligible penstock candidates.
- Validation 204/204 PASS; M5 55/55 and M8 10/10 Code-node syntax PASS; JSON/diff checks PASS.
- Production still M5 v102 `fd54c08f-7bd4-480d-9959-27d882ca7c63` / M8 v57 `ecb6889c-b8b7-4a01-8f30-8e9a41f8213b`.
- Not deployed yet. HUMAN PASS false; EN30 blocked.


## M5 late timing-stability fix tested — 2026-09-22

- Fresh job `c2e66456-1593-4052-b0d7-61fe53bf696d` stopped in M5 execution 9424 on v103 with `got 25, target 27`.
- Same 24-word Chirp3-HD narration varied 13.896–15.024 s across real syntheses. A single 13.344 s Probe-4 result was incorrectly used to recalculate target words.
- Local M5 WIP now sends Probe-4 bounded near-misses through the existing 3-sample stability gate, adds origin-4 routing, and allows only a tightly bounded semantic nearest word-count hybrid to reach real Probe 5.
- Exact 9424 replay passes to Probe 5 with 25 words vs target 27; semantic guard remains active.
- Validation 208/208 PASS; M5 55/55 Code-node syntax PASS; graph/JSON/diff checks PASS.
- Production still M5 v103 `26ab19ec-ad1c-44ed-9f98-1f6c9d41214b` / M8 v58 `05df9dcc-404c-4a78-9b2a-e45e930b9dc6`.
- Not deployed yet. HUMAN PASS false; EN30 blocked.


## M5 v104 production checkpoint — 2026-09-22

- M5 active v104 `2a30c8ab-083a-4d4f-967e-ffd2a5889620`, source commit `964cada1e3414134645c1a6d69cfbaffc32d02a4`.
- M8 remains v58 `05df9dcc-404c-4a78-9b2a-e45e930b9dc6`.
- Backup `.backups/m5-before-late-stability-20260922-115826.json`.
- Other 31 workflows unchanged by exact fingerprint; live M5 core matches repo; services healthy; no restart/credential change.
- Runtime proof/HUMAN acceptance pending. One fresh PL15 is next.


## M5 precision scene fallback tested — 2026-09-22

- Job `b1fb1aa8-854f-4d47-b4d1-174e8410b0ef` stopped in M5 execution 9438 on v104 because precision retry introduced prohibited filler `potężnie`.
- Semantic guard remains strict. Local WIP now falls back per scene to a same-scene previous narration only if it independently passes the unchanged semantic guard; otherwise immutable original is used.
- Exact 9438 replay passes with S2 using the prior valid line, no `potężnie`, 27 total words and next node `Prepare Timing Probe 3`.
- Validation 211/211 PASS; focused tests 3/3 PASS; JSON/diff checks PASS.
- Production still M5 v104 `2a30c8ab-083a-4d4f-967e-ffd2a5889620` / M8 v58 `05df9dcc-404c-4a78-9b2a-e45e930b9dc6`.
- Not deployed yet. HUMAN PASS false; EN30 blocked.


## M5 v105 production checkpoint — 2026-09-22

- M5 active v105 `56bcb365-4180-4ff4-b3c9-6732e2c7cfb5`, source commit `689b08f5940ac98da78e8402be77613918569385`.
- M8 remains v58 `05df9dcc-404c-4a78-9b2a-e45e930b9dc6`.
- Backup `.backups/m5-before-precision-fallback-20260922-121005.json`.
- Other 31 workflow rows unchanged by exact fingerprint; live M5 core matches repo; services healthy; no restart/credential change.
- Runtime proof/HUMAN acceptance pending. One fresh PL15 is next.


## M8 execution 9229 deterministic replay accepted — 2026-09-22

- Exact v53 replay reproduces the old S1 failure from execution 9229 on original saved inputs.
- Current M8 + separately captured changed-query responses selects five compliant images with no terminal failure:
  S1 `172815415`, S2 `39943534`, S3 Pexels `12270481`, S4 `34396499`, S5 `27207173`.
- Manual source-image review: 5/5 PASS.
- Full suite 232/232 PASS; M5/M8 syntax+graph checks PASS; diff/JSON checks PASS.
- Temporary search workflows removed; original job 9229-source unchanged.
- Production remains M5 v105 / M8 v58. Current M8 WIP is not deployed yet.
- Next action: commit/push and deploy only M8, then exactly one fresh PL15.


## M8 v59 production checkpoint — 2026-09-22

- M8 v59 activeVersionId `96b3a6b9-b5ef-4a28-a68a-5c3c928b8185` from commit `cb656d9d0dc7aaea5f79583024a6a77b08cbb7f1`.
- M5 remains v105 `56bcb365-4180-4ff4-b3c9-6732e2c7cfb5`.
- Backup `.backups/m8-before-9229-replay-20260922-161125.json`.
- Other 31 workflow fingerprint unchanged; live M8 core matches repo; Publisher/Studio healthy; no restart.
- Exactly one fresh PL15 is now authorized by the deterministic replay acceptance.


## M5 transient Gemini 503 retry fix tested — 2026-09-22

- Post-M8-replay PL15 job `8f2970ba-4406-4eca-aecb-f9d67d2a895c` stopped in M5 execution 9488 because `Generate Storyboard` received Gemini HTTP 503/high demand.
- M8 v59 was not reached.
- Root cause: n8n retry detector reads main `json.error`, while Gemini nodes used `continueErrorOutput`; their apparent retry configuration was therefore bypassed.
- Local M5 WIP puts provider errors on main output for n8n retry detection, uses 3 attempts / 5 s, and preserves final provider error through existing bounded validator error routing.
- Validation: 235/235 full tests PASS.
- Production remains M5 v105 / M8 v59; M5 fix is not deployed yet.


## M5 v106 repair-provider fallback tested — 2026-09-22

- Job `8d03a4e9-fab8-48bc-9feb-401cad6738c8`, M5 execution `9499`.
- First storyboard response was usable but invalid (4/5 scenes); first repair then exhausted Gemini 503 retries.
- Local fix makes second repair fall back to the original successful draft + original validation error instead of failing with `first Gemini output is empty`.
- Exact 9499 replay PASS; full suite 237/237 PASS.
- Production still M5 v106 / M8 v59. Fix not deployed yet.


## M5 v107 final-hybrid semantic filter tested — 2026-09-22

- Job `34fd153d-0164-4cf9-8eef-25da2401d498`, M5 execution `9516`.
- Root cause: final measured hybrid search could reinsert semantic-invalid `base/pre_final` scene variants because only measured drafts were prevalidated.
- Local fix prevalidates every hybrid option against immutable scene semantics before dynamic-programming selection.
- Exact 9516 replay returns 24/24 words with valid S3.
- Full suite 238/238 PASS; M5 syntax/graph PASS.
- Production still M5 v107 / M8 v59. Fix not deployed yet.


## Exact-audio M5->M6 handoff tested — 2026-09-22

- Replaced timing prediction across independent Chirp syntheses with reuse of the exact real MP3 that already passed the final duration gate.
- Exact 9523 replay selects 15.336 s / SHA `8d56d85b...f716` from the saved 15.336 / 13.368 / 16.248 s syntheses.
- Isolated media-worker store/promote integration PASS.
- DB candidate registration/adoption test PASS under ROLLBACK.
- Full suite 245/245 PASS; M5/M6 syntax+graph checks PASS.
- Production is still unchanged: M5 v108, M6 v7, M8 v59.
- Next: deploy migration + media-worker + only M5/M6, then one fresh PL15.


## Fresh PL15 reached M8 after exact-audio success; S5 fix tested — 2026-09-22

- Job `7813ffd0-76bb-4e99-8fd4-dc8d4819520b`: M5 v109 PASS, M6 v8 PASS via exact candidate reuse, M7 PASS, M8 v59 failed only on S5.
- Exact reused final voiceover: 14.808 s, SHA `88eac0eb...e56a9`; no M6 Google TTS call and no M6 TTS usage reservation.
- M8 run 9532 completed all 45 searches / 343 results; only S5 had zero eligible candidates.
- Local M8 fix accepts explicitly requested substation/switchyard as an operational grid setting and allows concrete machinery-only Commons categories to prove the machinery subject.
- Generic power-plant and contextual non-machinery protections remain fail-closed.
- Full suite 247/247 PASS; deterministic 9229 selected IDs unchanged.
- Production still M8 v59; fix not deployed yet.


## M8 v60 live; M5 continuous-narration scene-segment contract tested — 2026-09-22

- M8 v60 activeVersionId `980fdaec-f66b-45ba-8da0-d6005be00a9a`; scoped deploy verified clean.
- Fresh job `21f8e198-d15c-434d-b89a-d6772ddbc129` stopped in M5 execution 9537 only because five visual segments were required to be five standalone sentences.
- Local M5 fix makes scenes contiguous visual cut segments of one continuous narration; only the joined narration must be a complete utterance.
- Exact 9537 replay PASS; full suite 252/252 PASS; M5 syntax/graph PASS.
- Production still M5 v109 / M6 v8 / M8 v60. M5 fix not deployed yet.


## M8 v61 production checkpoint — 2026-09-22

- M8 v61 `a73aefbc-4c8e-4458-8ef2-c48bbce3a957` from commit `539fa22652814acbb4407dfd69e1a51314bc041c`.
- Generator/turbine hall is now treated as an operational power-generation setting only when real generating machinery and generation context are present.
- `hall` no longer becomes a hard domain qualifier.
- Wikimedia machinery categories cannot override a different explicitly named machine.
- 256/256 tests PASS; old 9229 selected assets unchanged.
- Waiting only for unrelated active production execution to finish before one fresh PL15.


## Manual acceptance rejected a machine-QA-passed PL15 — 2026-09-22

- Job `345adac7-105e-461b-97ff-1a66789704ba` rendered successfully, but manual review found a cross-scene visual-subject error and malformed visual-cut punctuation.
- S5 `Który wytwarza prąd.` incorrectly switched from generator to transformer. M5 local fix now enforces inherited visual primary for relative/personal anaphoric segments.
- Final canonicalizer normalizes `,.`/similar boundary artifacts without changing words.
- Full suite 260/260 PASS.
- Production remains M5 v110 / M6 v8 / M8 v61; M5 fix not deployed yet.


## M5 v111 deployed — 2026-09-22

- M5 v111 activeVersionId `31eaa7a9-98d1-44b6-bec6-416ef388753b`.
- M6 v8 and M8 v61 unchanged.
- Non-M5 workflow fingerprint unchanged.
- Live M5 == Git; Publisher/Studio 200; no n8n restart.
- Next action: one fresh PL15 only.


## Fresh PL15 machine QA passed — manual review pending — 2026-09-22

- Job `8ce87adb-3952-43cb-ab1d-7a1b2d549651`.
- M5 v111 PASS; M6 v8 PASS; M8 v61 PASS.
- visual_run `cfb7a60e-ed47-408f-85f9-3bbaa7626648`: PASS, 45/45 searches, 288 results.
- Job state: `machine_qa_passed`.
- No replacement PL15 should be launched.
- Next: inspect this exact final MP4 once SentinelX reconnects; only then decide pass/fail and next action.


## PL15 manual visual acceptance failed after machine QA — 2026-09-23

- Job `8ce87adb-3952-43cb-ab1d-7a1b2d549651` reached `machine_qa_passed`.
- Technical render PASS and audio/narration PASS.
- Manual visual FAIL on S2/S3/S4; S1/S5 PASS.
- Current blocker is M8 visual ranking/eligibility for water-flow, turbine-blade, and operating-turbine scenes.
- No new PL15 until M8 is fixed from saved execution `9601` data.


## M8 visual-detail fix tested — 2026-09-23

- Current production remains M5 v111 / M6 v8 / M8 v61.
- Local M8 fix rejects the exact S2/S3/S4 false positives from job `8ce87adb-3952-43cb-ab1d-7a1b2d549651`.
- Specific hard visual-detail anchors are component-only and derived generically from storyboard intent + first query.
- Full suite 265/265 PASS.
- Old deterministic 9229 selections/pools unchanged.
- Fix not deployed yet; next action is M8-only deploy after Git checkpoint.


## M8 v62 deployed — 2026-09-23

- M8 v62 activeVersionId `90329f54-40fd-4382-92fd-2fd1e9ecea01`.
- M5 v111 and M6 v8 unchanged.
- Non-M8 workflow fingerprint unchanged.
- Live M8 == Git; Publisher/Studio 200; no n8n restart; worker healthy.
- Next: one fresh PL15, then technical/audio/manual visual acceptance.


## Fresh PL15 failed M5 anaphoric guard — 2026-09-23

- Job `5429bbe8-9b13-4fe6-b3f4-9b6c36d5a9dc`, M5 execution `9609`.
- M8 v62 was not reached.
- Current blocker: anaphoric guard wrongly rejects an explicitly named new object (`generator`) in `która wprawia w ruch generator`.
- No new acceptance job until M5 guard is fixed and deployed.


## M5 explicit-object anaphora fix tested — 2026-09-23

- Production remains M5 v111 / M6 v8 / M8 v62.
- Local M5 fix accepts explicit new visual primary in an anaphoric segment only when that primary is lexically named in the same narration.
- Exact execution 9609 replay PASS.
- Old unmentioned-transformer regression remains rejected.
- Full suite 266/266 PASS.
- Fix not deployed yet.


## M5 v112 deployed — 2026-09-23

- M5 v112 activeVersionId `d7eab2c2-c0a6-4258-9c17-4a28a706a701`.
- M6 v8 and M8 v62 unchanged.
- Live M5 == Git; non-M5 workflow fingerprint unchanged.
- Next: one fresh PL15, then manual acceptance.


## PL15 on M5 v112 failed antecedent-position guard — 2026-09-23

- Job `d74ebc77-dfe1-4440-8d06-357b584785d2`, M5 execution `9613`.
- M8 v62 was not reached.
- Current blocker: M5 assumes a leading relative pronoun refers to previous visual primary even when a later noun/result in previous narration is the actual antecedent.
- No new PL15 until deterministic antecedent-position refinement is tested and deployed.

## M5 9613 antecedent-position fix tested — 2026-09-23

- Current production: M5 v112 / M6 v8 / M8 v62.
- Local M5 fix handles a leading anaphor whose true antecedent is a later noun in the previous narration cut rather than the previous visual primary.
- Exact 9613 regression PASS.
- Old transformer rejection and 9609 explicit-object regression preserved.
- Focused 11/11 PASS; full suite 267/267 PASS.
- Fix not deployed yet.

## M5 v113 deployed — 2026-09-23

- M5 v113 activeVersionId `8e841105-87de-4816-8a15-224ec30b4350`.
- M6 v8 and M8 v62 unchanged.
- Non-M5 workflow fingerprint unchanged.
- Live M5 == Git; Publisher/Studio 200; no restarts.
- Next action: exactly one fresh PL15.

## M5 9617 branch-safe precision fallback tested — 2026-09-23

- Fresh PL15 `a3da9db9-d818-4a83-a217-48ff080637f1` failed in M5 execution `9617` because `Build Timing Precision Retry` read an unexecuted `Validate Repaired Storyboard` branch.
- Local fix uses guaranteed `Normalize Timing Probe.storyboard` instead.
- Focused timing 16/16 PASS; full suite 268/268 PASS.
- Production remains M5 v113 / M6 v8 / M8 v62 until deploy.

## M5 v114 deployed — 2026-09-23

- M5 v114 activeVersionId `34b07b1f-2b22-4c6c-a68e-54e5e05fab22`.
- M6 v8 and M8 v62 unchanged.
- Non-M5 workflow fingerprint unchanged.
- Live M5 == Git; Publisher/Studio 200; no restarts.
- Next: exactly one fresh PL15.

## M5 9621 pre-TTS punctuation canonicalization tested — 2026-09-23

- Fresh PL15 `94f5e4ff-b6b3-4ebf-b161-98deb3c7bbe7` failed in M5 execution `9621` at accepted voiceover candidate registration.
- Root cause: probe-3 TTS/ledger used 189-char narration with three `,.` artifacts; final canonicalizer then changed it to 186 chars, so exact-audio usage no longer matched final narration.
- Local fix canonicalizes visual-cut punctuation in Prepare Timing Probe 1–5 before TTS/usage reservation.
- Focused exact-audio 8/8 PASS; full suite 269/269 PASS.
- Production remains M5 v114 / M6 v8 / M8 v62 until deploy.


## M5 v115 deployed and verified — 2026-09-23

- M5 v115 `4ec491e1-fb68-4c5e-8125-c6d501e7d48d`.
- M6 v8, M8 v62, M9 v1 unchanged.
- Live M5 matches Git.
- Non-M5 fingerprint unchanged.
- Publisher/Studio 200; no n8n restart; media worker healthy.
- Next action: exactly one fresh PL15.


## Current blocker: M5 execution 9629 — 2026-09-23

- Job `fd7d4a16-cb18-4871-b5ba-c53ef2126c63` failed in M5 v115 before M6.
- Provider final word-count retry was valid and matched immutable original.
- Deterministic hybrid admitted semantic-invalid base/pre_final options before DP.
- Current action: filter hybrid options semantically before DP in `Validate Final Word Count Retry`; no new PL15 yet.


## M5 9629 fix tested — 2026-09-23

- `Validate Final Word Count Retry` now filters retry/base/pre_final options semantically before DP.
- Exact 9629 regression 2/2 PASS; full suite 271/271 PASS.
- Not yet production-complete until M5-only deploy is verified.


## M5 v116 deployed and verified — 2026-09-23

- M5 v116 `64654d56-c7c8-481f-8bd3-37e37cc27289`.
- M6 v8 / M8 v62 / M9 v1 unchanged.
- Live M5 matches Git; non-M5 fingerprint unchanged.
- Publisher/Studio 200; no n8n restart; media worker healthy.
- Next: one fresh PL15 only.


## Current blocker: M5 execution 9633 — 2026-09-23

- Job `72af62de-3c64-4b48-bf6b-c1395e07abed` failed before M6.
- False anaphora restriction: no lexical grounding for English `water reservoir` in Polish narration was treated as positive antecedent evidence.
- Planned fix: no-match => restriction does not apply; positive terminal matches remain fail-closed.


## M5 9633 fix tested — 2026-09-23

- Cross-language no-match no longer invents antecedent certainty.
- Positive terminal lexical matches remain fail-closed.
- Exact 9633 regression PASS.
- Full suite 273/273 PASS.
- Not production-complete until M5-only deploy is verified.


## M5 v117 deployed and verified — 2026-09-23

- M5 v117 `e368d875-ebae-4c7b-ab38-6683c218a1d4`.
- M6 v8 / M8 v62 / M9 v1 unchanged.
- Live M5 matches Git; non-M5 fingerprint unchanged.
- Publisher/Studio 200; no n8n restart; media worker healthy.
- Next: one fresh PL15 only.


## Current blocker: M8 execution 9640 — 2026-09-23

- Job `835c8fc3-7d0b-425f-ab9e-62c19788c8a3`: M5/M6 PASS, M8 FAIL.
- S3 and S4 both had zero eligible candidates.
- Confirmed issue is retrieval planning, not missing source material: Commons has suitable generator+turbine-unit and generator-interior photos under structurally better queries.
- Planned fix: remove process/output pseudo-domains and enrich provider queries with paired-machinery `unit` and inside-location `interior`; scorer unchanged.


## M8 9640 retrieval-planning fix validated — 2026-09-23

- Production still M8 v62 until deploy.
- Planner-only fix removes output/process pseudo-domains and adds structural retrieval terms for exact 9640 S3/S4.
- Scorer unchanged.
- Full suite 283/283 PASS.
- Deterministic 9229 replay PASS.
- Live current-query diagnostic:
  - S3 q3 -> 2 eligible Commons assets;
  - S4 q3 -> 2 eligible Commons assets.
- Next: M8-only deploy, then one fresh PL15.


## M8 v63 deployed — 2026-09-23

- M8 v63 activeVersionId `7256ee89-8b9a-47df-bdc9-66bd2136df35`.
- M5 v117 / M6 v8 / M9 v1 unchanged.
- Non-M8 workflow fingerprint unchanged.
- Live M8 == Git; Publisher/Studio 200; no restarts.
- Next: exactly one fresh PL15 only.


## Current blocker: M5 execution 9660 — exact word-count compliance

- Fresh PL15 job `6aa86246-ec15-4514-a688-d150129d35ad` failed in M5 v117.
- 26-word narration is genuinely too short (12.984 / 13.200 / 13.128 s).
- Target 29 is justified.
- Gemini hard retry returned 22 words instead of 29; existing semantic hybrid could only reach 26.
- Timing/semantic gates remain unchanged.
- Next: bounded compliance retry + deterministic 9660 regression; no new PL15 before M5 fix/deploy.


## M5 9660 compliance fix ready for deploy — 2026-09-23

- One bounded final exact-word compliance retry implemented.
- No timing/semantic gate weakened.
- Full suite 288/288 PASS.
- M5 graph PASS; 59/59 Code-node syntax PASS.
- Pending: commit/push then M5-only production deploy.


## M5 v118 deployed — 2026-09-23

- M5 v118 activeVersionId `346ad9c2-1cc2-4c8d-ac37-6ae540b1fff1`.
- M6 v8 / M8 v63 / M9 v1 unchanged.
- Non-M5 workflow fingerprint unchanged.
- Live M5 == Git; Publisher/Studio 200; no restarts.
- Next: one fresh PL15 only.


## Current blocker — M5 precision validator destroys continuous narration — 2026-09-23

- Fresh PL15 `ab79e346-a7d7-45c4-9bc9-a82212bab1c4` is machine-QA PASS but manual acceptance FAIL.
- Root cause is `Validate Timing Precision Retry.normalizeSentenceSurface`: it adds periods/capitalization at every visual cut.
- Gemini precision response itself preserved correct continuous segment surfaces.
- No EN30/new PL15 until M5 validator regression is fixed/tested/deployed.


## M5 9672 continuity fix ready for deploy — 2026-09-23

- Forced per-scene punctuation/capitalization removed from precision validator.
- Exact 9672 regression preserves continuous narration across visual cuts.
- Full suite 290/290 PASS.
- M5 graph PASS; 59/59 Code-node syntax PASS.
- Pending: commit/push, M5-only deploy, one fresh PL15.


## M5 v119 deployed — 2026-09-23

- M5 v119 activeVersionId `bad8d367-3399-4ada-87c4-3a6d6c044b62`.
- M6 v8 / M8 v63 / M9 v1 unchanged.
- Live M5 == Git and non-M5 fingerprint unchanged.
- Next: one fresh PL15 and full manual acceptance.


## Current blocker: M8 execution 9683 — 2026-09-23

- Post-v119 PL15 job `a6d8d4dc-c30c-41ef-b816-0301fdfd1cda`.
- M4/M5/M6/M7 passed; M8 v63 execution `9683` failed S4-A; M9 did not run.
- Eligible pools: S1=10, S2=2, S3=2, S4=0, S5=3.
- Wikimedia `135264822` is a hydro generator whose direct caption explicitly says `hydro power plant` and `in working condition`, but it is rejected only as `missing_operational_setting_context`.
- Root cause: the scorer has secondary/context metadata for short direct captions, but operational-setting checks use only strong primary metadata.
- Fix scope is operational context/lifecycle evidence only. Do not weaken primary depiction, must_show, domain or score thresholds.
- Evidence: `docs/acceptance/2026-09-23-m8-9683-operational-context-fail.json`.


## M8 9683 operational-context fix tested — 2026-09-23

- Fix is limited to operational setting/lifecycle evidence.
- Wikimedia may use its concise direct caption as context evidence, but not as primary depiction proof.
- Pixabay/Pexels operational evidence behavior is unchanged.
- `disused/decommissioned/abandoned/inactive/retired` explicitly conflict with an operational machinery shot.
- Exact positive/negative 9683 regressions PASS.
- Focused 42/42, full 293/293, 9229 replay 12/12 PASS.
- 9229 selected assets and eligible counts unchanged.
- JSON/diff/M8 Code-node syntax PASS.
- Not production-complete until M8-only deploy is verified.


## M8 v64 deployed and verified — 2026-09-23

- M8 v64 activeVersionId `88b9f81a-6d41-452b-8a35-082b7c088006`.
- M5 v119 / M6 v8 / M9 v1 unchanged.
- Backup `.backups/m8-before-9683-context-20260923-123042.json`, SHA256 `f535079c5f3ff6f538fc29c20c4a3635a106707227e76a7d3567c28d6ae5fd47`.
- Other 31 workflows unchanged by fingerprint `31|935f3b89581cc695b22bca91b315f846`.
- Live M8 == Git; Publisher/Studio 200; n8n restart 0; media worker healthy restart 0.
- Active project executions = 0.
- Next: exactly one fresh PL15 on v119/v64 and full manual acceptance if it reaches M9.


## Current blocker: fresh PL15 M5 execution 9687 — 2026-09-23

- Job `bfac49a7-bde2-4ec0-85fc-7dd9b6afbc36` is terminal `script_failed`.
- M4 passed; M5 v119 execution `9687` failed; M6-M9 did not run.
- Error: `got 27, target 31, allowed delta 2 [line 431]`.
- Classifier and compliance-route nodes executed, but the bounded compliance Build/Repair/Validate branch did not.
- Root cause is not yet proven. No M5 change is authorized until exact classifier/router data is inspected.


## M5 9687 root cause proven — 2026-09-23

- n8n delivered the final word-count validator error as a string in `$json.error`.
- The classifier only parsed object-form errors, produced an empty classification message, and set `compliance_retry=false`.
- The existing bounded compliance retry branch therefore did not run.
- Fix is limited to classifier error normalization; retry eligibility must remain narrow.


## M5 9687 classifier fix tested — 2026-09-23

- String-form n8n validation errors are now normalized in the final measured word-count retry classifier.
- Retry eligibility remains narrow: only the existing full message or the exact stripped `got N, target N, allowed delta N [line N]` format.
- Unrelated string errors remain fail-closed.
- Focused 10/10, full 293/293, JSON/diff/59 M5 Code nodes PASS.
- Not production-complete until M5-only deploy is verified.


## M5 v120 deployed and verified — 2026-09-23

- M5 v120 activeVersionId `28f7440c-9410-4143-8962-352f967cfe1f`.
- M6 v8 / M8 v64 / M9 v1 unchanged.
- Backup `.backups/m5-before-9687-classifier-20260923-131636.json`, SHA256 `4a512505d75848a7f432cf4dc328bd0f5113c502f877ff0d19cbd6661402c50e`.
- Other 31 workflows unchanged by fingerprint `31|cfacbe4e094739b106490c3c93ec2506`.
- Live M5 == Git; Publisher/Studio 200; n8n restart 0; media worker healthy restart 0.
- Active project executions = 0.
- Next: exactly one fresh PL15.


## Current blocker: M5 execution 9692 — 2026-09-23

- Fresh PL15 job `4dc1af7d-0ec9-4af5-8557-e926beef4cac` failed in `Validate Final Duration Repair`.
- Builder targets were `[10,5,4,3,5]`; PL15 hard scene bound is 2-10 words.
- Gemini returned scene counts `[11,7,5,7,6]`; S1 exceeded the hard bound.
- Root cause is prompt/validator mismatch: prompt calls per-scene targets preferences but omits the absolute 2-10 hard bound.
- Fix prompt contract only; keep validator fail-closed.


## M5 9692 late-timing prompt fix tested — 2026-09-23

- Both late-timing builders now expose the same hard scene bound that validators already enforce.
- PL15 hard bound: 2-10 words per scene.
- target_words remain soft timing guidance.
- Focused 37/37, full 294/294, JSON/diff/59 Code nodes PASS.
- Not production-complete until M5-only deploy is verified.


## M5 v121 deployed and verified — 2026-09-23

- M5 v121 activeVersionId `692ceedd-a51c-45c5-bf1e-c85814129e4d`.
- M6 v8 / M8 v64 / M9 v1 unchanged.
- Backup `.backups/m5-before-9692-scene-bound-20260923-133216.json`, SHA256 `92098a8015c357dfb373dba9f2f84899e22f0913e85401369c12f238183e9f51`.
- Other 31 workflows unchanged by fingerprint `31|cfacbe4e094739b106490c3c93ec2506`.
- Live M5 == Git; Publisher/Studio 200; restart 0; supporting services healthy.
- Active project executions = 0.
- Next: exactly one fresh PL15.


## Current blocker: M5 execution 9699 — 2026-09-23

- Job `d0d127b8-c70a-4cef-b3ae-1dc2cc43e104` is terminal `script_failed`.
- Initial / repair1 / repair2 visual-primary failures: power lines -> transformer station -> electrical substation, each replacing inherited `electric generator`.
- S5 narration starts with `który` and does not explicitly name a new visual primary; validator correctly rejects the switches.
- Repair 2 received only stripped `A -> B [line 698]` diagnostics.
- Candidate fix already exists uncommitted in shared working tree: generic stripped-error normalization in both repair builders plus regression test.
- Validate before commit/deploy; keep validator strict.


## M5 9699 candidate fix tested — 2026-09-23

- Both storyboard repair builders now expand stripped anaphoric validator diagnostics into a generic antecedent-preservation instruction.
- Unrelated validation errors are unchanged.
- Validators remain strict; no topic-specific logic.
- Focused 35/35, full 295/295, JSON/diff/59 M5 Code nodes PASS.
- Pending M5-only deploy.


## M5 v122 deployed and verified — 2026-09-23

- M5 v122 activeVersionId `4a9a48fd-985c-4f77-b592-44a0945377dd`.
- M6 v8 / M8 v64 / M9 v1 unchanged.
- Equivalent predeploy backups:
  - `.backups/m5-before-9699-repair-error-20260923-135152.json`
  - `.backups/m5-before-9699-anaphoric-20260923-135204.json`
- Both backups SHA256 `a7ff82d9608b05cd8648d856dd9f2023adcd7208dd47d55f1f4cb814a4f20628`.
- Other 31 workflows unchanged by fingerprint `31|cfacbe4e094739b106490c3c93ec2506`.
- Live M5 == Git; Publisher/Studio 200; n8n restart 0; media worker healthy restart 0.
- Postgres/SearXNG healthy; active project executions = 0.
- Next: exactly one fresh PL15.


## Current blocker: render letterboxing after machine QA PASS — 2026-09-23

- Job `e8d662c9-cd28-4228-9169-6ac875ff0d16` passed M4-M9 and machine QA.
- Audio/content review passes.
- Manual frame review fails because still images are rendered with black top/bottom bars inside the 1080x1920 canvas.
- Cropdetect from final MP4: S1 1080x1620, S2 1080x1384, S3 1080x1698, S4 1080x720, S5 1080x1820.
- S4 leaves 600 black rows at both top and bottom.
- Next: generic M9/media-worker scale/crop fix; do not accept this PL15 and do not start another acceptance job yet.


## Render root cause confirmed — 2026-09-23

- Current media worker intentionally uses contain + black pad.
- Hard center crop is not an acceptable rollback: it previously caused important edge-object loss.
- Chosen generic fix: blurred full-frame background + complete proportional foreground.
- Scope: media-worker renderer and its render-fit regression only.


## Blurred-fill renderer fix tested — predeploy

- Still photos now keep the complete source as foreground and use a blurred cover copy behind it.
- Synthetic FFmpeg regression preserves edge content and removes black letterbox.
- All five exact failed PL15 assets render as full 1080x1920 content by cropdetect.
- Full Node suite 295/295; Python compile and diff checks PASS.
- Not production-complete until the media-worker-only deploy is verified.


## Blurred-fill media-worker live — 2026-09-23

- New worker image `sha256:40d31f96de302b8bf0f69bd07e5d9dac2d82a8ed8e102fc0a1c383ea4129fd3c`.
- Live server.py exactly matches Git.
- Worker healthy, restart 0.
- Supporting containers unchanged.
- Publisher/Studio 200; active executions 0.
- Next: one fresh PL15 and manual MP4 review.


## Current blocker: M8 contextual Wikimedia depiction false positives — 2026-09-23

- Fresh PL15 `33aa659d-e6b6-4529-8e41-8dd830f3b920` passed machine QA.
- Blurred-fill renderer is confirmed fixed in the actual production MP4.
- Audio is correct and continuous.
- Manual visuals fail S1 and S5.
- S5 is decisive: Wikimedia 136934049 is visually a forest/survey-tripod archive photo, but its catalog title mentions transformer/substation/transmission and M8 accepted those contextual words as depiction evidence.
- Next: tighten generic Wikimedia primary-depiction grounding; M8 scorer stays fail-closed and no new PL15 before deploy.
