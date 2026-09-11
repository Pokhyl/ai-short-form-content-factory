# V6 regression fixture failure — 2026-09-11

The first `v6_storyboard_purpose_canonicalization_regression.mjs` run reached the unchanged storyboard mechanism gate and failed with `process/mechanism storyboard contains no constructed diagram`.

Cause: the new test fixture used a `why`/mechanism topic but supplied only external-media shots. This is a regression-fixture defect, not a product or canonicalizer failure. Do not weaken the mechanism diagram requirement. Correct only the fixture so it contains a valid diagram scene, then rerun the unchanged purpose canonicalizer and existing storyboard gates.
