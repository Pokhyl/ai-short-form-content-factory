# Fast enumeration continuation — 2026-09-15

Branch `codex/entity-beats-v5-20260914`, PR #10.

## Reconciled VPS baseline

The user-designated worktree `/opt/ai-short-form-content-factory-pr10` was at `ac1af93` with seven modified tracked files (not a clean Git status). Those exact changes were copied, without replacement by older GitHub code, into this branch. Resolver hashes matched both `/opt/ai-short-form-content-factory/releases/final-ac1af93` and the running renderer. Runtime image: `sha256:1399f65dadf3e041edd554ebcc6fe5bd7730aee249b0628b2924af1d141a4fec`. Reconciled full native suite: 127/127 PASS. The release's old `tests.log` still showed 104 tests, so it was not used as evidence of the current suite.

Preserve the imported grammar, planner calibration/normalization, exact P910/P301 category identity and associated regression tests. No TTS or workflow changes are needed for the next fix.

## Actual blocker

Immutable failed job `be51fab6-fd30-44de-a250-6cb9d3f6f7b9`, video `cmu2pekb5000001s8bzetbylx`, completed exact grounding, one Gemini synthesis (Enceladus, 54.32s), and Whisper (94 captions). Four semantic scenes aligned to the actual audio. `planVisualBeats` then failed `visual_density` on all eight planet identities.

Cause: lists over six entries are forced into one montage, and short caption-timed entries can also be replaced by a montage. The long montage then violates the five-second static hold gate. Replace this planning behavior with sequential exact identities anchored to actual source/caption spans. No collage, entity deletion, generic fallback, random/equal timing, audio retiming, or weakened gates. Preserve all eight identities in spoken order. Existing failed jobs remain untouched.

Next: reproduce with the actual caption/span timeline; regression tests; full suite; deploy renderer; dry plan on VPS; one NEW normal `Сонячна система / uk / 60` job; exact MP4 QA. Only the user may declare HUMAN PASS.

## Sequential planner implementation

Forced montage paths are removed from `planVisualBeats`, including the `>6` shortcut. Every named member uses its real source span and caption onset. A missing alignment is recovered only when exactly the same number of unassigned source words and captions lie between two established anchors; ambiguous gaps and shared-caption member timing fail closed.

The actual Mars caption lasts 230ms. To retain the existing 350ms readability minimum, Jupiter starts 120ms after its caption onset, still inside its own spoken interval. No speech or caption timestamps are altered. `timingEvidence` records caption indices, actual spoken bounds, alignment provenance, and start adjustment in the video audit.

Long holds use real caption boundaries where feasible and the hard 5000ms limit otherwise, not equal slices. Distinct exact alternatives preserve entity identity. Counted enumeration retains explicit class/possessor evidence for a grounded lead-in; no generated collage is rendered. A group is not inferred from the source topic when that evidence is absent.

Regression input `tests/fixtures/fast-enumeration-timing.json` contains the actual narration/alignment and 94 captions re-extracted from a scratch copy of the immutable failed-job audio. The original job and its files were not changed. Current validation and deployment results are recorded in PR #10.
