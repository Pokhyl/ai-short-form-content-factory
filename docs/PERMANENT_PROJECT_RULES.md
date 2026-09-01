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
