# Operator Execution Rules

Before every meaningful change:
1. Read PLAN.md.
2. Read docs/CURRENT_STATE.md.
3. Read docs/LESSONS_LEARNED.md.
4. Read docs/PROVIDER_POLICY.md before provider/API changes.
5. Confirm scope is /opt/ai-short-form-content-factory and Compose project shorts-v2.
6. Do not touch unrelated projects, databases, containers, credentials, domains, or repositories.

For destructive actions:
- identify exact IDs/names first;
- create rollback backup when state matters;
- use explicit allowlists, never broad pattern deletion;
- execute once;
- verify exact post-state immediately.

A zero exit code is not proof that the intended state changed.

Runtime rules:
- never run two n8n servers against the same single-instance PostgreSQL DB;
- never route production root through a recovery base path;
- after N8N_PATH/proxy/editor URL changes, verify root HTML and a referenced JS asset;
- shorts-v2 uses only project-local .env;
- never reuse another stack's entire .env;
- never copy another installation's encryption key as a troubleshooting shortcut;
- on encryption-key mismatch, inspect local n8n config before changing secrets.

n8n/database rules:
- PostgreSQL is source of truth;
- docker exec receiving heredoc/stdin requires -i;
- after SQL mutation verify row counts and exact IDs;
- old/rejected video workflows are not a baseline and must not be restored;
- failed/rejected product jobs remain immutable.

Product rules:
- n8n mandatory;
- free-only production, no paid fallback;
- no OpenAI, Anthropic, OpenRouter, Groq, ElevenLabs, FAL, Ollama, local LLM, or model-worker;
- Gemini TTS is not production TTS;
- Google Cloud TTS is the production voice path;
- one continuous final narration;
- never change speech speed or trim narration to force duration;
- multi-source visuals with relevance gates;
- no topic-specific hacks or manual asset selection;
- only explicit HUMAN PASS accepts final output.

Failure handling:
- after two failures of the same approach, change strategy;
- do not weaken gates;
- record systemic defects in docs/LESSONS_LEARNED.md;
- record resulting state in docs/CURRENT_STATE.md.


## Production n8n lock
- Production video orchestration runs only in `publisher.hodor.com.pl`.
- The existing 22 MCP/ADMIN workflows there are protected.
- The restored 9 credentials stay there and are the credential base for the video project.
- Do not create a second production n8n.
- Do not create or repurpose another n8n domain.
- Do not use `tiktok-n8n.hodor.com.pl` for this project.
- Do not use or modify `n8n.hodor.com.pl` for this project.
- Supporting Postgres/media-worker/SearXNG may remain isolated; orchestration and production credentials do not move out of publisher.
- Any exception requires a documented technical blocker and explicit user approval before implementation.
