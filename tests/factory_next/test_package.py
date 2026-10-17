"""Prevent silently omitting factory_next from the deployable app image."""
from pathlib import Path
import unittest


class PackageContract(unittest.TestCase):
    def test_runtime_image_copies_replacement_core(self):
        project=Path(__file__).resolve().parents[2]
        docker=(project/'factory_v3'/'Dockerfile').read_text()
        self.assertIn('COPY factory_next /app/factory_next',docker)
        self.assertIn('COPY material_first /app/material_first',docker)
        self.assertIn('COPY factory_v3 /app/factory_v3',docker)
        self.assertTrue((project/'factory_next'/'adapters.py').exists())
        self.assertTrue((project/'factory_next'/'duration.py').exists())


if __name__=='__main__':unittest.main()
