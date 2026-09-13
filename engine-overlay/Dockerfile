FROM gyoridavid/short-video-maker:latest-tiny@sha256:4cbb6bfd1ceca2a812833ec5773cabc7376e0922bc32cd35fc400bf0f2485c3b
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv && rm -rf /var/lib/apt/lists/*
COPY visual-requirements.txt /tmp/visual-requirements.txt
RUN python3 -m venv /opt/visual-nlp && /opt/visual-nlp/bin/pip install --no-cache-dir -r /tmp/visual-requirements.txt
ENV VISUAL_PYTHON=/opt/visual-nlp/bin/python
RUN cd /app/data/libs/whisper/models && sh ./download-ggml-model.sh tiny
COPY Kokoro.js /app/dist/short-creator/libraries/Kokoro.js
COPY Whisper.js /app/dist/short-creator/libraries/Whisper.js
COPY Pexels.js /app/dist/short-creator/libraries/Pexels.js
COPY VisualSubject.js visual-lemmas.py /app/dist/short-creator/libraries/
COPY shorts.js /app/dist/types/shorts.js
COPY PortraitVideo.js /app/dist/components/videos/PortraitVideo.js
COPY ShortCreator.js /app/dist/short-creator/ShortCreator.js
ENV WHISPER_MODEL=tiny
CMD ["node", "dist/index.js"]
