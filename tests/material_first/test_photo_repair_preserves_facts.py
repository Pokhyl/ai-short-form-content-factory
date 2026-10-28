"""An image quote correction never authorizes a factual rewrite."""
import hashlib
import unittest
from copy import deepcopy
from factory_v3.gemini import obj,array,string,BOOL
from material_first.source_spans import source_spans
from material_first.research_review import (
    reviewed_brief, preserve_facts_after_photo_repair,
    photo_only_validation_failure,
)

class PhotoRepairFactInvariant(unittest.TestCase):
    def test_only_photo_errors_are_classified(self):
        self.assertTrue(photo_only_validation_failure([
            "setting: selected source span does not contain the object mention; detail: search hint names only a broad category"]))
        self.assertFalse(photo_only_validation_failure(["fact f1: unsupported chronology"]))
        self.assertFalse(photo_only_validation_failure(["model response fields differ from required schema"]))
        self.assertFalse(photo_only_validation_failure(["setting: wrong", "fact f2: wrong"]))

    def test_photo_mention_repair_preserves_original_facts_for_unrelated_topics(self):
        for topic,things in [
            ("Wildflower pollination",("meadow","bee","pollen")),
            ("Coral habitat",("reef","coral","fish")),
        ]:
            with self.subTest(topic=topic):
                text="The "+things[0]+" contains a "+things[1]+", with "+things[2]+" nearby."
                sources=[{"id":"source1","url":"https://example.org/research",
                          "title":topic,"text":text,
                          "sha256":hashlib.sha256(text.encode()).hexdigest()}]
                span=source_spans(sources)[0]["id"]
                facts=[{"id":"f"+str(i),"text":"Source-backed claim "+str(i),
                        "support":[{"span_id":span}]} for i in (1,2,3)]
                contexts={role:{"fact_ids":["f"+str(i)],
                          "support_span_ids":[span],
                          "source_mention":thing if i!=1 else "invented place",
                          "english_photo_object":thing}
                          for i,(role,thing) in enumerate(
                              zip(("setting","subject","detail"),things),start=1)}
                initial={"facts":facts,"required_fact_ids":["f1","f2","f3"],
                         "photo_contexts":contexts}
                row=obj({"id":string(),"text":string(),
                         "support":array(obj({"span_id":string([span])}),1,3)})
                c=obj({"fact_ids":array(string(),1,8),
                       "support_span_ids":array(string([span]),1,3),
                       "source_mention":string(),
                       "english_photo_object":string()})
                schema=obj({"facts":array(row,3,8),
                            "required_fact_ids":array(string(),3,3),
                            "photo_contexts":obj({x:c for x in ("setting","subject","detail")})})
                class Model:
                    calls=[]
                    def generate(self,key,instruction,context,required_schema):
                        self.calls.append(key)
                        if key=="material-brief-repair:review:1":
                            self_prompt=instruction
                            assert "Return ONLY photo_contexts" in self_prompt
                            assert set(required_schema["properties"])=={"photo_contexts"}
                            revision=deepcopy(initial)
                            revision["photo_contexts"]["setting"]["source_mention"]=things[0]
                            revision["facts"][0]["text"]="MODEL-INVENTED HISTORICAL CLAIM"
                            return {"photo_contexts":{role:{k:v for k,v in row.items() if k!="fact_ids"}
                                for role,row in revision["photo_contexts"].items()}},{}
                        if key=="material-brief-review:2":
                            assert context["facts"][0]["text"]==facts[0]["text"]
                            return {"facts":{
                                identity:{"supported":True,"reason":"source evidence"}
                                for identity in ("f1","f2","f3")}},{}
                        raise AssertionError("unexpected model call: "+key)
                model=Model()
                original=deepcopy(initial)
                result=reviewed_brief(model,{"topic":topic},sources,
                                      source_spans(sources),schema,deepcopy(initial),
                                      check_photos=False)
                self.assertEqual(result["facts"],facts)
                self.assertEqual(result["required_fact_ids"],initial["required_fact_ids"])
                self.assertEqual(result["photo_contexts"]["setting"]["source_mention"],things[0])
                self.assertEqual(model.calls,["material-brief-repair:review:1","material-brief-review:2"])
                self.assertEqual(initial,original)

    def test_extra_photo_fact_associations_are_rejected(self):
        before={
            "facts":[{"id":"f1","text":"Fact one"},{"id":"f2","text":"Fact two"}],
            "required_fact_ids":["f1"],
            "photo_contexts":{
                "subject":{"fact_ids":["f1"],"source_mention":"source name"}
            }
        }
        proposed=deepcopy(before)
        proposed["photo_contexts"]["subject"]["fact_ids"]=["f1","f2"]
        proposed["facts"][0]["text"]="Invented rewrite"
        with self.assertRaisesRegex(ValueError,"prohibited fields"):
            preserve_facts_after_photo_repair(before,proposed)

    def test_facts_cannot_be_rebound_to_different_photo_context(self):
        before={"facts":[{"id":"f1","text":"Original"}],
                "required_fact_ids":["f1"],
                "photo_contexts":{"setting":{"fact_ids":["f1"]}}}
        changed=deepcopy(before)
        changed["photo_contexts"]["setting"]["fact_ids"]=["f2"]
        with self.assertRaisesRegex(ValueError,"prohibited fields"):
            preserve_facts_after_photo_repair(before,changed)


if __name__=="__main__":
    unittest.main()