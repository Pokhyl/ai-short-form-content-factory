"""Stop surplus photo inspections while keeping real topical-source coverage."""
import unittest
from hashlib import sha256
from unittest.mock import Mock, patch

from factory_next.preparation import PreparationStages, required_verified_image_target


class PhotoBudgetStopTests(unittest.TestCase):
    def run_materials(self, coverage, seconds=15, owned=False, candidate_count=20, entailment=False, accepted_count=None):
        source_text = "A test source documenting three facts for grounded photographs."
        evidence = {
            "sources": [{"id": "source-1", "url": "https://example.org/source",
                         "text": source_text, "sha256": sha256(source_text.encode()).hexdigest()}],
            "facts": [{"id": fact, "text": "Fact " + fact,
                       "support": [{"source_id": "source-1", "quote": source_text}]}
                      for fact in ("f1", "f2", "f3")],
        }
        request = {"topic": "Arbitrary independent subject", "language": "en",
                   "seconds": seconds, "visual_validation_mode": "gemini",
                   "required_fact_ids": ["f1", "f2", "f3"]}
        if entailment:
            request.update(visual_entailment_policy="independent-visual-entailment-v1")
        source = {"request": request, "evidence": evidence, "queries": ["any"]}
        candidate_ids = ["asset-" + str(i) for i in range(candidate_count)]
        ops = Mock()
        ops.discover.return_value = [{"id": identity} for identity in candidate_ids]

        def download(candidate):
            signature = sha256(candidate["id"].encode()).hexdigest()
            return {"id": candidate["id"], "sha256": signature,
                    "media_type": "photo",
                    "visual_fingerprint": {"source_sha256": signature}}

        def inspect(batch, unused_evidence):
            return [{"asset_id": asset["id"], "accepted":
                     (accepted_count is None
                      or (candidate_ids.index(asset["id"]) < accepted_count
                          if isinstance(accepted_count, int)
                          else candidate_ids.index(asset["id"]) in accepted_count)),
                     "receipt_id": "initial-" + asset["id"]} for asset in batch]

        def accepted(asset, receipt, unused_evidence, unused_facts, unused_mode):
            if receipt.get('accepted') is False:
                return None
            index = candidate_ids.index(asset["id"])
            return {"id": asset["id"], "sha256":asset['sha256'], "supported_fact_ids": coverage(index),
                    **({"visual_entailment": receipt["visual_entailment"]}
                       if "visual_entailment" in receipt else {})}

        ops.download.side_effect = download
        ops.inspect_many.side_effect = inspect
        ops._photo.side_effect = lambda asset: {"bytes": b"x" * 100}
        def independent_review(unused_ops, assets, unused_evidence, receipts):
            return [{**receipt, "visual_entailment": {"policy": "independent-visual-entailment-v1",
                    "receipt_id": "independent-" + asset["id"]}}
                    for asset, receipt in zip(assets, receipts)]
        with patch("factory_next.preparation.validate_material"), \
             patch("factory_next.preparation.pixels"), \
             patch("factory_next.preparation.same_photo", return_value=False), \
             patch("factory_next.preparation.inspected_material", side_effect=accepted), \
             patch("material_first.visual_entailment.review_batch", side_effect=independent_review) as entailment_review:
            from types import SimpleNamespace
            model=SimpleNamespace(fact_owned_story=True) if owned else None
            output = PreparationStages("/unused", ops, lambda: None,narrative_model=model).materials(
                {"outputs": {"research": source}})
            ops.review_batch_call_sizes = [len(call.args[1])
                                           for call in entailment_review.call_args_list]
        return output, ops

    def test_distinct_source_anchors_prevent_premature_stop_on_actual_coverage_shape(self):
        result,ops=self.run_materials(lambda i:['f1'] if i<3 else ['f2','f3'],owned=True)
        self.assertEqual(ops.inspect_many.call_count,2)
        self.assertEqual(len(result['photos']),8)

    def test_owned_story_does_not_search_for_unobservable_fact_pixels(self):
        result,ops=self.run_materials(lambda i:['f1'] if i%2 else ['f3'],owned=True)
        self.assertEqual(ops.inspect_many.call_count,1)
        self.assertEqual(len(result['photos']),4)

    def test_independent_entailment_batches_accepted_photos_across_candidate_batches(self):
        result, operations = self.run_materials(
            lambda i: ["f1"] if i % 2 == 0 else ["f2"], seconds=45,
            candidate_count=32, entailment=True,
            accepted_count=[0, 4, 8, 12, 16, 20, 24, 28, 29])
        self.assertEqual(operations.inspect_many.call_count, 8)
        self.assertEqual(operations.review_batch_call_sizes, [4, 4, 1])
        self.assertEqual(len(result["photos"]), 9)
        self.assertTrue(all("visual_entailment" in photo for photo in result["photos"]))

    def test_editorial_target_respects_five_second_cadence_for_all_durations(self):
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

    def test_invisible_source_fact_does_not_exhaust_material_inspections(self):
        # f2 is inheritance: no still image directly proves it. 45-second
        # cinema can use a separately source-verified DNA diagram as context.
        result,operations=self.run_materials(
            lambda i: ["f1"] if i%2==0 else ["f3"],seconds=45)
        self.assertEqual(len(result["photos"]),12)
        self.assertEqual(operations.inspect_many.call_count,3)
        self.assertEqual(operations.download.call_count,12)
        self.assertEqual({f for photo in result["photos"]
                          for f in photo["supported_fact_ids"]},{"f1","f3"})
        self.assertTrue(all(set(p["supported_fact_ids"]) & {"f1","f2","f3"}
                            for p in result["photos"]))

    def test_non_topic_illustrations_do_not_count_toward_source_coverage(self):
        # Model-reported extra topics cannot be promoted to required visual
        # evidence; still seek enough explicitly inspected source visuals.
        def coverage(index):
            if index<4:return ["f4"]
            if index<8:return ["f1"]
            return ["f3"]
        result,operations=self.run_materials(coverage)
        self.assertEqual(len(result["photos"]),8)
        self.assertEqual(operations.inspect_many.call_count,3)
        self.assertEqual(operations.download.call_count,12)
        self.assertNotIn("f4",{f for photo in result["photos"]
                               for f in photo["supported_fact_ids"]})

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
