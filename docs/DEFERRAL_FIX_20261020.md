# Retry sequence repair

Live SQL defer_preparation_call now permits the same six bounded attempts as deployed Gemini code f98a351. Real PostgreSQL regression reproduced the old failure and passed 17 controls after correction. Core suite 127/127 passed. Factory Next full suite had 163/165 passing; both stale photo-only mock failures reproduced on the base release and their corrected fixture subsequently passed 5/5.

Normal Studio job 29342f75-919b-4c78-bb78-92a70bff5ea7 reached all six attempts without SQL error, but every Gemini response was HTTP503/UNAVAILABLE. Final status needs_attention at research. No TTS or MP4. Do not replay terminal jobs or claim project ready. Existing budgets and unrelated services unchanged.

Function migration is live; include corrected SQL in future releases. Evidence is under acceptance/factory-v3/deferral-*. VPS git lacked credentials; this branch is saved through the connected GitHub API.
