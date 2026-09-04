# V5 n8n Photo-First Media Policy — 2026-09-04

## Trigger

The autonomous n8n job `d23617c3-1311-43c1-97e0-c6504522bd77` (`Почему листья меняют цвет осенью`, `ru`, requested `60 s`) reached `review_ready` and produced a technically valid 59.064 s vertical MP4.

Human review result: **HUMAN FAIL**.

The general visual defect was not lack of free media. The workflow was biased toward stock video and selected long/repetitive video material even though the product should primarily use the much larger pool of relevant still images.

## Mandatory media policy

The automatic visual path is **photo/image first**.

Primary visual inventory should come from free/licensed still-image sources such as:

- Pexels Photos;
- Wikimedia Commons / canonical Wikipedia media;
- Pixabay Images;
- other free/publicly licensed image providers added later.

Still images are normal production assets, not a fallback. They must be edited as video through crop/reframe, pan/zoom, detail crops, masks, layouts, callouts, parallax, maps/documents/diagrams, or other purposeful motion treatment. The result must not become a static slideshow.

## Video clips

Video is optional and secondary.

A video candidate may be considered only when all of the following are true:

1. the narration segment actually describes visible motion/action;
2. candidate metadata matches both the canonical subject and the segment-specific visual target;
3. local visual ranking says the video is more relevant than the best available still candidate for that same segment;
4. the output use is a short clip (maximum four seconds per selected shot in the current policy).

If these conditions are not met, use a relevant still image instead of generic stock video.

No video may be selected merely because it is moving footage.

## Systemic fix

The fix belongs in the shared n8n/media-worker visual path, not in a topic-specific blacklist or manual selection step.

Required implementation direction:

- Pexels default search endpoint is Photos, not Videos;
- Wikimedia/Pixabay/Pexels photo candidates are ranked before optional motion-gated video candidates;
- WF04 representation order is photo/diagram first;
- Pexels video search runs only for motion-led segments;
- video candidates require stronger metadata relevance and must beat the best still in local visual rank;
- long video shots are forbidden.

This policy is cross-topic and must be used by the same n8n workflow for all future proof jobs.
