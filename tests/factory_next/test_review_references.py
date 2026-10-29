"""Replay exact rejected request; short references retain server-owned text."""
from copy import deepcopy
import json
from pathlib import Path
from unittest import TestCase
from factory_v3.gemini import Gemini,ModelSchemaError
from factory_v3.preflight import digest


class Capture(Exception):pass


class ReviewReferencesTests(TestCase):
    def setUp(self):
        self.saved=json.loads((Path(__file__).parent/'fixtures/actual-review-400-279615cb.json').read_text())
        self.request=deepcopy(self.saved['request'])
        self.identity=None;self.response=None
        owner=self
        class Calls:
            def run(self,key,kind,identity,invoke):
                owner.identity=identity
                if owner.response is None:raise Capture()
                return {'status':200,'body':{'candidates':[{'finishReason':'STOP',
                    'content':{'parts':[{'text':json.dumps(owner.response)}]}}]}}
        self.model=Gemini(Calls(),lambda:'unused',None,model=self.saved['model'],free_tier_confirmed=True)
        self.model.require_fact_coverage=True;self.model.default_thinking_level='medium'

    def capture(self):
        with self.assertRaises(Capture):self.model.review_script(self.request)
        return self.identity

    def test_exact_old_failure_reconstructs_without_external_call(self):
        self.assertEqual(digest(self.capture()),self.saved['failed_request_hash'])

    def test_compact_schema_has_only_short_references_and_unchanged_text(self):
        old=self.capture();self.request['review_reference_policy']='scene-ids-v1';new=self.capture()
        old_schema=old['body']['generationConfig']['responseJsonSchema']
        schema=new['body']['generationConfig']['responseJsonSchema']
        self.assertLess(len(json.dumps(schema)),len(json.dumps(old_schema))//2)
        old_context=json.loads(old['body']['contents'][0]['parts'][0]['text'])
        context=json.loads(new['body']['contents'][0]['parts'][0]['text'])
        self.assertEqual(context,old_context)
        for scene in self.request['scenes']:
            self.assertNotIn(scene['narration'],json.dumps(schema,ensure_ascii=False))

    def controlled_response(self):
        self.request['review_reference_policy']='scene-ids-v1'
        identity=self.capture();schema=identity['body']['generationConfig']['responseJsonSchema']
        checks=schema['properties']['factual_checks']['properties']
        return {'language':'ru','language_match':True,'visual_contracts_match':True,
                'no_unsupported_claims':False,'topic_covered':False,'native_language_quality':True,
                'factual_checks':{key:{'narration_scene_id':row['properties']['narration_scene_id']['enum'][0],
                    'comparison':'Controlled negative verdict','supported':False} for key,row in checks.items()},
                'coverage_checks':{f:{'comparison':'Controlled missing cause','narration_scene_ids':[],
                    'missing_details':['cause'],'covered':False} for f in self.request['required_fact_ids']}}

    def test_exact_quotes_are_restored_without_overwriting_negative_verdicts(self):
        from unittest.mock import patch
        from factory_v3.grounding import validate_script_review
        self.response=self.controlled_response()
        with patch('factory_v3.gemini.validate_script_review',wraps=validate_script_review) as validate:
            with self.assertRaisesRegex(ValueError,'semantic/language'):
                self.model.review_script(self.request)
            result=validate.call_args.args[4]
        scenes={s['id']:s['narration'] for s in self.request['scenes']}
        for check in result['factual_checks']:
            self.assertEqual(check['narration_quote'],scenes[check['scene_id']])
            self.assertFalse(check['supported'])
        self.assertFalse(result['no_unsupported_claims'])
        self.assertTrue(all(not row['covered'] for row in result['coverage_checks'].values()))

    def test_another_scene_cannot_be_substituted_for_assertion(self):
        self.response=self.controlled_response()
        first=next(iter(self.response['factual_checks'].values()))
        first['narration_scene_id']='invented-scene'
        with self.assertRaises(ModelSchemaError):self.model.review_script(self.request)

    def test_opted_in_negative_review_retains_feedback_and_never_approves(self):
        from factory_v3.gemini import ScriptReviewRejected
        self.response=self.controlled_response()
        self.request['voice_review_repair_policy']='one-reviewed-repair-v1'
        with self.assertRaises(ScriptReviewRejected) as caught:
            self.model.review_script(self.request,review_key='script-review-repaired')
        self.assertFalse(caught.exception.review['topic_covered'])
        self.assertTrue(all(not row['covered'] for row in caught.exception.review['coverage_checks'].values()))
