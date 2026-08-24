# Current Project State

Last updated: 2026-08-24

This file is the first checkpoint to read before continuing work on this repository. If chat history conflicts with this file, `docs/ARCHITECTURE.md`, or `docs/ROADMAP.md`, the repository wins.

## Mandatory assistant protocol

For every technical reply or action about this project, fetch the current `docs/CURRENT_STATE.md` from the active feature branch first. Fetch `docs/ARCHITECTURE.md` when architecture is involved and `docs/ROADMAP.md` when milestone scope, acceptance, or progression is involved. Repository state overrides chat memory. Unknown facts must not be guessed. After every completed implementation or runtime/setup step, update this file before moving on. Export production n8n workflows into the repository.

## Project

AI Short-Form Content Factory

- repository: `Pokhyl/ai-short-form-content-factory`
- branch: `feat/m5-voiceover`
- milestone: M5 — Voiceover (`in progress`)

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

Production `WF01 — Create Content Job`:

- workflow ID `Xy94qe35OigtMxkR`
- verified export blob `a71161b373bb56bd0aba8abeba410e17011dcb5c`
- verified hand-off target `TJfA4ZYUEKSTad6k` (`WF02`)
- verified input `job_id = {{ $json.job_id }}`
- verified `waitForSubWorkflow = false`
- verified `Insert Job` branches to `Return Created Job` and `Start Script Planning`
- remote workflow commit `353149dbe5ff7e511ad5dfe7683b00755f765727`
- final WF01->WF02 end-to-end runtime hand-off has not yet been acceptance-tested

Production `WF02 — Plan Script and Scenes`:

- workflow ID `TJfA4ZYUEKSTad6k`
- M4 accepted topology: 8 nodes ending in `Persist Scene Plan`
- accepted export SHA-256 `be35214a12a4ef933145e629a3cf070376378a1b1a9ba9cd3256b8fbd5f0fdc1`
- accepted export commit `8a545d3f2fc1942b3f95aa9c6919b0cfc2995ac2`
- accepted quality job `6b08098c-e5c7-45bd-babb-036705b563e1`, Polish, 30 seconds, exactly 8 scenes, manual quality PASS
- do not rerun prior M4 acceptance jobs
- WF02->WF03 is not wired yet

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

`WF03 — Voiceover Generation` is a separate n8n stage. It:

- receives only `job_id`
- reloads persisted job/scenes from PostgreSQL
- validates eligibility
- changes `jobs.current_stage` to `voiceover` only when M5 begins
- generates one audio file per scene using the exact voice for `jobs.language_code`
- stores `scenes.audio_path`
- stores measured real `scenes.duration_seconds`
- keeps PostgreSQL writes in n8n; media-worker never writes product state
- starts Visual Sourcing only after all required scene audio is ready
- on stage failure must record `jobs.status = failed`, `jobs.current_stage = voiceover`, and `jobs.last_error`, and must not start the next stage

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
- voice comes from the locked map above
- no hardcoded topic, test narration, Polish-only setting, or concrete acceptance job in permanent production nodes

## Media-worker audio boundary

Commit `1ac60492baa19e113baf9d7cdb315e7641988ff0` added `POST /audio/store` to existing `media-worker`.

Request:

```json
{
  "job_id": "<uuid>",
  "scene_number": 1,
  "audio_base64": "<Google TTS MP3 base64>"
}
```

Behavior:

- deterministic path `jobs/<job_id>/voiceover/scene-XX.mp3`
- ffprobe validation before final replace
- returns `audio_path`, measured `duration_seconds`, and `bytes`
- synthetic runtime acceptance already passed; do not repeat before real TTS

## Google Cloud TTS authentication

Use existing project `n8n-drive-voiceover` and dedicated OAuth client `n8n-tts-oauth`.

Verified:

- Text-to-Speech API enabled
- active free-trial credit
- current callback `https://publisher.hodor.com.pl/rest/oauth2-credential/callback`
- n8n credential type `Google OAuth2 API`
- scope `https://www.googleapis.com/auth/cloud-platform`
- Google authorization completed in current runtime
- first real authenticated TTS request still pending acceptance

Do not create replacement auth objects. Never expose OAuth secrets.

## WF03 production export checkpoint

Production workflow:

- name `WF03 — Voiceover Generation`
- workflow ID `UHxvCZNqaLb1RKMM`
- saved production export SHA-256 `15c8b7d6bb2c6e5833f1d91b1b8e04321638d53b048b26bcaf611ec6b8f12faa`
- export reports `ACTIVE: False`
- export reports exactly 12 nodes
- VPS was synchronized by fast-forward to remote commit `2a2b525`
- production export is copied to `n8n/workflows/WF03-voiceover-generation.json`
- workflow file is still untracked on VPS and has not been committed

Export-proven topology:

```text
Receive Job ID
-> Normalize Job ID
-> Load Voiceover Context
-> Require Eligible Voiceover Job
-> Begin Voiceover Stage
-> Prepare Voiceover Items
-> Generate Voiceover
-> Store Audio
-> Persist Audio Result
-> Require Persisted Audio Batch
-> Verify Voiceover Completion
-> Require Voiceover Completion
```

The first export validation returned `CRITICAL_EXPORT_CHECKS: OK` and `EXPORT_READY_FOR_REVIEW: YES` for workflow ID, all 12 nodes, Google TTS endpoint/header, media-worker endpoint presence, MP3, all four locked voices, dynamic narration/voice, `audioContent`, `audio_path`, `duration_seconds`, and `all_audio_ready`.

## Exact WF03 parameter review

A full parameter dump of all 12 saved production nodes was reviewed line-for-line on 2026-08-24.

Verified exactly from the export:

- `Receive Job ID` uses `executeWorkflowTrigger` with one declared `job_id` input, matching the accepted WF02 trigger shape.
- `Normalize Job ID` matches the intended UUID normalization/validation code.
- `Load Voiceover Context` matches the intended parameterized SQL and `{{ [ $json.job_id ] }}` query parameter.
- `Require Eligible Voiceover Job` matches the intended resumable `processing/script` or `processing/voiceover` validation and scene/audio consistency checks.
- `Begin Voiceover Stage` matches the intended conditional `script -> voiceover` transition/resume SQL and returns `ready_to_run` / `started_now`.
- `Prepare Voiceover Items` matches the intended four-language voice map and pending-scene item shape.
- `Generate Voiceover` is correctly saved as `POST https://texttospeech.googleapis.com/v1/text:synthesize`, uses `googleOAuth2Api`, `x-goog-user-project: n8n-drive-voiceover`, dynamic narration, dynamic language mapping, dynamic voice name, and MP3.
- `Persist Audio Result`, `Require Persisted Audio Batch`, `Verify Voiceover Completion`, and `Require Voiceover Completion` match the intended SQL/code.
- all node execution flags are currently empty; no M5 failure handling has been added yet.

Critical mismatch found in the saved export:

- `Store Audio` does **not** contain a `method` parameter.
- n8n HTTP Request v4.x defaults `method` to `GET` when omitted.
- therefore the currently saved `Store Audio` node would call `GET http://media-worker:3001/audio/store`, while media-worker accepts only `POST /audio/store`.
- this must be fixed before any real TTS execution or failure-path work proceeds.

No real TTS request has been accepted yet.

## M5 acceptance

Per `docs/ROADMAP.md`:

- every scene has a playable audio file
- actual audio duration is measured
- voice quality is manually accepted in all supported languages used for testing

Do not start M6 before real M5 acceptance.

## Deferred M9 Studio status endpoint

During M9 add one separate read-only n8n HTTP status workflow/webhook accepting `job_id`, validating it, reading PostgreSQL, and returning at minimum `job_id`, `status`, `current_stage`, `last_error`. Do not add public progress webhooks to WF02/WF03/WF04. Browser never connects directly to PostgreSQL. Studio may poll this single endpoint.

## Exact next action

Continue M5 in production `WF03 — Voiceover Generation` (`UHxvCZNqaLb1RKMM`).

1. Fix `Store Audio` so its saved HTTP method is explicitly `POST`.
2. Do not change any other `Store Audio` parameter.
3. Re-export WF03 and verify that the exported `Store Audio.parameters.method` is exactly `POST` before doing anything else.
4. Then add the smallest stage-specific failure path required by architecture so failures after entering `voiceover` record `jobs.status = failed`, keep `jobs.current_stage = voiceover`, store `jobs.last_error`, and do not start a later stage.
5. Do not run real TTS yet, do not wire WF02->WF03, and do not start M6.

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
