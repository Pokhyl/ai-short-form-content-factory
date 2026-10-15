import base64
import copy
import importlib.util
import itertools
import json
from pathlib import Path
import tempfile
import unittest

from material_first.photo_geometry import describe, decode, same_view
from material_first.photo_identity import fingerprint, same_photo


@unittest.skipUnless(importlib.util.find_spec('cv2'), 'runtime OpenCV dependency required')
class PhotoGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.fixture = json.loads((Path(__file__).parent / 'fixtures/actual-framed-photos-77e1.json').read_text())
        cls.samples = {}
        for identity, row in cls.fixture['samples'].items():
            path = cls.root / (identity.replace(':', '-') + '.jpg')
            path.write_bytes(base64.b64decode(row['derived_jpeg'], validate=True))
            cls.samples[identity] = describe(path)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_actual_framed_versions_match_in_both_orders(self):
        for a, b in self.fixture['duplicate_pairs']:
            self.assertTrue(same_view(self.samples[a], self.samples[b]), (a, b))
            self.assertTrue(same_view(self.samples[b], self.samples[a]), (b, a))

    def test_different_actual_observations_and_common_labels_remain_distinct(self):
        duplicates = {frozenset(pair) for pair in self.fixture['duplicate_pairs']}
        for a, b in itertools.combinations(self.samples, 2):
            if frozenset((a, b)) not in duplicates:
                self.assertFalse(same_view(self.samples[a], self.samples[b]), (a, b))
                self.assertFalse(same_view(self.samples[b], self.samples[a]), (b, a))

    def test_general_textures_reframe_without_merging_other_subjects(self):
        import cv2 as cv
        import numpy as np
        samples = []
        for seed in range(3):
            rng = np.random.default_rng(seed)
            image = cv.GaussianBlur(rng.integers(0, 256, (480, 640, 3), dtype=np.uint8), (5, 5), 0)
            for i in range(80):
                x, y = rng.integers(30, 450, 2)
                cv.circle(image, (int(x), int(y)), int(rng.integers(3, 15)),
                          tuple(int(n) for n in rng.integers(0, 256, 3)), -1)
            cv.putText(image, 'SAME LOGO', (10, 470), cv.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            path = self.root / f'pattern-{seed}.jpg'
            cv.imwrite(str(path), image)
            samples.append(describe(path))
            framed = cv.copyMakeBorder(image, 30, 80, 40, 40, cv.BORDER_CONSTANT, value=(0, 0, 0))
            cv.putText(framed, 'Different caption', (50, 550), cv.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            path2 = self.root / f'framed-{seed}.jpg'
            cv.imwrite(str(path2), cv.resize(framed, (540, 440)))
            self.assertTrue(same_view(samples[-1], describe(path2)))
        for a, b in itertools.combinations(samples, 2):
            self.assertFalse(same_view(a, b))

    def test_geometry_is_reproducible_and_bound_to_original_bytes(self):
        identity = next(iter(self.fixture['samples']))
        path = self.root / (identity.replace(':', '-') + '.jpg')
        import hashlib
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        a = fingerprint(path, sha, 768, 768)
        self.assertEqual(a, fingerprint(path, sha, 768, 768))
        self.assertEqual(a['source_sha256'], sha)
        self.assertTrue(same_photo(a, a))
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), sha)

    def test_corrupt_geometry_cannot_be_used(self):
        sample = next(iter(self.samples.values()))
        for field, value in (('algorithm', 'unknown'), ('points', [[float('nan'), 0]]),
                             ('descriptors', 'bad'), ('rgb256', 'bad')):
            changed = copy.deepcopy(sample)
            changed[field] = value
            with self.assertRaises(ValueError):
                decode(changed)
