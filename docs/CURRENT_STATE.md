## Current continuation — material-call budget fix in progress, 2026-11-11

Fresh normal job `e23b6fc2-295c-4e70-ae2e-91243c0662ad` is terminal at `story`; do not resume or retry it. It reached 9 accepted photos, but materials consumed 15 Gemini calls and research consumed 2. The existing story+voice reserve is 12; only 11 calls remained, so story preflight stopped before any story provider call. The VPS and public Studio are healthy; this was avoidable per-photo review call overhead, not a server outage.

Candidate based on exact `e319c29603db64a425415a6b8bf24dcb355d6675` batches the same independent visual-entailment review across up to 4 already accepted photos and 8 MiB. The initial photo inspection and all independent review gates remain enabled. The regression models 32 candidates with 9 accepted across 8 initial batches and checks 8 initial calls plus entailment groups `[4,4,1]` (11 material calls rather than 15). Focused budget, entailment, and resume tests: 17/17 PASS; `git diff --check` PASS. No new provider calls, job, deployment, or MP4 from this candidate.

Next: inspect and reclaim only safe Docker build-cache space (root filesystem had 59 MiB free), commit/push the candidate, build and run exact-image network-disabled checks, then use the protected rollout procedure and submit one fresh normal request only after the live revision is verified. Keep the failed job immutable, free-only model/budget, retry limits, photos and factual/visual gates unchanged. `project_ready=false` for the current candidate until fresh production MP4 and media audit pass.

## Latest acceptance blocker — 2026-10-12

Последний gate-аудит выявил две ошибки retry-пути: повторные модельные ремонты делили один durable call key, а цикл обрывался перед второй разрешённой коррекцией. Исправлены уникальные ключи initial/review и лимит ровно в две коррекции; regression воспроизводит fact repair → плохие photo hints → query-only repair. Целевые тесты 23/23 и material-first 198/198 PASS. Точный amd64 package `factory-v3:repair-retry-f45c6ec-amd64` (`sha256:e613eb5f47f8bd480fc97a93531b68ab9636ae4231bf70a11ce93f2eb5b8913e`) прошёл network-disabled suites: material-first 198/198, Factory v3 112/112. Production не менялся.

The latest local gate audit found two more factory defects: repair calls reused one durable request key, and the bounded review loop stopped before its second allowed correction. Fixes now assign distinct initial/review keys and allow two corrections before terminal rejection. A regression covers fact repair followed by bad photo hints and a query-only repair. Targeted checks 23/23 and material-first 198/198 pass. The exact amd64 package `factory-v3:repair-retry-f45c6ec-amd64` (`sha256:e613eb5f47f8bd480fc97a93531b68ab9636ae4231bf70a11ce93f2eb5b8913e`) passed network-disabled suites: material-first 198/198 and Factory v3 112/112. Production is unchanged.

UK60 preparation `6914b51b-f8c3-47d1-919e-f7b5cc15ffce` is immutable: 30 photos downloaded/inspected, 1 accepted, then stopped before TTS/render because 60 seconds requires at least 12 unique photos. Production still runs `factory-v3:distinct-context-repair-amd64-20261012-r1`, revision `bc3eaae`; no deployment or provider calls were made during this work. Read-only status: 28 jobs, 110 preparations, no active work, 327 MB free. Studio remains public at `https://studio.hodor.com.pl/`, without a password.

Post-failure PostgreSQL receipts showed the initial brief was repaired into the actual search hints `space`, `neutron star`, and `Hubble Space Telescope`; the following review checked facts only. The pushed fix now validates hints after every repair and prevents a query-only repair from changing facts/source bindings. Actual repaired hints and call hashes are in `tests/material_first/fixtures/actual-photo-hint-repair.json`; this fixture deliberately lacks the complete source/provider payload.

Commits `2cb7bf7`, `e0f3697`, and `cff1b54` are pushed to `factory-v3`. The exact AMD64 image from `e0f3697` was built but not deployed; network-disabled suites passed 197/197 material-first and 112/112 Factory v3. Receipts are in `acceptance/factory-v3/photo-hint-review-*`. `project_ready=false`; there is still no accepted new MP4.

Next: complete the read-only source/provider replay for the failed preparation, preserve and hash the exact source spans/model outputs, then close the connected offline release-gate corpus across PL/EN/RU/UK and 15/30/45/60. No fresh production request before that gate closes. Keep failed IDs immutable and all photo relevance/uniqueness/cadence gates strict.

## Previous acceptance blocker — 2026-10-11

UK60 natural-speed regression r14 `19e8ad95-60a2-48cc-893b-491e235d9fd3` is immutable and failed at render: two measured voices were 50,928 and 59,616 ms, then render found only 5 relevant photos for the 9 cuts in the longest interval. Two TTS and three Gemini calls were spent; no render exists. Production now runs amd64 image r2 at revision `614090f`: it preflights photo capacity before each TTS and selects the closest-duration paragraph combination that preserves that capacity. Exact image tests passed (material-first 182, factory-v3 112). App/Studio health200; free Gemini 3.5 billing-disabled proof and DB counts unchanged; no new provider calls or jobs. VPS root has 371 MB free (99% used). Read the visual-capacity and voice-variant plans under `acceptance/factory-v3/`. `project_ready=false`; no actual accepted MP4 or audio/HUMAN review.

## Studio moved to its domain; public UI deployed — 2026-10-11

`studio.hodor.com.pl/` now serves the current factory UI directly, without the previous redirect to publisher and without a password prompt. Studio Caddy root rewrites internally to `/factory-v3/`; its API/assets share the studio origin. Removed publisher's `/factory-v3` route while preserving n8n, recovery and existing studio webhooks. App image `factory-v3:c921bd0`, exact source revision `c921bd0a12bb06f22de477a0cceb8824b283603b`, health200. Anonymous GET of studio root, JS and session endpoint returned200; former publisher factory path returned404. Caddy backup and private settings backup are retained; settings changed only `public_origin` and `public_access`. Active V3 job/preparation/stage/call counts were0 before restart; no provider calls or new MP4. Public access makes studio history and API reachable by all site visitors. No test suite run. This UI deployment does not change `project_ready=false` or product acceptance. Receipt `acceptance/factory-v3/studio-public-deployment-20261011.json`.

## Image/connected worker gate passed; scoped rollout authorized — 2026-10-06

Exact source5ff1ce84b2afffc0808b21a676d251a979373387 built as factory-v3:5ff1ce8, imageIDsha256:8695690c168d07d269f2dc8289f42a6f0d357def9a07d1296810c284aa474096. Packaged51 replacement+86 legacy tests PASS, network disabled. Two initial legacy harness mounts lacked correct root/acceptance fixture; corrected read-only fixture mounts, no runtime correction/rebuild. Isolated actual PhotoWorker staging/render/QA PASS: saved RU45 voice57.552s fit1.2789333333,23 whole original photos,45.000s/1350frames, AAC correlation0.999975991633632; zero providers. Fixture6e24b0cb-4455-43d3-a660-001703fa0960 under /var/lib/factory-v3/whole-fixture-6e24b0cb, saved input volume read-only. This is a controlled rendering boundary, not a production/model/HUMAN acceptance.

Preflight active preparations/stages/nondeleted n8n executions all0. Protected34 workflow rows digestf03a2dc3cd6a4432330e3a5e2c7c84c2 using sorted per-row hashes; all7 V3 table row digests, supporting service IDs/images and private-settings SHA captured. Runtime stillcab79d3 until rollout completes. Only live compose app image changes to5ff1ce8, all other config must compare identical. Run the single receipt-producing scoped replacement, preserve old YAML and current image, stop on unknown effect and inspect. Verify exact running image/revision, public UI/health/JS bytes and unchanged protected snapshot before fresh normal RU30 request383bcc36-4d1a-4690-8810-275e338e7d46. No gateway/Caddy/schema/credential/other-service changes, no old-ID retries. Actual receipts are acceptance/factory-v3/connected-presentation-*.

## Connection authorized — whole-photo exact presentation, 2026-10-06

User explicitly requested connecting the corrected montage to the website. Implemented versioned whole-photo-exact-v1 policy: originals retained for inspection/render; bounded discovery preferred ceil(seconds/2)+12 candidates; inspection groups<=4 with total input<=8MiB, within unchanged Gemini16 ceiling; completed malformed individual rows reject only their images (unknown/provider errors remain terminal). Source-backed narration uses5–8 paragraphs independently of8/15/23/30 preferred visual photographs. Frozen pool verifies exact bytes, distinct IDs/hashes, whole-original framing and cadence before voice. PhotoWorker stages the entire pool, synthesizes once, aligns original voice, fits its tempo without pitch change, schedules distinct photographs independently, and runs frame-count/packet-timestamp exact render and independent final audit. Owner detail/photo routes show the entire frozen pool and final actual duration/photo count; existing plans retain legacy execution contracts.

51 replacement+86 legacy unique controlled tests PASS; browser JS syntax PASS. New image build, isolated actual PhotoWorker render/QA and deployment PENDING. Live app stillcab79d3. Release plan: acceptance/factory-v3/connected-presentation-release-plan-20261006.json. Build exact committed source in isolated checkout; package tests network-disabled; one isolated bread45/23-photo saved-media worker render/QA, zero provider calls. Then assert no running preparations/stages/nondeleted n8n executions, capture protected DB/workflow/service fingerprints; replace ONLY factory-v3 app, preserve settings/gateway/Caddy/schema/unrelated services and old jobs. Verify actual image/revision, public UI/health, protected digests. One fresh normal RU30 owner request with listed budgets only after those pass; source IDs/failed jobs remain immutable. project_ready=false until actual current-release/human acceptance; no automatic matrix repeats.

## Current correction — exact duration and whole photographs, 2026-10-06

The user rejected the previous varied previews for duration, too few photographs and cropping. New separate viewing artifacts are delivered: EN coffee30.000s/15 distinct photos/900frames; RU bread45.000s/23photos/1350frames; UK water60.000s/29photos/1800frames. Original photographs are shown whole with aspect preserved and solid matte, no crop/blur/animation. Cuts average2.00/1.96/2.07s and are independent of narration sentences. Existing single-TTS tracks are reused with pitch-preserving tempo0.7416/1.2789333333/1.2236. Original audio and photo bytes remain unchanged. No new TTS/Gemini/search calls; one bounded cached-result catalog downloaded10 water photos, all receipts retained.

Source: material_first/presentation.py and scripts/render_whole_photo_preview.py;41 replacement+84 legacy tests PASS. The initial frame-counted concat still accumulated9–10ms from rounded segment container durations. Packet timestamps normalized by setts at30fps, without re-encoding existing video/audio; final video/audio/container durations exactly match all three requests. All output files fully decoded, fitted-track/final-audio correlation>=0.9999759, all67 representative final shots visually inspected, downloaded MP4 SHA matches receipts. No listening/HUMAN or ASR phrase-alignment claim. Source frozen jobs and original failed/UNKNOWN jobs remain immutable.

Proof: acceptance/factory-v3/whole-photo-previews-20261006.json, whole-photo-{coffee,bread,water}-plan-20261006.json, whole-photo-water-download-receipt-20261006.json. Actual videos are outputs/{coffee-en-30s-whole,bread-ru-45s-whole,water-uk-60s-whole}.mp4 under /Users/hodor/Documents/Codex/2026-10-05/new-chat. VPS separate artifact IDs: coffee ddf7aa8f-a172-408a-9d96-8e81bdb26b74, bread52a842fc-c65e-464c-b2db-639c39cfdb70, water bf3b9211-6ad8-4785-aa0f-887c4e0491ec; directories /data/whole-photo-previews/<ID>/final-exact.mp4 and proof-exact.json. Initial outputs are preserved separately in those directories.

**Not deployed/wired into the automatic product.** Live app remains cab79d34ad3475e43acd8baf301281deb7a39dc5 /factory-v3:cab79d3. project_ready=false. New renderer is implemented and actual-media verified; manually selected cached previews do not certify automatic discovery/inspection/planning. Remaining integration: preserve originals in download/inspection; collect and validate a larger diverse pool with bounded/batched inspection; separate source-backed narration beats from independent visual cuts in frozen plans; wire fitted audio, exact packet timestamps and actual-photo-count QA into PhotoWorker; update owner preview/review contracts. Close these connected boundaries offline with saved receipts before deployment and a fresh bounded product case. Do not retry immutable job IDs or another full prompt-patch matrix.

## COMPACT OUTLINE SCHEMA ACCEPTED LIVE; EXACT IMAGE BUILD NEXT

Execution12143 compact outline schema HTTP200, finishMAX_TOKENS expected diagnostic256 cap, usage264 tokens. Same instruction/context/model with array grammar bounds12141 was400; only provider schema grammar changed. This establishes accepted compact schema, NOT completed outline/video. Local exact array/string/count/semantic acceptance stays strict. Source704f01a,79/79 Python PASS. No source/job rescue/TTS/new product.

BOUND compact-schema-build-20261005: fresh remote detached .tmp/v3-schema-build-704f01a from exact704f01a after fetch, Docker image factory-v3:704f01a with SOURCE_REVISION full hash. Build bounded background, private no secrets involved, record image/revision; run packaged79 tests network-disabled against exact source tests. SQL/executor/adapters/services unchanged since earlier realPG package gates, reuse those gate results with explicit scope. No service starts/deployment/provider calls. Only after package verification, change compose image tag and config-check; active preparations/stages/nondeleted executions must be0 before a separately recorded ONLY-app replacement. Gateway/Caddy/credentials/DB/other services untouched. Failed jobs immutable; project_ready=false.

## STRING-KEYWORD HYPOTHESIS REJECTED; COMPACT PROVIDER GRAMMAR TEST NEXT

Execution12141 compiled supported schema still400 INVALID_ARGUMENT; string-keyword omission did not resolve blocker. No runtime deployment/new job/TTS. Array bounds nested64 facts x6 support plus5 units are remaining grammar-complexity hypothesis. provider_schema now emits array count requirements as documented description text and retains type/properties/items/required/enums/closed objects; original local array/string/exact-count validation remains mandatory and unchanged. This is a provider-grammar simplification, not acceptance weakening. Regression explicitly rejects wrong array counts.

NEXT gemini-compact-schema-20261005 ONE controlled call, same fixed context/instruction/model,256 max output, only compiled schema difference from failed12141. No retry/TTS/product. Plan gemini-compact-schema-plan.json. Require HTTP200 to establish changed schema is accepted; diagnostic truncation is never product PASS. Do not deploy until proof/current-image verification. Prior400 receipts preserved. project_ready=false.

## SCHEMA CLASS PROVEN; DOCUMENTED SUBSET COMPILER OFFLINE PASS

Controlled simple schema execution12139 HTTP200/STOP usage33 tokens; same model/instruction/context with outline schema execution12140 HTTP400 INVALID_ARGUMENT. Auth/context/native request transport excluded. Unsupported string keywords minLength/maxLength absent from official documented subset are a specific hypothesis, not yet live proven. New provider_schema compiles documented keywords and omits only local string lengths; full original schema still validates responses, field names preserved and unknown keywords fail before HTTP. 79/79 Python +gateway guards PASS. Corrected full native HTTP harness PASS; failed explicit Content-Type assumption preserved because request helper json=true supplies it, confirmed by native capture and real200.

NEXT gemini-supported-schema-20261005: ONE controlled generation using same fixed instruction/context and compiled outline schema, max256 output tokens, no TTS/product job. Compare HTTP status; output truncation allowed only as diagnostic, never product acceptance. Plan gemini-supported-schema-plan.json. No retry. If accepted, build/test exact committed runtime and scoped app update before any fresh job; gateway unchanged. If rejected, do not deploy speculative compiler as proven fix; isolate schema complexity using offline/direct boundary evidence. Current live runtime2a6d997; gateway9891e8d9; failed jobs immutable; project_ready=false.

## GEMINI MODEL/AUTH/NATIVE REQUEST BOUNDARIES PASS; SCHEMA DIAGNOSTIC PLANNED

Metadata execution12138 HTTP200 exact model supports generateContent, input1048576/output65536. Query-key hypothesis disproved for metadata path. Full installed native HttpRequestV3.execute with only transport mocked, network-disabled exact image PASS: structured body/Unicode/systemInstruction sent unchanged and response body retained. Harness gateway_native_http.js; native-http-test.json. No product rescue/new job/TTS.

BOUND gemini-schema-boundary-20261005: max2 generation diagnostics,256 output tokens each, same fixed controlled instruction/context/model and only schema varies. Simple schema first; only if HTTP200, outline PL15 three-source-ID schema second. HTTP status/finish/usage captured, no requirement to finish full complex JSON within256. Separate from failed job; no source text or narration reuse. Free-tier proof remains verified billingEnabled=false; exact total quota includes unknown thinking/input until response usage. No retries; stop transport ambiguity or baseline failure. Success simple+400 outline proves schema class; both200 leaves actual context/payload difference unresolved. Keep gates/local validation strict; do not reduce/alter schema before evidence. Plan gemini-schema-boundary-plan.json. Project_ready=false.

## 2026-10-05T19:20:29.185172+00:00 — NEW JOB TERMINAL UNKNOWN AT FIRST GEMINI CALL

Immutable7ef29657-1b98-4236-bcf6-01a7482c8f29 passed billing/research/three source fetches; evidence-outline gateway12137 HTTP400 INVALID_ARGUMENT generic Request contains an invalid argument. Preparation unknown, no execution job/TTS/MP4. No repeat/rescue. Live body contract remains verified. Receipt response-body-product-terminal.json.

Installed @n8n/n8n-nodes-langchain GooglePalmApi authenticate uses qs.key. Official API key docs show header x-goog-api-key but do NOT establish query rejection; this is a hypothesis only. Model official output limit65536 means outline max16384 is valid. Schema complexity remains possible. Official links https://ai.google.dev/gemini-api/docs/api-key , https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite , https://ai.google.dev/gemini-api/docs/structured-output (verified2026-10-05).

NEXT bounded diagnostic response-body-model-metadata-20261005: native gateway gemini_info GET1 using exact existing credential/model, no generation/TTS/export/retry. Record status/sanitized error or model identity/limits. Success narrows defect to generation payload; failure requires credential/endpoint diagnosis before any payload changes. No new product launch. Source replay/offline schema/native request contract check next. project_ready=false.

## 2026-10-05T19:18:18.587358+00:00 — FRESH PL15 LAUNCHED EXACTLY ONCE

7ef29657-1b98-4236-bcf6-01a7482c8f29 normal topic/language/seconds endpoint session200/POST202 created=true/preparing; canonical DB input matches. Product_posts1. Correct active preflight excludes deletedAt tombstones. Launch receipt response-body-product-launch-continuation.json. No custom narration/assets/rescue. Current gateway9891e8d9 body contract deployed and live billing PASS; runtime2a6d997 unchanged.

NEXT follow this exact preparation_calls/stage_runs to terminal using bounded reads, preserve failed/unknown job immutable, inspect saved provider evidence offline before any new job. Do not redeploy/restart while work active. If final MP4 produced, actual frame/audio/decode/identity evidence plus explicit HUMAN review remain required. Project_ready=false; product acceptance unproven.

## 2026-10-05T19:17:27.618529+00:00 — PRODUCT PREFLIGHT FALSE ACTIVE DETECTED; NO POST YET

Initial launch preflight stopped before session/product POST (both0). New ID7ef29657-1b98-4236-bcf6-01a7482c8f29 absent; preparing0/stages0. Execution12135 has status running but deletedAt2026-10-05T18:13:05.596Z. Installed native ExecutionPersistence soft deletion marks deletedAt without updating status (buffer timestamp may be backdated). It is logically deleted, not active. Operator query was incorrect. Correct active-execution condition: status='running' AND "deletedAt" IS NULL. No execution row/status is changed manually.

NEXT continuation receipt response-body-product-launch-continuation.json: same still-absent planned ID (never submitted), corrected read-only preflight, owner session1/product POST1, capture response/DB canonical request (topic/language/seconds). Retain initial preflight receipt immutable. No billing rerun needed; live boundary already PASS. Runtime/Gateway unchanged; project_ready=false.

## 2026-10-05T19:13:31.503068+00:00 — RESPONSE CONTRACT DEPLOYED; BILLING ROUNDTRIP PASS

Scoped single gateway import/publish/restart PASS, active9891e8d9-bc62-4d97-8150-9242a22ab4e1 source SHAe323c356dbddaf7002bf7e15e23760deed8d8d295233506bbdb81e2839cf339f active/history exact, all33 protected rows unchanged. Public app health/root200. Fresh single billing execution12135 transport200/receipt200 exact gen-lang-client-0532024148 billingEnabled=false. No generation/TTS/new job yet. Receipts response-body-rollout.json/response-body-billing.json.

NEXT ONE normal input launch: fresh7ef29657-1b98-4236-bcf6-01a7482c8f29 PL15 topic Dlaczego pszczoły odwiedzają kwiaty?. Budget plan response-body-product-plan.json retains server-owned limits; generation max18, searches max15/provider, downloads15, source_fetch6, research_search1, metadata1; exact quota consumption unknown until calls, one final TTS only under enforced existing free ceilings. Assert ID absent and no preparing/running job or execution; owner session1 then product POST1. Persist started receipt before POST. No custom script/assets/manual rescue/retries. Stop failed/unknown terminal, inspect saved evidence offline. Prior failed job immutable; project_ready=false until actual acceptance matrix/media/human review.

## 2026-10-05T19:11:33.197777+00:00 — NATIVE RESPONSE IMPORT GATE PASS; SCOPED ROLLOUT

Exact d3c4f66 gateway SHAe323c356dbddaf7002bf7e15e23760deed8d8d295233506bbdb81e2839cf339f. Native output/parser +78/78 Python +guards PASS; isolated actual n8n import/export nodes/connections/settings parity PASS. Prior rollout receipt verified passed with activeVersion f3fb1604-7cb4-48b4-8596-93b1741e7816; do not repeat it.

BOUND response-body-rollout-20261005: assert all33 original protected workflow rows unchanged and executions/preparing/stages zero; save current gateway privately; import ONLY corrected gateway once, publish once, restart ONLY ai-short-form-n8n once. Verify source/active history parity and health. No image/schema/credential/Caddy/service mutations; no provider/product requests. Stop any unknown effect and inspect before continuation. Then separate fresh single billing roundtrip; only after exact project/billingEnabled=false plan fresh normal product input. project_ready=false.

## 2026-10-05T19:10:09.874007+00:00 — CHAT RECOVERED; NATIVE RESPONSE BODY CONTRACT FIXED OFFLINE

Resumed clean factory-v3 HEAD8b5c806. Read actual immutable native-json-billing receipt on VPS: execution12131 transport200/receipt200 but projectId/billingEnabled absent. Installed native HTTPRequest4.5 text/fullResponse branch writes response body to outputPropertyName (default data); gateway incorrectly expected body. All six upstream nodes now explicitly outputPropertyName=body. Receipt rejects missing/null/scalar/malformed successful bodies with502 instead of reporting false200. No provider calls or production mutation in this continuation.

78/78 Python PASS, gateway guards PASS. Exact running n8n image sha256:307d6065be25619aa24cfc63a7c2f04ca56d084a08c05c8e9f189a89f353b1ec network-disabled native parser/output-branch harness PASS: old default reproduces missing body, six configured nodes preserve response through receipt. This executes installed output branch with controlled response, not entire authenticated HTTP execution. Evidence native-response-contract.json/native-response-python.txt. Code NOT DEPLOYED; no new MP4; project_ready=false.

NEXT isolated actual n8n import/export parity for corrected workflow; then preserve/check gateway and all33 protected workflows, active executions/preparations/stages before scoped single gateway import/publish/restart. Do not rerun earlier mutation or failed job. Fresh bounded billing diagnostic only after exact deployed active/history parity; fresh normal-input job only after billingEnabled=false. Prior authorization remains; no new approval needed for this scoped correction.

## 2026-10-05T18:34:19.732538+00:00 — CORRECTED GATEWAY IMPORT/PARSER GATES PASS; EMPTY RUNTIME BEFORE ROLLOUT

Exact committeda6c17d0 gateway SHA381c1bff19cd53366004b5f29e4c31955fa051c29809ca66ae6348e7d737d18c: isolated actual n8n2.37.10 import/export parity PASS; actual native parser checks PASS. Checkout .tmp/v3-gateway-a6c17d054243. Source Python/image/SQL unchanged, prior78/78 packaged and realPG gates retained. Pre-rollout active executions EMPTY, V3 preparing0/running stages0; execution12130 no longer running. All33 original workflow rows unchanged; private old gateway backup at .tmp/v3-predeployment-20261005T173043Z/gateway-before-native-json.json.

BOUND v3-native-json-rollout-20261005: started receipt; import ONLY corrected gateway1, publish1, restart ONLY publisher ai-short-form-n8n1, exact active/history/source and original33 parity, public health200. No service/image/Caddy/schema/credential mutation. Then NEW v3-native-json-billing-20261005 diagnostic: one internal gateway POST using existing broker token and google_metadata billing operation on gen-lang-client-0532024148. Timeout30s, no retry; no exports/account mutations/generation/TTS. Store status/body shape/gateway execution ID and require HTTP200, JSON status200, exact projectId, billingEnabled=false. Preserve initial unknown job immutable. Only then fresh productID and ONE normal input launch. project_ready=false.

## 2026-10-05T18:31:36.141609+00:00 — FIRST PRODUCT UNKNOWN; NATIVE JSON CONTRACT DEFECT FIXED OFFLINE

Immutable9f751c54-47f5-443b-a2fd-9d72b59aee53 stopped on metadata gemini-billing-check: preparation unknown / JSONDecodeError, response null, no research/model/TTS/job stage. Native gateway execution12130 was still running when inspected; logs explicitly The value in the JSON Query Parameters field is not valid JSON. Exact deployed n8n2.37.10 HTTPRequest4.5 parseJsonParameter source unconditionally JSON.parse(jsonString): object expressions fail. Prior import parity and object-shape tests did NOT exercise this native parser boundary.

Systemic source correction serializes jsonQuery/jsonHeaders/jsonBody/RespondToWebhook responseBody via JSON.stringify and explicitly selects body contentType=json. No runtime Python/image/SQL/worker changes. Static regression failed before correction;78/78 Python and guards PASS. New gateway_native_json.js executes exact actual n8n parser module in network-disabled2.37.10 image: all3 old object cases reject and6 generated JSON fields plus response serialization preserve Unicode/nested values. Provider calls0. Receipt native-json-parser.json.

NEXT gated rollout: isolated n8n2.37.10 import/export for corrected committed gateway, then exact single-workflow import/publish/restart with prior gateway private backup, all33 originals preserved. First inspect12130 and reject deploying while any OTHER execution or preparing V3 request exists; terminal unknown product never rerun/rescued. Bounded read-only native gateway billing diagnostic1 after rollout, no generation/TTS; retain exact structured response. Only after real gateway200/billingEnabled=false persist fresh product UUID/input and launch ONCE. No MP4/human acceptance; project_ready=false.

## 2026-10-05T18:24:58.443440+00:00 — FIRST V3 PRODUCT JOB LAUNCHED EXACTLY ONCE

Fresh9f751c54-47f5-443b-a2fd-9d72b59aee53 input Dlaczego pszczoły odwiedzają kwiaty?, pl15 submitted through normal owner product endpoint at2026-10-05T18:24:06Z. Session200, requests202 created=true/preparing. DB identity/input and runtime2a6d997 match. Receipt product-pl15-launch-continuation.json. First operational preflight had guessed a nonexistent preparation_runs.state; no session/POST/job occurred in that attempt (product-pl15-launch.json). Corrected read-only preflight showed ID absent, preparing0/running stages0 and n8n active0 before the ONE launch. No job rerun or manual media/script changes.

NEXT inspect this exact job preparation_calls/stage_runs to terminal, preserve actual full relevant responses for offline systemic reproduction if failed. Do not submit another job while active, change its script/assets, restart/redeploy while running or retry immutable failed/unknown attempts. If final MP4 exists, inspect actual bytes/frames/audio evidence and require explicit human acceptance. Current machine/media/human outcome remains unproven; project_ready=false. Live deployment/gateway preserved; all33 prior workflows were unchanged at deployment verification.

## 2026-10-05T18:21:14.042517+00:00 — V3 LIVE DEPLOYMENT VERIFIED; FIRST AUTONOMOUS INPUT PLANNED

Gateway active c26e5d8f-0616-4c85-9995-978fdbcb1ba2, exact source5552d477 active/history parity. V3 service factory-v3-app healthy, image c509487e exact runtime2a6d997. Publisher-only /factory-v3 route live. Public health/UI/assets and original publisher root/JS HTTP200; all33 previous workflow rows unchanged; worker/Postgres/SearXNG healthy. Publish/restart/service start/Caddy reload each executed once. Initial default-urllib health probe HTTPError preserved in activation.json; exact product User-Agent verification passes without any repeated deployment mutation. Receipt deployment-verified.json.

FIRST NEW CASE PL15 UUID 9f751c54-47f5-443b-a2fd-9d72b59aee53, topic Dlaczego pszczoły odwiedzają kwiaty?, language pl, seconds15. Saved exact request and server budgets in product-pl15-plan.json; NOT LAUNCHED. NEXT verify HEAD/remote includes this ID, DB ID absent and no active V3/legacy executions; create owner session1 using private token then POST normal /factory-v3/api/requests ONCE. Endpoint automatically runs producer/executor, no private plans/assets/scripts supplied. Started immutable launch receipt before POST, capture response and DB identity. Failed/unknown ID never rerun, no manual asset/script rescue. Follow actual calls to terminal, inspect exact MP4 frames/audio if produced; human acceptance remains explicit. Later EN30/RU45/UK60 sequential cases only after resolving systemic findings. project_ready=false.

## 2026-10-05T17:42:29.590852+00:00 — V3 PROVISIONED AND VERIFIED; ACTIVATE/SERVICE/ROUTE NEXT

Corrected provisioning PASS: dedicated verified Gemini + broker credential in exact existing project, original Gemini unchanged, settings0600, all7 V3 tables created atomically, jobs/requests0. Gateway imported once inactive with exact source5552d477 nodes/connections/settings parity. All33 original workflow rows unchanged. Secret temps removed. Receipt provisioning-continuation.json. Live Caddy/compose/candidate image preflight PASS; service not running and route unchanged.

BOUND v3-activate-service-20261005: started immutable receipt before actions. Assert current gateway parity/inactive, all33 originals unchanged and active executions0. Publish ONLY VIDEO-V3-Credential-Gateway once; verify active version/history equals source. Restart ONLY ai-short-form-n8n once for native webhook registration, verify actual running/version and protected rows/public health. Start ONLY factory-v3 app using exact5552d477 deployment checkout compose and preverified2a6d997 image, --wait bounded60s. Verify internal service health before route. Assert /opt/n8n/Caddyfile original SHA equals backup; insert only prevalidated /factory-v3 route (candidate SHA f5c5f0b1074d244ceaa9cf05e0fb4fe4df3d825ab665f47ca2869ac2ab6a9436), reload ONLY n8n-caddy-1 config once; verify public /factory-v3/health/UI and existing publisher root/JS, original workflow fingerprints, worker and supporting health. No generation/TTS/job in this stage. Stop first unknown/failure, retain exact partial effects; never rerun completed started actions. Rollback file under .tmp/v3-predeployment-20261005T173043Z remains private.

NEXT after verified live deployment checkpoint: persist fresh product job ID/input/budgets before one launch through normal owner request endpoint; actual media QA and human acceptance still required. project_ready=false.

## 2026-10-05T17:39:26.928710+00:00 — PARTIAL PROVISIONING INSPECTED; FILE PERMISSION DEFECT REPRODUCED

Original provisioning receipt immutable: settings0600 written; credential import failed; both target credentials absent, V3 workflow absent; schema application never started. Private secret temps removed. CLI raw error was not retained, so EACCES is an evidence-backed diagnosis, not a quoted original error: controlled actual-container test proves root-owned0600 staged files are unreadable by node, node-owned0600 files readable. Docker cp preserved root ownership. Fix staging with explicit container owner node:node, retain0600, capture command receipt privately and sanitize errors. Caddy candidate/compose/image preflight PASS (live-deployment-preflight.json); no active route/service.

NEW BOUND v3-provision-continuation-20261005: assert target credentials/workflow/schema still absent, reuse existing private settings and tokens. Original Gemini export1, exact full SHA check, corrected node-owned0600 import file, credential import1 for two IDs in exact owner project. Isolated export1 for verification, confirm original encrypted row unchanged. Apply four V3 SQL files in one transaction, inactive gateway import1 with node-readable source file; verify parity and all33 original workflows. Started immutable receipt before actions; preserve original failure, no job/provider calls. NEXT publish/service/route only after checkpoint.

## 2026-10-05T17:34:57.404611+00:00 — GATEWAY IMPORT GATE PASS; EXACT V3 PROVISIONING PLAN

Isolated n8n2.37.10 import/export source5552d477 parity PASS; workflow SHA30056814b648a2286185dd930fd76a242913e03a1d758f6cfff06aa5210f6141. Python78/78/native guards PASS. Detached deployment checkout /opt/ai-short-form-content-factory/.tmp/v3-deploy-5552d477c4b5; packaged runtime remains exact2a6d997.

BOUND v3-provision-20261005: assert neither V3 credential ID/workflow nor V3 schema/settings exists. Started immutable receipt before mutation. Export ONLY original Gemini credential once to generated0700 temp; assert exact verified full key SHA; create a dedicated copy V3GeminiFreeTier20261005 and separate generated header credential V3ProviderGatewayToken in owner project FF7o9vSL9orH8B5T via one credential import. Original credential untouched. Independently generated broker/owner tokens and existing shorts_factory DSN stay only private0600 settings. Apply ledger.sql, preparation.sql, provider_cache.sql, review.sql in ONE transaction; existing quota functions/limits untouched. Import ONLY VIDEO-V3-Credential-Gateway once inactive, read back nodes/connections/settings and all33 protected fingerprints; no publish/restart/service/route/job in this stage. Stop on unknown/failure; inspect actual effects before any continuation. Exact backups at .tmp/v3-predeployment-20261005T173043Z; no broad deletion/restore. Verify secret cleanup and IDs/sharing/schema/settings mode.

NEXT after verified provisioning checkpoint: publish ONLY V3 gateway once, controlled publisher n8n restart only if CLI requires registration, verify active/history/source/health and all33 originals; start single scoped V3 service, validate publisher-only route against backup and reload Caddy once, then fresh sequential product acceptance. No MP4/HUMAN PASS; project_ready=false.

## 2026-10-05T17:32:55.132080+00:00 — ISOLATED GEMINI SOURCE VERIFIED; PRODUCTION BASELINE SAVED

Gateway now references dedicated V3GeminiFreeTier20261005 for generation and model metadata. Regression failed before and passes after; full78/78 and native guards PASS. Only workflow/generator/test changed; packaged Python runtime remains verified2a6d997. Actual publisher n8n2.37.10 contains33 workflows and11 credentials (older31/9 counts are stale), active executions0. All33 row fingerprints and private originals saved in /opt/ai-short-form-content-factory/.tmp/v3-predeployment-20261005T173043Z. Caddy backup SHA and actual TTS quota saved; V3 schema absent. Initial read used an incorrect view name, failed without mutation; corrected provider_budget_status confirms869933 Chirp and3600000 WaveNet characters remaining. No quota limits changed.

NEXT gate: fresh detached deployment checkout of this source, isolated n8n2.37.10 import/export parity and Code syntax for changed gateway, compose config and image revision. Then provision only dedicated Gemini copy and V3ProviderGatewayToken in existing owner project FF7o9vSL9orH8B5T, private settings (broker/owner independently generated), four V3 SQL files in shorts_factory, one new gateway import/publish. Confirm all33 originals unchanged. Do not launch job until service/route/health verified. Every mutation will have started receipt and exact post-state; no repeated imports/enable on unknown state.

## 2026-10-05T17:28:02.481204+00:00 — LIVE BILLING METADATA PASS; FREE-TIER BLOCKER CLOSED

Both authorized metadata APIs enabled. New bounded diagnostic v3-enabled-project-billing-20261005 succeeded: OAuth refresh200, billingInfo200, exact gen-lang-client-0532024148, billingEnabled=false. Receipt enabled-project-billing.json; private0600 /var/lib/factory-v3/gemini-free-tier-proof.json written using previously fully verified production key SHA. Secret temporaries removed; no generation/TTS or billing mutation. Prior403 failures remain preserved.

NEXT deployment-preparation stage: read actual ai-short-form-n8n version/config and workflow/credential identity metadata, exact supporting Postgres/media networks, existing quota schema and publisher Caddy routing. Capture protected workflow fingerprints and scoped rollback backup before any deployment mutations. Prepare isolated Gemini reference V3GeminiFreeTier20261005 and regression/source parity, run existing gateway gates; commit/push before credential provisioning/import. Scope only V3 gateway/tables/settings/service and /factory-v3 publisher route; no other workflow edits/restarts yet. No V3 job/MP4; project_ready=false.

## 2026-10-05T17:26:04.881649+00:00 — BOTH AUTHORIZED METADATA APIS VERIFIED ENABLED

Executed approved browser plan once per service on gen-lang-client-0532024148. Service Usage exact project page explicitly shows Interfejs API został włączony; Cloud Billing exact project metrics page offers Wyłącz interfejs API. Receipt browser-metadata-enable.json. No billing account/IAM/key changes.

NEXT BOUNDED v3-enabled-project-billing-20261005: export ONLY Google OAuth8KbFC6GBZOd18bzG once, refresh1, exact billingInfo GET1 with x-goog-user-project=gen-lang-client-0532024148; no other API, no retry, no generation/TTS. Start immutable receipt before export, persist sanitized failure reason/service/consumer, cleanup exact secret temporaries. Only if exact projectId and billingEnabled=false, write private0600 proof using previously full-key-verified SHA4184d804b53524b29138a4f4adb7145fd32f59d6e985fb37f21909ee2960bba2. Push plan before calls. Earlier failures remain immutable. Candidate runtime not deployed; no new job/MP4; project_ready=false.

## 2026-10-05T17:22:51.323346+00:00 — USER APPROVED EXACT TWO METADATA API ENABLES

Owner explicitly approved Service Usage API and Cloud Billing API on gen-lang-client-0532024148 under the displayed Google Cloud terms. Previous pending approval is superseded. Bounded plan acceptance/factory-v3/browser-metadata-enable-plan.json: inspect initial state, at most one Enable click per service, verify actual post-state; no billing linking/payment/IAM/key/OAuth changes. Candidate image/tests unchanged and verified; not deployed. Next execute this exact browser plan, checkpoint actual results, then new bounded OAuth/billing verification with the trusted quota-project header. No new job/MP4; project_ready=false.

## 2026-10-05T16:36:03.864418+00:00 — CURRENT VERIFIED IMAGE READY; API ENABLE CONFIRMATION STILL PENDING

Project_ready=false. Exact Gemini key/project/Free tier verified in Google AI Studio; Project ID gen-lang-client-0532024148 / number529636078126 is known and FULL SHA256 matched production credential (key-ui-binding.json). Official selected-model pricing reconfirmed2026-10-05: gemini-3.5-flash-lite Standard input/output free in Free Tier, https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite . No need to replace the model or ask owner for Project ID.

Checked quota-project gateway correction committed/pushed2a6d9971be21bd38bfc913ab1804d7bb698a96d9; NOT DEPLOYED. Full78/78 local Python and native gateway guards PASS; isolated n8n2.37.10 import/export exact nodes/connections/settings parity + Code syntax PASS. New image factory-v3:2a6d997 built from EXACT2a6d997, image sha256:c509487e0a156a457ee0bb3ef1ee1372edd47609b3d5bd01fca22ff5066a9c51. Packaged78/78 PASS without external network; CLI source_revision matches2a6d997. Updated deployment compose image tag, config PASS, actual image ID/revision verified, services_started0. Build in isolated source worktree /opt/ai-short-form-content-factory/.tmp/v3-build-aa46f5d2fbb84d2080c7f0acd261c0f2; primary VPS checkout remains9400cb0. Receipts/logs quota-project-image-build.json/txt, quota-project-image-python.txt, quota-project-compose.json; current image manifest/log updated. One native Docker log line had trailing whitespace; normalized only that formatting, with original/normalized SHA256 and retained VPS original recorded in build-log-normalization.json. SQL/executor/service Python unchanged since earlier real-PostgreSQL package verification; that evidence is reused, not a newly repeated PG run.

Billing metadata blockers precisely recorded: known-project-billing.json403 SERVICE_DISABLED; explicit project configuration billing-api-config.json403 SERVICE_DISABLED for serviceusage.googleapis.com on projects/gen-lang-client-0532024148. enable_attempts0, billing_mutations0, all temporary secret directories removed. Do not rerun completed diagnostics. Browser Google Console is at Service Usage API Enable for this exact project. Explicit user confirmation remains PENDING to enable ONLY Service Usage + Cloud Billing metadata APIs under displayed Google Cloud terms. Status question did not approve. No new roles/scopes/key/billing-account changes are authorized by that question. Do not click Enable while pending.

NEXT EXACT: after explicit approval, push a bounded browser activation plan for these TWO API services on this known project; verify initial disabled states, enable each once, read actual post-state, never accept a billing link/payment/IAM expansion. Then push a new bounded billing read (Google OAuth refresh1 + known-project billingInfo GET1 with x-goog-user-project exact project, export1, no retry), retain actual receipt and only create0600 server proof if exact billingEnabled=false. Original403 receipts preserved. Provision isolated V3 credentials/settings/tables/gateway, capture rollback and unrelated31 workflow fingerprints, import/activate gateway once with parity, scoped Caddy/compose deployment and health. Only then push fresh exact job UUID/topic/language/duration/budget and perform actual media acceptance. No V3 production workflow/schema/service/route or fresh job/MP4 exists; HUMAN PASS pending.

## 2026-10-05T16:29:31.926788+00:00 — QUOTA PROJECT GATEWAY FIX VERIFIED; GOOGLE UI ENABLE CONFIRMATION PENDING

Exact production Gemini authorization key/project/Free tier verified by FULL SHA256 in signed-in AI Studio; key-ui-binding.json. Project ID is known; do not ask owner for it again. Direct billing call403 SERVICE_DISABLED; explicit-quota-project configuration diagnostic then403 because Service Usage API itself is disabled in this exact Gemini project. Receipt billing-api-config.json: enable_attempts0, billing_mutations0; temporary secrets removed. Do not repeat either completed diagnostic.

Systemic gateway defect corrected: billing metadata now emits x-goog-user-project from the validated billing project; generated native google_metadata HTTP node forwards ONLY server-generated headers. Caller header override/CRLF, other provider headers, no retries and sanitized errors checked. Regression failed before correction (undefined header) and passes after. Full78/78 Python PASS; isolated actual n8n2.37.10 import/export nodes/connections/settings parity PASS; Code node syntax PASS. Evidence quota-project-python.txt, quota-project-native.json, quota-project-import.json/txt. No changed SQL/executor/owner service Python code; prior isolated PostgreSQL checks remain prior evidence. Source fix NOT DEPLOYED; new image build still required because factory_v3 source changed.

Google Console is open at ONLY https://console.cloud.google.com/apis/library/serviceusage.googleapis.com?project=gen-lang-client-0532024148 with Enable button. Browser automation confirmation pending for enabling Service Usage API and Cloud Billing API ONLY on this project, under existing Google Cloud terms; no billing-account/IAM/OAuth/key change. Asked via explicit UI confirmation tool; no owner response yet. Do not infer approval from elapsed time/status questions or activate while pending. API activation requires new pushed exact browser operation plan after explicit approval; never link billing or buy credits. After verified API enable, new bounded billing read can establish explicit billingEnabled=false using known quota project. Original403 failures retained.

NEXT independent: commit/push this checked gateway fix, build new exact committed image on VPS, run packaged tests/config checks, checkpoint image ID/source. Then await/handle explicit API-enable response, verify known-project billing, isolate credentials, provision only V3 schema/settings/gateway/route/service with rollback/protected fingerprints and exact source parity. No V3 service/schema/workflow/route deployed; no new job/MP4. Project_ready=false.

## 2026-10-05T16:19:56.995173+00:00 — DIRECT BILLING FAILURE CLASSIFIED; NARROW METADATA API CONFIGURATION PLANNED

Exact Gemini key/project/Free tier remains independently verified in Google's UI (key-ui-binding.json). Direct known-project billing diagnostic completed ONCE: refresh200; billingInfo403/PERMISSION_DENIED, reason SERVICE_DISABLED, domain googleapis.com. Both secret temporary directories removed; no billing/account/credential mutation or generation/TTS call. Receipt known-project-billing.json. This failure does NOT contradict Google's displayed Free tier, and does not prove missing IAM rights.

NEXT bounded configuration v3-billing-api-config-20261005: ONLY project gen-lang-client-0532024148 / number529636078126, ONLY cloudbilling.googleapis.com. Export existing Google OAuth8KbFC6GBZOd18bzG once, refresh1; GET serviceusage.googleapis.com/v1/projects/529636078126/services/cloudbilling.googleapis.com1, using x-goog-user-project=gen-lang-client-0532024148. Save exact initial state before mutation. If and only if exact returned service is DISABLED, POST that exact service:enable once (empty body). Maximum operation-status GET1, service post-verification GET1 and billingInfo GET1 with explicit same quota project after ENABLED verification. Total HTTP max6, export1; no sleep/poll loops/retries. Stop first denial/unknown/mismatch, IAM/scope/billing requirement, or pending operation; never grant roles/change scopes/link billing/add funds. If pending, inspect saved operation later without replaying enable. API configuration is the only permitted mutation; no billing account changes. Rollback reference is initial DISABLED service receipt; do not disable unrelated services. New immutable started receipt before operations prevents duplicate mutation after timeout. Cleanup generated secret temporaries. Push plan before operations.

If billing GET explicitly confirms exact project and billingEnabled=false, preserve runtime gate and configure ONLY V3 google_metadata node with explicit quota-project header, regression, generated workflow validation. Then isolated credentials/schema/settings/gateway/service deployment with protected workflow fingerprints and real new media acceptance. No V3 MP4/deployment yet; Project_ready=false.

## 2026-10-05T16:14:51.845414+00:00 — EXACT GEMINI KEY/PROJECT/FREE TIER VERIFIED IN GOOGLE UI

Production credential zsRz2tvE57EKe8zy fingerprint equals the FULL key fingerprint from signed-in Google AI Studio: SHA2564184d804b53524b29138a4f4adb7145fd32f59d6e985fb37f21909ee2960bba2. Exact key details identify projects/529636078126; API Keys table identifies project gen-lang-client-0532024148 and Free tier / Set up billing. Evidence acceptance/factory-v3/key-ui-binding.json and key-fingerprint.json. No key/account/billing changed; one scoped export, temporaries verified removed. Original403 receipt preserved. The earlier conclusion that Project ID must be supplied by owner is superseded by actual existing browser evidence.

NEXT BOUNDED DIAGNOSTIC PLAN v3-known-project-billing-20261005: known project gen-lang-client-0532024148. Export ONLY Google OAuth credential8KbFC6GBZOd18bzG once into generated0700 temporary directories; OAuth refresh POST1, GET https://cloudbilling.googleapis.com/v1/projects/gen-lang-client-0532024148/billingInfo1. No key-owner/project-discovery request, Gemini key export, generation/TTS/provider call, account mutation or retry. Exact question: can existing project OAuth read this known project's billing, which is required by the current per-request runtime gate? Stop on first failure; retain bounded safe Google error reason/domain/status, never raw error message/token. Started immutable receipt before operations; cleanup secret temporaries. Push before calls. If explicit billingEnabled=false and exact projectId match, existing API gate can remain. If denied, use verified UI evidence to redesign credential-bound enforcement without requiring owner to configure unrelated IAM rights; do not invent API proof.

Project_ready=false; V3 not deployed, no new job/MP4. Continue on factory-v3. Next execute this diagnostic once, then preserve exact result and scope deployment accordingly.

## 2026-10-05T16:10:45.227548+00:00 — AI STUDIO FREE TIER OBSERVED; LOCAL KEY BINDING PLANNED

New evidence from existing signed-in Google AI Studio API Keys page: project gen-lang-client-0532024148, three displayed keys (masked suffixes yiPg/cLWU/m2Ag), all marked Free tier with Set up billing. This is live Google UI evidence, not an inferred plan from HTTP200. Exact production credential-to-row binding remains UNVERIFIED. Old403 diagnostic is preserved; no retry of lookupKey planned.

AUTHORIZED BOUNDED LOCAL DIAGNOSTIC: v3-key-fingerprint-20261005. Export exactly credential zsRz2tvE57EKe8zy once from ai-short-form-n8n into generated0700 container/host temporary directories. Retain only credential ID, SHA256 and last4 for comparison with the already observed Google table. Maximum exports1; provider/API/OAuth/generation/TTS calls0; credential imports/updates/deletes0. Delete only generated secret temporaries and verify cleanup. Persist a started receipt BEFORE export, so a timeout/crash never authorizes a repeat. Stop on identity mismatch/missing key/operation failure. No free-tier proof file or deployment until exact binding is independently established. Push this plan before execution.

Next: perform that one local fingerprint read, compare to Google's existing Free tier table, and establish full-key identity without emitting secrets. Then replace mandatory per-job Cloud Billing metadata dependence with an independently verified, isolated credential binding only if that preserves free-only enforcement. Do not merely set confirmed=true or remove safeguards. Project_ready=false; no new job/MP4.

## 2026-10-05T15:51:47.429679+00:00 — CURRENT BRANCH/RUNTIME RECHECK; MACOS TEST PORTABILITY FIX

Project_ready=false. Continue factory-v3, not the obsolete September V5 branch. GitHub and VPS source both verified at 9400cb0ebedcd5774e6ea684f70f48317beb47c9 before this test/docs-only checkpoint. VPS has only untracked .tmp/; preserved. Production publisher n8n remains2.37.10; no downgrade/restart/import/deployment/provider call performed.

Fresh local suite initially77/78 PASS: owner MP4 test compared unresolved macOS /var path against canonical /private/var returned by asset_path. Corrected the test to compare file.resolve(); production identity/security code unchanged, replacement-byte and non-QA rejection assertions retained. Full78/78 PASS; log acceptance/factory-v3/macos-python.txt. No packaged service code changed, so existing d6f0a04 image evidence remains the earlier isolated package check, not a new build/deployment.

Live read-only VPS recheck confirms immutable diagnostic v3-account-boundary-20261005 remains blocked/key_owner_rejected, free_tier_confirmed=false, generation/TTS calls0; /var/lib/factory-v3/gemini-free-tier-proof.json absent. No V3 service container or new MP4. Do not rerun that diagnostic or invent proof.

NEXT EXACT STEP: resolve project-scoped Google access or obtain owner-confirmed exact Gemini key/project identity with independent billing verification. After access changes, push a new bounded diagnostic plan/ID before calls. Then follow docs/FACTORY_V3_RELEASE_READINESS.md for scoped deployment and fresh actual-media acceptance. No new job was created in this checkpoint; latest diagnostic and historical failed jobs remain immutable.

## 2026-10-04 — M5v226 / M8v87 + SQL DEPLOYED; 9bf5e97c-0059-48a8-8e5d-7da1b1feb923 CREATED ONLY

- New production regression `9bf5e97c-0059-48a8-8e5d-7da1b1feb923` created EXACTLY ONCE HTTP201 at 2026-10-04T17:43:55.960941+00:00: jak działa zszywacz biurowy, pl30/Gemini. DBcreated confirmed. NOT LAUNCHED. Persist/push this ID before its single launch. Latest failed b76675c8 and every prior failure remain immutable.
- Code60589e9 deployed: M5v226 active/version eb1c9f83-1e46-4ad4-8769-58430df6b491; M8v87 active/version264666d5-5c3d-4864-926e-22f28f7d9abf. Live nodes/connections/settings and active-history nodes/connections exactly equal Git. get_gemini_visual_candidate_sets body SHA315ca8da0556f51f4e211ab9e3e958026b90d6d3ed0124d646f5f11de992e4b0 exactly verified. Other31 workflows unchanged; worker unchanged/healthy; direct/public health200; active0.
- Exact operations: one actual import of two allowlisted workflows, one function replacement, one publication per workflow, one n8n restart. Initial marker-write preparation failed BEFORE n8n import; separate actual-state read confirmed zero effects before the first actual import. No blind repeated production side effect. Backups .backups/release-60589e9/ with tracked hashes.
- Evidence/receipts/logs: acceptance/release-coverage/deployment-verified.json, deployment-operations.json, protected-workflow-fingerprints.json, production-create.json, first-production-budget.json. Native integrated9 unique selection, Node886/886, SQL8/8 and separate5/5 remain the verified release checks; no source code changed since them. Earlier NOT DEPLOYED notes below are historical.
- NEXT: verify this exact ID in HEAD/origin + DBcreated and active0, launch this ID EXACTLY ONCE, checkpoint its receipt, follow M4-M9 to terminal. On failure: preserve job, inspect ALL observed blockers and close offline without another blind job. On machine pass: inspect actual MP4/frames/audio identity and avoid unsupported HUMAN/listening claims. Then complete representative PL15/EN30/RU45/UK60 sequentially under DELIVERY_STRATEGY.md. This30s regression is not the whole project and does not replace the acceptance matrix.
- Continue autonomously after status questions: answer briefly and resume authorized work. Do not stop at a progress report while engineering/acceptance work remains. No completion date promised; product readiness NOT YET PROVEN.

## 2026-10-04 19:21 Warsaw — RELEASE COVERAGE AND INTEGRATED VISUAL CHECKS PASS; NOT DEPLOYED

- New method implemented: executable scripts/inventory_release_coverage.py with JSON/Markdown report in acceptance/release-coverage/. Initial inventory:40 tracked fixtures,80 Node-suite files,8 SQL runners,5 separate runners; new integrated fixture/regression extends this corpus. Static references and explicit metadata are coverage clues, not production pass. The generator verifies evidence hashes and reports unresolved boundaries.
- Full Node886/886 PASS; SQL8/8 prior results remain valid because SQL/workflow sources are unchanged; all5 separate runners PASS on recorded image IDs. Real FFmpeg duration test needs76s: initial45s harness timeout and verified bounded retry are both recorded. No production service restart.
- All three S4 new actual previews manually inspected. One native S4 Gemini call rejects empty/disassembled tools and accepts visible loaded staple strip95. One native S8 call was needed because its third ranked candidate changed; wide first candidate is now rejected, two close-up tool photos pass. Exactly TWO new provider calls, no retries/fresh production jobs, temporary exported keys deleted.
- Systemic diagnostic defect found: old preview replay refreshed a fixed list of scenes and paired S8 current candidate metadata with old preview bytes. It is an OFFLINE HARNESS defect, not a proven production workflow defect. Reuse now requires matching ordered provider/asset/type/preview/download sources; actual S8 change and generic URL/order changes have regressions in tests/release-m8-integrated.test.cjs.
- Current native parser/collector replay PASS:9 unique selected assets, every original must-show concept/intent/exclusion gate passes. Two fresh S4/S8 responses + seven saved responses have matching current ranked source identities and original contracts. This is NOT a fresh nine-call run and NOT production acceptance. Capture:tests/fixtures/release-m8-12108-integrated.json; executable:scripts/replay_m8_release.cjs; reports/hashes:acceptance/release-coverage/release-checkpoint.json and integrated-visual-replay.json.
- Last live versions remain M5v225/ab663ac4-c283-4d2f-b0e6-e2c7d0770a64 and M8v86/54776132-c5a5-40e9-acb1-3e9498e273e5; no import/publish/restart/create/run initiated. Immutable failed b76675c8 stays untouched. Earlier source corrections are committed, NOT DEPLOYED. Worker unchanged.
- Next: review remaining stage-boundary limits in coverage.md; verify actual live versions/active0/other31 workflows and production backups, then deploy only M5/M8 + get_gemini_visual_candidate_sets once after confirming all observed blockers closed. Exact active/history/source/SQL and health verification precedes any fresh job. Follow DELIVERY_STRATEGY.md representative release acceptance and actual media checks; one clip does not establish product completion. No architecture redesign or rerun of failed jobs.
- No completion date or HUMAN/audio-listening PASS claimed. Keep logs, provenance, meaningful checkpoints pushed to GitHub. Do not repeat the two model calls or completed tests without new evidence/change.

## 2026-10-04 18:35 Warsaw — USER REQUESTED METHOD CHANGE; PROJECT NOT READY

Authoritative working method: [DELIVERY_STRATEGY.md](DELIVERY_STRATEGY.md); root AGENTS.md tells subsequent chats to load it. This supersedes old immediate-smoke directions below. User wants the complete usable factory, not one demonstration video. No new production run or provider call was made for this checkpoint.

| Area | Verified state | Remaining work |
|---|---|---|
| Current corrections | Generic M5 authored-pair preservation; M8 retrieval/identity/co-presence/loaded-container fixes; SQL nomination priority | Code checkpoint only; NOT DEPLOYED |
| Offline regressions | Node883/883, SQL8/8; tracked original/current provider pools and negative controls | Inventory diverse corpus and stage-boundary coverage; prove integrated release gates |
| Latest production | b76675c8 immutable: M4-M7 PASS, M8 FAIL, M9 not started | Do not rerun; complete systematic closure before new acceptance |
| Current unresolved boundary | Closed S4 stapler cannot prove loaded staples; final original query dropped container owner. Generic open-owner fallback yields three actual photo previews | Inspect all three S4 pixels; native strict acceptance for new candidate set is UNKNOWN |
| Visual integration | S6/S7/S9 corrections tested; paperclips and closed-container false positives captured as negatives | Final strict nine-scene globally unique assignment has NOT passed after latest S4 change |
| Production | Last verified M5v225/ab663ac4-c283-4d2f-b0e6-e2c7d0770a64, M8v86/54776132-c5a5-40e9-acb1-3e9498e273e5; worker unchanged | Re-read actual state before deployment; deploy only M5/M8 + get_gemini_visual_candidate_sets after closure |
| Product acceptance | Whole-project readiness NOT PROVEN; no final media for latest failed job | Representative multilingual/duration acceptance, actual MP4 checks and honest human/audio status; release/tag only after evidence |

Portable evidence: acceptance/2026-10-04-project-checkpoint/evidence.json and test logs; tests/fixtures/m8-12108-fastening-contract.json; tests/m5-m8-12108-fastening-contract.test.cjs; tests/m8-12108-semantic-nomination-ranking.py. Fixture contains original pools, baseline/current ranking, provider query probes, actual paperclip and closed-container negative responses. Passed tests do not prove current provider or production acceptance.

Server diagnostic data remains at .review/m8-12108/: current-replay/previews.json + S*-request.json, probe/loaded-owner-result.json, normalize-all.cjs, rank-all.py, current-replay/gemini-all.cjs and original decoded execution.json. These ignored paths are supplementary; do not assume GitHub contains them. If unavailable, reproduce from tracked fixture and actual workflow code, not from memory. Latest successful preparation job job_6d0085f7db4f produced three S4 Commons candidates164586506/25823633/8141365; IDs are diagnostic evidence, never production mappings. Full Node result job_17b4c6f56aa2; eight SQL result job_ade6cb0f2ec8.

Resume:
1. Read new strategy; verify Git/live/active jobs before mutation. Do NOT restart architecture analysis or duplicate completed test runs without a new change/failure.
2. Implement an executable inventory/report of existing multilingual/topic fixture coverage and uncovered stage-boundary interactions. Use saved traces/media; no new production smoke to discover gaps. This is the next engineering deliverable.
3. Close the explicit S4 pixel/provider uncertainty with a recorded bounded call budget only where live evidence is essential; then one integrated strict9/uniqueness release check. Keep strict anchors, min55, three queries/previews, identity, timing and exact audio gates.
4. Commit/push subsequent meaningful changes; deploy exact changed components once ONLY after offline/integrated closure, verify active/history code, other31 workflows and health.
5. Follow the release matrix in DELIVERY_STRATEGY.md; persist/push each fresh job ID before its single launch. No failed-job reruns. Do not equate one passed movie with a ready project.

No import/publish/restart/create/run is pending from this checkpoint. Preserve existing untracked .tmp/. No promised completion date or claimed measured ChatGPT-credit saving.

## 2026-10-04 — b76675c8 / M8 12108 generic offline correction checkpoint; NOT DEPLOYED
- Failed `b76675c8-be07-44c0-9b27-22b350d86ef8` is IMMUTABLE: M4-M7 passed, M8 failed, M9 never started. Never relaunch it or any prior failure.
- Full trace inspection found S6 sparse two-object retrieval, S7 paperclips incorrectly approved as staples, and S9 M5 dropping an independently authored paper-document anchor and its office fastening relationship. M5 now preserves only independently authored/query-grounded fastening pairs in all four validators, without narration/timing changes.
- Generic M8 correction: final physical-pair query compaction; separate final surface-pair/result-state retrieval; direct completed-state Commons category nomination and physical-object document-photo classification, retaining diagram/SVG/packaging rejection; explicit fastener identity and direct contact evidence in Gemini. No topic/asset-ID mapping, inferred hidden objects or lowered thresholds.
- SQL semantic-review priority now ranks directly depicted physical/component nominees before cross-shot novelty; trusted ranking stays unchanged and the existing global collector still requires nine distinct approved selections. Three queries, three previews and relevance55 remain unchanged.
- Actual negative replay rejects production paperclip6077915; measurement illustration is rejected. Heftklammern is valid for the two-object S6 view but failed the stronger S7 bound-document intent: do not force that pass. A real API orientation comparison showed portrait-only Pexels excludes physical fastening photos. The last connector-first physical-result fallback now uses its authored concrete surface and landscape photos; first two queries and video orientation are unchanged. Actual retrieved photo6991328 was manually inspected: three staples visibly pierce paper. Current nine-scene strict Gemini/global-uniqueness replay is IN PROGRESS, not accepted production.
- Prior full878/878 and eight SQL regressions passed. Final orientation controls, current nine-scene replay and final full suite still required before commit/push/deployment.
- Live remains M5v225 `ab663ac4-c283-4d2f-b0e6-e2c7d0770a64`, M8v86 `54776132-c5a5-40e9-acb1-3e9498e273e5`; worker unchanged. Only M5/M8 and `get_gemini_visual_candidate_sets` SQL function need deployment after every offline blocker closes. No import/publish/restart/create/run pending.
- Evidence: `.review/m8-12108/`, tests `m5-m8-12108-fastening-contract.test.cjs` / `m8-12108-semantic-nomination-ranking.py`, saved full provider pools and baseline/current native SQL/Gemini fixtures. Final media does not exist.
- Next: close ALL observed blockers offline and final regressions; commit/push; deploy only exact changed components ONCE, verify active/history code, other31 workflows, worker/public health and active0; create ONE fresh pl30/Gemini ID, persist/push it in all three docs, verify HEAD/origin ID and DB-created/active0, launch ONCE, follow M4-M9 to terminal and inspect actual final frames/audio evidence.

## 2026-10-04 — b76675c8 IMMUTABLE M8 12108 failure; new production acceptance failed
- Acceptance `b76675c8-be07-44c0-9b27-22b350d86ef8` launched EXACTLY ONCE HTTP202 accepted=true at 2026-10-04T10:09:00Z after prelaunch HEAD/origin85bf4f4 matched, ID persisted, DB created, active0. Receipt `.review/m8-12093/new-acceptance-launch.json`.
- Terminal visuals_failed: M4-M7 PASS; M8 run `a9d02b45-3024-4fd2-995d-fc00d325e904` failed execution12108 (10:10:50–10:15:29Z), no Gemini-approved unique visual candidate for S6-A; M9 never started. NEVER relaunch this failed ID. Inspect ALL9 reviews and full pools before changes; no new smoke before every observed blocker closes offline and full checks/deploy verification.
- Prior correction7edb2d8 and actual46912c2a offline S6/S7 replay passed865/865+7SQL regressions, but this new production result disproves production acceptance. ActiveM8v86/54776132-c5a5-40e9-acb1-3e9498e273e5, M5v225 unchanged. No further import/publish/restart/create/run pending.
- Full new execution extraction in progress at `.review/m8-12108/execution.json`. Final media does not exist. Preserve strict anchors/photographs/Gemini gates, relevance55,3queries/3previews, uniqueness and timing.

## 2026-10-04 — M8 v86 deployed; b76675c8 CREATED ONLY
- New acceptance `b76675c8-be07-44c0-9b27-22b350d86ef8` created EXACTLY ONCE HTTP201 at 2026-10-04T10:07:42Z: topic jak działa zszywacz biurowy, pl30/Gemini. NOT LAUNCHED. Receipt `.review/m8-12093/new-acceptance-create.json`.
- Correction `7edb2d88b982a30a739ce4865e1f58989c9c44af` pushed; full865/865 and seven M8 SQL regressions PASS; actual strict native Gemini replay closes BOTH S6/S7 blockers, illustration negative rejected; all9 unique scene assignment OFFLINE PASS.
- M8 v86 active/version `54776132-c5a5-40e9-acb1-3e9498e273e5`: live nodes/connections/settings and active history exactly match Git. Import/publish/n8n restart ONCE each. Other32 workflows unchanged, M5v225 unchanged, worker healthy, restart counts0, direct-container/public health200, active0. Evidence `.review/m8-12093/deployment-verified.json`, backup SHA5b49176c8e6041a17e6d9ac9b897b8d0c2cf0b2fa4e25698f40d0f4c5a5dddfb.
- Push this ID checkpoint, verify HEAD/origin ID and DB created plus active0, then launch this ID EXACTLY ONCE. Follow M4-M9 to terminal and inspect actual final frames/media. Never relaunch46912c2a or any earlier failure. Production acceptance remains unproven; no HUMAN/audio-listening PASS on the unsupported audio model surface.

## 2026-10-04 — M8 12093 blockers closed OFFLINE; deploy only M8 next
- Failed acceptance `46912c2a-5d75-4482-a1bd-6d4016645f28` remains immutable visuals_failed; NEVER relaunch. M4-M7 passed; M9 never started. Both observed M8 blockers S6/S7 are now reproduced and closed offline, not yet production accepted.
- Generic Wikimedia query fallback uses a plural already authored elsewhere in the same storyboard only for a qualified physical owner/consumable pair. Purpose-only captions and compound object types cannot prove independent paired objects; direct exposed owners and one paired category plus a state caption can nominate metadata-rejected review candidates. Native bounded owner scoring preserves rejection and min55. No topic or asset-ID production mapping.
- Wikimedia previews strip tracking query/fragment and use actual original dimensions when the API returns an unscaled original. All six replay previews fetched HTTP200 through the production worker; all three original failed URLs independently fetched HTTP200 query-free.
- Unchanged production SQL replay, temporary tables and ROLLBACK: S6 slots Commons8141312/Pixabay487701/Pexels29157286; S7 slots Commons75797646/Commons12612756/Pexels8478388. Three slots, relevance>=55, cross-scene uniqueness and trusted metadata priority retained.
- Actual native Gemini3.5flash-lite replay accepted photograph8141312 for S6 (100) and photograph12612756 for S7 (90), with every required concept visible and exclusions clear. Annotated drawing75797646 has both depicted concepts but intent_match=false (20), correctly failing the photographic requirement. All nine actual scene reviews produce a strict unique assignment offline.
- Full865/865 Node tests and all seven M8 SQL ranking regressions PASS. Only three workflow code nodes changed; topology/settings, parser, collector, SQL, worker, all shot anchors and timing gates unchanged. Fixture retains actual provider responses and image fingerprints. Old snapshot expectations updated only for corrected transport URLs/dimensions.
- Before deployment: M8 v85 active/version4ddd4f4c-fc25-420a-aa43-8aa33b885640; M5 v225 unchanged; other32 baseline saved; n8n active0. Commit/push, backup and deploy ONLY M8 once, verify exact active source/history/health/other32, then create ONE fresh pl30/Gemini smoke and persist/push its ID before its single launch. Inspect actual final frames/audio after M9; audio input remains unsupported on this model surface, so never claim listening/HUMAN PASS.

## 2026-10-04 — 46912c2a IMMUT
…[sentinelx: truncated 273211 bytes]…
-2d421b3c3142`, M8 v53 `0953f69f-e982-467e-95e0-35161a613771`.
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


## 2026-09-27 — bounded voiceover and exact render contract (offline checkpoint)

- Starting Git state for this pass: main at 43ca6b3, with only pre-existing .tmp/ untracked; the three handoff changes had already been committed as 8f17a0f.
- The 8f17a0f candidate path padded short MP3s with silence. This pass removes padding. An accepted M5 candidate is the exact MP3 promoted by M6; no voice speed changes.
- Audio acceptance is one-sided: no longer than target and no shorter than observed production bounds 14208/28464/42864/58176 ms for 15/30/45/60 s. Production DB evidence changed the 30 s bound from the handoff's approximate 28584 ms to 28464 ms: one machine-QA-passed job has 28464 ms audio; a recent barometer job has 28512 ms.
- M5 sends an obviously short first synthesis to one semantic-safe expansion. Failed expansion validation or a second out-of-window candidate terminates; old multiple timing-repair branches are no longer reachable through this path.
- factory.begin_render() now returns actual audio and product target durations. Speech remains within the audio; the final visual segment ends at the product target. M9 passes both durations; worker muxes unmodified narration and a target-length video. QA checks separately the final video (<=100 ms), muxed audio versus source audio (<=100 ms), scene coverage, codecs, dimensions, 30 fps, SHA and asset uniqueness.
- Earlier job 38cc57d3-6dfd-4e84-9f2e-dc9eba31944a was created before this pass and failed M8 because S3 required a weather station on a desk while three Gemini-reviewed photos showed outdoor stations. Vision correctly rejected them. Generic M5 visual prompt constraints now discourage invented settings and mutually inconsistent photo requirements. Production behavior of this prompt change is still unobserved.
- Offline evidence: focused timing tests passed; full n8n-image Node suite 460/460 after the final route edit, real 30 s two-scene FFmpeg regression PASS (including 27 s and >30 s rejection, unchanged source audio), render-fit regression PASS, isolated Postgres 18 schema initialization and old->new begin_render signature migration PASS. The full suite was re-run after the final route edit and passed.
- Next gate: git diff --check, focused and full tests, commit/push; check zero active production executions, take workflow and DB/worker backups, deploy only M5/M6/M9 and the changed SQL/worker, compare active nodes/connections/settings with Git, and check worker health. Only then launch one new UK30 barometer Gemini smoke; never reuse failed IDs.