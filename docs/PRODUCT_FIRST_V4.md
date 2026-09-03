# Product-First V4 Redesign

Last updated: 2026-09-03

This document supersedes the semantic-v3 product architecture for all new development on branch `rebuild/product-first-v4`.

## Trigger

Production job `61f662ee-565c-4dd6-8759-17a51f3e7ec3` reached machine `review_ready` but received explicit HUMAN FAIL.

The failure was not a rendering bug. The machine produced a technically valid 1080x1920 video with durable segments/shots and perceptual diversity, yet the product was bad:

- raw encyclopedic Ukrainian prose was sent directly to TTS;
- `кГц` was not speech-normalized and was pronounced as letters instead of a natural unit name;
- the script contained long source sentences, parenthetical prose and Unicode stress marks that were never rewritten for spoken delivery;
- selected visuals included fried eggs, bacon, a campfire and generic cooking footage for a video about how induction cooking works;
- machine visual gates passed because they measured diversity and weak metadata overlap rather than whether the viewer actually saw the intended subject/mechanism.

Therefore semantic-v3 machine PASS is invalidated as a product-quality signal. M8 remains 2/10. No more production jobs are allowed through semantic-v3.

## Research basis

The redesign was informed by a broad comparison of mature/open-source short-video systems rather than one repository:

- `harry0703/MoneyPrinterTurbo` — large, mature topic->script->keywords->materials->TTS->subtitles->render pipeline; supports custom scripts, multiple LLM providers, Ollama, Pexels/Pixabay/Coverr, batch variants and optional multimodal reranking.
- `rayventura/shortgpt` — AI video automation framework with semantic content planning before media/editing.
- `AbdullahNaveed/ai-shorts-generator` — structured script JSON, semantic clip library, scene visuals, voiceover, faster-whisper word timing, FFmpeg assembly and local review dashboard with clip swap.
- `gyoridavid/short-video-maker` — REST/MCP/n8n-compatible service using TTS, Whisper-derived captions, Pexels and Remotion.
- `het8802/OpenNolan` — explicit research -> script -> scene plan -> assets -> edit -> compose architecture, multiple visual styles, word-level captions, human approval/editing and separate rendering runtimes.
- `Cstrp/vml` — TTS + Whisper + Pexels + FFmpeg service pattern.
- Remotion-based faceless-video projects — code/motion-graphics tracks for explainers instead of forcing stock footage into every scene.

The repeated pattern across these projects is more important than any single implementation.

## Core conclusion

Do not try to reconstruct semantic understanding with dozens of hand-written thresholds and token-fragment heuristics.

The product needs one coherent semantic `director` artifact first. Everything downstream consumes that artifact.

V4 critical path:

`topic -> factual research -> semantic director -> speech-ready script + scene storyboard -> TTS -> transcription/alignment from actual audio -> scene asset production -> preview QA -> Remotion/FFmpeg render -> human review`

Orchestration and persistence are secondary. A direct vertical prototype must produce a good video before the pipeline is rebuilt around it.

## 1. Semantic director artifact

One semantic stage creates a validated JSON plan for the whole short.

Required top-level fields:

- `topic`
- `language`
- `target_seconds`
- `hook`
- `spoken_script`
- `facts[]` with source provenance
- `scenes[]`

Each semantic scene owns:

- `scene_id`
- `narration`
- `purpose` (`hook`, `explain`, `proof`, `example`, `transition`, `close`)
- `visual_mode`
- `visual_query`
- `must_show[]`
- `must_not_show[]`
- `source_refs[]`
- optional `on_screen_text`
- `shots[]`

`shots[]` is the editing layer inside a semantic scene. A semantic scene is not synonymous with one asset. A scene may contain several short shots, inserts, crop-safe portrait clips, diagram beats, text beats, collage beats or motion graphics aligned to the narration.

The semantic director must output natural speech, not source prose copied verbatim.

## 2. Factuality

Research remains grounded and provenance-bearing, but source text is evidence, not narration.

The semantic director may paraphrase evidence into natural spoken language while preserving facts. This deliberately replaces the failed rule that narration must be assembled almost verbatim from Wikipedia sentences.

For factual videos, the stored artifact must preserve fact/source mapping so claims remain auditable.

## 3. Speech-ready narration

TTS must never receive raw article text.

Before TTS, a general multilingual text-normalization layer converts the director's script to spoken form:

- Unicode normalization;
- remove editorial stress/markup artifacts;
- expand units and abbreviations according to language;
- normalize ranges, percentages, dates and symbols into speakable forms;
- normalize punctuation for natural pauses;
- reject unexpanded technical abbreviations when pronunciation is ambiguous.

This is a standard TTS text-normalization boundary, not a topic-specific pronunciation patch.

The first implementation may keep the already selected male Edge voices, but voice quality is judged on the speech-ready script. Provider rate/pitch manipulation remains forbidden unless a future human-approved voice profile explicitly requires it.

## 4. Actual-audio timing

Do not invent subtitle timestamps by splitting text into fixed beat counts.

After one continuous voice track is created, run Whisper/faster-whisper/whisper.cpp on that exact audio and use its word/segment timestamps for:

- captions;
- semantic scene timing alignment;
- shot timing/edit timing.

This pattern appears repeatedly in mature short-video pipelines and removes a large class of synthetic timing logic.

## 5. TikTok-first editing contract

The product is a TikTok/Shorts/Reels-style vertical short, not a narrated slideshow or presentation.

Required editing behavior:

- one semantic scene may contain multiple shots;
- visual state changes frequently enough to maintain short-form pacing rather than leaving one still image on screen for an entire sentence or paragraph;
- the hook contains immediate visual activity, not a static title card;
- use real portrait footage/photos, close-ups, cutaways, diagram beats, text beats, collage beats and motion graphics as appropriate;
- dynamic video/motion is the primary visual language; still images are supporting beats rather than the dominant format;
- kinetic captions and on-screen emphasis may reinforce narration but must not dominate the visual field;
- no full-screen landscape photograph as a normal TikTok photo shot;
- important subjects, captions and overlays stay inside a TikTok-safe content area so platform UI does not cover the message.

TikTok's own current creative guidance reinforces these product rules: frame content vertically at 9:16, use vertical-by-nature imagery, keep key information inside the UI safe zone and avoid relying on static imagery as the primary experience. These external rules guide product behavior; they are not substitutes for human review.

### Portrait media rule

For normal full-screen `photo` or `video` shots, source media must be portrait/vertical or genuinely composed so the focal subject survives a vertical crop without losing meaning.

Do not take a wide landscape photograph and treat `object-fit: cover` as proof that it is suitable for TikTok.

If the only truthful exact asset is landscape/widescreen:

- do not stretch it;
- do not crop away required explanatory content;
- route it to a representation designed for horizontal evidence, such as `diagram`, `screen/card`, `collage`, picture-in-picture or another contain-layout;
- otherwise obtain a portrait alternative.

This is a product representation rule, not a topic-specific threshold.

### Safe-zone rule

The renderer must expose safe-zone controls rather than hard-code one layout for every aspect ratio.

For vertical TikTok review renders:

- captions must be movable upward from the physical bottom edge;
- caption width must be bounded so text does not sit under the right-side interaction controls;
- important overlay text and focal subjects must not depend on screen areas normally occupied by platform UI;
- safe-zone settings belong to the renderer/profile, not to individual topics.

Do not certify a video as TikTok-ready merely because the encoded canvas is 1080x1920.

## 6. Visual modes instead of one stock lane

Every scene declares a visual mode. Stock footage is only one option.

### `exact_media`
For a concrete person/object/place/product/entity. Use exact Wikimedia/Openverse/provider media or fail/route to another truthful mode.

### `stock`
For genuinely contextual/lifestyle scenes where generic real-world footage is acceptable. Search terms come from the semantic storyboard, not fragments of narration.

### `diagram`
For mechanisms, processes, comparisons, numbers and technical explanations. Render with Remotion/SVG/code-driven graphics rather than searching for unrelated stock.

### `generated_image`
Optional local/free image generation when hardware permits and the representation is not truth-critical.

### `screen/text/card`
For definitions, statistics, steps, UI/process diagrams and transitions.

A factual mechanism scene must not silently degrade into generic cooking/lifestyle footage.

## 7. Visual relevance contract

The old rule `metadata overlap -> eligible -> SigLIP rank` is rejected.

For retrieved assets:

1. scene-specific query and `must_show` requirements come from the semantic director;
2. provider metadata is evidence only, never enough by itself;
3. local visual similarity/reranking compares the asset against the full visual intent, not one or two token fragments;
4. negative intent (`must_not_show`) is evaluated when applicable;
5. low-confidence assets are not forced into the video;
6. no joker/generic fallback terms for factual scenes;
7. if retrieval is weak, change representation mode (usually diagram/card) instead of inserting unrelated stock;
8. full-screen photo/video assets must also satisfy the portrait-media rule above.

Perceptual diversity remains useful only after relevance is established.

## 8. Editing/rendering

Adopt the common split used by mature projects:

- structured timeline/artifact first;
- Remotion for captions, kinetic typography, diagrams, cards, collages and compositing;
- FFmpeg for media normalization, audio mixing, final encode and ffprobe validation.

Required final profile remains vertical 1080x1920, H.264 + AAC unless a later product decision changes it.

Renderer input is a shot timeline, not a one-scene/one-asset slideshow.

## 9. Captions and sound

- word-level captions from actual audio alignment;
- readable short-form caption style;
- caption placement respects the vertical platform safe zone;
- optional music/SFX only after narration/visual quality is solved;
- automatic ducking if music is enabled;
- no audio speed fitting.

## 10. Review model

The old machine `review_ready` meaning is retired.

V4 review has two levels:

- `machine_rendered`: technical render exists and machine checks passed;
- `human_approved`: user watched the exact artifact and accepted script, pronunciation, visual relevance and edit quality.

During V4 bring-up, every scene's selected visual and internal shot timeline must be previewable/swappable before final render, following the review-dashboard pattern used by established projects.

## 11. What is retained

Retain only components that are independently useful:

- job intake concepts;
- PostgreSQL durability where it simplifies recovery/audit;
- media download/cache utilities;
- FFmpeg normalization/ffprobe;
- useful provider adapters;
- rollback discipline;
- human review requirement;
- no topic-specific hacks.

## 12. What is retired

Do not carry these semantic-v3 concepts into the new core unless separately justified:

- raw evidence sentences as final spoken narration;
- fixed synthetic beat counts for captions;
- narration-fragment-derived stock queries;
- weak metadata eligibility as truth proof;
- SigLIP as a substitute for semantic planning;
- forcing every semantic interval to consume found stock;
- elaborate perceptual thresholds before basic relevance is proven;
- machine `review_ready` as evidence of content quality;
- one semantic scene = one visual asset;
- widescreen stills used as ordinary full-screen TikTok photo shots;
- hard-coded caption placement that ignores vertical platform UI.

## 13. Cost / provider boundary

User requirement remains: do not turn the project into a paid-per-video service.

The semantic director must therefore be provider-pluggable. Preferred free path is a sufficiently capable local model (for example through Ollama on hardware that can actually run it), with optional BYOK hosted providers for experimentation but no mandatory paid dependency.

Do not repeat the old mistake of forcing a weak model onto the 2 vCPU / 3.7 GiB VPS merely to preserve an architectural rule. Product quality decides where the semantic model runs.

## 14. V4 build sequence

1. Freeze production semantic-v3; no new jobs.
2. Build a direct CLI prototype outside n8n.
3. Director produces one complete spoken script + storyboard JSON with semantic scenes and internal `shots[]`.
4. Add multilingual speech text normalization.
5. Generate one continuous voice and transcribe the actual audio for timing.
6. Implement the visual-mode router with `diagram` and `stock/exact` paths.
7. Enforce portrait-first media for normal full-screen shots and route landscape evidence into diagram/card/collage modes.
8. Enforce renderer-level vertical safe-zone controls for captions/important overlays.
9. Produce a multi-shot 9:16 prototype with short-form pacing and inspect it manually.
10. Fix only product-level defects until the prototype is HUMAN PASS.
11. Repeat on at least three materially different topics/languages.
12. Only then design the minimal DB/n8n orchestration around the proven artifact contracts.

No production deploy is allowed before the direct prototype is human-approved.
