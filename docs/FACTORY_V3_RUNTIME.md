# V3 trusted runtime

The image embeds its exact Git source revision. The private settings file is mounted at /run/factory-v3/settings.json and must have mode 0600. It contains database_url, broker_token, credential_scope and an independently verified Gemini free_tier_proof; never commit this file. The native credential gateway is active in `publisher.hodor.com.pl` as `VIDEO-V3-Credential-Gateway`; it uses a dedicated V3 Gemini credential and the existing Google Cloud TTS credential. Current production model is 3.6 and the planned 3.5 alignment is not deployed yet. Existing credential values remain in n8n.

Public intake may submit only topic, language (pl/en/ru/uk) and seconds (15/30/45/60). It must generate a fresh UUID, call request once and run once. It must not accept caller plans, credentials, budgets or review receipts.

Commands:
    python -m factory_v3.cli version
    python -m factory_v3.cli request UUID --topic "TOPIC" --language pl --seconds 15
    python -m factory_v3.cli run UUID
    python -m factory_v3.cli status UUID

Repeated request creation is read-only for an identical identity. Running/failed/unknown external attempts are never automatically retried. Machine QA does not establish human acceptance. Historical request `72705d11-4556-4a4a-b751-676cc71e215d` produced a 60,000 ms UK60 MP4 with 17 unique photos and one TTS, and passed machine QA on an earlier runtime. The user rejected the narration as unusable, so that file is not an accepted deliverable or proof of the current release. The current natural-speed voice acceptance is still open: r10/r11 stopped on Gemini HTTP 503 before proofread and produced no MP4.

Owner service: python -m factory_v3.server --settings /run/factory-v3/settings.json --media-root /data --port 3002
Mount the media volume read/write for the producer. Join only project networks shorts-v2_default and n8n_default. Route /factory-v3/* without stripping its prefix on studio.hodor.com.pl; rewrite only the studio root to /factory-v3/ at the proxy. Runtime settings include owner_token (separate >=32 characters), public_origin=https://studio.hodor.com.pl and public_access=true for the password-free studio. Public access exposes the studio history and operations to site visitors; retain the same-origin POST check, bounded queue and provider budgets. Apply review.sql only alongside V3 ledger/preparation/cache migrations. No automatic job recovery or retry after a restart. Max one running/four waiting jobs. Accepted decisions are immutable; generation remains independently machine-gated.
