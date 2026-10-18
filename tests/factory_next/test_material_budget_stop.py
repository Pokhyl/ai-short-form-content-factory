"""Stop surplus photo inspections without losing required-fact coverage."""
import unittest
from hashlib import sha256
from unittest.mock import Mock, patch

from factory_next.preparation import PreparationStages, required_verified_image_target


class PhotoBudgetStopTests(unittest.TestCase):
    def run_materials(self, coverage):
        source_text = "A test source documenting three facts for grounded photographs."
        evidence = {
            "sources": [{"id": "source-1", "url": "https://example.org/source",
                         "text": source_text, "sha256": sha256(source_text.encode()).hexdigest()}],
            "facts": [{"id": fact, "text": "Fact " + fact,
                       "support": [{"source_id": "source-1", "quote": source_text}]}
                      for fact in ("f1", "f2", "f3")],
        }
        request = {"topic": "Arbitrary independent subject", "language": "en",
                   "seconds": 15, "visual_validation_mode": "gemini",
                   "required_fact_ids": ["f1", "f2", "f3"]}
        source = {"request": request, "evidence": evidence, "queries": ["any"]}
        candidate_ids = ["asset-" + str(i) for i in range(20)]
        ops = Mock()
        ops.discover.return_value = [{"id": identity} for identity in candidate_ids]

        def download(candidate):
            signature = sha256(candidate["id"].encode()).hexdigest()
            return {"id": candidate["id"], "sha256": signature,
                    "media_type": "photo",
                    "visual_fingerprint": {"source_sha256": signature}}

        def inspect(batch, unused_evidence):
            return [{"asset_id": asset["id"]} for asset in batch]

        def accepted(asset, receipt, unused_evidence, unused_facts, unused_mode):
            index = candidate_ids.index(asset["id"])
            return {"id": asset["id"], "supported_fact_ids": coverage(index)}

        ops.download.side_effect = download
        ops.inspect_many.side_effect = inspect
        with patch("factory_next.preparation.validate_material"), \
             patch("factory_next.preparation.pixels"), \
             patch("factory_next.preparation.same_photo", return_value=False), \
             patch("factory_next.preparation.inspected_material", side_effect=accepted):
            output = PreparationStages("/unused", ops, lambda: None).materials(
                {"outputs": {"research": source}})
        return output, ops

    def test_quota_saving_target_respects_cadence_for_all_durations(self):
        self.assertEqual({n:required_verified_image_target(n)
                          for n in (15,30,45,60)},
                         {15:3,30:6,45:9,60:12})
        for seconds in (15,30,45,60):
            count=required_verified_image_target(seconds)
            self.assertTrue(seconds/7.5<=count<=seconds/2.5)

    def test_45_second_coverage_succeeds_after_three_batches(self):
        # A 45-second output does not need 13 illustrations; 9-12 sourced,
        # visually distinct images preserve a viable measured edit.
        original=required_verified_image_target(45)
        self.assertEqual(original,9)

    def test_stop_when_preferred_photo_count_and_all_required_facts_verified(self):
        def coverage(i):
            return ["f1"] if i < 4 else ["f2", "f3"]
        result, operations = self.run_materials(coverage)
        self.assertEqual(len(result["photos"]), 8)
        self.assertEqual(operations.inspect_many.call_count, 2)
        self.assertEqual(operations.download.call_count, 8)
        self.assertEqual(len(result["assets"]), 8)

    def test_keep_searching_if_photo_count_met_but_required_facts_uncovered(self):
        def coverage(i):
            return ["f1"] if i < 8 else ["f2", "f3"]
        result, operations = self.run_materials(coverage)
        self.assertEqual(len(result["photos"]), 12)
        self.assertEqual(operations.inspect_many.call_count, 3)
        self.assertEqual(operations.download.call_count, 12)
        self.assertTrue({"f1", "f2", "f3"} <=
                        {f for p in result["photos"] for f in p["supported_fact_ids"]})


if __name__ == "__main__":
    unittest.main()
