# Operator Execution Rules — MUST READ BEFORE ANY ACTION

Last updated: 2026-09-04

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
- spending time on Studio/n8n/DB before the direct autonomous product path works.

These patterns are forbidden.

## Mandatory pre-action check

Before **every** meaningful action, code change, render, test, architecture decision, dependency addition, or direction change:

1. Read this file.
2. Read `docs/CURRENT_STATE_V5.md`.
3. Confirm that the planned action directly advances the real product goal below.
4. If the action is based on an assumption, first verify the actual output/source state.
5. If it does not advance the product goal, do not do it.

## Real product goal

The product input is only:

`topic + language + requested duration`

After that, the system must autonomously perform:

`research -> licensed visual inventory -> visual verification/ranking -> showable story angle -> final script -> one continuous narration -> exact-audio word timing -> autonomous edit plan -> render -> QA -> exact-artifact human review`

The target durations remain `15 / 30 / 45 / 60` seconds and the output format is vertical `9:16` short-form video.

## What counts as a valid proof

A proof is valid only when, after supplying `topic + language + duration`, there is **zero manual creative intervention**.

The following invalidate the proof:

- manually choosing clips/images;
- manually writing or repairing scene composition for the topic;
- manually authoring the edit plan;
- manually changing search queries for one topic to rescue it;
- manually looping/reusing assets to fill duration;
- renderer-specific one-off tuning for a proof;
- changing speech speed to fit duration;
- calling a machine-rendered MP4 a success before user HUMAN PASS.

If manual intervention is required, the autonomous test is failed.

## Media rule

Do **not** claim that free visual material is the main blocker without evidence.

There is a large free image/media inventory across sources such as Wikimedia Commons, Openverse, Internet Archive, Library of Congress, NASA/NARA and stock-video providers already used by the project.

The real engineering problem is automatic **selection, verification and editorial use** of relevant visuals. Images are allowed and expected when appropriate, but the result must not degrade into a static slideshow. Still images may be used through purposeful crops, details, pans, masks, layouts, maps, documents, callouts, parallax or motion graphics.

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

Do not rebuild Studio, n8n orchestration, PostgreSQL product state, or production workflow integration until the **same direct autonomous path** produces multiple materially different videos that receive explicit HUMAN PASS.

Renderer choice is replaceable implementation detail. The architecture must not be built around MoneyPrinterTurbo, HyperFrames, OpenNolan, MoviePy, FFmpeg, or any other renderer before the autonomous path is proven.

## Source of truth order

Before work, use this order:

1. `docs/OPERATOR_EXECUTION_RULES.md`
2. `docs/CURRENT_STATE_V5.md`
3. current factual runtime/output evidence
4. other historical docs

Chat history must not override newer repository facts.
