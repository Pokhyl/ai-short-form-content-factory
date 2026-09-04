# Engineering History — V5 Agentic Editor

## 2026-09-04 — complete V4 product architecture rejected

After repeated cross-topic failures, the user explicitly required a complete project redesign rather than further V4 patches.

The V4 failure pattern was systemic: static/slideshow rendering survived shot-count changes, speech and visual correction responsibilities were coupled, and visual planners could invent media that free providers did not contain.

Decision: freeze V4 as evidence and start a clean V5 branch. Details: `V5_REBUILD_DECISION_20260904.md`.

## 2026-09-04 — clean V5 branch and runtime created

Created branch `rebuild/agentic-editor-v5`. Stopped `ai-short-form-v4-selftest.service`. No new `/api/v4` product work is allowed.

Pinned current OpenNolan upstream at commit `4457349c386ea1a89c01547f9a76fa650970c131` (`v1.0.2`, AGPL-3.0) in `/opt/ai-short-form-v5-upstreams/OpenNolan`.

Created isolated runtime `/opt/ai-short-form-v5-runtime/.venv`, installed OpenNolan core requirements, `faster-whisper 1.2.1`, `edge-tts 7.2.8`, and host FFmpeg `6.1.1`.

V5 source has a preflight guard rejecting dependencies on V4 product modules.

## 2026-09-04 — asset-first order selected

V5 reverses the old order. The final factual story/script is not frozen before visual feasibility is known.

New critical path:

`topic -> research -> actual licensed visual inventory -> showable story angle -> script -> continuous voice -> exact-audio word timing -> concrete NLE edit plan -> mature editor operations -> QA -> human review`

The editor core is upstream-native OpenNolan/FFmpeg rather than another custom V5 renderer.

## 2026-09-04 — upstream-native preflight and inventory probes

Fresh preflight confirmed exact upstream SHA plus OpenNolan `DirectClipSearch`, `VideoCompose` and `Transcriber` as available.

Active inventory probes across mechanism, history and comparison topics returned candidates through Pexels, Pixabay Video, Wikimedia and Archive.org.

A meaningful upstream provider-health defect was found: Coverr `is_available()` reported available while real searches returned HTTP `401`. V5 therefore treats an active search result as provider-health evidence and leaves Coverr out of the initial default inventory set.

The same probes also showed that provider results may be adjacent/irrelevant. Availability is not visual relevance proof; candidate media still requires actual-frame inspection before final selection.

## 2026-09-04 — obsolete V4 runtime bulk removed

After failure evidence was committed, the frozen V4 Remotion Docker image, old OpenMontage checkout and obsolete V4 Python tools environment were removed to reclaim disk for the new runtime. The V4 self-test service remains stopped.
