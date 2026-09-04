# Permanent Project Rules — V5 Agentic Editor

These rules apply to branch `rebuild/agentic-editor-v5`.

## 1. V5 is a clean core

New V5 product code must not import or call `prototype/v4/*`, `services/v4-selftest/*`, `VerticalShort`, `SequenceShort`, semantic-v3, or the old V4 visual correction machinery.

V4 stays in the repository as historical evidence only.

## 2. Mature editor first

Do not write another custom video editor, renderer, stock-selection framework, shot-density system or visual-threshold maze when the pinned upstream already implements the needed editing primitive.

Prefer pinned OpenNolan tools/contracts for stock acquisition, trimming, reframing, cutting, transitions, overlays, motion operations, captions, audio and FFmpeg composition. Our layer should adapt policy and provenance, not reimplement editing.

## 3. Asset-first factual storytelling

For factual/person/place/history/mechanism content, discover a real licensed visual inventory before freezing the final story/script.

The final story angle must be demonstrably producible from available truthful media and/or a justified deterministic visual representation. Do not invent a shot and search indefinitely for it afterward.

## 4. Dynamic edited video, not slideshow arithmetic

Do not use shot count, scene count, image count or cut frequency as a proxy for product quality.

The primary visual language must be actual edited motion: real footage, source video, screen capture, meaningful animated evidence, or genuine compositing/motion treatment. Still images may support documentary evidence but cannot become the default primary experience merely by adding zoom.

## 5. Truth and media

- no generic factual stock fallback;
- text-only primary visuals are forbidden for normal factual narration;
- factual media must carry source/provenance/license information;
- a search result or provider tag is not proof that the visible content supports the narration;
- if a truthful visual story cannot be made from the available inventory, change the story angle before script freeze or fail closed.

## 6. Speech and timing

Generate one continuous speech-ready narration. No per-scene TTS and no audio speed fitting.

Timing for captions and edit anchors comes from the exact generated audio through faster-whisper word timestamps (or an equivalent real-audio aligner), never from synthetic duration division.

## 7. Free-required path

The production-critical path must not require paid per-video APIs.

Current allowed free-required building blocks include self-hosted research, free licensed media providers, Edge TTS or local TTS, faster-whisper and FFmpeg. Optional paid/BYOK providers may be evaluated separately but cannot be required for the baseline.

## 8. No topic patches

No topic-specific word replacements, media IDs, hand-picked query fallbacks, acceptance bypasses, arbitrary sleeps, blind retries or threshold weakening to make a fixture pass.

## 9. Cross-topic product proof

Any architecture claim must be exercised on materially different subjects/languages. Unit tests establish software contracts only.

`human_approved` requires the user to watch the exact artifact and accept it. Multiple unrelated HUMAN PASS artifacts are required before orchestration work resumes.

## 10. Durable evidence

Record every meaningful fail, root cause, upstream decision, architecture change and exact artifact identity in GitHub before moving to the next independent architecture stage.
