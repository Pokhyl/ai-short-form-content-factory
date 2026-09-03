# Engineering History — Product-First V4

This file records V4-specific chronology. Older project history remains preserved in `docs/ENGINEERING_HISTORY.md`.

## 2026-09-03 — semantic-v3 machine PASS invalidated by HUMAN FAIL

Fresh production job `61f662ee-565c-4dd6-8759-17a51f3e7ec3` (`как работает индукционная плита / uk / 60`) reached machine `review_ready` but the user watched the exact video and rejected it completely.

Verified persisted facts:

- raw encyclopedic Ukrainian `script_text` went directly to Edge after whitespace cleanup only;
- script contained `Індукці́йна плита́`, `20-100 кГц`, repeated `20 кГц`, parenthetical prose and long source sentences;
- user reported unnatural delivery and `кГц` read as letters rather than natural `кілогерц`;
- exact selected shots included Pixabay fried egg footage, a campfire, Pexels bacon cooking and Pexels egg cooking;
- machine visual-quality metrics still reported PASS because they measured diversity/weak metadata overlap rather than visible semantic relevance.

Conclusion: semantic-v3 can generate a technically valid but bad product. Do not patch pronunciation tokens, eggs/bacon, this topic or thresholds specifically. Architecture is rejected.

M8 remains `2/10`. Job `61f662ee-565c-4dd6-8759-17a51f3e7ec3` is consumed and must never be retried/reused.

## 2026-09-03 — broad upstream research before redesign

A broad set of open-source short-video projects was reviewed instead of choosing the first search result.

### MoneyPrinterTurbo

Mature MIT project with topic/custom-script input, LLM script generation, separate LLM video-term generation, Pexels/Pixabay/Coverr materials, Edge TTS and other voices, Whisper subtitles, batch variants, WebUI/API/CLI and Ollama support. Its ordered-material mode explicitly asks the semantic model for chronological English stock-video search terms from the full script.

### ShortGPT

Uses semantic planning as the front of the video automation pipeline rather than reconstructing meaning from downstream thresholds.

### AI Shorts Generator

Uses structured script JSON, scene visuals, a reusable semantic clip library, voiceover, faster-whisper word-level captions, FFmpeg assembly and a local review dashboard where a user can approve/regenerate scripts and swap clips before final export.

### Short Video Maker

Provides REST/MCP integration suitable for n8n, with TTS -> Whisper captions -> Pexels -> Remotion. Its architecture reinforces that captions should come from actual audio and rendering should remain a normal media layer.

### OpenNolan

Explicit creative flow: research -> script -> scene plan -> assets -> edit -> compose. It separates visual styles and representation types, uses word-level captions, Remotion/FFmpeg, preview/editing and human creative decisions.

### VML and other Remotion-based systems

Reinforce the modular TTS + Whisper + visual assets + rendering pattern and show code/motion-graphics tracks as a normal alternative to forcing stock footage into explainers.

## 2026-09-03 — V4 architecture selected

New branch: `rebuild/product-first-v4`.

V4 critical path:

`topic -> factual research -> semantic director -> speech-ready script + scene storyboard -> TTS -> actual-audio Whisper alignment -> scene-specific visual modes -> preview QA -> Remotion/FFmpeg render -> human review`

Key reversal from semantic-v3:

- evidence is source material, not final speech;
- semantic director writes natural spoken script and visual intent together;
- TTS text receives general multilingual normalization;
- actual audio determines captions/timing;
- visual representation can be exact media, stock, diagram/motion graphic, card/screen or optional generated image;
- generic stock is not a factual fallback;
- relevance precedes diversity;
- machine-rendered does not mean human-approved.

Full design: `docs/PRODUCT_FIRST_V4.md`.

## Immediate boundary

Semantic-v3 production is frozen and retained only for rollback/reference. No new production jobs.

Next independent stage: build a direct V4 prototype outside n8n/DB, using mature upstream components/patterns rather than another custom workflow rewrite.