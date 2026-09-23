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

## M5 execution 9672 continuity fix implemented and tested

Implemented only in `Validate Timing Precision Retry`:
- removed forced capitalization of every visual segment start;
- removed forced terminal punctuation on every visual segment;
- each segment now receives whitespace normalization only;
- existing semantic fallback/anti-runaway checks remain unchanged;
- existing joined narration completeness gate remains unchanged.

Exact execution 9672 regression proves:
- Gemini precision response keeps mid-sentence visual cuts:
  - `Elektrownia wodna gromadzi wodę`
  - `w wielkim zbiorniku za tamą.`
  - `Spadająca masa cieczy napędza`
  - `turbinę wodną, która następnie`
  - `porusza generator wytwarzający czysty prąd elektryczny.`
- validator output preserves these exact surfaces;
- joined narration equals the original continuous narration;
- artificial `napędza. Turbinę` and `następnie. Porusza` breaks are absent.

Validation:
- focused continuity/precision/scene tests: 18/18 PASS;
- full project suite: 290/290 PASS;
- M5 graph: PASS, 132 nodes;
- M5 Code-node syntax: 59/59 PASS;
- diff/JSON checks: PASS.

## M5 v119 continuity fix deployed and verified

Production:
- M5: v119 / `bad8d367-3399-4ada-87c4-3a6d6c044b62`
- M6: v8 / `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8: v63 / `7256ee89-8b9a-47df-bdc9-66bd2136df35`
- M9: v1 / `5b6c937c-1767-4c3e-99c4-31ea38a26961`

Deploy verification:
- published backup: `.backups/m5-before-9672-continuity-20260923-085258.json`
- non-M5 fingerprint before/after: `31|c27d87623ffd8872701cef34695d8265`
- live M5 nodes/connections/settings == Git: PASS
- Publisher 200
- Studio 200
- n8n restart count 0
- media worker healthy, restart count 0

## Immediate next step

1. Read PLAN before the next production action.
2. Verify Git clean and active project executions = 0.
3. Run exactly ONE fresh PL15 on M5 v119 / M6 v8 / M8 v63 / M9 v1.
4. Follow only that job to terminal state.
5. If machine QA passes:
   - inspect actual final MP4 technically;
   - verify canonical narration remains continuous;
   - inspect actual audio silence/pause structure;
   - review every visual scene against narration.
6. If PL15 passes manual acceptance, checkpoint GitHub and proceed to EN30.
7. If it fails, record and fix only the exact demonstrated blocker; no parallel job.

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

## Fresh PL15 v119/v63 failure — M8 execution 9683

Job: `a6d8d4dc-c30c-41ef-b816-0301fdfd1cda`

Pipeline:
- M4 PASS
- M5 execution 9680 on v119: PASS
- M6 execution 9681 on v8: PASS
- M7 execution 9682: PASS
- M8 execution 9683 on v63: FAIL
- M9 did not run
- visual_run: `02a9de5e-17f1-49b1-b51b-e575ef1d0bc4`

Eligible pools:
- S1: 10
- S2: 2
- S3: 2
- S4: 0
- S5: 3

Exact S4:
- narration: `który produkuje prąd,`
- visual intent: `electric power generation equipment in hydro plant`
- must_show: `electric generator`
- provider searches completed 9/9 for S4.

Demonstrated valid-context candidate:
- Wikimedia `135264822`
- direct caption states Wienerbruck hydro power plant / Generator 2 / `in working condition`
- category includes `Hydroelectric generators`
- current scorer: 81, rejected only for `missing_operational_setting_context`.

Confirmed code defect:
- Wikimedia intentionally exposes a short direct caption through secondary/context metadata;
- operational-setting validation checks only `strongSet` (title/object/categories);
- therefore explicit plant/working-condition context in the direct caption is ignored.
- Primary depiction gates are not the problem and must not be weakened.

Next:
1. Add exact 9683 positive regression and a `disused` negative.
2. Use combined strong + secondary metadata only for operational location/lifecycle evidence.
3. Keep primary subject, must_show, domain, thresholds and retrieval unchanged.
4. Focused tests -> full suite -> deterministic 9229 replay -> diff/JSON checks.
5. No new PL15 before fix is tested, checkpointed and deployed.


## M8 execution 9683 operational-context fix validated

Scoped fix:
- operational context/lifecycle checks now use an explicit `contextSet`;
- Pixabay and Pexels keep their previous operational-context evidence source (`strongSet`);
- Wikimedia alone combines `strongSet` with the already-existing concise direct-caption/secondary metadata;
- primary depiction, must_show, domain context, visual-detail and relevance thresholds are unchanged;
- `disused/decommissioned/abandoned/inactive/retired` are explicit non-operational lifecycle conflicts.

Exact regression:
- Wikimedia `135264822` with direct caption `hydro power plant ... in working condition` now satisfies the S4 operational setting;
- equivalent metadata marked `disused` is rejected;
- caption-only mention of a generator still cannot prove the primary depicted subject.

Validation:
- focused operational/context + 9601 + 9640 tests: 42/42 PASS;
- full suite: 293/293 PASS;
- deterministic 9229 replay: 12/12 PASS;
- selected 9229 assets unchanged: 172815415 / 39943534 / Pexels 12270481 / 34396499 / 27207173;
- 9229 eligible counts unchanged: 1 / 5 / 5 / 8 / 4;
- M8 Code nodes: 10/10 syntax PASS;
- workflow JSON parse: PASS;
- `git diff --check`: PASS.

Next:
1. Commit/push this tested M8 fix.
2. Verify active project executions = 0.
3. Export published M8 backup and capture non-M8 fingerprint.
4. Deploy only M8; version must increment exactly once.
5. Verify live M8 == Git, non-M8 fingerprint unchanged, Publisher/Studio 200, containers healthy, no restart.
6. Then run exactly one fresh PL15.


## M8 v64 operational-context fix deployed and verified

Production:
- M5 v119 / `bad8d367-3399-4ada-87c4-3a6d6c044b62`
- M6 v8 / `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 v64 / `88b9f81a-6d41-452b-8a35-082b7c088006`
- M9 v1 / `5b6c937c-1767-4c3e-99c4-31ea38a26961`

Deploy verification:
- M8 version incremented exactly once: v63 -> v64.
- Published backup: `.backups/m8-before-9683-context-20260923-123042.json`.
- Backup SHA256: `f535079c5f3ff6f538fc29c20c4a3635a106707227e76a7d3567c28d6ae5fd47`.
- non-M8 fingerprint before/after unchanged: `31|935f3b89581cc695b22bca91b315f846`.
- live M8 nodes/connections/settings == Git: PASS.
- Publisher 200; Studio 200.
- n8n running, restart count 0.
- media worker running/healthy, restart count 0.
- Postgres and SearXNG healthy.
- active project executions after verification: 0.
- no unrelated workflow, credential, service or container changed.

## Immediate next step after M8 v64

1. Verify Git clean and active project executions = 0.
2. Run exactly ONE fresh PL15:
   - topic: `jak działa elektrownia wodna?`
   - language: `pl`
   - duration: 15
3. Follow only that job to terminal state.
4. If it reaches machine QA, inspect the exact final MP4 technically, audio/narration continuity and S1-S5 visual correspondence.
5. If PL15 passes manual acceptance, checkpoint and proceed to EN30.
6. If it fails, checkpoint the exact blocker before any new fix; do not start another PL15.


## Fresh PL15 on M5 v119 / M8 v64 — M5 execution 9687 failed

Job: `bfac49a7-bde2-4ec0-85fc-7dd9b6afbc36`

Pipeline:
- M4 PASS
- M5 v119 execution `9687`: FAIL
- M6/M7/M8/M9 did not run
- script_run: `e0bed2f3-7cce-4004-83b9-ced1db6b75de`
- terminal job status: `script_failed`

Exact failure:
- `got 27, target 31, allowed delta 2 [line 431]`.

Execution-tail evidence:
- final measured correction ran;
- final measured word-count retry ran;
- `Classify Final Measured Word Count Retry Failure` ran;
- `Route Final Measured Word Count Compliance Retry` ran;
- no Build/Repair/Validate compliance-retry node executed;
- execution routed to Prepare Script Failure -> Fail Script -> Raise Script Failure.

No root cause is claimed yet.

Immediate next step:
1. Inspect exact 9687 classifier/router data and the v119 classifier conditions.
2. Prove why the bounded compliance retry was not entered for 27 vs target 31.
3. Record the proven root cause before changing M5.
4. Do not start another PL15.


## M5 execution 9687 — root cause proven

Production evidence:
- classifier input carried `$json.error` as the string:
  `got 27, target 31, allowed delta 2 [line 431]`;
- raw execution ref for that value: `1684`;
- `Classify Final Measured Word Count Retry Failure` output:
  - `compliance_retry=false`
  - `compliance_retry_error_message=""` (raw ref `857`).

Confirmed code defect:
- classifier only treats `$json.error` as usable when it is an object;
- string-form n8n errors are discarded before classification;
- therefore the existing bounded compliance retry was skipped even though the failure came from the final measured word-count retry path.

Fix scope:
1. Normalize string-form and object-form `$json.error`.
2. Keep the existing retry class narrow; do not retry arbitrary M5 failures.
3. Add exact regression for execution 9687 string-form error.
4. Focused tests, full suite, diff/JSON/Code-node checks.
5. Checkpoint before M5-only deploy.
6. No new PL15 until fix is tested and deployed.


## M5 execution 9687 classifier fix validated

Change:
- `Classify Final Measured Word Count Retry Failure` now normalizes both object-form and string-form `$json.error`;
- the old full retry message still qualifies;
- n8n's stripped string form qualifies only when it exactly matches `got <N>, target <N>, allowed delta <N> [line <N>]`;
- unrelated string errors such as provider 503 remain non-retry failures;
- no retry loop was added and no timing/semantic validator was weakened.

Validation:
- focused compliance/provider tests: 10/10 PASS;
- full suite: 293/293 PASS;
- M5 Code nodes: 59/59 syntax PASS;
- workflow JSON parse: PASS;
- `git diff --check`: PASS.

Next:
1. Commit/push this tested M5 fix.
2. Verify active project executions = 0.
3. Export published M5 v119 backup and capture non-M5 workflow fingerprint.
4. Deploy only M5 and publish current version; expect exactly v120.
5. Verify live M5 nodes/connections/settings == Git; non-M5 fingerprint unchanged; Publisher/Studio 200; no container restart.
6. Run exactly one fresh PL15 and follow it to terminal state.


## M5 v120 classifier fix deployed and verified

Production:
- M5 v120 / `28f7440c-9410-4143-8962-352f967cfe1f`
- M6 v8 / `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 v64 / `88b9f81a-6d41-452b-8a35-082b7c088006`
- M9 v1 / `5b6c937c-1767-4c3e-99c4-31ea38a26961`

Deploy verification:
- M5 incremented exactly once: v119 -> v120.
- Published backup: `.backups/m5-before-9687-classifier-20260923-131636.json`.
- Backup SHA256: `4a512505d75848a7f432cf4dc328bd0f5113c502f877ff0d19cbd6661402c50e`.
- non-M5 fingerprint unchanged: `31|cfacbe4e094739b106490c3c93ec2506`.
- live M5 nodes/connections/settings == Git: PASS.
- Publisher 200; Studio 200.
- n8n running, restart 0.
- media worker running/healthy, restart 0.
- Postgres and SearXNG healthy.
- active project executions = 0.

Immediate next step:
1. Verify Git clean and active project executions = 0.
2. Run exactly ONE fresh PL15 on v120/v64.
3. Follow only that job to terminal state.
4. If it reaches M9 machine PASS, perform exact MP4 technical/audio/visual review before EN30.
5. If it fails, checkpoint the exact new blocker before any new fix or retry.


## Fresh PL15 on M5 v120 — execution 9692 failed; root cause proven

Job: `4dc1af7d-0ec9-4af5-8557-e926beef4cac`

Pipeline:
- M4 PASS
- M5 v120 execution `9692`: FAIL
- M6/M7/M8/M9 did not run
- script_run: `50024835-3e15-4405-b33c-6fa5ef2cec3a`
- terminal error: `11 [line 251]`

Exact final-duration evidence:
- measured TTS: 12096 ms
- target: 15000 ms
- internal repair aim: 14600 ms
- current narration: 22 words
- target narration: about 27 words
- builder target scene counts: `[10,5,4,3,5]`
- validator PL15 hard scene bound: 2-10 words
- Gemini returned scene counts: `[11,7,5,7,6]`
- S1 response had 11 words.

Confirmed contract defect:
- `Build Final Duration Repair` correctly clamps calculated scene targets to max 10;
- its prompt then says every per-scene `target_words` is only a preference and does not state the hard 2-10 scene bound;
- Gemini therefore produced S1 with 11 words;
- `Validate Final Duration Repair` correctly rejected it at the hard max check.

Fix scope:
1. Keep per-scene target_words as soft timing guidance.
2. Add explicit HARD structural rule: every returned scene must remain within 2-`maxSceneWords` words.
3. Do not weaken validator, semantic preservation, timing or sentence-continuity gates.
4. Add exact 9692 regression.
5. Focused/full tests, JSON/diff/Code-node checks.
6. Checkpoint before M5-only deploy; no new PL15 before deploy.


## M5 execution 9692 late-timing scene-bound fix validated

Change:
- `Build Final Duration Repair` and `Build Final Measured Correction` now explicitly state a HARD per-scene structural bound;
- for PL15 every returned narration segment must remain within 2-10 whitespace-separated words;
- per-scene `target_words` remain soft timing guidance inside that hard bound;
- validator, semantic preservation, timing acceptance and narration-continuity rules are unchanged.

Validation:
- focused late-timing + semantic tests: 37/37 PASS;
- full suite: 294/294 PASS;
- M5 Code nodes: 59/59 syntax PASS;
- workflow JSON parse: PASS;
- `git diff --check`: PASS.

Next:
1. Commit/push this tested M5 fix.
2. Verify active project executions = 0.
3. Export published M5 v120 backup and capture non-M5 fingerprint.
4. Deploy only M5; expect exactly v121.
5. Verify live M5 == Git, non-M5 fingerprint unchanged, Publisher/Studio 200, no restart.
6. Run exactly one fresh PL15 and follow it to terminal state.


## M5 v121 late-timing scene-bound fix deployed and verified

Production:
- M5 v121 / `692ceedd-a51c-45c5-bf1e-c85814129e4d`
- M6 v8 / `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 v64 / `88b9f81a-6d41-452b-8a35-082b7c088006`
- M9 v1 / `5b6c937c-1767-4c3e-99c4-31ea38a26961`

Deploy verification:
- M5 incremented exactly once: v120 -> v121.
- Backup: `.backups/m5-before-9692-scene-bound-20260923-133216.json`.
- Backup SHA256: `92098a8015c357dfb373dba9f2f84899e22f0913e85401369c12f238183e9f51`.
- non-M5 fingerprint unchanged: `31|cfacbe4e094739b106490c3c93ec2506`.
- live M5 nodes/connections/settings == Git: PASS.
- Publisher 200; Studio 200.
- n8n restart 0; media worker healthy restart 0.
- Postgres/SearXNG healthy.
- active project executions = 0.

Immediate next step:
1. Verify Git clean and active project executions = 0.
2. Run exactly ONE fresh PL15 on v121/v64.
3. Follow only that job to terminal state.
4. If machine QA passes, inspect exact MP4 technically and manually before EN30.
5. If it fails, checkpoint the exact blocker before any new change.


## Fresh PL15 on M5 v121 — execution 9699 blocker checkpoint

Job: `d0d127b8-c70a-4cef-b3ae-1dc2cc43e104`

Pipeline:
- M4 PASS
- M5 v121 execution `9699`: FAIL
- M6/M7/M8/M9 did not run
- script_run: `b97c46b5-0b89-47de-a14d-1879eaffe669`

Exact sequence:
- initial storyboard rejected: `electric generator -> power lines [line 698]`
- first repair rejected: `electric generator -> transformer station [line 698]`
- second repair rejected: `electric generator -> electrical substation [line 698]`
- final failing node: `Validate Repaired Storyboard 2`

Scene context:
- S4 narration: `Obracający się wirnik porusza generator,`
- S4 primary: `electric generator`
- S5 narration: `który wytwarza czystą energię elektryczną.`
- S5 does not explicitly name a new concrete visual primary.
- The validator is correct: the likely inherited primary is the generator.

Confirmed repair-path defect:
- all three model attempts violate the existing anaphoric visual-primary contract;
- Repair 2 received only the stripped diagnostic `electric generator -> transformer station [line 698]`;
- n8n removed the descriptive validator prefix, leaving an opaque `A -> B [line N]` message;
- the validator must remain fail-closed.

Candidate fix scope:
- normalize stripped `A -> B [line N]` errors in both storyboard repair builders into an explicit generic anaphoric visual-primary diagnosis;
- no generator/substation/hydropower hardcoding;
- no validator weakening.

Shared working-tree note:
- a parallel process has already placed an uncommitted candidate implementation and regression test in the working tree;
- do not overwrite it;
- validate it before fix commit/deploy.

Next:
1. Commit this docs/evidence blocker checkpoint only.
2. Run focused regression tests on the existing candidate fix.
3. Run full suite, JSON/diff/M5 Code-node checks.
4. If all PASS, record tested fix, commit/push code+test+docs.
5. M5-only deploy after zero-active check/backup/fingerprint.
6. No new PL15 before verified deploy.


## M5 execution 9699 repair-error normalization validated

Implemented only in `Build Storyboard Repair` and `Build Storyboard Repair 2`:
- stripped anaphoric validator diagnostics are expanded into an explicit antecedent-preservation repair instruction;
- unrelated validation errors pass through unchanged;
- no topic-specific vocabulary;
- storyboard validators and fail-closed gates are unchanged.

Validation:
- focused scene/visual tests: 35/35 PASS;
- full suite: 295/295 PASS;
- M5 Code nodes: 59/59 syntax PASS;
- workflow JSON parse: PASS;
- `git diff --check`: PASS.

Next: commit/push the tested fix, then M5-only deploy with zero-active check, backup and non-M5 fingerprint. No new PL15 before verified deploy.


## M5 v122 repair-error normalization deployed and verified

Production:
- M5 v122 / `4a9a48fd-985c-4f77-b592-44a0945377dd`
- M6 v8 / `0bcabe39-ae90-42fe-842b-8a56ad238709`
- M8 v64 / `88b9f81a-6d41-452b-8a35-082b7c088006`
- M9 v1 / `5b6c937c-1767-4c3e-99c4-31ea38a26961`

Deploy verification:
- M5 incremented exactly once: v121 -> v122.
- Equivalent published predeploy backups:
  - `.backups/m5-before-9699-repair-error-20260923-135152.json`
  - `.backups/m5-before-9699-anaphoric-20260923-135204.json`
- Both backups SHA256: `a7ff82d9608b05cd8648d856dd9f2023adcd7208dd47d55f1f4cb814a4f20628`.
- live M5 nodes/connections/settings == Git: PASS.
- non-M5 fingerprint unchanged: `31|cfacbe4e094739b106490c3c93ec2506`.
- Publisher 200; Studio 200.
- n8n running, restart 0.
- media worker running/healthy, restart 0.
- Postgres/SearXNG healthy.
- active project executions = 0.

Immediate next step:
1. Verify Git clean and active project executions = 0.
2. Run exactly ONE fresh PL15 on v122/v64.
3. Follow only that job to terminal state.
4. If machine QA passes, inspect the exact MP4 technically and manually before EN30.
5. If it fails, checkpoint the exact new blocker before any new change.


## Fresh PL15 v122/v64 — machine PASS, manual visual FAIL

Job: `e8d662c9-cd28-4228-9169-6ac875ff0d16`

Pipeline:
- M4 execution 9702 PASS
- M5 v122 execution 9703 PASS
- M6 v8 execution 9704 PASS
- M7 execution 9705 PASS
- M8 v64 execution 9706 PASS
- M9 v1 execution 9707 PASS
- job status: `machine_qa_passed`

Final MP4:
- `/data/renders/e8d662c9-cd28-4228-9169-6ac875ff0d16/final.mp4`
- SHA256 `c5c889531ab2f90a7ec57b6be2eeed4439aa3ae32f0ad297a18d793755781e4f`
- 1080x1920, H.264 + AAC, 30 fps
- video/audio duration: 14496 ms / 14496 ms
- Whisper review matches the intended continuous Polish narration.

Manual visual review:
- S1 dam/reservoir: relevant.
- S2 concrete dam: relevant.
- S3 hydro machinery/turbine hall: relevant.
- S4 hydro generator: relevant.
- S5 power grid: relevant.
- BUT all five still images are letterboxed vertically instead of filling the 9:16 frame.

Measured content crops from the actual rendered MP4:
- S1: `crop=1080:1620:0:150`
- S2: `crop=1080:1384:0:268`
- S3: `crop=1080:1698:0:110`
- S4: `crop=1080:720:0:600`
- S5: `crop=1080:1820:0:50`

S4 is the clearest failure: only 720 of 1920 vertical pixels contain the photo; the rest is black bars.

Manual acceptance: FAIL.

Next:
1. Inspect M9/media-worker still-image scaling.
2. Fix generic still-image rendering to fill 1080x1920 without distortion, using safe crop rather than black-bar contain.
3. Keep all existing machine QA and semantic/visual gates.
4. Add regression for landscape/square stills rendered to 9:16.
5. Full tests + deterministic render check.
6. Deploy only the responsible render component/workflow.
7. Then run exactly one fresh PL15.


## Render letterbox root cause and safe fill strategy

Confirmed current renderer:
- `_render_segment` uses proportional `force_original_aspect_ratio=decrease`;
- then pads to 1080x1920 with `color=black`;
- this exactly explains the manual cropdetect/letterbox failure.

Do NOT simply restore hard center crop:
- historical PL15 v44 manual review already documented that center-crop removed important edge content from selected visuals;
- commit `fbce953` intentionally switched from center crop to full-source fit for that reason.

Updated fix strategy:
1. Preserve the complete source as a proportional foreground.
2. Fill the entire 1080x1920 background with a center-cropped copy of the same source.
3. Blur the fill background so it does not compete with the foreground.
4. No black padding and no foreground distortion.
5. Update `render-fit-regression.py` to require both edge-landmark preservation and non-black full-frame fill.
6. Keep machine QA, provenance, audio and semantic/visual gates unchanged.


## Blurred-fill still-image renderer fix validated

Implemented:
- still-image foreground remains complete and proportional;
- the same source fills 1080x1920 behind it using cover + center crop + Gaussian blur;
- black padding is removed;
- hard foreground crop is not reintroduced;
- video-media branch is unchanged in this scoped fix.

Regression:
- real FFmpeg `render-fit-regression.py`: 3/3 PASS for 1600x1611, 1920x1080 and 1080x1920;
- synthetic left/right edge landmarks remain visible;
- top/bottom fill probes are non-black.

Exact failed PL15 assets rendered offline with the candidate:
- S1 `crop=1080:1920:0:0`
- S2 `crop=1080:1920:0:0`
- S3 `crop=1080:1920:0:0`
- S4 `crop=1080:1920:0:0`
- S5 `crop=1080:1920:0:0`
- manual S2/S4 spot-check confirms complete foreground preserved with blurred fill and no black bars.

Validation:
- Python compile PASS;
- render-fit regression PASS;
- full Node suite 295/295 PASS;
- `git diff --check` PASS.

Next:
1. Commit/push tested renderer + regression + evidence.
2. Capture current media-worker image/health and build only media-worker.
3. Recreate only `shorts-v2-media-worker-1`.
4. Verify running/healthy, restart count, image/source match, supporting services unchanged.
5. Run exactly one fresh PL15 and manually review the actual final MP4.


## Blurred-fill media-worker deployed and verified

Deployment:
- only Compose service `media-worker` rebuilt/recreated;
- old image: `sha256:74433bc72ce63976434949c8c5144bf6f79596adb689d381db4155191b741220`;
- new image: `sha256:40d31f96de302b8bf0f69bd07e5d9dac2d82a8ed8e102fc0a1c383ea4129fd3c`;
- rollback image recorded in `.backups/worker-before-blurred-fill-20260923-141837.txt`.

Verification:
- worker running / healthy / restart 0;
- live `/worker/server.py` SHA256 matches Git exactly: `c6ee183981d45283f99f52a835906a9546af9bdba9fdf2b71ca672c97a2fae91`;
- Postgres, SearXNG and n8n container IDs unchanged;
- active project executions = 0;
- Publisher 200; Studio 200;
- Git clean and HEAD == origin/main.

Immediate next:
1. Commit/push this deploy checkpoint.
2. Run exactly ONE fresh PL15.
3. Follow only that job to terminal state.
4. If machine QA passes, inspect exact final MP4 frames, cropdetect and audio before deciding acceptance.
5. If PL15 passes manual acceptance, checkpoint and proceed to EN30.


## Fresh PL15 after blurred-fill deploy — machine PASS, manual visual FAIL

Job: `33aa659d-e6b6-4529-8e41-8dd830f3b920`

Pipeline:
- M3 9708 PASS
- M4 9710 PASS
- M5 v122 9711 PASS
- M6 v8 9712 PASS
- M7 9713 PASS
- M8 v64 9714 PASS
- M9 v1 9715 PASS
- status: `machine_qa_passed`

Final MP4:
- SHA256 `f042e93193ad9a64b97299bc095d4e1b94388658a0143bb7519ec90570749379`
- 1080x1920 H.264/AAC, 30 fps
- duration/audio: 14784 / 14784 ms.

Renderer/manual format check:
- blurred-fill fix works on the actual production MP4;
- cropdetect: S1 1080x1900, S2-S5 1080x1920;
- S1's remaining dark edge is embedded in the historical source itself, not renderer black padding;
- no previous top/bottom letterbox behavior remains.

Audio manual check: PASS.
Whisper:
`Woda gromadzona jest w wielkim zbiorniku za tamą. Następnie spada z dużej wysokości, uderzając bezpośrednio w turbinę wodną, która napędza nowoczesny generator wytwarzający czysty prąd elektryczny.`

Visual manual check:
- S1 Wikimedia 124944982: FAIL. Historical small dam/weir scene does not visibly establish the requested large reservoir behind the dam.
- S2 Wikimedia 81510447: PASS. Clear hydro penstock pipes.
- S3 Pexels 12270481: PASS. Industrial hydro machinery.
- S4 Wikimedia 34522651: PASS. Hydroelectric generator bay / turbine-generator shaft.
- S5 Wikimedia 136934049: FAIL. Actual photo shows a forest clearing/survey tripod; no transformer or transformer station is visibly depicted. Transformer/substation/transmission terms are catalog/contract context, not the photographed subject.

Manual acceptance: FAIL.

Confirmed progress:
- render letterboxing is fixed in production;
- remaining blocker is M8 depiction grounding for contextual Wikimedia catalog metadata.

Next:
1. Inspect exact Wikimedia M8 strong/secondary metadata construction for selected 124944982 and 136934049.
2. Prove why contextual title/catalog terms satisfy primary subject.
3. Tighten generic depiction grounding only; no asset IDs, hydro terms or topic-specific blacklists.
4. Add exact regressions for contextual/catalog title false positives while preserving direct descriptive title/photo positives.
5. Full tests + deterministic 9229 and current regressions.
6. M8-only deploy, then one fresh PL15.


## 2026-09-23 — selectable visual validation mode

Product decision:
- Studio exposes a user-selectable visual validation mode for each job.
- `metadata` mode keeps the current deterministic M8 metadata/scoring path and does not call Gemini Vision.
- `gemini` mode adds pixel-level validation of selected visual candidates before they become final scene assets.
- Do not intentionally degrade `metadata` mode; it is the lower-cost path with less semantic assurance.
- Gemini must validate still frames/images, not the complete rendered video.
- Gemini validation input is limited to the candidate image plus the scene contract (`visual_intent`, `must_show`, and relevant exclusions).
- Gemini mode is bounded to at most 3 candidate images per scene and validates them in one Gemini request per scene. This reduces request-rate usage while still allowing deterministic fallback among approved candidates; no unbounded retries.
- Existing deterministic metadata/scoring remains the retrieval/pre-filter layer in both modes.
- The mode must persist with the job from Studio/intake through M8 so behavior is explicit and reproducible.
- No new acceptance job until implementation, regression tests, deployment, and live verification are complete.

Implementation order:
1. Persist `visual_validation_mode = metadata | gemini` on the job and expose it in Studio/intake.
2. Extend M8 selection so Gemini mode can evaluate up to the top 3 eligible candidates per scene instead of committing the first metadata winner immediately.
3. Reuse the existing n8n Gemini credential; do not introduce another secret.
4. Parse Gemini response fail-closed and persist validation evidence with the selected asset.
5. Preserve the existing metadata-only route unchanged when `visual_validation_mode=metadata`.
6. Add deterministic tests for routing, call bound, PASS/FAIL/fallback, malformed Gemini response, and no-Gemini behavior.
7. Deploy only the components changed by this feature, verify live state, then run one controlled comparison job per mode.


Implementation checkpoint:
- Decision is committed in Git as `398738e`.
- Phase 1 source implementation is complete locally:
  - jobs persist `visual_validation_mode` with default `metadata`;
  - intake accepts explicit `metadata|gemini` while remaining backward-compatible when the field is omitted;
  - Studio exposes the selector and submits it;
  - latest-job API returns the saved mode.
- Focused tests: 7/7 PASS.
- Workflow JSON parse: PASS.
- `git diff --check`: PASS.
- Phase 1 is not deployed yet; next step is the M8 Gemini branch and bounded 3-candidate validation before any deployment.


Phase 2 implementation checkpoint:
- M8 now routes by the persisted job mode after visual search collection.
- `metadata` continues through the existing deterministic `factory.select_visuals` path.
- `gemini` obtains up to 3 deduplicated eligible candidates per shot, fetches bounded image previews through media-worker, and sends all candidates for one scene in a single Gemini request.
- Gemini image parts explicitly use `MEDIA_RESOLUTION_LOW` to reduce media-token usage.
- Gemini output is parsed fail-closed. A candidate passes only when required concepts are visible, forbidden concepts are clear, intent matches, and score is at least 70.
- Cross-scene provider-asset reuse is prevented; the collector falls back to another Gemini-approved candidate when available.
- Final Gemini validation evidence is persisted on `visual_selections`.
- Existing Gemini credential is reused; no new secret was introduced.
- Media-worker preview endpoint accepts 1-3 images, image MIME types only, max 3 MiB each / 8 MiB total.
- SQL migration/function syntax was verified inside a rollback-only transaction against the production PostgreSQL engine: PASS.
- media-worker `py_compile`: PASS.
- focused Node regressions including the existing Wikimedia depiction work: 63/63 PASS.
- `git diff --check`: PASS.
- Full regression suite is the next gate; nothing from Phase 2 is deployed yet.


Full regression checkpoint:
- Full Node suite: 316/316 PASS.
- media-worker `py_compile`: PASS.
- `git diff --check`: PASS.
- Source checkpoint before deployment: `d5bde05`.
- Next gate: isolated n8n workflow import/schema check, then production migration + targeted M3/M8/API/Studio/media-worker deployment and live verification. No acceptance job before those checks pass.


Isolated n8n validation checkpoint:
- The current M8 workflow imported successfully into a clean isolated n8n 2.37.10 SQLite instance.
- This validates the exported workflow shape/new node definitions without touching production.
- Production check immediately before deployment: no active `new/running/waiting` publisher executions; target workflow IDs remain `VideoM3Intake001`, `VideoM8Visuals001`, and `VideoSelfTestApi001`.
- Studio is bind-mounted read-only from this repository into the live Caddy container, so the committed Studio selector source is already the file served by Caddy; no Caddy restart is required.
- Next: production DB migrations, media-worker rebuild/recreate, then publish only M3/M8/Self-Test-API and verify exact live source/state before any job.

Production deployment checkpoint — selectable Gemini visual validation:
- Production DB migration applied successfully: jobs now persist `visual_validation_mode`; visual selections persist `validation_mode` and `validation_evidence`; Gemini candidate/commit functions are live.
- media-worker rebuilt and recreated only for the bounded `/visual-previews` endpoint. Live image: `sha256:d24abec8545dbdbfe3d75bec7d370b728e043d4373e6d39544569d10a77cc54a`; restart count 0; health `healthy`; live `/worker/server.py` SHA matches Git source.
- Live preview endpoint was exercised against a real Pexels preview and returned one bounded WebP preview successfully.
- Published only target n8n workflows:
  - M3 Intake v3;
  - M8 Multi-Source Visuals v65;
  - Self Test API v4.
- Published exports for all three match Git exactly for nodes/connections/settings.
- Non-target workflow fingerprint remained unchanged: `29|57e0fed4a6d13bed63ef6fb752071d64`.
- Publisher n8n was restarted once only after CLI publish because production webhooks were not registered until restart. After restart:
  - POST `/webhook/jobs` accepts `visual_validation_mode=gemini`;
  - invalid mode rejects with the exact validation error;
  - GET `/webhook/factory/latest` returns persisted `visual_validation_mode`.
- Studio live HTML is serving the new visual-quality selector.
- Active publisher executions after deployment: 0.
- Next: one controlled non-acceptance Gemini-mode test job to exercise the actual M8 Gemini credential/request/selection path. Poll in short verified steps; no long blind wait.


Controlled Gemini-mode smoke-test blocker — 2026-09-23:
- Job `21e30e0c-2ee2-491e-bd57-2eebb92e25e3` failed before M8, in M5 execution `9724`.
- Exact provider failure: Gemini HTTP 503 `This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.`
- `Generate Storyboard` already had n8n transient retry enabled (`retryOnFail=true`, `maxTries=3`, `waitBetweenTries=5000`), so the provider remained unavailable through all existing attempts.
- This is not a Gemini visual-validation/M8 failure. Do not change M8 for this blocker.
- Next gate: harden M5 transient-provider retry without adding a new paid service/model, run focused regression tests, deploy only M5 if clean, then rerun one controlled Gemini-mode smoke job.
