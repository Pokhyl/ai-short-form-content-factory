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

On 2026-08-24 the operator added one native n8n `Execute Sub-workflow` node after `Persist Scene Plan`:

- reported node name: `Start Voiceover Generation`
- reported target: `WF03 — Voiceover Generation` (`UHxvCZNqaLb1RKMM`)
- intended payload: dynamic `job_id` only
- intended `waitForSubWorkflow = false`

A first combined export/verification shell block stopped immediately after printing `=== EXPORT WF02 ===`, before its Python verification ran. A follow-up diagnostic proved the n8n export itself is healthy:

```text
REPO FILE STATE: M n8n/workflows/WF02-plan-script-and-scenes.json
repo export size: 25138 bytes
n8n export command: success
EXPORT_RC: 0
FILE_CREATED: YES
diagnostic export size: 25138 bytes
```

`n8n export:workflow --id=TJfA4ZYUEKSTad6k` reported `Successfully exported 1 workflow.` The diagnostic JSON begins with the expected workflow ID/name and `active=true`.

This proves the export command succeeded and the local workflow file is non-empty; it does **not yet prove** the local file is byte-identical to the diagnostic export or that the new WF02->WF03 hand-off fields are correct. The hand-off is not yet committed.

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

## WF03 repository/runtime checkpoint

- name `WF03 — Voiceover Generation`
- workflow ID `UHxvCZNqaLb1RKMM`
- inactive (`active=false`)
- 17 nodes
- final export SHA-256 `e767862611224b0a1a414508750d13817409ffc5cbb6352b4ecec22f86975438`
- original local workflow commit `519ae3391771884abf6e2caa1632a2002b4085e2`
- merge/push checkpoint `28b5cca041cf29984ca155e36b280ef00649d873`
- remote file SHA verified identical
- no M6/Visual Sourcing hand-off yet

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

## M5 status

Voice generation is functionally proven with real TTS output and the selected voice set is locked. M5 remains `in progress` only because the new WF02->WF03 integration must be verified from the fresh export and committed/pushed.

## Exact next action

1. Do not rerun accepted M4/M5 jobs.
2. Compare host `n8n/workflows/WF02-plan-script-and-scenes.json` with `/tmp/wf02-diagnostic.json` from the successful n8n diagnostic export (hash/byte identity).
3. Verify from the exported JSON:
   - workflow ID `TJfA4ZYUEKSTad6k`
   - `Persist Scene Plan` connects to exactly one `Start Voiceover Generation`
   - node type `n8n-nodes-base.executeWorkflow`
   - target `UHxvCZNqaLb1RKMM`
   - payload contains only dynamic `job_id`
   - `waitForSubWorkflow=false`
   - no hardcoded acceptance UUID/topic data
   - inspect `versionId` vs `activeVersionId` to determine whether the edited version is published
4. Only after those checks pass, commit/push the refreshed WF02 export (and publish first if required).
5. Then update this file with export SHA/commit and close M5 before starting M6.

## Do not do

- do not change the four selected voices
- do not rerun prior accepted M4/M5 jobs
- do not start M6 before WF02->WF03 integration is verified and committed
- do not expose private SSH keys, GitHub tokens, OAuth secrets, or credentials
- do not hardcode test job/topic/language-specific data into permanent nodes
- do not reuse Gemini credential for TTS
- do not create new Google TTS auth objects
- do not modify the `n8n` PostgreSQL schema manually
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure
- do not add extra services
- do not put secrets in GitHub
