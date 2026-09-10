# V6 Storyboard-First Editor Rebuild

Date: 2026-09-10
Status: implementation branch, NOT deployed
Current documentation checkpoint branch: `rebuild/editorial-core-20260908`. Implementation will move to a dedicated V6 branch after this failure-ledger checkpoint is pushed.

## Trigger

The V5 inventory-first product path is retired as the target architecture after repeated cross-topic fail-closed runs and repeated HUMAN FAILs. The decisive 2026-09-10 HUMAN FAIL was job `2e84dc84-edd9-4e27-b2b1-6bc7c4aea4b3`, SHA256 `b55620961fe031867dcde1d8f61f28d84565ddb0eeaa0eab715e1aeff103129e`. It repeated two permanent visible defects: slideshow/landscape-card visual language and narration that describes a mechanism while the actual shots do not communicate that mechanism.

This rebuild does not attempt another threshold patch on `inventory-first-story-v1`.

## Product invariants retained

- External input remains only `topic + language + requested duration`.
- n8n remains the mandatory product orchestrator.
- PostgreSQL remains the durable state/audit store.
- Mandatory per-video dependencies remain free/self-hosted or genuinely free-access.
- One continuous natural-rate voiceover; no speech-rate fitting.
- Final output remains 9:16 short-form video.
- Failed/rejected product jobs remain immutable.
- Machine render is never HUMAN PASS. Exact MP4 assistant visual review and explicit user HUMAN PASS remain mandatory.
- No topic-specific search dictionaries, manual media selection, manual storyboard rescue, or generic stock fallback for factual/mechanism beats.

## Retired V5 assumptions

The new core must not depend on these V5 contracts:

- `find a generic reviewed inventory first, then let the story emerge from it`;
- `two still images per semantic unit`;
- `mechanism/detail must include a photo option`;
- `visual_target` token overlap as the main proof that narration can be communicated;
- static `factual_image` / `factual_graphic` classification as sufficient editing direction;
- `composition_quality.pass=true` based only on renderer policy labels;
- one FFmpeg crop/pan recipe as the normal still-image editing language.

They remain historical/rollback compatibility only.

## New critical path

`topic -> evidence research -> visual story director -> shot feasibility -> bounded storyboard replan if needed -> final speech-ready script -> one continuous TTS -> exact word timing -> shot timeline -> exact asset resolution / graphic compilation -> Remotion editor -> FFmpeg final encode -> pixel QA -> assistant visual review -> HUMAN review`

The important reversal is that the director specifies a coherent visual story before final narration is frozen, but every proposed shot is then checked against real executable representation capability before the script becomes immutable.

## Phase A — visual story director

After topic resolution and grounded research, one structured semantic director produces a provisional story artifact. It contains scenes and editing shots, not a pool of candidate facts.

Each scene contains:

- `scene_id`
- `purpose`: `hook | establish | explain | proof | example | transition | close`
- `grounded_fact_ids[]`
- `narration_intent` — meaning to communicate, not final spoken wording
- `shots[]`

Each shot contains:

- `shot_id`
- `representation`: `exact_media | annotated_media | diagram | map | document | collage`
- `must_show[]` — concrete visible requirements
- `must_not_show[]`
- `search_query_en` when external media is required
- `communication_goal` — what the viewer must understand from this shot
- `crop_policy`: `portrait_required | crop_safe | preserve_full | not_applicable`
- optional `annotation_plan` for `annotated_media`
- optional `diagram_spec` for constructed factual diagrams

A semantic scene may contain multiple shots. Shot count is editorial, not derived from a fixed seconds-to-images formula.

## Phase B — executable feasibility gate

Every provisional shot is checked before final speech is written.

For retrieved media the system must prove:

1. correct subject/entity;
2. actual pixels satisfy `must_show` and do not violate `must_not_show`;
3. the image/video is capable of communicating `communication_goal` rather than merely sharing topic keywords;
4. portrait suitability is explicit: either the reviewer returns a valid normalized `focus_box` and `crop_safe_portrait=true`, or the shot must use a representation that preserves the full frame (`collage`, `document`, `map`, annotated composition). A landscape source may not silently become a normal full-screen portrait shot;
5. exact provider identity, license and preview hash are retained.

For constructed `diagram` shots the compiler validates a factual, non-decorative diagram spec against grounded fact IDs. A diagram may explain motion/state/flow that cannot be proven by a static exterior photograph.

If one or more required shots are not executable, exactly one bounded storyboard replan may replace representation/shot structure while keeping the research facts and user intent. It occurs BEFORE final narration and BEFORE TTS. No iterative repair loop is allowed.

## Phase C — final speech freeze

Only after all selected shots are executable does the final director write the speech-ready narration. Narration is constrained by the already-feasible storyboard:

- every factual clause maps to grounded research IDs;
- every explanatory clause maps to one or more shots whose `communication_goal` can show/explain that clause;
- no narration may introduce a mechanism/action/state change that the frozen visual plan cannot communicate;
- natural spoken language is required in the requested language;
- target duration word budget is explicit before TTS.

## Phase D — exact voice timing

One continuous natural-rate voice track is generated. Exact provider word timing or exact-audio alignment drives scene/shot timing. Semantic scene boundaries and editing shot boundaries are independent from ASR segmentation.

No audio speed manipulation is permitted.

## Phase E — editor/rendering

The target editor is the Remotion `VerticalShort` approach that already received HUMAN PASS on the Eiffel/Polish artifact, adapted as a reusable n8n-driven rendering component. FFmpeg remains final normalization/encode tooling, not the semantic editor.

Required rendering modes:

- `exact_media`: full-screen only for portrait/crop-safe assets with reviewer-provided focal region;
- `annotated_media`: exact image plus factual arrows/highlights/labels tied to grounded visual elements;
- `diagram`: code-driven factual motion diagram;
- `map`: preserve factual geometry/labels with deliberate vertical composition;
- `document`: preserve evidence content with controlled zoom/pan/detail regions;
- `collage`: deliberate multi-crop vertical composition for wide evidence that cannot survive a single portrait crop.

Standalone text cards and generic filler are not primary visual fallbacks.

## Phase F — real post-render quality gate

A renderer may not self-certify composition by setting `pass=true` unconditionally.

Machine QA must inspect the rendered pixels and fail closed on at least:

- blank/black/letterboxed card-like states outside explicitly allowed map/document/collage modes;
- missing visible-state changes relative to the frozen shot timeline;
- repeated near-identical rendered states;
- caption overflow/safe-zone violations;
- focal-region loss for crop-safe exact media;
- required diagram/annotation layers absent from rendered frames.

These checks are diagnostics only; assistant visual review and HUMAN review remain authoritative.

## Cross-topic acceptance matrix

V6 must not be promoted from implementation to production based on one topic. Before replacing V5 product routing, the same n8n-orchestrated path must produce assistant-visual-PASS artifacts across materially different classes, including at minimum:

1. physical mechanism/process;
2. science/natural process;
3. person/history or concrete entity;
4. comparison/technology or data/diagram-heavy topic.

At least two materially different exact artifacts require explicit user HUMAN PASS before V6 becomes the production default. A failure on any test remains useful evidence but cannot be repaired manually.
