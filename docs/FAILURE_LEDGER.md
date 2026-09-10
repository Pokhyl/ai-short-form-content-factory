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
