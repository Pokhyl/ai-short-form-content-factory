# V4 self-test shot-collapse failure — 2026-09-04

## Scope

This failure belongs to the standalone V4 self-test runtime at `/opt/ai-short-form-v4-selftest`. Semantic-v3 remains frozen and is not involved.

## Human-visible failure

The first GPS self-test artifact (`как работает GPS / ru / 15`) rendered successfully after the Remotion mount fix, but the user rejected the editing density: the video behaved almost like one image per semantic section.

Exact job:

`dafae8be-67c7-4b7d-966a-7147dc678738`

Director output contained:

- 3 semantic scenes;
- only 4 total internal shots (`S1A`, `S2A`, `S3A`, `S3B`);
- therefore the first two semantic scenes each had one visual asset for the whole scene.

The self-test prompt required `5-7` shots for a 15-second job, but runtime validation only rejected `total < 4`. The invalid under-populated storyboard was therefore accepted.

A second independent self-test (`Зеленский / ru / 30`) exposed the same structural collapse before rendering:

- 6 semantic scenes;
- 6 total shots, exactly one shot per scene;
- the prompt required `8-10` shots for a 30-second job;
- it also violated the factual visual rule by returning stock media for an `explain` scene, which the existing validator correctly rejected.

Job:

`f181088e-052a-404c-a9f5-2e514294894c`

## Root cause

The standalone self-test relied on prompt wording to obtain the requested editing-shot count, but the hard validator did not enforce the duration-specific shot contract. That allowed the semantic director to collapse the editing layer back toward `semantic scene == shot`, recreating the slideshow defect already rejected in earlier V4 work.

This is cross-topic evidence (GPS + Zelensky), not a GPS-specific issue.

## Required systemic correction

1. enforce the existing duration-specific shot ranges as a hard structural contract;
2. reject the degenerate case where every semantic scene contains exactly one shot;
3. keep semantic scenes authoritative for meaning and keep shots as a separate editing layer;
4. if the initial semantic director plan violates only shot/editing structure, use one bounded shot-plan correction stage that preserves script, facts, scene narration, purpose and source references exactly; this is not a blind Gemini retry and must not loop;
5. do not weaken factual media rules: `stock` remains forbidden for explain/proof/mechanism shots;
6. re-use existing GPS research/script/audio/Whisper when repairing the rejected GPS artifact; only shot planning/media/timeline/render may be regenerated as required by the new edit plan.

## Acceptance boundary

A corrected render is at most `machine_rendered` until the user watches the exact MP4. The old GPS artifact is not human-approved.