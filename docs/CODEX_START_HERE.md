# Universal factory — active checkpoint, 2026-11-15

Read factory_universal/README.md and the root AGENTS.md.

project_ready=false. Unit checks, image-only preflights and historical eSpeak videos do not establish completed universal MP4 acceptance.

## Studio access is fixed

https://studio.hodor.com.pl/ is password-free in the checkout and deployed app. Real unauthenticated checks returned HTTP 200 for page/API, HTTP 206 for an MP4 range, and HTTP 400 for invalid form data without creating a job. Keep Studio password-free.

## Google connection restored

The owner reconnected the retained Google account. Read-only metadata execution 14691 returned READY after earlier OAUTH_GRANT_REJECTED executions 14689–14690. Do not ask the owner to reconnect again while current health checks pass. Selected-voice synthesis now succeeds: test db43f2c5-9c6f-480a-a97f-823b7da002f3 received unchanged Algenib recordings of 13008 and 14016 ms, then failed at the legacy shared renderer duration gate. Preserve that failed ID; do not replay it. The new project-owned FFmpeg renderer removes the unrelated legacy gate while preserving exact frames and unchanged voice input. Full new API acceptance remains required.

The public app checks the native connection before admitting jobs. Failed test f632a0cf-b09b-4bd7-a553-d7c9e695900a remains immutable; any new test must record the restored connection and diagnosed image fixes as its reason.

## Implemented and checked

- Four selected Google voices, unchanged natural audio, no audible eSpeak or paid model API.
- Primary-article identity binding, typed native definitions, connected source blocks and original spans.
- Correct abbreviation/exponent handling; no spoken navigation marks.
- Generic process discovery and source-scoped visual subjects.
- Source-backed human identity plus a separate human-content screen. Real document and billboard controls were rejected.
- Whole-photo aspect ratios, bounded searches, distinct images, complete captions and provenance.
- All image verification precedes synthesis. Tests verify missing images cause zero sends.
- Rejected meanings persist as data. The owner-rejected Ходор → Hadar-star interpretation (Q13175) stays rejected pending clarification.
- Public UI/API, provider admission gate, JavaScript syntax and focused runtime checks passed.
- Failed drafting/translation experiments and about 1.4 GiB of unused weights were removed. Only the pinned visual model remains.

## Acceptance still required

Normal API test f632a0cf-b09b-4bd7-a553-d7c9e695900a (Photosynthesis EN15) completed images and stopped at gateway HTTP 502. Preserve its failed ID and stopped attempt. Do not resend it or refund its conservative quota claim.

The replacement matrix covers Photosynthesis EN15, Warszawa PL30, Марс RU45, Бджоли UK60, paper manufacturing EN30 and Зеленский UK30. Full MP4/frame/audio/render review remains pending acceptance runs after reconnection. Image-only tests are separate operator records, not completed videos.

Temporary sanitized records are under /data/factory-universal/qa/. Publish meaningful changes and evidence under acceptance/factory-universal/, then verify checkout and deployment against the delivery branch.

## Image review correction

The first image-only matrix was not delivery acceptance: manual review rejected Photosynthesis charts/drawings, staged Mars stock scenes and one bee landscape without a visible bee. Paper manufacturing also failed image selection. The next bounded image-only matrix checks photographic metadata, astronomical provenance, insect framing and generic manufacturing subject extraction before any new synthesis. Preserve both histories.

## Continuity

Server checkout: /opt/factory-universal. App: factory-universal. Branch: codex/factory-universal-20261112. Checkpoint f18fe794f9fc8ab0aa8d48c4ea1bdf1c9b283303 is published; subsequent renderer and frame-review corrections remain pending publication.

Mac local execution was unavailable; SentinelX host_58bbeb7da5059807 is the working connection. Use one short Sentinel call at a time and finite background jobs. No subagents.

Do not restore Gemini or failed text-model experiments, alter unrelated files/services/workflows, expose secrets, rewrite failed jobs or remove storage/quota bounds.
