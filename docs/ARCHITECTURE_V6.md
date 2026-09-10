# Architecture V6 — visual-facts-first editorial pipeline

Date: 2026-09-10
Status: implementation in progress; production remains V5 until full verification and controlled deployment.

## Product contract unchanged

Input remains only `topic + language + duration` through WF01. n8n remains the mandatory orchestrator. PostgreSQL remains product state. The stack remains free/self-hosted with existing free media/model/TTS routes. Output remains natural-rate continuous narration and 9:16 MP4. Failed/rejected jobs remain immutable. Exact MP4 still requires assistant visual review and explicit HUMAN PASS.

## Rejected V5 planning model

V5 accumulated a brittle loop: model invents visual hypotheses, lexical/identity validators constrain them, media is searched, claims are authored, media is searched/reviewed again, and final narration attempts to preserve the resulting bindings. This fails cross-topic: concept/question topics can lose literal canonical-subject tokens even when the search is semantically correct, while mechanism topics can satisfy metadata/target gates with generic contextual photographs that do not explain narration. A second post-claim search/review duplicates availability work and introduces another failure surface.

V6 removes that causal structure rather than adding more rescue thresholds.

## V6 causal order

`topic -> semantic class -> research evidence -> evidence-grounded visual facets -> real provider inventory -> pixel-derived visual facts -> evidence ∩ visual-fact story candidates -> final narration -> natural TTS -> exact timings -> reserved-shot execution -> render -> rendered-artifact QA -> assistant visual gate -> HUMAN PASS`

### 1. Semantic class drives identity policy

Topic resolution already returns `topic_kind` and `subject_type`. Visual discovery uses two explicit modes:

- `named_subject`: people, named objects, organizations, named places/events where literal identity is meaningful;
- `semantic_topic`: questions, concepts, processes and phenomena where no single photographed object can literally equal the canonical topic phrase.

Only `named_subject` requires canonical identity anchors in provider metadata. `semantic_topic` requires evidence-grounded facet/query relevance instead of literal canonical-token identity.

### 2. Visual facets are discovery directions, not claims

WF02 produces bounded diverse facets from research. Each facet contains only: ID, provider query, observable target, preferred factual form, purpose, identity mode and evidence IDs. No narration and no hidden factual claim is attached to a facet.

### 3. Pixel review creates Visual Facts

The first and only pre-narration image review is authoritative about visible content. For each real asset it returns:

- visible description;
- actual visual form;
- communication role (`establish|context|detail|process|relationship|result|reference`);
- explanation strength (`direct|supporting|context_only`);
- portrait crop safety for ordinary photos.

Research remains authority for factual truth. Pixel review never infers hidden causality or numbers.

### 4. Story is authored only from intersection of research and Visual Facts

Candidate story units cite research evidence and 1-2 already-reviewed asset IDs. No later provider query is generated. A mechanism/process unit is legal only when at least one selected visual fact has `direct` explanatory strength and an appropriate communication role. A context-only asset cannot satisfy an explanatory unit. Diagram/map/document/illustration/photo compete by explanatory adequacy; photo is never mandatory.

The old second `Discover Pre-Script Visual Inventory -> fingerprint -> image review -> claim selector` loop is removed from the active WF02 path.

### 5. Final writer cannot change factual or visual identity

The final writer chooses a coherent subset/order from validated story candidates and writes only narration in the requested language. It may not invent claims, evidence IDs, assets, searches or visual targets. Evidence/asset identity is frozen before WF03. Duration rewrites may change wording only.

### 6. Portrait composition is an inventory property

Ordinary photographs that cannot survive a deliberate 9:16 subject-preserving crop are not eligible as normal full-frame shots. Factual graphics may use fit-preserve composition. The renderer must not turn arbitrary landscape photos into small horizontal cards merely to make them fit.

### 7. Render QA must be derived, never declared

`composition_quality.pass=true` and aggregate `visual_quality.pass=true` may not be unconditional constants. Machine QA must derive pass/fail from measurable render checks and the frozen visual-fact contract. `review_ready` still does not imply visual quality; assistant exact-artifact inspection remains mandatory before HUMAN review.

## Cross-topic acceptance

No architecture proof may rely on repeated runs of one topic. Before production acceptance V6 must pass materially different topic classes, including at least:

1. one named concrete/mechanical subject;
2. one concept/question/process topic where literal canonical-image identity is inappropriate;
3. one ordinary non-mechanism informational topic.

A topic-specific vocabulary list, manual asset choice, manual query repair or special-case threshold invalidates the proof.
