# Current Project State

Last updated: 2026-08-24

This file is the first checkpoint to read before continuing work on this repository. If chat history conflicts with this file, `docs/ARCHITECTURE.md`, or `docs/ROADMAP.md`, the repository wins.

## Mandatory assistant protocol

For every technical reply or action about this project, fetch the current `docs/CURRENT_STATE.md` from the active feature branch first. Fetch `docs/ARCHITECTURE.md` when architecture is involved and `docs/ROADMAP.md` when milestone scope, acceptance, or progression is involved. Repository state overrides chat memory. Unknown facts must not be guessed. After every completed implementation or runtime/setup step, update this file before moving on. Export production n8n workflows into the repository.

## Project

AI Short-Form Content Factory

Repository: `Pokhyl/ai-short-form-content-factory`

Current branch: `feat/m5-voiceover`

Current milestone: M5 — Voiceover (`in progress`).

Target flow:

```text
Topic
  -> Script + scene plan
  -> Voiceover
  -> Visual sourcing
  -> Render
  -> Human review
  -> Buffer draft
```

## Runtime

- VPS: `root@37.27.87.6`
- project path: `/opt/ai-short-form-content-factory`
- services exactly: `n8n`, `postgres`, `media-worker`
- n8n: `https://publisher.hodor.com.pl/`
- future Studio: `https://studio.hodor.com.pl/`
- application state: PostgreSQL `public`
- n8n internal schema: `n8n`; never modify it manually

## Completed upstream checkpoints

M4 PR #5 merged into `main` on 2026-08-23, merge commit `7d25bac1c4d1a90b2b29183d9ec3ca280d1acfc4`.

Production `WF02 — Plan Script and Scenes`:

- workflow ID `TJfA4ZYUEKSTad6k`
- accepted topology: 8 nodes ending in `Persist Scene Plan`
- accepted export SHA-256 `be35214a12a4ef933145e629a3cf070376378a1b1a9ba9cd3256b8fbd5f0fdc1`
- accepted export commit `8a545d3f2fc1942b3f95aa9c6919b0cfc2995ac2`
- accepted quality job `6b08098c-e5c7-45bd-babb-036705b563e1`, Polish, 30 seconds, exactly 8 persisted scenes, manual quality PASS
- do not rerun prior M4 acceptance jobs

Production `WF01 — Create Content Job`:

- workflow ID `Xy94qe35OigtMxkR`
- verified export blob `a71161b373bb56bd0aba8abeba410e17011dcb5c`
- verified target `TJfA4ZYUEKSTad6k` (`WF02`)
- verified input `job_id = {{ $json.job_id }}`
- verified `waitForSubWorkflow = false`
- verified `Insert Job` branches to both `Return Created Job` and `Start Script Planning`
- remote workflow commit `353149dbe5ff7e511ad5dfe7683b00755f765727`
- WF01 must return HTTP 201 without waiting for downstream completion

## M5 exact voice configuration

Provider: Google Cloud Text-to-Speech.

| Language | Exact voice preset |
| --- | --- |
| `en` | `en-US-Chirp3-HD-Algenib` |
| `pl` | `pl-PL-Chirp3-HD-Enceladus` |
| `ru` | `ru-RU-Wavenet-D` |
| `uk` | `uk-UA-Chirp3-HD-Enceladus` |

Do not substitute guessed voices.

## M5 architecture contract

`WF03 — Voiceover Generation` is a separate n8n stage workflow. It:

- receives only `job_id`
- reloads persisted job/scenes from PostgreSQL
- validates stage eligibility
- changes `jobs.current_stage` to `voiceover` only when M5 actually begins
- generates one voiceover file per scene using the exact configured voice for the job language
- stores `scenes.audio_path`
- measures real audio duration and stores it in `scenes.duration_seconds`
- persists product state through n8n, not directly from media-worker
- starts Visual Sourcing only after every required scene audio is ready
- on failure records `jobs.status = failed`, `jobs.current_stage = voiceover`, and `jobs.last_error`, and does not start the next stage

Internal stage hand-off payload remains only:

```json
{
  "job_id": "<uuid>"
}
```

Internal automatic hand-offs use native n8n sub-workflows, not public webhooks. Caller must not wait for the complete downstream pipeline.

## Production generality invariant

- narration comes from persisted `scenes.narration`
- language comes from persisted `jobs.language_code`
- voice comes from the locked four-language map above
- no hardcoded topic, test narration, Polish-only setting, or concrete acceptance job in permanent production nodes

## Media-worker audio boundary

Commit `1ac60492baa19e113baf9d7cdb315e7641988ff0` added `POST /audio/store` to the existing `media-worker`.

Request:

```json
{
  "job_id": "<uuid>",
  "scene_number": 1,
  "audio_base64": "<Google TTS MP3 base64>"
}
```

Behavior:

- deterministic media-relative path `jobs/<job_id>/voiceover/scene-XX.mp3`
- ffprobe validation before final replace
- returns `audio_path`, measured `duration_seconds`, and `bytes`
- media-worker never writes PostgreSQL

Synthetic acceptance already passed; do not repeat it before real TTS.

## Google Cloud TTS authentication

Use existing project `n8n-drive-voiceover` and existing dedicated OAuth client `n8n-tts-oauth`.

Verified:

- Text-to-Speech API enabled
- active free-trial credit
- current callback `https://publisher.hodor.com.pl/rest/oauth2-credential/callback`
- n8n credential type `Google OAuth2 API`
- scope `https://www.googleapis.com/auth/cloud-platform`
- Google authorization completed in current runtime
- first real authenticated TTS request still pending acceptance

Do not create replacement auth objects and never expose OAuth secrets.

## WF03 implementation checkpoint

Production workflow:

- name `WF03 — Voiceover Generation`
- workflow ID `UHxvCZNqaLb1RKMM`

Directly verified from screenshots:

- old Manual Trigger removed; `Receive Job ID` present
- `Normalize Job ID` exists with accepted UUID normalization/validation code and Mode `Run Once for All Items`
- `Load Voiceover Context` exists, uses `Application PostgreSQL` / `Execute Query`, `$1::uuid`, and query parameter `{{ [ $json.job_id ] }}`
- visible SQL loads job fields and aggregated scenes including `scene_id`, `scene_number`, `narration`, `audio_path`, `duration_seconds`, and scene `status`
- `Generate Voiceover` is HTTP Request with `POST`, `Google OAuth2 API`, credential display name `Google account`, header `x-goog-user-project: n8n-drive-voiceover`, `Send Body = ON`, `Body Content Type = JSON`, `Specify Body = Using JSON`
- visible lower JSON includes dynamic `$json.voice_name` and `audioEncoding = 'MP3'`
- complete TTS JSON has not yet been independently export-verified
- no real Cloud TTS request has been accepted yet

User-reported implementation steps, not yet independently verified by screenshot/export:

1. `Require Eligible Voiceover Job` exists after `Load Voiceover Context`. It was updated to allow `processing/script` or resumable `processing/voiceover`, validates exact scene count/sequence/narration, and requires consistent audio state per scene.
2. `Begin Voiceover Stage` exists after eligibility validation. It was updated to atomically change `processing/script` to `voiceover` or accept an already `processing/voiceover` resumable job, returning `ready_to_run` and `started_now`.
3. `Prepare Voiceover Items` exists after `Begin Voiceover Stage`. It was updated to require `ready_to_run`, select the exact locked voice, skip scenes whose `audio_path` and `duration_seconds` are already complete, and emit one item per pending scene with `job_id`, `scene_id`, `scene_number`, `language_code`, `voice_name`, and `narration`.
4. User reports `Prepare Voiceover Items -> Generate Voiceover` is connected.
5. `Store Audio` was added after `Generate Voiceover` as HTTP Request `POST http://media-worker:3001/audio/store`, no authentication, JSON body using the linked scene `job_id`, `scene_number`, and Google response `$json.audioContent` as `audio_base64`.
6. User reports `Generate Voiceover -> Store Audio` is connected.
7. `Persist Audio Result` was added after `Store Audio` as `Application PostgreSQL` / `Execute Query`. The supplied SQL updates the exact scene by `scene_id + job_id`, writes media-worker `audio_path` and measured `duration_seconds`, requires an empty prior audio state and positive duration, and returns `persisted` plus the stored values. User reports this step is configured and connected.

Do not treat the user-reported nodes/connections as independently verified until workflow export or screenshot proves them.

## Deferred M9 Studio status endpoint

Do not implement during M5, but do not forget it. During M9 add one separate read-only n8n HTTP status workflow/webhook accepting `job_id`, validating it, reading PostgreSQL, and returning at minimum `job_id`, `status`, `current_stage`, and `last_error`. Do not add public progress webhooks to WF02/WF03/WF04. Browser never connects directly to PostgreSQL. Studio may poll this single endpoint.

Recorded also in `docs/ROADMAP.md` M9 by commit `ec0eb9a6167820c6d3c895ec9f8a606773a2f470`.

## Exact next action

Continue M5 in production `WF03 — Voiceover Generation` (`UHxvCZNqaLb1RKMM`).

1. Add a Code node after `Persist Audio Result`, Mode `Run Once for All Items`, that requires every persistence result in the current pending-scene batch to have `persisted === true`, requires a single shared `job_id`, and emits exactly one `{ job_id }` item.
2. Add one PostgreSQL completion-verification node after that aggregation. It must verify from durable PostgreSQL state that the job is still `processing/voiceover`, that the exact duration-specific scene count exists, and that every scene has non-empty `audio_path` plus positive `duration_seconds`.
3. Do not advance `current_stage` to `visuals` and do not wire a Visual Sourcing workflow yet; M6 is not implemented.
4. Do not execute real TTS until the full WF03 structure is in place and exported/verified.
5. Do not wire WF02 to WF03 and do not run the end-to-end chain yet.

Before the next VPS Git change, synchronize the VPS branch because remote documentation commits have advanced the feature branch.

## Do not do

- do not substitute voice presets
- do not hardcode topic/narration/language-specific test data
- do not reuse Gemini credential for TTS
- do not create new auth objects
- do not expose secrets
- do not start M6 before M5 real voice acceptance
- do not modify the `n8n` PostgreSQL schema manually
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure
- do not add extra services
- do not put secrets in GitHub
