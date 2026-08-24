# Current Project State

Last updated: 2026-08-24

This file is the first checkpoint to read before continuing work on this repository. If chat history conflicts with this file, `docs/ARCHITECTURE.md`, or `docs/ROADMAP.md`, the repository wins.

## Mandatory assistant protocol

For every technical reply or action about this project, fetch the current `docs/CURRENT_STATE.md` from the active feature branch first. Fetch `docs/ARCHITECTURE.md` when architecture is involved and `docs/ROADMAP.md` when milestone scope, acceptance, or progression is involved. Repository state overrides chat memory. Unknown facts must not be guessed. After every completed implementation or runtime/setup step, update this file before moving on. Export production n8n workflows into the repository.

## Project

- repository: `Pokhyl/ai-short-form-content-factory`
- branch: `feat/m5-voiceover`
- milestone: M5 — Voiceover (`in progress`)

Target flow:

```text
Topic -> Script + scene plan -> Voiceover -> Visual sourcing -> Render -> Human review -> Buffer draft
```

## Runtime

- VPS: `root@37.27.87.6`
- project path: `/opt/ai-short-form-content-factory`
- services exactly: `n8n`, `postgres`, `media-worker`
- n8n: `https://publisher.hodor.com.pl/`
- future Studio: `https://studio.hodor.com.pl/`
- application state: PostgreSQL `public`
- n8n internal schema: `n8n`; never modify it manually

## Upstream checkpoints

### WF01 — Create Content Job

- workflow ID `Xy94qe35OigtMxkR`
- verified hand-off target `TJfA4ZYUEKSTad6k` (`WF02`)
- verified payload `job_id = {{ $json.job_id }}`
- verified `waitForSubWorkflow = false`
- remote workflow commit `353149dbe5ff7e511ad5dfe7683b00755f765727`
- final WF01->WF02 runtime hand-off has not yet been acceptance-tested

### WF02 — Plan Script and Scenes

- workflow ID `TJfA4ZYUEKSTad6k`
- accepted export SHA-256 `be35214a12a4ef933145e629a3cf070376378a1b1a9ba9cd3256b8fbd5f0fdc1`
- accepted export commit `8a545d3f2fc1942b3f95aa9c6919b0cfc2995ac2`
- accepted quality job `6b08098c-e5c7-45bd-babb-036705b563e1`, Polish, 30 seconds, 8 scenes, manual quality PASS
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

## M5 contract

WF03 receives only `job_id`, reloads persisted state from PostgreSQL, validates eligibility, sets `current_stage = voiceover`, generates one audio file per scene using the locked voice map, stores `scenes.audio_path` and measured `scenes.duration_seconds`, and records stage failures as `status = failed`, `current_stage = voiceover`, plus `last_error`. PostgreSQL writes remain in n8n. M6 is not wired yet.

Production generality is mandatory: narration from `scenes.narration`, language from `jobs.language_code`, voice from the locked map, and no hardcoded topic/test narration/test job in permanent nodes.

## Media-worker audio boundary

Commit `1ac60492baa19e113baf9d7cdb315e7641988ff0` added `POST /audio/store` to the existing media-worker.

- deterministic path `jobs/<job_id>/voiceover/scene-XX.mp3`
- ffprobe validation
- returns `audio_path`, measured `duration_seconds`, and `bytes`
- synthetic runtime acceptance already passed; do not repeat it before real TTS

## Google Cloud TTS authentication

Use existing project `n8n-drive-voiceover` and dedicated OAuth client `n8n-tts-oauth`.

Verified:

- Text-to-Speech API enabled
- active free-trial credit
- callback `https://publisher.hodor.com.pl/rest/oauth2-credential/callback`
- n8n credential type `Google OAuth2 API`
- scope `https://www.googleapis.com/auth/cloud-platform`
- Google authorization completed
- first real authenticated TTS request still pending acceptance

Do not create replacement auth objects or expose secrets.

## WF03 final verified export

- workflow name `WF03 — Voiceover Generation`
- workflow ID `UHxvCZNqaLb1RKMM`
- exact final export is inactive (`active = false`)
- exact final export has 17 nodes
- final export SHA-256 `e767862611224b0a1a414508750d13817409ffc5cbb6352b4ecec22f86975438`
- no Visual Sourcing hand-off exists yet

Verified success topology:

```text
Receive Job ID
-> Normalize Job ID
-> Load Voiceover Context
-> Require Eligible Voiceover Job
-> Begin Voiceover Stage
-> Prepare Voiceover Items
-> Generate Voiceover
-> Require TTS Response
-> Store Audio
-> Require Stored Audio
-> Persist Audio Result
-> Require Persisted Audio Batch
-> Verify Voiceover Completion
-> Require Voiceover Completion
-> STOP
```

Verified failure topology:

```text
error output -> Prepare Voiceover Failure -> Record Voiceover Failure -> Stop Voiceover Failure
```

Verified invariants include intended `continueErrorOutput` routes, TTS POST endpoint, media-worker POST endpoint, response guards, failure SQL, per-item linkage, no hardcoded acceptance UUIDs, and no M6 hand-off.

## WF03 repository checkpoint — remote verified

The exact verified workflow export was originally committed on the VPS as:

```text
519ae3391771884abf6e2caa1632a2002b4085e2
feat: add WF03 voiceover workflow
```

That commit contains only `n8n/workflows/WF03-voiceover-generation.json` and remains intact in history.

A normal merge commit was created and pushed after documentation-only remote changes were proven disjoint from the local WF03-only commit:

```text
28b5cca041cf29984ca155e36b280ef00649d873
merge: sync M5 documentation before WF03 push
```

Post-push verification proved remote HEAD matched local HEAD and the remote WF03 file had exact SHA-256 `e767862611224b0a1a414508750d13817409ffc5cbb6352b4ecec22f86975438`.

## First real M5 acceptance job — prepared

A fresh disposable Polish 15-second acceptance job was created through production WF01 on 2026-08-24:

```text
job_id: db19212b-7914-4346-9ec6-234d315c80d0
```

Observed runtime progression:

```text
ATTEMPT_1: created|intake|0|0|0|
ATTEMPT_2: processing|script|4|4|0|
```

Therefore, at the second check the job had:

- `status = processing`
- `current_stage = script`
- exactly 4 scenes, which is the required count for a 15-second job
- non-empty narration for all 4 scenes
- zero existing audio fields

This job is the first controlled M5 TTS acceptance candidate. Do not reuse prior M3/M4 acceptance jobs.

No real TTS request has yet been executed for this job.

## M5 acceptance

Per `docs/ROADMAP.md`:

- every scene has a playable audio file
- actual audio duration is measured
- voice quality is manually accepted in all supported languages used for testing

Do not start M6 before real M5 acceptance.

## Exact next action

1. Use acceptance job `db19212b-7914-4346-9ec6-234d315c80d0` for the first real controlled WF03 run.
2. Do not wire WF02->WF03.
3. Invoke WF03 with only `{ "job_id": "db19212b-7914-4346-9ec6-234d315c80d0" }`.
4. After the run, verify job status/stage/error plus all four scenes in PostgreSQL.
5. Require non-empty `audio_path` and positive measured `duration_seconds` for all four scenes.
6. Verify the corresponding MP3 files exist and are readable/playable.
7. Manually listen to the Polish voice before marking Polish accepted.
8. If the run fails, inspect the exact n8n execution and persisted `last_error` before changing WF03; do not rerun blindly.
9. Keep M6 disconnected until M5 acceptance is complete.

## Do not do

- do not rerun prior M4 acceptance jobs
- do not wire WF02->WF03 yet
- do not expose private SSH keys, GitHub tokens, OAuth secrets, or credentials
- do not substitute voice presets
- do not hardcode topic/narration/language-specific test data into production nodes
- do not reuse Gemini credential for TTS
- do not create new Google TTS auth objects
- do not start M6 before M5 real voice acceptance
- do not modify the `n8n` PostgreSQL schema manually
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure
- do not add extra services
- do not put secrets in GitHub
