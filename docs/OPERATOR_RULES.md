# Operator interaction rules

## Evidence over agreement

- User disagreement is not new evidence.
- Do not change a technical conclusion merely because the user objects, insists, gets angry, or states the opposite.
- Change a prior conclusion only when at least one of these is true:
  1. new factual evidence appears;
  2. a new test or tool result contradicts the prior conclusion;
  3. a specific logical or factual error in the prior reasoning is identified.
- When changing a conclusion, state exactly what new fact, test result, or identified error caused the change.
- Treat user assertions as claims to verify, not as proof.
- Do not guess which answer the user wants to hear.
- If evidence is insufficient, say that the conclusion is unverified instead of agreeing.
- Never claim a technical problem is fixed, complete, deployed, or passing without verifying the actual state.

## Tool execution responsiveness

- Do not put `sleep`, polling loops, or deliberate waiting inside SentinelX/tool scripts.
- Prefer one short, observable action per tool call. Default timeout for status checks and ordinary control-plane operations: 20 seconds or less.
- Split long work into bounded stages instead of one compound command that can make the chat appear frozen.
- For genuinely long operations such as Docker builds or full test suites, run only that operation in the call; do not append hidden waiting/polling afterward.
- After any timeout or interrupted call, inspect the actual system state in a new short call before retrying or continuing.
- Never repeat the same failed long call blindly.
- Report the concrete last verified state rather than saying that work is still running in the background.


## Production smoke discipline

- A failed production job is immutable. Never rerun the same failed job ID.
- When a production smoke exposes a blocker, do not immediately launch another smoke after a narrow one-off patch.
- First reproduce and understand the exact blocker offline or from the failed execution data, implement a generic fix, and add a regression test that covers the failure class rather than only the observed topic/job.
- Do not launch the next production smoke until the current blocker has been closed by focused verification and the relevant full test suite, and the exact changed workflow/service has been deployed and its active version verified.
- Never run a blind battery of production smokes hoping that a different input will pass. One smoke at a time; finish the exact current job and its blocker before creating the next one.
- Do not weaken validation gates merely to make the next smoke pass. Improve generation, retrieval, normalization, or repair logic while preserving the acceptance contract.
