# Entity beats V5 follow-up checkpoint

Work only on `codex/entity-beats-v5-20260914`; source of truth is `CODEX_ENTITY_BEATS_V5_FOLLOWUP.md`.

The branch's exact dictionary/alias resolver, source character offsets, strict media identity and existing regression suite are retained. No checkout/cherry-pick of VPS-only `262f252` was attempted. The running VPS renderer was read only for bounded reconciliation of relevant behavior; its Kokoro and Whisper hashes match this branch.

New `VisualBeats.js` derives focal list spans from original text, retains all five names in UK/RU/PL/EN, excludes incidental relation endpoints/comparison objects, maps spans via the existing monotonic Whisper alignment, and validates coverage, duplicate identities and a five-second static hold. More than six members or insufficient hold time use an all-member group, never truncation. Exact-media pools retain identity proof and require >=1000px long edge and >=600px short edge for new visual beats; lower-quality images continue to exact P18/Commons alternatives. Direct exact images rank above taxonomy diagrams unless the claim is relational.

ShortCreator now preflights beat media before its unchanged single TTS call, retains the existing caption alignment word-to-caption map, plans within semantic scenes, and audits real per-beat spans/times/resolution/source dimensions/identity. Production's existing six-second maximum narration underrun (read from running ShortCreator, matching the task's 56.16s audio +3.84s padding) is reconciled instead of redeploying this branch's stale 1.5s value. The current production upper overrun bound of 0.35s is retained. No TTS model, voice, request count, audio speed, Whisper behavior or n8n configuration changed.

64/64 native tests pass at this checkpoint. Changes are not deployed. Remaining: further group/media/integration tests, live beat preflight, Docker build/tests, new normal job and exact MP4/frame/audit QA. Do not claim HUMAN PASS.

70/70 native tests now pass. Added full seven-member group and short-five-name group tests, a non-astronomy named list, exact low-resolution page -> high-resolution P18 test, same-claim density alternatives, and renderer audit assertions (source spans, dimensions, start/end/hold, one synthesis). Local Docker build/test and read-only live beat preflight are in progress. No new job or deployment yet.

Local Linux Docker build succeeded and all 70 tests passed offline. Live exact-media preflight passed for the documented V5 narrations; five list items including Eris are retained, Pallas is 1080×1087, Sedna/Haumea 1080×1080. See `ENTITY_BEATS_V5_LIVE_MAPPING.md` for every real source span and media. Some claims have no second proven exact asset, so their >5s timed holds will correctly FAIL rather than manufacturing unrelated beats or weakening the density gate. One fresh normal validation job is next; avoid repeated submissions of the same video.

71/71 native and Linux offline tests pass after fixing first-list-item timing: a nonzero source-span position maps to its actual caption start, with a distinct exact claim visual covering the lead-in. Missing alignment/context fails; no equal slicing or early first-name portrait. Renderer build passes. These source changes are ready for one fresh normal-job validation; no HUMAN PASS.
