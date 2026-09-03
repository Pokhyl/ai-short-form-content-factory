# V4 Cross-Topic Validation Matrix

Date: 2026-09-03

Purpose: prevent architecture from being tuned to one fixture. No renderer/media/director rule is accepted from a single topic.

## Matrix cases

### A — Technical mechanism / Ukrainian

Topic class: mechanism explainer.

Representative topic: `Як працює індукційна плита`.

Primary visual problem:

- mechanism cannot be explained by generic cooking footage;
- requires exact induction media plus coil / magnetic-field / induced-current / heating diagrams or motion graphics.

This case remains in the matrix as regression evidence, but it is NOT the next fixture to tune.

### B — Exact place/history / Polish

Representative topic: `Jak zbudowano Wieżę Eiffla`.

Primary visual problem:

- the exact entity must remain visibly the Eiffel Tower / construction history;
- historical photos may be landscape and therefore need portrait-safe collage/PIP/contain treatment;
- generic Paris/travel footage cannot silently substitute construction evidence.

Expected visual language:

- exact tower footage/photos;
- historical construction imagery;
- map/date/height annotations as overlays;
- no standalone title-card replacement of the visual track.

### C — Process/object / Russian

Representative topic: `Как работает молния на одежде`.

Primary visual problem:

- needs close-up mechanism/detail rather than generic fashion footage;
- can mix exact macro footage/photos with simple motion graphics showing teeth/slider engagement.

Expected visual language:

- macro zipper/slider shots;
- mechanism diagram/motion graphic;
- continuous meaningful visual track;
- text only as overlay/annotation.

### D — Comparison / English

Representative topic: `OLED vs LCD: what actually changes`.

Primary visual problem:

- comparison should not devolve into random phone/TV stock;
- requires structured side-by-side visual evidence and diagrams for self-emissive vs backlit pixels.

Expected visual language:

- exact display close-ups where available;
- side-by-side comparison composition;
- simple pixel/backlight motion graphics;
- concise overlay labels rather than full-screen text cards.

## Shared acceptance contract

Every case is evaluated against the same rules:

1. `continuous_visual_track` — meaningful visual representation exists throughout normal narration;
2. `no_text_substitution` — typography does not replace the visual track by default;
3. `exact_or_justified_media` — factual footage/photo is exact or clearly justified by the storyboard;
4. `no_generic_factual_fallback` — generic adjacent stock is rejected instead of forced into the timeline;
5. `portrait_first` — normal full-screen photo/video is portrait or genuinely crop-safe;
6. `horizontal_evidence_treated_explicitly` — landscape exact evidence uses contain/PIP/collage/diagram treatment;
7. `meaning_driven_pacing` — shot changes follow semantic beats and visual information, not an arbitrary fixed cut count;
8. `actual_audio_timing` — captions/timing derive from the exact generated narration;
9. `safe_zone` — important text/subjects stay clear of vertical platform UI;
10. `human_review` — no machine metric can promote a candidate to `human_approved`.

## Architecture acceptance

A new architecture or general rule is not accepted because one matrix case improves.

Minimum before production orchestration resumes:

- materially different cases rendered through the same general contracts;
- no fixture-specific code or thresholds;
- each exact artifact reviewed;
- failures/root causes recorded before changes;
- multiple languages represented;
- at least three HUMAN PASS direct prototypes remain the working target before n8n/DB reconstruction.

M8 remains unchanged until exact artifacts are human-approved.