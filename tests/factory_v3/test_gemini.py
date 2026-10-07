"""HTTP/model responses here are explicitly controlled, not live provider evidence."""
import copy
import hashlib
import json
import unittest
import test_catalog
from test_preparation import FakeLedger
from factory_v3.gemini import Gemini, obj, string, array, provider_schema
from factory_v3.preparation import BudgetedCalls
from factory_v3.preflight import digest, verify_before_voice


class HTTP:
    def __init__(self, result):
        self.result = result
        self.requests = []
        self.finish = "STOP"
        self.raw_text = None

    def request_receipt(self, method, url, body, headers, timeout):
        self.requests.append((method, url, body, headers, timeout))
        return {"status": 200, "headers": {"x-ratelimit-remaining": "controlled"},
                "body": {"candidates": [{"finishReason": self.finish,
                    "content": {"parts": [{"text": self.raw_text or json.dumps(self.result)}]}}],
                         "modelVersion": "controlled-test",
                         "usageMetadata": {"totalTokenCount": 42}}}


class GeminiTests(unittest.TestCase):
    def test_provider_subset_keeps_field_names_and_local_string_validation(self):
        schema = obj({"minLength": {**string(), "maxLength": 3}})
        compiled = provider_schema(schema)
        self.assertEqual(compiled["properties"]["minLength"], {"type": "string"})
        self.assertEqual(schema["properties"]["minLength"]["maxLength"], 3)
        with self.assertRaisesRegex(ValueError, "unsupported provider schema"):
            provider_schema({"type": "string", "pattern": "secret"})
        from factory_v3.gemini import validate_json
        for text in ["", "too long"]:
            with self.assertRaisesRegex(ValueError, "empty text"):
                validate_json({"minLength": text}, schema)
        bounded = array(string(), 2, 2)
        compiled_array = provider_schema(bounded)
        self.assertEqual(compiled_array["description"], "Return exactly 2 items.")
        self.assertNotIn("maxItems", compiled_array)
        for items in [["one"], ["one", "two", "three"]]:
            with self.assertRaisesRegex(ValueError, "array exceeds"):
                validate_json(items, bounded)

    def setUp(self):
        self.fixture = test_catalog.CatalogTests()
        self.fixture.setUp()
        self.ledger = FakeLedger()
        self.ledger.limit = 20
        self.http = HTTP({"answer": "controlled"})
        self.adapter = Gemini(BudgetedCalls(self.ledger, "test"), lambda: "controlled-secret",
                              self.http, model="gemini-3.5-flash-lite", free_tier_confirmed=True)

    def tearDown(self):
        self.fixture.tearDown()

    def generate(self):
        return self.adapter.generate("test", "controlled", {"question": "test"},
                                     obj({"answer": string()}))

    def test_exact_replay_uses_one_http_request_and_retains_usage(self):
        first = self.generate()
        self.assertEqual(first, self.generate())
        self.assertEqual(len(self.http.requests), 1)
        self.assertEqual(first[1]["usage"]["totalTokenCount"], 42)
        self.assertEqual(first[1]["http"]["headers"]["x-ratelimit-remaining"], "controlled")
        self.assertNotIn("controlled-secret", json.dumps(first))

    def test_truncated_response_is_not_retried(self):
        self.http.finish = "MAX_TOKENS"
        for _ in range(2):
            with self.assertRaisesRegex(ValueError, "incomplete"):
                self.generate()
        self.assertEqual(len(self.http.requests), 1)

    def test_invalid_schema_and_duplicate_fields_are_rejected(self):
        self.http.result = {"answer": "test", "approval": True}
        with self.assertRaisesRegex(ValueError, "schema"):
            self.generate()
        self.adapter.calls = BudgetedCalls(FakeLedger(), "other")
        self.http.raw_text = '{"answer":"first","answer":"second"}'
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.generate()

    def test_free_tier_gate_blocks_before_http(self):
        with self.assertRaisesRegex(ValueError, "free-tier"):
            Gemini(None, None, self.http, model="gemini-3.5-flash-lite", free_tier_confirmed=False)
        self.assertEqual(self.http.requests, [])

    def test_exact_photo_bytes_and_all_review_hashes(self):
        import base64
        f = self.fixture
        unit, asset = f.catalog["units"][0], f.catalog["assets"][0]
        photo = b"\xff\xd8\xffcontrolled-test-photo"
        (f.root / asset["path"]).write_bytes(photo)
        asset["sha256"] = hashlib.sha256(photo).hexdigest()
        self.http.result = {"is_real_photo": True, "match_score": 90,
            "must_show_visible": True, "must_not_show_clear": True, "intent_match": True,
            "must_show_checks": [{"concept": "object", "visible": True}],
            "supported_fact_ids": unit["fact_ids"]}
        result = self.adapter.review_photo(f.root, unit, asset, f.evidence)
        parts = self.http.requests[0][2]["contents"][0]["parts"]
        self.assertEqual(base64.b64decode(parts[1]["inlineData"]["data"]), photo)
        self.assertEqual(result["asset_sha256"], asset["sha256"])
        self.assertEqual(result["contract_sha256"], digest(unit["contract"]))
        self.assertEqual(result["evidence_sha256"], digest(f.evidence))
        (f.root / asset["path"]).write_bytes(photo + b"changed")
        with self.assertRaisesRegex(ValueError, "changed"):
            self.adapter.review_photo(f.root, unit, asset, f.evidence)
        self.assertEqual(len(self.http.requests), 1)

    def test_cited_but_unnarrated_fact_fails_independent_model_review(self):
        f = self.fixture
        scenes = [{"id": "u0", "narration": "Unrelated sentence.", "evidence_ids": ["f0"],
                   "contract": f.catalog["units"][0]["contract"]}]
        request = {"topic": "controlled", "language": "pl", "script": scenes[0]["narration"],
                   "scenes": scenes, "evidence": f.evidence}
        self.http.result = {"language": "pl", "language_match": True,
            "visual_contracts_match": True, "no_unsupported_claims": False, "topic_covered": True,
            "factual_checks": [{"scene_id": "u0", "fact_id": "f0",
                               "narration_quote": "Unrelated sentence.", "supported": False}]}
        with self.assertRaisesRegex(ValueError, "semantic"):
            self.adapter.review_script(request)
        self.assertEqual(len(self.http.requests), 1)

    def native_review_fixture(self):
        from pathlib import Path
        saved=json.loads((Path(__file__).parent/'fixtures/partial-native-review.json').read_text())
        request=saved['request']
        response={k:v for k,v in saved['actual_review'].items() if k!='factual_checks'}
        pairs=[(scene,fact) for scene in request['scenes'] for fact in scene['evidence_ids']]
        response['factual_checks']={'assertion_'+str(i+1):
            {'narration_quote':scene['narration'],'supported':True} for i,(scene,fact) in enumerate(pairs)}
        return saved,request,response,pairs

    def test_native_review_requires_every_named_scene_fact_pair(self):
        saved,request,response,pairs=self.native_review_fixture()
        self.assertEqual(len(saved['actual_review']['factual_checks']),4)
        self.assertEqual(len(pairs),6)
        self.http.result=response  # Controlled completion, not new semantic approval.
        result=self.adapter.review_script(request)
        self.assertEqual([(c['scene_id'],c['fact_id']) for c in result['factual_checks']],
                         [(s['id'],f) for s,f in pairs])
        body=self.http.requests[0][2]
        checks=body['generationConfig']['responseJsonSchema']['properties']['factual_checks']
        self.assertEqual(checks['type'],'object')
        self.assertEqual(len(checks['required']),6)
        context=json.loads(body['contents'][0]['parts'][0]['text'])
        self.assertEqual(len(context['required_assertions']),6)
        self.assertEqual(len(self.http.requests),1)

    def test_native_named_check_cannot_omit_even_a_nonessential_fact(self):
        _,request,response,_=self.native_review_fixture()
        del response['factual_checks']['assertion_1']
        self.http.result=response
        with self.assertRaisesRegex(ValueError,'schema'):self.adapter.review_script(request)
        self.assertEqual(len(self.http.requests),1)

    def test_named_check_rejects_unsupported_fact_and_nonverbatim_quote(self):
        _,request,response,_=self.native_review_fixture()
        response['factual_checks']['assertion_1']['supported']=False
        self.http.result=response
        with self.assertRaisesRegex(ValueError,'not supported'):self.adapter.review_script(request)
        self.assertEqual(len(self.http.requests),1)

    def test_named_check_rejects_invented_narration_quote(self):
        _,request,response,_=self.native_review_fixture()
        response['factual_checks']['assertion_1']['narration_quote']='Invented claim.'
        self.http.result=response
        with self.assertRaisesRegex(ValueError,'actual narration'):self.adapter.review_script(request)
        self.assertEqual(len(self.http.requests),1)

    def test_narration_composer_receives_fixed_contracts_and_no_tools(self):
        f = self.fixture
        request = {"topic": "controlled", "language": "pl", "seconds": 15,
                   "evidence": f.evidence,
                   "scenes": [{"id": u["id"], "contract": u["contract"], "fact_ids": u["fact_ids"]}
                              for u in f.catalog["units"]]}
        self.http.result = f.compose(request)
        self.assertEqual(self.adapter.compose(request), self.http.result)
        body = self.http.requests[0][2]
        self.assertNotIn("tools", body)
        context = json.loads(body["contents"][0]["parts"][0]["text"])
        self.assertEqual(context["scenes"], request["scenes"])

    def test_grounded_preflight_rejects_forged_photo_or_fact_approval(self):
        frozen = self.fixture.run_prepare()
        for change in ["photo", "facts"]:
            mutated = copy.deepcopy(frozen)
            review = mutated["payload"]["reviews"][0]
            if change == "photo":
                review["is_real_photo"] = False
            else:
                review["supported_fact_ids"] = []
            mutated["sha256"] = digest(mutated["payload"])
            with self.assertRaises(ValueError):
                verify_before_voice(self.fixture.root, mutated)

    def test_grounded_outline_requires_exact_quotes_and_distinct_search_contexts(self):
        f = self.fixture
        units = copy.deepcopy(f.catalog["units"])
        for index, unit in enumerate(units):
            unit["queries"] = [{"query": "object " + str(index) + " view " + str(i), "orientation": "portrait"}
                               for i in range(3)]
        self.http.result = {"facts": f.evidence["facts"], "required_fact_ids": ["f0"], "units": units}
        request = {"topic": "controlled", "language": "pl", "seconds": 15, "sources": f.evidence["sources"]}
        result = self.adapter.outline(request)
        self.assertEqual(result["evidence"], f.evidence)
        self.assertEqual(len(result["units"]), 5)
        self.adapter.calls = BudgetedCalls(FakeLedger(), "other")
        self.http.result = copy.deepcopy(self.http.result)
        self.http.result["facts"][0]["support"][0]["quote"] = "Invented quote"
        with self.assertRaisesRegex(ValueError, "quotation"):
            self.adapter.outline(request)

    def test_compact_evidence_keeps_every_quote_and_full_hash_validation(self):
        from factory_v3.grounding import compact_evidence, validate_evidence
        full = copy.deepcopy(self.fixture.evidence)
        original = copy.deepcopy(full)
        view = compact_evidence(full)
        self.assertEqual(view['facts'], full['facts'])
        self.assertEqual(view['sources'][0]['sha256'], full['sources'][0]['sha256'])
        self.assertNotIn('text', view['sources'][0])
        self.assertEqual(full, original)
        view['facts'][0]['text'] = 'Mutation'
        self.assertEqual(full, original)
        full['sources'][0]['text'] += 'Tampered'
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            validate_evidence(full)

    def test_completed_schema_failure_exposes_draft_without_repeating_upstream(self):
        from factory_v3.gemini import ModelSchemaError
        self.http.result = {'words': ['short']}
        schema = obj({'words': array(string(), 10, 20)})
        for _ in range(2):
            with self.assertRaises(ModelSchemaError) as caught:
                self.adapter.generate('short-draft', 'controlled', {}, schema)
            self.assertEqual(caught.exception.result, {'words': ['short']})
        self.assertEqual(len(self.http.requests), 1)
        self.assertFalse(self.ledger.terminal)

class ImageBatchTests(unittest.TestCase):
    setUp = GeminiTests.setUp
    tearDown = GeminiTests.tearDown

    def test_four_original_images_bound_to_ids_in_one_receipted_request(self):
        import base64
        photos = [{'bytes': b'\xff\xd8\xffphoto'+bytes([i]), 'mime':'image/jpeg', 'asset_id': 'a'+str(i)} for i in range(4)]
        result, receipt = self.adapter.generate('batch', 'inspect', {}, obj({'answer':string()}), photos=photos)
        self.assertEqual(len(self.http.requests), 1)
        parts = self.http.requests[0][2]['contents'][0]['parts']
        for i,p in enumerate(photos):
            self.assertIn(p['asset_id'], parts[1+i*2]['text'])
            self.assertEqual(base64.b64decode(parts[2+i*2]['inlineData']['data']), p['bytes'])
        self.assertTrue(receipt['receipt_id'])
        self.assertEqual((result,receipt), self.adapter.generate('batch', 'inspect', {}, obj({'answer':string()}), photos=photos))
        self.assertEqual(len(self.http.requests), 1)

    def test_image_batch_budget_rejects_before_any_http_call(self):
        photo = {'bytes': b'x', 'mime':'image/jpeg'}
        for kwargs in [{'photos':[photo]*5},{'photo':photo,'photos':[photo]}, {'photos':{}},
                       {'photos':[{'bytes':b'x'*(5*1024*1024),'mime':'image/jpeg'}]*2}]:
            with self.assertRaises(ValueError):
                self.adapter.generate('bad-batch','inspect',{},obj({'answer':string()}),**kwargs)
        self.assertEqual(self.http.requests, [])
