# AI Short-Form Content Factory — Production Plan

Updated: 2026-09-22

## Source of truth and execution rules

- Repository: `Pokhyl/ai-short-form-content-factory`.
- Branch: `main`.
- VPS path: `/opt/ai-short-form-content-factory`.
- Production n8n: `https://publisher.hodor.com.pl`.
- Studio: `https://studio.hodor.com.pl/`.
- GitHub + actual production state are the source of truth.
- Before every substantive action, read this PLAN and verify that the action matches the current next step.
- After every substantive finding, fix, test result, deploy, acceptance result, or change of direction:
  1. update this PLAN if current state or next step changed;
  2. update detailed handoff/evidence where applicable;
  3. commit and push immediately.
- A change that is not committed/pushed is not a durable project checkpoint.
- Never create a fresh acceptance job while another project execution is active.
- If a tool times out, inspect actual state before retrying.
- Do not touch unrelated workflows, credentials, n8n instances, domains, containers, or jobs.
- User disagreement is not new evidence. Change a technical conclusion only because of new evidence, a new test/tool result, or a specific identified error in the prior reasoning.
- Never claim fixed/deployed/passing without verifying the actual state.

## Product goal

Fully automatic n8n short-form video factory:

topic + language + duration
-> research
-> continuous narration/storyboard
-> exact accepted TTS audio
-> alignment
-> visual retrieval/selection
-> render
-> machine QA
-> final vertical MP4.

Inputs:
- topic
- language: PL / EN / RU / UK
- duration: 15 / 30 / 45 / 60 seconds

Constraints:
- n8n is the mandatory orchestrator.
- Free-only production path.
- No hacks or topic-specific production rules.
- No hardcoded visual asset IDs.
- Draft/inbox publishing only.
- Do not weaken semantic, visual, timing, or QA gates merely to pass acceptance.

## Current production state

Current verified production versions:
- M5 Script/Storyboard: v111
  - activeVersionId: `31eaa7a9-98d1-44b6-bec6-416ef388753b`
- M6 Voiceover: v8
  - activeVersionId: `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 Visuals: v61
  - activeVersionId: `a73aefbc-4c8e-4458-8ef2-c48bbce3a957`

M5 v111 deployment verification:
- published backup: `.backups/m5-before-anaphoric-20260922-210414.json`
- non-M5 workflow fingerprint unchanged: `31|f28cd4244a334ea2ea539357a3302585`
- live M5 nodes/connections/settings == Git: PASS
- Publisher: 200
- Studio: 200
- n8n restart count: 0
- media worker: healthy, restart count 0

The anaphoric/cross-scene visual fix is now deployed and verified live.

## Proven architecture decisions

### Exact audio handoff M5 -> M6
M5 preserves the exact synthesized MP3 that passed the final duration gate.
M6 reuses that exact file instead of independently synthesizing the same narration again.
This avoids stochastic TTS-duration drift.

### Continuous narration
Narration is continuous.
Scene boundaries are visual/timing cuts and may occur inside a sentence.
Do not require every scene narration segment to be a standalone sentence.

### Visual selection
Visual gates remain fail-closed:
- primary subject must be grounded;
- operational setting must be grounded when required;
- unrelated/museum/component/background false positives remain rejected;
- no topic-specific asset exceptions.

## Latest accepted technical result

Job:
- `345adac7-105e-461b-97ff-1a66789704ba`

Result:
- reached `machine_qa_passed`;
- rendered technically valid MP4:
  - 1080x1920
  - H.264
  - AAC
  - 30 fps
  - 14.800 s

Manual review identified a real cross-scene grounding defect:
- S5 narration `Który wytwarza prąd.` inherited its grammatical subject from the previous generator scene;
- storyboard visual primary incorrectly switched to transformer/substation imagery;
- malformed boundary punctuation such as `turbiny,.` / `generator,.` also appeared.

Evidence:
- `docs/acceptance/2026-09-22-pl15-machine-pass-manual-reject-anaphoric-visual-fix.json`

## Current Git-only fix

The latest M5 fix in Git:
- keeps one continuous narration contract across initial and repair prompts;
- detects relative/personal anaphoric scene starts and requires them to retain the previous concrete visual primary;
- excludes demonstratives that can legitimately introduce a new explicitly named subject;
- normalizes conflicting visual-cut punctuation without changing words or semantic content.

Validation recorded in Git:
- focused scene-segment tests: 9/9 PASS;
- full suite: 260/260 PASS;
- JSON/diff checks: PASS.

This fix is not considered production-complete until deployment and live verification succeed.

## Latest fresh PL15

Job: `8ce87adb-3952-43cb-ab1d-7a1b2d549651`

Verified pipeline state before SentinelX disconnected:
- M5 v111: PASS
- M6 v8: PASS
- M8 v61: PASS
- visual_run `cfb7a60e-ed47-408f-85f9-3bbaa7626648`: PASS
- visual searches: 45/45
- provider results collected: 288
- job status: `machine_qa_passed`

No new acceptance job may be created. This exact PL15 remains the active acceptance artifact until its final MP4 has been manually reviewed.

## Manual acceptance result for current PL15

Job: `8ce87adb-3952-43cb-ab1d-7a1b2d549651`

Technical MP4 checks: PASS
- render execution: `9602`
- render id: `fa9dc976-a76d-40fb-977e-135af4c38e47`
- 1080x1920
- H.264 / yuv420p / 30 fps
- AAC mono 24 kHz
- video duration: 14.933 s
- audio duration: 14.904 s
- duration delta: 29 ms
- full decode: PASS
- render SHA256: `e43b6e1a9e1fa07b84e8675665c2394e09e9b0390c4a71897c04ba66f1b78a66`

Audio/narration checks: PASS
- Whisper transcript matched canonical narration with `global_coverage=1.000`
- alignment method: `whisper_token_sequence_match`
- lexical coverage: 25 tokens
- audio SHA256: `45602fa3cd7d6228d39b862288f3893e7548ca0b24b48e1db23316659869b90c`

Manual visual checks: FAIL
- S1 PASS: dam/reservoir image matches narration.
- S2 FAIL: narration describes a large falling water stream / penstock context; selected frame is a small rocky brook with a thin blue pipe.
- S3 FAIL: narration says water strikes turbine blades directly; selected frame is a general generator/turbine hall and does not show turbine blades.
- S4 FAIL: narration describes the turbine in rapid rotation; selected frame is a static old/museum-like turbine exhibit rather than an operating turbine.
- S5 PASS: electric generator image matches narration.

This PL15 is NOT accepted despite machine QA passing.

## M8 visual-detail fix tested locally

Source evidence:
- job `8ce87adb-3952-43cb-ab1d-7a1b2d549651`
- M8 execution `9601`
- visual_run `cfb7a60e-ed47-408f-85f9-3bbaa7626648`

Demonstrated selection defects:
- S2 selected Pexels `12496885`: generic rocky brook + thin blue tube; intent required powerful falling water through penstock pipes.
- S3 selected Pexels `12270481`: generic turbine/generator hall; intent required turbine runner blades.
- S4 selected Wikimedia `19189428`: Deutsches Museum 1840 turbine; intent required rotating water-turbine shaft in operation.

Root cause:
- `must_show` correctly described the broad primary object, but M8 did not require the specific visible component/detail that distinguished the requested shot from generic subject imagery.

Tested fix:
- infer hard visual-detail anchors only from component terms shared by `visual_intent` and the most-specific first query;
- preserve existing domain/must_show semantics;
- add missing component anchors to effective provider queries without rewriting original query provenance;
- require the same component evidence in scorer metadata;
- treat explicit `in operation` intent as operational context so museum/exhibit imagery conflicts;
- keep generic shots unaffected when no specific component detail is present.

Exact current anchors:
- S2: `penstock + pipe`
- S3: `blade + runner`
- S4: `shaft`

Validation:
- exact 9601 regression tests: PASS;
- focused M8 compatibility tests: 47/47 PASS;
- full suite: 265/265 PASS;
- old deterministic 9229 replay: terminal PASS, provider calls 0, selected assets unchanged:
  - S1 Wikimedia 172815415
  - S2 Wikimedia 39943534
  - S3 Pexels 12270481
  - S4 Wikimedia 34396499
  - S5 Wikimedia 27207173
- old 9229 eligible pool counts unchanged: 1 / 5 / 5 / 8 / 4.

The M8 visual-detail fix is now deployed and verified live.

Production after deploy:
- M5 v111: `31eaa7a9-98d1-44b6-bec6-416ef388753b`
- M6 v8: `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 v62: `90329f54-40fd-4382-92fd-2fd1e9ecea01`

M8 v62 deploy verification:
- published backup: `.backups/m8-before-detail-anchor-20260922-222108.json`
- non-M8 workflow fingerprint before/after: `31|18aedb2a006c96e8033db6f0770b6bee`
- live M8 nodes/connections/settings == Git: PASS
- Publisher 200
- Studio 200
- n8n restart count 0
- media worker healthy, restart count 0

## M5 9617 branch-safe precision fallback deployed

Production:
- M5 v114: `34b07b1f-2b22-4c6c-a68e-54e5e05fab22`
- M6 v8: `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 v62: `90329f54-40fd-4382-92fd-2fd1e9ecea01`

Deploy verification:
- published backup: `.backups/m5-before-branch-safe-20260923-040114.json`
- non-M5 workflow fingerprint before/after: `31|6d5bcd9e4ad7e94f6f9907f52426c741`
- live M5 nodes/connections/settings == Git: PASS
- Publisher 200
- Studio 200
- n8n restart count 0
- media worker healthy, restart count 0

Validation before deploy:
- focused timing 16/16 PASS;
- full suite 268/268 PASS;
- exact 9617 missing-branch regression PASS.

## Immediate next step

1. Read this PLAN before production action.
2. Commit/push the deployment checkpoint.
3. Verify Git clean and active project execution count = 0.
4. Run exactly ONE fresh PL15 on M5 v114 / M6 v8 / M8 v62.
5. Follow only that job to terminal state.
6. If it reaches M9 PASS, inspect the actual rendered MP4 technically, audio-wise, and scene-by-scene visually before EN30.
7. If it fails, fix only that exact demonstrated blocker from saved execution data.

## Acceptance sequence after PL15

Only after PL15 passes full manual acceptance:

1. EN30 — `how do bees make honey?`
2. RU45 — `как работает GPS?`
3. UK60 — `як утворюються вулкани?`

Run sequentially, never in parallel.

For each:
- complete production path must pass;
- technical MP4 checks must pass;
- actual final output must be manually reviewed;
- only demonstrated defects may be fixed.

## Definition of done

The project is done only when PL15 + EN30 + RU45 + UK60 all pass the complete production path and actual rendered outputs pass:

- requested timing window;
- 1080x1920 vertical output;
- H.264 / yuv420p / 30 fps;
- AAC audio;
- successful full decode;
- continuous natural narration;
- scene/visual semantic match;
- no missing/broken visual;
- no invalid-domain imagery;
- no semantic subject drift across scene cuts;
- actual final MP4 manually reviewed.

After all four pass:
- freeze M5/M6/M8/M9 production versions;
- record final evidence;
- create final Git checkpoint/tag;
- stop development.