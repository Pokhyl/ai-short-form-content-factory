# V3 trusted runtime

The image embeds its exact Git source revision. The private settings file is mounted at /run/factory-v3/settings.json and must have mode 0600. It contains database_url, broker_token, credential_scope and an independently verified Gemini free_tier_proof; never commit this file. The native credential gateway is inactive until a separately scoped deployment. Existing credential values remain in n8n.

Public intake may submit only topic, language (pl/en/ru/uk) and seconds (15/30/45/60). It must generate a fresh UUID, call request once and run once. It must not accept caller plans, credentials, budgets or review receipts.

Commands:
    python -m factory_v3.cli version
    python -m factory_v3.cli request --job-id UUID --topic "TOPIC" --language pl --seconds 15
    python -m factory_v3.cli run --job-id UUID
    python -m factory_v3.cli status --job-id UUID

Repeated request creation is read-only for an identical identity. Running/failed/unknown external attempts are never automatically retried. Machine QA does not establish human acceptance. No live V3 job has passed yet.
