# Release gate — current execution contract

## Latest topical-photo failure and offline correction — 2026-10-11

- Natural-speed acceptance r14 `19e8ad95-60a2-48cc-893b-491e235d9fd3` is immutable `failed_terminal`: 2 TTS sends measured 50,928 and 59,616 ms, and 3 Gemini calls were made. Render stopped because 17 unique photos could not cover all topical intervals. The first 31-second interval had only 5 relevant photographs for 9 cuts. No render was produced.
- `material_first.verify` now checks word- and character-weighted scene timing estimates before each voice send. Exact measured timing remains the render gate. The saved r14 initial plan passes; the corrected plan is rejected by offline replay before its second TTS. A fully relevant 17-photo control passes. Packaged material-first 181/181 and factory-v3 112/112 pass.
- Evidence: `acceptance/factory-v3/visual-capacity-preflight-20261011.json` and `acceptance/factory-v3/visual-capacity-preflight-deployment-20261011.json`. The first image was built ARM64, failed on the AMD64 VPS and was rolled back immediately. The reusable image builder now defaults to `linux/amd64`; exact amd64 image network-disabled suites pass. The compatible image is deployed and healthy at revision `4f49448`; Studio200, free-tier proof remains `gemini-3.5-flash-lite` with billing false. Database counts and other service IDs/images are unchanged. No provider calls or new jobs. The fix is deployed but not product-accepted. `project_ready=false`.
- Next: finish the connected offline release gate, then run one fresh bounded normal case; never repeat r14 or any failed ID. Preserve the natural-speed voice rule and strict visual relevance.

## Follow-on voice-variant selection correction — 2026-10-11

The deployed preflight blocks r14's corrected plan before a second TTS. A further generic correction now filters already-generated paragraph combinations by the same visual-capacity gate before proofread/review, then chooses the closest duration fit among feasible combinations. Regression uses the saved r14 photo/fact graph and controlled alternatives. Local material-first 182/182 and factory-v3 112/112 pass; this selector change is not yet packaged or deployed. Plan: `acceptance/factory-v3/voice-variant-photo-feasibility-plan-20261011.json`. No provider calls. `project_ready=false`.

## Verified state — 2026-10-07

- LIVE source9c8501df53e2385e477e99ad11750d323ae28212.216 exact-image checks PASS; app-only rollout protected snapshots equal/publichealth exact.
- Explicit owner instruction «так не останавливайся» authorizes continuing through diagnosed failures to actual output; supersedes historical automatic stops. Every fresh normal case remains bounded/free-only; failed/deleted IDs immutable, no blind repeats/second TTS for same case.
- Actual491002b6 reached one voice/alignment, then render stopped because fact8 paragraph needed3slots with1eligible photo. Native editor copied Russianisms despite model language approval, and raw planner pools dropped strict photo protocol flags. No native/HUMAN/MP4 approval.
- Current corrections propagate strict subject and original-byte fingerprints; partition oversized image groups; skip rate-limited photo hosts without retries; keep native editor independent of source wording and block observed wrong forms; check estimated unique-photo cadence and merge only adjacent same-role paragraphs before review/TTS.
- Actual saved15photos contain1visual copy.14distinct photos remain cadence-feasible after same-role merge; original actual voice timing replay with15different byte files also passes assignment. These are offline assignment proofs, not new output approval.
- New normal strict UK60 Vision c7bfd577-ac32-4d23-9451-ebd5aa926fee submitted on current revision. Actual new qualified photos/native text/voice/final MP4 verification pending. project_ready=false.

## Boundary verification contract
1. Produce one executable boundary inventory covering normal intake -> credential gateway -> research -> grounded outline -> all three photo providers -> download/exact bytes -> independent image review -> global unique assignment -> composition -> script review -> free quota -> one voice -> alignment -> render -> machine audit -> owner review. For each boundary distinguish actual native/provider evidence from controlled fixtures and list concrete uncovered failure modes. Do not count test totals as coverage.
2. Reconstruct the failed request from persisted research/source receipts without network. Bind the reconstructed outline payload to the stored request hash. Retain a sanitized reproducible fixture, not an unexplained screenshot or temporary log.
3. Connect existing components in a deterministic replay runner using saved real responses where available; keep controlled missing-provider fixtures visibly labelled. Use actual installed n8n HTTP execute, actual PostgreSQL claims/quota and actual media decode/render where those boundaries are exercised. No live production database mutation.
4. Run a representative corpus acrossPL/EN/RU/UK and15/30/45/60; exercise invalid provider JSON,429/400, missing or irrelevant photos, duplicate bytes, quote mismatch, stale contracts, duration mismatch, concurrent/ambiguous requests and strict terminal failures. Fixture coverage is NOT proof of unseen-provider quality. Resolve connected failures as a set before further product runs.

## External calls and release
Only after the offline inventory/connected suite closes, consolidate unavoidable provider uncertainty into a bounded release verification plan. Reuse existing model/billing/native proofs; no repeated metadata probes. Build one exact source artifact, run packaged gates, deploy only changed component after idle-state checks. Use normal input for a small representative acceptance matrix; never rescue a failed job. Actual MP4 playback/human acceptance is mandatory before claiming production ready.

## Communication and persistence
One concise update per completed stage or material blocker; no mechanical per-tool narration. One checkpoint for completed code+evidence+next action; maintain this compact status instead of repeatedly prepending the same long history. If the next step does not reduce a named unresolved boundary, do not execute it.
