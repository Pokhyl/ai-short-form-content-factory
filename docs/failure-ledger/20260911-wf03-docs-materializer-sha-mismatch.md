# 2026-09-11 — WF03 docs materializer transport SHA mismatch

GitHub Actions run `34618725874` (`Materialize WF03 duration unit docs`) failed before checking out the target parent or applying any repository patch.

Exact failure: the extracted transport patch at `.transport/wf03-duration-unit-docs-20260911.patch` did not match the expected local SHA256 `612afd0585f5b4438387cc9161b38759da2770caa2de9b5ef0c7527be13fb309`; `sha256sum -c` returned `FAILED` and the job exited 1.

No result branch was created, the target branch was not advanced by the materializer, and no server/runtime/product state was changed by this failed Action.

Correction rule: inspect the exact bytes stored on the GitHub transport branch and keep the integrity check; do not bypass verification or treat this transport failure as product evidence.
