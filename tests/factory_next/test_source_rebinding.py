"""Regression: source-backed research repair may rebind a literal source mention.

No provider requests, no billing, no synthetic fact acceptance shortcuts.
"""
import unittest
from copy import deepcopy
from hashlib import sha256
from material_first.operations import Operations
from material_first.presentation import TOPIC_POLICY
from material_first.source_spans import source_spans


class Source:
    def __init__(self):
        contents=[
            "Галактика Андромеды — большая спиральная галактика. Астрономы наблюдают её.",
            "Галактика Андромеди має багато зірок. Її можна спостерігати в телескоп.",
            "Andromeda Galaxy is a spiral galaxy. Its visible stars can be studied.",
        ]
        self.sources=[
            {"id":"source-"+str(i+1),"url":"https://example.org/galaxy/"+str(i+1),
             "title":"Scientific summary","text":text,
             "sha256":sha256(text.encode()).hexdigest()}
            for i,text in enumerate(contents)]
    def fetch(self,*args):
        return deepcopy(self.sources)


def contexts(spans,*,repaired):
    source_id=spans[1]["id"] if repaired else spans[0]["id"]
    mention="Галактика Андромеди" if repaired else "Галактика Андромеды"
    subject="Andromeda Galaxy" if repaired else "telescope"
    return {role:{"fact_ids":["f"+str(i+1)],
                   "support_span_ids":[source_id],
                   "source_mention":mention,
                   "english_photo_object":subject}
            for i,role in enumerate(("setting","subject","detail"))}


class Model:
    def __init__(self,sources,repaired=None, *, refuse_correction=False):
        spans=source_spans(sources)
        facts=[{"id":"f"+str(i+1),"text":"Andromeda has observable stars.",
                "support":[{"span_id":spans[i]["id"]}]} for i in range(3)]
        self.original={"facts":facts,"required_fact_ids":["f1","f2","f3"],
                       "photo_contexts":contexts(spans,repaired=False)}
        self.repaired=deepcopy(self.original)
        self.repaired["photo_contexts"]=contexts(spans,repaired=True)
        if repaired is not None:repaired(self.repaired)
        self.keys=[]
        self.valid_rebound_contexts=contexts(spans,repaired=True)
        self.refuse_correction=refuse_correction

    def generate(self,key,*args):
        self.keys.append(key)
        if key=="material-brief":
            return deepcopy(self.original),{"cached":True}
        if key=="material-brief-repair:initial":
            return deepcopy(self.repaired),{"cached":True}
        if key in ("material-brief-repair:review:1", "material-brief-repair:review:2"):
            next_draft=deepcopy(self.repaired)
            if not self.refuse_correction:
                next_draft['photo_contexts']=deepcopy(self.valid_rebound_contexts)
            return next_draft,{"cached":True}
        if key in ("material-brief-review:1", "material-brief-review:2", "material-brief-review:3"):
            return {"facts":{f["id"]:{"supported":True,"reason":"source quote matches"}
                             for f in self.repaired["facts"]}},{"cached":True}
        raise AssertionError("unexpected Gemini request: "+key)


class ResearchRebindingTests(unittest.TestCase):
    def run_research(self,mutation=None, *, refuse_correction=False):
        source=Source()
        model=Model(source.sources,mutation,refuse_correction=refuse_correction)
        ops=Operations("/isolated",source,model,search=None,downloader=None,
                       documented_contexts=True)
        ops.voice_correction_enabled=True
        ops.availability_first_contexts=True
        data=ops.research({"topic":"Галактика Андромеди","language":"uk","seconds":45,
                           "presentation_policy":TOPIC_POLICY,
                           "visual_validation_mode":"gemini"})
        return data,model

    def test_corrected_source_mention_can_move_to_actual_quoted_language(self):
        plan,model=self.run_research()
        self.assertEqual(model.keys[:3],
            ["material-brief","material-brief-repair:initial","material-brief-review:1"])
        self.assertEqual(plan["required_fact_ids"],["f1","f2","f3"])
        self.assertEqual(len(plan["queries"]),3)

    def test_bounded_additional_repair_recovers_invalid_source_mention(self):
        def mutate(result):
            result["photo_contexts"]["setting"]["source_mention"]="Неіснуюча галактика"
        data,model=self.run_research(mutate)
        self.assertIn('material-brief-repair:review:1',model.keys)
        self.assertIn('material-brief-review:2',model.keys)
        self.assertEqual(len(data['evidence']['facts']),3)
        self.assertEqual(data['required_fact_ids'],['f1','f2','f3'])

    def test_unresolved_source_literal_stops_after_two_extra_reviews(self):
        def mutate(result):
            result["photo_contexts"]["setting"]["source_mention"]="Неіснуюча галактика"
        with self.assertRaisesRegex(ValueError,"research preflight failed after 2 revisions"):
            self.run_research(mutate,refuse_correction=True)

    def test_repair_may_not_change_facts(self):
        def mutate(result):
            result["facts"][0]["text"]="Unsupported invented story"
        with self.assertRaisesRegex(ValueError,"changed source-backed facts"):
            self.run_research(mutate)

    def test_repair_may_not_reassign_claim_fact(self):
        def mutate(result):
            result["photo_contexts"]["setting"]["fact_ids"]=["f3"]
        with self.assertRaisesRegex(ValueError,"changed setting fact bindings"):
            self.run_research(mutate)


if __name__=="__main__":
    unittest.main()
