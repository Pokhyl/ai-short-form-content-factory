"""Exactly one extra fact-only correction after image citations consumed repair slots."""
import hashlib
import unittest
from copy import deepcopy

from factory_v3.gemini import obj, array, string
from material_first.source_spans import source_spans
from material_first.research_review import reviewed_brief


def fixture(topic, names):
    text=("A "+names[0]+" contains a "+names[1]+" and "+names[2]+
          ". The source describes all three visible things.")
    sources=[{"id":"s","url":"https://example.org/verified",
              "text":text,"sha256":hashlib.sha256(text.encode()).hexdigest()}]
    spans=source_spans(sources)
    ident=spans[0]["id"]
    facts=[{"id":f"f{i}","text":f"Documented fact {i}",
            "support":[{"span_id":ident}]} for i in (1,2,3)]
    contexts={
        role:{"fact_ids":[f"f{i}"],"support_span_ids":[ident],
              "source_mention":"imaginary place" if i==1 else word,
              "english_photo_object":word}
        for i,(role,word) in enumerate(zip(("setting","subject","detail"),names),1)
    }
    draft={"facts":facts,"required_fact_ids":["f1","f2","f3"],
           "photo_contexts":contexts}
    s=obj({"id":string(),"text":string(),
           "support":array(obj({"span_id":string([ident])}),1,3)})
    c=obj({"fact_ids":array(string(),1,8),
           "support_span_ids":array(string([ident]),1,3),
           "source_mention":string(),
           "english_photo_object":string()})
    schema=obj({"facts":array(s,3,8),
                "required_fact_ids":array(string(),3,3),
                "photo_contexts":obj({x:c for x in ("setting","subject","detail")})})
    return sources,spans,draft,schema


class BoundedFactAfterPhotoRepair(unittest.TestCase):
    def test_a_fact_correction_becomes_available_only_after_photo_repairs(self):
        for topic,names in (
            ("Wildflower biodiversity",("meadow","bee","pollen")),
            ("Coral biodiversity",("reef","coral","fish")),
        ):
            with self.subTest(topic=topic):
                sources,spans,initial,schema=fixture(topic,names)
                class Provider:
                    def __init__(self):self.called=[]
                    def generate(self,key,task,context,expected_schema):
                        self.called.append(key)
                        if key.startswith("material-brief-repair:review:"):
                            attempt=int(key.rsplit(":",1)[1])
                            edited=deepcopy(initial)
                            if attempt==1:
                                edited["photo_contexts"]["setting"]["source_mention"]="still fictional"
                            elif attempt==2:
                                edited["photo_contexts"]["setting"]["source_mention"]=names[0]
                            elif attempt==3:
                                edited["photo_contexts"]["setting"]["source_mention"]="fake change"
                                edited["facts"][1]["text"]="Independent correction of fact two"
                            edited["facts"][0]["text"]="Unapproved photo-repair rewrite" if attempt<=2 else edited["facts"][0]["text"]
                            return edited,{}
                        if key=="material-brief-review:3":
                            self.assert_noop=False
                            assert context["facts"][0]["text"]==initial["facts"][0]["text"]
                            return {"facts":{
                                f"f{i}":{"supported":i!=2,"reason":"semantic rejection" if i==2 else "supported"}
                                for i in (1,2,3)}},{}
                        if key=="material-brief-review:4":
                            assert context["facts"][1]["text"]=="Independent correction of fact two"
                            assert context["facts"][0]["text"]==initial["facts"][0]["text"]
                            return {"facts":{
                                f"f{i}":{"supported":True,"reason":"source supported"}
                                for i in (1,2,3)}},{}
                        raise AssertionError("unapproved provider call "+key)
                provider=Provider()
                result=reviewed_brief(provider,{"topic":topic},sources,spans,schema,
                                      deepcopy(initial),check_photos=False)
                self.assertEqual(result["facts"][0],initial["facts"][0])
                self.assertEqual(result["facts"][1]["text"],"Independent correction of fact two")
                self.assertEqual(result["photo_contexts"]["setting"]["source_mention"],names[0])
                self.assertEqual(provider.called,[
                    "material-brief-repair:review:1",
                    "material-brief-repair:review:2",
                    "material-brief-review:3",
                    "material-brief-repair:review:3",
                    "material-brief-review:4",
                ])

    def test_without_photo_repairs_there_is_no_third_rewrite(self):
        sources,spans,initial,schema=fixture("Wildflower biodiversity",("meadow","bee","pollen"))
        initial["photo_contexts"]["setting"]["source_mention"]="meadow"
        class Rejecting:
            def __init__(self):self.calls=[]
            def generate(self,key,task,context,schema):
                self.calls.append(key)
                if key.startswith("material-brief-review:"):
                    return {"facts":{
                        f"f{i}":{"supported":False,"reason":"unsupported"}
                        for i in (1,2,3)}},{}
                if key.startswith("material-brief-repair:review:"):
                    return deepcopy(initial),{}
                raise AssertionError(key)
        model=Rejecting()
        with self.assertRaisesRegex(ValueError,"after 2 revisions"):
            reviewed_brief(model,{"topic":"Wildflower biodiversity"},sources,spans,schema,
                           deepcopy(initial),check_photos=False)
        self.assertEqual(model.calls,[
            "material-brief-review:1","material-brief-repair:review:1",
            "material-brief-review:2","material-brief-repair:review:2",
            "material-brief-review:3",
        ])


if __name__=="__main__":
    unittest.main()