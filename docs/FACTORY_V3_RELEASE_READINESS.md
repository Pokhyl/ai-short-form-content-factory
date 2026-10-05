# Factory V3 release state — 2026-10-05

Project_ready=false. The new core and owner interface are packaged, not deployed or production accepted.

| Boundary | Actual evidence | State |
|---|---|---|
| Core/owner API | 78 unique controlled Python tests; native JavaScript syntax | PASS offline |
| Packaged runtime | Image d6f0a04, real psycopg/PostgreSQL; producer/stage races, no retry, immutable owner review insert | PASS isolated |
| Gemini selected model | Live GET models/gemini-3.5-flash-lite HTTP200; generateContent listed | PASS model metadata only |
| Google OAuth refresh | HTTP200, tokens never saved to Git/output | PASS refresh only |
| Exact Gemini key owner | Full key SHA256 from signed-in AI Studio equals scoped production fingerprint; project529636078126 / gen-lang-client-0532024148 | PASS UI binding |
| Gemini free tier | Exact-key row in signed-in AI Studio shows Free tier / Set up billing | PASS UI observation |
| Runtime billing API | Direct billing403 SERVICE_DISABLED; Service Usage itself disabled under explicit target quota project | Pending scoped API enable confirmation |
| V3 gateway/workflow/schema/service/route | Source/templates only | NOT DEPLOYED |
| New real photo/model/TTS/video execution | Zero generation/TTS calls; no new V3 MP4 | NOT ATTEMPTED |
| PL15/EN30/RU45/UK60 acceptance | No accepted release cases | NOT READY |

Diagnostic v3-account-boundary-20261005 is immutable. Do not rerun scripts/check_factory_v3_account.py or erase account-check.json. Successful model metadata does not prove the key's project is unbilled. No paid fallback.

The precise cause of HTTP403 is not captured; do not assert whether it was IAM permission, OAuth scope or service enablement. Official lookupKey requires apikeys.keys.lookup on the parent project and cloud-platform.read-only or cloud-platform OAuth scope:
https://docs.cloud.google.com/api-keys/docs/reference/rest/v2/keys/lookupKey

Project identity and Free tier are now independently established in Google UI with exact full-key SHA256 binding (key-ui-binding.json). Do not ask owner for Project ID again. Next boundary: explicit browser confirmation to activate only Service Usage and Cloud Billing metadata APIs in this known Gemini project; no paid billing, IAM, OAuth or key change. Preserve the completed known-project-billing.json and billing-api-config.json failures. Gateway quota-project header regression and n8n2.37.10 isolated import/export checks PASS; source not deployed. Build the checked gateway source image, then use a new bounded billing verification after actual API enable.

Deployment preparation is complete as templates under deploy/factory-v3. Do not start the compose service until a real0600 settings file has independently verified free-tier proof, dedicated gateway/owner secrets and exact database credential. Verify the current image ID equals acceptance/factory-v3/image-current.json. Never copy the placeholder file as live settings.

Provision only V3 gateway credentials/workflow and V3 tables (ledger.sql, preparation.sql, provider_cache.sql, review.sql); existing quota schema stays authoritative. Isolate the verified Gemini credential before enabling the gateway so shared credential rotation cannot silently invalidate key/project proof. Verify generated workflow uses that isolated key reference, push source, import once and verify exact active history. Record and compare unrelated31 workflow fingerprints, native M5/M8/worker hashes and project health before/after.

Join only the existing project media/proxy networks. Add ONLY the supplied /factory-v3 Caddy handle in publisher's block; preserve every other domain and existing publisher route. Validate Caddy config before a scoped reload. No broad restart.

Only after live gateway and service verification, push a fresh exact smoke UUID/topic/language/duration/budgets for one release case. Inspect actual media/ASR/QA, retain immutable failures, and continue sequential representative cases. Explicit user acceptance of actual MP4 remains separate from machine QA.
