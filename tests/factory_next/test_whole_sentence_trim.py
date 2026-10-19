"""Local complete-sentence duration correction remains subject to semantic review.

No external requests or TTS. The same structural policy applies to unrelated
subjects; deletion cannot silently mutate words or cited source identities.
"""
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from factory_next.duration import revision_length_fits, NaturalDurationRejected
from factory_next.voice_length_repair import (
    sentence_contract, trim_one_complete_sentence_locally,
)
from factory_next.preparation import PreparationStages


def fixture(topic):
    window={
        'target_words':111, 'min_words':104, 'max_words':118,
        'target_characters':863, 'min_characters':794, 'max_characters':932,
    }
    scenes=[
        {'id':f'beat-{i}', 'material_id':f'photo-{i}',
         'evidence_ids':[f'fact-{i}'], 'narration':'Original independently reviewed claim.'}
        for i in range(1,4)
    ]
    schema,counts=sentence_contract(scenes,window)
    result={}
    for beat,row in schema['properties'].items():
        result[beat]={}
        for j,key in enumerate(row['required']):
            sentence='These archived records describe documented historical research outcomes and their public context.'
            assert len(sentence.split())==12
            result[beat][key]=sentence[:-1]+f'{beat[-1]}{j}.'
    return topic,scenes,window,schema,result


class WholeSentenceCorrectionTests(unittest.TestCase):
    def test_whole_sentence_trim_fits_and_never_changes_remaining_words(self):
        for topic in ('bee pollination','coral ecosystems','historical computing'):
            with self.subTest(topic=topic):
                _,scenes,window,schema,data=fixture(topic)
                # Make every sentence text distinct, and retain exact text
                # for each sentence not selected for omission.
                before=[s for beat in schema['required']
                        for s in data[beat].values()]
                result=trim_one_complete_sentence_locally(
                    data,schema,scenes,window)
                after=' '.join(row['narration'] for row in result['beats'])
                self.assertTrue(revision_length_fits(after,window))
                self.assertEqual([b['material_id'] for b in result['beats']],
                                 [s['material_id'] for s in scenes])
                self.assertEqual([b['fact_ids'] for b in result['beats']],
                                 [s['evidence_ids'] for s in scenes])
                self.assertEqual(sum(len(b['narration'].split())
                                     for b in result['beats']),108)
                # Each remaining sentence is unchanged, in original order.
                remaining=[x for x in before if x in after]
                self.assertEqual(len(remaining),len(before)-1)
                original_text=' '.join(before)
                self.assertGreater(len(original_text.split()),window['max_words'])
                self.assertEqual(len(' '.join(remaining).split()),108)

    def test_no_trim_of_underlength_already_valid_or_duplicate(self):
        topic,scenes,window,schema,data=fixture('another topic')
        valid_window={**window,'max_words':130,'max_characters':1200}
        with self.assertRaisesRegex(NaturalDurationRejected,'not needed'):
            trim_one_complete_sentence_locally(data,schema,scenes,valid_window)
        all_one_sentence=deepcopy(data)
        for beat in data:
            first_key=next(iter(data[beat]))
            for key in data[beat]:
                all_one_sentence[beat][key]=data[beat][first_key]
        with self.assertRaisesRegex(NaturalDurationRejected,'repeated'):
            trim_one_complete_sentence_locally(
                all_one_sentence,schema,scenes,window)

    def test_active_stage_still_invokes_independent_review_before_tts(self):
        topic,scenes,window,schema,data=fixture('verified historical topic')
        # Actual voice revision uses its own derived sentence window; patch
        # only that deterministic window in this isolated stage test.
        class FakeProvider:
            def __init__(self):
                self.calls=object()
                self.keys=[]
                self.review_requests=[]
            def generate(self,key,instruction,payload,expected):
                self.keys.append(key)
                self.assert_key=key
                return deepcopy(data), {'receipt_id':'offline-test'}
            def review_script(self,request):
                self.review_requests.append(deepcopy(request))
                return {'native_language_quality':True}
        provider=FakeProvider()
        stage=PreparationStages('/tmp',SimpleNamespace(gemini=provider),lambda:None)
        context={
            'request':{'topic':topic,'language':'en','seconds':60},
            '_voice_correction_round':2,
            'outputs':{
                'research':{'request':{'topic':topic,'language':'en','seconds':60},
                            'evidence':{'facts':[{'id':f'fact-{i}'} for i in range(1,4)]}},
                'materials':{'photos':[{'id':f'photo-{i}'} for i in range(1,4)]},
                'story':{'scenes':scenes,
                         'script':'Original reviewed narration.'}
            }
        }
        # Use the exact fixture's measured window and keep each subsequent
        # independent validator in the active execution path.
        def checked_story(req,evidence,photos,draft):
            return [{**scene,'narration':beat['narration']}
                    for scene,beat in zip(scenes,draft['beats'])]
        with patch('factory_next.preparation.revision_length_window',
                   return_value=window), \
             patch('factory_next.preparation.validated_next_story',
                   side_effect=checked_story), \
             patch('factory_next.preparation.validate_native_surface'), \
             patch('factory_next.preparation.validate_script_review') as gate, \
             patch('factory_next.preparation.compact_materials',return_value=[]):
            answer=stage.revise_story(context,63168)
        self.assertEqual(provider.keys,['next-measured-duration-revision'])
        self.assertEqual(len(provider.review_requests),1)
        self.assertEqual(provider.review_requests[0]['script'],answer['script'])
        gate.assert_called_once()