# Release gate — current execution contract

## Latest topical-photo failure and offline correction — 2026-10-11

- Natural-speed acceptance r14 `19e8ad95-60a2-48cc-893b-491e235d9fd3` is immutable `failed_terminal`: 2 TTS sends and 3 Gemini calls produced a natural-speed 59,616 ms voice, but render stopped because 17 unique photos could not cover all topical intervals. The first 31-second interval had only 5 relevant photographs for 9 cuts. No render was produced.
- `material_first.verify` now checks word- and character-weighted scene timing estimates with the same unique, subject-related scheduler before voice synthesis. Exact measured timing remains the render gate. Regression: insufficient pool rejects before voice; a fully relevant 17-photo control passes. Material-first 180/180 and factory-v3 112/112 pass.
- Evidence: `acceptance/factory-v3/visual-capacity-preflight-20261011.json`. The first image was accidentally built as ARM64 on the Apple Silicon workstation, failed on the AMD64 VPS, and was rolled back immediately. App is healthy again on `35890a6`; DB counts and other service IDs/images are unchanged. The reusable image builder now defaults to `linux/amd64`; exact amd64 image network-disabled suites pass. The correction is not yet deployed or product-accepted. `project_ready=false`.
- Next: apply the already committed app-only rollout with the exact amd64 image, verify protected state, then continue the release gate. Never repeat r14 or any failed ID; do not start a new normal case until the connected offline release gate is complete.

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
