# Architecture — Clean Rebuild

Last updated: 2026-09-02

`docs/CURRENT_STATE.md` is the operational source of truth.

## Product

`topic -> factual evidence -> deterministic evidence-backed narration -> local duration preflight -> one natural voice -> timed beats -> deterministic visual intent + real media -> render -> human review`

Publishing remains outside automatic generation.

## Hard runtime invariants

Exactly three persistent services:

1. `n8n`
2. `postgres`
3. `media-worker`

Per-video external API cost remains `0 PLN`.

Production may not require Gemini or any other request-count/rate/quota-limited hosted semantic AI.

Production also may not require a general-purpose local generative LLM. The 2 vCPU / 3.7 GiB RAM VPS is not a reliable quality boundary for arbitrary multilingual generation, and model-hopping is explicitly rejected.

## Core correction

The critical path no longer asks a generative model to write narration or visual plans.

Fresh local measurements showed that even compact 3B/4B models either broke narration/length constraints or consumed most of the VPS memory while still failing duration-fit. A general local LLM therefore does not solve the product reliability problem.

The replacement is deterministic and evidence-first.

## WF01 — intake

Unchanged:

- validate `topic`, `language`, `duration`;
- create exactly one durable job;
- invoke WF02.

## WF02 — research + deterministic narration compiler

### A. Retrieval

Retrieve bounded factual sources for the immutable topic. Prefer factual material already available in the requested narration language. Wikipedia/MediaWiki is one adapter, not a semantic engine. Wikidata/Wikimedia may provide canonical identity/provenance.

If sufficient target-language factual evidence cannot be obtained, fail closed. Do not invent or silently translate facts with an unproven generative model.

### B. Evidence reduction

Split source text into atomic evidence units and deterministically remove neighboring/noisy entities.

Persist every selected unit with exact source/title/URL/language/passage locator/text/rank.

The reducer must be evaluated cross-topic. Topic-specific allowlists, manual mappings and threshold weakening are forbidden.

### C. Evidence-backed narration compiler

Narration is compiled from selected factual source spans rather than generated from scratch.

Allowed operations are deterministic and provenance-preserving:

- remove citation/source artifacts;
- normalize whitespace/punctuation;
- remove clearly parenthetical or incidental material without changing the remaining claim;
- split a source sentence only at a linguistically safe clause boundary;
- select and order complete evidence-backed clauses/sentences;
- capitalize/finalize punctuation without changing factual content.

Every final narration segment keeps the exact evidence IDs and source spans from which it was compiled.

The critical path may not add new names, numbers, dates, materials, mechanisms or factual predicates that do not occur in selected evidence.

### D. No fixed sentence-count gate

The previous exact `3/5/7/9` sentence requirement for `15/30/45/60` seconds is rejected. It was an internal implementation constraint, not a product requirement, and it encouraged unnatural prose.

Narration may use the number of natural sentences required by the evidence and duration. Product acceptance is based on factuality, coherence, natural speech and measured duration.

### E. Duration candidate selection

WF02 produces multiple deterministic evidence-backed candidate assemblies from the same selected evidence and chooses the candidate whose locally estimated natural Edge duration is closest to the requested target while preserving the required factual/mechanism coverage.

This search is local and does not consume TTS requests.

No candidate inside the pre-TTS acceptance band means fail closed before Edge.

## WF03 — exactly one natural Edge synthesis + timed beats

Fixed voices remain:

- EN `en-US-AndrewNeural`
- PL `pl-PL-MarekNeural`
- RU `ru-RU-DmitryNeural`
- UK `uk-UA-OstapNeural`

Provider rate/pitch/volume remain default.

Forbidden:

- `atempo`;
- time-stretch;
- rate correction;
- pause rewrite;
- silence removal;
- padding;
- scene-by-scene TTS;
- a second automatic TTS synthesis for fitting;
- hidden provider retry loops.

Automatic production performs exactly one Edge synthesis for the job.

The single clean output is measured once. Measured duration is authoritative. A miss fails the job; it does not trigger another synthesis.

Only after voice acceptance, deterministically create the requested transport beats/scenes and timing that exactly covers the measured voice track. Beat count is independent of narration sentence count.

## Local duration estimator

The estimator is a deterministic voice/language model trained only from already measured clean-Edge samples. No additional TTS calls are made for calibration experiments.

It is used to rank/accept candidate evidence assemblies before the single TTS call. The estimator must be validated out-of-sample and may use richer linguistic features than raw character count (word length distribution, punctuation/pause features, numbers/abbreviations and language-specific orthographic features).

Do not claim a safe band from a global worst-case residual if that makes almost every valid narration impossible. Instead define the pre-TTS operating band from measured out-of-sample error and verify its false-safe rate on the retained corpus. Final measured ±10% duration acceptance remains unchanged.

## WF04 — deterministic visual intent + sourcing

WF04 receives final timed beats and their evidence provenance.

A generative visual-planning call is not required.

For every beat, derive search/eligibility data deterministically from:

- beat text;
- supporting evidence text;
- canonical source title/entity identifiers;
- source type/provenance;
- extracted target-language/English keywords and named entities available from the factual source metadata.

Lanes remain:

- `exact`: canonical identity required;
- `reference`: canonical factual/technical source, including required media form when known;
- `stock`: contextual or concrete subject only when metadata can substantiate the requested subject.

The final asset is never chosen by a language model.

Eligibility happens before ranking:

- exact identity must match canonical identity;
- reference candidate must match canonical provenance and representation form;
- truth-critical stock metadata must support the concrete subject;
- contextual stock substitution must remain truthful.

Only eligible candidates reach local SigLIP relative ranking. Empty eligible lanes fail closed.

## WF05 — render

Consumes only accepted artifacts:

- one accepted continuous voice track;
- final timed beats;
- one accepted visual per beat.

Output remains 1080x1920, H.264/yuv420p 30fps, AAC 48 kHz stereo. ffprobe validates the result before `review_ready`.

## WF06 — human review

Generation stops at `review_ready`. Human review remains a separate boundary.

## Durable state

PostgreSQL owns:

- job state;
- selected evidence/provenance;
- compiled narration and exact evidence spans;
- measured voice duration/path;
- timed beats;
- deterministic visual intent/eligibility provenance;
- selected assets;
- render/review state.

`scenes` support `timed -> visual_planned -> visual_ready`; legacy historical `planned` remains compatible.

## Heavy compute

With the required generative LLM removed from critical path, heavyweight model overlap is reduced. SigLIP remains bounded local compute inside `media-worker` and must not cause uncontrolled concurrent RAM/swap use.

## Acceptance

Fresh CASE 1 remains:

`How does a zipper work? / en / 15`

It passes only when one unchanged runtime proves:

- relevant persisted evidence;
- factual/coherent deterministic narration;
- local pre-TTS duration candidate passes;
- exactly one Edge synthesis;
- measured clean Edge duration inside the unchanged target gate;
- timed beats exactly cover accepted voice;
- deterministic visual intent is evidence-consistent;
- every selected visual/provenance/content check passes;
- final ffprobe passes;
- human-visible voice/render quality passes.

First real product failure stops progression and is repaired systemically.