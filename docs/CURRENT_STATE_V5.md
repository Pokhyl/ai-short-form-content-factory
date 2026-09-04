# Current State — V5 n8n Autonomous Video Orchestrator

Last updated: 2026-09-04

Branch: `rebuild/agentic-editor-v5`.

## Mandatory pre-action gate

Before any meaningful action, code change, render, test, architecture decision, dependency addition, or direction change, **read `docs/OPERATOR_EXECUTION_RULES.md` first**, then read this file.

The current primary project risk is operator/assistant decision drift: changing direction without proof, handcrafting proofs, inventing blockers, or replacing the required n8n product with side architectures. Do not repeat those patterns.

## Product definition

The product is a **free/self-hosted n8n orchestrator**.

External input:

`topic + language + requested duration`

Required n8n-controlled path:

`input -> research -> free/licensed visual inventory -> visual verification/ranking -> story/script -> one continuous narration -> exact-audio timing -> autonomous edit plan -> render -> QA -> exact-artifact human review`

Supported durations: `15 / 30 / 45 / 60` seconds.

Output: vertical `9:16` short-form MP4.

No mandatory paid-per-video API dependency is allowed.

## Current autonomous proof state

First real n8n-orchestrated 60-second proof:

- job: `d23617c3-1311-43c1-97e0-c6504522bd77`;
- topic: `Почему листья меняют цвет осенью`;
- language: `ru`;
- requested duration: `60 s`;
- rendered duration: `59.064 s`;
- technical state: `review_ready`;
- human state: **HUMAN FAIL**.

The result proved that the existing n8n chain can reach a final MP4 automatically, but the video is not acceptable product output.

Two general defects are already visible:

1. **visual policy defect** — WF04/media-worker was biased toward stock video, producing long/generic moving footage instead of using the much larger relevant still-image inventory;
2. **narration defect** — current WF02 deterministic extractive narration can sound encyclopedic and expose source artifacts instead of producing natural spoken short-form text.

Neither defect may be repaired manually for one topic.

## Mandatory photo-first visual policy

Durable record: `docs/V5_N8N_PHOTO_FIRST_MEDIA_POLICY_20260904.md`.

Default visual inventory is still-image first:

- Pexels Photos;
- Wikimedia Commons / canonical Wikipedia media;
- Pixabay Images;
- additional free/publicly licensed image providers as they are integrated.

Still images are normal production assets and must be turned into dynamic video through purposeful crop/reframe, pan/zoom, detail crops, masks, layouts, callouts, parallax, maps/documents/diagrams or other motion treatment.

Video is optional and secondary. A clip may be selected only when the segment is genuinely motion-led, metadata matches both subject and segment target, local visual ranking says it is more relevant than the best still for that segment, and the selected clip is short (currently max four seconds).

Generic moving footage is a fail.

## What counts as a valid proof

A proof starts by supplying only `topic + language + duration` to n8n.

After that there is zero manual creative intervention.

Invalid proof methods include:

- manual clip/image selection;
- manual query rescue for one topic;
- manual scene/edit-plan repair;
- looping/reusing assets to fill duration;
- speech-speed manipulation to force duration;
- bypassing n8n with a handcrafted direct/CLI path;
- calling machine success a product success before explicit HUMAN PASS.

## Historical renderer findings

Renderer-centric bake-off is historical evidence only and is not the current product method.

Relevant records:

- `docs/V5_ENGINE_BAKEOFF_20260904.md`;
- `docs/V5_ENGINE_BAKEOFF_ROUND2_20260904.md`;
- `docs/V5_MONEYPRINTERTURBO_HUMAN_FAIL_20260904.md`;
- `docs/V5_HYPERFRAMES_QR_PROOF_20260904.md`;
- `docs/V5_BAKEOFF_METHOD_REJECTION_20260904.md`.

MoneyPrinterTurbo remains HUMAN FAIL. HyperFrames proved only handcrafted rendering and is not product evidence.

## Immediate gate

1. deploy the shared photo-first media policy in the existing n8n WF04/media-worker path;
2. rerun the same n8n flow without manual visual intervention and verify selected media provenance/types;
3. fix the general natural-narration defect in WF02 without topic-specific text;
4. produce exact MP4 for human review;
5. repeat the same n8n path on materially different topics/languages after HUMAN PASS.

Do not create a separate product architecture. n8n remains the orchestrator.
