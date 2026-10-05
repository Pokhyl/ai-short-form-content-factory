"""Download only bounded selected candidates, once, for exact-byte model review."""
import hashlib
from pathlib import Path
from uuid import UUID
from .preflight import digest, validate_asset
from .providers import media_url
from .worker_adapters import probe_photo


class PhotoDownload:
    def __init__(self, root, request_id, calls, http, probe=probe_photo):
        self.root = Path(root).resolve()
        self.request_id = str(UUID(str(request_id)))
        self.calls, self.http, self.probe = calls, http, probe

    def download(self, candidate):
        url = media_url(candidate["provider"], candidate["media_url"])
        identity = {"request_id": self.request_id, "asset_id": candidate["id"],
                    "url": url, "byte_limit": 8 * 1024 * 1024}
        def send():
            receipt = self.http.binary_receipt(url)
            raw = receipt["body"]
            content_type = receipt["headers"].get("content-type", "").split(";")[0].strip().lower()
            extension = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}.get(content_type)
            if extension is None or not raw:
                raise ValueError("selected photo has unsupported/empty content")
            directory = self.root / "catalog" / self.request_id / digest(candidate["id"])
            directory.mkdir(parents=True, exist_ok=True)
            if not directory.resolve().is_relative_to(self.root):
                raise ValueError("photo storage escapes media root")
            file = directory / ("selected" + extension)
            with file.open("xb") as handle:
                handle.write(raw)
            dimensions = self.probe(file)
            asset = dict(candidate)
            asset.update({"path": str(file.relative_to(self.root)),
                          "sha256": hashlib.sha256(raw).hexdigest(),
                          "width": dimensions["width"], "height": dimensions["height"],
                          "download_receipt": {k: v for k, v in receipt.items() if k != "body"}})
            validate_asset(self.root, asset)
            return asset
        asset = self.calls.run("download:" + candidate["id"], "download", identity, send)
        validate_asset(self.root, asset)
        return asset
