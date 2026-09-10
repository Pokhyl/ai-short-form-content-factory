from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from urllib.request import urlretrieve

from huggingface_hub import snapshot_download

WHISPER_REVISION = "536b0662742c02347bc0e980a01041f333bce120"
VOICES = {
    "en_US-norman-medium": (
        "en/en_US/norman/medium",
        "b9739443232a80a59c7d18810dd856899bf16a7964725f5ab81ea49b1351cb71",
        "6c2db7f558a4a8deb9fe822583c1c5105f6c4e834dd0f9de8ad17a888ee9fe1d",
    ),
    "pl_PL-darkman-medium": (
        "pl/pl_PL/darkman/medium",
        "db505438a5364e8e2e0242c4324130a873ed660dfbe8d9689cef428ffb1b645f",
        "70f999f11fa8ad13d3ef779041ee93c9f38be5abdbacdfad42449712fe91c81b",
    ),
    "ru_RU-dmitri-medium": (
        "ru/ru_RU/dmitri/medium",
        "f073356ebc4bd0f80c5af58df2953a5988bd5bdab1eb38635ce960b071fbefcb",
        "667ef3117bc642c2892dff7690d8bdc8ca4228aeaa783b2dc1416df632855e0d",
    ),
    "uk_UA-mykyta-high": (
        "uk/uk_UA/mykyta/high",
        "081d253cd246d7d4d698c6dd147b74cad498dafd213527887a3a490519138243",
        "b5db6b4efb02d4a0e8f128253fd64e82dfa72d1105e9060b0c6fd9610eec6a4f",
    ),
}
WHISPER_FILES = {
    "model.bin": "3e305921506d8872816023e4c273e75d2419fb89b24da97b4fe7bce14170d671",
    "config.json": "b55496ac7940a7ae47d2c01eab40edfd8701feec1229d9cce3b40014383fb828",
    "tokenizer.json": "fb7b63191e9bb045082c79fd742a3106a12c99513ab30df4a0d47fa6cb6fd0ab",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice-dir", required=True)
    parser.add_argument("--whisper-dir", required=True)
    args = parser.parse_args()
    voice_dir = Path(args.voice_dir)
    whisper_dir = Path(args.whisper_dir)
    voice_dir.mkdir(parents=True, exist_ok=True)
    whisper_dir.mkdir(parents=True, exist_ok=True)

    base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
    for name, (folder, model_sha, config_sha) in VOICES.items():
        for suffix, expected in ((".onnx", model_sha), (".onnx.json", config_sha)):
            target = voice_dir / f"{name}{suffix}"
            urlretrieve(f"{base}{folder}/{target.name}", target)
            actual = sha256_file(target)
            if actual != expected:
                raise SystemExit(f"Piper voice checksum mismatch for {target.name}: {actual}")

    snapshot_download(
        repo_id="Systran/faster-whisper-small",
        revision=WHISPER_REVISION,
        local_dir=str(whisper_dir),
    )
    for name, expected in WHISPER_FILES.items():
        path = whisper_dir / name
        actual = sha256_file(path)
        if actual != expected:
            raise SystemExit(f"Whisper checksum mismatch for {name}: {actual}")

    print("PINNED_TTS_MODELS_READY")


if __name__ == "__main__":
    main()
