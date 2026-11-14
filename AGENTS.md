# Active factory instructions

Start with `docs/CODEX_START_HERE.md` and `factory_universal/README.md`.

The active implementation is `factory_universal/`, deployed from `/opt/factory-universal` as the `factory-universal` service at https://studio.hodor.com.pl/ . Earlier factory-next/factory-v3/Gemini implementations and their old execution plans are historical. Their instructions remain available in Git history; the previous start document is retained under `docs/archive/`.

## Scope and cost

- Maintain the universal topic/language/duration-to-MP4 workflow on EN/PL/RU/UK and 15/30/45/60 seconds.
- Use the retained read-only settings and credentials. Never print plaintext secrets or commit them.
- No Gemini or paid model APIs. Local eSpeak NG, the pinned local visual verifier, and the existing media-worker implement generation.
- Modify only this project and its app service. Leave unrelated host files, n8n workflows, services and credentials alone. Do not globally prune Docker or shared media.
- Cleanup may select only exact UUID directories owned by this factory SQLite database. Preserve the output/cache quotas and free-disk reserve.

## Operation and verification

- Use one short Sentinel call at a time. Run long finite work in the background and follow it through completion. Avoid busy polling and blind repeated side effects.
- No subagents unless the user explicitly authorizes them.
- Check live jobs before submitting more work or recreating the service. Keep failed job IDs immutable; after a diagnosed fix use a new job, with a recorded reason.
- Respect HTTP 429. Do not conceal missing source material by inserting unrelated or repeated assets.
- Preserve whole photographs on a solid matte, complete readable captions, source/media provenance, unique assets and exact frame counts.
- Automated pixel checks are a screen; inspect actual output frames and captions. Never claim owner/HUMAN listening or approval from technical checks or assistant frame review.
- Run `factory_universal/checks.py` inside the runtime. `review_outputs.py` collects the recorded acceptance outputs without creating jobs.

## Git continuity

The delivery branch is `codex/factory-universal-20261112`. The old `codex/factory-rebuild-20261111` branch has separate history; do not force-push it. Commit and publish meaningful changes and evidence, then verify the checkout against the delivery branch. Do not merge or deploy to unrelated production systems. Report committed, deployed and verified states accurately; successful unit checks alone do not establish delivery.
