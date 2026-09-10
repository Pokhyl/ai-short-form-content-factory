FROM node:22-bookworm-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core ca-certificates chromium python3 python3-venv \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY python ./python
RUN python3 -m venv /opt/tts-venv \
  && /opt/tts-venv/bin/pip install --no-cache-dir piper-tts==1.2.0 faster-whisper==1.2.1 requests==2.32.5 \
  && /opt/tts-venv/bin/python /app/python/download_tts_models.py --voice-dir /opt/piper-voices --whisper-dir /opt/faster-whisper-small

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY src ./src
COPY remotion ./remotion

ENV NODE_ENV=production \
    TTS_PYTHON=/opt/tts-venv/bin/python \
    PIPER_VOICE_DIR=/opt/piper-voices \
    FASTER_WHISPER_MODEL_DIR=/opt/faster-whisper-small
EXPOSE 3001

CMD ["node", "src/server.mjs"]
