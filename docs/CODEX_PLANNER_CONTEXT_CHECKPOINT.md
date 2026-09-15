# Planner context continuity — 2026-09-15

Branch `codex/entity-beats-v5-20260914`, PR #10. This follows the personal-anaphora checkpoint.

The active VPS WF10 `Build Extractive Narration` Code node was read through an n8n workflow export and compared with the server JSON: identical. Its code is now tracked in `n8n/code/WF10-build-extractive.js`; workflow topology, credentials and other nodes are not imported into GitHub. Current UK60 calibration remains `1.78` / `-0.35`, and heading stripping is retained.

Previously both contiguous-window selection and the noncontiguous fallback could begin with an orphan pronoun. Filtering short/long source sentences also erased evidence of missing intervening context. Selection now excludes context-dependent openings and requires the immediately preceding original source sentence for subsequent dependent sentences. Original source sentence indexes survive filtering. This does not grant identity to a pronoun: exact renderer preflight still validates the immediate antecedent and media, before TTS.

Regression coverage: UK/RU/PL/EN orphan openings, contiguous context, skipped/filtered predecessors, possessives/demonstratives, internal pronouns, a full timing-valid orphan rejected by the new planner (accepted by the old planner), and selection of a valid alternative. Timing windows/calibration are unchanged. No topic-specific names are used in selection rules.

Only the existing Code node is to be patched from this tracked source after full native/container PASS. Preserve all other live workflow fields, back up first, and check the baseline code before mutation. Deploy the already-tested personal-subject renderer too. Submit only a NEW normal job; old failed/rejected rows remain immutable. No HUMAN PASS may be claimed.

## Normal-job validation and subsequent resolver fixes

Release `context-2f845f5` passed 104/104 native, Docker and VPS tests and was deployed. The active WF10 node, all other workflow nodes/connections/settings/active states, service HTTP200, and unchanged TTS/Whisper hashes were verified. The new normal Solar System job `7e927bf8-308d-4e77-ac11-44cc658718cf` / video `cmu261jo9000001qg9iqse7f3` failed before TTS on a degree-modified subject. It is immutable; do not retry it.

Read-only replay of its actual seven scene inputs exposed and motivated four general fixes:

- Determiners plus comparative/superlative size adjectives can precede an exact subject; arbitrary verb/preposition prefixes still fail.
- An explicit classification predicate focuses the exact class instead of incidental substances.
- Coordinated subjects with a following claim preserve all members, including comma separators. Bare lists without a claim and unknown trailing members still fail; existing rejection tests remain unchanged.
- Initial scene/group media selection now consults the existing exact high-quality beat pool when its thumbnail/P18/search path has no usable image. It retains identity exclusions and same-entity-only reuse, and does not introduce generic source fallback.

All additions have regression tests; the full native suite is 110/110 PASS. No TTS, Whisper, density, timing, audio-speed or job immutability rules were changed. The latest renderer changes require the final container/live checks and deployment; see PR #10 for the current run result.
