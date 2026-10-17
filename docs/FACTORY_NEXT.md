# Replacement requested 2026-10-17


## Bounded provider 503 recovery checkpoint — 2026-10-17

The exact source Docker image for commit 63de52e was built separately as
factory-v3:factory-next-63de52e, image sha256
74ecb192e467b0dfb38f62052c404f3dd2719c9e9c779d963cee93c7a206ed3f.
All 36 tests ran **inside** that baked image with networking disabled and
passed. The deployed factory-v3-app was never switched.

A fresh real PL15 job c8944de0-482a-4f9d-8479-990715be0e10 was then
submitted through the verified free-tier gateway and existing preparation
budget. During research, Gemini explicitly rejected an invocation with
503/UNAVAILABLE. The existing PostgreSQL ledger correctly persisted a
bounded deferred attempt, but factory_next Pipeline v1 incorrectly treated
PreparationDeferred as an ambiguous terminal needs_attention failure.
No research output, voice or MP4 was produced, and no provider request was
replayed. The real job remains immutable and blocked at research.
Evidence: acceptance/factory-next/pl15-provider-503-20261017.json.

The revised checkpoint system now distinguishes a **verified** model
rejection from unknown transport failures. Only research, materials and
story can persist provider_wait with the database-assigned due timestamp.
A subsequent explicit Pipeline.step() returns unchanged until due.
At due, the trusted ProviderResumeGate verifies the exact job/revision,
a matching waiting PostgreSQL deferral and zero started/unknown provider
calls, then claims the bounded preparation run before continuing. Crashes
during reconciliation stop as checking_provider (manual reconciliation).
Real Google TTS and every other non-ledger stage remain non-replayable.

The full source-level factory_next suite passed **44/44** (8 new tests).
This is not yet an exact-image test of the new recovery revision, nor is
the database due/resume path verified with a real post-fix 503.
The previous research/voice failures are NOT unlocked and must NOT be
resent. No Studio traffic switch or production deployment occurred.



## Actual provider PL15 checkpoint and voice review collision — 2026-10-17

An isolated, budgeted normal PL15 diagnostic request
04a59c6f-4f9a-4ad2-a6e5-076e5b882f53 ran with exact source revision
27f8e5e54deff10a2d93e9d64e3b60fcef78984d. The existing verified
free-only Gemini gateway and existing provider/quota ledger were used.
No normal Studio intake was switched, and unrelated projects were untouched.

Connected provider evidence, not controlled fixtures:
- Research completed: 3 source-grounded facts, 3 essential facts,
  3 photo queries and 3 source records.
- Materials completed: 23 reviewed, distinct byte-identified photos
  sourced across Wikimedia, Pexels and Pixabay.
- Story completed: 3 source-bound scenes / 66 Polish words; independent
  native-language review passed.
- Google TTS attempt 1 was actually synthesized, measured and archived:
  33,864 ms (requested 15,000 ms), SHA-256
  b4ba32ef6fbf4a8e06b9faf4853eefc42b569d7d2cf8d0a2ba57117eb365735b.
  This requires a shorter source-grounded reviewed narration.
- The voice correction draft generated, but its independent script review
  reused the original script-review ledger key with different model input.
  Existing factory_v3.claim_preparation_call correctly rejected the
  conflicting identity; the Pipeline checkpoint became needs_attention.
  No second TTS synthesis, no final MP3, no MP4 and NO replay of this ID.

Generic implementation fix (not deployed/real-provider accepted):
factory_next.preparation.VoiceRevisionCalls namespaces both Gemini
revision and independent factual/native review claims under
next-voice-correction:2, including explicitly deferred retry identities.
It keeps the *same* BudgetedCalls and the same free-tier enforcement;
the original story review receipt is never changed. The live failure
class is reproduced by tests/factory_next/test_voice_revision_claims.py.
All 36 local factory_next tests pass, including offline HTTP and
real-byte MP4 audit. Record:
acceptance/factory-next/pl15-first-real-20261017.json.

The failed job remains immutable. Do NOT resend its voice or assume its
correction is accepted. Before the next normal paid/free provider smoke:
review this generic fix, check full suites, build the exact protected
image when server disk permits, and separately authorize/verify a new
immutable request. Studio production is still the old image.


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

## Runtime image packaging checkpoint — 2026-10-17

The factory_v3/Dockerfile previously omitted factory_next entirely.
It now copies the factory_next package alongside factory_v3 and
material_first. A source-level regression test checks this inclusion.
No exact Docker image has been built or tested from this revision:
the server root disk had only about 1.2 GiB available at inspection,
so an image build was deliberately withheld rather than risk unrelated
production containers. Runtime image build, package imports inside the
image, isolated exact-image test suite and protected deployment remain
outstanding. This is a packaging source correction, not deployment proof.

## Measured natural-voice correction — offline checkpoint 2026-10-17

The new voice adapter now measures MP3 bytes with the existing local
media-worker voiceover-probe endpoint before storing the accepted voice.
The strict speech window is [requested duration - 1000 ms, requested duration].
If attempt 1 misses, it invokes **one** source/photo-grounded Gemini rewrite
with the same mandatory facts and paragraph count. The revised
script receives the full native-language and independent factual review
before attempt 2 may be synthesized. A word estimate is a prompt hint only,
never a substitute for measuring the second MP3.

Every actual TTS synthesis has its own factory.reserve_provider_usage and
factory.commit_provider_usage key and an exclusive fsynced local attempt
archive. The provider-produced bytes must match the hash returned by the
media-worker probe. At most two synthesis calls are possible. A miss on
attempt 2 stops without promoting a voice candidate or launching a third
call. The accepted candidate alone is saved and then promoted through the
media-worker voiceover-candidates endpoints; it is not an in-place
replacement of an existing final file. Speech speed is unchanged.
The final alignment and edit compiler both use the newly reviewed scenes
attached to the selected voice receipt. All uncertain transport/provider
results remain held by the Pipeline non-replayable running checkpoint:
there is NO blind automatic re-send.

Tests include scripted provider/quota/worker failures, missing revision
review, immutable attempt identity, and a real-byte pair of FFmpeg-encoded
9 s / 14.6 s MP3 inputs. The latter exercises actual ffprobe measurement,
accepted voice hashing and source archive retention through an isolated
worker protocol double. This does **not** establish real Google TTS,
actual Gemini revision quality, running media-worker compatibility,
real provider budget/recovery, exact container-image acceptance, normal
PL15/EN30/RU45/UK60 results or Studio integration. The old production
deployment, previously failed jobs and user media are untouched.

## Composed stage adapter checkpoint — 2026-10-17

factory_next/adapters.py now composes the existing preparation (research,
materials, story), voice (synthesis and alignment), and media (render and
independent audit) adapters behind the complete eight-stage Pipeline
interface. A separate optional preflight gate can stop the entire stage
**before** dispatch. tests/factory_next/test_adapters.py covers ordered
checkpoint receipt execution and pre-dispatch gate behavior with controlled
adapters. The live Studio intake is NOT routed to this composed adapter yet.
No claim is made that actual provider budgets, restart recovery of ambiguous
requests, or natural-duration correction are fully integrated.

## Durable pre-dispatch recovery checkpoint — 2026-10-17

The replacement pipeline now has persisted **pre-dispatch only** provider
deferrals via the optional adapters.preflight(stage, context) contract and
PreDispatchUnavailable(provider, retry_after_seconds). The runner claims a
checking checkpoint before calling preflight. Only a typed, explicitly
bounded unavailability response returned there can become deferred. Due
rechecks require another explicit step() call; no sleep or background retry
loop is introduced. Each stage is capped at three preflight deferrals, with
attempt counts, provider identity and next-retry epoch retained in the
fsynced state. Unknown/checking/running and all after-dispatch failures
(including a PreDispatchUnavailable raised by an actual stage method) remain
blocked for operator reconciliation and are **never re-sent** automatically.
Previous completed-stage output fingerprints are checked before every revisit.

tests/factory_next/test_recovery.py covers pre-dispatch due/resume, limit,
unexpected preflight failure, interrupted claim, after-send failure, corrupted
prior checkpoint, and invalid retry metadata. The full local factory_next suite
passed 14/14 (including the real FFmpeg file-level integration test). This
does **not** mean provider recovery is live: no production adapter currently
supplies the non-dispatching preflight contract, and no durable per-provider
call ledger or Studio due-work scheduler is connected. No network provider,
TTS or normal production job was invoked. Production remains unchanged.

## Offline file-level integration checkpoint — 2026-10-17

`tests/factory_next/test_media.py` exercises the replacement measured edit,
`MediaStages.render`, the existing FFmpeg whole-photo renderer and the
independent byte-level `MediaStages.audit`, using freshly generated distinct
fixture images and a 14.5-second encoded test tone. The resulting actual
15-second MP4 passes file-format, frame count, SHA-256, decoded output,
source/fitted audio correlation, and visual-frame-timeline checks. This is a
technical transport/render/audit integration check, **not** reviewed spoken
narration, genuine provider-sourced photo acceptance, a saved-production-media
replay, or a natural voice quality test. The deployed service was not changed.

The active `shorts-v2_media_data` volume had zero MP3 and zero MP4 files at
this inspection, so an independent old-audio replay cannot be claimed from
that volume. Remaining work before traffic switch is the provider-budget and
safe stage-reconciliation implementation, measured-duration correction with
stored attempts, actual saved-provider media/voice connected acceptance when
available, normal language/duration matrix, Studio routing, and owner review.


## Provider runtime wiring and live read-only admission — 2026-10-17

factory_next/wiring.py now constructs the reviewed research/photo/story
PreparationStages, natural GoogleVoice + quota-accounted VoiceStages and
whole-photo MediaStages using the **existing** Runtime.producer, broker gateway,
BudgetedCalls, PostgresLedger and confirmed free-tier project. Adapter
assembly alone does not register a job, reserve quota or send a provider
request. It refuses an invalid job identity or unverified producer admission.
tests/factory_next/test_wiring.py covers construction without dispatch,
invalid identity, free-tier refusal and an optional local preflight gate.

Real gateway read-only metadata checks against the running, unchanged
factory-v3 app returned HTTP 200 for the free project's billing status
(confirmed unbilled) and gemini-3.1-flash-lite model identity. A real
settings/dependency import in a network-disabled, read-only isolated
Docker container successfully assembled the connected adapters; actual
types were CredentialHTTP, Operations and PostgresLedger. A read-only
Postgres check confirmed the reserve_provider_usage and
commit_provider_usage(text,text) signatures and enabled Google TTS
budget limits. These checks do **not** imply any real source/Gemini/TTS
creation, public job migration, provider budget exhaustion safety under
real load, or a deployed factory_next build.

An actual-provider one-stage research execution must first provision a
fresh immutable request identity and preparation budget through the
existing bounded Runtime; no arbitrary direct gateway sends or unmetered
Gemini calls are permitted. A completed or unknown call is never replayed.

## Isolated real media-worker HTTP integration — 2026-10-17

The full factory_next source test suite completed **29/29 PASS** (including\nthe three isolated actual-worker HTTP integration tests).\n\ntests/factory_next/test_worker_http.py starts the **real** Python HTTP
handler from services/media-worker/server.py on a loopback-only ephemeral
port, with **every** media storage root redirected to a fresh disposable
directory. It drives VoiceStages via the real JSONHTTP and WorkerAdapters
transport, without touching the running media-worker, any Docker volume,
production credentials or Google/Gemini provider endpoints.

Verified with real FFmpeg-encoded MP3 bytes:
- First fitting voice: probe -> exclusive candidate create -> promote to final;
  SHA-256 and measured duration match, 409 on duplicate cannot overwrite.
- First too short, second fitting: two quota reservations/commits, independent
  retained attempt audio files and exclusive promotion of only the winner.
- Full eight-stage checkpointed Pipeline: controlled source and photo facts,
  real local HTTP voice save, **controlled** alignment timings (no ASR),
  measured edit, real 1080x1920 H.264/AAC whole-photo MP4 rendering and
  independent file-level audit. Exact 15-second duration and all audit gates
  passed; the only TTS provider call was a local recorded-audio fixture.

Scope is **offline technical integration**, not finished product acceptance.
All photographs and sound in this test are synthetic, upstream research/review
and ASR are fixtures, and the live worker service was never modified.
Still required: full real-provider story and photo evidence review, actual
Google TTS and ASR, measured-duration correction on real spoken audio,
normal PL15/EN30/RU45/UK60 cases, Studio routing, exact Docker image build,
and protected real output acceptance. No production deployment occurred.
