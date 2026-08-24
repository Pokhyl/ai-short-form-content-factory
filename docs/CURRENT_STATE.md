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
- on stage failure must record `jobs.status = failed`, keep `jobs.current_stage = voiceover`, store `jobs.last_error`, and not start the next stage

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
- first full saved export SHA-256 `15c8b7d6bb2c6e5833f1d91b1b8e04321638d53b048b26bcaf611ec6b8f12faa`
- workflow is inactive
- first export had exactly 12 nodes
- first export was copied to `n8n/workflows/WF03-voiceover-generation.json` on VPS and remains uncommitted/untracked until final verification

Export-proven topology before failure handling:

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

## Exact parameter review

Full parameter dump of all 12 nodes was reviewed line-for-line.

Verified:

- `Receive Job ID` is `executeWorkflowTrigger` with declared `job_id` input.
- `Normalize Job ID` matches intended UUID normalization/validation.
- `Load Voiceover Context` matches intended parameterized SQL.
- `Require Eligible Voiceover Job` matches intended resumable `processing/script` or `processing/voiceover` validation and scene/audio consistency checks.
- `Begin Voiceover Stage` matches intended `script -> voiceover` transition/resume SQL.
- `Prepare Voiceover Items` matches the locked four-language voice map and emits pending-scene items.
- `Generate Voiceover` is saved as `POST https://texttospeech.googleapis.com/v1/text:synthesize`, uses Google OAuth2, `x-goog-user-project: n8n-drive-voiceover`, dynamic narration, dynamic language mapping, dynamic voice name, and MP3.
- `Store Audio` body uses the linked `Prepare Voiceover Items` `job_id`/`scene_number` and Google `audioContent`.
- `Persist Audio Result` writes the exact scene by linked `scene_id + job_id` and stores media-worker `audio_path` plus measured `duration_seconds` only when prior audio state is empty.
- `Require Persisted Audio Batch`, `Verify Voiceover Completion`, and `Require Voiceover Completion` match the intended code/SQL.

A mismatch was found in the first export: `Store Audio.parameters.method` was omitted, which would default to GET. The node was corrected in n8n to explicit POST.

Runtime/export verification after the correction returned exactly:

```text
STORE_AUDIO_METHOD: POST
STORE_AUDIO_METHOD_OK: YES
```

Therefore `Store Audio` method is now verified as `POST` in the saved production workflow.

No real TTS request has been accepted yet.

## Reliability note for current n8n line

Failure handling is not yet implemented. Do not run real TTS before it is added and re-exported.

There is a current upstream report against n8n 2.33.5 where HTTP Request with `On Error = Continue (using error output)` can route a failed request through the normal output as well. This behavior is not proven on this runtime's 2.33.3, but critical M5 failure handling should not depend blindly on that mode without accounting for the risk.

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

1. Add the smallest stage-specific failure path for failures after `Begin Voiceover Stage`.
2. The failure path must resolve the current `job_id` from the already-validated upstream job, persist `status = failed`, `current_stage = voiceover`, and a non-empty `last_error`, then terminate the execution as failed.
3. Do not add generic retry/dispatcher/error infrastructure.
4. Because of the current HTTP Request error-output regression reported on n8n 2.33.5, choose a design that does not allow a failed HTTP request to continue into persistence as if it succeeded.
5. Re-export and verify the final WF03 after failure handling.
6. Only then begin the first real TTS acceptance run.
7. Do not wire WF02->WF03 and do not start M6.

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
