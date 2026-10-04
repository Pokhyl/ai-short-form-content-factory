import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from factory_v3.preflight import digest, freeze, verify_before_voice


class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.path = self.root / "controlled-test-image"
        self.path.write_bytes(b"controlled test bytes; not a production visual approval")
        self.asset = {"id": "controlled:test", "path": self.path.name,
                      "sha256": hashlib.sha256(self.path.read_bytes()).hexdigest(),
                      "source_url": "https://example.invalid/test", "author": "test",
                      "license": "CC0", "license_url": "https://example.invalid/license"}
        self.contract = {"visual_intent": "controlled test", "must_show": ["object"],
                         "must_not_show": ["conflict"]}
        self.scenes = [{"id": "s1", "narration": "Controlled narration.",
                        "evidence_ids": ["controlled-evidence"], "contract": self.contract}]
        self.review = {"receipt_id": "controlled-test", "model": "controlled-test",
                       "scene_id": "s1", "asset_id": self.asset["id"],
                       "asset_sha256": self.asset["sha256"],
                       "contract_sha256": digest(self.contract), "match_score": 90,
                       "must_show_visible": True, "must_not_show_clear": True, "intent_match": True,
                       "must_show_checks": [{"concept": "object", "visible": True}]}

    def tearDown(self):
        self.temp.cleanup()

    def make(self, reviews=None):
        return freeze(self.root, "pl", 15, "Controlled narration.", self.scenes,
                      [self.asset], [self.review] if reviews is None else reviews)

    def test_exact_media_and_contract_pass(self):
        frozen = self.make()
        self.assertEqual(verify_before_voice(self.root, frozen)["selection"], {"s1": "controlled:test"})

    def test_replacing_render_bytes_invalidates_freeze(self):
        frozen = self.make()
        self.path.write_bytes(b"other image")
        with self.assertRaisesRegex(ValueError, "bytes changed"):
            verify_before_voice(self.root, frozen)

    def test_old_contract_review_cannot_approve_new_detail(self):
        self.contract["must_show"].append("new detail")
        with self.assertRaisesRegex(ValueError, "TTS must not start"):
            self.make()

    def test_missing_concept_checks_or_low_score_block_voice(self):
        for change in ({"must_show_checks": []}, {"match_score": 54}, {"must_not_show_clear": False}):
            review = dict(self.review, **change)
            with self.assertRaises(ValueError):
                self.make([review])

    def test_frozen_script_tampering_rejected(self):
        frozen = self.make()
        frozen["payload"]["script"] = "Different narration."
        with self.assertRaisesRegex(ValueError, "modified"):
            verify_before_voice(self.root, frozen)

    def test_traversal_and_unknown_license_rejected(self):
        for change in ({"path": "../outside"}, {"license": "unknown"}):
            before = dict(self.asset)
            self.asset.update(change)
            with self.assertRaises(ValueError):
                self.make()
            self.asset = before

    def test_multiple_candidates_remain_verifiable_after_freeze(self):
        alternate_path = self.root / "alternative"
        alternate_path.write_bytes(b"another controlled test image")
        alternate = dict(self.asset, id="controlled:alternative", path=alternate_path.name,
                         sha256=hashlib.sha256(alternate_path.read_bytes()).hexdigest())
        review = dict(self.review, asset_id=alternate["id"], asset_sha256=alternate["sha256"],
                      receipt_id="controlled-alternative")
        frozen = freeze(self.root, "pl", 15, "Controlled narration.", self.scenes,
                        [self.asset, alternate], [self.review, review])
        self.assertEqual(verify_before_voice(self.root, frozen), frozen["payload"])

    def test_same_bytes_under_two_provider_ids_are_not_unique(self):
        alias = dict(self.asset, id="other-provider:same-image")
        scene = copy.deepcopy(self.scenes[0])
        scene["id"] = "s2"
        scene["narration"] = "Second narration."
        review = dict(self.review, asset_id=alias["id"], scene_id="s2", receipt_id="controlled-alias")
        with self.assertRaisesRegex(ValueError, "TTS must not start"):
            freeze(self.root, "pl", 15, "Controlled narration. Second narration.",
                   [self.scenes[0], scene], [self.asset, alias], [self.review, review])
