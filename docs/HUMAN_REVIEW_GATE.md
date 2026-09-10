# Human Review Gate — mandatory final product gate

Last updated: 2026-09-08

This file is a permanent acceptance contract for `Pokhyl/ai-short-form-content-factory`.
It exists because machine-success states and automated QA repeatedly allowed obviously bad videos to be treated as candidates for user review.

## Non-negotiable rule

No MP4 may be described as `ready`, `good`, `passed`, `successful`, `final`, or presented to the user as a review candidate until the assistant has visually inspected the **exact artifact** that will be shown to the user.

The artifact must be identified by exact path and SHA256 before review. The reviewed file and the delivered file must be byte-identical.

Machine states such as `success`, `review_ready`, `machine_rendered`, workflow completion, ffprobe success, motion metrics, subtitle presence, codec checks, or any other automated QA result are **never substitutes for visual inspection**.

If the environment cannot provide a real visual inspection of the exact artifact, do not claim that the video has been visually reviewed. Do not present it as ready. State the inspection limitation instead.

User `HUMAN PASS` remains the final acceptance authority. Assistant visual review is a mandatory precondition before asking for that verdict; it never replaces the user's verdict.

## Mandatory assistant pre-delivery review

Before any exact MP4 is shown to the user, the assistant must visually inspect the complete artifact with available visual tooling. At minimum the inspection must cover the full timeline, every edit/shot transition, the opening hook, middle and ending, subtitle changes, framing/crop changes, and any diagram/map/text-heavy visual.

The assistant must explicitly decide `ASSISTANT VISUAL PASS` or `ASSISTANT VISUAL FAIL` for that exact SHA256.

If the verdict is FAIL:

1. do not present that MP4 to the user as a candidate;
2. preserve the exact artifact and failure evidence;
3. record the concrete visible defects;
4. identify and fix a general system cause;
5. generate a completely new autonomous product run for the next proof;
6. never manually rescue or cosmetically patch the failed artifact and call that automation proof.

## Immediate visible FAIL conditions

Any one of the following is sufficient for `ASSISTANT VISUAL FAIL`, regardless of machine QA:

- subtitles, captions or titles are clipped, cropped, outside safe area, partially off-screen, or unreadably large/small;
- text occupies an unreasonable portion of the phone frame or obscures the subject;
- visible words are cut at the left/right/top/bottom edge;
- ordinary landscape media appears as a small horizontal card inside a 9:16 frame instead of a deliberate vertical composition;
- the video repeatedly shows generic or near-identical footage while narration discusses a more specific object, mechanism, place, person, event or process;
- visual cuts are frequent numerically but semantically useless, for example switching among near-identical ships/water shots;
- narration describes a mechanism/process while the visuals never actually illustrate the mechanism/process with suitable footage, stills, diagrams, maps, documents, labels, callouts or other appropriate visual form;
- the selected media contradicts or materially fails to correspond to the narration at that moment;
- one or very few assets are stretched across most of the video without editorial justification;
- repeated or perceptually near-duplicate shots create the appearance of fake cadence;
- the main subject is lost by 9:16 crop/reframe;
- an important diagram/document/graphic is cropped so its factual content is lost;
- subtitles or typography visibly collide with the subject, UI-safe zones, or other on-screen elements;
- narration contains obviously awkward, broken or unnatural phrasing that should have been caught before delivery;
- units, names, language or terminology are obviously inappropriate for the requested language/audience;
- beginning, middle or ending contains obviously broken composition, blank/black frames, frozen frames, bad transitions, or unintended overlays;
- the result is technically valid but visibly looks like an automated draft rather than a coherent short-form edit.

These are minimum conditions, not an exhaustive checklist. Passing them does not force a PASS if the video still visibly looks bad.

## Content-to-visual requirement

A short-form edit must communicate the actual story visually, not merely maintain motion.

For each narration beat, the visible material must have an editorial reason to be on screen. The system may use the visual form that best communicates that beat: real video, still photograph, detail crop, diagram, map, archive/document, labeled graphic, callout, or another factual visual treatment.

Motion alone is not relevance. A moving generic stock clip is worse than a relevant still/diagram when the still/diagram explains the narration better.

Shot-count and motion metrics are diagnostics only. They cannot prove editorial correspondence.

## Permanent regression history

Past visible failures are permanent acceptance regressions. They must not be rediscovered as new requirements.

### Rejected production artifact — 2026-09-07

Job `515408f3-0f17-4ce4-aaf5-63d709998ee9`, MP4 SHA256 `0f765192024fb2f3cbc241b3eeac3d41509cd54fe7fd6a3745235be7ec66dae6`.

Permanent lessons:

- three photos across roughly sixteen seconds is too sparse;
- ordinary landscape photos must not be rendered as horizontal cards inside the phone frame;
- machine completion is not HUMAN PASS.

### Rejected V6 review candidate — 2026-09-08

Run `20260908T173343Z-5cfe625f`, MP4 SHA256 `34764af46cf7aadc65f293a98776fa609b1eb7ab0e9b45b34333f1270e775866`.

Visible inspection found:

- subtitles were extremely large;
- subtitle text was visibly clipped at frame edges;
- visuals were dominated by similar ship/water/lock footage;
- the narration described how canal locks work but the edit did not adequately show the mechanism;
- numerical cut cadence looked acceptable while editorial variety/correspondence was poor;
- Russian narration included awkward wording and inappropriate unit phrasing.

Permanent lessons:

- subtitle rendering needs visual safe-area validation, not only file/track presence;
- cut frequency cannot substitute for semantic visual variety;
- editorial correspondence must be judged on the rendered video, not inferred from asset metadata;
- final narration quality is part of video quality and must be reviewed together with visuals.

## No forgetting / no rediscovery rule

These requirements are already known. Do not present them later as a new architectural discovery.

Before changing architecture, adding a QA metric, adding a renderer, or starting another proof run, reread this file and verify that the proposed work addresses an actual unresolved defect rather than rediscovering a requirement already recorded here.

When a new user or assistant HUMAN FAIL reveals a general defect, append that defect and exact artifact identity here (or in a linked durable regression document) before continuing development.

### Assistant visual FAIL — 2026-09-09

Job `386d332c-e0f9-42e8-a4c0-f7d52915ac8b`, exact MP4 SHA256 `f86dc120141cc54d431a59d8f47136760c5a0575546d55db9a2907e3b1b3514e`.

Assistant pixel review rejected the exact rendered artifact before user delivery. Scene 1 narration described a ship entering and gates closing while the selected shots were mostly general lock-chamber/water views. Scene 2 narration described valves opening, chamber filling and the ship rising while both selected shots showed a container ship/general lock infrastructure without valves, filling, water-level change, explanatory diagram/callout or visible lift. Scene 3 had materially better correspondence because a locomotive/tow vehicle was actually visible beside the ship.

Systemic lesson: research-grounded factual truth and pixel truth may remain separate, but explanatory mechanism narration may not be paired with generic subject/context imagery. A mechanism/detail candidate must share a mechanism-specific visible anchor with its visual target and pixel-reviewed inventory, and the final explanatory unit must retain direct reviewer-bound visual support for that same claim.


### HUMAN FAIL — 2026-09-10 — repeated visual-subsystem regression

Job `2e84dc84-edd9-4e27-b2b1-6bc7c4aea4b3`, exact MP4 SHA256 `b55620961fe031867dcde1d8f61f28d84565ddb0eeaa0eab715e1aeff103129e`. The user explicitly rejected the exact artifact. It repeated two already-forbidden failure classes: ordinary stills read as landscape/static slideshow material rather than deliberate native 9:16 editing, and a narration beat about a changing-water-level mechanism was paired only with static lock/chamber imagery that did not explain the process.

Permanent additional lesson: a framing-policy label or renderer code path is not evidence that the rendered composition is acceptable. Machine composition QA must measure the rendered output and fail closed. For explanatory units, target/form correspondence alone is insufficient: selected real pixels must be capable of communicating the mechanism/state change/relation that narration actually says. Ordinary photo is not a required representation type for an explanatory mechanism; diagram/map/illustration/document/photo-action must compete by explanatory adequacy.
