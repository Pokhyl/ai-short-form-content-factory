# Lessons Learned

Updated: 2026-09-19

1. A restored DB is not automatically production-ready.
Verify owner/auth, project ownership, N8N_PATH, editor URL, webhook URL, and asset paths before cutover.

2. user-management:reset changes auth state.
It preserved workflows and credentials but returned the instance to owner setup. Only use it with an explicit owner re-creation plan.

3. Wrong N8N_PATH can produce a white UI.
Root HTML pointed to /recovery assets and the browser received wrong content for JavaScript. Production root must use N8N_PATH=/ and asset paths must be verified after changes.

4. Do not run duplicate n8n servers on one DB.
Recovery and root must never be active against the same restored single-instance database.

5. A foreign whole .env is not a fix.
The clean shorts-v2 compose was temporarily pointed at a recovery .env and inherited the wrong encryption-key state. shorts-v2 must use only its own .env.

6. n8n volume config can preserve a stale encryption key.
Even after compose was corrected, /home/node/.n8n/config still contained the key created under the bad recovery environment. Inspect the config first; do not blindly replace project secrets.

7. Exit code 0 is not proof of a DB mutation.
A heredoc sent to docker exec without -i did not reach psql. Always verify post-counts and exact IDs.

8. Do not touch unrelated n8n.
n8n.hodor.com.pl is unrelated. publisher.hodor.com.pl contains MCP/business workflows that must remain intact.

9. Google Cloud TTS historically worked, and restored OAuth status must be verified by a live provider call.
The August backup proves repeated successful Cloud TTS executions with the selected voices. On 2026-09-19 the restored OAuth initially failed live refresh despite the UI showing `Account connected`; reconnecting the same credential fixed it and all four locked voices passed.

10. Gemini TTS is not production TTS.
Production narration remains Google Cloud Text-to-Speech.

11. Historical visual failures were systemic.
Too few images and generic loosely related assets are unacceptable. Every shot needs visual intent, must-show/must-not-show, multiple search queries, multi-source discovery, deterministic ranking, and fail-closed relevance.

12. Human review is final.
Machine PASS is provisional. Only explicit HUMAN PASS accepts the exact final MP4.


13. Restoring credentials into the intended production n8n determines where orchestration belongs.
The 9 credentials were restored into `publisher.hodor.com.pl` so the video project could use them there. Creating another n8n afterward defeats that work and creates unnecessary OAuth, routing, authentication and encryption-key problems.

Prevention:
- production video orchestration stays in `publisher.hodor.com.pl`;
- MCP/ADMIN workflows remain protected by exact identity;
- supporting services may be isolated, but production n8n/credentials stay in publisher;
- no new n8n domain or second production n8n without a proven technical blocker and explicit user approval.


14. An encrypted n8n credential export is not a usable recovery source without its original encryption key.
The related recovery export still contains the old Google Gemini API credential metadata, but the source encryption key is not preserved in the project/recovery files and the available recovery key does not decrypt it.

Prevention:
- preserve the matching n8n encryption key whenever encrypted credential exports are retained;
- never treat credential presence in an encrypted export as proof that the secret is recoverable;
- do not copy encryption keys from unrelated n8n instances as a shortcut.


15. Do not double-escape executable strings when generating n8n workflow JSON.
The first M3 Postgres node stored literal `\\n` sequences inside SQL. n8n passed the backslashes to PostgreSQL, which failed with a syntax error near `\`.

Prevention:
- generate executable SQL/code as the actual runtime string, then JSON-serialize it exactly once;
- after importing a generated workflow, read the stored node parameter back from the n8n database before publishing;
- run a real workflow execution, not only a JSON/schema validation;
- treat a successful credential connection as separate from query correctness.

16. A Code node returning multiple items must use Run Once for All Items.
The first M4 execution used Run Once for Each Item but returned an array of items, so n8n rejected the output before search.

Prevention:
- when a Code node fan-outs one input into multiple items, use `runOnceForAllItems`;
- test node execution semantics, not only JavaScript syntax.

17. Prefer provider-parsed URL metadata over browser globals inside the n8n Code sandbox.
SearXNG already returns `parsed_url`. The first M4 candidate normalizer wrapped `new URL(...)` in a catch; every candidate was silently discarded in the Code sandbox. Rebuilding canonical URLs from SearXNG `parsed_url` produced the expected 10 independent candidates.

Prevention:
- use structured provider fields when available;
- never hide every parse failure behind a catch that converts the entire candidate pool to empty;
- unit-check candidate counts on retained real provider output before consuming another product test job.


18. A scene-count range plus a separate shot-count floor does not reliably produce the required visual density.
The first M5 live output was otherwise valid, but Gemini chose 5 scenes and one shot per scene, producing 5 shots when a 30-second job required at least 7. The validator correctly rejected it and the job remained immutable.

Prevention:
- do not weaken the visual-density gate after underproduction;
- use a deterministic generic density contract by duration;
- M5 now requires exactly 4/7/10/13 scenes and exactly one shot per scene for 15/30/45/60 seconds;
- test fixes only on a fresh job after a terminal failure.


19. Before modifying the next milestone, inspect existing local stage files and the live database state.
M6 already had a local migration, production workflow and applied DB schema from the immediately preceding work. Rebuilding the stage from memory would have duplicated or weakened already-established invariants.

Prevention:
- before creating a new milestone file, search the project for that milestone/workflow name;
- inspect live DB tables/functions and publisher workflow rows first;
- preserve stronger existing invariants instead of replacing them with a newly improvised contract;
- only apply a migration after confirming whether its objects already exist.
