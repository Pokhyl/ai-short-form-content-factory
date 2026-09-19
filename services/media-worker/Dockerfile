FROM ghcr.io/ggml-org/whisper.cpp@sha256:9cfbaf11ef5bec57ec9cade6af7ed991ab5e32b01a6e40db3380a12363336e11 AS whisper

FROM python:3.13-slim@sha256:9d2e5553305c7c7b0097999bb17187c69b921ccd6bc9d40e4bb5ebe652c00285

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg ca-certificates libgomp1 libstdc++6 \
 && rm -rf /var/lib/apt/lists/*

COPY --from=whisper /app/build/bin/whisper-cli /opt/whisper/whisper-cli
COPY --from=whisper /app/build/bin/libwhisper.so.1 /opt/whisper/libwhisper.so.1
COPY --from=whisper /app/build/bin/libggml.so.0 /opt/whisper/libggml.so.0
COPY --from=whisper /app/build/bin/libggml-base.so.0 /opt/whisper/libggml-base.so.0
COPY --from=whisper /app/build/bin/libggml-cpu.so.0 /opt/whisper/libggml-cpu.so.0

ENV LD_LIBRARY_PATH=/opt/whisper

WORKDIR /worker
COPY server.py /worker/server.py

EXPOSE 3001
CMD ["python3", "/worker/server.py"]
