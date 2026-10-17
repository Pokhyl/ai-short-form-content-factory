# Studio browser and research validation — 2026-10-17

Observed owner-submitted Studio job `77963714-f8ec-4d76-aad7-f6087b4af0a2`, Ukrainian, 45 seconds, for the exact submitted topic `галактик а андромеда`. The original immutable state is `needs_attention` at research with `ValueError`; no MP3 or MP4 for this job.

Two concrete mechanisms:

1. Studio inline JavaScript declared global `async function history()`, shadowing browser `window.history`. After successfully creating an API job, the client called `window.history.replaceState` and raised `TypeError`, falsely displaying an error for a job already created. Rename to `loadJobHistory` without changing API semantics. An offline Node VM test simulates a browser-global window, one form POST, the read-after-write API and a failed job card; verifies exactly one POST, no TypeError, no video in an unaudited job.
2. Persisted PostgreSQL preparation ledger shows `research-search`, three source fetches, `material-brief` and `material-brief-repair:initial` all `succeeded`. The Gemini repair preserved facts, required facts, and fact IDs but changed legitimate literal source mentions and supporting source span IDs. The previous guard rejected *any* span/mention change. New guard protects immutable factual claims and fact IDs while revalidating every updated mention literally against the fetched source spans; the independent review remains required. Malicious nonexistent source mentions and changed facts/fact IDs are rejected by offline tests.

A read-only replay of both real saved Gemini responses (without provider, search or quota requests) reached independent `material-brief-review:1` after the guard correction. This is **not** proof that later independent semantic review will accept the submitted topic. Never resume the old failed ID; new requests must use fresh UUIDs.

Verified before deployment: 81 factory_next and 127 factory_v3 offline tests in the pinned base Docker image with the modified files mounted, plus separate live-source replay and Node VM browser event simulation. The next image must be rebuilt at the exact new commit, retested as-baked, then deployed and tested over actual HTTP. Production and other projects must remain untouched.
