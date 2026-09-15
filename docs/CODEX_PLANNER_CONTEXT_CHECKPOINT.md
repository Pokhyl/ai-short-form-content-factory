# Planner context continuity — 2026-09-15

Branch `codex/entity-beats-v5-20260914`, PR #10. This follows the personal-anaphora checkpoint.

The active VPS WF10 `Build Extractive Narration` Code node was read through an n8n workflow export and compared with the server JSON: identical. Its code is now tracked in `n8n/code/WF10-build-extractive.js`; workflow topology, credentials and other nodes are not imported into GitHub. Current UK60 calibration remains `1.78` / `-0.35`, and heading stripping is retained.

Previously both contiguous-window selection and the noncontiguous fallback could begin with an orphan pronoun. Filtering short/long source sentences also erased evidence of missing intervening context. Selection now excludes context-dependent openings and requires the immediately preceding original source sentence for subsequent dependent sentences. Original source sentence indexes survive filtering. This does not grant identity to a pronoun: exact renderer preflight still validates the immediate antecedent and media, before TTS.

Regression coverage: UK/RU/PL/EN orphan openings, contiguous context, skipped/filtered predecessors, possessives/demonstratives, internal pronouns, a full timing-valid orphan rejected by the new planner (accepted by the old planner), and selection of a valid alternative. Timing windows/calibration are unchanged. No topic-specific names are used in selection rules.

Only the existing Code node is to be patched from this tracked source after full native/container PASS. Preserve all other live workflow fields, back up first, and check the baseline code before mutation. Deploy the already-tested personal-subject renderer too. Submit only a NEW normal job; old failed/rejected rows remain immutable. No HUMAN PASS may be claimed.
