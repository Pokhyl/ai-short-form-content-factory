# Process Gate — Autonomous Product Proof

Last updated: 2026-09-04

## Mandatory first step

Before doing anything meaningful in this project:

1. read `docs/OPERATOR_EXECUTION_RULES.md`;
2. read `docs/CURRENT_STATE_V5.md`;
3. verify current runtime/output facts before acting on assumptions.

No action is valid if this pre-action read was skipped.

## Active gate

The current task is **not** renderer bake-off and **not** Studio/n8n/PostgreSQL integration.

The active gate is one direct autonomous prototype whose only external inputs are:

`topic + language + requested duration`

After input, no manual creative intervention is allowed.

Required autonomous sequence:

`research -> licensed media inventory -> visual verification/ranking -> showable story angle -> final script -> one continuous narration -> exact-audio timing -> autonomous edit plan -> render -> QA -> exact-artifact human review`

## Pass condition

A proof passes only when:

- the same autonomous path runs without manual clip/image selection;
- no topic-specific manual scene/edit construction is added;
- requested duration is respected without speech-speed tricks or clip looping;
- factual visuals are relevant and licensed/provenanced;
- output is vertical short-form MP4;
- the user explicitly gives HUMAN PASS to the exact artifact;
- the same path later survives materially different topics.

Machine render success alone is not a pass.

## Failure condition

The proof fails if the operator/assistant has to manually rescue the topic by selecting media, rewriting scene structure, inventing special search queries, tuning thresholds, looping assets, changing voice speed, or adding a one-off renderer workaround.

On failure: capture exact evidence, record the general cause in GitHub, make a systemic fix or reject the approach. Do not polish one failed proof indefinitely.

## Media rule

Do not presume that free visual inventory is scarce. Use actual evidence from free/publicly licensed sources. The hard problem is autonomous relevance selection and editorial use, not simply finding any image.

Still images are valid when the autonomous edit uses them intentionally; they must not become a repetitive static slideshow.

## Forbidden shortcuts

- no topic-specific fixes;
- no arbitrary threshold rescue;
- no blind retries/sleeps;
- no manual clip/image selection in a product proof;
- no manual topic-specific edit plan;
- no renderer-centric architecture decision before autonomous proof;
- no n8n/DB/Studio rebuild before multiple HUMAN PASS artifacts;
- no paid-per-video dependency as a required production path.

## Source of truth

1. `docs/OPERATOR_EXECUTION_RULES.md`
2. `docs/CURRENT_STATE_V5.md`
3. current factual runtime/output evidence
4. historical docs
