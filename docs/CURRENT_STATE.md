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
- hand-off target `TJfA4ZYUEKSTad6k` (`WF02`)
- payload `job_id = {{ $json.job_id }}`
- `waitForSubWorkflow = false`
- remote workflow commit `353149dbe5ff7e511ad5dfe7683b00755f765727`

### WF02 — Plan Script and Scenes

- workflow ID `TJfA4ZYUEKSTad6k`
- accepted export SHA-256 `be35214a12a4ef933145e629a3cf070376378a1b1a9ba9cd3256b8fbd5f0fdc1`
- accepted export commit `8a545d3f2fc1942b3f95aa9c6919b0cfc2995ac2`
- accepted quality job `6b08098c-e5c7-45bd-babb-036705b563e1`
- WF02->WF03 is not wired yet

## M5 exact voice configuration — locked

Provider: Google Cloud Text-to-Speech.

| Language | Exact voice preset |
| --- | --- |
| `en` | `en-US-Chirp3-HD-Algenib` |
| `pl` | `pl-PL-Chirp3-HD-Enceladus` |
| `ru` | `ru-RU-Wavenet-D` |
| `uk` | `uk-UA-Chirp3-HD-Enceladus` |

On 2026-08-24 the operator explicitly decided to keep **all four configured voices unchanged**. No further voice substitution or voice-selection work is required unless a concrete runtime problem appears.

## M5 contract

WF03 receives only `job_id`, reloads persisted state from PostgreSQL, validates eligibility, sets `current_stage = voiceover`, generates one audio file per scene using the locked voice map, stores `scenes.audio_path` and measured `scenes.duration_seconds`, and records stage failures as `status = failed`, `current_stage = voiceover`, plus `last_error`. PostgreSQL writes remain in n8n. M6 is not wired yet.

Production generality is mandatory: narration from `scenes.narration`, language from `jobs.language_code`, voice from the locked map, and no hardcoded topic/test narration/test job in permanent nodes.

## Google Cloud TTS authentication

Use existing project `n8n-drive-voiceover` and dedicated OAuth client `n8n-tts-oauth`.

Verified:

- Text-to-Speech API enabled
- callback `https://publisher.hodor.com.pl/rest/oauth2-credential/callback`
- n8n credential type `Google OAuth2 API`
- scope `https://www.googleapis.com/auth/cloud-platform`
- Google authorization completed

Do not create replacement auth objects or expose secrets.

## WF03 repository checkpoint

Production workflow:

- name `WF03 — Voiceover Generation`
- workflow ID `UHxvCZNqaLb1RKMM`
- inactive (`active = false`)
- 17 nodes
- final export SHA-256 `e767862611224b0a1a414508750d13817409ffc5cbb6352b4ecec22f86975438`
- local workflow commit `519ae3391771884abf6e2caa1632a2002b4085e2`
- merge/push checkpoint `28b5cca041cf29984ca155e36b280ef00649d873`
- remote file SHA verified identical
- no Visual Sourcing hand-off exists yet

Success topology:

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

Failure topology:

```text
error output -> Prepare Voiceover Failure -> Record Voiceover Failure -> Stop Voiceover Failure
```

## Real M5 runtime acceptance

Polish 15-second acceptance job:

```text
db19212b-7914-4346-9ec6-234d315c80d0
```

Verified before WF03:

```text
status = processing
current_stage = script
scene_count = 4
narration_count = 4
audio_state_count = 0
```

The real WF03 execution completed through the normal success path.

Verified after WF03:

```text
status = processing
current_stage = voiceover
last_error = empty
```

Persisted and probed audio:

| Scene | duration_seconds | size bytes |
| ---: | ---: | ---: |
| 1 | 6.096 | 24384 |
| 2 | 6.576 | 26304 |
| 3 | 6.768 | 27072 |
| 4 | 6.576 | 26304 |

All four `audio_path` values are populated, all four MP3 files exist, are non-empty, and are readable/probeable. The files were copied to the operator Mac and listened to manually; Polish voice quality was accepted.

The operator has now explicitly confirmed that all four configured voice presets are to remain as selected. Do not spend additional time comparing/replacing EN/PL/RU/UK voices.

## M5 status

M5 voice generation is functionally proven with a real TTS run: playable files are produced, real durations are measured/persisted, and the selected voice set is accepted by the operator.

M5 remains `in progress` only because final pipeline integration WF02->WF03 has not yet been added/exported/verified. Do not start M6 before that integration checkpoint is complete.

## Exact next action

1. Keep the four voice presets exactly as locked above.
2. Do not rerun the accepted Polish job.
3. Prepare the grounded WF02->WF03 native n8n sub-workflow hand-off using payload only `{ "job_id": "<uuid>" }` and `waitForSubWorkflow = false`.
4. Export and verify the resulting WF02 workflow before committing it.
5. After the hand-off checkpoint is complete, close M5 and only then start M6.

## Do not do

- do not change the four selected voice presets
- do not rerun prior accepted M4/M5 jobs
- do not expose private SSH keys, GitHub tokens, OAuth secrets, or credentials
- do not hardcode topic/narration/language-specific test data into production nodes
- do not reuse Gemini credential for TTS
- do not create new Google TTS auth objects
- do not start M6 before the WF02->WF03 integration checkpoint is complete
- do not modify the `n8n` PostgreSQL schema manually
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure
- do not add extra services
- do not put secrets in GitHub
