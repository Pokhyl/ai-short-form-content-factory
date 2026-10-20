# Narrative provider deadline correction — 2026-10-20

Actual normal run77e850da-b9aa-479f-9e10-e763ea4b2789 on0152761 completed research/materials. Gemini3.8 story generation returned explicit503 once, then succeeded in48seconds through the existing separately metered policy. Its independent review hit the application90second HTTP deadline and is durably UNKNOWN. Pipeline terminal needs_attention/EXTERNAL_OPERATION_UNCERTAIN. Zero TTS/MP4 for this normal run. Never replay/rescue its UUID or uncertain review call.

The model capability and measured voice boundary remain valid: known-bad controls rejected, source/native correction reviewed, single actual14208ms MP3 passed15s band. The failed normal run exposes a separate transport deadline mismatch: existing caller90s was shorter than native upstream120s and workflow180s.

Candidate fixed-role hierarchy for Gemini3.8: upstream240s < caller270s < workflow300s. No payload, source, native-quality, token or call-count limit is relaxed. Unknown sends still fail terminal and are not automatically retried. Other provider HTTP deadlines remain as before. One shared Python profile generates native role/workflow limits and supplies the caller limit; regression compares hierarchy and proves a timeout does not resend.

Next: exact-image/native tests; publish scoped gateway profile and app from the same candidate source with protected snapshots; one fresh multilingual semantic/performance boundary with no relation to rescuing the old job, then one new normal automatic request. No old-ID replay, paid fallback or extra voice for the14208ms diagnostic.
