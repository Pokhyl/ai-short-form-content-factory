# Architecture — Product-First V4

Last updated: 2026-09-03

`docs/CURRENT_STATE.md` is authoritative. `docs/PRODUCT_FIRST_V4.md` contains the detailed redesign contract. Semantic-v3 is historical only.

## Product goal

Produce a short-form video that a human accepts for:

- factual/coherent script;
- natural speech and pronunciation;
- relevant visuals;
- readable synchronized captions;
- competent edit/render.

Technical validity alone is not product quality.

## V4 critical path

`topic -> factual research -> semantic director -> speech-ready script + scene storyboard -> TTS -> Whisper alignment from actual audio -> scene asset production -> preview QA -> render -> human review`

## Semantic director

One coherent semantic stage creates the full spoken script and scene storyboard from factual evidence. It is provider-pluggable.

The director must not emit raw encyclopedia copy as narration. It paraphrases evidence into natural spoken language while preserving source references.

Every scene declares:

- narration;
- purpose;
- visual mode;
- visual query when retrieval is required;
- `must_show` and `must_not_show` constraints;
- fact/source references;
- optional on-screen text.

## Upstream foundation

V4 does not rebuild commodity short-video subsystems.

Primary pinned upstream foundation: MoneyPrinterTurbo, currently pinned at commit `cbbb366393105d5cefc254dc9ed492d43da0711b` (MIT).

Reuse/adapt its proven modules where appropriate:

- LLM provider abstraction;
- Edge TTS;
- faster-whisper subtitles;
- Pexels/Pixabay/Coverr material retrieval/cache;
- video normalization/composition/render utilities.

Other reference architectures include ShortGPT, AI Shorts Generator, Short Video Maker, OpenNolan, VML and Remotion-based faceless-video systems.

## Speech boundary

TTS receives only speech-ready text.

The semantic director must spell numbers, units and abbreviations as ordinary spoken words. A lightweight language-independent guard removes editorial markup and rejects digits, symbols, URLs, parenthetical notation and ambiguous written abbreviations before TTS.

This guard does not maintain topic-specific pronunciation dictionaries.

Voice output is one continuous narration track. No scene-by-scene voice and no audio speed fitting.

## Timing boundary

Caption/edit timing comes from the actual generated voice track through Whisper/faster-whisper/whisper.cpp or equivalent alignment.

Fixed synthetic beat counts are retired.

## Visual boundary

Every scene chooses one explicit representation mode:

- `exact_media`;
- `stock`;
- `diagram` / motion graphic;
- `screen_text` / card;
- optional `generated_image`.

Stock is contextual media, not a universal fallback.

Mechanism/technical scenes must not silently degrade into lifestyle stock. If retrieval cannot satisfy a scene, the scene remains unresolved or changes representation mode through the semantic plan/review flow.

Provider metadata alone is not proof of visible relevance. CLIP/SigLIP may rerank candidates after semantic planning but cannot replace it.

## Rendering

Use a normal media pipeline instead of encoding semantics inside the renderer.

Preferred split:

- Remotion/code graphics for diagrams, cards, captions and compositing;
- FFmpeg/MoneyPrinterTurbo utilities for media normalization, audio, encode and ffprobe validation.

Target output remains vertical 1080x1920 H.264 + AAC unless product testing justifies another format.

## Review boundary

During V4 bring-up, scene assets must be previewable before final render.

Use two distinct states:

- `machine_rendered`: playable output exists and technical checks pass;
- `human_approved`: user watched and accepted the exact artifact.

Only `human_approved` counts as product success.

## Orchestration boundary

n8n/PostgreSQL production orchestration is intentionally deferred.

First prove the direct CLI prototype on multiple topics/languages. After human approval, wrap the proven artifact contracts in the minimum orchestration required for durability/recovery.

The existing semantic-v3 production stack remains frozen as rollback/reference and must not receive new generation jobs.