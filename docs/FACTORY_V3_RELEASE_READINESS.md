# Factory V3 release state — 2026-10-05

Project_ready=false. The new core and owner interface are packaged, not deployed or production accepted.

| Boundary | Actual evidence | State |
|---|---|---|
| Core/owner API | 78 unique controlled Python tests; native JavaScript syntax | PASS offline |
| Packaged runtime | Image d6f0a04, real psycopg/PostgreSQL; producer/stage races, no retry, immutable owner review insert | PASS isolated |
| Gemini selected model | Live GET models/gemini-3.5-flash-lite HTTP200; generateContent listed | PASS model metadata only |
| Google OAuth refresh | HTTP200, tokens never saved to Git/output | PASS refresh only |
| Exact Gemini key owner | Live API Keys lookupKey HTTP403 PERMISSION_DENIED | BLOCKED |
| Identified project/billing | Not attempted after first denial | UNVERIFIED |
| V3 gateway/workflow/schema/service/route | Source/templates only | NOT DEPLOYED |
| New real photo/model/TTS/video execution | Zero generation/TTS calls; no new V3 MP4 | NOT ATTEMPTED |
| PL15/EN30/RU45/UK60 acceptance | No accepted release cases | NOT READY |

Diagnostic v3-account-boundary-20261005 is immutable. Do not rerun scripts/check_factory_v3_account.py or erase account-check.json. Successful model metadata does not prove the key's project is unbilled. No paid fallback.

The precise cause of HTTP403 is not captured; do not assert whether it was IAM permission, OAuth scope or service enablement. Official lookupKey requires apikeys.keys.lookup on the parent project and cloud-platform.read-only or cloud-platform OAuth scope:
https://docs.cloud.google.com/api-keys/docs/reference/rest/v2/keys/lookupKey

Next actionable boundary: obtain project-scoped Google access sufficient to identify this exact key and read its project/billing, or owner-supplied exact key/project identity with independent billing verification. Do not grant broader permissions blindly or modify the existing shared Google credential without scoped authorization. Create a new bounded diagnostic with a new record and push its plan before calls; preserve the original failure.

Deployment preparation is complete as templates under deploy/factory-v3. Do not start the compose service until a real0600 settings file has independently verified free-tier proof, dedicated gateway/owner secrets and exact database credential. Verify the current image ID equals acceptance/factory-v3/image-current.json. Never copy the placeholder file as live settings.

Provision only V3 gateway credentials/workflow and V3 tables (ledger.sql, preparation.sql, provider_cache.sql, review.sql); existing quota schema stays authoritative. Isolate the verified Gemini credential before enabling the gateway so shared credential rotation cannot silently invalidate key/project proof. Verify generated workflow uses that isolated key reference, push source, import once and verify exact active history. Record and compare unrelated31 workflow fingerprints, native M5/M8/worker hashes and project health before/after.

Join only the existing project media/proxy networks. Add ONLY the supplied /factory-v3 Caddy handle in publisher's block; preserve every other domain and existing publisher route. Validate Caddy config before a scoped reload. No broad restart.

Only after live gateway and service verification, push a fresh exact smoke UUID/topic/language/duration/budgets for one release case. Inspect actual media/ASR/QA, retain immutable failures, and continue sequential representative cases. Explicit user acceptance of actual MP4 remains separate from machine QA.
