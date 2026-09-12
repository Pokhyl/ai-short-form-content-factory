FROM gyoridavid/short-video-maker:latest-tiny
RUN cd /app/data/libs/whisper/models && sh ./download-ggml-model.sh tiny
COPY Kokoro.js /app/dist/short-creator/libraries/Kokoro.js
COPY Pexels.js /app/dist/short-creator/libraries/Pexels.js
COPY shorts.js /app/dist/types/shorts.js
COPY PortraitVideo.js /app/dist/components/videos/PortraitVideo.js
COPY ShortCreator.js /app/dist/short-creator/ShortCreator.js
ENV WHISPER_MODEL=tiny
CMD ["node", "dist/index.js"]
