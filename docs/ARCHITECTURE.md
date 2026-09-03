# Architecture — Clean Rebuild

Last updated: 2026-09-03

`docs/CURRENT_STATE.md` is the operational source of truth. `docs/VISUAL_SEGMENTATION_DESIGN.md` defines the detailed semantic visual contract.

## Product

`topic -> factual evidence -> deterministic evidence-backed narration -> local duration preflight -> exactly one natural Edge voice -> timed beats -> deterministic semantic visual segments -> truthful real-media eligibility -> local SigLIP ranking + perceptual identity -> global visual-shot assignment -> pre-render visual gate -> independent subtitle + visual timelines -> render-v3 -> post-render visual-state gate -> human review`

Publishing remains outside automatic generation.

## Hard runtime invariants

Exactly three persistent services:

1. `n8n`
2. `postgres`
3. `media-worker`

Per-video external API cost remains `0 PLN`.

Production may not require Gemini or any other request-count/rate/quota-limited hosted semantic AI.

Production also may not require a general-purpose local generative LLM. The 2 vCPU / 3.7 GiB RAM VPS is not a reliable quality boundary for arbitrary multilingual generation, and model-hopping is explicitly rejected.

Automatic production performs exactly one Edge synthesis per job. Do not solve failures with retry/quota sleeps, extra accounts/keys, paid fallback, topic-specific patches, acceptance bypasses or threshold weakening.

## Core correction

The critical path does not ask a generative model to write narration or visual plans.

Narration is deterministic and evidence-first. Visual planning is also deterministic and provenance-driven.

A second architectural correction separates subtitle/voice timing from visual semantics:

`timed beat != visual scene`.

Timed beats are transport units for subtitles and accepted voice timing. They do not automatically create independent media-search obligations. Visual structure is derived after voice acceptance by deterministic semantic segmentation over existing timed-beat boundaries.

## WF01 — intake

Unchanged:

- validate `topic`, `language`, `duration`;
- create exactly one durable job;
- invoke WF02.

## WF02 — research + deterministic narration compiler

### A. Retrieval

Retrieve bounded factual sources for the immutable topic. Prefer factual material already available in the requested narration language. Wikipedia/MediaWiki is one factual adapter, not a semantic engine. Wikidata/Wikimedia may provide canonical identity/provenance.

If sufficient factual evidence cannot be obtained under the bounded multilingual contract, fail closed. Do not invent or silently translate facts with an unproven generative model.

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

WF02 produces multiple deterministic evidence-backed candidate assemblies from the same selected evidence and chooses the candidate whose locally estimated natural Edge duration is closest to the requested target while preserving required factual/mechanism coverage.

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

The single clean output is measured once. Measured duration is authoritative. A miss fails the job; it does not trigger another synthesis.

Only after voice acceptance, deterministically create timed beats that exactly cover the measured voice track. Beat count is independent of narration sentence count and independent of later visual segment count.

## Local duration estimator

The estimator is a deterministic voice/language model trained only from already measured clean-Edge samples. No additional TTS calls are made for calibration experiments.

It is used to rank/accept candidate evidence assemblies before the single TTS call. The estimator must be validated out-of-sample and may use richer linguistic features than raw character count.

Do not claim a safe band from a global worst-case residual if that makes almost every valid narration impossible. Define the pre-TTS operating band from measured out-of-sample error and verify its false-safe rate on the retained corpus. Final measured ±10% duration acceptance remains unchanged.

## WF04 — semantic visual segmentation + truthful sourcing

WF04 receives the accepted voice timing, final timed beats and their evidence provenance.

### A. Semantic segmentation

Deterministically group adjacent timed beats into semantic visual segments. Segment boundaries may occur only on existing timed-beat boundaries.

A segment is one visual obligation by default. Elapsed time alone may not create additional shots.

The quality-constrained maximum is:

`effective_max_segment_seconds = min(8.5, accepted_voice_duration * 0.34)`.

This does not restore a fixed-duration visual cadence. Different content with the same duration may produce different segment counts. If one timed beat itself exceeds the effective cap, fail closed instead of splitting that beat merely to satisfy the visual gate.

An additional shot may be introduced only by a future deterministic semantic or representation transition, never by a hard `N seconds = new visual` rule.

### B. Visual intent and eligibility

For every semantic segment derive search/eligibility data deterministically from:

- segment narration;
- supporting evidence text/IDs;
- canonical factual source title/entity identifiers;
- source type/provenance;
- extracted target-language/English keywords and named entities available from factual metadata.

Lanes remain conceptually:

- `exact`: canonical identity required;
- `reference`: canonical factual/technical source, including required representation when known;
- `stock`: contextual/concrete subject only when metadata substantiates the requested subject.

The final asset is never chosen by a language model.

Eligibility happens before ranking:

- exact identity must match canonical identity;
- reference candidate must match canonical provenance/representation requirements;
- truth-critical stock metadata must support the concrete subject;
- contextual stock substitution must remain truthful.

Only eligible candidates reach local SigLIP relative ranking. Empty eligible lanes fail closed.

### C. Perceptual assignment

Global shot assignment uses local rank plus perceptual identity rather than file-name uniqueness.

Product-visible diversity is enforced through perceptual clusters and the rendered result. Reusing the same truthful asset is allowed when the sequence remains within the unchanged quality constraints.

Semantic-v3 pre-render gates include:

- no adjacent duplicate perceptual cluster;
- max cluster occurrence `2`;
- max cluster duration share `0.34`;
- required rendered-state count derived from shot count and max occurrence;
- non-finite/missing quality values fail closed.

There is no hard maximum shot duration of five seconds. A proven disposable render accepted 6-second shots while preserving all perceptual gates.

## WF05 — independent-timeline render-v3

WF05 consumes only accepted artifacts:

- one accepted continuous voice track;
- final timed beats for subtitles/voice timing;
- durable semantic visual segments;
- durable visual shots with their own contiguous visual timeline;
- persisted semantic-v3 pre-render quality proof.

Subtitle timing and visual-shot timing are independently validated and must each cover the accepted continuous voice track.

`/render-v3` renders the visual-shot timeline while burning subtitles from the timed-beat timeline.

Output remains:

- 1080x1920;
- H.264/yuv420p;
- 30 fps;
- AAC 48 kHz stereo.

ffprobe validates container/video/audio output. Rendered midpoint frames are independently clustered after rendering and must satisfy the same actual-state adjacency/occurrence/duration-share constraints before `review_ready`.

## WF06 — human review

Generation stops at `review_ready`. Human review remains a separate product boundary.

A machine PASS never changes the M8 human-accepted count until the user watches the exact fresh video and accepts it.

## Durable state

PostgreSQL owns:

- job state;
- selected evidence/provenance;
- compiled narration and exact evidence spans;
- measured voice duration/path;
- timed beats;
- semantic visual segments;
- visual shots and their independent timeline;
- media-library asset identity/provenance;
- selected visual quality metrics;
- render/review state.

Semantic-v3 adds the durable entities:

- `visual_segments`;
- `visual_shots`;
- `media_library_assets`.

Legacy scene/visual state remains historical compatibility data; semantic-v3 must not reintroduce `one timed beat = one visual obligation`.

## Heavy compute

With the required generative LLM removed from critical path, heavyweight model overlap is reduced. SigLIP remains bounded local compute inside `media-worker` and must not cause uncontrolled concurrent RAM/swap use.

## Acceptance

Semantic-v3 deployment may proceed only after the exact implementation is synchronized to GitHub, pre-deploy gates pass, and a bounded rollback snapshot exists.

The first production proof after deploy must be a completely fresh job and must prove in one unchanged runtime:

- relevant persisted evidence;
- factual/coherent deterministic narration;
- local pre-TTS duration candidate passes;
- exactly one Edge synthesis;
- measured clean Edge duration inside the unchanged target gate;
- timed beats exactly cover accepted voice;
- deterministic semantic visual segments cover the same voice timeline;
- truthful eligibility and local SigLIP ranking;
- durable visual-shot sequence passes pre-render perceptual gates;
- render-v3 passes actual post-render visual-state gates;
- ffprobe validates the final MP4;
- human-visible voice/render quality is reviewed by the user.

First real product failure stops progression and is repaired systemically. No topic-specific patch or threshold weakening is allowed.