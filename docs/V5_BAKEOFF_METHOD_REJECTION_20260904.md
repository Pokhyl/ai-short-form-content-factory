# V5 Bake-off Method Rejection — 2026-09-04

## Status

REJECTED.

The current engine bake-off method is not valid evidence for the actual product goal.

## What was wrong

We were manually constructing one-off proof videos around candidate renderers:

- manually choosing the topic/script;
- manually selecting a very small media set;
- manually writing/assembling the edit composition;
- manually fixing renderer-specific issues;
- then judging the renderer output.

That tests whether a renderer can execute a handcrafted composition. It does **not** test whether the project can autonomously create good short-form videos from only the product input (`topic`, `language`, `duration`).

This is the same category of mistake that caused previous months of work: optimizing a local component while the end-to-end autonomous product remains unproven.

The 60-second QR proof exposed the problem directly. A handcrafted HyperFrames composition was being debugged for timing/render/runtime behavior instead of testing the production task. The render was stopped and is not evidence for product quality.

## Consequence

- Stop the current 60-second HyperFrames render.
- Do not continue hand-authoring candidate-specific proof compositions.
- Do not select HyperFrames, OpenNolan, MoneyPrinterTurbo, or any other renderer as the project architecture based on handcrafted demonstrations.
- Existing bake-off artifacts remain historical evidence only.

## Correct acceptance test

A candidate approach is relevant only if the test starts from the same input the finished product will receive and runs without manual creative intervention:

`topic + language + requested duration`

The system itself must then perform:

1. research/fact selection;
2. real media discovery and acquisition;
3. visual inspection/ranking of actual assets;
4. story angle selection based on what can truthfully be shown;
5. final script generation;
6. one continuous narration;
7. exact narration timing;
8. autonomous edit planning;
9. video rendering;
10. QA.

No manual clip selection, no manually written scene composition, no topic-specific edit plan, no post-hoc patch to make one proof pass.

## Promotion gate

The architecture is not chosen until the **same autonomous path** produces HUMAN PASS videos for multiple materially different topics and requested durations.

A renderer is an implementation detail inside that path, not the architecture itself.
