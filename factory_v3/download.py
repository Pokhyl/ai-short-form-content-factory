"""Download only bounded selected candidates, once, for exact-byte model review."""
import hashlib
import subprocess
from pathlib import Path
from uuid import UUID
from urllib.parse import urlsplit
from .preparation import ResourceUnavailable
from .preflight import digest, validate_asset
from .providers import media_url
from .worker_adapters import probe_photo


class PhotoDownload:
    def __init__(self, root, request_id, calls, http, probe=probe_photo):
        self.root = Path(root).resolve()
        self.request_id = str(UUID(str(request_id)))
        self.calls, self.http, self.probe = calls, http, probe
        self.rate_limited_hosts = {}
        # Only Factory Next opts in. Legacy photo download semantics unchanged.
        self.skip_invalid_local_media = False

    def download(self, candidate):
        url = media_url(candidate["provider"], candidate["media_url"])
        host = urlsplit(url).hostname
        if host in self.rate_limited_hosts:
            raise ResourceUnavailable(self.rate_limited_hosts[host])
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
            try:
                dimensions = self.probe(file)
                # A valid ffprobe header does NOT guarantee that FFmpeg can
                # decode its pixels. Run the exact fingerprint validation in
                # this same protected block and persist a definitive rejection
                # if the original source bytes are undecodable.
                visual_fingerprint = None
                if candidate.get("topic_protocol") == "topic-specific-v1":
                    from material_first.photo_identity import fingerprint
                    visual_fingerprint = fingerprint(
                        file, hashlib.sha256(raw).hexdigest(),
                        dimensions["width"], dimensions["height"])
            except (subprocess.CalledProcessError, ValueError):
                if not self.skip_invalid_local_media:
                    raise
                # This is a definitive LOCAL image-decoding failure after a
                # successful, durably receipted external fetch. Return a
                # JSON-safe refusal result so the ledger finishes the call
                # rather than recording an ambiguous unknown provider send.
                # No second HTTP request is authorized on replay.
                return {"local_image_rejected": True,
                        "asset_id": candidate["id"],
                        "reason": "UNDECODABLE_DOWNLOADED_IMAGE",
                        "sha256": hashlib.sha256(raw).hexdigest()}
            asset = dict(candidate)
            asset.update({"path": str(file.relative_to(self.root)),
                          "sha256": hashlib.sha256(raw).hexdigest(),
                          "width": dimensions["width"], "height": dimensions["height"],
                          "download_receipt": {k: v for k, v in receipt.items() if k != "body"}})
            if visual_fingerprint is not None:
                asset['visual_fingerprint'] = visual_fingerprint
            validate_asset(self.root, asset)
            return asset
        try:
            asset = self.calls.run("download:" + candidate["id"], "download", identity, send, allow_unavailable=True)
        except ResourceUnavailable as error:
            if error.receipt.get("status") == 429:
                self.rate_limited_hosts[host] = error.receipt
            raise
        if (self.skip_invalid_local_media and isinstance(asset, dict)
                and asset.get("local_image_rejected") is True
                and asset.get("asset_id") == candidate["id"]):
            # The saved ledger response is now safely reusable without any
            # re-download, and the caller can inspect other candidates.
            raise ResourceUnavailable({"reason": "UNDECODABLE_DOWNLOADED_IMAGE",
                                       "asset_id": candidate["id"]})
        validate_asset(self.root, asset)
        return asset
