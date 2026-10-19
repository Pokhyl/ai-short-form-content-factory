"""Preserving previously literal source links is safe only for unchanged context identity."""
import unittest

from material_first.research_review import preserve_literal_context_on_fact_repair


class LiteralContextPreservationTests(unittest.TestCase):
    def setUp(self):
        self.spans = [
            {"id": "s1", "text": "The founders first worked in a workshop near the house."},
            {"id": "s2", "text": "The engineer built a prototype in the laboratory."},
        ]
        self.previously_valid = {
            "setting": {
                "subject": "historic workshop", "query": "historic workshop",
                "fact_ids": ["f1"], "source_mention": "workshop",
                "support_span_ids": ["s1"],
            },
        }
        self.changed = {
            "facts": [{"id": "f1", "text": "Edited factual statement"}],
            "photo_contexts": {
                "setting": {
                    "english_photo_object": "historic workshop",
                    "fact_ids": ["f1"], "source_mention": "childhood workshop",
                    "support_span_ids": ["s2"],
                }
            }
        }

    def test_recovers_only_saved_literal_reference(self):
        fixed = preserve_literal_context_on_fact_repair(
            self.changed, self.previously_valid, self.spans)
        row = fixed["photo_contexts"]["setting"]
        self.assertEqual(row["source_mention"], "workshop")
        self.assertEqual(row["support_span_ids"], ["s1"])
        self.assertEqual(fixed["facts"], self.changed["facts"])
        self.assertEqual(self.changed["photo_contexts"]["setting"]["source_mention"],
                         "childhood workshop")  # the input is not mutated

    def test_different_object_cannot_inherit_previous_reference(self):
        self.changed["photo_contexts"]["setting"]["english_photo_object"] = "radio telescope"
        fixed = preserve_literal_context_on_fact_repair(
            self.changed, self.previously_valid, self.spans)
        self.assertEqual(fixed, self.changed)

    def test_different_fact_binding_cannot_inherit_previous_reference(self):
        self.changed["photo_contexts"]["setting"]["fact_ids"] = ["f2"]
        fixed = preserve_literal_context_on_fact_repair(
            self.changed, self.previously_valid, self.spans)
        self.assertEqual(fixed, self.changed)

    def test_valid_new_citation_is_not_overwritten(self):
        row = self.changed["photo_contexts"]["setting"]
        row["source_mention"] = "laboratory"
        fixed = preserve_literal_context_on_fact_repair(
            self.changed, self.previously_valid, self.spans)
        self.assertEqual(fixed, self.changed)

    def test_invalid_old_citation_is_not_resurrected(self):
        self.previously_valid["setting"]["source_mention"] = "unmentioned building"
        fixed = preserve_literal_context_on_fact_repair(
            self.changed, self.previously_valid, self.spans)
        self.assertEqual(fixed, self.changed)

    def test_wrong_language_stays_rejected(self):
        row = self.changed["photo_contexts"]["setting"]
        row["english_photo_object"] = "историческая мастерская"
        self.previously_valid["setting"]["subject"] = "историческая мастерская"
        fixed = preserve_literal_context_on_fact_repair(
            self.changed, self.previously_valid, self.spans)
        self.assertEqual(fixed, self.changed)


if __name__ == "__main__":
    unittest.main()
