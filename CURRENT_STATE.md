# Current State — Clean V1

## Runtime
- PostgreSQL 18 is the source of truth for content jobs.
- n8n 2.37.10 is the orchestrator.
- `gyoridavid/short-video-maker` is the rendering foundation.
- A derived engine image replaces only the upstream TTS adapter with a local Edge-TTS sidecar and bundles multilingual Whisper `tiny`.
- Render output is portrait 1080x1920 H.264/AAC.

## Active workflows
- WF00 Job Intake: validates `topic`, `language`, `duration`; invalid input creates no row; valid input returns HTTP 201 with `job_id` and inserts exactly one PostgreSQL row.
- WF01 Render Short Video: accepts `job_id` plus scenes, resolves the language-specific voice, starts render, and persists `video_id`/rendering state.
- WF02 Video Status: accepts `job_id`, queries the renderer, and synchronizes terminal state/output path back to PostgreSQL.
- WF03 Download Video: accepts `job_id` and returns the exact rendered MP4 binary when the job is ready.

## Multilingual proof
Fresh jobs have reached `ready` for EN, PL, RU and UK using Edge-TTS voices and multilingual Whisper `tiny`.
PL download was verified byte-for-byte by SHA-256 against the renderer output.

## Known failure resolved
The first Polish render used upstream `tiny.en` Whisper and stalled after producing an incomplete MP4. That job was marked failed and not resumed. The derived engine now bundles multilingual `tiny`; a fresh Polish job completed successfully.

## Next milestone
Automate `topic -> script -> scene plan -> render` inside n8n using a free/self-hosted structured-output model. Manual scene payloads are temporary and are not the product interface.
