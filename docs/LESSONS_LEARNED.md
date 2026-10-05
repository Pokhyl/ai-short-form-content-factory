## 2026-10-05 — Import parity cannot prove native JSON invocation

Production n8n2.37.10 HTTP Request4.5 parser unconditionally JSON.parse on JSON query/header fields. Object-valued expressions passed static/import checks but failed at runtime before billing API; caller then got a non-JSON reply and immutable unknown. Serialize all JSON query/header/body/response expressions and explicitly select JSON body content type. Native parser regression reproduces old failure and preserves Unicode/nested values for all generated fields. Require a bounded actual gateway metadata roundtrip before the next product launch. Failed first V3 request remains immutable.

## 2026-10-05 — Native n8n import staging ownership

Docker cp from root-created0600 host files preserves root ownership; production n8n CLI runs as node. Actual controlled file-read contract gives EACCES before chown node:node and READ_OK afterwards while retaining0600. Stage private imports with exact owner and permissions, persist command failure receipts, then verify DB effects; never blindly repeat a failed import. First provisioning imported no credentials and never reached schema/workflow.

## 2026-10-05T16:29:31.926788+00:00 — Explicit quota project for native OAuth metadata

Cloud Billing read defaulted to OAuth caller quota context; V3 now derives x-goog-user-project only from the validated target billing project and forwards no caller headers. Regression reproduced undefined header, then passed, including CRLF/override rejection and unchanged Gemini/TTS paths. Service Usage itself being disabled requires console bootstrap, not repeated failing API calls. Exact-key Free tier evidence is independent of these metadata failures. Do not ask owner for a Project ID already read and SHA-bound from Google UI.

## 2026-10-05T16:19:56.995173+00:00 — Diagnose account metadata separately from product provider access

The old key-owner403 was not evidence that the owner must supply Project ID. Existing signed-in AI Studio exposed the exact project and Free tier; full credential SHA256 matched its exact key details. A separate direct billing check classified SERVICE_DISABLED. Preserve safe ErrorInfo reason/domain and distinguish metadata-service configuration from key failure, payment tier and IAM. Never erase failed diagnostics or infer free access from model HTTP200. Existing evidence: key-ui-binding.json, key-fingerprint.json, known-project-billing.json.

## 2026-10-05T15:51:47.429679+00:00 — Canonical test paths across operating systems

Production asset_path intentionally resolves filesystem aliases before serving SHA-verified media. Tests must compare canonical expected paths too; macOS /var and /private/var refer to the same temporary file. Fix the test expectation, preserve production path containment and hash checks. Reproduced77/78, corrected78/78; this says nothing about actual media acceptance.

## 2026-10-05T09:00:18.915555+00:00 — V3 CORE/OWNER PACKAGE VERIFIED; LIVE GOOGLE ACCESS BLOCKER; NOT DEPLOYED

Project_ready=false. New V3 core, producer/runtime/CLI, private fixed-route native credential gateway, owner intake/status/history/exact photographs/citations/licenses/MP4/review UI and scoped deployment templates are implemented and in Git. 78 unique controlled Python tests PASS; native browser JavaScript syntax PASS. Image factory-v3:d6f0a04 built from d6f0a04673be450f45c57314d71bdf8c09326b83; ID sha256:5092570e09471a3da42f445c4b369ebd625d7df264b8a5648ea668bc372779ca. Real psycopg/PostgreSQL packaged checks PASS: immutable request, concurrent producer1/2, ambiguous prep blocks, full stage chain/single voice/concurrent stage1/2, owner review inserted once. Actual service module/static-byte packaging, compose config and named Caddy route validation PASS. A test-only Caddy fixture formatting failure was corrected; failed log retained. Logs: acceptance/factory-v3/server-python.txt, image-postgres-driver.txt, package-checks.json; deployment templates deploy/factory-v3. Source runtime in image stays d6f0a04; later checkpoint commits do not change packaged runtime.

LIVE DIAGNOSTIC v3-account-boundary-20261005 COMPLETED ONCE: selected Gemini model info HTTP200; existing Google OAuth refresh HTTP200; exact key-owner lookup HTTP403 PERMISSION_DENIED. Stopped immediately. Project-info and billing-info NOT attempted; free_tier_confirmed=false, no proof invented. Actual generation/TTS/photo/source calls0, billing mutations0. Exactly two selected credential records exported to0700 temporaries; secret values never output/Git. Both container and host secret temporaries verified removed; no free-tier proof file exists. Immutable secret-free receipt: acceptance/factory-v3/account-check.json. DO NOT rerun/erase this diagnostic.

No new production V3 schema/service/workflow/route, no existing worker/n8n workflow modifications and no V3 MP4/actual release acceptance. Existing production stays intact. Model metadata and test counts are not product acceptance.

ACTIONABLE NEXT: obtain Google access scoped to the exact Gemini key's project, sufficient to identify the key and read project/billing, or owner-confirmed exact key/project identity plus independent billing verification. Official lookupKey requires apikeys.keys.lookup on the parent project and cloud-platform.read-only or cloud-platform OAuth scope (https://docs.cloud.google.com/api-keys/docs/reference/rest/v2/keys/lookupKey). The403's precise cause was not retained; do not claim IAM vs scope vs service enablement. Do not change the existing shared Google credential or grant broad roles blindly. Push a NEW bounded diagnostic ID/call plan before any calls after access changes; preserve original failure. This external access issue blocks live free-only generation. Independent packaging/interface work is complete for the current boundary.

After verified unbilled project: isolate that exact Gemini key/reference, provision only V3 gateway credentials/workflow/settings and V3-only tables, import/activate once and verify exact active version, then scoped compose/Caddy deployment with other31 workflow fingerprints/native hashes/health checks. Only then push fresh exact job UUIDs/budgets before sequential PL15/EN30/RU45/UK60 actual media acceptance. HUMAN PASS requires explicit actual-MP4 user decision. See docs/FACTORY_V3_RELEASE_READINESS.md and FACTORY_V3_RUNTIME.md. Continue factory-v3; old failed jobs remain immutable.

## 2026-10-05T08:47:57.872074+00:00 — OWNER UI/API IMPLEMENTED; READ-ONLY GOOGLE DIAGNOSTIC PLANNED; NOT DEPLOYED

78 unique Python tests PASS; browser JavaScript syntax PASS. New owner interface accepts topic/PL-EN-RU-UK/15-30-45-60, shows durable requests/status/narration/selected exact photographs/fact sources and licenses, streams only exact machine-passed MP4 with byte ranges, and records explicit immutable owner acceptance/rejection bound to the actual MP4 SHA. Private owner token, signed 12h HttpOnly/Secure/SameSite session, exact origin check, max1 running +4 queued requests; duplicate request never enqueues again. New review.sql is V3-only and NOT applied to production.

Image factory-v3:8ba8e8e built (sha256:fd9e1749d95b9388c19004bd4a236ae9a14efd8574d0eb7640d027be9c63e75d); real psycopg/PostgreSQL packaged runtime checks PASS: immutable request, concurrent producer1/2, ambiguous prep blocks, all stages/single voice/claim1/2. This image excludes newer UI/review; rebuild required. Logs image-postgres-driver.txt/server-python.txt/server-javascript.txt. Caddy n8n-caddy-1 routes publisher domain; isolated /factory-v3/ route can be added without replacing existing n8n/recovery routes. No new production schema/service/workflow or V3 MP4. Project_ready=false.

AUTHORIZED NEXT LIVE DIAGNOSTIC (NOT EXECUTED AT THIS CHECKPOINT): diagnostic_id v3-account-boundary-20261005, scripts/check_factory_v3_account.py. Exact unresolved questions: selected Gemini model exists; selected existing Gemini key belongs to a project whose billing is explicitly false; selected project Google OAuth can read only that key/project/billing. Export ONLY Gemini credential zsRz2tvE57EKe8zy and Google credential8KbFC6GBZOd18bzG into generated0700 temporary directories, no other credentials, no values in Git/output; delete temporaries. Maximum calls: selected model GET1, existing OAuth refresh POST1, exact key-owner lookup GET1, identified project GET1, its billingInfo GET1. Maximum credential exports2, one record each. NO generateContent/TTS/source/photo calls, no billing/key/account mutations, no provider retries/fallback. Expected generation/TTS quota0; metadata/auth API quota actual limits unknown, at most5 HTTP requests. Stop on first non200/unknown/invalid response, unavailable model, identity mismatch or billing not explicitly false; no repeat after account-check.json exists. Secret-free receipts go to acceptance/factory-v3/account-check.json; successful verified proof only to0600 /var/lib/factory-v3/gemini-free-tier-proof.json. Bounded background120s, HTTP8s, export20s. Commit+push this exact plan BEFORE diagnostic.

NEXT after diagnostic: record/push actual result; if free-only proof succeeds, provision isolated V3 key/gateway and scoped service/schema/route, verify exact active code, other31 workflow fingerprints/health and inactive jobs. Build/test current packaged UI/review. Only then fresh planned actual-media release cases PL15/EN30/RU45/UK60. If diagnostic blocks, close the actual boundary without paid fallback or inventing proof; continue independent packaging/interface work. Old failed jobs remain immutable.

## 2026-10-05T08:29:54.032916+00:00 — RUNTIME/SCOPED CREDENTIAL GATEWAY VERIFIED OFFLINE; NOT DEPLOYED

69 unique Python tests PASS, including paid-project rejection before research/model/voice, idempotent request creation and old-media-ID protection. Native n8n JavaScript gateway checks PASS (gateway-native-node.txt). New fixed-route private gateway uses existing project credential references, native Google OAuth refresh, no retries, no generic URLs; workflow source remains inactive and was NOT imported. Runtime/CLI connects trusted preparation -> one voice -> alignment -> render -> independent QA. Runtime requires server-owned free-tier proof and a per-request unbilled-project metadata check BEFORE generation.

No live provider/model/TTS calls, credential export/import, production mutation or new V3 MP4. Product_ready=false. Evidence: acceptance/factory-v3/runtime-python.txt, gateway-python.txt, gateway-native-node.txt, gateway-checks.json. Runtime source is now ready for image build; existing images are stale.

NEXT: build current image and run isolated real-PostgreSQL packaged runtime checks; implement public request/status/video/attribution/review interface. Before any scoped live credential diagnostics, record exact bounded read-only calls and stop conditions here and push; verify actual Gemini project billing/model without inventing proof. Then scoped credential-gateway/service deployment with unrelated-workflow/health verification, followed by fresh planned actual-media acceptance. Continue factory-v3; do not retry immutable failed jobs or legacy M5/M8.

## 2026-10-05T07:17:08.973390+00:00 — CONNECTED AVAILABILITY-FIRST PRODUCER VERIFIED; NOT DEPLOYED

60 unique Python tests PASS; isolated actual PostgreSQL checks PASS. Producer connects bounded fetched research -> exact-quote factual outline ->3 search contexts per unit across Pix/Pex/Wiki ->at most3 selected photo downloads/reviews per unit ->global unique-byte/factual coverage ->one composition ->independent semantic/topic review ->frozen plan/execution handoff. SQL atomic producer claim blocks duplicate runs. Frozen topic/language/duration and exact render bytes revalidated. Bounded source fetch pins public DNS address while retaining TLS hostname; private/mixed addresses and redirects rejected. Definitive selected-resource403/404/410 receipts replay without another call, allow another distinct source inside original budget;429/unknown remain terminal.

Controlled connected/provider/model fixtures only; no new actual provider/model/TTS calls, production changes or V3 MP4. Runtime image ade8a1d is stale. Product_ready=false. Logs: acceptance/factory-v3/producer-checks.json, producer-python.txt, producer-postgres.txt.

NEXT: trusted credential provisioning/automatic Google refresh, runtime constructor/CLI plus public intake/review; build current image and real PostgreSQL concurrent producer/runtime proof. Known project credential REFERENCES (not values) verified in Git workflows: postgres gQ3TDSsTe7Tn2X8B, Google OAuth8KbFC6GBZOd18bzG, Gemini zsRz2tvE57EKe8zy, Pix Z61TBglXcV08CRbT, Pex l6QGoHtq4KUiMaWe. Native old M6/M8 retry/fallback workflows are NOT invoked by V3. Record exact live diagnostics/budgets/free-tier proof before any provider/model/TTS request. Then scoped deployment and actual release acceptance. Continue factory-v3; old failed jobs remain immutable.

## 2026-10-05T06:59:13.858261+00:00 — PHOTO ADAPTERS/CACHE/DOWNLOAD VERIFIED OFFLINE; NOT DEPLOYED

52 unique Python tests PASS; isolated actual PostgreSQL ledger/preparation/cache checks PASS. Pix/Pex/Wiki adapters retain source metadata, author/attribution, exact license versions and response/rate headers. Exact query identity includes orientation/settings/non-secret credential scope; responses retained24h. Pending/unknown query claims block repeats. Selected photos download once and retain exact SHA/ffprobe dimensions; cached file tampering is rejected. Failed HTTP receipts preserve safe headers, never credential URLs/bodies. Preparation rejects changed language/duration at execution handoff. Evidence: acceptance/factory-v3/providers-checks.json and providers-*.txt; official documentation links recorded there.

Controlled fixtures only: no new actual provider/model/TTS calls, production mutations or V3 MP4. Runtime image ade8a1d excludes later changes. Product_ready=false. NEXT: research fetch/evidence and grounded unit outline; connect bounded catalog discovery/producer; trusted credential refresh; public intake/review and current runtime/concurrency checks. Then live free-tier/model verification, scoped deployment and representative actual-media acceptance. Continue factory-v3; immutable old failures and unrelated automation stay protected.

## 2026-10-05T06:48:24.753831+00:00 — BUDGETED GEMINI ADAPTER VERIFIED OFFLINE; NOT DEPLOYED

46 unique Python tests PASS. Gemini adapter sends exact image bytes, preserves HTTP/rate/usage provenance, uses source-revision-bound durable preparation calls and exact successful-response replay; no retries, Search grounding, model fallback or Gemini TTS. Trusted server free-tier confirmation required. Composer keeps scene contracts; independent final semantic review checks actual narrated claims. Grounded preflight now also enforces real-photo and per-scene factual approval. Tests include changed photo bytes, malformed/duplicate JSON, token-truncated response, unsupported narrated fact and receipt tampering. Official REST/schema references recorded in acceptance/factory-v3/gemini-checks.json.

This is controlled HTTP/model verification, NOT live credential/model acceptance. No new provider/model/TTS calls or production changes. Product_ready=false; no new V3 MP4. Native legacy downloader has internal429 retries; new V3 single-attempt downloader must avoid invoking that retry loop.

NEXT: durable24h provider cache, bounded Pix/Pex/Wiki adapters and single-attempt exact-byte downloads; fetched research and grounded unit outline; automatic trusted credential refresh; producer/public intake/review and runtime integration. Deploy only after live free-tier/model boundary verification, then actual representative media acceptance. Continue factory-v3.

## 2026-10-05T06:41:26.376285+00:00 — DURABLE PREPARATION BUDGETS VERIFIED; NOT DEPLOYED

38 unique Python tests PASS; isolated actual PostgreSQL assertions PASS. New preparation ledger persists every call before invocation, replays exact successful response only, bounds provider/model calls, forbids changed request/source revision, blocks ambiguous attempts without retry, records local rejection and atomically creates execution job only after frozen preflight. No actual provider/model/TTS calls or production mutations. Logs: acceptance/factory-v3/preparation-checks.json and preparation-*.txt.

Image factory-v3:ade8a1d successfully built with catalog/semantic preflight (sha256:b733bf6e1ddc905d6f492f32b9f2416ae7ea935416afa7f04fa9baa2e01d7f63). It excludes the later preparation ledger; not deployed. Python base tag remains unpinned; do not claim a pinned base digest. Product_ready=false; no new V3 MP4.

NEXT: implement live bounded research/photo/Gemini adapters using this ledger, persist rate headers and exact 24h cache identity, review actual render bytes; add automatic trusted Google credential refresh; wire public intake/review; build current runtime and verify real PostgreSQL concurrency. Then exact scoped deployment and PL15/EN30/RU45/UK60 actual media acceptance. Continue factory-v3; do not resume the legacy patch loop or retry failed jobs.

## 2026-10-05 08:25 Warsaw — CATALOG + SEMANTIC PREFLIGHT PASS; PACKAGED EXECUTOR PASS; NOT DEPLOYED

All32 unique Python tests PASS. Catalog/grounding validates source text hashes/exact support quotes, real-photo approval bound to bytes/contracts/evidence, globally feasible coverage BEFORE composition, fixed visual scene contracts/required factual scope. Trusted semantic script review must approve exact final text/language/evidence and every narrated fact; citation IDs alone are insufficient. New model callbacks are controlled tests; no live model/provider/TTS calls.

Image factory-v3:3e0f51c built;23 image tests and real psycopg3.3.6/PostgreSQL integration PASS: full stage chain, one voice attempt, ambiguous result blocks, concurrent claim1/2, quota1. Failed import-path/name-shadowing harness logs retained and corrected; isolated DB containers removed. Image excludes later catalog changes; image-executor.json records scope. Requirements pinned to actual installed versions. Base identification uses recorded build log; runtime artifact digest is recorded. No production schema/workflow/service/job changes. No new V3 MP4.

NEXT: build/test current committed catalog image, then implement live provider discovery/download/vision and composition/semantic adapters with durable preparation-call budgets; credential provisioning; public intake/review. Only then deployment and actual PL15/EN30/RU45/UK60 acceptance. Product_ready=false. Keep branch factory-v3; never resume legacy patch loop or failed jobs.

## 2026-10-05 08:03 Warsaw — V3 EXECUTOR AND MEDIA ADAPTERS IMPLEMENTED; NOT DEPLOYED

Current branch factory-v3. New ledger.sql/ledger.py use PostgreSQL atomic stage claims plus existing factory free-only quota functions. Executor verifies frozen media before the single voice send, records each stage first and refuses repeats after completed/failed/ambiguous/running states. Worker adapters call selected Google voices once, verify stored audio hash/window, align exact audio, build contiguous scene segments, reuse native renderer and run actual full-decode/audio-identity audit. Internal CLI/Dockerfile added. All23 UNIQUE Python tests PASS; disposable isolated PostgreSQL checks PASS. An earlier26 count included8 imported duplicates; removed and rerun. No provider/model/TTS calls, no production schema/workflow/service changes or jobs in this session. These interfaces are implemented, not yet exercised with a real new production job.

Source audit_final_media.py now accepts optional data_root; default /data unchanged. Token provisioning currently requires a trusted mounted access-token file; no automatic refresh yet. README gives runnable commands and precise limits.

NEXT: build/test isolated runtime image; implement trusted reviewed-media catalog and availability-led evidence-grounded composer; credential provisioning; integrate public intake/review. Only after full checks and exact deployment verification proceed to PL15/EN30/RU45/UK60 actual-media acceptance. Product_ready=false. Do not resume old M5/M8 patch loop. Failed legacy jobs stay immutable.

## 2026-10-04 23:15 Warsaw — V3 EXACT-MEDIA PREFLIGHT IMPLEMENTED; NOT CONNECTED TO PRODUCTION

Branch factory-v3 now has factory_v3/preflight.py: verifies actual local render bytes and provenance/license families, binds visual approval to exact scene contract/file hashes, checks all must-show concepts/min55/intent/exclusions, matches unique BYTES across providers, freezes final narration/scenes/assets/reviews, and revalidates before voice. All13 new tests PASS, including real historical7/9 blocker, stale contract/file, forged success, alias-image collision and multiple valid candidates. Controlled test receipts are explicitly synthetic tests, not new provider acceptance. No model/search/TTS calls and no production changes. Runtime TTS is NOT yet connected to this gate; product_ready=false.

NEXT: implement trusted availability-led provider/download/review inventory and evidence-grounded composition, then durable executor invoking verify_before_voice directly before existing one-TTS adapter. Exact downloaded render bytes must be reviewed, not another preview. Reuse working alignment/render; integrate intake/review and run actual release acceptance. Do not resume legacy M5/M8 patching. README and checked-in test logs describe runnable components and limits. Failed production IDs remain immutable.

## 2026-10-04 23:12 Warsaw — FACTORY-V3 IMPLEMENTATION STARTED; NOT DEPLOYED

Active branch factory-v3. Old correction/archive pushed on main at d358e4d1fe55c99b03759d60d0b74c21a7fc3fe8. New factory_v3/visual_plan.py implements global maximum unique matching, deficit witnesses and receipt revalidation before downstream work. Five meaningful tests PASS. Native saved failed12126 graph correctly blocks7/9 with both S6/S8 collision and S9 absence; acceptance/factory-v3/failed-12126-preflight.json. Zero provider/model/TTS calls, zero production mutations. This is a runnable first component, NOT a working end-to-end replacement or product acceptance.

NEXT IMPLEMENTATION: build the reviewed media inventory with exact file/source/license/review-contract hashes; availability-led evidence-grounded composition before TTS; freeze and connect preflight to durable execution. Reuse proven alignment/rendering components. See factory_v3/README.md for runnable commands and explicit missing components. Do not resume the old M5/M8 patch loop. Product_ready=false; PL15/EN30/RU45/UK60 acceptance pending. Current production unchanged; failed jobs immutable.

## 2026-10-04 23:09 Warsaw — USER AUTHORIZED ARCHITECTURE REPLACEMENT; PRODUCT NOT READY

User explicitly ordered radical project replacement. Stop the M5/M8 patch-and-production-retry approach. Preserve current production; create factory-v3 branch for an availability-first pipeline: evidence and actual reviewed assets -> globally feasible visual plan -> evidence-grounded narration -> frozen preflight -> one TTS -> alignment -> existing renderer -> actual media QA/review. Reuse working media processing and credential boundaries; do not touch unrelated automation. Architecture restrictions requiring the old video orchestration shape are superseded by this explicit user instruction, not product quality/free-only rules.

Historical correction checkpoint: full Node897/897 PASS; cached current-source replay74/81 matches, THREE unique missing source requests. All27 actual previous previews inspected; old approvals cannot prove stronger contracts. Code NOT DEPLOYED; no new API/model/TTS/job/import/restart. Latest failed9bf5e97c stays immutable. PL15/EN30/RU45/UK60 unaccepted; product_ready=false. Saved corrections are forensic/reference material, not a direction to continue that loop.

NEXT: implement and test the new pre-voice feasibility boundary using the real failed graph (maximum7/9), then availability-led planning and frozen provenance. Commit/push runnable changes and concrete limitations on factory-v3. Do not call a planner prototype a finished project.

## 2026-10-04 22:41 Warsaw — GENERIC CONTRACT CORRECTION OFFLINE PASS; NOT DEPLOYED

- Failed9bf5e97c remains IMMUTABLE visuals_failed (M8execution12126), no final MP4; NEVER relaunch. Live M5v226/M8v87/code60589e9 unchanged. No new provider call/job/import/publish/restart in this correction phase.
- Four new native failure regressions reproduced4/4 failures BEFORE correction. Current full Node893/893 PASS and SQL8/8 PASS. Seven M5 boundaries reject standalone EN/PL/RU/UK closure fillers; preserve two explicitly open/exposed intent/query-grounded authored subjects and their intent through normalization. Generic motor/coil, closed/unproved/abstract and real closing-sentence controls pass. Authored piercing relations survive. All three M8 adapters now retain surface-first as well as connector-first physical result retrieval; detailed queries, original anchors and exclusions stay exact. Strict Gemini/min55/three previews/global uniqueness/timing unchanged.
- Cross-corpus expectations updated only for deliberately retained exposed blade/piercing contracts, new surface-first result retrieval and guarded call shape; old immutable baseline snapshot preserved. Only JS parameters in seven M5 nodes and three M8 request builders changed; topology/settings/SQL/worker unchanged.
- Portable exact fixtures tests/fixtures/m5-m8-12126-contract.json and m8-12126-full-pools.json include original responses, context,81 effective requests, all normalized pools and all nine vision decisions. Synthetic narration copy replaces Koniec. only to isolate visual regression; no product job edited. Evidence/log hashes acceptance/release-coverage/12126-correction-checkpoint.json; failed and passing test logs retained.
- NOT ALL BLOCKERS CLOSED: new stricter exposed-detail/piercing contracts invalidate old matching-provider evidence. Actual preview inspection and integrated strict9 unique assignment/source identities remain required before deployment/fresh acceptance. S6/S8 previously share sole approved image; S9 had zero approvals. Do NOT treat893 passing tests as production readiness or launch another blind job.
- NEXT: inspect exact saved preview pixels/full pools, connected-contract selection feasibility and source cache identities; only bounded recorded provider diagnostics where this unresolved boundary requires new evidence. Current Pillow contact-sheet attempt failed because worker has no Pillow; no image files written, no dependency install/service change. Use existing FFmpeg for diagnostic sheets. Close all observed blockers, then full relevant checks/push; deploy changed components once with exact active/history/other31/health verification. PL15/EN30/RU45/UK60 final-media release acceptance remains pending. Continue autonomous work after status questions.

## 2026-10-04 — 9bf5e97c TERMINAL VISUALS_FAILED; ALL-SCENE BLOCKERS

- Job `9bf5e97c-0059-48a8-8e5d-7da1b1feb923` is IMMUTABLE. Single launch HTTP202 at17:48:43Z; M4-M7 passed; M8 run7acf65fd-9eef-42c3-8dd1-5accb3ec91c3/execution12126 failed17:56:06Z: no approved unique candidate for S9-A. M9 never started; no final MP4. NEVER relaunch this or any failed job.
- ALL nine Gemini responses inspected, not just reported S9: S9 has zero approved candidates; S6 and S8 each approve only the SAME image, so nine-unique assignment is impossible even with an isolated S9 fix. This contradicts treating previous saved nine-scene replay as adequate production reliability. No new provider call/job is authorized by this failure alone; root-cause offline closure is next.
- M5 execution12119 comparison: local normalization removed independently authored internal-component requirements in S2/S3/S4; accepted narration ends with prompt-forbidden filler Koniec. Investigate full repair/normalization boundaries and generic controls, not topic-specific patches or weaker gates.
- Tracked evidence: acceptance/release-coverage/production-status.json, production-launch.json, production-m5-contract-comparison.json, production-m8-all-scenes.json. Full decoded traces server .review/release-60589e9/acceptance-9bf5e97c/. Deployed M5v226/M8v87/code60589e9 remains unchanged; no pending deployment/restart/run. Existing offline checks passed but production acceptance FAILED; product_ready=false.
- NEXT: inspect original/repaired/final M5 contracts and ALL full provider pools/current ranking; identify mechanisms behind no-result and overlapping approved pools. Add connected-corpus regressions and controls; full checks, pushed correction and exact deployed verification precede any fresh acceptance. Continue authorized engineering after status questions. PL15/EN30/RU45/UK60 release matrix remains unaccepted.

## 2026-10-04 — 9bf5e97c LAUNCHED ONCE; M4-M7 PASS; M8 RUNNING

- Job `9bf5e97c-0059-48a8-8e5d-7da1b1feb923` launched EXACTLY ONCE at 2026-10-04T17:48:43.532740+00:00: HTTP202 accepted=true. Prelaunch HEAD/origin/remote f7bbbde7e68d1426520d23f91fd3b6d1f90131c1, ID in all three docs, DBcreated and active0 verified. Receipt acceptance/release-coverage/production-launch.json. NEVER repeat launch/create/import/publish/restart.
- Read-only DB snapshot after launch: research b06f89c0-defa-4b12-9f69-6496562310b6 PASS; script cb297883-0f5e-403a-b4a4-ff81ed861446 PASS; voice98ce297d-eca1-4baa-82bc-4bd330b5999e PASS; alignment d69ac10a-38f3-4293-b99b-59bdf0da5c6f PASS; visual7acf65fd-9eef-42c3-8dd1-5accb3ec91c3 RUNNING, job visuals_collecting; no render run yet. This is a snapshot, NOT a terminal result.
- Deployed code60589e9, M5v226/eb1c9f83-1e46-4ad4-8769-58430df6b491 and M8v87/264666d5-5c3d-4864-926e-22f28f7d9abf remain the verified release. Offline Node886/886, SQL8/8, separate5/5 and integrated nine unique selections passed. Product readiness NOT PROVEN.
- NEXT: follow this exact job read-only through M8/M9 to terminal, then actual final media inspection. If failed preserve it immutable, inspect full execution/all scenes and close blockers offline. Do not stop at a status report. PL30 regression does not replace PL15/EN30/RU45/UK60 representative acceptance. Earlier CREATED ONLY notes are historical.

# Lessons Learned

## 2026-09-25: a 15-second smoke misses long-schema failures

The same M5 provider schema worked for en15 but rejected a real uk45 request with HTTP400 INVALID_ARGUMENT. Reproduce the exact request and isolate schema admission before assuming language/content failure. A single scene shape with only an outer array count was accepted for en15/pl30/uk45/ru60; preserve exact lexical and structural constraints in deterministic local validation. Provider HTTP200 is not semantic or E2E acceptance: en15/ru60 diagnostic drafts still failed visual-contract validation. Test all supported language/duration contracts and explicitly track remaining E2E coverage.

Do not change HTTP nodes from continueRegularOutput merely to route errors: the deployed n8n retry detector depends on json.error on that output. Preserve the original provider failure in repair builders when there is no usable draft, retaining the existing original-draft fallback for transient repair errors.

## 2026-09-25: verify each required visual concept

A model aggregate PASS can contradict its own explanation. Require indexed evidence for every must_show concept and derive aggregate visibility in code. Replay the exact false-positive image bytes before deployment, then inspect every scene in the actual rendered MP4. The old missing-beam S3 was rejected by the revised checks; fresh job4b6a5e27 passed all five visual scenes. Keep technical/ASR audio evidence distinct from subjective listening.

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

63. Verify exact audio identity before changing alignment tolerances. Execution 9802 used the correct MP3, but Whisper heuristic offsets extended beyond it. Word-level output did not repair those offsets. A separate bounded DTW pass produced usable emission points; consuming t_dtw requires explicit unit/interval conversion and strict monotonic/bounds checks, not merely enabling the flag. Preserve both passes and keep failed jobs immutable.
