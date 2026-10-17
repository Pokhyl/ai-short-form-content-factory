FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY factory_v3/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY factory_v3 /app/factory_v3
COPY material_first /app/material_first
COPY factory_next /app/factory_next
COPY scripts/audit_final_media.py scripts/replay_material_preparation.py /app/scripts/
ARG SOURCE_REVISION
ENV FACTORY_V3_REVISION=$SOURCE_REVISION
ENTRYPOINT ["python3", "-m", "factory_v3.cli"]
CMD ["--help"]
