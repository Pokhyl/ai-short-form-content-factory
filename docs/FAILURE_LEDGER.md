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
