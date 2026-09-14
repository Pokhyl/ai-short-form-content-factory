# Failure Ledger

## F-001 — Polish render stalled with English-only Whisper
- Symptom: Edge-TTS completed, output MP4 stopped growing and lacked a `moov` atom; renderer queue stayed `processing`.
- Evidence: upstream container reported `WHISPER_MODEL=tiny.en`.
- Disposition: affected job was marked `failed`; it was not resumed or manually repaired.
- Systemic fix: derived renderer image bundles multilingual Whisper `tiny` and sets `WHISPER_MODEL=tiny`.
- Verification: a fresh Polish job completed to `ready`, produced a valid 1080x1920 H.264/AAC MP4, and downloaded through WF03 with matching SHA-256.
