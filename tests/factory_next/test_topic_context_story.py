"""Factory Next-only contextual visuals for facts that cannot be photographed.

These are fixture tests; no Google, network, external database or paid sends.
"""
import hashlib
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

from factory_v3.preflight import digest
from material_first.engine import validate_story, MaterialUnavailable
from material_first.presentation import TOPIC_POLICY
from factory_next.preparation import PreparationStages


TOPICS=(
    ("DNA molecule",
     ("DNA strands form a double helix.", "DNA stores inherited information.",
      "DNA bases form complementary pairs.")),
    ("Black holes",
     ("A black hole has an event horizon.", "Gravity changes the trajectories of light.",
      "Orbiting hot matter can form an accretion disk.")),
    ("How tree leaves work",
     ("Leaves contain stomata.", "Water moves through the plant by transpiration.",
      "Leaf cells contain chloroplasts.")),
)


def fixture(topic, statements):
    corpus=" ".join(statements)
    source={"id":"source-1","url":"https://example.org/science",
            "text":corpus,"sha256":hashlib.sha256(corpus.encode()).hexdigest()}
    facts=[{"id":f"f{i+1}","text":fact,
            "support":[{"source_id":"source-1","quote":fact}]}
           for i,fact in enumerate(statements)]
    return {"request":{"topic":topic,"language":"en","seconds":45,
                       "presentation_policy":TOPIC_POLICY,
                       "required_fact_ids":["f1","f2","f3"]},
            "evidence":{"sources":[source],"facts":facts}}


def photos():
    result=[]
    for i,support in enumerate((("f1",),("f1","f3"),("f3",)),1):
        result.append({
            "id":f"source-visual-{i}","sha256":f"{i:064x}",
            "source_interval":{"type":"still"},"capacity_ms":60000,
            "visible_description":f"Source-backed diagram {i} of requested topic",
            "supported_fact_ids":list(support),
            "visual_kind":"scientific_illustration",
            "inspection":{"topic_relation":{"kind":"direct_subject"},
                          "visible_fact_details":[{"fact_id":k} for k in support]}
        })
    return result


def draft_for(statements):
    return {"beats":[
        {"material_id":f"source-visual-{i}",
         "narration":statements[i-1],"fact_ids":[f"f{i}"]}
        for i in range(1,4)]}


class SourceGroundedContextTests(unittest.TestCase):
    def test_three_unrelated_science_topics_can_explain_nonvisible_functions(self):
        for topic,facts in TOPICS:
            with self.subTest(topic=topic):
                source=fixture(topic,facts)
                media=photos()
                draft=draft_for(facts)
                with self.assertRaisesRegex(MaterialUnavailable,"unrelated"):
                    validate_story(source["request"],source["evidence"],media,draft)
                scenes=validate_story(source["request"],source["evidence"],media,
                                       draft,allow_topic_context=True)
                self.assertEqual([s["visual_relation"] for s in scenes],
                    ["direct_fact_visual","topic_context","direct_fact_visual"])
                self.assertEqual(
                    [s["contract"]["contextual_not_direct_proof"] for s in scenes],
                    [False,True,False])
                self.assertEqual({f for scene in scenes
                                  for f in scene["evidence_ids"]},{"f1","f2","f3"})
                self.assertEqual(len({scene["material_id"] for scene in scenes}),3)
                self.assertTrue(all(scene["capacity_ms"]==60000 for scene in scenes))

    def test_contextual_image_must_support_at_least_one_required_topic_fact(self):
        source=fixture(*TOPICS[0]);media=photos()
        source["evidence"]["facts"].append({
            "id":"f4","text":"Some other unrelated visible fact.",
            "support":[{"source_id":"source-1",
                        "quote":TOPICS[0][1][0]}]})
        media[1]["supported_fact_ids"]=["f4"]
        with self.assertRaisesRegex(MaterialUnavailable,"not inspected for the actual topic"):
            validate_story(source["request"],source["evidence"],media,
                           draft_for(TOPICS[0][1]),allow_topic_context=True)

    def test_other_policies_and_nonboolean_opt_in_cannot_use_context_mode(self):
        source=fixture(*TOPICS[0])
        for unauthorized in ("yes",1,None):
            with self.subTest(value=unauthorized):
                with self.assertRaisesRegex(ValueError,"explicit topic context policy"):
                    validate_story(source["request"],source["evidence"],
                                   photos(),draft_for(TOPICS[0][1]),
                                   allow_topic_context=unauthorized)
        source["request"]["presentation_policy"]="whole-photo-exact-v2"
        with self.assertRaisesRegex(ValueError,"topic policy"):
            validate_story(source["request"],source["evidence"],photos(),
                           draft_for(TOPICS[0][1]),allow_topic_context=True)

    def test_studio_story_invokes_independent_review_with_explicit_context_label(self):
        source=fixture(*TOPICS[0])
        materials=photos()
        draft=draft_for(TOPICS[0][1])
        class Reviewer:
            reviewed=None
            def generate(self,key,instruction,context,schema):
                assert key=="next-story"
                assert "not direct visual evidence" in instruction
                return deepcopy(draft),{"receipt_id":"offline-source-fixture"}
            def review_script(self,request):
                self.reviewed=deepcopy(request)
                script=request["script"]
                return {
                    "receipt_id":"trusted-test-review", "model":"fixture-review",
                    "script_sha256":hashlib.sha256(script.encode()).hexdigest(),
                    "evidence_sha256":digest(request["evidence"]),
                    "language":"en", "language_match":True,
                    "visual_contracts_match":True,"no_unsupported_claims":True,
                    "topic_covered":True,
                    "topic_sha256":hashlib.sha256(request["topic"].encode()).hexdigest(),
                    "native_language_quality":True,
                    "factual_checks":[{
                        "scene_id":scene["id"],"fact_id":scene["evidence_ids"][0],
                        "narration_quote":scene["narration"],"supported":True}
                        for scene in request["scenes"]]}
        reviewer=Reviewer()
        operations=SimpleNamespace(gemini=reviewer,
                                   review_script=reviewer.review_script)
        result=PreparationStages("/unused",operations,lambda:None).story({
            "outputs":{"research":source,"materials":{"photos":materials}}})
        self.assertEqual(len(result["scenes"]),3)
        self.assertEqual(result["scenes"][1]["visual_relation"],"topic_context")
        self.assertEqual(reviewer.reviewed["scenes"][1]["contract"]
                         ["contextual_not_direct_proof"],True)
        self.assertTrue(result["review"]["no_unsupported_claims"])
        self.assertTrue(result["review"]["visual_contracts_match"])


if __name__=="__main__":
    unittest.main()
