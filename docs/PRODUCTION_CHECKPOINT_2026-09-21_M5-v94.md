# Production checkpoint — 2026-09-21 — M5 v94

This checkpoint records historical deployment state before SentinelX disconnected. **Continuation update:** M5 v94 runtime was subsequently confirmed by execution 9122; PL15 cd432c5e-20b2-4f08-ad45-3cc21d4ee588 reached machine PASS but failed exact-frame visual review. M8 has since advanced to v46. See the authoritative Resume section in CODEX_HANDOFF.md; do not execute this historical Next exact step again.

## Production versions

- M5 `VideoM5Storyboard001`: **versionCounter 94**, activeVersionId/versionId `b4122d0a-5754-4311-8b7a-adab15ff0697`.
- M8 `VideoM8Visuals001`: **versionCounter 45**, versionId `3778d30c-70c0-4cd2-9df8-e8465d4fdd7a`.
- M6 remains versionId `98e671f3-a0dc-42fa-81e9-4c9524a05e6a`.
- M7 remains versionId `91fbac4f-f40d-4d75-9111-3e4ed01bd9ff`.
- Media-worker remains the existing full-fit renderer image from the prior checkpoint.

## M5 v94 deployment

Repository commit before deployment: `748c6e0046d317c4673de1f558b2639953de67f3` (`fix: drop nonvisual process anchors from must show`).

Deployment completed successfully before agent disconnect:
- no project executions were running/waiting before import;
- exact v93 backup: `.backups/m5-before-process-anchor-20260921-114529.json`;
- only `VideoM5Storyboard001` was imported/published;
- M5 became counter 94 / activeVersionId `b4122d0a-5754-4311-8b7a-adab15ff0697`;
- aggregate hash of the other 31 workflow rows remained identical: `82bea1f9183f9a16961489ab0c438e5c`.

The n8n CLI printed its standard restart advisory. No restart was issued. Runtime v94 has **not yet** been confirmed by a fresh execution snapshot because the SentinelX agent disconnected immediately after publication.

## v94 change

The M5 storyboard validator no longer turns process/state concepts into hard visual requirements when they are secondary `must_show` anchors.

Examples covered by regression:
- `["penstock","water flow"] -> ["penstock"]`
- `["electric generator","energy generation"] -> ["electric generator"]`
- `["turbine","shaft rotation"] -> ["turbine"]`

Visible independent context remains allowed/required where appropriate; e.g. a visible spillway plus falling water remains a valid pair.

Validation before deploy:
- full Node suite: **58/58 PASS**;
- all **55 M5 Code nodes** passed `node --check`;
- `git diff --check` PASS.

## Diagnostic jobs leading to v94

### v91 PL15
Job `debf4427-9e6e-47b3-a413-c61c2693ce9e`:
- M5 v91 PASS;
- M6 PASS;
- M7 PASS;
- M8 v45 FAIL on S4-A.
Root cause: `electric generator + industrial machinery` made generic machinery a hard secondary requirement. This led to v92.

### v92 PL15
Job `e61a97d5-ac1d-403f-a21f-15bd2c5df6c0`:
- M5 v92 PASS;
- M6 PASS;
- M7 PASS;
- M8 v45 FAIL on S4-A.
Root cause: `electric generator + turbine shaft` required a secondary concept not requested by the shot's own visual_intent. This led to v93.

### v93 PL15
Job `1f37dca9-e46e-427d-8844-2447e806c2f3`:
- M4 PASS;
- M5 v93 PASS, execution 9113;
- M6 PASS, execution 9114, final audio 14,376 ms;
- M7 PASS, execution 9115;
- M8 v45 FAIL, execution 9116, after all 45 searches / 306 candidates;
- failed shot S2-A: visual_intent `Water rushing down through a large penstock pipe`, must_show `["penstock","water flow"]`.
Real penstock candidates were retrieved, but `water flow` was treated as a hard secondary subject even though flow inside a closed penstock is not necessarily visible. This is the direct regression fixed by v94.

## Next exact step

When SentinelX reconnects:
1. verify M5 live row is still counter 94 / `b4122d0a-5754-4311-8b7a-adab15ff0697`;
2. verify publisher/Studio 200 and n8n/media-worker healthy with restart counts unchanged;
3. export live M5 and confirm core matches repository, including `secondaryProcessHeads`;
4. create a fresh PL15 only:
   - topic: `jak działa elektrownia wodna?`
   - language: `pl`
   - duration: 15
5. confirm M5 execution snapshot uses v94;
6. run the same job through M6 -> M7 -> M8 v45 -> M9;
7. if it reaches machine_qa_passed, inspect exact final MP4 before starting EN30;
8. if it fails, diagnose the exact failed shot/execution and make only a systemic fix.

Do not claim v94 runtime acceptance or PL15 acceptance until the fresh execution exists.
