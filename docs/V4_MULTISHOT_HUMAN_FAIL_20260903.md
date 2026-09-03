# V4 Multi-shot TikTok Prototype — HUMAN FAIL

Date: 2026-09-03

Artifact:

`/opt/ai-short-form-v4-upstreams/OpenMontage/remotion-composer/out/v4-induction-tiktok.mp4`

SHA256:

`dbaf1e92e3cd7fd66920520a683b403a46bb04b875a89fcbda696a2950b54af5`

## Human verdict

The exact 25-cut portrait-first artifact is HUMAN FAIL.

The user rejected the video as a whole and identified two general product defects:

1. some visual shots were replaced by standalone text screens (`hero_title`, `text_card`, `callout`) instead of keeping a meaningful visual track;
2. several stock clips were generic cooking/electric-stove footage rather than exact or clearly relevant material for the factual subject.

## Verified timeline evidence

The render timeline contained standalone text/card cuts including:

- `hero_title` 0.00–1.15;
- `hero_title` 2.25–3.35;
- `text_card` 5.95–7.15;
- `callout` 8.75–10.15;
- `text_card` 14.55–15.95;
- `callout` 17.25–18.16;
- `hero_title` 25.00–26.55;
- `callout` 26.55–28.10;
- `hero_title` 30.75–31.968.

This means the visual track repeatedly disappeared and was replaced by text presentation beats. That is not accepted as the default TikTok editing language for this project.

The portrait stock pool also contained general cooking/electric-stove material selected primarily because it fit 9:16. Portrait format alone does not establish semantic relevance.

## General root cause

The project over-corrected the earlier slideshow failure by optimizing for cut frequency and portrait orientation without preserving a stronger invariant: every moment still needs a meaningful visual representation of the narration.

Two incorrect shortcuts resulted:

- `more cuts` became a proxy for good TikTok editing;
- `portrait media` became a proxy for relevant media.

Neither is sufficient.

## Permanent product decisions

### Continuous visual track

For normal factual/explainer shorts, `hero_title`, `text_card`, `callout` or other typography must not replace the primary visual track by default.

Text is normally an overlay or annotation over relevant video/photo/diagram/motion graphics. Full-screen typography may only be used when the semantic director explicitly chooses it as the truthful representation and the style is human-approved across validation topics.

### Exact/relevant media before generic stock

For factual/mechanism content, generic lifestyle or adjacent-category footage is forbidden as a fallback merely to keep motion on screen.

A full-screen factual shot must be one of:

- exact media showing the actual subject/entity/action;
- clearly relevant contextual media justified by the storyboard;
- a truthful diagram/motion graphic;
- a precise photo with camera motion/collage treatment;
- another explicit representation mode that preserves meaning.

If exact moving footage is unavailable, change representation mode instead of inserting a generic video.

### No one-topic tuning

Do not keep tuning the induction fixture.

The next renderer/media/director changes must be tested as a cross-topic matrix covering materially different visual problems and multiple languages before architecture is accepted.

## Status

- Artifact: `human_fail`.
- OpenMontage remains evaluation/reference only.
- No V4 artifact is human-approved.
- M8 remains `2/10`.
- Production semantic-v3 remains frozen.
- No n8n/DB rebuild is allowed yet.