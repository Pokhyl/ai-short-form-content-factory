# Entity beats V5 follow-up checkpoint

Work only on `codex/entity-beats-v5-20260914`; source of truth is `CODEX_ENTITY_BEATS_V5_FOLLOWUP.md`.

The branch's exact dictionary/alias resolver, source character offsets, strict media identity and existing regression suite are retained. No checkout/cherry-pick of VPS-only `262f252` was attempted. The running VPS renderer was read only for bounded reconciliation of relevant behavior; its Kokoro and Whisper hashes match this branch.

New `VisualBeats.js` derives focal list spans from original text, retains all five names in UK/RU/PL/EN, excludes incidental relation endpoints/comparison objects, maps spans via the existing monotonic Whisper alignment, and validates coverage, duplicate identities and a five-second static hold. More than six members or insufficient hold time use an all-member group, never truncation. Exact-media pools retain identity proof and require >=1000px long edge and >=600px short edge for new visual beats; lower-quality images continue to exact P18/Commons alternatives. Direct exact images rank above taxonomy diagrams unless the claim is relational.

ShortCreator now preflights beat media before its unchanged single TTS call, retains the existing caption alignment word-to-caption map, plans within semantic scenes, and audits real per-beat spans/times/resolution/source dimensions/identity. Production's existing six-second maximum narration underrun (read from running ShortCreator, matching the task's 56.16s audio +3.84s padding) is reconciled instead of redeploying this branch's stale 1.5s value. The current production upper overrun bound of 0.35s is retained. No TTS model, voice, request count, audio speed, Whisper behavior or n8n configuration changed.

64/64 native tests pass at this checkpoint. Changes are not deployed. Remaining: further group/media/integration tests, live beat preflight, Docker build/tests, new normal job and exact MP4/frame/audit QA. Do not claim HUMAN PASS.
