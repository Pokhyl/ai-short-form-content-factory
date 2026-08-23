# Current Project State

Last updated: 2026-08-23

This file is the first checkpoint to read before continuing work on this repository. If chat history conflicts with this file, `docs/ARCHITECTURE.md`, or `docs/ROADMAP.md`, the repository wins.

## Mandatory assistant protocol

For every technical reply or action about this project, fetch the current `docs/CURRENT_STATE.md` from the active feature branch first. Fetch `docs/ARCHITECTURE.md` when architecture is involved and `docs/ROADMAP.md` when milestone scope, acceptance, or progression is involved. Repository state overrides chat memory. Unknown facts must not be guessed. After every completed implementation or runtime step, update this file before moving on. Export production n8n workflows into the repository.

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

## M4 completed checkpoint

M4 PR #5 was merged into `main` on 2026-08-23.

Merge commit: `7d25bac1c4d1a90b2b29183d9ec3ca280d1acfc4`.

Production WF02:

- workflow ID: `TJfA4ZYUEKSTad6k`;
- name: `WF02 — Plan Script and Scenes`;
- final accepted M4 topology: 8 nodes ending in `Persist Scene Plan`;
- final accepted export SHA-256: `be35214a12a4ef933145e629a3cf070376378a1b1a9ba9cd3256b8fbd5f0fdc1`;
- final accepted export commit: `8a545d3f2fc1942b3f95aa9c6919b0cfc2995ac2`;
- accepted quality job: `6b08098c-e5c7-45bd-babb-036705b563e1` with exactly 8 persisted scenes and manual quality PASS.

Do not rerun prior M4 acceptance jobs.

## Runtime

VPS: `root@37.27.87.6`

Project path: `/opt/ai-short-form-content-factory`

Services: `n8n`, `postgres`, `media-worker`.

Public n8n URL: `https://publisher.hodor.com.pl/`

The `n8n` PostgreSQL schema belongs to n8n and must not be modified manually.

## Exact recovered M5 voice configuration

Provider: Google Cloud Text-to-Speech.

These exact presets are product decisions and must be reused exactly:

| Language | Exact voice preset |
| --- | --- |
| English (`en`) | `en-US-Chirp3-HD-Algenib` |
| Polish (`pl`) | `pl-PL-Chirp3-HD-Enceladus` |
| Russian (`ru`) | `ru-RU-Wavenet-D` |
| Ukrainian (`uk`) | `uk-UA-Chirp3-HD-Enceladus` |

Do not substitute guessed voices.

## M5 architecture contract

Voiceover Generation is a separate n8n stage workflow.

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

Stage hand-off remains only:

```json
{
  "job_id": "<uuid>"
}
```

## Production generality invariant

WF03 is a reusable production stage, not a workflow for one topic, one test phrase, one language, or one job.

- narration must come from persisted `scenes.narration`;
- language must come from persisted `jobs.language_code`;
- the TTS voice must be selected deterministically from the exact four-language voice map above;
- no production TTS node may hardcode a topic, narration phrase, or Polish-only language setting;
- a concrete job may be used for acceptance, but test values must not become permanent workflow configuration.

## Verified M5 production boundary

- production VPS is on `feat/m5-voiceover`;
- accepted M4 job `6b08098c-e5c7-45bd-babb-036705b563e1` is `pl`, 30 seconds, `processing/script`, with exactly 8 planned scenes, non-empty narration, and all `audio_path` / `duration_seconds` still NULL;
- media-worker `GET /health` returns HTTP 200 with FFmpeg 8.1.2 and ffprobe 8.1.2;
- persistent Docker volume `ai-short-form-content-factory_media_data` is mounted at `/data` and writable by media-worker;
- n8n does not mount that media volume directly.

## Accepted media-worker audio boundary

Commit `1ac60492baa19e113baf9d7cdb315e7641988ff0` added internal `POST /audio/store` to the existing `media-worker` service.

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
- validates the stored candidate with ffprobe before replacing the final path;
- returns `audio_path`, measured `duration_seconds`, and byte size;
- never writes PostgreSQL directly.

Runtime acceptance passed with a disposable MP3: endpoint HTTP 200, path exact, duration 0.8s, size 4312 bytes, independent ffprobe match, cleanup confirmed, PostgreSQL untouched.

Do not repeat synthetic media-worker testing before real TTS.

## Recovered Google Cloud TTS authentication path

Existing Google Cloud project: `n8n-drive-voiceover`.

Verified:

- Cloud Text-to-Speech API is already enabled;
- project has active free-trial credit;
- there are no API keys;
- there are no service accounts;
- OAuth clients include `n8n-tts-oauth` and `n8n-drive-oauth`;
- `n8n-tts-oauth` is the dedicated prior TTS OAuth client;
- its old redirect URI pointed to deleted `https://tiktok-n8n.hodor.com.pl/rest/oauth2-credential/callback`;
- on 2026-08-23 the same OAuth client was updated and saved with current callback `https://publisher.hodor.com.pl/rest/oauth2-credential/callback`;
- on 2026-08-23 one new enabled client secret was created on this same existing OAuth client; the old secret remains present separately;
- the actual new secret value must stay local and must never be posted to chat or GitHub;
- on 2026-08-23 the current n8n runtime was configured with a new `Google OAuth2 API` credential using the existing `n8n-tts-oauth` Client ID, the fresh client secret, scope `https://www.googleapis.com/auth/cloud-platform`, and the current n8n callback URL;
- on 2026-08-23 the user completed Google account authorization for that saved credential in the current n8n runtime; authorization is treated as connected pending the first real authenticated Cloud TTS request.

Do not create a replacement OAuth client, API key, service account, or billing setup.

## WF01 hand-off checkpoint

WF01 is no longer treated as fully finished merely because M3 acceptance passed. Production chain wiring is being completed as downstream stages become available.

On 2026-08-23 the user added and saved a real `Execute Sub-workflow` node named `Start Script Planning` in production `WF01 — Create Content Job`. It targets `WF02 — Plan Script and Scenes` and maps only the newly inserted `job_id` according to the user's configuration step.

The screenshot supplied immediately afterward was actually the `WF02 — Plan Script and Scenes` canvas, not WF01. Therefore the WF01 branch topology has NOT yet been visually confirmed from a screenshot. Do not claim otherwise.

Required production behavior remains:

```text
Insert Job
├──> Return Created Job
└──> Start Script Planning -> WF02
```

The updated live WF01 workflow export and runtime end-to-end hand-off have not yet been verified or committed.

WF01 must return HTTP 201 without waiting for the downstream pipeline to complete.

## WF03 implementation checkpoint

The production n8n workflow `WF03 — Voiceover Generation` has been created as the real M5 stage workflow, and a real HTTP Request node named `Generate Voiceover` has been added to it. The exact workflow ID has not yet been recorded. No Cloud TTS request from this real node has been accepted yet.

The previously suggested disposable/temporary TTS node is no longer part of the plan. The real `Generate Voiceover` node will remain in WF03, but it must be fed by the permanent dynamic job/scene path rather than by hardcoded test narration or language.

## Smallest M5 implementation boundary

No new service is required.

- n8n owns Google Cloud TTS requests and PostgreSQL reads/writes;
- media-worker owns local audio persistence plus ffprobe duration validation;
- `scenes.audio_path` stores a media-relative path under `/data`;
- no generic retry/idempotency framework is added.

For HTTP Request authentication, use the saved dedicated `Google OAuth2 API` credential backed by `n8n-tts-oauth`. Do not reuse the Gemini header-auth credential.

## Exact next action

Return to the production `WF01 — Create Content Job` canvas and visually verify that `Insert Job` branches to both `Return Created Job` and `Start Script Planning`. Confirm that `Start Script Planning` targets WF02 and passes only `job_id`. Only after that visual confirmation, export the saved production WF01 and inspect the diff before any end-to-end test.

## Do not do

- do not substitute different voice presets;
- do not hardcode a topic, narration phrase, or Polish-only settings in production WF03;
- do not reuse the Gemini credential for TTS;
- do not create a new OAuth client, API key, service account, or billing setup;
- do not expose OAuth secrets in chat, screenshots, or GitHub;
- do not implement M5 on the old M4 branch;
- do not start M6 before M5 passes real voice acceptance;
- do not modify the n8n PostgreSQL schema manually;
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure;
- do not add extra services;
- do not put secrets in GitHub.