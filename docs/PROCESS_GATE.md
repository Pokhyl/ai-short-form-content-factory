# Process Gate — Rebuild

Last updated: 2026-09-01

`docs/CURRENT_STATE.md` is the operational source of truth.

## Mandatory process

Before every technical action, read fresh GitHub `docs/PERMANENT_PROJECT_RULES.md` and branch `rebuild/simple-pipeline/docs/CURRENT_STATE.md`. Read additional scope docs as required there.

No topic-specific hacks, acceptance bypasses, magic thresholds, query rewrites for one case, manual asset substitutions, sleeps/retries to hide provider quotas, extra keys/accounts/projects, or paid fallback.

## Active gate — remove hosted quota dependency

Current production semantic path is blocked by Gemini Free Tier `429 RESOURCE_EXHAUSTED` and `503 UNAVAILABLE`. This is classified as an architecture reliability failure because a quota-limited hosted AI remains required.

The next accepted change must remove Gemini / quota-limited hosted semantic AI from the REQUIRED generation path while preserving:

- 0 PLN per-video API cost;
- exactly three persistent services;
- factual grounding;
- EN/PL/RU/UK;
- natural Edge timing/voice;
- current visual truth and render gates.

## Required sequence

1. Read-only VPS/model feasibility probes.
2. Prove candidate local semantic engine on materially different topics and all four languages against the existing structured WF02 contract.
3. Reject any candidate that cannot meet factual/structured quality; do not compensate with case-specific production rules.
4. Document selected architecture decision in `ARCHITECTURE.md`, `UPSTREAM_DECISION.md`, and `CURRENT_STATE.md` before production mutation.
5. Implement boundedly inside the existing three-service topology.
6. Run full local static/behavior/Code-node/Studio/WF04/R8/media-worker/render/diff gates.
7. Commit implementation and update GitHub source-of-truth.
8. Deploy boundedly with rollback evidence and exact-published proof.
9. Start one completely fresh frozen CASE 1: `How does a zipper work?` / `en` / `15`.
10. CASE 1 passes only if narration facts/coherence, natural clean Edge duration, every selected visual/provenance/content check, final ffprobe and human-visible voice/render quality all pass.
11. First real product failure stops progression and must be repaired systemically before any later case.