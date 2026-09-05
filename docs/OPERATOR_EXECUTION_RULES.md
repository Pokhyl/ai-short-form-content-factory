# Operator Execution Rules — MUST READ BEFORE ANY ACTION

Last updated: 2026-09-05

This file is a mandatory pre-action gate for all work on `Pokhyl/ai-short-form-content-factory`.

## Current primary project risk

The largest current risk is **operator/assistant decision drift**, not lack of free media or renderer capability.

Repeated failure patterns already observed:

- changing direction without proof;
- handcrafting test videos and treating them as evidence for automation;
- focusing on a renderer instead of the end-to-end autonomous product;
- inventing blockers or constraints without checking real source/output data;
- patching one topic/render instead of fixing a general system defect;
- continuing to improve a failed candidate instead of rejecting it;
- replacing the actual n8n product with a separate CLI/direct-prototype product path;
- spending time on Studio/DB before the n8n-orchestrated product path works.

These patterns are forbidden.

## Mandatory pre-action check

Before **every** meaningful action, code change, render, test, architecture decision, dependency addition, or direction change:

1. Read this file.
2. Read `docs/CURRENT_STATE_V5.md`.
3. Confirm that the planned action directly advances the real product goal below.
4. If the action is based on an assumption, first verify the actual output/source state.
5. If it does not advance the product goal, do not do it.

## Real product goal

The product is a **free/self-hosted n8n orchestrator** for automatic short-form video generation.

The external product input is only:

`topic + language + requested duration`

n8n is mandatory and remains the orchestration layer. It must coordinate the complete flow:

`input -> research -> licensed/free visual inventory -> visual verification/ranking -> showable story angle -> final script -> one continuous narration -> exact-audio word timing -> autonomous edit plan -> render -> QA -> final MP4`

The target durations remain `15 / 30 / 45 / 60` seconds and the output format is vertical `9:16` short-form video.

Mandatory production dependencies must not require paid per-video API usage. Prefer self-hosted/free/open-source components and genuinely free provider access.

### Hosted AI quota rule — hard architecture gate

A quota-limited hosted AI service must never be the only required path for script planning, rewriting, visual-query generation, multimodal review, TTS, or any other production-critical stage.

If a required hosted AI call fails with quota/rate-limit/credit exhaustion, that is an **architecture FAIL**, not a retry-tuning problem. Do not repair it with provider sleeps, quota waits, rate-limit schedulers, increased timeouts, repeated retries, or a paid-plan assumption. Replace/demote that provider so the baseline remains self-hosted or otherwise quota-independent.

The repository contract in `config/production-dependency-policy.json` and `.github/workflows/production-contract.yml` is mandatory. A change that violates that contract must not be committed as production architecture or deployed.

A standalone CLI may be used only as an internal diagnostic tool for one component. It must never replace n8n as the product orchestrator or become a parallel product architecture.

## What counts as a valid proof

A proof is valid only when, after supplying `topic + language + duration` to the n8n workflow, there is **zero manual creative intervention**.

The following invalidate the proof:

- manually choosing clips/images;
- manually writing or repairing scene composition for the topic;
- manually authoring the edit plan;
- manually changing search queries for one topic to rescue it;
- manually looping/reusing assets to fill duration;
- renderer-specific one-off tuning for a proof;
- changing speech speed to fit duration;
- bypassing n8n with a handcrafted/direct generation path and calling that product proof;
- calling a machine-rendered MP4 a success before user HUMAN PASS.

If manual intervention is required, the autonomous test is failed.

## Mandatory photo-first media policy

The default visual strategy is **still-image first**, not stock-video first.

Primary automatic inventory must prioritize relevant free/licensed images from sources such as:

- Pexels Photos;
- Wikimedia Commons and canonical Wikipedia media;
- Pixabay Images;
- other free/publicly licensed image sources added to the shared provider layer.

Still images are normal production assets. They must be edited into dynamic short-form video through purposeful crop/reframe, pan/zoom, detail crops, masks, layouts, callouts, parallax, maps/documents/diagrams or other motion treatment. Do not turn the result into a static slideshow.

Video clips are optional and secondary. A video candidate may be used only when:

1. the narration segment actually describes visible motion/action;
2. its metadata matches both the canonical subject and the segment-specific visual target;
3. local visual ranking says it is more relevant than the best available still candidate for the same segment;
4. the selected output shot is short — current maximum is four seconds.

If those conditions are not met, select a relevant still image. Never choose generic video merely because it moves.

Durable record: `docs/V5_N8N_PHOTO_FIRST_MEDIA_POLICY_20260904.md`.

## Media rule

Do **not** claim that free visual material is the main blocker without evidence.

There is a large free image/media inventory across sources such as Wikimedia Commons, Openverse, Internet Archive, Library of Congress, NASA/NARA and stock providers already used by the project.

The real engineering problem is automatic **selection, verification and editorial use** of relevant visuals.

## No-hacks rule

No topic-specific fixes, no arbitrary threshold rescue, no acceptance bypass, no retry/sleep hacks, no special-case blacklist/whitelist added just to make one test pass.

A fix must address a general system defect and remain valid cross-topic.

## Failure handling

When something fails:

1. capture the exact failure/output;
2. identify the general cause;
3. record it in GitHub;
4. either make a systemic fix or reject/demote the approach;
5. do not keep polishing one failed proof for hours/days.

## Architecture gate

n8n is not optional and must not be postponed as a "later wrapper". It is the required orchestrator from the product path onward.

Do not build a separate CLI product, separate custom orchestration service, or renderer-centric architecture instead of n8n.

Studio UI and PostgreSQL product-state expansion may wait until the n8n-orchestrated generation path itself works reliably across materially different topics.

Renderer choice remains a replaceable implementation detail. The architecture must not be built around MoneyPrinterTurbo, HyperFrames, OpenNolan, MoviePy, FFmpeg, or any other renderer.

## Source of truth order

Before work, use this order:

1. `docs/OPERATOR_EXECUTION_RULES.md`
2. `docs/CURRENT_STATE_V5.md`
3. current factual runtime/output evidence
4. other historical docs

Chat history must not override newer repository facts.
