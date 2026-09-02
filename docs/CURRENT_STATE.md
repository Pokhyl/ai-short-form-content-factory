# Current Project State — Rebuild

Last updated: 2026-09-02

This file is authoritative for branch `rebuild/simple-pipeline`. Repository state overrides chat memory.

## Mandatory protocol

Before EVERY technical response, diagnosis, recommendation, code/config change, deployment, or test:

1. Read `docs/PERMANENT_PROJECT_RULES.md` from GitHub.
2. Read this file from GitHub branch `rebuild/simple-pipeline`.
3. Architecture change: also read `docs/ARCHITECTURE.md`.
4. Milestone/acceptance/gate change: also read `docs/ROADMAP.md` and `docs/PROCESS_GATE.md`.
5. Upstream/provider change: also read `docs/UPSTREAM_DECISION.md`.

## Product

`topic -> factual evidence -> deterministic evidence-backed narration -> local duration preflight -> one continuous natural voice -> timed beats -> deterministic truthful visuals -> render -> human review`

Publishing is outside automatic generation.

## Runtime invariants

Exactly three persistent services:

- `ai-short-form-content-factory-n8n-1`
- `ai-short-form-content-factory-postgres-1`
- `ai-short-form-content-factory-media-worker-1`

Per-video external API cost: `0 PLN`.

Measured VPS:

- 2 vCPU
- 3.7 GiB RAM
- 2.0 GiB swap
- no GPU

## Permanent provider rule

Production MUST NOT require a request-count/rate/quota-limited hosted semantic AI.

Fresh Gemini production evidence included both `429 RESOURCE_EXHAUSTED` and `503 UNAVAILABLE / high demand`.

Do not solve this with waiting, retries, extra keys/accounts/projects, paid fallback or weaker acceptance.

## Local LLM decision — rejected as required critical path

The later compact-local-model direction has also been rejected after actual VPS measurements.

Observed failures:

- Qwen3 1.7B: grounded output possible, but narration length/contract remained unreliable;
- Qwen2.5 3B: constrained fitting damaged natural sentence structure;
- Qwen3 4B: grounded narration possible, but duration fitting failed and memory reached roughly 3.2-3.5 GB RSS;
- Qwen3.5 4B IQ4_XS: roughly 2.5 GB RSS plus material swap during inference;
- continuing to benchmark more general models is classified as model hopping, not architecture work.

All current llama/Qwen benchmark processes have been stopped. Experimental Qwen GGUF files were removed from `/tmp/local-narrator-eval`; disk returned to roughly 6.3 GB free and normal service memory remained available.

Do not resume general-LLM model selection unless the user explicitly reverses this architecture decision.

## Selected critical path — deterministic

### WF02

1. Retrieve bounded factual sources, preferring the requested narration language.
2. Split into atomic evidence units.
3. Deterministically remove neighboring/noisy entities and persist selected evidence/provenance.
4. Compile narration from factual evidence spans only.
5. Allowed compiler operations: source-artifact cleanup, whitespace/punctuation normalization, removal of clearly incidental parenthetical material, linguistically safe clause splitting, evidence-span selection/order, capitalization/final punctuation.
6. Every final narration segment keeps exact evidence IDs/source spans.
7. No generated factual predicates, names, dates, numbers, materials or mechanisms may be added.
8. The old exact `3/5/7/9` narration sentence-count gate is removed. Natural sentence count may vary.
9. Generate multiple deterministic evidence-backed candidate assemblies and use local duration estimation to choose the best fitting one before TTS.

### WF03

Fixed Edge voices remain:

- EN `en-US-AndrewNeural`
- PL `pl-PL-MarekNeural`
- RU `ru-RU-DmitryNeural`
- UK `uk-UA-OstapNeural`

Provider rate/pitch/volume remain default.

Automatic production performs exactly ONE Edge synthesis per job.

No `atempo`, speed correction, silence removal, pause rewrite, padding, scene-level TTS, second fitting synthesis or hidden provider retry.

Measured clean Edge duration is authoritative. A miss fails closed.

Timed beats are created only after voice acceptance and are independent of narration sentence count.

### Duration preflight

Use only already measured clean-Edge calibration data. No new TTS calls for calibration experiments.

The current simple char/sentence estimator is not accepted as final. A combined 160-sample check exposed worst-case errors around 4.5 seconds for EN/UK, which is too weak for reliable one-shot TTS.

Next estimator must use richer deterministic linguistic features and be evaluated out-of-sample. Final measured target gate remains unchanged.

### WF04

A generative visual-planning call is no longer required.

Derive visual lane/query/eligibility from final beat text + evidence + canonical source/entity metadata.

Eligibility remains before SigLIP:

- exact identity match;
- canonical reference provenance + representation form;
- metadata-supported concrete subject for truth-critical stock;
- truthful contextual stock only.

Only eligible candidates reach local relative SigLIP ranking. Empty lane fails closed.

## Existing redesign work on VPS

Uncommitted local rebuild work currently includes:

- `db/migrations/012_staged_semantic_pipeline.sql`;
- updated `db/init/001_init.sql`;
- `tests/staged_pipeline_core.mjs`;
- `tests/staged_pipeline_regression.mjs`.

Migration 012 was already proved on disposable databases both as an upgrade of the current schema and as fresh-init compatibility. It has NOT been applied to production.

The migration keeps legacy historical `planned` rows compatible and introduces new `timed -> visual_planned -> visual_ready` lifecycle states.

The deterministic evidence reducer has been exercised on real historical cases:

- zipper EN15;
- popcorn PL15;
- induction EN15;
- glass RU30;
- Poland UK15;
- Zelensky UK30.

It correctly removed known neighboring/noisy sources such as Quarter-zipper, Genmaicha, V.E.T.O., Wielkopolska/Małopolska where they were not the target.

## Voice issue already repaired

The destructive old `silenceremove` post-processing stage was removed. Edge output now preserves provider timing and is only normalized to 48 kHz stereo PCM WAV.

## Visual issue still unresolved

The old zipper run proved canonical reference-form selection, but a continuous-coil beat still received an unsupported generic drysuit zipper photo. This must be fixed by deterministic evidence/metadata eligibility, never by a zipper-specific patch.

## Frozen product acceptance

CASE 1 remains:

`How does a zipper work? / en / 15`

No later matrix case is accepted before a fresh CASE 1 passes on one unchanged redesigned runtime:

- relevant persisted evidence;
- factual/coherent natural narration;
- local pre-TTS duration candidate accepted;
- exactly one Edge synthesis;
- measured clean Edge duration passes;
- timed beats exactly cover accepted voice;
- every visual intent/provenance/content check passes;
- final ffprobe passes;
- human-visible voice/render quality passes.

First real product failure stops progression and is repaired systemically.

## Immediate next action

Do not benchmark another LLM.

Continue local/disposable implementation in this order:

1. implement deterministic provenance-preserving narration compiler on the six real cases;
2. replace fixed sentence-count validation with natural variable sentence count;
3. build richer clean-Edge duration estimator from existing measured corpus and prove out-of-sample false-safe behavior;
4. combine narration candidates + estimator into a zero-TTS preflight search;
5. implement one-shot WF03 + timed beats;
6. implement deterministic WF04 visual intent/eligibility;
7. full local regression;
8. commit implementation and exact proof;
9. bounded production deploy with rollback evidence;
10. completely fresh CASE 1.