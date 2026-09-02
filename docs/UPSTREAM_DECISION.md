# Upstream Decision — Local Semantic Replacement

Last updated: 2026-09-02

## Trigger

Production WF02 currently requires Gemini Free Tier. Fresh production evidence showed both:

- `gemini-3.6-flash` -> `429 RESOURCE_EXHAUSTED` on Free Tier request quota;
- `gemini-3.5-flash` -> `503 UNAVAILABLE / high demand`.

A quota-limited hosted semantic AI is rejected as a required production dependency.

## Rejected approach: local model behind the old WF02 contract

The first local-model experiment preserved the old monolithic WF02 request: a large source dump plus narration, evidence-linking, duration-shape and visual-planning instructions in one response.

Fresh evaluation proved that this was the wrong workload for the VPS, not merely the wrong model:

- zipper EN15 old request contained about 4.7k input tokens before generation;
- the response contract also required exact script tokens, claim support and six visual-plan objects;
- Qwen3 0.6B / 1.7B fit memory individually, but the full old workload was too slow/brittle for production;
- complex JSON-schema/GBNF decoding added further sampler/latency problems.

Do not continue model hopping against that monolithic contract. It is superseded.

## Selected systemic direction

Keep exactly three persistent services and move to a staged semantic boundary:

1. deterministic retrieval and evidence reduction in n8n;
2. one compact local narration call using only a small persisted evidence packet;
3. real clean-Edge synthesis and measured duration;
4. at most one bounded text-fit rewrite against the same evidence if measured duration misses the unchanged gate;
5. deterministic timed-beat creation only after final narration/voice are accepted;
6. a separate compact local visual-intent call on the final beats;
7. deterministic candidate eligibility + local visual ranking;
8. render + review.

The local model is no longer responsible for research, final asset selection, duration measurement, evidence storage and visual planning simultaneously.

## Evidence boundary

Raw retrieved source text is split deterministically into atomic evidence units. The reducer selects a small diverse packet before any generative call.

Normal maximum selected evidence count is two units per requested narration sentence:

- 15 s: 3 sentences -> max 6 selected units;
- 30 s: 5 sentences -> max 10;
- 45 s: 7 sentences -> max 14;
- 60 s: 9 sentences -> max 18.

Selected evidence and provenance must be persisted in PostgreSQL. The narration model may cite only those selected IDs.

## Narration boundary

The compact local narration request contains topic, target language, duration/length guidance and selected evidence only.

It returns narration + sentence-to-evidence references only. It does not return visual scenes.

Actual Edge duration remains the hard timing signal. Clean-Edge calibration is planning guidance, not a reason to impose an ultra-narrow character grammar on the model.

One bounded text-fit pass is allowed only after a real measured duration miss. It rewrites content, never audio speed/timing, and must pass the same evidence/language validator. No unbounded retry loop exists.

## Visual boundary

Visual intent is generated only after final script and measured voice are accepted.

The visual-intent request receives final timed beats and only relevant evidence/canonical context. It returns mode/query/brief/reference form/concrete subject/exact identity plus evidence references for fact-critical specificity.

The semantic model never selects the final media file.

WF04 continues to enforce deterministic lanes:

- exact identity eligibility;
- canonical technical-reference provenance + `reference_media_kind`;
- metadata-supported `concrete_subject` for truth-critical stock;
- relative local image ranking only after eligibility.

Empty eligible lanes fail closed.

## Runtime / memory boundary

The local semantic engine runs inside existing `media-worker` as bounded compute, not a fourth service.

The VPS is 2 vCPU / 3.7 GiB RAM / 2 GiB swap / no GPU. Therefore local semantic inference and SigLIP must share one heavyweight-compute gate and must not remain concurrently resident when that would exceed measured memory.

Model selection resumes only against the new compact contracts. The candidate must pass cross-topic and EN/PL/RU/UK quality before deployment.

## Forbidden responses to failure

- restore Gemini or another quota-limited semantic fallback;
- quota waits/retry loops;
- extra API keys/accounts/projects;
- paid hosted fallback;
- topic-specific prompts/mappings;
- weakening factual/duration/visual/render gates;
- forcing a weak local model into production merely because it is local;
- adding a fourth persistent service to avoid fixing boundaries.

## Production acceptance

After the staged architecture is implemented and regression-tested, restart frozen CASE 1 `How does a zipper work? / en / 15` from a completely new job. It must pass evidence, narration, natural voice/duration, timed beats, visual intent, every selected asset/provenance/content check, ffprobe and human-visible quality on one unchanged runtime.