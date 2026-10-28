"""Measured overlong natural speech must never be shortened by deleting verbs.

The original stage was observed to produce 135 Ukrainian words and 69.288
seconds for a requested 60 seconds. A model-proposed omission plan deleted
verbs, leaving fragments. Public voice revision must instead request complete
sentences and retain independent fact/native-language review before TTS.
"""
import unittest
from types import SimpleNamespace
from copy import deepcopy
from unittest.mock import patch

from factory_next.preparation import PreparationStages
from factory_next.duration import revision_length_window, revision_length_fits
from factory_next.voice_length_repair import sentence_contract,assemble_sentence_repair


def sentences_for(schema):
    rows={}
    k=0
    for beat, spec in schema["properties"].items():
        rows[beat]={}
        for field in spec["required"]:
            k+=1
            # 11 distinct complete sentences of 11 words, approximately
            # 70 characters each, with no externally asserted facts.
            rows[beat][field]=(
                f"Архів також описує цей епізод для читача через давні офіційні записи{k}.")
    return rows


class FakeModel:
    def __init__(self, invalid=False):
        self.calls=object()
        self.invalid=invalid
        self.keys=[]
        self.reviews=[]
        self.prompts=[]
    def generate(self,key,instruction,context,schema, **kwargs):
        if kwargs: assert kwargs == {'max_tokens':16384,'thinking_level':'medium'}
        self.keys.append(key)
        self.prompts.append(instruction)
        draft=sentences_for(schema)
        if self.invalid:
            draft={"remove_ids":["old-dangerous-word"]}  # never accepted
        return draft,{"cached":True}
    def review_script(self,context):
        self.reviews.append(deepcopy(context))
        return {"native_language_quality":True}


class CoherentOverlongTests(unittest.TestCase):
    def make_context(self,topic):
        # Match actual UK60 overall word/character evidence without baking
        # a named person into the runtime.
        original=("слово "*135).strip().ljust(959,".")
        beats=[{"id":f"b{i}","material_id":f"p{i}",
                "evidence_ids":[f"f{i}"],"narration":"Первинний документ розповідає факти."}
               for i in (1,2,3)]
        return {"request":{"topic":topic,"language":"uk","seconds":60},
                "_voice_correction_round":2,
                "outputs":{"research":{
                    "request":{"topic":topic,"language":"uk","seconds":60},
                    "evidence":{"facts":[{"id":f"f{i}"} for i in (1,2,3)]}},
                    "materials":{"photos":[{"id":f"p{i}"} for i in (1,2,3)]},
                    "story":{"scenes":beats,"script":original}}}

    def test_overlong_requests_whole_sentences_and_independent_review(self):
        for topic in ("зв'язок бджіл із квітами","виникнення коралових рифів"):
            with self.subTest(topic=topic):
                context=self.make_context(topic)
                model=FakeModel()
                stage=PreparationStages("/tmp",SimpleNamespace(gemini=model),lambda:None)
                def valid_story(request,evidence,photos,draft):
                    return [{"id":f"b{i}","material_id":row["material_id"],
                             "evidence_ids":list(row["fact_ids"]),
                             "narration":row["narration"]}
                            for i,row in enumerate(draft["beats"],1)]
                with patch("factory_next.preparation.validated_next_story",side_effect=valid_story), \
                     patch("factory_next.preparation.validate_native_surface"), \
                     patch("factory_next.preparation.validate_script_review") as reviewer, \
                     patch("factory_next.preparation.compact_materials",return_value=[]), \
                     patch("factory_next.preparation.extractive_omission_candidates",
                           side_effect=AssertionError("word deletion must not execute")):
                    revised=stage.revise_story(context,69288)
                self.assertEqual(model.keys,["next-measured-duration-revision"])
                self.assertIn("Shorten",model.prompts[0])
                self.assertTrue(revision_length_fits(
                    revised["script"],revision_length_window(context["outputs"]["story"]["script"],69288,60)))
                self.assertEqual(len(model.reviews),1)
                self.assertEqual(model.reviews[0]["script"],revised["script"])
                self.assertEqual([x["material_id"] for x in revised["scenes"]],["p1","p2","p3"])
                self.assertEqual([x["evidence_ids"] for x in revised["scenes"]],[["f1"],["f2"],["f3"]])
                reviewer.assert_called_once()

    def test_old_word_deletion_json_cannot_bypass_review(self):
        context=self.make_context("документована історія")
        model=FakeModel(invalid=True)
        stage=PreparationStages("/tmp",SimpleNamespace(gemini=model),lambda:None)
        with patch("factory_next.preparation.compact_materials",return_value=[]):
            with self.assertRaises(ValueError):
                stage.revise_story(context,69288)
        self.assertEqual(model.keys,[
            "next-measured-duration-revision",
            "next-measured-duration-structured-repair"])
        self.assertEqual(model.reviews,[])


if __name__=="__main__":
    unittest.main()
