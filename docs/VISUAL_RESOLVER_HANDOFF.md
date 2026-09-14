# Visual resolver handoff

> Current authorization update (2026-09-13): the user explicitly lifted the production deployment restriction and asked work to continue. Deploying the tested renderer and creating a NEW normal validation job are now authorized. Do not ask for deployment permission again. TTS/settings and old jobs must remain unchanged. Production validation is in progress; HUMAN PASS still requires the user to watch the resulting MP4.


Branch: `codex/visual-resolver-rework-20260913`.
Issue: https://github.com/Pokhyl/ai-short-form-content-factory/issues/8

## Required reading

1. Issue #8 and `docs/CODEX_VISUAL_RESOLVER_TASK.md`.
2. `docs/VISUAL_RESOLVER_REVIEW.md` for implementation and production-baseline details.
3. `docs/VISUAL_RESOLVER_MAPPING.md` for every acceptance narration → entity → media.

## Completed

- Replaced fuzzy/prefix subject selection with source aliases, dictionary-normalized complete phrases, conservative subject rules, and exact Wikipedia/Wikidata identity.
- Isolated anaphora to the previous resolved semantic scene; removed incoming history/topic fallback paths.
- Added all-member montage treatment for explicit lists; Commons depicts verification; file dedup; timed exact-image alternatives; preflight before TTS/render.
- Preserved the existing TTS adapter and Whisper implementation byte-for-byte after synchronizing the actual production baseline in commit `e9463e3`.
- 38/38 tests pass natively and in the built Linux amd64 renderer with network disabled. This includes 32 acceptance narrations across four languages and real Wikimedia replay for all eight UK scenes.
- Read-only live UK resolver check passes all eight scenes. Exact responses are committed as a replay fixture.
- Docker build succeeded and release `6480f48` was deployed. The new validation job failed safely in preflight; no production MP4 exists. Original failed/rejected rows were verified unchanged on 2026-09-14.

## Resume safely

Work only on this branch. Read the PR and `git log` for final SHAs. The repository contains all implementation, tests, pinned NLP dependencies, replay data, mapping and build instructions; no previous agent memory is required.

The PR has been created and the additional resolver review regressions pass. Deployment is authorized. Do not replace production compose/workflows with the repository's older baseline configuration. Do not change Gemini TTS (`gemini-3.1-flash-tts-preview`, Enceladus, one synthesis per video), Studio UI, audio timing, or duration/quality gates. Failed/rejected jobs remain immutable.

There is no production MP4 and no HUMAN PASS. The deployed resolver rejected a mixed-population sentence as ambiguous; see the checkpoint below. Do not resume or repair this or other failed jobs.

Unsupported/ambiguous grammatical constructions and unavailable exact media fail preflight. Dictionary/source data are finite; passing the recorded scenarios is not a claim of unrestricted semantic understanding. Live source content can change; keep frozen tests deterministic and review any fixture update.

## Active production validation checkpoint

- Deployed source: `6480f48` (same branch). Renderer image: `ai-short-form-content-factory/short-video-maker:visual-6480f48`.
- Release: `/opt/ai-short-form-content-factory/releases/visual-resolver-6480f48` on `hodor-vps`.
- Compose uses the existing production `compose.yaml` plus this release's `compose.override.json`; only the renderer was recreated. Health is OK.
- TTS and Whisper runtime SHA-256 hashes match the pre-deploy versions.
- Rollback image: `ai-short-form-content-factory/short-video-maker:before-6480f48`, rebuilt from exact running overlay files because the previous Docker image had missing stored layers.
- 37/37 tests passed on the production host in the new image with network disabled before the switch.
- A NEW normal job was accepted via `https://publisher.hodor.com.pl/webhook/jobs`: `aaf35d9b-db00-4fb9-a618-22e8b7a16462`, topic `Сонячна система`, language `uk`, duration 60. The Studio proxy required browser Basic auth; its first unauthenticated attempt returned 401 and created no job. The publisher public endpoint targets the same normal intake workflow.
- Status checked 2026-09-14: FAILED. Video ID `cmu05t8it000001ln5h4j3pk7`. Preflight threw `ambiguous_subject` on scene 4, before TTS/render. This job is now immutable.
- Original failed/rejected rows: 39; pre-deploy digest `3922c0d31ee56eedb1b4dce2abf6acc2fff9961579e9b5c2a688ba1e5f273623`. Their read-only baseline is stored privately as `old-failed-before.jsonl` in the release directory. Verify only those original IDs after validation; new failed jobs must not be resumed or repaired.

## 2026-09-14 verified checkpoint

- Full suite: 38/38 native and Linux container offline, including a new deterministic regression for the actual rejected narration. Runtime code remains `6480f48`; this checkpoint changes tests/documentation only.
- Rejected narration: `Додатково до тисяч малих тіл у цих двох ділянках є інші популяції різноманітних дрібних тіл, як-от комети, метеороїди та космічний пил, що рухаються навколо Сонця.`
- Candidate conflict: `Малі тіла Сонячної системи` / `космічний пил`. No selected media. No fallback to previous TNO. The fail-closed requirement works, but the normal production job has not succeeded.
- 39 original failed/rejected rows compared in full by original IDs: unchanged; SHA-256 matches `3922c0d31ee56eedb1b4dce2abf6acc2fff9961579e9b5c2a688ba1e5f273623`.
- Remaining work: general semantic treatment of mixed-population/adjunct/example-list sentences with positive and negative multilingual regressions, without arbitrarily choosing a list member or accepting an unverified group. Then use a NEW normal job for end-to-end validation. Do not weaken the existing rejection to force this job through. Successful MP4 validation and user HUMAN PASS remain outstanding.

## 2026-09-14 implementation checkpoint (validation ongoing)

The previous mixed-population rejection has been addressed with explicit all-member treatment of existential example lists. Quantified coordinated subjects preserve both groups; descriptive paired appositions retain the leading subject. Unknown list members still fail. An inadequate page thumbnail can use exact same-QID Wikidata P18, with unchanged media quality gates. New tests were run failing before implementation.

51/51 tests pass natively. `tests/enumeration.test.cjs` includes multilingual non-astronomy cases, negative cases and exact member-media integration. Current changes are NOT deployed yet; live read-only preflight, container tests and a new normal job are still pending. Existing failed jobs stay immutable. Do not interpret the earlier 38-test checkpoint as the current implementation status.

### Additional safety and exact media checkpoint

54/54 native tests pass. Added rejection of unknown coordinated quantified subjects, per-member media identity/dedup, and exact Wikidata P527 all-part montages when a group has no usable page/P18/Commons image. P527 must be 2–8 unqualified, nondeprecated identities; each English sitelink must ground back to its exact QID. No generic parent-topic image is used. Live sequential preflight of the seven original production narrations is running; no failed job was changed.

### Live seven-scene preflight passed

All seven original production narrations now pass in sequence through live Wikimedia APIs, including exact all-member Comet/Meteoroid/Cosmic dust treatment, quantified groups, four verified Outer planets parts and Solar wind. Captured responses replay offline. See `docs/VISUAL_RESOLVER_PRODUCTION_MAPPING.md`. 55/55 native tests pass; final container run is in progress. Runtime source remains `faaa9d4`. Next: deploy this source after container checks, create a NEW normal public-intake job, inspect resulting audit and MP4. No new deployment/job has happened at this checkpoint.
