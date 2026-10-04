# Continuation instructions for this production project

Start with docs/OPERATOR_RULES.md, docs/DELIVERY_STRATEGY.md and the TOP checkpoint in docs/CODEX_HANDOFF.md. Then read PLAN.md and docs/LESSONS_LEARNED.md before meaningful implementation; docs/PROVIDER_POLICY.md before provider changes.

The user requested a radical change of working method on 2026-10-04: deliver the complete usable project; do not continue an endless one-job/one-patch loop. The release-oriented process in docs/DELIVERY_STRATEGY.md supersedes old next-smoke instructions as the working method, while preserving the product contract, strict gates, production scope and failed-job immutability.

Repository: Pokhyl/ai-short-form-content-factory, main, VPS /opt/ai-short-form-content-factory. Production n8n: publisher.hodor.com.pl. Supporting Compose: shorts-v2. Do not touch unrelated projects/workflows/credentials/domains. Do not alter architecture without evidence. No topic/asset-specific production fixes, weaker acceptance gates, or paid fallbacks.

Every meaningful checkpoint must be committed AND pushed to GitHub with tests/evidence and exact continuation steps. Verify HEAD equals origin/main after push. State explicitly whether code is committed, deployed, offline verified or production accepted. Do not call the project complete because tests pass.

Use one short tool call at a time with an immediate factual update. Long operations run bounded in background. No sleep/poll loops or blind repeated side effects. No subagents unless explicitly authorized. Do not claim HUMAN/audio-listening PASS on an unsupported model surface.
