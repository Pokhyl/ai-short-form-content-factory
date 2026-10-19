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
        # Voice correction now produces a fixed, server-owned natural
        # sentence structure in exactly one model call.
        result=self.calls.run(key,'gemini',{'instruction':instruction,'context':context},
            lambda:{f'beat_{i+1}':{'sentence_1':
                    ' '.join(['pszczol']*10)+f' temat{i}.'}
                    for i in range(3)})
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
                'story':{'script':' '.join(['pszczol']*73),
                         'scenes':[{'id':f'beat-{i+1}','material_id':f'p{i}',
                                    'narration':'Original scene','evidence_ids':[f'f{i}']}
                                   for i in range(3)]}}}
        revised_scenes=[{'id':f'beat-{i+1}','material_id':f'p{i}',
                         'narration':' '.join(['pszczol']*10),
                         'evidence_ids':[f'f{i}']} for i in range(3)]
        # This test exercises isolated scoped ledger identity, not real
        # research/TTS prose. Supply a controlled reviewed scene edit so
        # the extractive correction branch uses the same durable namespace.
        fixed={'beats':[{'material_id':f'p{i}','fact_ids':[f'f{i}'],
                         'narration':'Controlled shortened scene.'}
                        for i in range(3)]}
        with patch('factory_next.preparation.extractive_omission_candidates',
                   return_value=([{'id':'b0:5'}],[{'id':'b0:5'}],{'type':'object'})), \
             patch('factory_next.preparation.apply_extractive_omission_plan',
                   return_value=fixed), \
             patch('factory_next.preparation.validate_json'), \
             patch('factory_next.preparation.validate_story',return_value=revised_scenes), \
             patch('factory_next.preparation.validate_native_surface'), \
             patch('factory_next.preparation.validate_script_review'):
            from factory_next.duration import revision_length_window
            window=revision_length_window(context['outputs']['story']['script'],33864,15)
            result=preparation._revise_overlong_extractively(context,window)
        self.assertEqual(result['review']['native_language_quality'],True)
        self.assertEqual(result['scenes'],revised_scenes)
        self.assertEqual(ledger.claims['script-review'],
                         {'script':'original reviewed narration'})
        self.assertIn('next-voice-correction:2:next-measured-extractive-deletions',
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

    def test_third_correction_has_distinct_durable_keys(self):
        ledger=StrictLedger()
        second=VoiceRevisionCalls(ledger,attempt=2)
        third=VoiceRevisionCalls(ledger,attempt=3)
        second.run('script-review','gemini',{'script':'second'},lambda:{'pass':True})
        third.run('script-review','gemini',{'script':'third'},lambda:{'pass':True})
        self.assertIn('next-voice-correction:2:script-review',ledger.claims)
        self.assertIn('next-voice-correction:3:script-review',ledger.claims)
        with self.assertRaises(ValueError):VoiceRevisionCalls(ledger,attempt=4)

    def test_structured_repair_is_a_new_bounded_claim_in_each_voice_round(self):
        ledger=StrictLedger()
        for attempt in (2,3):
            scoped=VoiceRevisionCalls(ledger,attempt=attempt)
            scoped.run('next-measured-duration-revision','gemini',
                       {'round':attempt,'draft':'completed_invalid'},
                       lambda:{'status':'completed'})
            scoped.run('next-measured-duration-structured-repair','gemini',
                       {'round':attempt,'draft':'corrected_new_request'},
                       lambda:{'status':'completed'})
            scoped.run('script-review','gemini',
                       {'round':attempt,'approved':'reviewed'},
                       lambda:{'native_language_quality':True})
        self.assertEqual(len(ledger.claims),7) # original review plus 3 * 2 rounds
        self.assertEqual(ledger.claims['script-review'],
                         {'script':'original reviewed narration'})
        for attempt in (2,3):
            self.assertIn(
                f'next-voice-correction:{attempt}:next-measured-duration-structured-repair',
                ledger.claims)
        # Replacing a persisted request under the same key must still fail.
        with self.assertRaisesRegex(ValueError,'request changed'):
            VoiceRevisionCalls(ledger,attempt=2).run(
                'next-measured-duration-structured-repair','gemini',
                {'round':2,'draft':'different'},
                lambda:{'status':'unreachable'})

    def test_original_review_collision_is_reproduced_without_namespace(self):
        ledger=StrictLedger()
        with self.assertRaisesRegex(ValueError,'request changed'):
            ledger.run('script-review','gemini',{'script':'new correction'},
                       lambda:{'native_language_quality':True})


if __name__=='__main__':unittest.main()
