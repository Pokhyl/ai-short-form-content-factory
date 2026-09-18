# AI Short-Form Content Factory

Clean rebuild from 2026-09-18.

## Product

Input:
- topic
- language: en / pl / ru / uk
- duration: 15 / 30 / 45 / 60 seconds

Output:
- one vertical 9:16 MP4

Target path:

topic + language + duration
-> text/script
-> one continuous final TTS synthesis
-> free visual sourcing
-> local timing/alignment
-> local render
-> MP4

## Hard constraints

- n8n is the orchestrator.
- Free-only production path.
- No paid API, paid fallback, or hidden billing dependency.
- Gemini text is allowed only on a verified Free Tier model.
- Gemini TTS is allowed only on a verified Free Tier model.
- Exactly one final TTS synthesis per production job.
- No Gemini/API transcription in production; timing/alignment must be local.
- No Gemini/API visual verification in production; verification must be local/deterministic.
- Visual sources must be free to access and suitable for reuse; Wikimedia is the first source.
- Rendering is local with FFmpeg/Remotion or another verified local tool.
- No publishing/UI work until one real end-to-end MP4 passes human review.
- No provider or dependency may be added before its actual license, runtime requirements, and free-tier limits are checked.
- No changes to other projects or shared services unless explicitly required and proven safe.

See `config/free-only-policy.json` for the machine-readable production policy.
