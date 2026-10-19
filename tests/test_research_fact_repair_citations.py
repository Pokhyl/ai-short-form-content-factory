"""Fact repairs must not silently replace grounded photo citations."""
from copy import deepcopy
import hashlib
import unittest

from factory_v3.gemini import obj, array, string, BOOL
from material_first.source_spans import source_spans
from material_first.research_review import (
    preserve_validated_contexts_after_fact_repair, reviewed_brief,
)


class FactRepairContextRegression(unittest.TestCase):
    def test_fact_only_review_preserves_literal_image_citations_across_topics(self):
        for topic, things in (
            ("Bee pollination", ("meadow", "bee", "pollen")),
            ("Coral reef", ("reef", "coral", "fish")),
        ):
            with self.subTest(topic=topic):
                source_text = (
                    f"Researchers observed a {things[1]} near a {things[0]}. "
                    f"The report describes {things[2]} and the documented habitat. "
                    "The scene is a real, photographable environment. "
                )
                sources = [{
                    "id": "source-1", "url": "https://example.org/published-research",
                    "text": source_text,
                    "sha256": hashlib.sha256(source_text.encode()).hexdigest(),
                }]
                spans = source_spans(sources)
                span_id = spans[0]["id"]
                facts = [
                    {"id": f"fact-{i}", "text": "unsupported claim" if i == 2 else
                     f"Documented observation {i}",
                     "support": [{"span_id": span_id}]}
                    for i in range(1, 4)
                ]
                roles = ("setting", "subject", "detail")
                contexts = {
                    role: {
                        "fact_ids": [f"fact-{i}"],
                        "support_span_ids": [span_id],
                        "source_mention": thing,
                        "english_photo_object": thing,
                    }
                    for i, (role, thing) in enumerate(zip(roles, things), start=1)
                }
                initial = {
                    "facts": facts,
                    "required_fact_ids": [f"fact-{i}" for i in range(1, 4)],
                    "photo_contexts": contexts,
                }
                item_schema = obj({
                    "id": string(), "text": string(),
                    "support": array(obj({"span_id": string([span_id])}), 1, 3),
                })
                context_schema = obj({
                    "fact_ids": array(string(), 1, 8),
                    "support_span_ids": array(string([span_id]), 1, 3),
                    "source_mention": string(), "english_photo_object": string(),
                })
                schema = obj({
                    "facts": array(item_schema, 3, 8),
                    "required_fact_ids": array(string(), 3, 3),
                    "photo_contexts": obj({role: context_schema for role in roles}),
                })

                class CachedProvider:
                    called = []

                    def generate(self, key, instruction, payload, expected_schema):
                        self.called.append(key)
                        if key == "material-brief-review:1":
                            return {"facts": {
                                f"fact-{i}": {
                                    "supported": i != 2,
                                    "reason": "unsupported source wording" if i == 2
                                    else "source-supported",
                                } for i in range(1, 4)
                            }}, {}
                        if key == "material-brief-repair:review:1":
                            revision = deepcopy(initial)
                            revision["facts"][1]["text"] = "Corrected sourced claim"
                            # An LLM may attempt to replace a grounded image
                            # mention while fixing a completely separate fact.
                            revision["photo_contexts"]["setting"][
                                "source_mention"] = "invented unsupported venue"
                            return revision, {}
                        if key == "material-brief-review:2":
                            return {"facts": {
                                f"fact-{i}": {"supported": True, "reason": "supported"}
                                for i in range(1, 4)
                            }}, {}
                        raise AssertionError("unplanned model call: " + key)

                provider = CachedProvider()
                saved = deepcopy(initial)
                result = reviewed_brief(
                    provider, {"topic": topic}, sources, spans, schema,
                    deepcopy(initial), check_photos=False,
                )
                self.assertEqual(result["facts"][1]["text"], "Corrected sourced claim")
                self.assertEqual(
                    result["photo_contexts"]["setting"]["source_mention"], things[0]
                )
                self.assertEqual(initial, saved)
                self.assertEqual(provider.called, [
                    "material-brief-review:1",
                    "material-brief-repair:review:1",
                    "material-brief-review:2",
                ])

    def test_cannot_preserve_a_context_if_fact_id_was_removed(self):
        previous = {
            "facts": [{"id": "f1"}, {"id": "f2"}],
            "photo_contexts": {"subject": {"fact_ids": ["f2"]}},
        }
        changed = {"facts": [{"id": "f1"}, {"id": "f3"}],
                   "photo_contexts": {"subject": {"fact_ids": ["f3"]}}}
        with self.assertRaisesRegex(ValueError, "fact identities"):
            preserve_validated_contexts_after_fact_repair(previous, changed)


if __name__ == "__main__":
    unittest.main()
