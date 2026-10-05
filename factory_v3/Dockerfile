FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY factory_v3/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY factory_v3 /app/factory_v3
COPY scripts/audit_final_media.py /app/scripts/audit_final_media.py
ENTRYPOINT ["python3", "-m", "factory_v3.cli"]
CMD ["--help"]
