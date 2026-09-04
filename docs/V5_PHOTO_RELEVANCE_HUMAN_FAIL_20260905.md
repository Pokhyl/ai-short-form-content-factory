# V5 photo relevance HUMAN FAIL — 2026-09-05

## Human decision

The user rejected all five review-ready artifacts from the topic-resolution matrix. They are **HUMAN FAIL** and must not be cited as product-quality successes.

User direction: prefer a relevant still image over video that is only weakly related to the narration.

## Exact general defect

The rejected jobs were already still-image-first, but WF04 accepted irrelevant stills. Persisted evidence included:

- a bicycle-path sign and bicycle horn for the refrigeration `cycle`;
- an ammonia bomb image for refrigeration;
- an office/marketing image and wooden beads for Rayleigh `scattering`;
- repeated abstract people/smartphone imagery for Samsung;
- a cheetah/leopard comparison image in the jaguar story.

The local visual scores for obvious garbage were effectively zero (`2e-9`, `2e-7`, `9e-5`), but metadata overlap added `0.018` bonuses and made those candidates assignable. This converted lexical coincidence into visual acceptance.

WF02 already generated English story-specific visual concepts, but did not persist them. WF04 therefore derived anchors from non-English narration and produced mixed-language queries such as `Refrigeration cycle небудь замислювалися`.

## Systemic correction

- Migration 019 persists 4-16 grounded English visual queries with each job.
- WF04 requires that inventory and sends it to the media worker.
- Visual discovery maps those concepts across semantic segments and uses them for provider searches.
- Local ranking now compares images against `canonical subject + exact English visual target`, not a long mixed-language narration/evidence blob.
- Candidates below the calibrated semantic relevance floor `0.01` are rejected before metadata utility is applied. Metadata can no longer rescue a visually unrelated candidate.
- Video remains secondary: it must pass the same relevance floor, be motion-led, match subject and target metadata, and score above the best eligible still.
- If no relevant photo/diagram exists, the job fails instead of filling the timeline with weak media.

No topic-specific media, query, alias, provider override, or acceptance bypass was added.
