# Current State — V5 Agentic Editor

Last updated: 2026-09-04

Branch: `rebuild/agentic-editor-v5`.

## Mandatory pre-action gate

Before any meaningful action, code change, render, test, architecture decision, dependency addition, or direction change, **read `docs/OPERATOR_EXECUTION_RULES.md` first**, then read this file.

The current primary project risk is operator/assistant decision drift: changing direction without proof, handcrafting proofs, inventing blockers, and fixing one topic instead of the autonomous product. Do not repeat those patterns.

## Status

V4 product/runtime is frozen and the old V4 Studio self-test service is stopped.

V5 is **not** a chosen production architecture.

The previous renderer-centric bake-off method is now **REJECTED** because it relied on handcrafted proof videos and therefore did not test the real autonomous product goal. Durable record: `docs/V5_BAKEOFF_METHOD_REJECTION_20260904.md`.

The in-progress 60-second handcrafted HyperFrames QR render was stopped. It is not product evidence.

No V5 video is `human_approved` as evidence of the final autonomous path.

## Product acceptance contract

Every meaningful proof must start only from the same inputs the finished product receives:

`topic + language + requested duration`

From there the system itself must perform:

`research -> actual licensed media inventory -> visual inspection/ranking -> showable story angle -> final script -> one continuous narration -> exact-audio timing -> autonomous edit plan -> render -> QA -> exact-artifact human review`

Final script freeze must happen after real visual inventory is known.

A valid proof has zero manual creative intervention after the input is supplied.

## Forbidden proof method

Do not use any of the following as evidence that the product architecture works:

- manual clip/image selection;
- manually written topic-specific scene composition;
- manually authored edit plans;
- topic-specific search-query rescue;
- renderer-specific tuning for one proof topic;
- repeated fixes just to make one test render complete;
- looping/reusing assets simply to fill duration;
- speech-speed manipulation to force duration;
- machine render success without user HUMAN PASS.

Renderer choice is an implementation detail, not the project architecture.

## Media reality

Do not treat lack of free imagery as a presumed blocker. The project can draw from large free/publicly licensed inventories such as Wikimedia Commons, Openverse, Internet Archive, Library of Congress, NASA/NARA and existing stock-video sources.

The actual engineering problem is autonomous relevance selection, verification and editorial use of those visuals. Still images are valid when used purposefully; the product must not collapse into a repetitive static slideshow.

## Historical renderer findings

The earlier bake-off records remain historical evidence only:

- `docs/V5_ENGINE_BAKEOFF_20260904.md`;
- `docs/V5_ENGINE_BAKEOFF_ROUND2_20260904.md`;
- `docs/V5_MONEYPRINTERTURBO_HUMAN_FAIL_20260904.md`;
- `docs/V5_HYPERFRAMES_QR_PROOF_20260904.md`;
- `docs/V5_BAKEOFF_METHOD_REJECTION_20260904.md`.

MoneyPrinterTurbo is HUMAN FAIL because it violated requested duration and looped already-used clips when media was insufficient.

HyperFrames proved only that a handcrafted composition can be rendered; that is insufficient for product selection.

## Immediate gate

Build and test one minimal autonomous end-to-end path from `topic + language + duration`, with zero manual creative intervention after input.

The first proof must exercise the real sequence, not a handcrafted renderer demo. Then run the **same** autonomous path across materially different topics.

Do not rebuild Studio/n8n/PostgreSQL orchestration and do not promote any renderer until the same autonomous path produces multiple HUMAN PASS artifacts.
