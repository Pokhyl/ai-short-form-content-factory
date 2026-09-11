# 2026-09-11 — WF03 docs materializer patch lost final newline

GitHub Actions run `34619102479` (`Materialize WF03 duration unit docs v2`) passed the corrected SHA256 integrity check for the exact transport file, checked out parent `fadfab4b19cc3e2cbf7d0e0118c2faca9da58057`, then failed at `git apply --check` with `corrupt patch at /tmp/change.patch:24`.

Inspection established that the local generated patch was 5506 bytes and ended with a newline, while the GitHub Contents transport file was 5505 bytes. The contents-API write preserved the text except for the final newline, so the unified patch was syntactically incomplete for `git apply`.

No result branch was created, the target branch was not advanced by the materializer, and no server/runtime/product state changed.

Correction rule: retain the SHA256 check against the exact stored transport bytes, then restore exactly one terminal newline in the temporary patch before `git apply`; do not weaken integrity verification.
