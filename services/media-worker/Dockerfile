FROM ghcr.io/ggml-org/whisper.cpp:main-da54572229bcf64ba367d96c7ef15770376c4280@sha256:9cfbaf11ef5bec57ec9cade6af7ed991ab5e32b01a6e40db3380a12363336e11

WORKDIR /worker
COPY server.py /worker/server.py

USER 1000:1000

EXPOSE 3001
ENTRYPOINT ["python3", "/worker/server.py"]
