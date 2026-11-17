# Universal Video Factory

Owner rejection: e4371771-bf21-4585-b195-fe7c77d23650 is a scene-irrelevant portrait slideshow and must not be accepted. General scene-to-media grounding is required; do not fix one video with handpicked assets.

Owner regression, 2026-11-16: Илон Маск / UK60 failed image selection at scene 24 (ae9b4750-4df5-4e1a-9ea0-7083625de950), with zero narration sends. Earlier six-case acceptance remains historical; general readiness is withdrawn until this regression and broader person selection are verified.

Native-language topic → source-grounded vertical MP4.

Studio: https://studio.hodor.com.pl/ . The site and review API require no password.

## Current delivery state

project_ready=false for the implemented automated MP4 workflow. Six normal API outputs passed exact frames/duration, full decoding, unchanged selected-voice input, image/provenance gates and assistant inspection of every shot: EN15, PL30, RU45, UK60, manufacturing EN30 and named-person UK30.

Evidence: acceptance/factory-universal/2026-11-16/acceptance.json . Studio is password-free; unauthenticated page/video-range checks pass. The owner rejected the portrait-only replacement e4371771-bf21-4585-b195-fe7c77d23650. General source-linked storyboard work is under verification and is not deployed; general readiness remains withdrawn. Owner listening approval is separate and remains pending.

Inputs require an identifiable source and enough suitable licensed photographs. Ambiguous or unsupported inputs stop instead of inventing facts or inserting unrelated media.

## Pipeline

- EN/PL/RU/UK; 15/30/45/60 seconds.
- Resolve the primary native Wikipedia article before binding its Wikidata identity. Structured label/description evidence is typed separately from article quotes.
- Select complete source sentences and connected paragraphs, preserving original spans. Connected blocks expand into readable aligned captions. Protect abbreviations and real exponents; omit reference/navigation marks.
- Fit natural narration using completed selected-voice measurements. Prefer fewer complete facts and more images per fact. Exact MP4 frame counts remain mandatory; natural speech may leave a short final visual hold.
- Search at most seven distinct stock queries and three Commons queries for broad subjects, or 24 bounded Commons queries for source-linked storyboards, across the whole job including planning and duration corrections. Commons searches return at most 50 candidates each. Cache source/provider results for 24 hours.
- Preserve complete photographs at their original aspect ratio. Screen pixels using the pinned local CLIP model. Human subjects additionally require matching Commons depicts metadata or the exact Wikidata-linked category and a separate photographic human-content screen. Named places require Commons category identity, with bounded distinct searches for proper-name details. Named astronomical bodies require institutional provenance. Maps, woodcuts and downstream uses of manufactured goods are rejected.
- Verify all 6/12/18/24 distinct images before requesting narration. Each narration beat has at least two images.
- Align the unchanged selected-voice MP3; render 1080×1920 H.264/AAC at 30 fps using the project-owned FFmpeg renderer; fully decode before ready.
- Keep source/media provenance, licenses, image hashes, pixel screening, voice receipts, alignment and render checks in the manifest.

| Language | Fixed owner-selected voice |
|---|---|
| EN | en-US-Chirp3-HD-Algenib |
| PL | pl-PL-Chirp3-HD-Enceladus |
| RU | ru-RU-Wavenet-D |
| UK | uk-UA-Chirp3-HD-Enceladus |

Google uses the retained native n8n gateway and shared PostgreSQL free-tier character ledger. Durable claims precede uncertain sends. Timeouts/errors stop without automatic resends. Up to three distinct texts may be synthesized after completed duration misses. Completed identical audio may be reused for 24 hours. A completed narration plan is reusable only while its entity, exact source spans, selected voice and duration still match; stale sources are rejected. No audible eSpeak fallback, tempo change, Gemini call or paid model API is allowed.

Experimental drafting/translation models failed quality checks and were removed. They are not dependencies. Only the checksum-pinned visual model remains, mounted read-only. The shared media-worker is used for alignment; its old per-duration render thresholds are not part of the universal renderer. eSpeak is an internal estimate only.

## Bounds

One isolated worker, with a 900-second process-group deadline. Cleanup selects exact SQLite-owned UUID directories: 30-day output retention, 2-GiB output cap including ASR/review records, 512-MiB JSON/audio cache cap, 2-GiB free-disk reserve. Temporary image/audio files are removed after completion/failure. Image-only acceptance artifacts share the output cap. Expired manifests are compacted while job/error identities remain.

Commons requires Public domain, CC0 or CC BY 2.0/2.5/3.0/4.0 metadata. Cards include required author/source/license/adaptation notices.

## Run and verify

Authoritative checkout: /opt/factory-universal. Container: factory-universal. Delivery branch: codex/factory-universal-20261112.

Retained settings under /var/lib/factory-rebuild/secrets are mounted read-only. Never print or commit secret values. Removing Studio login does not require deleting shared credentials.

Reverify the visual model with factory_universal/setup_models.py. Check active jobs before recreating only this app:

    docker compose -f factory_universal/compose.yaml build app
    docker compose -f factory_universal/compose.yaml run --rm --no-deps -T app python3 - < factory_universal/checks.py
    docker compose -f factory_universal/compose.yaml run --rm --no-deps -T app python3 - < factory_universal/alignment_checks.py
    docker compose -f factory_universal/compose.yaml run --rm --no-deps -T app python3 - < factory_universal/renderer_checks.py
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


2026-11-17 verification checkpoint (not a release): images are screened for photographic genre and scene identity before narration. Physical awards must show the award object rather than unrelated laureates; process scenes require the narrated operation instead of generic factory imagery. Crop/resize duplicate detection uses bounded in-memory OpenCV features. `preflight_outputs.py` remains image-only with a duration-scaled 300–480 second per-case deadline, no synthesis. Failed or semantically rejected image tests are not successful MP4 acceptance. No new production deployment is implied by an image build.
