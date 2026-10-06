"""Keep downloaded original photographs whole for inspection and rendering."""
from pathlib import Path
from copy import deepcopy
from factory_v3.preflight import validate_asset


class PortraitDownload:
    # Retained adapter name for compatibility; no crop is generated.
    def __init__(self, root, downloader):
        self.root, self.downloader = Path(root).resolve(), downloader
        self.calls = downloader.calls

    def download(self, candidate):
        original = self.downloader.download(candidate)
        validate_asset(self.root, original)
        asset = deepcopy(original)
        asset['framing'] = 'original-whole'
        return asset
