# V4 TikTok Format HUMAN FAIL — 2026-09-03

Artifact reviewed by the user:

`/opt/ai-short-form-v4-upstreams/OpenMontage/remotion-composer/out/v4-induction.mp4`

The artifact was technically valid and corrected the previous gross layout defects, but it received explicit HUMAN FAIL.

## What improved technically

- 1080x1920 H.264/AAC artifact rendered successfully;
- images were no longer stretched;
- technical diagrams were contained rather than destroyed by crop;
- captions were bounded at the bottom instead of covering most of the frame.

These facts are technical only and do not imply product quality.

## Human-visible product failure

The user identified the actual remaining product problem:

- the video still looked like a narrated slideshow/presentation, not TikTok;
- one photo/asset remained on screen for an entire semantic scene;
- five semantic scenes became five long visual scenes across roughly 32 seconds;
- there was insufficient visual change, motion and short-form editing cadence;
- ordinary photo treatment still relied on widescreen/landscape source material rather than portrait-first TikTok media.

## Root cause

The storyboard/render contract still implicitly equated:

`semantic scene = one visual asset = one long timeline cut`

That model is wrong for short-form social video.

A semantic scene describes meaning. It may require several short visual shots, inserts, close-ups, portrait clips, diagram beats, text beats, collage beats or motion graphics during the same sentence.

A vertical final canvas alone does not make the source media TikTok-native. `object-fit: cover` is not a substitute for portrait-first media selection.

## Permanent correction

The V4 contract now requires:

- `scene.shots[]` editing layer inside each semantic scene;
- frequent visual-state changes suitable for TikTok/Shorts/Reels rather than one asset per sentence/paragraph;
- normal full-screen photo/video shots use portrait/vertical source media or a crop-safe composition where the subject survives the vertical crop;
- widescreen evidence is routed to diagram/card/collage/PIP/contain representations, not used as an ordinary full-screen TikTok photo;
- hook begins with visual activity;
- kinetic captions/emphasis may support the video without becoming the video.

Authoritative product contract updated in `docs/PRODUCT_FIRST_V4.md` commit `c48abce6f95e6af86dc7beb7afc540d054e8d683`.

## Current boundary

This OpenMontage artifact is permanently `human_fail`.

No HUMAN PASS count change. M8 remains `2/10`.

Next artifact must be a multi-shot portrait-first TikTok-style direct prototype. No production/n8n rebuild is allowed yet.
