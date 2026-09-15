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

## LIMIT HANDOFF — latest state (read this first)

The user asked to save everything before the usage limit. No new normal job has been submitted for the fast-enumeration fix, and **no renderer deployment has been performed for it**. Production still runs `final-ac1af93`, image `sha256:1399f65dadf3e041edd554ebcc6fe5bd7730aee249b0628b2924af1d141a4fec`.

Completed:
- Reconciled other-agent changes: commit `10e1c79`.
- Sequential timing implementation and actual eight-name regression: commit `be3aa53`.
- 132/132 native and Docker PASS at `be3aa53`; a server image/test release was built at `/opt/ai-short-form-content-factory/releases/fast-be3aa53` but NOT deployed.
- `/opt/ai-short-form-content-factory-pr10` was verified clean at `be3aa53`; the original seven uncommitted files are additionally preserved in a named Git stash.

The full four-scene live dry plan exposed an internal merged-word case in the second scene: source `малі тіла Сонячної системи`, caption `малітіла`, then `сонячної`, `системи`. The first and last words have exact caption anchors, but one interior source word has no separate caption. Latest code permits this **within one exact multiword entity only**, using the real outer caption bounds and recording `caption_span_envelope`; it still rejects unanchored boundaries and different entities sharing a caption. A regression test was added. See the final save commit / PR for its native test result.

Reproduction assets are committed:
- `tests/fixtures/fast-enumeration-timing.json`: actual eight-name scene, alignment and captions.
- `tests/fixtures/fast-enumeration-replay.json`: all four real scenes, full alignment and 94 captions.
- `scripts/dry-fast-enumeration.cjs`: runs exact preflight and all four `planVisualBeats` calls read-only, without TTS/render. Run with the configured `VISUAL_PYTHON`; stdout is the complete compact media/timing plan.

Remaining work, in order:
1. Run the final full native and rebuilt-container suite (the newest merged-word envelope change needs final container verification).
2. Run `node scripts/dry-fast-enumeration.cjs` and inspect all four scene plans. The prior whole-plan failure was the internal merged caption described above; do not assume the final whole plan has passed yet.
3. Update the clean VPS Git worktree from this same branch without replacing live planner changes; build a NEW release from the final commit.
4. Preserve a fresh private snapshot of all failed/rejected job rows, verify no active jobs, verify TTS/Whisper hashes, and switch ONLY the renderer using existing compose plus image override. Do not run stale deployment scripts for earlier releases.
5. Run the dry plan against the deployed code. Only after PASS, submit exactly one NEW normal `Сонячна система / uk / 60` job via `https://publisher.hodor.com.pl/webhook/jobs` with JSON `{"topic":"Сонячна система","language":"uk","duration":60}`.
6. Inspect exact MP4, frame/contact sheet, ffprobe 1080x1920 H264 AAC, HTTP 200, timing audit and preserved eight-identity spoken order. Compare old failed/rejected rows in full against the snapshot. No HUMAN PASS.
7. Commit/push all results and update PR #10. Do not restart an architecture audit or rerun the immutable failed job.

TTS hash (`Kokoro.js`): `55a0a5685af175645826ddacaf51c760ee68599795da7044d8de445378291d42`.
Whisper hash: `72127af318b8ab5b51bd4340ff4a3d71c8fcc492325c0f8566b4bbb74f993fec`.
Latest planning changes do not change synthesis, voice, audio speed, Whisper extraction or workflow topology.

Final save verification: **133/133 native PASS**, zero skips, including merged-caption envelope regression. Server suite at the preceding `be3aa53` release: **132/132 PASS**. Production image was checked again and remains `final-ac1af93`; no deployment or new normal job was performed during this save.
