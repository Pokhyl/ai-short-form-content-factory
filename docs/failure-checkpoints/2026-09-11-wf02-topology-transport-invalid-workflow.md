# WF02 topology materializer workflow validation failure — 2026-09-11

GitHub Actions run `34635228739` completed as failure with `jobs=[]`: GitHub did not create any job, so the generated Actions workflow itself failed validation before execution. No checkout, product edit, test execution, commit, result branch, or runtime mutation occurred. This is transport-harness failure only. Stop using GitHub Actions materializers for this correction; use Git Data API primitives directly to create the already locally verified source/test blobs, tree, commit, and fast-forward ref.
