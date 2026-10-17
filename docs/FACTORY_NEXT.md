# Replacement requested 2026-10-17

The owner explicitly requested a complete rebuild. Development now targets
`factory_next`; the previous dual-cadence candidate is tested but NOT deployed.
Live Studio and existing output/media/accounting remain intact.

The replacement owns source -> full photo corpus -> native story -> natural
voice -> measured alignment -> edit -> render -> actual file audit. Text length
is not a visual timing authority. All reviewed photographs remain available
until actual audio exists. The edit compiler searches legal photo densities
against measured phrase intervals. No speech speed change, crop, fabricated
source support, duplicate photo, paid fallback or terminal-job replay.

Implemented, not production accepted:
- separate checkpointed stage orchestrator with exclusive host lock, atomic
  fsynced writes, revision/output digests and no resend of ambiguous claims;
- source/photograph/story adapters using existing audited provider transports,
  source validation, pixel review and independent factual/native review;
- no legacy word-slot rewrite, simulated paragraph fitting or preselected pool;
- full bounded photo corpus rather than stopping at preferred photo count;
- actual-audio edit compiler and existing whole-photo renderer/independent audit;
- natural Google voice adapter with existing global quota reserve/commit before
  send; shared ASR alignment validates exact audio identity and coverage.

Remaining before ANY traffic switch:
1. Provider-budget wiring and stage recovery/reconciliation, including explicit
   temporary rejection versus ambiguous HTTP outcomes. Current checkpoint
   implementation is conservative and stops an interrupted stage.
2. Measured duration correction contract: exact requested duration still must
   hold; initial synthesis alone cannot guarantee it. Current compiler rejects
   out-of-window audio. Do not hide this with silence/stretch or claim reliable
   synthesis. Design and test bounded measured text correction with stored
   attempts, preserved source/native review, and quota accounting.
3. Complete connected saved-input run using real media/voice, then new bounded
   normal PL15/EN30/RU45/UK60 runs, no handcrafted scripts or injected approvals.
4. Studio progress/history/cancel/download integration and migration routing for
   new jobs only. Old IDs and owner-deleted media stay immutable.
5. Exact-image tests, protected deployment comparison, independent final output
   audit and explicit owner playback review. Test counts do not imply readiness.

Next step: connected adapter contract tests and real saved-media render before
provider integration; preserve explicit list of unproven boundaries above.
