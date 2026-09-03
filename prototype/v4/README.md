# V4 direct prototype

This prototype deliberately runs outside n8n/PostgreSQL. It pins and adapts MoneyPrinterTurbo for provider/TTS/Whisper/material/video services while keeping only the product-specific V4 director, speech guard and representation router in this repository.

Upstream pin: see `upstreams.lock.json`.

Basic commands from repository root:

```bash
PYTHONPATH=. python3 -m prototype.v4.cli verify-upstream
PYTHONPATH=. python3 -m prototype.v4.cli validate director.json
PYTHONPATH=. python3 -m prototype.v4.cli manifest director.json --output manifest.json
```

Director generation uses MoneyPrinterTurbo's pinned provider adapter. The default provider is Ollama and requires `V4_LLM_MODEL`; optionally set `V4_LLM_BASE_URL`. No hosted paid provider is mandatory.

The `voice` command uses MoneyPrinterTurbo Edge TTS at natural rate. The `transcribe` command uses its faster-whisper path on the actual audio.

Production semantic-v3 is intentionally not invoked by this prototype.
