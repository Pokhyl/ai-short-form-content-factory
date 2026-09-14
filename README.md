# AI Short-Form Content Factory — clean rebuild

Current architecture:

- n8n: orchestration
- short-video-maker: rendering/TTS/captions/media engine
- FFmpeg/Remotion/Whisper/Kokoro inside the engine
- generated videos: `data/videos`

Phase 1 target: prove n8n -> engine -> vertical MP4.
No publishing is enabled.
