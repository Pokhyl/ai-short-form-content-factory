"""Actual rejected model text; no live calls or fabricated acceptance."""
import json
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase

from factory_v3.gemini import Gemini, ModelSchemaError
from factory_v3.preparation import verify_saved_request
from factory_next.preparation import PreparationStages, validated_next_story


class ActualStoryReplay(TestCase):
    def test_exact_saved_requests_reproduce_length_failure_before_review(self):
        saved=json.loads((Path(__file__).parent/'fixtures/actual-story-4369.json').read_text())
        responses={r['key']:r for r in saved['responses']}
        seen=[]
        class Calls:
            def run(self,key,kind,identity,send):
                response=responses[key]
                verify_saved_request(identity,response['request_hash'])
                seen.append(key)
                return {'status':200,'body':{'candidates':[{'finishReason':'STOP',
                    'content':{'parts':[{'text':text} for text in response['texts']]}}]}}
        model=Gemini(Calls(),lambda:None,None,model='gemini-3.5-flash-lite',free_tier_confirmed=True)
        stage=PreparationStages('/unused',SimpleNamespace(gemini=model),lambda:None)
        with self.assertRaises(ModelSchemaError):stage.story(saved['context'])
        self.assertEqual(seen,['next-story','next-story-length-repair:1'])

    def test_actual_initial_story_also_fails_photo_uniqueness(self):
        saved=json.loads((Path(__file__).parent/'fixtures/actual-story-4369.json').read_text())
        outputs=saved['context']['outputs']
        draft=json.loads(''.join(saved['responses'][0]['texts']))
        with self.assertRaises(ValueError):
            validated_next_story(outputs['research']['request'],outputs['research']['evidence'],
                                 outputs['materials']['photos'],draft)
