# Failure Ledger

Generated from production PostgreSQL on 2026-09-10. This is the durable engineering index. The exact per-job snapshot is `docs/failure-ledger/production-failures-20260910.jsonl`.

## Mandatory use

Before changing planning, retrieval, model contracts, TTS, visual selection, rendering, QA, or deployment behavior, search this ledger and `CURRENT_STATE_V5.md` for the same failure class. A failed/rejected product job must be recorded and pushed to GitHub **before** the next corrective code change. Failed/rejected jobs are immutable and are never repaired in place.

## Snapshot totals

- Exact failed/rejected records: **303**
- `failed` product jobs: **297**
- explicit rejected review artifacts: **6**

## Failure classes (diagnostic grouping; raw rows are authoritative)

- `visual_availability_or_relevance`: 77
- `voiceover_duration_or_budget`: 52
- `other_visuals`: 45
- `other_script`: 30
- `workflow_data_or_persistence`: 22
- `model_output_contract`: 22
- `provider_quota_or_timeout`: 20
- `visual_identity_or_contract`: 12
- `research_or_resolution`: 9
- `other_voiceover`: 8
- `human_or_review_rejection`: 6

## Failed stage distribution

- `visuals`: 135
- `script`: 101
- `voiceover`: 60
- `render`: 1

## Highest-repeat topics in recorded failures

- `How does a zipper work?`: 54
- `How the Panama Canal locks work`: 28
- `Why is the sky blue?`: 9
- `Как Илон Маск основал SpaceX?`: 9
- `Володир Зеленський`: 9
- `How does induction cooking work?`: 8
- `как образуется молния`: 8
- `How does an induction cooktop heat a pan?`: 7
- `Steve Jobs introduces the first iPhone in 2007`: 7
- `Ходор`: 7
- `Dlaczego niebo jest niebieskie?`: 6
- `как работает индукционная плита`: 6
- `почему извергаются вулканы`: 6
- `How does popcorn pop?`: 5
- `How do bees make honey?`: 5
- `Почему стекло прозрачное`: 5
- `why is the sky blue`: 5
- `как образуются облака и дождь`: 5

## Recent failures/rejections

| Created | Job | Topic | Stage | Result | Exact failure |
|---|---|---|---|---|---|
| 2026-09-07T15:46:50 | `b978e057-ab76-413d-8839-bcec6512fbe1` | How the Panama Canal locks work | `script` | `failed` | 400 - "{\"error\":\"invalid_rank_query\",\"message\":\"query must contain between 1 and 200 characters\"}" |
| 2026-09-07T20:42:00 | `515408f3-0f17-4ce4-aaf5-63d709998ee9` | How the Panama Canal locks work | `review` | `rejected` | HUMAN FAIL: only 3 photos across the entire ~16s video is visually too sparse; landscape source photos are displayed as landscape frames with blurred fill instead of being composed as native 9:16 mobile shots. Fix systemically: denser visual cadence and true p |
| 2026-09-08T06:33:02 | `f7401fa2-1b25-4af9-8835-a2add047cd91` | How the Panama Canal locks work | `voiceover` | `failed` | Voiceover duration 17.708s is still outside target after 3 story rewrites [line 1] |
| 2026-09-08T08:11:34 | `7927b142-545f-4251-93c0-f8173a0e6bfa` | How the Panama Canal locks work | `script` | `failed` | pre-script verified two-photo claim inventory 0/3 [line 1] |
| 2026-09-08T15:34:59 | `168472b5-ba0f-406e-9c1b-fe76e3ed8b74` | How the Panama Canal locks work | `script` | `failed` | candidate claim C4 needs a compact observable visual_target [line 1] |
| 2026-09-08T20:54:25 | `a7ffe07a-8e2f-4eba-b8ed-1a8a68603dd2` | How the Panama Canal locks work | `voiceover` | `failed` | duration story rewrite word count 44 missed hard target 30-34 [line 1] |
| 2026-09-08T22:58:36 | `cca532fa-2b9f-4f44-8c46-8aea19bb9c1f` | How the Panama Canal locks work | `voiceover` | `failed` | duration story rewrite word count 36 missed hard target 27-29 [line 1] |
| 2026-09-09T06:31:14 | `da025c06-dac9-45fc-8c10-78345b61100e` | How the Panama Canal locks work | `script` | `failed` | pre-script global reviewed visual inventory assets=3/6, claims=1/3 [line 1] |
| 2026-09-09T07:31:01 | `bc00ab62-e305-43ac-b8d8-9ed372456553` | How the Panama Canal locks work | `script` | `failed` | pre-script global reviewed visual inventory assets=2/6, claims=1/3 [line 1] |
| 2026-09-09T15:20:59 | `ef5b9af0-6312-4e18-98e5-54b25ae96f96` | How the Panama Canal locks work | `script` | `failed` | inventory reviewer returned invalid JSON for batch 1 [line 1] |
| 2026-09-10T07:34:22 | `b5c0f36e-0524-4b02-b569-e74fa99bcdf2` | How the Panama Canal locks work | `script` | `failed` | candidate claim C6 needs a compact observable visual_target [line 1] |
| 2026-09-10T09:35:24 | `27915acb-2aa5-49ab-920b-f64b5b62de3b` | How the Panama Canal locks work | `script` | `failed` | candidate claim 1 is incomplete [line 1] |
| 2026-09-10T10:04:44 | `70fe8dbc-dcf6-4793-8f20-d9007f9e1f79` | How the Panama Canal locks work | `voiceover` | `failed` | Voiceover duration 17.933s is still outside target after 1 bounded story rewrite [line 2] |
| 2026-09-10T10:24:59 | `d7bdcaec-1c36-4082-9105-e4f29efc8579` | How the Panama Canal locks work | `script` | `failed` | candidate claim C2 mechanism visual target is not claim-aligned [line 1] |
| 2026-09-10T11:25:27 | `477a7177-0651-4e86-bf1f-cd162b8844bd` | How the Panama Canal locks work | `script` | `failed` | duplicates claim or visual target [line 50] |
| 2026-09-10T12:56:25 | `2e84dc84-edd9-4e27-b2b1-6bc7c4aea4b3` | How the Panama Canal locks work | `review` | `rejected` | HUMAN FAIL 2026-09-10: visible landscape-card/static-slideshow presentation in 9:16 and narration-to-visual mechanism mismatch; user explicitly ordered visual subsystem rework. |
| 2026-09-10T13:56:58 | `e4dd9e69-830d-4caa-9caa-8d01609bf531` | как возникла жизнь на земле? | `script` | `failed` | visual exploration Q1 lost resolved-subject identity [line 1] |
| 2026-09-10T14:06:32 | `2f0baeec-dbbd-49f4-b7fe-0608be2d7a3e` | телескоп роман | `voiceover` | `failed` | 502 - "{\"error\":\"free_fallback_tts_failed\",\"message\":\"Free fallback TTS failed: Timed out\"}" |

## Permanent lessons already demonstrated

- Do not infer product quality from `review_ready`, workflow success, ffprobe, shot count, or renderer self-reported PASS.
- Do not force literal canonical-subject token identity onto concept/question/process topics.
- Do not use generic subject/context photos as proof or communication of hidden mechanisms/state changes.
- Do not require `photo` as the representation for an explanatory mechanism; diagrams/maps/documents/illustrations may be the truthful form.
- Do not freeze narration before executable visual support is known.
- Do not run a second creative media-search/rebind loop after the visual source of truth is frozen.
- Do not add topic-specific synonyms, manual asset selection, arbitrary threshold relaxation, retry/sleep loops, or old-job repair as a rescue.
- Do not declare composition/visual QA PASS with unconditional constants.
- Do not repeat one topic as the sole architecture proof; cross-topic stability is mandatory.
- Free-provider timeouts/quota failures must be treated as provider-path reliability defects; do not hide them by calling the product successful on another topic.
- Record operator/deployment mistakes in `CURRENT_STATE_V5.md` when they can affect future procedure.

## Raw snapshot integrity

The JSONL file is a dated immutable snapshot. Future checkpoints create a new dated snapshot rather than rewriting historical evidence.

### Operator/tooling note — V6 renderer dependency lookup

- 2026-09-10: VPS host has no `npm`; a read-only renderer dependency lookup failed before code mutation. Use a disposable Node/project container for npm metadata instead of installing host tooling or assuming npm exists.

- 2026-09-10: V6 dependency audit harness was accidentally run with `--network none`, causing `EAI_AGAIN` against npm registry. No vulnerability conclusion is valid from that run; repeat with network access.

### Dependency/security finding — V6 media worker

- 2026-09-10: valid `npm audit --omit=dev` found 2 high-severity findings via `sharp 0.34.5` / libvips/libheif. `@huggingface/transformers 3.8.1` forces the vulnerable 0.34.x range but is no longer imported by production media-worker source after SigLIP removal. Required correction: remove unused Transformers and upgrade direct `sharp` to fixed 0.35.4; do not ship the V6 renderer image with the known vulnerable unused dependency.

- 2026-09-10: first V6 Remotion `bundle()` smoke silently received no heredoc because `docker run` lacked `-i`; Node syntax passed, bundle was not exercised. Never treat an empty successful container exit as a bundle PASS; require the explicit `REMOTION_BUNDLE_PASS` marker.

### V6 renderer component failure — rendered-state similarity

- 2026-09-10: first true synthetic Remotion component run produced an MP4 but failed the new pixel gate with `states=2/3`, `adjacent=2`, `black=0`, `flat=0`. The three fixtures reused the same layout/geometry and differed mainly in palette/text, so this does **not** justify weakening the perceptual duplicate threshold. Required next proof: rerun unchanged renderer/QA using structurally distinct synthetic visuals. Production unchanged; no renderer PASS.
- The same network-isolated run logged a non-fatal Remotion usage-event fetch failure to `www.remotion.pro`; rendering itself continued. Do not conflate that telemetry warning with the pixel-QA failure.

### Operator/tooling note — V6 host Node absence

- 2026-09-10: the integrated `/render-v6 + WF05` precommit gate reached workflow JSON parse PASS, then host `node --check` failed with `node: command not found`. No renderer/source correction is justified by this result. All Node syntax/tests on this VPS must run in a disposable Node/project container; do not install host Node as a workaround. Production remained unchanged.

### Operator/tooling note — GitHub push transport mismatch

- 2026-09-10: docs commit `77643bd` was created locally, but `git push origin HEAD` failed because `origin` is an HTTPS URL and the non-interactive host could not provide a GitHub username. Do not modify git config or credentials. Use the existing deploy key with a direct `git@github.com:Pokhyl/ai-short-form-content-factory.git` push target for this checkout.

### Operator/tooling note — V6 host ripgrep absence

- 2026-09-10: a read-only gate-discovery script failed at host `rg` because ripgrep is not installed. No product test was interpreted from that failure and no source correction is justified. Use POSIX `grep/find` on host or a disposable tooling container; do not install host packages as a workaround.

### V6 WF05 regression migration — renderer endpoint routing

- 2026-09-10: integrated V6 deterministic gate reached workflow JSON parse PASS, `git diff --check` PASS and Node syntax PASS, then produced exactly `70 PASS / 1 FAIL`. The sole failure was `tests/wf05_visual_segments_regression.mjs`, which still asserted the legacy literal URL `http://media-worker:3001/render-v3`. Current WF05 intentionally routes `visual-facts-story-v1` to `/render-v6` while preserving `inventory-first-story-v1` on `/render-v3`. This is a regression-fixture migration requirement, not permission to restore V5-only routing. Update the test to prove both branches explicitly.

### Operator/test-harness note — structured invocation ran in wrong image

- 2026-09-10: V6 standard integration gate produced `FRESH_DATABASE_CONTRACT_PASS: 21 workflow SQL statements + staged writes` and `N8N_IMPORT_CONTRACT_PASS: 8 workflows on 2.37.10`. The subsequent structured invocation fixture was mistakenly run in plain `node:22-bookworm-slim` and failed before exercising product code because `/usr/local/lib/node_modules/n8n/node_modules/n8n-workflow` does not exist there. Re-run the unchanged fixture in exact `n8nio/n8n:2.37.10`; do not modify product code from this harness failure.

### Operator/test-harness note — wrong Remotion entry path in image gate

- 2026-09-10: the exact V6 image preverify script stopped before `docker build` because it attempted `sha256sum services/media-worker/remotion/index.jsx`, which does not exist. This is a harness path mistake, not a renderer/build result. Resolve the actual Remotion entry file from the checkout and rerun the unchanged image build gate.

### V6 isolated HTTP renderer integration failure — output stream contract

- 2026-09-10: exact preverified media-worker image `sha256:19a0ecc304807070b037c7168d4f445b5220f47a379e9763a294529d28e5873d` passed build/content SHA checks, but the first isolated server-level `POST /render-v6` returned HTTP 422: `V6 video could not be rendered: V6 render stream format does not match H.264 yuv420p / AAC 48kHz stereo contract`. The request reached the real server route, durable job-owned audio/visual paths, exact `provider-word-timing-v1`, Remotion render and post-render stream validation. Do not weaken the stream gate. First reproduce the exact fixture at component level and inspect actual ffprobe stream fields to determine whether the defect is renderer output or the synthetic fixture.
- The same harness then hit a separate shell/Python JSON quoting error while parsing the already-captured response. That parser error is not the product failure and must be corrected only in the test harness after preserving the HTTP 422 evidence.

### Operator/test-harness note — nested heredoc interpolation in V6 stream inspection

- 2026-09-10: the first direct component stream-inspection harness confirmed the synthetic input WAV is `pcm_s16le`, `48000 Hz`, `2 channels`, `3.000000 s`, then failed before `renderV6Composition()` because the outer shell expanded `${job}` / `${i}` inside an embedded Node heredoc under `set -u`. No renderer conclusion is drawn. Re-run by writing a standalone `.mjs` fixture file and executing it inside the exact image; do not alter product code from this quoting failure.

### V6 renderer root cause — Remotion emits full-range `yuvj420p`

- 2026-09-10: exact component replay of the HTTP fixture preserved the rendered MP4 and proved the stream mismatch precisely. Input WAV is `pcm_s16le`, `48000 Hz`, `2 channels`, `3.000000 s`. Remotion output is H.264 `1080x1920`, AAC `48000 Hz`, `2 channels`, container `3.051 s`, and measured pixel QA PASS `3/3 states`, `0 adjacent`, `0 black`, `0 flat`; however ffprobe reports video `pix_fmt=yuvj420p`, not required `yuv420p`, despite `renderMedia(pixelFormat:'yuv420p')`. Do not weaken the final stream gate. Normalize the completed Remotion video deterministically to limited-range `yuv420p` before final pixel QA/hash/publish, then verify the exact normalized artifact.

### V6 renderer verification closure

- 2026-09-10: renderer implementation commit `6482946b1376f43b8743cb81eb33aaf648fa00e8` passed `72/72` Node regressions, `13/13` Python regressions, fresh PostgreSQL, n8n 2.37.10 import, 5 structured model invocations, exact image SHA parity and isolated `/render-v6` HTTP proof. The final proof artifact is actual H.264 `yuv420p` + AAC 48 kHz stereo and measured pixel QA passed. This closes the renderer/composition-machine-gate blocker only; HUMAN review remains mandatory and production has not been promoted.

### Operator/test-harness note — wrong WF03 filename during TTS inspection

- 2026-09-10: the read-only TTS inspection successfully proved the current media-worker `audio/synthesize-free-fallback` path is still Microsoft Edge Read Aloud with two attempts, so it is not an independent provider. The script then failed only because it referenced nonexistent `n8n/workflows/WF03-voiceover.json`. Resolve the actual WF03 filename from the checkout and continue inspection; no product code change is justified by the path error.

### V6 Piper dependency probe — alignment JSON display failure

- 2026-09-10: disposable `python:3.11-slim` successfully installed `piper-tts[alignment]==1.8.0`, downloaded and alignment-patched `ru_RU-dmitri-medium`, loaded it with `include_alignments=true`, and synthesized the full Russian test sentence as one continuous `AudioChunk` (`22050 Hz`, mono, 141312 PCM bytes) with 80 phonemes and 80 phoneme alignments. The probe then failed only while JSON-serializing NumPy `int64` alignment fields for display. This is not a Piper synthesis/alignment failure. Re-run with explicit primitive casts; do not change product source from this harness error.

### Operator/tooling note — V6 timing inspection SIGPIPE

- 2026-09-10: a read-only timing-contract inspection used `grep ... | head` under `set -o pipefail`; `head` closed the pipe after its limit and `grep` exited on SIGPIPE, producing return code 141 before the Remotion caption source was printed. This is not a product/TTS/renderer failure. Repeat the inspection without a truncating pipe. No product source or production state changed.

### Operator/tooling note — Piper/Whisper snapshot-only mount failure

- 2026-09-10: RU component proof successfully synthesized one full narration with Piper as 3 sentence chunks in ~1.5s, but faster-whisper initialization failed because only the Hugging Face `snapshots/<revision>` directory was mounted. Its `model.bin` is a symlink into sibling `blobs/`, so the target was unavailable inside the disposable container. This is a cache-mount harness failure, not a Piper or faster-whisper model failure. Repeat with the full `models--Systran--faster-whisper-small` cache root (or dereferenced files); do not change product source from this result.

### V6 WF03 duration rewrite still rejects the V6 story version

- 2026-09-10: source inspection during independent TTS work found a real V6 execution defect in `Apply Duration Rewrite`: it still requires `old.version === 'inventory-first-story-v1'`, while `Require Eligible Voiceover Job`, persistence, and the V6 architecture accept `visual-facts-story-v1`. Therefore any V6 narration that is outside the first exact-duration measurement and legitimately enters the single bounded rewrite would fail before the rewritten narration can be accepted. Correct the version gate to accept both explicit story contracts without weakening the one-rewrite, frozen-identity, grounding, or sentence-completion rules. Production remains unchanged.

### Operator/tooling note — MIT Piper 1.2.0 voice downloader mismatch

- 2026-09-10: compatibility probe confirmed `piper-tts==1.2.0` installs on Python 3.11, reports MIT license, and exposes `PiperVoice`, but the probe then failed because this older package does not ship the newer `piper.download_voices` module. No synthesis compatibility conclusion is drawn yet. Repeat with pinned direct voice-model/config downloads and SHA verification; do not switch back to GPL solely because the helper module is absent.

### Operator/tooling note — V6 TTS change-set Dockerfile generator syntax failure

- 2026-09-10: the first source-mutation script for the Edge -> Piper/faster-whisper fallback stopped before Dockerfile/server/WF03 edits because the temporary Python string used to rewrite the Dockerfile had an unterminated quoted literal around the multiline `ENV` replacement. The standalone helper file may have been staged in the working tree before the failure, but no production state changed and no TTS implementation PASS is claimed. Preserve only this failure note, inspect the working tree, then resume from exact partial state with safer file writes.
- 2026-09-10: first full deterministic regression after the V6 independent-TTS change-set returned 73 Node PASS / 1 FAIL. `audio_provider_tail_trim_regression.mjs` was stale and required literal `wavPath`; current source uses `edgeWavPath` after splitting Edge/Piper temporary files. Exact source lines still call `trimProviderTrailingSilence(edgeWavPath, providerCues)` immediately before `normalizeNaturalVoiceoverTail(edgeWavPath, targetDurationSeconds)`. Treat this as a test-migration failure, not permission to weaken the Edge tail-trim gate.
- 2026-09-10: a full-suite harness after the Edge tail-trim test migration was invalid: it accidentally invoked host `node` for the loop (host Node is absent), hit reused `/tmp` output-file permission errors, and printed a false PASS marker because a failed `&&` guard was not the final command under `set -e`. Do not use this run as product evidence. Use a disposable Node container per test and an explicit numeric final `if`/`exit 1` guard. The same run independently exposed one real Python contract mismatch: `tts_provider_budget_regression.py` expects 95000 ms while the modified WF03 TTS request now differs; inspect exact source before changing either side.
- 2026-09-10: after replacing provisional TTS timeouts with bounded budgets, targeted `tts_provider_budget_regression.py` and Edge tail-trim passed, while `wf03_independent_tts_failover_regression.mjs` failed only because it still asserted the old provisional `>=360000` request timeout. The accepted contract is now Edge <=40s per attempt, two Edge attempts maximum, local Piper/Whisper <=180s, composite n8n HTTP guard 280s. Update the stale test; do not enlarge provider timeouts.
- 2026-09-10: integration gate fresh DB and 8/8 n8n import passed, then the structured-output regression did not execute because `n8nio/n8n:2.37.10` default entrypoint interpreted `node` as an n8n command. Re-run with `--entrypoint node`; no product conclusion may be drawn from this harness error.

- 2026-09-10: exact V6 TTS media-worker image build failed while downloading the checksum-pinned `Systran/faster-whisper-small` snapshot with `No space left on device`. OS/Python dependency layers had succeeded. This is build-host capacity, not a Piper/Whisper product failure. `docker builder prune -f` reclaimed only disposable builder cache; running production images/volumes were not touched. Before another build, inspect and remove only Docker objects proven unused.

- 2026-09-10: during disk-recovery checkpointing, direct non-root Git was rejected with `dubious ownership` for the root-owned repo. Do not add a `safe.directory` exception or alter git config. Use `sudo git -C` with the existing deploy key, matching prior successful repository operations.
- 2026-09-10: the post-disk-recovery V6 TTS build/verification script hit SentinelX's 600 s wrapper timeout, but immediate read-only Docker inspection proved the requested image had already completed as `sha256:921826cc6efec846e86c5089518711118201adc7382e08ad10a6c51741332b13`; no build process remained. Treat this as an operational wrapper timeout, not an image-build failure. Do not rebuild; verify the existing exact image.

- 2026-09-10: first network-disabled Edge→Piper image proof used `docker exec ... node -` without `-i`; stdin was not attached, so no POST occurred and no WAV existed. This is a harness-only failure. Re-run unchanged with `docker exec -i`; do not alter TTS source from this result.
- 2026-09-10: repeated known operator failure: isolated offline TTS proof used `docker exec ... node -` without `-i`, so Node received no heredoc, no HTTP request was made, and the response file was empty. This exact stdin-attachment mistake has occurred before. Mandatory lesson: any stdin-fed `docker exec` command must include `-i`; an empty response from such a harness is never product evidence.

- 2026-09-10: network-disabled Edge→Piper HTTP proof itself succeeded (`200`, `self_hosted_piper`, `failover_used=true`, pinned faster-whisper timing), but the final harness ffprobe used a stale `/audio/voiceover.wav` path instead of the endpoint-returned `jobs/<id>/voiceover/full.wav`. This is a harness-path mismatch only; re-probe the exact returned durable path without changing TTS source.
- 2026-09-10: corrected offline exact-image TTS proof genuinely sent the Edge-primary request in `--network none`, but `/audio/synthesize-free-fallback` returned non-2xx after ~19 s instead of succeeding through local Piper. The wrapper exited 2 and trap cleanup removed the response file before the body was surfaced. Treat this as a real component failure with incomplete diagnostics. Re-run the exact request while preserving HTTP body and container logs; no source correction is allowed before root cause is known.

- 2026-09-10: first V6 schema-prep helper failed before any DDL because nested shell quoting stripped quotes from `status IN ('new','running','waiting')`, yielding `column "new" does not exist`. Production schema was unchanged. Re-run the identical preflight with SQL on stdin; do not alter migration source from this harness failure.

- 2026-09-10: first isolated V6 stage-workflow generator aborted before import because the post-transform guard still found production ID `TJfA4ZYUEKSTad6k`. This is a staging-harness mapping defect. Find the exact residual JSON field, fix only the stage-copy generator, and retain the fail-closed guard; do not alter source workflows or production routing from this failure.

- 2026-09-10: after publishing isolated V6 stage workflows and restarting n8n, `/healthz` returned healthy before the stage webhook row was visible in `n8n.webhook_entity`. Seconds later startup logs confirmed all five stage workflows activated and the DB contained `V6SmhHfzATicrvTF|v6-stage/jobs|POST`. This is a restart-readiness race, not a workflow activation defect. Future deployment/staging readiness must require both health and the expected webhook registration before proceeding.

### 2026-09-10 V6 stage cross-topic preflight DB-user mistake

The first preflight for the V6 stage cross-topic run failed before any webhook POST because the operator harness used the disposable-test PostgreSQL user `appuser` against the production database container. PostgreSQL correctly returned `role "appuser" does not exist`. No product job, workflow execution, database mutation, media artifact, or production routing change occurred. Future production DB probes must execute `psql` using the container's own `${POSTGRES_USER}` / `${POSTGRES_DB}` environment variables without printing secret values.

### 2026-09-10 V6 stage monitor stale jobs-column name

After creating the first V6 stage cross-topic job, a read-only monitor queried `public.jobs.stage`; the current durable column is `current_stage`. PostgreSQL rejected the monitor before it could report product state. The product job itself is unaffected. Monitoring scripts must inspect the current schema and use `current_stage`; do not infer job failure from this harness error.

### 2026-09-10 V6 stage cross-topic failure — SearXNG fetch

First real V6 stage cross-topic job `8985460d-4473-4111-9737-ddfa6233df60` (`Почему небо голубое?` / `ru` / `15`) is immutable FAILED at `script`. Stage WF01 execution `17456` succeeded; stage WF02 execution `17457` failed with exact durable error `502 - {"error":"research_search_failed","message":"SearXNG research failed: fetch failed"}`. No voiceover, visuals, render, MP4, or HUMAN review exists for this job. Do not retry/resume it. Before changing product code, prove whether this is stage network configuration or a shared media-worker research defect.

### 2026-09-10 V6 stage SearXNG failure root cause — missing edge network

Read-only comparison proved stage job `8985460d-4473-4111-9737-ddfa6233df60` failed because `cf-v6-stage-worker` was attached only to `ai-short-form-content-factory_default`, while shared `ai-short-form-v4-search` is reachable on `n8n_default`. Production media-worker is attached to both networks and its identical `SEARXNG_URL` returns HTTP 200; stage worker returned `fetch failed`. This is staging infrastructure parity, not a V6 research-code defect. Correct only the stage worker network attachment; do not resume the failed job and do not change product retrieval logic.

### 2026-09-10 V6 stage direct progress probe quoting/sudo failure

A read-only progress probe for stage job `5d073afc-3733-4f7e-8288-42e58a5304fa` was mistakenly issued through direct exec without sudo and with nested shell quoting that broke the SQL command. It failed with shell `command not found` fragments and Docker socket permission denial. The job and production state were not mutated. Subsequent job-state probes must use privileged `sentinel_script_run` with standalone SQL quoting, not nested direct-exec shell composition.

### 2026-09-10 V6 stage diagnostic transport interruptions

A read-only SentinelX child-execution diagnostic for stage job `5d073afc-3733-4f7e-8288-42e58a5304fa` first returned connector HTTP 502 before host evidence, then a subsequent docs-checkpoint attempt was interrupted by a SentinelX hub restart (`agent_offline`) before any host action. Neither transport event changed the server, repository, job, workflow, database, container, or artifact. These are operator-tool transport failures only and must not be treated as V6 product evidence.

### 2026-09-10 V6 stage cross-topic failure — Visual Facts reviewer unavailable

Second real V6 stage job `5d073afc-3733-4f7e-8288-42e58a5304fa` (`Почему небо голубое?` / `ru` / `15`) is immutable FAILED at `script`. Stage WF01 execution `17460` succeeded; stage WF02 execution `17461` failed after roughly 205 seconds with exact durable error `visual fact reviewer unavailable after bounded provider failover for batch 1 [line 1]`. The earlier SearXNG network defect was already corrected: this run advanced past research into actual-image review. No voiceover, WF04/WF05 render, MP4, or HUMAN review exists. Do not resume or repair this job. Before changing source, inspect exact child V4 model-gateway executions and reviewer payload/result to distinguish provider availability, schema-output failure, or V6 reviewer-contract incompatibility.

### 2026-09-10 V6 reviewer 12+12 replay harness JS failure

The first component replay intended to split immutable reviewer execution `17467` from 24 images into deterministic 12+12 halves did not reach the V4 model gateway. The diagnostic Node script incorrectly called `.catch()` on the return value of `process.stdin.on(...)`, causing `TypeError: process.stdin.on(...).catch is not a function`. No provider call from this replay, product job mutation, workflow/database change, or source change occurred. Re-run using a standalone JS file with execution data passed on stdin.

### 2026-09-10 V6 reviewer split proof — 12-image Kilo still length-limited

Exact component replay of immutable reviewer execution `17467` deterministically split its 24-image batch into two 12-image halves and sent both through the unchanged V4 model gateway. Both calls returned HTTP 200. Kilo `stepfun/step-3.7-flash:free` still failed on both halves with `finish_reason=length` (`unusable finish_reason:length` / `empty model output`), while Gemini `gemini-3.1-flash-lite` completed both halves successfully. Therefore reducing reviewer batch size only from 24 to 12 does not restore an independent Kilo reviewer fallback. No product job was resumed or mutated.

The diagnostic script then returned nonzero only during cleanup because the temporary JS copied into the n8n container was root-owned and `docker exec` attempted to remove it as the default node user (`Operation not permitted`). Both model calls had already completed. Future cleanup must run as container root; this cleanup error is not product evidence.

### 2026-09-10 V6 reviewer split proof — 6-image Kilo still length-limited

Exact component replay of immutable reviewer execution `17467` split the same 24 reviewed images into four deterministic 6-image chunks and sent all four through the unchanged V4 model gateway. All calls returned HTTP 200. Kilo `stepfun/step-3.7-flash:free` failed all four chunks with `finish_reason=length` / empty model output; Gemini `gemini-3.1-flash-lite` completed all four. This proves reviewer batch cardinality alone is not the root cause and that Kilo is not currently a functional reviewer fallback even at six images. No product job or durable product row was resumed or mutated.

### 2026-09-10 V6 reviewer one-image control — Kilo still length-limited

A final control replay used only one exact image from immutable reviewer execution `17467` with the unchanged Visual Facts reviewer prompt/schema and V4 model gateway. The call returned HTTP 200 through Gemini, but Kilo `stepfun/step-3.7-flash:free` again ended with `finish_reason=length` and empty model output. Therefore reviewer batch size is conclusively not the cause: the current Kilo visual-review lane is nonfunctional even for one image. Do not spend further product iterations lowering batch cardinality. Inspect Kilo completion/reasoning usage next; if hidden reasoning consumes the 4096-token budget, disable it by provider contract, otherwise replace/demote Kilo for multimodal review with an independent free reviewer.

### 2026-09-10 V4 source-inspection export-shape mistake

A read-only source inspection for `V4-model-gateway.json` assumed the exported workflow file root was an object, but this file is an array containing one workflow object. The diagnostic failed with `TypeError: list indices must be integers or slices, not str`. No workflow, provider configuration, database row, container, or job was mutated. Future inspection must normalize exported workflow JSON as `array -> first workflow` before reading nodes.

### Operator/tooling note — repository ownership under SentinelX account

- 2026-09-10: a read-only repository orientation command was run as the SentinelX service account and stopped at Git safe-directory protection (`detected dubious ownership`). No repository or production state changed. Do not modify global/local Git configuration to bypass this; run repository Git operations through the existing privileged execution path that owns the checkout.

### Operator/tooling note — nonexistent migrations search path

- 2026-09-10: a read-only schema search included a nonexistent top-level `migrations` path after already finding the required definitions under `db/migrations`, causing grep to exit 2. No product or repository state changed. Use the actual repository paths discovered by `find`/existing layout instead of speculative path operands in strict shell commands.


### V6 storyboard-first planning regression — legacy model-gateway reference remained

- 2026-09-10: first `v6_storyboard_first_planning_regression.mjs` run failed because `WF02-plan-script-and-scenes.json` still contained `/webhook/v4-model-gateway` in the retained semantic-intake/topic-resolution nodes. The new storyboard and final-story nodes already used `v6-model-gateway`, but the retained upstream text calls had not yet been remapped. No workflow was deployed and no product job was started. Correction must remap every V6 WF02 model call to the separate free-only V6 gateway; legacy V4 gateway remains untouched for rollback.

### 2026-09-10 — V6 focused regression command used host Node that is not installed
- Engineering/test failure: after wiring storyboard-first WF04/WF05 support, the focused regression command attempted `node ...` directly on the VPS host and failed with `node: command not found` before any Node regression executed.
- Cause: operator chose the host runtime instead of the exact Node runtime already available in the n8n/media-worker containers.
- Product impact: none; workflow JSON parsing completed, but regression execution was not proven by that command.
- Lesson: run V6 Node regressions inside the pinned n8n/media-worker Node 22 container/runtime; do not assume host Node exists.

### 2026-09-10 — n8n image regression retry hit image entrypoint instead of Node binary
- Engineering/test failure: retrying the V6 Node regressions with `docker run ... n8nio/n8n:2.37.10 node ...` invoked the image's n8n entrypoint, which treated `node` as an n8n command and returned `Error: Command "node" not found`.
- Cause: container invocation did not override the image entrypoint.
- Product impact: none; no regression body executed.
- Lesson: invoke the pinned image with `--entrypoint node` for repository Node regressions.

### 2026-09-10 — bounded deployment-history grep included missing paths
- Engineering/operator failure: a read-only grep for prior stage deployment commands included repository paths `scripts` / `.github` that are not present in this checkout; under `set -euo pipefail` grep returned exit code 2 after printing useful matches.
- Cause: operator passed optional paths without checking existence.
- Product impact: none; no runtime or source mutation occurred.
- Lesson: search only confirmed paths or build the path list conditionally before grep.

### 2026-09-10 — new V6 free-only gateway source omitted n8n owner ACL metadata
- Engineering defect found before deployment: `n8n/workflows/V6-model-gateway.json` had `shared: []`, while deployable workflow sources require the personal project owner ACL used by the existing V4 gateway and stage workflows.
- Cause: the new gateway generator intentionally stripped legacy workflow metadata but also stripped required n8n ownership metadata.
- Product impact: none yet; the V6 gateway has not been imported or published.
- Lesson: new standalone n8n workflow sources must preserve a valid `workflow:owner` shared entry with their own workflowId; add a regression before deployment.

### 2026-09-10 — V6 gateway ACL regression edit used a stale test marker
- Engineering/edit failure: the source ACL correction was written successfully, but the same helper then failed before updating the regression because it searched for a marker string not present in the current test file (`test marker missing`).
- Cause: operator assumed an exact test-file line shape instead of inspecting the current file first.
- Product impact: no runtime impact; source gateway owner ACL is corrected in the working tree, but the regression has not yet been strengthened.
- Lesson: inspect the bounded current test content before deterministic insertion; do not couple a source mutation and an unverified marker-based test mutation in one helper.

### 2026-09-10 — stage workflow generator assumed WF01 webhook node name
- Engineering/operator failure: the storyboard-first stage import generator stopped before writing an import file because it searched WF01 for a node named exactly `Webhook`; the current WF01 webhook node has a different name.
- Cause: generator depended on a stale node-name assumption instead of selecting the unique webhook by node type.
- Product impact: none; no workflow import/publish/runtime mutation occurred.
- Lesson: stage generator must identify WF01 webhook by `type=n8n-nodes-base.webhook`, assert uniqueness, then rewrite its path.

### 2026-09-10 — V6 stage deploy health poll reused root-owned fixed /tmp file
- Engineering/operator failure: after successful import/publish of the six V6 stage workflows and n8n restart, the bounded health loop redirected into fixed `/tmp/n8n-health.out`; an older root-owned file blocked the redirection and produced repeated `Permission denied`. The script later printed stale content from that path, so that particular health line is not valid deployment evidence.
- Cause: fixed shared `/tmp` evidence filename was reused across sudo execution contexts.
- Product impact: workflow import/publish/restart completed; subsequent DB checks in the same run independently showed both V6 webhook rows registered and all six V6 workflows active/current, while production WF01-WF05 version snapshot remained unchanged. Health itself must be re-proven separately before a new job.
- Lesson: use a unique evidence path under the deployment backup directory or capture health into a shell variable; never reuse fixed `/tmp` evidence files.

### 2026-09-10 — postdeploy verification helper had shell quoting error after successful health checks
- Engineering/operator failure: the V6 postdeploy verification helper successfully re-proved n8n health, stage-worker health, both V6 webhook registrations, and zero active executions, then terminated with `unexpected EOF while looking for matching quote` before completing production-default diff and six-workflow active/current count checks.
- Cause: an over-complex nested shell/SQL quoting expression in the remaining verification block.
- Product impact: none; no source/runtime mutation occurred in this verification helper.
- Lesson: use Python/subprocess or simpler SQL quoting for multi-line verification; do not pack nested shell quoting into long fail-closed scripts.

### 2026-09-10 — first fresh V6 stage submission helper did not pass stdin into docker exec
- Engineering/operator failure: the first attempt to POST a fresh `Почему небо голубое? / ru / 15` stage job used `docker exec ... node -` without `-i`; Node received no stdin script, exited successfully, and no HTTP request was sent.
- Cause: incorrect Docker stdin invocation.
- Product impact: none; no job was created, so there is no failed/rejected product row to preserve.
- Lesson: use `docker exec ... node -e <script>` or explicit `docker exec -i` when running inline Node through stdin; verify the HTTP status/body and resulting job row before treating a submission as created.

### 2026-09-10 — fresh V6 job monitor used invalid psql variable cast syntax
- Engineering/operator failure: monitoring fresh stage job `9bbe6a4b-70dc-46ef-98e6-d06fd15fdfb3` failed immediately because the psql query used `:'job'::uuid` in a context where the variable substitution was not parsed as intended, producing a SQL syntax error before any row was read.
- Cause: unnecessary psql variable indirection in a fixed-UUID read-only query.
- Product impact: none; the product job continues independently in n8n/PostgreSQL and was not modified by the failed monitor.
- Lesson: for fixed internally generated UUIDs, use a safely embedded quoted UUID in read-only SQL or Python/subprocess parameter handling rather than fragile psql meta-variable syntax.

### 2026-09-10 — long blocking V6 job monitor exceeded tool execution window
- Engineering/operator failure: a long-lived Python polling helper for fresh stage job `9bbe6a4b-70dc-46ef-98e6-d06fd15fdfb3` exceeded the remote tool execution window and returned a timeout before a terminal result could be reported.
- Cause: operator used one blocking multi-minute tool call instead of short bounded status probes.
- Product impact: none; the job runs independently and was not modified by the monitor.
- Lesson: use short one-shot DB/execution probes and repeat as needed; do not hold a SentinelX tool call open for the full product execution.

### 2026-09-10 — V6 fresh-job execution lookup assumed nonexistent job_events.execution_id
- Engineering/operator failure: a one-shot status probe successfully read fresh job `9bbe6a4b-70dc-46ef-98e6-d06fd15fdfb3` as `created/intake`, then its optional execution lookup failed because it assumed `public.job_events.execution_id` exists.
- Cause: stale schema assumption in a read-only diagnostic query.
- Product impact: none; the job row was not modified. The useful observation is that the job remained `created/intake`, so the stage orchestration must be inspected directly in n8n execution history.
- Lesson: inspect known n8n stage workflow executions directly; do not infer an execution foreign key in product tables without schema evidence.

- 2026-09-10 V6 storyboard-first fresh stage job `9bbe6a4b-70dc-46ef-98e6-d06fd15fdfb3` failed in WF02 execution `17496` before any storyboard was created. Exact execution evidence shows `V6ModelGatewayFreeOnly` execution `17497` returned `provider_exhausted=true`: `stepfun/step-3.7-flash:free` ended with `finish_reason=length` and `empty model output` even for the text-only semantic-intake prompt. WF02 then exposed a second defect: `Prepare Planner Failure` could not recover `job_id`, so the failed execution left the job row at `created/intake` instead of persisting product failure. Do not resume this job. Before another product job, replace the unusable StepFun text route with a currently verified zero-cost model and make the WF02 failure handler recover the job id from the new storyboard-first node path; prove both with regressions and a direct gateway fixture.

- 2026-09-10 free-model replacement diagnostic used the live unauthenticated Kilo `/models` catalog and one bounded parallel semantic-intake fixture. `nex-agi/nex-n2.5-pro:free` PASS (`stop`, valid required JSON, 515 chars) and `nvidia/nemotron-3-super-120b-a12b:free` PASS (`stop`, valid required JSON, 950 chars). `nex-agi/nex-n2.5-mini:free` returned only `{}` and failed required shape; `dots-studio/dots-3-note-preview:free` and `liquid/lfm-2.5-2.6b:free` both ended `finish_reason=length` with zero content. Do not retry the three failed candidates for the same role. The replacement path may use the two proven zero-priced specific models only, with bounded failover and local schema validation.

- 2026-09-10 V6 stage deployment attempt after commit `251bd19` failed before any workflow import/publish because the generated `V6-model-gateway.json` contained duplicate node IDs/names for `Nex Free Model`, `Normalize Nex Response`, `Nex Succeeded?`, and `Normalize Nex Success`. n8n rejected the workflow structure during import; no workflow was imported, published, or restarted by this attempt. Root cause: the source-mutation script renamed existing nodes in-place and then appended the same renamed node objects again because the removal filter still matched only the old names. Correct the source to one unique node instance per role, strengthen the regression to assert unique node names/IDs, then retry deployment from a new verified GitHub commit.

- 2026-09-10 live V6 gateway probe execution `17501` ultimately succeeded, but the engineering client timed out at 110s because the new primary `nex-agi/nex-n2.5-pro:free` itself hit the n8n HTTP timeout at 90,000ms (`ECONNABORTED`), after which `nvidia/nemotron-3-super-120b-a12b:free` fallback completed in about 20.6s with valid schema-conforming JSON. This is not acceptable as the normal primary route. Promote the proven Nemotron free model to primary and keep any secondary attempt strictly bounded; do not increase timeouts to hide provider latency.

- 2026-09-10 execution-17504 diagnostic mistake: attempted to decode n8n `execution_data.data` inside the running n8n container with `require('flatted')`, but that package is not directly resolvable from the container's `/home/node/[eval]` module path. This was read-only and changed no runtime state. Do not retry by installing packages into production; decode the stored Flatted representation with a bounded local parser instead.

- 2026-09-10 fresh V6 storyboard-first stage job `9a90fc06-efdb-4e49-b92d-e9f86d3b1f75` failed in WF02 execution `17504` and is immutable. Gateway calls `17505` and `17506` completed earlier semantic/resolution work, but storyboard call `17507` hit the explicit 45s Nemotron HTTP bound and returned `provider_exhausted=true`; `Validate Storyboard` then failed closed with `free-only storyboard director provider exhausted`. The rewritten centralized `Prepare Planner Failure` still could not recover `job_id` from upstream `$()` references in the task-runner error branch, so the row remained `created/intake`. Do not resume this job. Before another product run, prove a free text model can complete the exact storyboard contract inside a bounded runtime and replace the fragile cross-node failure-context lookup with an explicit carried/persisted correlation that does not depend on `$()` from an error item.

- 2026-09-10 exact storyboard-contract free-model comparison reused the real 5,550-character sky storyboard prompt from failed execution `17504`. Under one bounded parallel 70s diagnostic, `nvidia/nemotron-3.5-lightning:free`, `nex-agi/nex-n2.5-pro:free`, and `nvidia/nemotron-3-super-120b-a12b:free` all timed out before returning; do not retry them for this exact storyboard role. `poolside/laguna-s-2.1:free` completed in 56.78s with `finish_reason=stop`, valid JSON, 5 scenes, and the required storyboard shape. The evidence supports role-specific free routing: keep fast Nemotron for short semantic/text contracts, use Poolside for storyboard generation with a measured bounded timeout, and reduce unnecessary storyboard prompt/output size rather than globally raising timeouts.

- 2026-09-10 21:49 CEST: while validating the new V6 storyboard model route, I repeated a previously known container invocation mistake by running `n8nio/n8n:2.37.10 sh -lc ...` without overriding the n8n entrypoint. n8n interpreted `sh` as an n8n command and returned `Command "sh" not found`. No workflow/runtime/job mutation occurred. Correction: use `docker run --entrypoint sh ...` for the exact-image Node regression run.

- 2026-09-10 21:51 CEST: the first exact-image regression after adding the evidence-based storyboard route failed because `tests/v6_free_only_model_gateway_regression.mjs` still asserted the old single-model 45-second timeout. The source route intentionally uses a bounded 70-second provider timeout because the exact saved storyboard prompt was proven at 56.78 seconds on `poolside/laguna-s-2.1:free`. This is a stale regression expectation, not a product/provider failure. No runtime/job mutation occurred.

- 2026-09-10 21:53 CEST: the retry of the V6 gateway regression failed for the same obsolete 45-second assertion because my scripted text replacement did not match the exact test line, so the stale assertion remained unchanged. No runtime/job mutation occurred. Before retry, inspect the exact line and edit it by content rather than assumed wording.

- 2026-09-10 21:55 CEST: after updating the timeout assertion, the V6 gateway regression exposed another stale single-model expectation: it still required the HTTP node name `Nemotron Free Model`, while the routed gateway intentionally renamed it `Kilo Free Model`. No runtime/job mutation occurred. Update the regression to the route-neutral node name before retry.

- 2026-09-10 21:58 CEST: predeploy active-execution readback used broken shell/SQL quoting, so PostgreSQL parsed `running` as an identifier. The read-only check failed before any runtime mutation. Correction: pass the SQL through an environment variable to psql instead of nested shell quoting.

- 2026-09-10 22:52 CEST: fresh immutable V6 stage job `17970103-3990-44e4-8be6-6296cd57edee` (`Почему небо голубое? / ru / 15`) failed in WF02 execution `17515` after the routed Poolside storyboard call. Gateway execution `17518` completed as a workflow but correctly returned `provider_exhausted=true` because the model produced JSON whose `scenes[1].grounded_fact_ids` exceeded the contract `maxItems=3` (`schema validation failed: $.scenes[1].grounded_fact_ids: array longer than maxItems`). The job must not be resumed/repaired. The same execution also reconfirmed the independent WF02 failure-handler defect: the error branch loses `job_id`, so `Prepare Planner Failure` fails instead of persisting the product failure. Correction must be systemic: canonicalize bounded storyboard evidence references before strict downstream validation and separately remove the failure-handler dependency on unavailable branch ancestry; do not weaken the 1-3 evidence gate and do not retry this job.

- 2026-09-10 22:58 CEST: fresh immutable V6 stage job `0b9c8185-ab46-4ae7-b7d2-97571c95181b` failed in WF02 execution `17520` after the new Poolside storyboard route returned valid JSON. Strict storyboard validation rejected diagram shot `S3A` because one entity used `lane:"center"`; the deterministic diagram contract only supports `left|right|unset`. This is an AI-output canonicalization boundary defect, not a reason to weaken geometry/grounding validation. The job must not be resumed/repaired. Systemic correction: normalize unsupported neutral/center lane to unset before strict entity validation, while still rejecting unknown non-neutral lane values. The already-known WF02 failure-handler `job_id` loss again prevented DB failure-state persistence.

- 2026-09-10 23:02 CEST: while implementing legitimate `center` lane support for comparison diagrams, the edit script changed `diagram-compiler.mjs` and WF02 successfully, then failed when it assumed a non-existent test filename `tests/v6_diagram_compiler_cross_topic.mjs`. No runtime deployment or new job occurred, but the working tree is partially modified. Correction: inspect the actual diagram-regression filename, add the center-lane regression there, then validate the already-written source changes before commit.

- 2026-09-10 23:08 CEST: fresh immutable V6 stage job `e8c35dd1-b742-40dc-b16a-e14a4c45b6f1` progressed through semantic resolution, research, storyboard generation, strict storyboard validation, deterministic media discovery, and feasibility freeze, then failed at the final narration writer in WF02 execution `17527`. Gateway execution `17531` attempted the default `nvidia/nemotron-3-super-120b-a12b:free` route and the Kilo upstream returned HTTP 404 `The resource you are requesting could not be found` / provider error. The same model had succeeded on the earlier short semantic calls in this job, so this is a real long-generation route availability failure, not invalid input. The job must not be resumed/repaired. Systemic correction: route long final-story generation to the already-proven free Poolside long-generation model and keep strict final-story validation downstream; do not use Gemini or a paid fallback. The known WF02 failure-handler still lost `job_id` on the error branch.

- 2026-09-10: Engineering mistake while routing V6 final story: attempted to run Node regression tests with host `node`, but Node is not installed/available on the host PATH. Correction must use the existing n8n/container Node runtime; no product job was created by this failed test command.

- 2026-09-10: Engineering mistake during V6 final-story route deploy verification: workflow import/publish/restart completed, but the final verification SQL had malformed shell quoting around COALESCE and exited non-zero. Correction: verify state with parameter-safe SQL before creating a new job.

- 2026-09-10: Engineering mistake during fresh V6 stage submission after final-story routing fix: attempted external POST to publisher.hodor.com.pl from the VPS host and received HTTP 403. No job was created. Correction: submit from the n8n container to the registered local webhook, as used in prior successful stage jobs.

- 2026-09-10: Engineering diagnostic mistake while decoding execution 17533: invoked `docker exec ... node -` without `-i`, so the decoder script received no stdin and produced no output. Correction: rerun the same read-only decoder with `docker exec -i`.

- 2026-09-10: Engineering diagnostic mistake while decoding execution 17533: copied execution payload into n8n container with permissions unreadable by the node user, causing EACCES. Correction: copy to a readable path/adjust permissions before decode.

- 2026-09-10: Fresh V6 stage job `1b3090c3-083a-49ee-aa41-2010c66ffecb` failed in WF02 execution 17533 at `Freeze Storyboard Feasibility`: `no deterministic executable media for storyboard shot S4A`. The storyboard itself validated; failure occurred during deterministic media feasibility. The existing planner failure handler then also failed to recover job_id. Treat this job as immutable and do not resume/repair it.

- 2026-09-10: Fresh V6 stage job `738b3249-07fd-40ec-bc7f-e7809871ec86` failed in WF02 execution 17541 at `Validate Storyboard`: diagram shot S2A used entity role `flow`, while the high-level diagram contract accepts `input|process|output|layer|subject|result`. Storyboard generation otherwise returned successfully. The existing planner failure handler again failed to recover job_id. Treat this job as immutable; do not resume/repair it.

- 2026-09-10: Engineering deployment mistake before V6 diagram-role-alias stage update: shell-quoted SQL for active execution preflight stripped string quotes around running/waiting and failed before any build/deploy mutation. Correction: use Python parameter-safe docker/psql invocation for the preflight and deployment.

- 2026-09-10: Fresh V6 stage job `29f84b1c-7a74-4077-9c1c-cbcffedc4bd6` failed in WF02 execution `17546`. Short semantic calls succeeded, but the long storyboard call through `poolside/laguna-s-2.1:free` exceeded the bounded 70-second gateway timeout and returned `provider_exhausted=true`; `Validate Storyboard` failed closed. The job is immutable and must not be resumed or repaired. A bounded exact-prompt comparison then showed `cohere/north-mini-code:free` completing the same production storyboard request in 31.52 seconds with HTTP 200, `finish_reason=stop`, valid JSON and 4 scenes, while `kilo-auto/free` completed in 69.56 seconds by resolving back to Poolside. Systemic correction: use the independently proven Cohere free model for the long storyboard/final-story route rather than increasing Poolside timeout. The already-known planner failure-handler correlation defect remains separate.

- 2026-09-10: Engineering regression-run mistake after switching the V6 long route to Cohere: the test batch referenced non-existent file `tests/v6_diagram_comparison_center_regression.mjs` and stopped after the first six relevant tests had already passed. No runtime or product job mutation occurred. Correction: inspect the actual test filename before rerunning; do not assume names from console labels.

- 2026-09-10: Broad V6 regression run reached obsolete test `tests/v6_visual_facts_inline_fingerprint_regression.mjs` after 11 current V6 tests had passed. The stale test dereferenced retired node `Prepare Pre-Claim Review Batches`, which was intentionally removed by the storyboard-first architecture, and crashed with TypeError. No runtime/job mutation occurred. Correction: convert this obsolete regression into a retirement regression that asserts the mandatory visual-review nodes remain absent; do not reintroduce the retired reviewer path.

- 2026-09-10: Engineering monitoring mistake after creating fresh V6 job `4a132abd-0db9-4c73-a557-6eecdd397159`: the read-only status query assumed a non-existent `jobs.error_message` column and failed before polling. No runtime/job mutation occurred. Correction: inspect the actual `jobs` columns first, then monitor only existing fields.

- 2026-09-10: Fresh V6 stage job `4a132abd-0db9-4c73-a557-6eecdd397159` failed in WF02 execution `17554` after the Cohere long route returned successfully (`cohere/north-mini-code:free`, `provider_exhausted=false`, 6,953 chars). Strict storyboard validation rejected diagram `S2A` because the model used entity role `source`; the high-level contract expects `input|process|output|layer|subject|result`. Inspection of the same immutable output also found comparison diagram `S3A` with two comparable `subject` entities but no explicit left/right lanes, which would later violate deterministic comparison layout. Do not resume/repair this job. Systemic correction: canonicalize the common semantic alias `source -> input` and deterministically assign missing comparison lanes to the comparable subject pair (shared/context entities remain center), then validate/compile; do not weaken unknown-role rejection or grounding checks. The previously known planner failure-handler correlation defect is unchanged and is not re-recorded as a new root cause.

- 2026-09-10: Fresh V6 stage job `a1bbfb7c-0251-4f66-9dce-684811cf0549` failed in WF02 execution `17562` after Cohere again returned a complete storyboard (`cohere/north-mini-code:free`, 8,565 chars, provider_exhausted=false). The first strict rejection was `storyboard shot S1A is invalid` because Cohere emitted `must_show`/`must_not_show` as strings instead of arrays. Inspection of the same immutable output exposed the full systemic AI→diagram normalization gap in one pass: `source` role, `arrow`/`bar` shapes, `enters`/`scatters`/`reaches` relation verbs, and a `viewer` relation endpoint without an explicit entity. Do not resume/repair this job. Correction must be one deterministic canonicalization boundary: scalar constraints become one-item arrays; proven semantic aliases map to the finite compiler vocabulary; a model-explicit observer endpoint may be materialized as a neutral result entity when capacity allows; unknown values still fail closed. Do not create one-off topic rules.

- 2026-09-10: Fresh V6 stage job `df45018a-13ec-497e-be8c-808bfbcf2854` failed in WF02 execution `17567`. Cohere completed the long storyboard request with `finish_reason=stop`, but gateway execution `17570` rejected the 5,768-character response as invalid JSON. Exact parse failure: `Expected ',' or ']' after array element in JSON at position 4061`; inspection shows a structural brace mismatch near the end of scene 3, not truncation. The job is immutable. Do not add heuristic brace surgery or retries. Kilo's current gateway API documents both `response_format` and tool calling with JSON-Schema function parameters; investigate a schema-constrained/tool-call transport for the existing free Cohere route so malformed JSON cannot enter WF02.

- 2026-09-11 04:45 CEST: V6 tool-call transport stage deploy imported and published `V6ModelGatewayFreeOnly` and stage WF02 successfully, then the post-restart verification failed because n8n was not yet accepting localhost health checks and the expected `v6-model-gateway` webhook was absent from `webhook_entity` while `v6-stage/jobs` was present. Runtime was already mutated by the successful import/publish before verification stopped. Do not create a product job yet. Inspect bounded n8n container state/logs and webhook registration after the mandatory reads; determine whether this is delayed startup/registration or an activation/runtime error before any retry or further deploy.

- 2026-09-11 04:54 CEST: operator polling script for the first post-tool-call V6 stage run exceeded its 480-second SentinelX wall-clock bound and returned no captured output. This is an operator-observability failure, not evidence that the product job itself failed. Do not submit another job until the existing job/execution state is recovered read-only from PostgreSQL/n8n; use short bounded probes instead of one long blocking poll.

- 2026-09-11 04:57 CEST: read-only decoder for failed WF02 execution `17631` stopped because it tried `docker exec ... chmod /tmp/ex17631.txt` as the n8n container's non-root user; chmod returned `Operation not permitted`. No runtime/job mutation occurred. Correction: avoid in-container chmod as node user; copy the payload with readable host mode and decode it as container root or stream it over stdin with `docker exec -i`.

- 2026-09-11 04:59 CEST: fresh immutable V6 stage job `e082ebd5-ad1d-4565-ba92-bd21f86dee78` failed in WF02 execution `17631` after the new Cohere tool-call transport itself succeeded (`finish_reason=tool_calls`, structured output received). Strict storyboard validation rejected diagram shot `S3A`: the tool output used unsupported entity role `center` for `direct_path`, and relations also referenced `observer` although no `observer` entity was declared. This proves transport-level JSON validity is fixed but the function schema is still too weak around `diagram_spec`. Do not resume/repair this job. Systemic correction: put the complete diagram entity/relation enums into the function JSON Schema and explicitly require relation endpoints to be declared entity ids in the director contract; keep downstream fail-closed referential validation. The known planner failure branch again failed to persist the job failure because it lost `job_id`.

- 2026-09-11 05:01 CEST: fresh immutable V6 stage job `571e00f6-d1d8-4019-b96d-9abf53aad929` failed in WF02 execution `17636` at the storyboard gateway boundary. The request correctly sent Cohere `cohere/north-mini-code:free` with `tools` and explicit function `tool_choice`, but Kilo returned `finish_reason:stop`, no `tool_calls`, and a 11,501-character content body that parsed as valid JSON with 5 scenes. The gateway rejected it as `required structured tool call missing`. Do not resume/repair this job. Systemic correction: keep tool-call-first transport, but accept ordinary content only when it is valid JSON and passes the exact same response schema; malformed content must still fail closed. This is transport compatibility, not a retry or schema weakening. The known WF02 failure handler again failed to recover `job_id`.

- 2026-09-11 05:04 CEST: exact read-only replay of execution `17639` through the patched tool-call/content-fallback normalizer did not pass because the older Cohere content JSON had more than 3 `grounded_fact_ids` in one scene. The fallback correctly parsed JSON but gateway-level strict schema validation rejected it before WF02's existing AI→storyboard canonicalization boundary could normalize bounded cardinalities. No runtime/job mutation occurred. Systemic correction: separate storyboard transport parsing from final-story strict validation. Storyboard route may accept syntactically valid structured output and must defer canonical contract enforcement to WF02 `Validate Storyboard`; final-story route must retain strict response-schema validation.
