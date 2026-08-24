# Current Project State

Last updated: 2026-08-24

This file is the first checkpoint to read before continuing work on this repository. If chat history conflicts with this file, `docs/ARCHITECTURE.md`, or `docs/ROADMAP.md`, the repository wins.

## Mandatory assistant protocol

Before every technical reply/action for this project, fetch this file from the active branch. Fetch `docs/ARCHITECTURE.md` when architecture is involved and `docs/ROADMAP.md` when milestone scope/acceptance/progression is involved. Repository state overrides chat memory. Unknown facts must not be guessed. After each completed implementation/runtime/setup step, update this file before moving on. Export production n8n workflows into the repository.

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

## WF01 — Create Content Job

- workflow ID `Xy94qe35OigtMxkR`
- native hand-off target `TJfA4ZYUEKSTad6k` (`WF02`)
- payload `job_id = {{ $json.job_id }}`
- `waitForSubWorkflow = false`
- remote workflow commit `353149dbe5ff7e511ad5dfe7683b00755f765727`

## WF02 — Plan Script and Scenes

- workflow ID `TJfA4ZYUEKSTad6k`
- accepted pre-handoff export SHA-256 `be35214a12a4ef933145e629a3cf070376378a1b1a9ba9cd3256b8fbd5f0fdc1`
- accepted pre-handoff export commit `8a545d3f2fc1942b3f95aa9c6919b0cfc2995ac2`
- accepted quality job `6b08098c-e5c7-45bd-babb-036705b563e1`

Verified WF02->WF03 hand-off structure:

```text
NODE_COUNT: 9
NODE_TYPE: n8n-nodes-base.executeWorkflow
HANDOFF_TARGET: UHxvCZNqaLb1RKMM
INPUT_KEYS: ['job_id']
JOB_ID_VALUE: ={{ $json.job_id }}
WAIT_FOR_SUBWORKFLOW: False
PERSIST_TARGETS: ['Start Voiceover Generation']
WF02_WF03_HANDOFF_VERIFICATION: OK
```

After removing pinned data and publishing, the fresh production export verified:

```text
WF02_ACTIVE: YES
WF02_VERSION: 294e91cb-54b5-4f5f-97b7-a0f1f57fd02b
WF02_PIN_DATA: EMPTY
WF02_WF03_HANDOFF: OK
```

Final verified export SHA-256:

```text
d06d0ff1bb325d6c54999c2f89fee8e9b887ed436872092caff34a9d21fc60b7
```

## M5 exact voice configuration — locked

Provider: Google Cloud Text-to-Speech.

| Language | Exact voice preset |
| --- | --- |
| `en` | `en-US-Chirp3-HD-Algenib` |
| `pl` | `pl-PL-Chirp3-HD-Enceladus` |
| `ru` | `ru-RU-Wavenet-D` |
| `uk` | `uk-UA-Chirp3-HD-Enceladus` |

The operator explicitly decided to keep all four configured voices unchanged. Do not spend additional time comparing/replacing them unless a concrete runtime problem appears.

## M5 contract

WF03 receives only `job_id`, reloads persisted state from PostgreSQL, validates eligibility, sets `current_stage = voiceover`, generates one voiceover per scene using the locked voice map, stores `scenes.audio_path` plus measured `scenes.duration_seconds`, and records failures as `status=failed`, `current_stage=voiceover`, plus `last_error`. PostgreSQL writes remain in n8n. M6 is not wired yet.

## Google Cloud TTS authentication

Use existing project `n8n-drive-voiceover` and dedicated OAuth client `n8n-tts-oauth`.

Verified:

- Text-to-Speech API enabled
- callback `https://publisher.hodor.com.pl/rest/oauth2-credential/callback`
- n8n credential type `Google OAuth2 API`
- scope `https://www.googleapis.com/auth/cloud-platform`
- Google authorization completed

Do not create replacement auth objects or expose secrets.

## WF03 — Voiceover Generation

- name `WF03 — Voiceover Generation`
- workflow ID `UHxvCZNqaLb1RKMM`
- 17-node production implementation
- no M6/Visual Sourcing hand-off yet

After removing pinned data and publishing, the fresh production export verified:

```text
WF03_ACTIVE: YES
WF03_VERSION: 3a606df5-21cb-45b3-9f7a-a9da74f74d3c
WF03_PIN_DATA: EMPTY
WF03_VOICE_MAP: OK
```

Final verified export SHA-256:

```text
666a2de498e4feac7e7877bf2ebc44e61c63fbd38698f239f427ecf673042c86
```

The final combined export verification also proved:

```text
HARDCODED_ACCEPTANCE_DATA: NONE
M5_FINAL_EXPORT_VERIFICATION: OK
```

## Real M5 runtime acceptance

Polish 15-second acceptance job:

```text
db19212b-7914-4346-9ec6-234d315c80d0
```

Before WF03:

```text
status=processing
current_stage=script
scene_count=4
narration_count=4
audio_state_count=0
```

Real WF03 execution completed through the normal success path. After WF03:

```text
status=processing
current_stage=voiceover
last_error=empty
```

Persisted/probed audio:

| Scene | duration_seconds | size bytes |
| ---: | ---: | ---: |
| 1 | 6.096 | 24384 |
| 2 | 6.576 | 26304 |
| 3 | 6.768 | 27072 |
| 4 | 6.576 | 26304 |

All four `audio_path` values are populated; all MP3 files exist, are non-empty, readable/probeable, and durations match PostgreSQL. Files were copied to the operator Mac and listened to manually; Polish voice quality was accepted. Do not rerun this job.

## Local repository checkpoint

The verified production exports were copied into the VPS repository and committed locally:

```text
8e6e4a9 feat: finalize M5 voiceover workflows
```

The commit contains only the refreshed WF02 and WF03 exports. The push then failed before reaching GitHub:

```text
fatal: could not read Username for 'https://github.com': No such device or address
```

Therefore `8e6e4a9` is currently a local VPS commit and is **not yet a remote checkpoint**.

## M5 status

Voice generation, production hand-off, active/current workflow versions, empty pin data, locked voice map, and final workflow exports are all verified. M5 remains `in progress` only because local workflow commit `8e6e4a9` has not yet been pushed to GitHub.

## Exact next action

1. Do not rerun accepted M4/M5 jobs.
2. On the VPS, verify the dedicated repository SSH deploy key exists and can read the repository.
3. Fetch the current remote `feat/m5-voiceover` branch over SSH, merge it normally with local commit `8e6e4a9` if the remote advanced, and push over SSH. Do not force/rebase/reset.
4. Verify remote head contains local workflow commit `8e6e4a9` as an ancestor and both workflow files have the final SHA-256 values above.
5. Then update this file with the final remote checkpoint, mark M5 complete, update `docs/ROADMAP.md`, and only then start M6.

## Do not do

- do not change the four selected voices
- do not rerun prior accepted M4/M5 jobs
- do not start M6 before the verified workflow commit is pushed and the remote checkpoint is recorded
- do not expose private SSH keys, GitHub tokens, OAuth secrets, or credentials
- do not hardcode test job/topic/language-specific data into permanent nodes
- do not reuse Gemini credential for TTS
- do not create new Google TTS auth objects
- do not modify the `n8n` PostgreSQL schema manually
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure
- do not add extra services
- do not put secrets in GitHub
