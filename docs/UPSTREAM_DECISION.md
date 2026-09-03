# Upstream Decision — Product-First V4

Last updated: 2026-09-03

## Trigger

The project previously tried to replace semantic planning with deterministic evidence/visual heuristics because quota-limited hosted AI was unreliable and small local models performed poorly on the VPS.

That architecture reached machine `review_ready` but failed human review badly: unnatural spoken encyclopedia text and irrelevant cooking/fire footage passed the machine gates.

Therefore the next redesign must not invent another bespoke semantic approximation.

## Research decision

A broad set of open-source short-video projects was reviewed before implementation, including MoneyPrinterTurbo, ShortGPT, AI Shorts Generator, Short Video Maker, OpenNolan, VML and Remotion-based faceless-video projects.

The common architecture is:

`semantic script/storyboard -> TTS -> actual-audio transcription/alignment -> scene-specific assets -> normal edit/render -> preview/human review`

V4 adopts this common pattern.

## Primary upstream foundation

MoneyPrinterTurbo is the primary commodity-video foundation.

Pinned upstream:

- repository: `harry0703/MoneyPrinterTurbo`;
- commit: `cbbb366393105d5cefc254dc9ed492d43da0711b`;
- version: `1.3.6`;
- license: MIT.

Focused upstream tests on the exact pin passed: 316 tests + 69 subtests, 7 skipped, 0 failures.

V4 may adapt/reuse its:

- LLM provider adapters, including Ollama/OpenAI-compatible configuration;
- Edge TTS service;
- faster-whisper subtitle service;
- Pexels/Pixabay/Coverr material retrieval/cache;
- video normalization/composition/render utilities.

Do not fork or rewrite these layers unless a concrete V4 product requirement proves a gap.

## V4-owned boundary

The project-specific code should remain thin and own only what upstream projects cannot know about our product:

- factual research/evidence contract;
- structured semantic director schema;
- spoken-text safety boundary;
- scene representation routing (`exact_media`, `stock`, `diagram`, `screen_text`, optional image generation);
- relevance/review workflow;
- later minimal persistence/orchestration adapter.

## Semantic model decision

A semantic director is required because the failed architecture proved that token overlap/thresholds are not a substitute for coherent script + storyboard generation.

The provider is pluggable.

Preferred zero-variable-cost path is Ollama or another local/open-source model on hardware capable of running a sufficiently strong model. MoneyPrinterTurbo already supports Ollama through its provider layer.

Do not force a weak 1.7B/3B/4B general model onto the current 2 vCPU / 3.7 GiB VPS. Previous measurements already rejected that hardware/model combination for quality reasons.

Optional hosted/BYOK providers may be used for development comparison, but no paid-per-video provider becomes mandatory and no quota-limited free tier is the only production path.

## Speech normalization decision

No single mature open-source text-normalization package was found that fully covers EN/PL/RU/UK written-form-to-spoken-form requirements.

Therefore the semantic director is responsible for emitting spoken-form text in the target language. The V4 speech layer is a small safety/validation boundary using standard Unicode handling and rejecting ambiguous written forms before TTS; it is not a new topic dictionary or semantic rewriting engine.

## Visual decision

MoneyPrinterTurbo stock retrieval is reused only for scenes explicitly marked `stock`.

Technical/mechanism scenes use other explicit modes such as exact factual media or code/motion graphics. MPT material retrieval is not allowed to act as a universal fallback.

## Production decision

Semantic-v3 production remains frozen as rollback/reference. V4 must reach direct CLI `human_approved` before any production orchestration deployment.