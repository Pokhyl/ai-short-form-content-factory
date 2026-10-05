# Factory v3 — availability before voice

Replacement authorized2026-10-04. Product readiness remains false.

Order: research -> review real downloaded media -> compose grounded narration from available material -> freeze globally feasible plan -> one TTS -> exact-audio alignment -> existing renderer -> actual MP4 audit -> explicit human review.

Implemented:
- Global maximum matching, exact deficit witnesses, byte-level uniqueness and frozen asset/contract provenance.
- PostgreSQL-only runtime ledger: atomic stage claims, exact character budget through existing factory quota functions, one voice attempt, immutable terminal/ambiguous states through the runtime functions.
- Executor rechecks the frozen plan immediately before sending voice and executes one stage per invocation. It never repeats a claimed operation after a lost response.
- Google TTS adapter uses the selected four voices, no speech manipulation and no duration retries.
- Existing media-worker adapters stage the exact reviewed files, align the stored voice, render from real timestamps and invoke the actual full-decode/audio-identity audit.
- Internal CLI and Dockerfile. Public callers must not submit their own visual approval receipts.

Runtime setup (not deployed):
1. Apply factory_v3/ledger.sql to the project PostgreSQL after existing factory provider-budget functions.
2. Build with docker build -f factory_v3/Dockerfile -t factory-v3:VERSION .
3. Provide V3_DATABASE_URL as a secret and a mounted V3_GOOGLE_ACCESS_TOKEN_FILE. Token refresh/provisioning is not yet integrated; an expired token fails without retry.
4. Share the same media volume at /data and internal network with shorts-v2-media-worker-1.
5. Call the internal CLI:
   python3 -m factory_v3.cli create JOB_UUID --plan frozen.json
   python3 -m factory_v3.cli step JOB_UUID
   python3 -m factory_v3.cli status JOB_UUID

Each step advances at most one stage. A running/unknown/failed stage requires evidence-based reconciliation; do not launch it again. QA pass is machine acceptance, never HUMAN PASS.

Verification:
- python3 -m unittest discover -s tests/factory_v3 -v (23 unique tests)
- python3 tests/factory_v3/run_postgres_ledger.py (isolated offline PostgreSQL; no production writes)
- python3 factory_v3/visual_plan.py acceptance/release-coverage/12126-assignment-deficits.json --output acceptance/factory-v3/failed-12126-preflight.json (expected blocked7/9, exit2)

Still missing: trusted availability-led provider/download/review catalog, evidence-grounded composer, automatic credential provisioning, public intake/review wiring, deployment and representative actual-media release acceptance. The new executor has NOT processed a production job. Controlled tests are not provider acceptance.
