# V5 full rebuild decision — 2026-09-04

## Status

Product-First V4 is frozen as historical evidence. It is not the base for new product code.

The V4 Studio service is stopped. New development moves to branch `rebuild/agentic-editor-v5`.

## Why V4 is rejected as a project architecture

The failure is broader than a renderer bug or one media query.

Observed cross-topic failures include:

- a technically valid induction artifact with irrelevant factual visuals;
- a custom compositor artifact with broken vertical composition and oversized captions;
- an OpenMontage attempt that became a narrated slideshow;
- a higher-cut attempt that replaced visuals with text cards and generic adjacent stock;
- an OLED path where constructed graphics became box/label/arrow presentation slides;
- GPS where increasing shot IDs from four to six did not change the slideshow visual language;
- Zelensky where speech repair and visual repair were incorrectly coupled;
- turbocharger where the visual planner invented media that the free provider inventory did not contain.

The repeated root problem is architectural: V4 keeps trying to encode creative editing as a rigid sequence of custom semantic artifacts, contracts and renderer obligations. Each new failure creates another custom contract, while the visible product remains fragile.

## Decision

Do not build V5 by extending `prototype/v4`, `VerticalShort`, `SequenceShort`, the V4 scene/shot planner, V4 media selector, or V4 correction passes.

V5 is a clean implementation that treats a mature editor as the production engine and keeps our code limited to product policy, factual grounding, provider configuration, reproducibility and review.

The first pinned editing-engine reference is OpenNolan at commit `4457349c386ea1a89c01547f9a76fa650970c131` (`v1.0.2`, AGPL-3.0). It already contains provider adapters, real editing operations, FFmpeg composition, transcript tooling, stock acquisition, motion operations and agent-oriented pipeline definitions.

## Fundamental reversal

V5 does not write a final script and then hope free providers can illustrate it.

The core order is:

`topic -> research -> real licensed visual inventory -> choose a showable story angle -> script -> one continuous voice -> exact-audio word timing -> real edit plan -> mature editor operations -> QA -> human review`

For factual content the available truthful media constrains the story before the final script is frozen. This is intentionally different from V4 availability-aware *visual* planning, which still froze semantic content before proving the visual story could be made.

## Product boundary

- no mandatory paid-per-video API;
- semantic-v3 remains frozen;
- V4 remains readable only as failure/history evidence;
- no new `/api/v4` product work;
- no n8n/PostgreSQL orchestration until the direct V5 editor path has multiple unrelated HUMAN PASS artifacts;
- no quality claim from unit tests, ffprobe, or a successful render alone.
