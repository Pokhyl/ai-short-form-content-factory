# Replacement checkpoint — 2026-10-05

User input stays topic + language + duration. Relevant real photographs are accepted when video is unavailable; photographs may illustrate source-supported actions and remain visible throughout narration. No arbitrary six-second hold cap or fixed scene count.

Implemented offline: research -> actual material discovery/download/inspection -> composition from available material -> source-bound script review -> frozen exact files. PhotoWorker bridges a material-first photo plan into existing continuous voice, alignment and rendering. Executor accepts an explicit verifier, preserving durable stage claims and voice accounting. Existing legacy callers retain their verifier and density behavior.

Verification: 11 replacement tests and 79 existing tests pass. Controlled fixtures test contracts and exact file staging; they are not visual acceptance of a real MP4.

Remaining: implement bounded real provider operations and runtime selection of replacement producer/worker; render actual video intervals without legacy looping; validate the connected preparation-to-MP4 path, then scoped deployment. Current production remains the old runtime. Do not launch/rescue previously failed or unknown jobs. Do not call this checkpoint production ready.

Connected implementation update: runtime now constructs bounded Operations + DurableProducer and PhotoWorker. Actual existing research, Pixabay/Pexels/Commons search, byte downloads, Gemini photo inspection, composition and final source review are wired in this order. Preparation uses at most three searches per provider, twelve downloads/inspections and fifteen Gemini calls, independent of requested shot count. Unavailable downloads spend their slot and are skipped; ambiguous calls retain durable stop behavior. Dockerfile includes the replacement package. 12 replacement and 79 legacy offline tests pass, including a controlled connected adapter contract. Runtime image and real MP4 still require validation before production deployment. This version intentionally uses the accepted photo fallback path; native source-video interval rendering remains future work.
