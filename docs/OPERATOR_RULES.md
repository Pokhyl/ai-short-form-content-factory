# Operator Rules

Before every meaningful action on this project:

1. Read `docs/PLAN.md`.
2. Read `config/free-only-policy.json`.
3. Confirm the target is `Pokhyl/ai-short-form-content-factory` and/or the isolated `shorts-v2` runtime.
4. Inspect current source/runtime before changing dependencies or architecture.
5. Never touch another project to make this one work.
6. Never add a paid or non-approved external provider.
7. Never add a second TTS call to the production path.
8. If evidence is insufficient, inspect first instead of guessing.
9. After a fix: test it, verify the real output, then continue.
10. Keep failed jobs immutable; create a new test job.
