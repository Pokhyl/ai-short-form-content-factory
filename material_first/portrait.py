"""Review the actual full-screen portrait crop, rather than the wider original."""
from pathlib import Path
from copy import deepcopy
import hashlib
import subprocess
from factory_v3.preflight import asset_path, validate_asset


class PortraitDownload:
    def __init__(self, root, downloader):
        self.root, self.downloader = Path(root).resolve(), downloader
        self.calls = downloader.calls

    def download(self, candidate):
        original = self.downloader.download(candidate)
        validate_asset(self.root, original)
        source = asset_path(self.root, original['path'])
        crop = source.parent / 'portrait-9x16.jpg'
        # An existing crop must be reconciled, never silently overwritten.
        if crop.exists():
            raise ValueError('portrait crop already exists')
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(source),
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase:force_divisible_by=2,crop=1080:1920,setsar=1',
            '-frames:v', '1', '-threads', '1', '-q:v', '2', '-n', str(crop)],
            check=True, capture_output=True, timeout=20)
        asset = deepcopy(original)
        asset.update({'path': str(crop.relative_to(self.root)),
            'sha256': hashlib.sha256(crop.read_bytes()).hexdigest(), 'width':1080,'height':1920,
            'source_file_sha256': original['sha256'], 'source_file_path': original['path'],
            'framing': 'center-crop-9x16'})
        validate_asset(self.root, asset)
        return asset
