# Permanent Project Rules

These rules are mandatory for all future technical work on `Pokhyl/ai-short-form-content-factory`.

## 1. Read GitHub first, every time

Before every technical response, diagnosis, code/config change, deployment, test, or recommendation for this project, first read this file from GitHub.

Then read the latest project source-of-truth for the active work. For the rebuild, `docs/CURRENT_STATE.md` is authoritative; architecture changes additionally require `docs/ARCHITECTURE.md`; milestone/acceptance/gate changes additionally require `docs/ROADMAP.md` and `docs/PROCESS_GATE.md`; upstream/provider decisions additionally require `docs/UPSTREAM_DECISION.md`.

Do not rely on chat memory as the source of truth. Repository state overrides chat memory.

## 2. No quota-limited hosted AI in the production critical path

Production must not depend on a request-count/rate/quota-limited hosted AI Free Tier as a required generation dependency.

Gemini Free Tier failures such as `429 RESOURCE_EXHAUSTED`, request-per-window/day quotas, and `503 high demand` are not acceptable normal operating conditions to wait around, retry around, or design around.

Do not solve quota exhaustion with sleeps, retry loops, quota-window waiting, model hopping, extra API keys/accounts/projects, paid fallback, or weaker acceptance gates.

The systemic direction is to remove quota-limited hosted semantic AI from the required production path while preserving:

- 0 PLN per-video API cost;
- truthful factual narration;
- existing quality/acceptance gates;
- exactly three persistent project services unless a separately proven architectural blocker justifies a documented change.

Any proposal that keeps Gemini or another quota-limited hosted AI as a required production dependency violates this rule unless the user explicitly reverses it.

## 3. Durable engineering history is mandatory

Every meaningful technical change and every discovered failure must be recorded in GitHub so the project does not repeat solved mistakes after a chat/context reset.

`docs/CURRENT_STATE.md` remains the operational source of truth for the active branch. `docs/ENGINEERING_HISTORY.md` is the required durable chronological engineering log for detailed changes, failures, root causes, regressions, rejected approaches, deployments and rollback facts.

Before moving past a meaningful change or failure, record the relevant facts, including when applicable:

- what changed: code, workflow, schema, configuration, provider contract, deployment, acceptance gate, or architecture;
- why it changed and the systemic defect/root cause it addresses;
- exact affected files/workflows/services and important job/execution IDs;
- test/regression result and what behavior it proves;
- production deploy/rollback state and rollback location when applicable;
- newly discovered error/failure, including the concrete symptom and the first verified root cause;
- rejected approaches when repeating them later would recreate the same failure;
- unresolved blockers and the exact next action.

Do not record guesses as facts. Mark hypotheses as hypotheses until verified.

Do not silently overwrite or erase a previous mistake. If an earlier result was incorrectly called PASS, explicitly record that it was invalidated, why it was invalidated, and what new regression/acceptance rule prevents recurrence.

A fix is not complete merely because code changed. The durable record must make it possible for a future session to understand the failure, the root cause, the implemented correction, and the proof without relying on chat memory.

Before starting a new approach, check both `docs/CURRENT_STATE.md` and `docs/ENGINEERING_HISTORY.md` for the same or equivalent failure so previously rejected/broken approaches are not repeated.

## 4. Logging cadence

Do not wait until the end of a long session to write history. Record a verified root cause, a material architectural/code change, a meaningful failed test, or an accepted regression result before moving on to the next independent stage.

Small transient command typos do not need separate entries unless they could mislead acceptance or are likely to recur. Any diagnostic mistake that could create a false PASS/FAIL must be recorded.
