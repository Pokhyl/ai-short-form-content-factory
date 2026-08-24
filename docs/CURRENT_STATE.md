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
- verified hand-off target `TJfA4ZYUEKSTad6k` (`WF02`)
- verified input `job_id = {{ $json.job_id }}`
- verified `waitForSubWorkflow = false`
- verified `Insert Job` branches to both response and `Start Script Planning`
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
- on stage failure records `jobs.status = failed`, keeps `jobs.current_stage = voiceover`, stores `jobs.last_error`, and does not start the next stage
- starts Visual Sourcing only after all required scene audio is ready; M6 is not wired yet

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

- deterministic path `jobs/<job_id>/voiceover/scene-XX.mp3`
- ffprobe validation before final replace
- returns `audio_path`, measured `duration_seconds`, and `bytes`
- synthetic runtime acceptance already passed; do not repeat it before real TTS

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

## WF03 final structural verification

Production workflow:

- name `WF03 — Voiceover Generation`
- workflow ID `UHxvCZNqaLb1RKMM`
- last full structural verification export SHA-256 `33f5ab18a4e80fa2e63ad80fc845d8d113ff168fc8e802ffb218c26495d45d1e`
- that full export had exactly 17 nodes
- every structural/configuration check passed except that the workflow was still published (`ACTIVE: True`) at that moment

Export-proven success topology:

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

Export-proven failure topology:

```text
error output
-> Prepare Voiceover Failure
-> Record Voiceover Failure
-> Stop Voiceover Failure
```

Verified `On Error = continueErrorOutput` plus error-output routing for:

- `Begin Voiceover Stage`
- `Prepare Voiceover Items`
- `Generate Voiceover`
- `Require TTS Response`
- `Store Audio`
- `Require Stored Audio`
- `Persist Audio Result`
- `Require Persisted Audio Batch`
- `Verify Voiceover Completion`
- `Require Voiceover Completion`

Verified from the full export:

- `Generate Voiceover.method = POST`
- exact TTS endpoint `https://texttospeech.googleapis.com/v1/text:synthesize`
- `Store Audio.method = POST`
- exact media-worker endpoint `http://media-worker:3001/audio/store`
- `Require TTS Response` is per-item and rejects missing `audioContent`
- `Require Stored Audio` is per-item and validates `audio_path`, positive `duration_seconds`, and positive `bytes`
- failure path resolves the validated upstream `job_id`, writes `status = failed`, keeps `current_stage = voiceover`, stores `last_error`, then stops with an error
- per-item linkage from `Prepare Voiceover Items` into `Store Audio` and `Persist Audio Result` is present
- no accepted M3/M4 test UUID is hardcoded
- no Visual Sourcing hand-off exists yet
- successful completion has no normal downstream connection

## Final inactive export and local commit checkpoint

After explicitly using **Unpublish** in n8n, the production export was independently verified as:

```text
WORKFLOW_ID: UHxvCZNqaLb1RKMM
ACTIVE: false
NODE_COUNT: 17
```

A fresh inactive export was written to `n8n/workflows/WF03-voiceover-generation.json` on the VPS and verified immediately before commit.

Verified exact file values:

- workflow ID `UHxvCZNqaLb1RKMM`
- `active = false`
- exactly 17 nodes
- export SHA-256 `e767862611224b0a1a414508750d13817409ffc5cbb6352b4ecec22f86975438`

The VPS created local commit:

```text
519ae3391771884abf6e2caa1632a2002b4085e2
feat: add WF03 voiceover workflow
```

The commit contains only `n8n/workflows/WF03-voiceover-generation.json`.

The first push did not complete because the VPS HTTPS remote has no write credentials:

```text
fatal: could not read Username for 'https://github.com': No such device or address
```

## VPS Git authentication and divergence diagnostic

A second non-destructive diagnostic was completed on 2026-08-24 after the remote documentation branch advanced.

Verified at diagnostic time:

- local HEAD remains `519ae33 feat: add WF03 voiceover workflow`
- merge base is `7c4c3dbe15c19ef2cff1d84a672fd66102f625b0`
- divergence was `1 2`: one local-only WF03 commit and two remote-only documentation commits
- local-only changed path is exactly `n8n/workflows/WF03-voiceover-generation.json`
- remote-only changed path is exactly `docs/CURRENT_STATE.md`
- therefore the local and remote changed paths are explicitly proven disjoint
- matching private key `/root/.ssh/tiktok-video-pipeline-v2-deploy` exists
- public-key fingerprint is `SHA256:PvJt6+susKrlP2CIm7xsojHotHFDEJCwPhCnqzn1XeQ`
- an explicit `IdentitiesOnly=yes` read test of that exact key against `git@github.com:Pokhyl/ai-short-form-content-factory.git` fails with `Permission denied (publickey)`
- therefore that existing key does not provide repository access and must not be used for this repository

The verified WF03 commit is still safe locally. Do not recreate, amend, reset, or rebase it. Because the changed paths are now proven disjoint, a targeted merge of the latest remote documentation branch into the local branch is allowed once a repository-specific write credential is available. Prefer a repository-specific deploy key rather than reusing the unrelated `tiktok-video-pipeline-v2-deploy` key.

No real TTS request has been accepted yet.

## M5 acceptance

Per `docs/ROADMAP.md`:

- every scene has a playable audio file
- actual audio duration is measured
- voice quality is manually accepted in all supported languages used for testing

Do not start M6 before real M5 acceptance.

## Deferred M9 Studio status endpoint

During M9 add one separate read-only n8n HTTP status workflow/webhook accepting `job_id`, validating it, reading PostgreSQL, and returning at minimum `job_id`, `status`, `current_stage`, and `last_error`. Do not add public progress webhooks to WF02/WF03/WF04. Browser never connects directly to PostgreSQL. Studio may poll this single endpoint.

## Exact next action

Continue M5 without touching n8n workflow configuration.

1. Preserve VPS local commit `519ae3391771884abf6e2caa1632a2002b4085e2`; do not amend, reset, recreate, or rebase it.
2. Create a new repository-specific ED25519 deploy key on the VPS for `Pokhyl/ai-short-form-content-factory`; never expose its private key.
3. Add only the generated public key to this GitHub repository as a deploy key with write access.
4. Verify repository read and dry-run write access with that exact key before changing any Git remote configuration.
5. Fetch the latest remote `feat/m5-voiceover`, verify again that remote-only changes remain documentation-only, then merge the remote branch into the local branch with a normal merge commit so local commit `519ae33` remains intact in history.
6. Push through the repository-specific SSH key, then verify the remote branch contains `n8n/workflows/WF03-voiceover-generation.json` with expected export SHA-256 `e767862611224b0a1a414508750d13817409ffc5cbb6352b4ecec22f86975438`.
7. Only after remote verification may the first real controlled M5 TTS acceptance run be prepared.
8. Do not wire WF02->WF03 and do not start M6.

## Do not do

- do not amend/reset/recreate/rebase local WF03 commit `519ae3391771884abf6e2caa1632a2002b4085e2`
- do not reuse `/root/.ssh/tiktok-video-pipeline-v2-deploy` for this repository
- do not expose private SSH keys, GitHub tokens, or credentials
- do not substitute voice presets
- do not hardcode topic/narration/language-specific test data
- do not reuse Gemini credential for TTS
- do not create new Google TTS auth objects
- do not start M6 before M5 real voice acceptance
- do not modify the `n8n` PostgreSQL schema manually
- do not add retry/dispatcher/queue/watchdog/Redis/generic idempotency infrastructure
- do not add extra services
- do not put secrets in GitHub
