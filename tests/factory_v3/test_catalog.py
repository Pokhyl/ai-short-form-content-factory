import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from factory_v3.catalog import prepare, CoverageUnavailable
from factory_v3.preflight import digest, verify_before_voice


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        text=" ".join("Controlled fact "+str(i)+"." for i in range(5))
        self.evidence={"sources":[{"id":"source","url":"https://example.invalid/article",
          "text":text,"sha256":hashlib.sha256(text.encode()).hexdigest()}],
          "facts":[{"id":"f"+str(i),"text":"Controlled fact "+str(i)+".",
           "support":[{"source_id":"source","quote":"Controlled fact "+str(i)+"."}]} for i in range(5)]}
        self.catalog={"units":[],"assets":[],"reviews":[]}
        self.compose_calls=0
        for i in range(5):
            file=self.root/(str(i)+".jpg")
            file.write_bytes(("controlled test image "+str(i)).encode())
            sha=hashlib.sha256(file.read_bytes()).hexdigest()
            asset={"id":"a"+str(i),"path":file.name,"sha256":sha,
              "source_url":"https://example.invalid/photo","author":"test",
              "license":"CC0","license_url":"https://example.invalid/license"}
            unit={"id":"u"+str(i),"fact_ids":["f"+str(i)],
              "contract":{"visual_intent":"controlled view "+str(i),"must_show":["object"],"must_not_show":[]}}
            review={"scene_id":unit["id"],"asset_id":asset["id"],"asset_sha256":sha,
              "contract_sha256":digest(unit["contract"]),"evidence_sha256":digest(self.evidence),
              "receipt_id":"controlled"+str(i),"model":"controlled-test","is_real_photo":True,
              "match_score":90,"must_show_visible":True,"must_not_show_clear":True,"intent_match":True,
              "must_show_checks":[{"concept":"object","visible":True}],"supported_fact_ids":unit["fact_ids"]}
            self.catalog["assets"].append(asset);self.catalog["units"].append(unit)
            self.catalog["reviews"].append(review)

    def tearDown(self):
        self.temp.cleanup()

    def compose(self, request):
        self.compose_calls+=1
        return {"scenes":[{"id":s["id"],"narration":"Controlled fact "+s["fact_ids"][0][1:]+".",
                         "fact_ids":s["fact_ids"]} for s in request["scenes"]]}

    def review_script(self, request):
        facts={f["id"]:f for f in request["evidence"]["facts"]}
        return {"receipt_id":"controlled-semantic-review","model":"controlled-test",
          "topic_covered":True,"topic_sha256":hashlib.sha256(request["topic"].encode()).hexdigest(),
          "script_sha256":hashlib.sha256(request["script"].encode()).hexdigest(),
          "evidence_sha256":digest(request["evidence"]),"language":request["language"],
          "language_match":True,"visual_contracts_match":True,"no_unsupported_claims":True,
          "factual_checks":[{"scene_id":s["id"],"fact_id":f,"narration_quote":s["narration"],
            "supported":facts[f]["text"] in s["narration"]} for s in request["scenes"] for f in s["evidence_ids"]]}

    def run_prepare(self, compose=None):
        return prepare(self.root,"controlled topic","pl",15,self.evidence,self.catalog,
                       ["f"+str(i) for i in range(5)],compose or self.compose,self.review_script)

    def test_catalog_produces_frozen_grounded_plan_and_rechecks(self):
        frozen=self.run_prepare()
        self.assertEqual(self.compose_calls,1)
        self.assertEqual(len(verify_before_voice(self.root,frozen)["selection"]),5)
        self.assertEqual(frozen["payload"]["evidence"],self.evidence)

    def test_unique_asset_shortage_prevents_composer_call(self):
        a,b=self.catalog["assets"][:2]
        (self.root/b["path"]).write_bytes((self.root/a["path"]).read_bytes())
        b["sha256"]=a["sha256"]
        self.catalog["reviews"][1]["asset_sha256"]=a["sha256"]
        with self.assertRaisesRegex(CoverageUnavailable,"unique"):
            self.run_prepare()
        self.assertEqual(self.compose_calls,0)

    def test_unreviewed_real_photo_flag_cannot_unlock_composition(self):
        self.catalog["reviews"][0].pop("is_real_photo")
        with self.assertRaises(CoverageUnavailable):
            self.run_prepare()
        self.assertEqual(self.compose_calls,0)

    def test_unsupported_source_quote_blocks_before_composer(self):
        self.evidence["facts"][0]["support"][0]["quote"]="Invented quote."
        with self.assertRaisesRegex(ValueError,"quotation"):
            self.run_prepare()
        self.assertEqual(self.compose_calls,0)

    def test_changed_fact_invalidates_previously_reviewed_catalog(self):
        self.evidence["facts"][0]["text"]="Changed meaning."
        with self.assertRaises(CoverageUnavailable):
            self.run_prepare()
        self.assertEqual(self.compose_calls,0)

    def test_composer_cannot_change_visual_contract_or_citations(self):
        def change(request):
            result=self.compose(request)
            result["scenes"][0]["contract"]={"must_show":["new subject"]}
            return result
        with self.assertRaisesRegex(ValueError,"visual contract"):
            self.run_prepare(change)
        def invent(request):
            result=self.compose(request)
            result["scenes"][0]["fact_ids"]=["f4"]
            return result
        with self.assertRaisesRegex(ValueError,"unsupported facts"):
            self.run_prepare(invent)

    def test_composer_cannot_silently_omit_required_factual_scope(self):
        self.catalog["units"][-1]["fact_ids"]=["f3","f4"]
        self.catalog["reviews"][-1]["supported_fact_ids"]=["f3","f4"]
        def omit(request):
            result=self.compose(request)
            result["scenes"][-1]["fact_ids"]=["f3"]
            return result
        with self.assertRaisesRegex(ValueError,"omitted required"):
            self.run_prepare(omit)

    def test_frozen_evidence_tampering_is_rejected(self):
        frozen=self.run_prepare()
        frozen["payload"]["evidence"]["facts"][0]["text"]="Modified after freeze"
        with self.assertRaisesRegex(ValueError,"modified"):
            verify_before_voice(self.root,frozen)

    def test_cited_but_unnarrated_fact_fails_semantic_review(self):
        self.catalog["units"][-1]["fact_ids"]=["f3","f4"]
        self.catalog["reviews"][-1]["supported_fact_ids"]=["f3","f4"]
        with self.assertRaisesRegex(ValueError,"not supported"):
            self.run_prepare()
