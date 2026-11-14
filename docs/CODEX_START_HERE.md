# Universal MP4 factory — active entry point

`project_ready=true` for the source-grounded topic-to-reviewable-MP4 workflow, verified 2026-11-14.

Open https://studio.hodor.com.pl/ with the retained Studio login. Enter a topic, EN/PL/RU/UK and 15/30/45/60 seconds. The service researches sources, selects distinct images, creates local speech and captions, assembles MP4 and presents the review screen automatically.

Read `factory_universal/README.md` for deployment and API operation. Active code: `factory_universal/`; server checkout: `/opt/factory-universal`; app/container: `factory-universal`; delivery branch: `codex/factory-universal-20261112`. Earlier Gemini/factory-v3 plans are historical. The old start notes are retained in `docs/archive/CODEX_START_HERE_legacy_20261111.md` and Git history.

## Verified acceptance outputs

| Language | Topic | Seconds | Frames | Images | Job ID |
|---|---|---:|---:|---:|---|
| pl | Energia słoneczna | 15 | 450 | 6 | 89ba9b95-7ae9-4316-95ad-d06f7121ad2a |
| en | Volcano | 60 | 1800 | 24 | bb024c75-eb1c-4c92-92ed-171e2a8c28bd |
| en | How glass bottles are made | 30 | 900 | 12 | d379cf75-db33-4c9e-ac5d-516e07473ec0 |
| en | Lunar eclipse | 45 | 1350 | 18 | 3153d204-ca03-4295-a513-02ead76bc103 |
| ru | Солнечная энергия | 15 | 450 | 6 | 3abed575-1a61-4a35-91d6-b71c349d1417 |
| uk | Сонячна енергія | 15 | 450 | 6 | f8a85823-497f-4bd5-b49a-f2191dfad4a9 |

All six normal API cases reached ready, passed full FFmpeg decode, output hash checks, 1080×1920 H.264/AAC, 30 fps, exact requested frame counts, source/media provenance, per-image local screening, unique assets, and at least two images per spoken fact. Current-planner script and metadata-filter replays passed for every output; generation source hashes are retained per case.

Assistant review inspected actual output contact sheets and captions. Local speech uses eSpeak NG; narration consists of complete cited extracts. Owner review remains pending in the product. No owner/HUMAN audio approval is asserted. The browser review and change-request controls remain available for editorial decisions. Missing usable articles or sufficient relevant photographs produces a visible failure.

## Evidence

- `acceptance/factory-universal/acceptance-20261114-results.json`: complete acceptance matrix, frame counts, hashes, source revisions and QA gates.
- `acceptance/factory-universal/compatibility-20261114.json`: replay against the delivered planner and subject filters.
- `acceptance/factory-universal/contrast-20261114.json`: real lunar images retained and real solar confusers rejected without lowering pixel thresholds; semantic aliases excluded from negative labels.
- `acceptance/factory-universal/runtime-20261114.json`: public HTTP 200, authenticated video byte ranges HTTP 206, exact runtime image/source and storage limits.
- `acceptance/factory-universal/storage-cleanup-20261114.json`: removal of superseded project test outputs, with accepted IDs preserved and no unrelated directories selected.

## Operation and limits

There are no Gemini or paid model API calls. Retained settings and provider credentials remain under `/var/lib/factory-rebuild/secrets/`, mounted read-only. The pinned local visual model is reused; run `sudo python3 factory_universal/setup_models.py` to install or reverify its checksums.

Only this app may be recreated: `sudo docker compose -f factory_universal/compose.yaml up -d --build app`. Check for active jobs first. The media-worker and shared shorts-v2/n8n networks are existing dependencies; do not remove unrelated services or shared directories.

One isolated worker executes jobs, with a 900-second process-group timeout. Before new jobs and at startup, cleanup expires outputs after 30 days, caps this factory outputs at 2 GiB and cache at 512 MiB, and preserves a 2 GiB free-disk reserve. Only exact SQLite-owned UUID directories are eligible. Completed temporary image/audio files are removed. A temporary diagnostic multilingual model was removed.

Focused checks: `sudo docker exec -i factory-universal python3 - < factory_universal/checks.py`. The dated `review_outputs.py` collector verifies recorded jobs without creating or retrying them. Keep failed IDs immutable. Do not rerun old rejected test jobs or restore their expired media.
