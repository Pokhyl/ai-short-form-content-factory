# Universal Video Factory

Native-language topic → source-grounded vertical MP4.

Studio: https://studio.hodor.com.pl/ . The site and review API require no password.

## Current delivery state

project_ready=false. The owner restored the retained Google connection; read-only metadata execution 14691 returned READY. The app checks that connection before admitting a job. Full MP4 acceptance is still required; metadata readiness alone does not establish narration success.

First replacement test f632a0cf-b09b-4bd7-a553-d7c9e695900a completed images and stopped at the voice gateway. Its stopped synthesis is not resent. Full replacement MP4 acceptance remains pending after reconnection and image-review corrections. Image-only checks do not establish MP4 or listening acceptance.

## Pipeline

- EN/PL/RU/UK; 15/30/45/60 seconds.
- Resolve the primary native Wikipedia article before binding its Wikidata identity. Structured label/description evidence is typed separately from article quotes.
- Select complete source sentences and connected paragraphs, preserving original spans. Connected blocks expand into readable aligned captions. Protect abbreviations and real exponents; omit reference/navigation marks.
- Fit natural narration using completed selected-voice measurements. Prefer fewer complete facts and more images per fact. Exact MP4 frame counts remain mandatory; natural speech may leave a short final visual hold.
- Search at most seven distinct stock queries and three Commons queries across the whole job, including duration corrections. Commons searches return at most 50 candidates each. Cache source/provider results for 24 hours.
- Preserve complete photographs at their original aspect ratio. Screen pixels using the pinned local CLIP model. Human subjects additionally require matching Commons depicts metadata or the exact Wikidata-linked category and a separate photographic human-content screen.
- Verify all 6/12/18/24 distinct images before requesting narration. Each narration beat has at least two images.
- Align the unchanged selected-voice MP3; render 1080×1920 H.264/AAC at 30 fps; fully decode before ready.
- Keep source/media provenance, licenses, image hashes, pixel screening, voice receipts, alignment and render checks in the manifest.

| Language | Fixed owner-selected voice |
|---|---|
| EN | en-US-Chirp3-HD-Algenib |
| PL | pl-PL-Chirp3-HD-Enceladus |
| RU | ru-RU-Wavenet-D |
| UK | uk-UA-Chirp3-HD-Enceladus |

Google uses the retained native n8n gateway and shared PostgreSQL free-tier character ledger. Durable claims precede uncertain sends. Timeouts/errors stop without automatic resends. Up to three distinct texts may be synthesized after completed duration misses. Completed identical audio may be reused for 24 hours. No audible eSpeak fallback, tempo change, Gemini call or paid model API is allowed.

Experimental drafting/translation models failed quality checks and were removed. They are not dependencies. Only the checksum-pinned visual model remains, mounted read-only. eSpeak is an internal estimate only.

## Bounds

One isolated worker, with a 900-second process-group deadline. Cleanup selects exact SQLite-owned UUID directories: 30-day output retention, 2-GiB output cap, 512-MiB JSON cache cap, 2-GiB free-disk reserve. Temporary image/audio files are removed after completion/failure. Image-only acceptance artifacts share the output cap.

Commons requires Public domain, CC0 or CC BY 2.0/2.5/3.0/4.0 metadata. Cards include required author/source/license/adaptation notices.

## Run and verify

Authoritative checkout: /opt/factory-universal. Container: factory-universal. Delivery branch: codex/factory-universal-20261112.

Retained settings under /var/lib/factory-rebuild/secrets are mounted read-only. Never print or commit secret values. Removing Studio login does not require deleting shared credentials.

Reverify the visual model with factory_universal/setup_models.py. Check active jobs before recreating only this app:

    docker compose -f factory_universal/compose.yaml build app
    docker exec -i factory-universal python3 - < factory_universal/checks.py
    docker compose -f factory_universal/compose.yaml up -d app

Leave the shared media-worker, volume, n8n networks and unrelated services intact.

## API

- GET /healthz: application status.
- GET /api/provider-status: cached read-only Google connection check; refresh=1 requests a throttled fresh check.
- POST /api/jobs: topic, language, duration_s; operator tests may set origin=test. A rejected connection returns 503 before creating a job or spending narration quota.
- GET /api/jobs: user history; view=examples or view=tests selects operator views.
- GET /api/jobs/{uuid}, /video, /manifest: state, ranged MP4 and audit.
- POST /api/jobs/{uuid}/review: approved or changes_requested.
- POST /api/jobs/{uuid}/subject: reject that resolved meaning without rewriting the original job or replaying synthesis.

The UI is index.html. It preserves playback during polling. Source clarification and Google reconnection are separate actions. Technical checks or assistant frame review never imply owner listening approval.
