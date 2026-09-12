FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /voices && python -m piper.download_voices --data-dir /voices uk_UA-mykyta-high

EXPOSE 5000
CMD ["python", "-m", "piper.http_server", "-m", "uk_UA-mykyta-high", "--data-dir", "/voices", "--host", "0.0.0.0", "--port", "5000"]
