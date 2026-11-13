# Universal MP4 factory — active entry point

The active implementation is `factory_universal/`. Read `factory_universal/README.md` before operating it. The earlier factory-next/factory-v3/Gemini implementation is historical; its previous notes are archived in `docs/archive/CODEX_START_HERE_legacy_20261111.md`.

User requirements: universal topic-driven MP4 generation on EN/PL/RU/UK, no Gemini or paid model APIs, preserve retained settings and credentials without exposing values, control disk growth, and leave unrelated projects alone.

## Runtime

- Server checkout: `/opt/factory-universal`.
- Service/container: `factory-universal`; browser: https://studio.hodor.com.pl/ .
- It reuses `shorts-v2-media-worker-1` and the shared media volume. Only directories whose UUIDs belong to this factory’s SQLite jobs are eligible for output retention cleanup.
- Project settings and provider credentials remain in the existing read-only files under `/var/lib/factory-rebuild/secrets/`.
- Local visual model is pinned and checksum-verified; install/reverify with `sudo python3 factory_universal/setup_models.py`. No model API key is used.

## Verification status

`project_ready=false`: final acceptance is still in progress. PL/RU/UK normal 15-second MP4 jobs completed technical checks on the prior deployed revision. A later source revision improves complete paragraph selection, narration timing, scene allocation, source-specific media queries and storage/time limits. Those changes require an exact-image full acceptance before readiness can be claimed.

- PL receipt job: `4c3cca52-d812-4f59-9ac0-0a61a42e8929`.
- RU receipt job: `ae5a45a1-ebf4-41b5-a018-3be9003bf4c3`.
- UK receipt job: `581e0770-8761-41af-b2e1-c30fca6a84dd`.
- Public page and health endpoint returned HTTP 200 with the expected factory content.
- Focused checks passed for paragraph filtering, proportional image/voice layouts, Cyrillic stress marks, local voice timing, scoped retention, successful supervised worker exit, timeout of its whole process group, and preservation of unrelated files.

Required remaining acceptance: deploy the pending source only after active jobs finish; generate and inspect fresh MP4s on all four languages and different topics; verify 15/30/45/60-second paths, complete decode and per-image audit; update GitHub source and final receipts; remove rejected project test media. Do not label one successful render as a finished universal factory.

## Operation

Use the existing checkout and single worker. Check an existing live job before creating another. Respect explicit HTTP 429 responses and use the cached source data for diagnostics. Build/recreate only this app with `sudo docker compose -f factory_universal/compose.yaml up -d --build app`. The old Gemini terminal jobs must not be retried.
