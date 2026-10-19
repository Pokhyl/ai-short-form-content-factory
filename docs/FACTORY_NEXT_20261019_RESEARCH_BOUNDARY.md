# Factory Next research boundary — 2026-10-19

## Contract

The factory must accept an arbitrary owner-entered topic, produce independently
source-reviewed facts, retrieve inspected topic-relevant photos, generate
natural speech, then render and independently audit the resulting portrait MP4.
Do not accept unsupported claims, invent visual evidence, replay terminal
job IDs, bypass the provider ledger, or modify other projects.

## Captured incident

- Immutable Studio job: `5a7eed21-d239-469a-a61f-8988c0f5d40d`.
- Owner-entered topic: «стив джобс», UK, 60 seconds.
- Running revision at the time: `fe08bfba800ffd92c4922ca7876704cf7ee9730b`.
- Stage: `research`; terminal status: `needs_attention`;
  persisted safe code: `RESEARCH_FACTS_REJECTED`.
- Source search and all three source fetches completed. The source corpus had
  190,005 characters and 177 exact source spans.
- Four completed Gemini operations were saved: provisional brief, photo/brief
  repairs 1 and 2, and independent fact review 3.
- Both repair slots were consumed correcting a nonliteral **photo source
  mention**. During those repairs the model also rewrote facts and added a
  photograph-to-fact association. When photo citations were acceptable, the
  independent reviewer rejected unsupported factual scope.
- No story, voice synthesis, or MP4 was created. Do not resume this job.

## Generic bounded correction

1. A local validation failure only about photo contexts cannot authorize an
   alteration of `facts` or `required_fact_ids`.
2. Preserve the original, narrower photo-to-fact identity bindings. Ignore
   additions introduced by a photo-only model correction, but reject deletion,
   substitution, duplicates, or unknown identities. The ordinary source and
   image validators still apply afterward.
3. Only in Factory Next's fact-only review mode, if an earlier correction slot
   was consumed by a photo-only issue and the independent review at attempt 3
   rejects facts, allow **one more separately claimed and metered factual
   correction** and **one independent follow-up review**. No additional
   correction for other failures; no unsafe repeat of uncertain operations.
4. The repair uses the existing `material-brief-repair:review:3` durable key
   and normal PostgreSQL Gemini budget. No provider limits were increased.

## Evidence

- Controlled regressions use wildflowers/bees and reef/coral examples; neither
  fix contains a Steve Jobs or DNA special case.
- The final candidate's exact Docker image ran 243 material-first tests and 127
  factory-v3 tests without failures. Factory Next's 152 tests were exercised;
  a package-layout test required mounting the package source tree separately
  into the isolated test container and passed when properly mounted.
- Read-only, **no-provider-send** replay of the exact saved failed job with
  the new image consumed its existing records and progressed to the distinct
  unsent key `material-brief-repair:review:3`, rather than stopping at
  `RESEARCH_FACTS_REJECTED`. This does NOT prove the next Gemini correction
  will be accepted.
- Deployed code revision: `e1e7d60fb3c8c32495c4c027fb93a700ef12abe9`.
- Deployed image: `factory-v3:factory-next-bounded-research-e1e7d60`.
- Container: `factory-next-studio-v9`. Previous container retained as
  `factory-next-studio-v9-before-photo-fact-20261019`.
- Studio HTTP 200, jobs API HTTP 200, existing audited DNA MP4 HTTP 206.
- A new UK60 job on the owner-specified Steve Jobs topic was admitted with
  ID `8d4d2acd-d30f-449f-a655-edaa4a58a460` on this revision. Its result
  must be inspected before any end-to-end acceptance claim.

## Cost guard

The gateway's live billing metadata returned HTTP 200 and
`billingEnabled=false` for the configured Gemini project. The TTS ledger
limits are 900,000 Chirp3-HD characters and 3,600,000 WaveNet characters
per month, below the respective published free allowances. Those are
internal guardrails; they do not independently establish total usage
outside the factory.

Never create a second attempt for a terminal job. If the new job fails,
diagnose its immutable receipts and make a general fix first.
