# Universal Video Factory

A topic-in, reviewable MP4 factory, built as a small self-contained Python service.

## What it does

- Accepts a topic, one of EN/PL/RU/UK, and a duration of 15, 30, 45, or 60 seconds.
- Retrieves up to six source articles from Wikipedia in the requested language. The narration uses short, source-spanned extracts and the review manifest links each beat to its article.
- Generates speech locally with eSpeak NG. It makes no Gemini, OpenAI, or other text-generation API calls.
- Searches Pexels and Pixabay once each per topic/language, caches provider responses for 24 hours, and selects two distinct photo assets per five seconds. Provider IDs, creator, provider page, article source, captions, and file hashes are saved in the manifest.
- Renders through the existing media-worker, verifies the render QA result, and fully decodes the MP4 with FFmpeg before marking the job ready.
- Provides a browser review screen with video preview, manifest, approval, and change-request status.
- Deletes temporary downloads and audio after rendering. Keeps completed MP4s for 30 days and caps the provider cache at 512 MB.

The source-based extractive approach is deterministic and free to run. If the selected language has too few suitable source passages or photo providers cannot return enough distinct topic-matched images, the job fails visibly instead of filling the video with repeated or unrelated assets.

## Runtime requirements

The deployment reuses the server's existing media-worker and shorts-v2_media_data volume. The app also joins n8n_default so Caddy can reach it. It expects these protected files on the server:

- /var/lib/factory-rebuild/secrets/settings.json: retained factory settings.
- /var/lib/factory-rebuild/secrets/visual-providers.json: existing Pexels and Pixabay credentials.
- /var/lib/factory-rebuild/secrets/n8n-project-settings.json: Studio Basic Auth username/password and public origin.

The compose file mounts them read-only. Do not copy secret values into this repository.

## Build and run

From the server checkout:

    docker compose -f factory_universal/compose.yaml config --quiet
    docker compose -f factory_universal/compose.yaml up -d --build
    docker logs --tail 100 factory-universal

The service listens on port 3000 inside Docker. Route the Studio hostname to factory-universal:3000 from a reverse proxy attached to n8n_default; retain existing n8n webhook routes before the Studio catch-all. The app enforces the retained Studio Basic Auth credentials. /healthz is an unauthenticated status-only check.

## Review API

- POST /api/jobs with JSON fields topic, language, and duration_s
- GET /api/jobs lists recent jobs.
- GET /api/jobs/{uuid} returns job state and manifest.
- GET /api/jobs/{uuid}/video streams the MP4 with byte-range support.
- GET /api/jobs/{uuid}/manifest returns the full source and media audit.
- POST /api/jobs/{uuid}/review accepts approved or changes_requested, with an optional note.

Every endpoint except /healthz requires Basic Auth.