FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends espeak-ng ffmpeg fonts-dejavu-core ca-certificates && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir Pillow==11.3.0 onnxruntime==1.23.2 tokenizers==0.22.1 numpy==2.3.4 psycopg[binary]==3.2.10
RUN pip install --no-cache-dir opencv-python-headless==4.13.0.92
RUN pip install --no-cache-dir ctranslate2==4.9.1 sentencepiece==0.2.1
WORKDIR /app
COPY app.py /app/app.py
COPY storyboard.py /app/storyboard.py
COPY source_translation.py /app/source_translation.py
COPY photo_duplicates.py /app/photo_duplicates.py
COPY renderer.py /app/renderer.py
COPY alignment_core.py /app/alignment_core.py
COPY index.html /app/index.html
COPY visual_verifier.py /app/visual_verifier.py
EXPOSE 3000
CMD ["python3", "/app/app.py"]

COPY fixtures /app/fixtures
