"""Regression for actual PL15 voice correction ledger-key collision."""
from copy import deepcopy
from unittest.mock import patch
import unittest

from factory_next.preparation import PreparationStages, VoiceRevisionCalls


class StrictLedger:
    def __init__(self):
        self.claims={'script-review':{'script':'original reviewed narration'}}
        self.deferrals=[]
    def run(self,key,kind,request,invoke,**kwargs):
        if key in self.claims and self.claims[key]!=request:
            raise ValueError('request changed or operation already claimed/ambiguous')
        self.claims[key]=deepcopy(request)
        return invoke()
    def defer_unavailable(self,old,new,delay):
        self.deferrals.append((old,new,delay))
        return {'deferred':True}


class SyntheticGemini:
    def __init__(self,calls):self.calls=calls
    def generate(self,key,instruction,context,schema):
        result=self.calls.run(key,'gemini',{'instruction':instruction,'context':context},
            lambda:{'beats':[{'narration':'Short revised Polish scene.',
                              'material_id':f'p{i}','fact_ids':[f'f{i}']}
                             for i in range(3)]})
        return result,{'model':'controlled'}
    def review_script(self,request):
        return self.calls.run('script-review','gemini',{'script':request['script']},
                              lambda:{'native_language_quality':True})


class Operations:
    def __init__(self,model):self.gemini=model
    def review_script(self,*args):
        raise AssertionError('the original review key must not be claimed again')


class VoiceRevisionLedgerRegression(unittest.TestCase):
    def test_scoped_review_uses_fresh_call_key_and_preserves_original(self):
        ledger=StrictLedger()
        operations=Operations(SyntheticGemini(ledger))
        preparation=PreparationStages('/isolated',operations,lambda:None)
        context={
            'request':{'topic':'How bees pollinate flowers','language':'pl','seconds':15},
            'outputs':{
                'research':{
                    'request':{'topic':'How bees pollinate flowers',
                               'language':'pl','seconds':15,
                               'required_fact_ids':['f0','f1','f2']},
                    'evidence':{'facts':[{'id':f'f{i}','text':'Source fact',
                                           'support':[]} for i in range(3)]}},
                'materials':{'photos':[{'id':f'p{i}','sha256':f'sha{i}'}
                                        for i in range(3)]},
                'story':{'script':'Original source reviewed script with many natural words.',
                         'scenes':[{'id':f'beat-{i+1}','material_id':f'p{i}',
                                    'narration':'Original scene','evidence_ids':[f'f{i}']}
                                   for i in range(3)]}}}
        revised_scenes=[{'id':f'beat-{i+1}','material_id':f'p{i}',
                         'narration':'Short revised Polish scene.',
                         'evidence_ids':[f'f{i}']} for i in range(3)]
        with patch('factory_next.preparation.compact_materials',return_value=[]),              patch('factory_next.preparation.validate_json'),              patch('factory_next.preparation.validate_story',return_value=revised_scenes),              patch('factory_next.preparation.validate_native_surface'),              patch('factory_next.preparation.validate_script_review'):
            result=preparation.revise_story(context,33864)
        self.assertEqual(result['review']['native_language_quality'],True)
        self.assertEqual(result['scenes'],revised_scenes)
        self.assertEqual(ledger.claims['script-review'],
                         {'script':'original reviewed narration'})
        self.assertIn('next-voice-correction:2:next-measured-duration-revision',
                      ledger.claims)
        self.assertIn('next-voice-correction:2:script-review',ledger.claims)
        self.assertIs(operations.gemini.calls,ledger)

    def test_deferral_keys_share_same_bounded_revision_namespace(self):
        ledger=StrictLedger()
        wrapper=VoiceRevisionCalls(ledger)
        self.assertEqual(wrapper.defer_unavailable('script-review','script-review:availability:2',60),
                         {'deferred':True})
        self.assertEqual(ledger.deferrals,
                         [('next-voice-correction:2:script-review',
                           'next-voice-correction:2:script-review:availability:2',60)])

    def test_original_review_collision_is_reproduced_without_namespace(self):
        ledger=StrictLedger()
        with self.assertRaisesRegex(ValueError,'request changed'):
            ledger.run('script-review','gemini',{'script':'new correction'},
                       lambda:{'native_language_quality':True})


if __name__=='__main__':unittest.main()
