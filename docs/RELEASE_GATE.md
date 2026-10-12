# Release gate — current execution contract

## Generic photo-search hint gate — 2026-10-12

Commit `2cb7bf77d8c0955228c32c6b72278c224e26f426` added a topic-aware pre-search gate. Read-only inspection of the actual failed preparation in PostgreSQL exposed a second path: the initial brief was acceptable, but `material-brief-repair` changed its hints to `space` and `Hubble Space Telescope`; the following review checked facts only. Commit `e0f36979d40a1306d2c9b4e6367acba350588f3b` therefore revalidates after each repair in the review loop. A query-only correction cannot alter facts, fact IDs, or source bindings. The regression fixture records actual model outputs and call hashes; it explicitly does not contain the full source payload.

The offline material-first suite passed 197/197 locally and in the exact AMD64 runtime image; Factory v3 passed 112/112 in that image. Packaged checks ran with networking disabled. Image `factory-v3:photo-hint-review-e0f3697-amd64` (`sha256:22c92bd3bfb5e037c24ff624542482e9b1cb8730462d1d89bc064ee9de215214`) was built from that commit and was not deployed. Receipt: `acceptance/factory-v3/photo-hint-review-package-checks-20261012.json`.

This closes only the offline pre-search/review-repair regression and package boundary. The exact source/provider replay bundle, unseen provider availability, photo quality, and full connected release gate remain open; no new MP4 is evidenced. Keep `project_ready=false`; do not run a fresh production request until the connected offline release gate below is closed.

## Последняя UK60-проверка фото — 2026-10-12

Подготовка `6914b51b-f8c3-47d1-919e-f7b5cc15ffce` остановилась до narration/TTS: из 30 загруженных и проверенных фотографий лишь одна прошла независимую проверку релевантности и реального наблюдательного материала. Требуемый минимум для 60 секунд — 12 уникальных фото; поэтому остановка штатная. Звук и монтаж этой попытки не оценивались. ID immutable; повтор запрещён.

Сохранённые запросы показали дефект до поиска: `space`, `neutron star`, `Hubble Space Telescope`. Запрос `space` вернул общие фоны/стоковые изображения; запрос по телескопу — посторонние галактики и туманности. В доступных исходниках есть конкретные каталожные имена нейтронных звёзд, но общий генератор не выбрал их как поисковые сущности. Пиксельная проверка сработала строго и остановила плохой пул. Следующая офлайн-работа — обобщённый валидатор/выбор наблюдаемых сущностей на multi-topic corpus, затем connected replay всех затронутых границ. Не исправлять одним тематическим запросом и не снижать требования к фото.

Сохранённое подтверждение: `acceptance/factory-v3/availability-first-distinct-context-acceptance-20261012.json`; отчёт текущих границ: `acceptance/factory-v3/current-boundaries.json`. До следующего production запуска воспроизвести именно весь путь фото по сохранённым данным, проверить причины отклонения кандидатов и закрыть общий connected offline release gate. Не снижать минимум фото, не принимать иллюстрации вместо наблюдений и не считать тесты компонентов доказательством сквозного результата.

## Latest topical-photo failure and offline correction — 2026-10-11

- Natural-speed acceptance r14 `19e8ad95-60a2-48cc-893b-491e235d9fd3` is immutable `failed_terminal`: 2 TTS sends measured 50,928 and 59,616 ms, and 3 Gemini calls were made. Render stopped because 17 unique photos could not cover all topical intervals. The first 31-second interval had only 5 relevant photographs for 9 cuts. No render was produced.
- `material_first.verify` now checks word- and character-weighted scene timing estimates before each voice send. Exact measured timing remains the render gate. The saved r14 initial plan passes; the corrected plan is rejected by offline replay before its second TTS. A fully relevant 17-photo control passes. Packaged material-first 181/181 and factory-v3 112/112 pass.
- Evidence: `acceptance/factory-v3/visual-capacity-preflight-20261011.json` and `acceptance/factory-v3/visual-capacity-preflight-deployment-20261011.json`. The first image was built ARM64, failed on the AMD64 VPS and was rolled back immediately. The reusable image builder now defaults to `linux/amd64`; exact amd64 image network-disabled suites pass. The compatible image is deployed and healthy at revision `4f49448`; Studio200, free-tier proof remains `gemini-3.5-flash-lite` with billing false. Database counts and other service IDs/images are unchanged. No provider calls or new jobs. The fix is deployed but not product-accepted. `project_ready=false`.
- Next: finish the connected offline release gate, then run one fresh bounded normal case; never repeat r14 or any failed ID. Preserve the natural-speed voice rule and strict visual relevance.

## Follow-on voice-variant selection correction — 2026-10-11

The deployed preflight blocks r14's corrected plan before a second TTS. A further generic correction filters already-generated paragraph combinations by the same visual-capacity gate before proofread/review, then chooses the closest duration fit among feasible combinations. Regression uses the saved r14 photo/fact graph and controlled alternatives. Exact amd64 image suites pass (material-first 182/182, factory-v3 112/112). Image r2 is deployed and healthy at revision `614090f`; Studio200, free-tier proof unchanged, DB counts unchanged, no provider calls or new jobs. Receipt: `acceptance/factory-v3/voice-variant-preflight-deployment-20261011.json`. Plan: `acceptance/factory-v3/voice-variant-photo-feasibility-plan-20261011.json`. `project_ready=false`.

## Adaptive photo-pool voice correction — 2026-10-12

Offline replay showed that no saved paragraph combination passes topical cadence with all 17 r14 photos, while a smaller subset of the same reviewed photos can pass. The selector now tries approved visual-pool prefixes at the minimum safe cadence and prunes only unused approved assets/observations after selection. Local and network-disabled amd64 image suites pass (183 material-first, 112 factory-v3). Image `factory-v3:gemini35-voice-adaptive-photo-pool-amd64-20261012-r1` is deployed and healthy at revision `516d98f`; Studio200; DB and other service IDs unchanged; no provider calls or production jobs. Receipt: `acceptance/factory-v3/adaptive-voice-visual-pool-deployment-20261012.json`. `project_ready=false`; r14 remains immutable and failed, and no final video is claimed.

## Duplicate retrieved-context repair — 2026-10-12

Six fresh UK60 IDs remain immutable: `7e35a252-eff1-4202-b534-a30371a2f9aa` stopped on duplicate labels; `b9f0421b-6a25-4a73-90d6-11c677627cc4` stopped on Gemini `UNAVAILABLE`; `fcee52f6-1af8-4102-be60-8002cceb3055` stopped on duplicate repair labels; `71d66aee-b30c-4591-8fe9-2650f376af96` failed independent metadata review; `39d12eda-e186-4d07-8e60-e3b6173d63d9` failed pre-search because duplicate provisional `supernova` hints were treated as final targets. No photos were downloaded, and no TTS/render ran. The availability-first fix now treats duplicate brief labels as search hints while preserving strict uniqueness after retrieved-context planning. It passes network-disabled amd64 suites (188 material-first, 112 Factory v3) and is deployed healthy; Studio root200; DB 28 jobs/107 preparations, zero active work, 365 MB free. Deployment made no provider calls/jobs. `project_ready=false`; no output is claimed. See `acceptance/factory-v3/provisional-hint-uniqueness-deployment-20261012.json` and the per-request acceptance records.

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
## Previous topical-photo failure and offline correction — 2026-10-11
