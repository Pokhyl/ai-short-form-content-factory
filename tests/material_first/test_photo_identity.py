import base64
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from material_first.photo_identity import fingerprint, pixels, same_photo


class PhotoIdentityTests(unittest.TestCase):
    def setUp(self):
        self.samples = json.loads((Path(__file__).parent / 'fixtures/crab-distinct-observations.json').read_text())['samples']
        for sample in self.samples:
            sample['algorithm'] = 'rgb32-v1'
            sample['source_sha256'] = sample['sha256']

    def test_actual_hubble_and_webb_observations_are_distinct(self):
        self.assertFalse(same_photo(*self.samples))

    def test_resized_reencoded_copy_with_small_quantization_changes_is_duplicate(self):
        original = self.samples[0]
        variant = copy.deepcopy(original)
        variant.update(width=960, height=960, source_sha256='different-encoding-sha')
        variant['rgb'] = base64.b64encode(bytes(min(255, max(0, v+(1 if i%2 else -1)))
            for i,v in enumerate(pixels(original)))).decode()
        self.assertTrue(same_photo(original, variant))

    def test_similar_blank_skies_are_not_fuzzy_duplicates(self):
        a = dict(self.samples[0], rgb=base64.b64encode(bytes([5]*3072)).decode())
        b = dict(a, rgb=base64.b64encode(bytes([6]*3072)).decode())
        self.assertFalse(same_photo(a,b))
        self.assertTrue(same_photo(a,a))

    def test_corrupt_or_unknown_samples_reject(self):
        for change in ({'rgb':'bad'}, {'algorithm':'other'}, {'width':0}):
            with self.assertRaises(ValueError):
                pixels(dict(self.samples[0], **change))

    def test_decode_bound_to_source_without_modifying_file(self):
        raw = pixels(self.samples[0])
        with patch('material_first.photo_identity.subprocess.check_output', return_value=raw) as decode:
            result=fingerprint('/source.jpg','source-sha',1920,1920)
        self.assertEqual(result['source_sha256'],'source-sha')
        self.assertEqual(pixels(result),raw)
        self.assertEqual(decode.call_args.kwargs['timeout'],20)
