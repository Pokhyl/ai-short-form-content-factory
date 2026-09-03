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

## 2026-09-03 — MoneyPrinterTurbo upstream checkout and focused suite PASS

MoneyPrinterTurbo was checked out as an isolated upstream reference at `/opt/ai-short-form-v4-upstreams/MoneyPrinterTurbo`, exact upstream commit `cbbb366393105d5cefc254dc9ed492d43da0711b`, version `1.3.6`, MIT license. Production containers and the V4 project working tree were not modified.

An isolated Python 3.12 virtual environment installed the upstream runtime dependencies, including Edge TTS `7.2.7`, faster-whisper `1.1.0`, MoviePy and the project's provider/material dependencies.

Focused real upstream tests covered `llm`, `voice`, `subtitle`, `material`, `material_cache`, `video` and `task` services. The first sparse-checkout run produced 11 failures solely because `webui/i18n` and bundled `resource/fonts` files had intentionally not been checked out. This was incomplete test-fixture evidence, not an upstream logic failure.

After expanding the same clean sparse checkout to include the upstream i18n files and bundled fonts, the unchanged upstream commit passed:

- `316 passed`;
- `69 subtests passed`;
- `7 skipped`;
- no test failures.

The host shell warned that FFmpeg is not installed on the VPS host; the existing project media-worker already contains FFmpeg/ffprobe. This warning did not cause the focused upstream suite to fail and no production runtime was changed.

Decision: V4 should reuse/adapt MoneyPrinterTurbo's proven `llm.py`, `voice.py`, `subtitle.py`, `material.py`, `material_cache.py`, `video.py` and task contracts where they fit, instead of rebuilding those subsystems. The custom V4 layer should stay thin and concentrate on factual research, structured director/storyboard, multilingual speech normalization, visual representation routing and human preview/review.

## Immediate boundary

Semantic-v3 production is frozen and retained only for rollback/reference. No new production jobs.

MoneyPrinterTurbo upstream core is locally proven at its exact commit. Next independent stage: inspect the stable module interfaces and create the thin direct V4 prototype adapter outside n8n/DB.