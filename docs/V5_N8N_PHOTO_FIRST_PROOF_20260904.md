# V5 n8n Photo-First Rerun Proof — 2026-09-04

## Trigger

Human review rejected the first real n8n 60-second autumn proof because WF04 selected generic/long stock video instead of using the large available still-image inventory.

The shared visual policy was changed systemically to photo-first. No media was manually selected for the reruns.

## First rerun after photo-first deployment — SYSTEM FAIL

Job:

`4f6816b2-38aa-4fe8-8e8d-fbf84a951818`

Input:

- topic: `Почему листья меняют цвет осенью`;
- language: `ru`;
- requested duration: `60 s`.

The job reached WF04 and failed while persisting the first selected photo.

Exact general cause: the existing PostgreSQL constraint `visual_shots_kind_check` still allowed only `generic_broll` and `factual_graphic`, while the new shared photo-first workflow correctly emitted `factual_image` for still photos and `context_video` for optional video.

This was a schema-contract defect, not a media-selection defect.

Systemic fix:

- migration `017_photo_first_visual_kinds.sql` expands the allowed visual kinds to:
  - `generic_broll`;
  - `factual_graphic`;
  - `factual_image`;
  - `context_video`.

No topic-specific retry rule or data bypass was added.

## Second rerun after schema fix — MACHINE RENDERED / REVIEW READY

Job:

`8d82fc3e-b8ad-4ac0-8ef5-f61190e3a904`

Same input:

- topic: `Почему листья меняют цвет осенью`;
- language: `ru`;
- requested duration: `60 s`.

Result:

- status: `review_ready`;
- rendered duration: `59.064 s`;
- output: 1080x1920, 30 fps, H.264 + AAC;
- exact review copy: `/opt/ai-short-form-content-factory/studio/bakeoff/n8n-photo-first-leaves-ru-60.mp4`;
- SHA256: `0b007fdde0a15994c7df7b1de0d7054fe136755d08c21a6a03f566c3c3e13850`.

Selected media composition was fully automatic:

- Pexels Photos: 4;
- Pixabay Images: 3;
- Wikimedia Commons images: 3;
- video clips: 0.

All ten selected shots are distinct still images. No manual clip/image choice was made after job submission.

The discovery layer itself was also verified after the change on a separate bounded request: it returned large still pools from Wikimedia, Pexels Photos and Pixabay, while Pexels video candidates were only added for motion-led segments.

## Acceptance state

This rerun is `machine_rendered` / `review_ready` only.

It is **not** `human_approved` until the user watches this exact MP4 and explicitly accepts it.

The known narration-quality defect remains separate: current WF02 extractive narration can still sound encyclopedic/source-like. Do not silently treat the visual-policy correction as a narration HUMAN PASS.
