# Upstream Decision — Deterministic Semantic Critical Path

Last updated: 2026-09-02

## Trigger

Production Gemini Free Tier is not reliable enough for a required dependency:

- `gemini-3.6-flash` produced `429 RESOURCE_EXHAUSTED`;
- `gemini-3.5-flash` produced `503 UNAVAILABLE / high demand`.

Quota waits, retries, extra accounts/keys, model hopping and paid fallback are forbidden.

## Rejected approach 1 — local model behind old WF02

The old request mixed research, narration, evidence linking, duration control and visual planning. It was several thousand input tokens and was too slow/brittle for small local models.

## Rejected approach 2 — required compact general local LLM

The boundary was reduced to compact narration-only prompts and tested again on the real 2 vCPU / 3.7 GiB VPS.

Measured results still failed the product requirement:

- Qwen3 1.7B produced valid-looking prose but did not reliably control narration length;
- Qwen2.5 3B broke natural sentence structure during constrained fitting;
- Qwen3 4B produced grounded text but failed bounded duration fitting and consumed roughly 3.2-3.5 GB RSS;
- Qwen3.5 4B IQ4_XS consumed roughly 2.5 GB RSS plus material swap during inference;
- repeated model benchmarking did not solve the one-shot-TTS duration/reliability boundary.

Therefore a general-purpose generative LLM is rejected as a REQUIRED production dependency on this VPS. Do not continue model hopping.

## Selected systemic direction

Critical path:

1. deterministic public factual retrieval;
2. deterministic evidence reduction and durable provenance;
3. deterministic evidence-backed narration compilation from source spans;
4. richer local duration estimation using existing clean-Edge measurements;
5. local candidate assembly/search with zero TTS calls;
6. exactly one automatic Edge synthesis per video;
7. measured duration acceptance once;
8. deterministic timed beat creation;
9. deterministic visual intent from beat/evidence/canonical metadata;
10. deterministic exact/reference/stock eligibility;
11. SigLIP relative ranking only after eligibility;
12. render + human review.

## Narration boundary

Narration is not free-form generation.

The compiler may only select, normalize, safely shorten and order factual source clauses/sentences while preserving exact evidence provenance. New factual predicates, identities, dates, numbers, materials and mechanisms may not be invented.

The exact `3/5/7/9` narration sentence-count requirement is removed. It was an internal implementation constraint, not a product requirement. Natural sentence count may vary.

## Duration boundary

Edge may be called exactly once automatically for a job.

Before Edge, candidate narration assemblies are evaluated locally against an empirical fixed-voice estimator using already measured clean-Edge samples. No new TTS calls are spent on calibration experiments.

The estimator chooses among evidence-backed candidates; it does not rewrite audio or create a hidden provider search loop.

The measured Edge output is authoritative. A miss fails closed and does not trigger another synthesis.

## Visual boundary

A generative visual-plan call is no longer required.

Visual lane/query/eligibility data is derived from final beat text, supporting evidence, canonical source titles/entity IDs and media metadata.

Final assets remain deterministic-eligibility-first:

- exact identity must match canonical identity;
- technical/reference media must match canonical provenance and representation form;
- truth-critical stock metadata must substantiate its concrete subject;
- contextual stock substitutions must remain truthful.

Only eligible candidates reach local SigLIP relative ranking.

## Provider-call budget

For Edge voice:

- maximum automatic synthesis count per job: `1`;
- no duration-fitting retry;
- no scene-by-scene TTS;
- no hidden retry around provider limits.

## Forbidden responses to failure

- restore Gemini or another quota-limited semantic fallback;
- benchmark more general LLMs as the critical narration path;
- quota waits/retry loops;
- extra keys/accounts/projects;
- paid hosted fallback;
- topic-specific mappings/prompts;
- weakening factual/duration/visual/render gates;
- repeated Edge synthesis;
- adding a fourth persistent service merely to avoid fixing boundaries.

## Production acceptance

After deterministic narration/duration/visual planning is implemented and fully regression-tested, restart frozen CASE 1 `How does a zipper work? / en / 15` from a completely new job. It must pass factual evidence, natural narration, one-shot Edge duration, timed beats, every selected visual/provenance/content check, ffprobe and human-visible quality on one unchanged runtime.