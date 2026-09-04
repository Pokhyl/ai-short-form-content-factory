# V4 Studio self-test v1 architecture rejection — 2026-09-04

## Human verdict

The Studio V4 self-test v1 is rejected as a product architecture.

The user reviewed the corrected GPS render and reported that the visible result was effectively unchanged: the program still behaved like a static slideshow. The user then ran a different topic (`Зеленский / ru / 30`) and the job failed before media/render.

This is not a GPS-specific failure and must not be fixed by further fixture tuning.

## Verified root causes

### 1. The renderer still reduced an editing shot to one still image

`VerticalShort.tsx` rendered `exact_media` with one `<Img>` plus a slow scale animation. Increasing GPS from four to six shot IDs therefore changed only the number of stills; it did not change the visual language.

The previous self-test work incorrectly treated `more shot ids` as if it solved the slideshow defect. It did not.

### 2. Semantic/speech/editing responsibilities were mixed

Fresh Studio job:

`c78f655e-96e1-45ab-9c0f-9a40ffeebf37` — `Зеленский / ru / 30`.

Initial semantic output contained the spoken abbreviation `КВН`, so the general speech guard correctly rejected it. The runtime then routed that error into the editing-shot correction stage. The correction model expanded the abbreviation to `Клубом веселых и находчивых`, but the same stage was forbidden from changing the frozen semantic fingerprint, so the job failed with:

`shot correction changed frozen semantic content`

This proves the architecture conflated two independent repairs: speech normalization and visual editing.

### 3. Structural tests were not product proof

The previous focused suite reached `69/69 PASS`, but those tests proved contracts and plumbing. They did not prove that arbitrary Studio jobs produced a good visual product. Calling the self-test path a technical/product success before cross-topic end-to-end validation was premature.

## Rejected approach

Retire the Studio v1 visual core:

`semantic scene -> editing shot -> one selected asset -> VerticalShort image/video sequence`

Do not keep increasing shot counts, adding fixture-specific media, or rerendering GPS to rescue it.

## Replacement experiment that was also rejected

A short-lived V4 experiment tried multi-asset visual sequences. It is retained only in local history; its code is not carried into V5. The later availability-blind failure is recorded separately.

## Acceptance boundary

V4 remains frozen. This document is historical failure evidence, not an implementation direction for V5.
