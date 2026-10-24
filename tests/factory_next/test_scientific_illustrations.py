"""Factory Next can truthfully use Wikimedia science diagrams; legacy photo gate stays strict.

All fixtures are offline. No network, Gemini calls, provider claims, or database writes.
"""
from copy import deepcopy
from hashlib import sha256
from unittest.mock import Mock
import unittest

from factory_v3.grounding import validate_evidence
from material_first.engine import inspected_material
from material_first.operations import Operations
from material_first.presentation import TOPIC_POLICY
from material_first.scientific_illustrations import (
    is_scientific_illustration, trusted_commons_illustration_source)


def evidence():
    text = "DNA contains two strands forming a double helix with complementary base pairs."
    return {
        "sources": [{"id": "source-1", "url": "https://example.org/biology",
                     "text": text, "sha256": sha256(text.encode()).hexdigest()}],
        "facts": [{"id": "f1", "text": "DNA has paired strands in a double helix.",
                   "support": [{"source_id": "source-1", "quote": text}]}],
    }


def diagram_asset():
    return {
        "id": "wikimedia:123", "provider": "wikimedia", "media_type": "photo",
        "sha256": "a" * 64, "source_url": "https://commons.wikimedia.org/wiki/File:DNA_schematic.png",
        "license": "CC BY-SA", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "author": "controlled fixture",
        "description": "Diagram of a DNA double helix",
    }


def response():
    return {
        "accepted": True, "is_real_material": True, "medium": "illustration",
        "illustration_type": "scientific_diagram",
        "topic_relation": {
            "kind": "direct_subject", "visible_subject": "DNA double helix",
            "connection": "The labeled diagram identifies two DNA strands and paired bases",
        },
        "subject_fully_visible": True,
        "visible_description": "A labeled schematic of the DNA double helix, not a photomicrograph",
        "visible_fact_details": [{"fact_id": "f1", "detail": "Two strands connected by base pairs"}],
    }


class ScientificIllustrationTests(unittest.TestCase):
    def setup_operations(self):
        ops = Operations("/isolated", None, Mock(model="gemini-3.1-flash-lite"), None, None)
        return ops

    def record(self, operations, asset=None, model_response=None):
        asset = diagram_asset() if asset is None else asset
        response_data = response() if model_response is None else model_response
        receipt = operations._inspection_receipt(
            asset, evidence(), response_data, {"receipt_id": "trusted-model-receipt"})
        return receipt

    def test_scientific_diagram_is_labeled_and_verified_against_grounded_fact(self):
        operations = self.setup_operations()
        operations.allow_source_illustrations = True
        asset = diagram_asset()
        receipt = self.record(operations)
        self.assertEqual(receipt["inspection_protocol"], "source-illustration-v1")
        self.assertTrue(receipt["accepted"])
        facts = validate_evidence(evidence())
        material = inspected_material(asset, receipt, evidence(), facts, "gemini_scientific")
        self.assertEqual(material["visual_kind"], "scientific_illustration")
        self.assertEqual(material["supported_fact_ids"], ["f1"])
        self.assertIn("not a photomicrograph", material["visible_description"])
        self.assertTrue(is_scientific_illustration(asset, receipt))

    def test_topical_landscape_painting_is_not_a_scientific_illustration(self):
        operations = self.setup_operations()
        operations.allow_source_illustrations = True
        asset = diagram_asset()
        asset['description'] = 'File:River through an Autumn Forest-William Mason Brown.jpg'
        model_response = {
            **response(),
            'illustration_type': 'artwork',
            'visible_description': 'A painting showing a river through an autumn forest.',
            'topic_relation': {
                'kind': 'direct_subject',
                'visible_subject': 'Autumn forest landscape',
                'connection': 'The painting depicts autumn foliage.',
            },
        }
        receipt = self.record(operations, asset=asset, model_response=model_response)
        self.assertEqual(receipt['inspection_protocol'], 'topic-specific-v1')
        self.assertFalse(receipt['accepted'])
        self.assertIsNone(inspected_material(
            asset, receipt, evidence(), validate_evidence(evidence()), 'gemini_scientific'))

    def test_legacy_photo_only_rejects_same_diagram(self):
        operations = self.setup_operations()
        asset = diagram_asset()
        self.assertFalse(self.record(operations)["accepted"])
        operations.allow_source_illustrations = True
        receipt = self.record(operations)
        self.assertIsNone(inspected_material(
            asset, receipt, evidence(), validate_evidence(evidence()), "gemini"))

    def test_fake_or_unlicensed_sources_do_not_pass_diagram_gate(self):
        operations = self.setup_operations()
        operations.allow_source_illustrations = True
        for change in (
            {"provider": "pexels", "id": "pexels:123"},
            {"source_url": "https://example.org/fake-diagram.png"},
            {"source_url": "http://commons.wikimedia.org/wiki/File:DNA.png"},
            {"license": "All rights reserved"},
            {"license_url": "https://example.org/claimed-license"},
        ):
            with self.subTest(change=change):
                asset = {**diagram_asset(), **change}
                self.assertFalse(trusted_commons_illustration_source(asset))
                self.assertFalse(self.record(operations, asset=asset)["accepted"])

    def test_model_rejections_and_decorative_art_remain_rejected(self):
        operations = self.setup_operations()
        operations.allow_source_illustrations = True
        for change in (
            {"accepted": False},
            {"subject_fully_visible": False},
            {"is_real_material": False},
            {"topic_relation": {"kind": "unrelated",
                                "visible_subject": "decorative helix",
                                "connection": "No connection to the documented molecule"}},
            {"visible_fact_details": []},
            {"medium": "synthetic"},
        ):
            with self.subTest(change=change):
                model_response = {**response(), **change}
                receipt = self.record(operations, model_response=model_response)
                self.assertFalse(receipt["accepted"])
                self.assertIsNone(inspected_material(
                    diagram_asset(), receipt, evidence(), validate_evidence(evidence()),
                    "gemini_scientific"))

    def test_factory_next_material_stage_accepts_distinct_verified_diagrams(self):
        from unittest.mock import patch
        from factory_next.preparation import PreparationStages

        ops = self.setup_operations()
        originals = []
        for i in range(8):
            original = diagram_asset()
            original.update(id=f"wikimedia:{i + 100}", sha256=f"{i + 1:064x}")
            original["visual_fingerprint"] = {"source_sha256": original["sha256"]}
            originals.append(original)
        ops.discover = Mock(return_value=[{"id":a["id"]} for a in originals])
        identities = {a["id"]:a for a in originals}
        ops.download = Mock(side_effect=lambda candidate: deepcopy(identities[candidate["id"]]))
        ops.inspect_many = Mock(side_effect=lambda batch, source_evidence: [
            ops._inspection_receipt(item, source_evidence, response(),
                                    {"receipt_id": "reviewed-" + item["id"]})
            for item in batch])
        request = {"topic":"The DNA molecule", "language":"en", "seconds":45,
                   "visual_validation_mode":"gemini", "required_fact_ids":["f1"],
                   "presentation_policy":TOPIC_POLICY}
        with patch("factory_next.preparation.validate_material"), \
             patch("factory_next.preparation.pixels"), \
             patch("factory_next.preparation.same_photo",return_value=False):
            output=PreparationStages("/isolated",ops,lambda:None).materials({
                "outputs":{"research":{"request":request,"evidence":evidence(),
                                       "queries":[{"query":"DNA double helix"}]}}})
        self.assertTrue(ops.allow_source_illustrations)
        self.assertEqual(ops.topic, "The DNA molecule")
        self.assertEqual(len(output["photos"]), 8)
        self.assertEqual(len(output["assets"]), 8)
        self.assertTrue(all(photo["visual_kind"]=="scientific_illustration"
                            for photo in output["photos"]))

    def test_opt_in_discovery_keeps_wikimedia_diagram_but_not_stock_art(self):
        from material_first.operations import Operations
        search = Mock()
        commons = {**diagram_asset(), "width": 1200, "height": 1600}
        stock = {"id": "pexels:bad", "provider": "pexels", "width": 1200, "height": 1600,
                 "description": "Synthetic 3D rendering of DNA", "source_metadata": {}}
        search.search.side_effect = lambda provider, query, orientation: {
            "candidates": [commons] if provider == "wikimedia" else
                          [stock] if provider == "pexels" else [],
        }
        req = {"topic": "DNA molecule", "seconds": 45,
               "presentation_policy": TOPIC_POLICY}
        targets = [{"id": "v0", "query": "DNA", "fact_ids": ["f1"],
                    "must_show": "DNA", "must_not_show": "unrelated images"}]
        old = Operations("/isolated", None, Mock(), search, None)
        self.assertEqual(old.discover(req, targets), [])
        new = Operations("/isolated", None, Mock(), search, None)
        new.allow_source_illustrations = True
        found = new.discover(req, targets)
        self.assertEqual([a["id"] for a in found], ["wikimedia:123"])
        self.assertEqual(found[0]["visual_qualification_protocol"], "qualified-target-v1")


if __name__ == "__main__":
    unittest.main()
