# Process Gate — Rebuild

Last updated: 2026-09-02

`docs/CURRENT_STATE.md` is the operational source of truth.

## Mandatory process

Before every technical action, read fresh GitHub `docs/PERMANENT_PROJECT_RULES.md` and branch `rebuild/simple-pipeline/docs/CURRENT_STATE.md`. Read additional scope docs as required there.

No topic-specific hacks, acceptance bypasses, magic thresholds, query rewrites for one case, manual asset substitutions, sleeps/retries to hide provider quotas, extra keys/accounts/projects, paid semantic fallback, repeated hosted TTS fitting, or weak local-model deployment merely to remove Gemini.

## Active gate — staged zero-quota semantic architecture

The old monolithic WF02 semantic boundary is rejected. Do not spend more time model-hopping against the old multi-thousand-token request.

The next accepted production architecture is:

`retrieval -> deterministic persisted evidence packet -> compact local narration -> local duration preflight/text fit -> exactly one natural Edge synthesis -> timed beats -> compact local visual intent -> deterministic visual eligibility/ranking -> render -> review`

Exactly three persistent services and 0 PLN per-video external API cost remain mandatory.

## Required implementation sequence

1. Add durable evidence/provenance schema.
2. Change scene lifecycle so WF03 can create `timed` narration/timing rows before visual fields exist, while DB constraints require complete visual intent before visual-ready state.
3. Build deterministic evidence reducer and compact narration evaluation contract. Do not feed raw source dumps to the local model.
4. Evaluate feasible local multilingual narration candidates on materially different topics and EN/PL/RU/UK using the compact contract and unchanged factual validator principles.
5. Build deterministic local duration preflight from fixed Edge voice/language calibration and measured clean production durations.
6. Any bounded evidence-grounded text-fit rewrite must happen BEFORE TTS and must not consume a hosted TTS request.
7. Automatic production may call Edge exactly once per job. No second synthesis for duration fitting and no hidden TTS retry loop.
8. If the single measured Edge duration misses the quality gate, fail closed and retain the measurement only as future calibration data.
9. Create timed beats only from final accepted script/voice.
10. Build compact visual-intent contract on final beats and relevant evidence only.
11. Enforce stock/reference/exact eligibility before local ranking; truth-critical stock requires metadata-supported `concrete_subject`.
12. Add heavyweight-compute serialization/model-lifetime controls in media-worker and prove semantic/SigLIP overlap cannot exhaust RAM/swap.
13. Run full static/behavior/Code-node/Studio/WF04/R8/media-worker/render/diff/database migration gates.
14. Commit implementation and update GitHub source-of-truth with exact hashes/proof.
15. Deploy boundedly with rollback evidence and exact-published proof.
16. Start one completely fresh frozen CASE 1: `How does a zipper work? / en / 15`.
17. CASE 1 passes only if evidence, narration, local duration preflight, exactly one natural clean Edge synthesis, measured duration, timed beats, visual intent, every selected visual/provenance/content check, final ffprobe and human-visible quality all pass.
18. First real product failure stops progression and is repaired systemically before any later case.

## Explicit non-goals

Do not:

- add another persistent model service;
- keep Gemini as emergency fallback;
- preserve the old exact giant JSON/GBNF response contract just because tests already exist;
- force visual planning before final voice duration is known;
- keep evidence only in transient n8n execution data;
- use SigLIP as a truth oracle before deterministic eligibility;
- loosen acceptance to make a local model appear successful;
- call Edge twice merely to learn that the first narration was too long or too short.