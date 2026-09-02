# Process Gate — Rebuild

Last updated: 2026-09-02

`docs/CURRENT_STATE.md` is the operational source of truth.

## Mandatory process

Before every technical action, read fresh GitHub `docs/PERMANENT_PROJECT_RULES.md` and branch `rebuild/simple-pipeline/docs/CURRENT_STATE.md`. Read additional scope docs as required there.

No topic-specific hacks, acceptance bypasses, manual asset substitutions, quota waits/retries, extra keys/accounts/projects, paid semantic fallback, repeated hosted TTS fitting, or model hopping.

## Active gate — deterministic zero-quota critical path

The old monolithic Gemini WF02 is rejected.

The later attempt to preserve a required compact local generative LLM is also rejected after measured 3B/4B failures on the actual VPS.

Accepted direction:

`retrieval -> persisted evidence -> deterministic evidence-backed narration compiler -> local duration candidate selection -> exactly one natural Edge synthesis -> timed beats -> deterministic visual intent/eligibility -> local ranking -> render -> review`

Exactly three persistent services and 0 PLN per-video external API cost remain mandatory.

## Required implementation sequence

1. Keep/prove durable evidence/provenance schema and staged scene lifecycle.
2. Finish deterministic evidence reducer on materially different real topics.
3. Implement provenance-preserving narration compiler from source sentences/clauses.
4. Remove exact `3/5/7/9` sentence count from narration acceptance; sentence count is not a product gate.
5. Build richer local Edge-duration estimator from already measured clean-Edge corpus only; do not generate new TTS calibration traffic.
6. Generate multiple deterministic evidence-backed narration assemblies locally and choose the best duration-fit candidate without TTS.
7. Require factual/mechanism coverage and exact evidence provenance for the selected narration.
8. Automatic production may call Edge exactly once per job. No second synthesis for fitting and no hidden retry loop.
9. A measured duration miss fails closed and becomes future calibration evidence only.
10. Create timed beats only after accepted measured voice; beat count is independent of sentence count.
11. Implement deterministic visual intent from beat/evidence/canonical metadata; no required generative visual-planning call.
12. Enforce exact/reference/stock eligibility before SigLIP ranking.
13. Truth-critical stock requires metadata support for the concrete subject; empty eligible lane fails closed.
14. Run full database/static/behavior/Code-node/Studio/WF04/R8/media-worker/render/diff gates.
15. Commit implementation and update GitHub source-of-truth with exact proof.
16. Deploy boundedly with rollback evidence.
17. Start one completely fresh frozen CASE 1: `How does a zipper work? / en / 15`.
18. CASE 1 must pass evidence, deterministic narration, preflight, exactly one natural Edge call, measured duration, timed beats, visual provenance/content, ffprobe and human-visible quality.
19. First real product failure stops progression and is fixed systemically.

## Explicit non-goals

Do not:

- benchmark more general LLMs as the main narration path;
- add a fourth persistent model service;
- keep Gemini as fallback;
- restore a fixed narration sentence count merely to simplify prompting;
- use SigLIP as a truth oracle;
- loosen the final duration or visual gates;
- call Edge more than once to search for a fitting script.