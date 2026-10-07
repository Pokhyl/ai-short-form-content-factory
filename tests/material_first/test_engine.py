"""Controlled semantics; these fixtures never constitute actual visual acceptance."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from factory_v3.preflight import digest
from material_first.engine import Producer, MaterialUnavailable, verify


class Operations:
    def __init__(self, root, kinds):
        self.events = []
        self.root = root
        text = "First source fact. Second source fact. Third source fact."
        self.evidence = {"sources": [{"id": "source", "url": "https://example.invalid/research",
            "text": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}],
            "facts": [{"id": "f" + str(i), "text": sentence,
                       "support": [{"source_id": "source", "quote": sentence}]}
                      for i, sentence in enumerate(text.split(". "))]}
        self.assets = []
        self.reject = set()
        self.draft = None
        self.support = {}
        for i, kind in enumerate(kinds):
            file = root / (str(i) + (".jpg" if kind == "photo" else ".mp4"))
            file.write_bytes(("controlled material " + str(i)).encode())
            asset = {"id": "a" + str(i), "path": file.name, "media_type": kind,
                "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
                "source_url": "https://example.invalid/source", "author": "fixture",
                "framing": "original-whole", "license": "CC0", "license_url": "https://example.invalid/license"}
            if kind == "video":
                asset["duration_ms"] = 60000
            self.assets.append(asset)
            self.support[asset["id"]] = ["f" + str(i)]

    def probe(self, path):
        return {"width": 1080, "height": 1920,
                "duration_ms": 60000 if path.suffix == ".mp4" else None}

    def research(self, request):
        self.events.append("research")
        return {"evidence": copy.deepcopy(self.evidence),
                "required_fact_ids": ["f0", "f1", "f2"], "queries": ["controlled topic"]}

    def discover(self, request, queries):
        self.events.append("discover")
        return copy.deepcopy(self.assets)

    def download(self, candidate):
        self.events.append("download:" + candidate["id"])
        return candidate

    def inspect(self, asset, evidence):
        self.events.append("inspect:" + asset["id"])
        return {"asset_id": asset["id"], "asset_sha256": asset["sha256"],
            "evidence_sha256": digest(evidence), "model": "controlled-fixture", "receipt_id": asset["id"],
            "accepted": asset["id"] not in self.reject, "is_real_material": True,
            "visible_description": "Controlled observation " + asset["id"],
            "supported_fact_ids": self.support[asset["id"]],
            "source_start_ms": 0, "source_end_ms": 60000}

    def compose(self, request):
        self.events.append("compose")
        if self.draft is not None:
            return self.draft
        return {"beats": [{"material_id": m["id"], "narration": "Fact " + m["id"],
                           "fact_ids": m["supported_fact_ids"]} for m in request["materials"]]}

    def review_script(self, request):
        self.events.append("review")
        return {"receipt_id": "controlled-script", "model": "controlled-fixture",
            "script_sha256": hashlib.sha256(request["script"].encode()).hexdigest(),
            "evidence_sha256": digest(request["evidence"]), "language": request["language"],
            "language_match": True, "visual_contracts_match": True, "no_unsupported_claims": True,
            "topic_covered": True, "topic_sha256": hashlib.sha256(request["topic"].encode()).hexdigest(),
            "factual_checks": [{"scene_id": s["id"], "fact_id": f,
                "narration_quote": s["narration"], "supported": True}
                for s in request["scenes"] for f in s["evidence_ids"]]}


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def run_prepare(self, operations, language="pl", seconds=15):
        return Producer(self.root, operations, probe=operations.probe).prepare(
            "original required topic", language, seconds)

    def test_photos_remain_first_class_without_five_scene_requirement(self):
        ops = Operations(self.root, ["photo", "photo", "photo"])
        result = self.run_prepare(ops)
        self.assertEqual(len(result["payload"]["scenes"]), 3)
        self.assertTrue(all(a["media_type"] == "photo" for a in result["payload"]["assets"]))
        self.assertGreater(ops.events.index("compose"), ops.events.index("inspect:a2"))

    def test_single_real_video_can_cover_minute_without_seventeen_shots(self):
        ops = Operations(self.root, ["video"])
        ops.support["a0"] = ["f0", "f1", "f2"]
        for language in ["pl", "en", "ru", "uk"]:
            result = self.run_prepare(ops, language, 60)
            self.assertEqual(len(result["payload"]["scenes"]), 1)
            self.assertEqual(result["payload"]["scenes"][0]["capacity_ms"], 60000)

    def test_mixed_photo_video_story_uses_only_observed_support(self):
        ops = Operations(self.root, ["photo", "video"])
        ops.support["a1"] = ["f1", "f2"]
        result = self.run_prepare(ops)
        self.assertEqual({a["media_type"] for a in result["payload"]["assets"]}, {"photo", "video"})

    def test_relevant_metadata_cannot_replace_actual_inspection(self):
        ops = Operations(self.root, ["photo", "photo", "photo"])
        ops.assets[2]["description"] = "original required topic perfectly relevant stock"
        ops.reject.add("a2")
        with self.assertRaises(MaterialUnavailable):
            self.run_prepare(ops)
        self.assertNotIn("compose", ops.events)

    def test_photo_can_illustrate_source_supported_motion_fact(self):
        ops = Operations(self.root, ["photo", "photo", "photo"])
        ops.evidence["facts"][0]["requires_motion"] = True
        result = self.run_prepare(ops)
        self.assertEqual(result["payload"]["scenes"][0]["source_interval"], None)

    def test_photos_can_cover_minute_without_artificial_hold_limit(self):
        ops = Operations(self.root, ["photo", "photo", "photo"])
        result = self.run_prepare(ops, seconds=60)
        self.assertEqual(len(result["payload"]["scenes"]), 3)

    def test_short_video_can_be_replaced_with_relevant_photo(self):
        ops = Operations(self.root, ["photo"])
        ops.support["a0"] = ["f0", "f1", "f2"]
        result = self.run_prepare(ops, seconds=60)
        self.assertEqual(result["payload"]["assets"][0]["media_type"], "photo")

    def test_composer_cannot_move_claim_to_wrong_picture_or_repeat_media(self):
        ops = Operations(self.root, ["photo", "photo", "photo"])
        for beats in [
            [{"material_id": "a0", "narration": "Wrong fact", "fact_ids": ["f1"]}],
            [{"material_id": "a0", "narration": "Fact", "fact_ids": ["f0"]}] * 2,
            [{"material_id": "invented", "narration": "Fact", "fact_ids": ["f0"]}],
        ]:
            ops.draft = {"beats": beats}
            with self.assertRaises(ValueError):
                self.run_prepare(ops)

    def test_changed_exact_bytes_fail_before_voice_even_if_plan_hash_is_recomputed(self):
        ops = Operations(self.root, ["photo", "photo", "photo"])
        result = self.run_prepare(ops)
        (self.root / ops.assets[0]["path"]).write_bytes(b"other material")
        result["sha256"] = digest(result["payload"])
        with self.assertRaisesRegex(ValueError, "bytes changed"):
            verify(self.root, result, ops.probe)

    def test_real_jpeg_nominal_duration_is_not_mistaken_for_animation(self):
        import json
        from unittest.mock import patch
        from types import SimpleNamespace
        from material_first.engine import probe_media
        raw = {"streams": [{"codec_type": "video", "width": 867, "height": 1300,
                           "duration": "0.040000", "nb_read_frames": "1"}],
               "format": {"format_name": "image2", "duration": "0.040000"}}
        with patch("material_first.engine.subprocess.run", return_value=SimpleNamespace(stdout=json.dumps(raw))):
            self.assertIsNone(probe_media("actual.jpg")["duration_ms"])
        raw["streams"][0]["nb_read_frames"] = "2"
        with patch("material_first.engine.subprocess.run", return_value=SimpleNamespace(stdout=json.dumps(raw))):
            self.assertEqual(probe_media("animated.png")["duration_ms"], 40)

    def test_collects_six_photos_instead_of_stopping_at_three(self):
        ops = Operations(self.root, ["photo"] * 8)
        for asset in ops.assets:
            ops.support[asset["id"]] = ["f0", "f1", "f2"]
        result = self.run_prepare(ops)
        self.assertEqual(len(result["payload"]["assets"]), 6)
        self.assertNotIn("inspect:a6", ops.events)

    def test_matching_reassigns_pictures_without_changing_claims_or_repeating_images(self):
        from material_first.engine import match_materials
        available = [{"id": "a", "supported_fact_ids": ["food", "pollination"]},
                     {"id": "b", "supported_fact_ids": ["food"]}]
        draft = {"beats": [{"material_id": "a", "fact_ids": ["food"], "narration": "Food"},
                           {"material_id": "b", "fact_ids": ["pollination"], "narration": "Pollination"}]}
        result = match_materials(available, draft)
        self.assertEqual([b["material_id"] for b in result["beats"]], ["b", "a"])
        self.assertEqual([b["narration"] for b in result["beats"]], ["Food", "Pollination"])

    def test_frozen_sample_must_redecode_to_the_exact_source_bytes(self):
        from unittest.mock import patch
        ops = Operations(self.root,['photo']*3)
        frozen = self.run_prepare(ops)
        asset = frozen['payload']['assets'][0]
        asset['visual_fingerprint'] = {'source_sha256':asset['sha256'],'rgb':'forged-sample'}
        frozen['sha256'] = digest(frozen['payload'])
        with patch('material_first.photo_identity.fingerprint',return_value={'source_sha256':asset['sha256'],'rgb':'actual-sample'}):
            with self.assertRaisesRegex(ValueError,'fingerprint differs'):
                verify(self.root,frozen,ops.probe)
