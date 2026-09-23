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
- M5 Script/Storyboard: v117
  - activeVersionId: `e368d875-ebae-4c7b-ab38-6683c218a1d4`
- M6 Voiceover: v8
  - activeVersionId: `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 Visuals: v62
  - activeVersionId: `90329f54-40fd-4382-92fd-2fd1e9ecea01`

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

## Latest fresh PL15 result

Job: `94f5e4ff-b6b3-4ebf-b161-98deb3c7bbe7`

Pipeline:
- M4 PASS
- M5 v114 FAIL, execution `9621`
- M6/M8/M9 did not run
- script_run `9279883f-70e2-4d8c-88d8-c40452eddb00`
- terminal reason: `candidate provider usage is not a committed matching M5 TTS call`

Exact root cause:
- accepted MP3 came from probe 3 with usage key `m5-tts-probe:9279883f-70e2-4d8c-88d8-c40452eddb00:3`;
- ledger row 875 for that key is committed and otherwise valid, with `amount=189` characters;
- exact probe-3 TTS narration was 189 characters and contained three malformed visual-cut endings `,.`;
- after TTS, `Canonicalize Final Storyboard` removed those three extra periods and produced a 186-character final narration;
- `register_voiceover_candidate` correctly requires committed usage amount to equal `char_length(final narration)`, so it rejected the 189-character provider usage for the 186-character final text;
- therefore the defect was post-TTS narration mutation, not the ledger or DB validation.

## M5 9621 pre-TTS punctuation canonicalization tested locally

Fix:
- all five `Prepare Timing Probe` nodes clone the storyboard and apply the same deterministic `normalizeVisualCutPunctuation` used by final canonicalization before TTS;
- top-level narration is rebuilt from the normalized scene narrations before `character_count`, usage reservation, and Google TTS;
- stability probes inherit the already-normalized storyboard;
- final canonicalization becomes idempotent with respect to visual-cut punctuation;
- DB candidate/usage validation is unchanged and remains fail-closed.

Exact regression:
- 9621 malformed narration: 189 chars before cleanup;
- normalized narration: 186 chars before TTS;
- every Prepare Timing Probe 1–5 outputs exactly the 186-char canonical narration;
- every `character_count` equals the actual normalized narration length;
- no `,.`, `;.`, or `:.` artifact reaches TTS.

Validation:
- focused exact-audio tests: 8/8 PASS;
- full suite: 269/269 PASS;
- `git diff --check`: PASS;
- workflow JSON parse: PASS.

## M5 v115 pre-TTS punctuation fix deployed and verified

Production:
- M5 v115: `4ec491e1-fb68-4c5e-8125-c6d501e7d48d`
- M6 v8 unchanged
- M8 v62 unchanged
- M9 v1 unchanged

Deployment verification:
- published backup: `.backups/m5-before-pretts-punct-20260923-041956.json`
- non-M5 workflow fingerprint: `31|6d5bcd9e4ad7e94f6f9907f52426c741`, unchanged from v114 checkpoint
- live M5 nodes/connections/settings == Git: PASS
- Publisher 200
- Studio 200
- n8n restart count 0
- media worker healthy, restart count 0
- active project executions after verification: 0

## Latest fresh PL15 result

Job: `fd7d4a16-cb18-4871-b5ba-c53ef2126c63`

Pipeline:
- M4 PASS
- M5 v115 FAIL, execution `9629`
- M6/M8/M9 did not run
- script_run `2a2f9f43-4fd6-4f0b-af2e-6a7cfbcf500b`
- terminal reason: `M5 script workflow failed: 2, allowed 1 [line 216]`

Exact root cause:
- `Repair Final Word Count` returned the immutable original narration exactly;
- that retry itself is semantically valid;
- `Validate Final Word Count Retry` then builds a deterministic word-count hybrid from `retry`, `base`, and `pre_final` scene options;
- those options are inserted into the DP before per-option immutable semantic validation;
- the DP can therefore select a numerically attractive but semantically invalid scene option;
- only after hybrid selection does the node run `assertSemanticPreservation`, which rejected the chosen hybrid with `2, allowed 1`;
- word-count remains guidance; real TTS is the acceptance authority, so semantically invalid options must be excluded before DP rather than poisoning the whole retry.

## M5 9629 semantic-filtered exact-word hybrid tested locally

Fix:
- changed ONLY `Validate Final Word Count Retry`;
- every retry/base/pre_final scene option is validated against the immutable `Normalize Timing Probe` scene before entering deterministic DP;
- semantic-invalid options are excluded before numeric word-count optimization;
- a scene with no semantic-valid option fails closed;
- semantic thresholds, word-count guidance, and real-TTS timing gates are unchanged.

Exact regression:
- job `fd7d4a16-cb18-4871-b5ba-c53ef2126c63`;
- execution `9629`;
- provider retry equal to immutable original remains eligible;
- invalid filler variants cannot re-enter through base/pre_final hybrid choices.

Validation:
- exact 9629 tests: 2/2 PASS;
- full suite: 271/271 PASS;
- workflow JSON parse: PASS;
- `git diff --check`: PASS.

## M5 v116 semantic-filtered exact-word hybrid deployed and verified

Production:
- M5 v116: `64654d56-c7c8-481f-8bd3-37e37cc27289`
- M6 v8 unchanged
- M8 v62 unchanged
- M9 v1 unchanged

Deployment verification:
- published backup: `.backups/m5-before-9629-20260923-052246.json`
- non-M5 workflow fingerprint before/after: `31|6d5bcd9e4ad7e94f6f9907f52426c741`
- live M5 nodes/connections/settings == Git: PASS
- Publisher 200
- Studio 200
- n8n restart count 0
- media worker healthy, restart count 0

## Latest fresh PL15 result

Job: `72af62de-3c64-4b48-bf6b-c1395e07abed`

Pipeline:
- M4 PASS
- M5 v116 FAIL, execution `9633`
- M6/M8/M9 did not run
- script_run `b43017d9-d18f-49ae-9396-9f80ee389826`
- terminal reason: `water reservoir -> penstock pipe [line 696]`

Exact root cause:
- S1 narration ended `... gromadzi wodę,`;
- S2 began `która spada z wysokości.`;
- Polish relative pronoun `która` refers to terminal noun `wodę`, not to the S1 visual primary `water reservoir`;
- `previousVisualPrimaryIsLikelyTerminalAntecedent` tries to locate the English visual primary inside non-English narration;
- when no lexical match is found it currently returns `true` (fail-closed), which incorrectly asserts that the previous visual primary is the antecedent;
- this falsely rejects a legitimate visual transition to falling water / penstock pipe;
- the original generator-anaphora regression remains detectable because `generator` is a real cognate and is positively found at the end of the previous narration.

## M5 9633 cross-language antecedent fix tested locally

Fix:
- changed only the three storyboard validators containing `previousVisualPrimaryIsLikelyTerminalAntecedent`;
- no lexical match between English visual primary and non-English narration now means no inherited-primary restriction;
- positive terminal lexical matches remain fail-closed exactly as before;
- no topic-specific vocabulary or translation table was added.

Exact regression:
- `... gromadzi wodę,` + `która spada...` may move from reservoir visual to penstock/falling-water visual;
- existing generator `Który...` subject-drift regression still rejects visual-primary drift.

Validation:
- focused scene-segment tests: 13/13 PASS;
- full suite: 273/273 PASS;
- workflow JSON parse: PASS;
- `git diff --check`: PASS.

## M5 v117 cross-language antecedent fix deployed and verified

Production:
- M5 v117: `e368d875-ebae-4c7b-ab38-6683c218a1d4`
- M6 v8 unchanged
- M8 v62 unchanged
- M9 v1 unchanged

Deployment verification:
- published backup: `.backups/m5-before-9633-20260923-053041.json`
- non-M5 workflow fingerprint before/after: `31|6d5bcd9e4ad7e94f6f9907f52426c741`
- live M5 nodes/connections/settings == Git: PASS
- Publisher 200
- Studio 200
- n8n restart count 0
- media worker healthy, restart count 0

## Latest fresh PL15 result

Job: `835c8fc3-7d0b-425f-ab9e-62c19788c8a3`

Pipeline:
- M5 v117 PASS
- M6 v8 PASS
- M8 v62 FAIL, execution `9640`
- M9 did not run
- visual_run `27cf596d-0c2f-4e3c-a021-41f6db8a6217`
- terminal: `no compliant relevant visual candidate for shot S3-A`

Observed M8 pools:
- S1: 8 eligible
- S2: 6 eligible
- S3: 0 eligible
- S4: 0 eligible
- S5: 10 eligible

S3 contract:
- narration: `Turbina napędza generator,`
- primary: `electric generator`
- secondary: `turbine machine`
- intent: generator connected to turbine in a power station

S4 contract:
- narration: `Który produkuje prąd.`
- primary: `electrical generator`
- intent: electrical generator/equipment generating electricity inside a plant

Confirmed retrieval root causes:
1. repeated machinery domain inference promotes output/process words such as `electricity` into `domain_context_terms`; this creates a hard metadata gate even though `electricity` is not the machinery domain;
2. provider queries omit structural retrieval terms already implied by the storyboard:
   - two mandatory machinery subjects need a combined `... unit` retrieval form;
   - `inside ... plant/station` needs an `... interior` retrieval form;
3. scorer behavior is correct to reject the currently returned weak/museum/diagram/context-only results.

Live diagnostic evidence (no production mutation):
- generic query `hydroelectric generator turbine unit interior` immediately returned real turbine-generator-unit interiors;
- `hydroelectric generator turbine unit power station` returned turbine-generator units;
- `hydroelectric plant interior generator` returned real generator installations/interiors;
- `hydroelectric power station interior generator` returned generator-room images.
Therefore fix retrieval planning, not QA thresholds.

## M8 9640 retrieval-planning fix validated locally

Scope:
- request planners only;
- scorer and eligibility thresholds unchanged.

Changes:
- generic output/process words `electricity`, `energy`, `current`, `voltage`, `output` are no longer promoted into hard machinery domain context;
- when a shot has 2+ machinery heads, retrieval keeps those machinery heads and adds `unit` as provider-query structure only;
- for a repeated output-focused machinery scene explicitly inside/interior an operating location, retrieval prefixes the location plus `interior`; these are not hard scorer domains;
- original storyboard `query` provenance is unchanged.

Exact 9640 generated queries:
- S3 q3: `hydroelectric generator turbine unit`
- S4 q3: `hydroelectric plant interior electrical generator`

Validation:
- focused 9640 planner regressions: 10/10 PASS;
- full suite: 283/283 PASS;
- deterministic M8 execution 9229 replay: PASS with the same five accepted assets;
- live non-mutating Wikimedia + current scorer:
  - S3 q3: 2 eligible assets, IDs `33715545`, `33715543`;
  - S4 q3: 2 eligible assets, IDs `33760010`, `34186551`.
- no production mutation has occurred yet.

## M8 v63 deployed and verified

- M8 v63 activeVersionId `7256ee89-8b9a-47df-bdc9-66bd2136df35`.
- M5 v117 / M6 v8 / M9 v1 unchanged.
- Published backup: `.backups/m8-before-9640-20260923-060948.json`.
- Non-M8 workflow fingerprint unchanged:
  `31|32241746eba2f4470b60db4bebbf74f3`.
- Live M8 nodes/connections/settings == Git: PASS.
- Publisher 200; Studio 200.
- n8n running, restart 0.
- media worker healthy, restart 0.

## Latest fresh PL15 failure — M5 execution 9660

Job: `6aa86246-ec15-4514-a688-d150129d35ad`

- M5 production version: v117 / `e368d875-ebae-4c7b-ab38-6683c218a1d4`.
- M5 execution: `9660`.
- script_run: `a5985b2f-c8b6-4342-9ea9-57b00f9a2f35`.
- Terminal job state: `script_failed`.
- Failure: `final measured word-count retry too far from target before TTS: got 26, target 29, allowed delta 2`.

Verified timing evidence for the final 26-word narration:
- Probe 4: 12.984 s
- Stability A: 13.200 s
- Stability B: 13.128 s
- PL15 final M6 lower timing bound is approximately 14.2 s, so allowing 26 words through would be an invalid weakening of the gate.

Verified provider-contract failure:
- measured correction correctly requested LONGER / about 29 words;
- hard exact retry required total 29 with scene targets `[10,6,4,4,5]`;
- Gemini 3.5 Flash Lite returned only 22 words with counts `[8,4,3,3,4]`;
- deterministic semantic hybrid could recover only 26 words, still 3 short;
- therefore current validator correctly failed closed.

Current blocker is not TTS stochasticity and not the timing tolerance. It is non-compliance of the bounded final exact-word Gemini retry.

## M5 execution 9660 fix implemented and tested

Implemented:
- existing final exact-word validator still fails closed when the semantic-valid nearest total is too far from target;
- only that exact `too far from target before TTS` error is classified for one extra bounded compliance retry;
- all provider/parse/semantic errors continue to script failure;
- compliance retry receives previous returned total/per-scene counts, immutable original narration, current semantic-valid narration, exact hard total and exact hard per-scene counts;
- compliance retry cannot loop: its validator success goes to existing Probe 5 and its error goes directly to script failure.

Execution 9660 deterministic regression:
- previous Gemini response detected as 22 words with [8,4,3,3,4];
- required counts [10,6,4,4,5], total 29;
- semantic-valid exact 29-word response passes the same final validator;
- repeated noncompliant 22-word response still fails closed.

Validation:
- focused compliance/provider tests: 10/10 PASS;
- full project suite: 288/288 PASS;
- M5 graph validation: PASS, 132 nodes;
- M5 Code-node syntax: 59/59 PASS;
- `git diff --check`: PASS;
- M5 JSON parse: PASS.

## M5 v118 compliance fix deployed and verified

Production:
- M5: v118 / `346ad9c2-1cc2-4c8d-ac37-6ae540b1fff1`
- M6: v8 / `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8: v63 / `7256ee89-8b9a-47df-bdc9-66bd2136df35`
- M9: v1 / `5b6c937c-1767-4c3e-99c4-31ea38a26961`

Deploy verification:
- published backup: `.backups/m5-before-9660-compliance-20260923-083302.json`
- non-M5 fingerprint before/after: `31|c27d87623ffd8872701cef34695d8265`
- live M5 nodes/connections/settings == Git: PASS
- Publisher 200
- Studio 200
- n8n running, restart count 0
- media worker healthy, restart count 0

## Fresh PL15 manual acceptance failure — execution 9672

Job: `ab79e346-a7d7-45c4-9bc9-a82212bab1c4`

Pipeline:
- M4 execution 9671: PASS
- M5 execution 9672 on v118 `346ad9c2-1cc2-4c8d-ac37-6ae540b1fff1`: PASS
- M6 execution 9673 on v8: PASS
- M7 execution 9674: PASS
- M8 execution 9675 on v63: PASS
- M9 execution 9676 on v1: PASS
- job status: `machine_qa_passed`

Technical render: PASS
- 1080x1920
- H.264 / yuv420p / 30 fps
- AAC mono 24 kHz
- duration 15.066667 s
- full decode clean

Lexical alignment: PASS
- global coverage 1.000
- 23 lexical tokens
- audio duration 15.048 s
- alignment method `whisper_token_sequence_match`

Manual narration/audio continuity: FAIL
- final canonical narration contains artificial sentence breaks at visual cuts:
  - `Spadająca masa cieczy napędza. Turbinę wodną...`
  - `...która następnie. Porusza generator...`
- silence detection on the actual final MP3 found internal pauses including approximately 0.776 s, 0.458 s and 0.992 s around these scene boundaries.

Exact root cause from M5 execution 9672:
- `Validate Storyboard` and `Normalize Timing Probe` preserved one natural continuous narration with mid-sentence visual cuts.
- Gemini `Repair Timing Precision Retry` also returned the correct segment surfaces without added periods:
  - `Elektrownia wodna gromadzi wodę`
  - `w wielkim zbiorniku za tamą.`
  - `Spadająca masa cieczy napędza`
  - `turbinę wodną, która następnie`
  - `porusza generator wytwarzający czysty prąd elektryczny.`
- `Validate Timing Precision Retry` then called `normalizeSentenceSurface`, which uppercased every segment start and appended a terminal period to every segment.
- This validator behavior contradicts the continuous-narration/visual-cut contract.
- Search of current M5 code found this forced sentence-surface normalization only in `Validate Timing Precision Retry`.

## Immediate next step

1. Do NOT run EN30 or another PL15 yet.
2. Fix only `Validate Timing Precision Retry`:
   - normalize whitespace only for each visual narration segment;
   - do not uppercase scene starts;
   - do not append terminal punctuation per scene;
   - keep the existing joined-narration requirement: the complete joined narration must start normally and end with sentence punctuation.
3. Add deterministic regression from execution 9672 proving the exact Gemini response remains one continuous narration.
4. Confirm no other late M5 validator forces sentence punctuation per visual segment.
5. Run focused tests, full suite, M5 graph and Code-node syntax.
6. Update PLAN/handoff/evidence; commit/push.
7. Deploy ONLY M5 after active project execution count = 0 with backup/fingerprint/live==Git verification.
8. Run exactly one fresh PL15.
9. Manually review its actual MP4, audio continuity and every visual scene before EN30.

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