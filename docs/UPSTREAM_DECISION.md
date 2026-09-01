# Upstream Decision — Local Semantic Replacement

Last updated: 2026-09-01

## Trigger

Production WF02 currently requires Gemini Free Tier. Fresh production evidence shows:

- `gemini-3.6-flash` can fail with `429 RESOURCE_EXHAUSTED` on Free Tier request quota;
- `gemini-3.5-flash` can simultaneously fail with `503 UNAVAILABLE / high demand`;
- repeated fresh jobs have stopped before TTS for these provider failures.

A quota-limited hosted AI is therefore rejected as a required production dependency.

## Permanent direction

Replace hosted semantic generation with a local semantic engine or deterministic local semantic pipeline that runs within the existing three-service architecture and costs `0 PLN` per video.

Preferred deployment boundary: existing `media-worker`, because it already owns local compute/media primitives and can expose a small local inference HTTP endpoint to n8n without becoming a fourth service.

## Candidate requirements

A candidate is acceptable only when all are true:

- fits 2 vCPU / 3.7 GiB RAM / 2 GiB swap / no GPU;
- persistent model/runtime storage fits current constrained disk or disk is safely reclaimed first;
- supports EN/PL/RU/UK sufficiently for short coherent factual narration;
- accepts supplied retrieved evidence and does not invent unsupported claims;
- produces deterministic/strict structured data compatible with the existing WF02 validator;
- can generate compact visual intent including stock/reference/exact decisions, canonical reference concept intent, and `reference_media_kind`;
- no external semantic request is required at generation time;
- no topic-specific mappings or manual asset hacks are needed;
- cross-topic/cross-language quality is materially acceptable before deployment.

## Evaluation order

1. Inspect available disk and remove only proven disposable caches/artifacts if needed.
2. Prefer a compact multilingual instruction model runnable through a local CPU inference runtime inside media-worker.
3. Benchmark strict JSON/structured output, factual grounding, latency, memory, and four-language quality on a bounded corpus.
4. If the compact model fails quality, test the next feasible local approach; do not deploy a weak model merely because it is local.
5. Only after a candidate passes, update architecture/source-of-truth and implement the production integration.

## Forbidden responses to failure

- restore Gemini as required fallback;
- quota waits/retry loops;
- extra API keys/accounts/projects;
- paid hosted fallback;
- topic-specific prompts/mappings to rescue test cases;
- weakening factual, duration, visual, or render acceptance;
- adding a fourth persistent service merely to avoid integrating local inference cleanly.

## Production acceptance

After local semantic integration, restart frozen CASE 1 `How does a zipper work?` / `en` / `15` from a completely new job. It must pass narration, clean Edge duration, every visual/provenance/content check, ffprobe and human-visible quality on the unchanged runtime before later matrix cases.