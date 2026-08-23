# Current Project State

Last updated: 2026-08-23

This file is the first checkpoint to read before continuing work on this repository. If chat history conflicts with this file, `docs/ARCHITECTURE.md`, or `docs/ROADMAP.md`, the repository wins.

## Mandatory assistant protocol

For every technical reply or action about this project, fetch the current `docs/CURRENT_STATE.md` from the active feature branch first. Fetch `docs/ARCHITECTURE.md` when architecture is involved and `docs/ROADMAP.md` when milestone scope, acceptance, or progression is involved. Repository state overrides chat memory. Unknown facts must not be guessed. After every completed implementation or runtime/setup step, update this file before moving on. Export production n8n workflows into the repository.

## Project

AI Short-Form Content Factory

Repository: `Pokhyl/ai-short-form-content-factory`

Current branch: `feat/m5-voiceover`

Current milestone: M5 — Voiceover (`in progress`).

Product goal:

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

VPS: `root@37.27.87.6`

Project path: `/opt/ai-short-form-content-factory`

Services exactly: `n8n`, `postgres`, `media-worker`.

Public n8n URL: `https://publisher.hodor.com.pl/`

Future Studio URL: `https://studio.hodor.com.pl/`

The `n8n` PostgreSQL schema belongs to n8n and must not be modified manually. Application state lives in `public`.

## Completed upstream checkpoints

M4 PR #5 merged into `main` on 2026-08-23, merge commit `7d25bac1c4d1a90b2b29183d9ec3ca280d1acfc4`.

Production `WF02 — Plan Script and Scenes`:

- workflow ID: `TJfA4ZYUEKSTad6k`;
- accepted topology: 8 nodes ending in `Persist Scene Plan`;
- accepted export SHA-256: `be35214a12a4ef933145e629a3cf070376378a1b1a9ba9cd3256b8fbd5f0fdc1`;
- accepted export commit: `8a545d3f2fc1942b3f95aa9c6919b0cfc2995ac2`;
- accepted quality job: `6b08098c-e5c7-45bd-babb-036705b563e1`, Polish, 30 seconds, exactly 8 persisted scenes, manual quality PASS.

Do not rerun prior M4 acceptance jobs.

Production `WF01 — Create Content Job`:

- workflow ID: `Xy94qe35OigtMxkR`;
- verified export blob SHA: `a71161b373bb56bd0aba8abeba410e17011dcb5c`;
- verified target: `TJfA4ZYUEKSTad6k` (`WF02`);
- verified input mapping: `job_id = {{ $json.job_id }}`;
- verified `waitForSubWorkflow = false`;
- verified `Insert Job` branches to both `Return Created Job` and `Start Script Planning`;
- remote workflow commit: `353149dbe5ff7e511ad5dfe7683b00755f765727`.

WF01 must return HTTP 201 without waiting for the downstream pipeline.

## Exact M5 voice configuration

Provider: Google Cloud Text-to-Speech.

Use these exact product-selected voices:

| Language | Exact voice preset |
| --- | --- |
| `en` | `en-US-Chirp3-HD-Algenib` |
| `pl` | `pl-PL-Chirp3-HD-Enceladus` |
| `ru` | `ru-RU-Wavenet-D` |
| `uk` | `uk-UA-Chirp3-HD-Enceladus` |

Do not substitute guessed voices.

## M5 architecture contract

`WF03 — Voiceover Generation` is a separate n8n stage workflow.

It:

- receives only `job_id`;
- reloads persisted job/scenes from PostgreSQL;
- validates stage eligibility;
- changes `jobs.current_stage` to `voiceover` only when M5 actually begins;
- generates one voiceover file per scene using the exact configured voice for the job language;
- stores `scenes.audio_path`;
- measures real audio duration and stores it in `scenes.duration_seconds`;
- persists product state through n8n, not directly from media-worker;
- starts Visual Sourcing only after every required scene audio is ready;
- on failure records `jobs.status = failed`, `jobs.current_stage = voiceover`, and `jobs.last_error`, and does not start the next stage.

Stage hand-off payload remains only:

```json
{
  "job_id": "<uuid>"
}
```

Internal automatic stage hand-offs use native n8n sub-workflows, not public webhooks. The caller must not wait for the complete downstream pipeline.

## Production generality invariant

WF03 is reusable production logic, not a workflow for one topic, one phrase, one language, or one job.

- narration comes from persisted `scenes.narration`;
- language comes from persisted `jobs.language_code`;
- voice is selected deterministically from the exact four-language map above;
- no production TTS node may hardcode a topic, narration phrase, or Polish-only settings;
- concrete values may be used only for acceptance/testing and must not remain as permanent production configuration.

## Accepted media-worker audio boundary

Commit `1ac60492baa19e113baf9d7cdb315e7641988ff0` added internal `POST /audio/store` to existing `media-worker`.

Request:

```json
{
  "job_id": "<uuid>",
  "scene_number": 1,
  "audio_base64": "<Google TTS MP3 base64>"
}
```

Behavior:

- stores deterministic media-relative path `jobs/<job_id>/voiceover/scene-XX.mp3`;
- validates the candidate with ffprobe before replacing the final path;
- returns `audio_path`, measured `duration_seconds`, and byte size;
- never writes PostgreSQL directly.

Synthetic runtime acceptance already passed and must not be repeated before real TTS.

## Google Cloud TTS authentication

Use existing project `n8n-drive-voiceover`.

Verified:

- Cloud Text-to-Speech API is enabled;
- project has active free-trial credit;
- dedicated OAuth client: `n8n-tts-oauth`;
- current callback: `https://publisher.hodor.com.pl/rest/oauth2-credential/callback`;
- current n8n credential type: `Google OAuth2 API`;
- scope: `https://www.googleapis.com/auth/cloud-platform`;
- user completed Google authorization in current n8n runtime;
- first real authenticated Cloud TTS request is still pending acceptance.

Do not create replacement auth objects and never expose OAuth secrets.

## Verified M5 production boundary

Accepted M4 job `6b08098c-e5c7-45bd-babb-036705b563e1` was `pl`, 30 seconds, `processing/script`, with exactly 8 planned scenes and non-empty narration. At the M5 starting checkpoint all its `audio_path` / `duration_seconds` values were NULL.

Media-worker health and writable persistent `/data` media volume were verified. n8n does not mount that media volume directly.

## Deferred M9 Studio status endpoint

Do not implement during M5, but do not forget it.

During M9 add one separate read-only n8n HTTP status workflow/webhook that accepts `job_id`, validates it, reads PostgreSQL, and returns at minimum `job_id`, `status`, `current_stage`, and `last_error`. Do not add public progress webhooks to WF02/WF03/WF04. Browser must never connect directly to PostgreSQL. Studio may poll the single status endpoint.

This is also recorded in `docs/ROADMAP.md` M9 by commit `ec0eb9a6167820c6d3c895ec9f8a606773a2f470`.

## WF03 implementation checkpoint

Production workflow:

- name: `WF03 — Voiceover Generation`;
- exact workflow ID: `UHxvCZNqaLb1RKMM`.

Directly verified from screenshots:

- old Manual Trigger is gone and `Receive Job ID` is present;
- `Normalize Job ID` exists with the accepted WF02 UUID normalization/validation code;
- `Normalize Job ID` Mode is `Run Once for All Items`;
- `Load Voiceover Context` exists after it;
- `Load Voiceover Context` uses `Application PostgreSQL`, `Execute Query`, `$1::uuid`, and expression query parameter `{{ [ $json.job_id ] }}`;
- visible SQL loads job fields and aggregated scene data including `scene_id`, `scene_number`, `narration`, `audio_path`, `duration_seconds`, and scene `status`;
- complete SQL has not yet been independently verified line-for-line from a single screenshot;
- `Generate Voiceover` is a real HTTP Request node using `POST`, `Google OAuth2 API`, credential display name `Google account`, header `x-goog-user-project: n8n-drive-voiceover`, and `Send Body = ON`;
- latest `Generate Voiceover` screenshot directly verifies `Body Content Type = JSON` and `Specify Body = Using JSON`;
- the visible lower part of the JSON expression includes dynamic `name: $json.voice_name` and `audioConfig.audioEncoding = 'MP3'`;
- the top of the JSON expression is outside the visible editor area, so `input.text`, language mapping, and the complete body are not yet independently verified line-for-line from a screenshot;
- the latest screenshot explicitly shows `No input connected` on the left side of `Generate Voiceover`; therefore `Prepare Voiceover Items -> Generate Voiceover` is not yet connected at this checkpoint;
- no real Cloud TTS request has been accepted yet.

User-reported implementation steps on 2026-08-23, not yet independently verified by screenshot/export:

1. `Require Eligible Voiceover Job` was added after `Load Voiceover Context`, Mode `Run Once for All Items`, using supplied validation code that checks job existence, `processing/script`, supported language, exact duration-specific scene count, sequential scenes, non-empty narration, and no existing audio results.
2. `Begin Voiceover Stage` was added after eligibility validation as `Application PostgreSQL` / `Execute Query`, using supplied SQL that atomically changes only `processing/script` jobs to `current_stage = voiceover`, keeps `status = processing`, and returns `transitioned`, `status`, and `current_stage`.
3. `Prepare Voiceover Items` was added after `Begin Voiceover Stage`, Mode `Run Once for All Items`, using supplied code that requires `transitioned === true`, checks job identity/state, selects the exact locked voice from `jobs.language_code`, and emits one item per scene with only `job_id`, `scene_id`, `scene_number`, `language_code`, `voice_name`, and `narration`.

Do not treat these three user-reported nodes as visually/export-verified until a screenshot or workflow export confirms them.

## Smallest M5 implementation boundary

No new service is required.

- n8n owns Google Cloud TTS requests and PostgreSQL reads/writes;
- media-worker owns local audio persistence plus ffprobe duration validation;
- `scenes.audio_path` stores a media-relative path under `/data`;
- no generic retry/idempotency framework is added.

## Exact next action

Continue M5 in production `WF03 — Voiceover Generation` (`UHxvCZNqaLb1RKMM`).

1. Connect `Prepare Voiceover Items` directly to the existing `Generate Voiceover` node. Do not execute it yet.
2. After connection, visually verify the full dynamic JSON body, especially `input.text = $json.narration` and dynamic language mapping, before the first real TTS request.
3. Then add the existing media-worker `/audio/store` call and persist returned `audio_path` plus measured `duration_seconds` through n8n.
4. Do not wire WF02 to WF03 and do not run the end-to-end chain yet.

Before the next VPS Git change, synchronize the VPS branch because the remote feature branch has advanced with documentation commits.

## Do not do

- do not substitute voice presets;
- do not hardcode topic, narration, or Polish-only settings;
- do not reuse Gemini credential for TTS;
- do not create new auth objects;
- do not expose secrets;
- do not start M6 before M5 real voice acceptance;
- do not modify the `n8n` PostgreSQL schema manually;
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure;
- do not add extra services;
- do not put secrets in GitHub.
