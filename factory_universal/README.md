# Universal Video Factory

A topic-in, reviewable MP4 factory, built as a small self-contained Python service.

## What it does

- Accepts a topic, one of EN/PL/RU/UK, and a duration of 15, 30, 45, or 60 seconds.
- Retrieves up to six source articles from Wikipedia in the requested language, anchors the selected meaning and removes unrelated homonyms. The narration uses complete, source-spanned extracts and the review manifest links each beat to its article.
- Generates speech locally with eSpeak NG. It makes no Gemini, OpenAI, or other text-generation API calls.
- Searches Pexels and Pixabay with at most seven distinct topic/action queries per job, including landscape photographs, caches provider responses for 24 hours, and selects 6/12/18/24 distinct still images for 15/30/45/60-second videos. Provider IDs, creator, provider page, article source, captions, and file hashes are saved in the manifest.
- Supplements stock images with at most three cached Wikimedia Commons searches per job. Commons media must have explicit Public domain, CC0, or CC BY 2.0/2.5/3.0/4.0 metadata; the card displays the author, source, license and adaptation notice, and the manifest retains the rights fields. Other licenses are excluded.
- Verifies downloaded image pixels locally using a quantized CLIP model on CPU. The runtime makes no model API calls; its model files are mounted read-only. Each accepted image has similarity scores in the manifest. This automated screen supplements browser review.
- Preserves each whole photograph on a solid matte, with complete captions. Voice planning reserves MP3 encoder delay so the renderer can produce the exact requested duration at 30 fps.
- Renders through the existing media-worker, verifies the render QA result, and fully decodes the MP4 with FFmpeg before marking the job ready.
- Provides a browser review screen with video preview, manifest, approval, and change-request status.
- Deletes temporary downloads and audio after completion or failure. Before starting new work, it expires MP4s after 30 days, caps this factory’s output directories at 2 GB, caps its cache at 512 MB, and removes abandoned failed-job files older than a day. It refuses new jobs if less than 2 GB is free.
- Runs one isolated job process at a time with a 15-minute process-group timeout; a stuck native model or media command cannot hold the queue indefinitely.

The source-based extractive approach is deterministic and free to run. If the selected language has too few suitable source passages or photo providers cannot return enough distinct topic-matched images, the job fails visibly instead of filling the video with repeated or unrelated assets.

## Runtime requirements

Non-English topics use the English interlanguage article title for photo discovery while keeping source text, captions and speech in the selected language. Narration uses complete article paragraphs and is planned against measured local voice duration. The number of spoken facts can adapt to the available duration; every fact has at least two distinct images, while the total image count stays fixed by video length.

The deployment reuses the server's existing media-worker and shorts-v2_media_data volume. The app also joins n8n_default so Caddy can reach it. It expects these protected files on the server:

- /var/lib/factory-rebuild/secrets/settings.json: retained factory settings.
- /var/lib/factory-rebuild/secrets/visual-providers.json: existing Pexels and Pixabay credentials.
- /var/lib/factory-rebuild/secrets/n8n-project-settings.json: Studio Basic Auth username/password and public origin.

The compose file mounts them read-only. Do not copy secret values into this repository.

## Build and run

From the server checkout, install the pinned local model once (about 156 MB; verified by SHA-256, reused across builds):

    sudo python3 factory_universal/setup_models.py

Then build and start:

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
## Verification

Run focused offline checks in the deployed runtime:

    docker exec -i factory-universal python3 - < factory_universal/checks.py

`review_outputs.py` collects the explicitly recorded acceptance jobs, checks frame count/duration and creates midpoint contact sheets. It never submits or retries generation jobs. Its dated plan is diagnostic evidence, not a production dependency.

Wikipedia HTTP 429 stops fresh retrieval. A saved source for the same topic/language may be reused for up to 24 hours, with a retrieval note in the manifest; without one the job fails visibly. Local pixel screening can reject a good photograph or miss a contextual mismatch, so the product keeps review and change-request controls.
