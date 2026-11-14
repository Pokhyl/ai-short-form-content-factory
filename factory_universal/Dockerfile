FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends espeak-ng ffmpeg fonts-dejavu-core ca-certificates && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir Pillow==11.3.0 onnxruntime==1.23.2 tokenizers==0.22.1 numpy==2.3.4 psycopg[binary]==3.2.10
WORKDIR /app
COPY app.py /app/app.py
COPY visual_verifier.py /app/visual_verifier.py
EXPOSE 3000
CMD ["python3", "/app/app.py"]

COPY fixtures /app/fixtures
