# V6 scope harness failure — 2026-09-11

The first broad current-scope regression run stopped before executing the first product test because the wrapper redirected output to `/tmp/test.out`, which was not writable in this runner context (`Permission denied`). This is a test-harness/operator failure, not a product regression. Do not change product code for it. Re-run the same test scope without the shared `/tmp` redirection.
