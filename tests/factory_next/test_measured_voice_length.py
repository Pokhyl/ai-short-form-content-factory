"""Measured voice correction protects third TTS from oversized model drafts."""
from copy import deepcopy
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch

from factory_next.duration import revision_length_window, revision_length_fits, NaturalDurationRejected
from factory_next.preparation import PreparationStages


def beats(words):
    text=' '.join(['galaxy']*words)
    lines=[' '.join(text.split()[i::3]) for i in range(3)]
    return {'beats':[{'material_id':f'p{i}',
                      'fact_ids':[f'f{i}'],'narration':line}
                     for i,line in enumerate(lines)]}


class FakeGemini:
    def __init__(self,drafts):
        self.drafts=list(drafts);self.calls=object();self.keys=[];self.reviews=[]
    def generate(self,key,*args):
        self.keys.append(key)
        return deepcopy(self.drafts.pop(0)),{'cached':True}
    def review_script(self,*args):
        self.reviews.append(1)
        return {'native_language_quality':True}


class LengthProtectionTests(TestCase):
    def context(self):
        old=beats(83)['beats']
        scenes=[{'id':f'b{i}','material_id':f'p{i}','evidence_ids':[f'f{i}'],
                 'narration':x['narration']} for i,x in enumerate(old)]
        return {'id':'11111111-1111-4111-8111-111111111111',
                'request':{'language':'uk','seconds':45},
                'outputs':{
                 'story':{'scenes':scenes,'script':' '.join(['galaxy']*83),
                          'review':{'native_language_quality':True}},
                 'research':{'request':{'language':'uk','seconds':45,'topic':'Andromeda'},
                             'evidence':{'facts':[{'id':f'f{i}'} for i in range(3)]}},
                 'materials':{'photos':[{'id':f'p{i}'} for i in range(3)]}}}

    def run_revision(self,drafts):
        context=self.context()
        gemini=FakeGemini(drafts)
        stage=PreparationStages('/empty',SimpleNamespace(gemini=gemini),lambda:None)
        def bind(_request,_evidence,_photos,draft):
            return [{'id':f'b{i}','material_id':beat['material_id'],
                     'evidence_ids':beat['fact_ids'],'narration':beat['narration']}
                    for i,beat in enumerate(draft['beats'])]
        with patch('factory_next.preparation.validate_story',side_effect=bind),\
             patch('factory_next.preparation.validate_native_surface'),\
             patch('factory_next.preparation.validate_script_review'),\
             patch('factory_next.preparation.compact_materials',return_value=[]):
            result=stage.revise_story({**context,'_voice_correction_round':3},40824)
        return result,gemini

    def test_actual_83_word_audio_40_seconds_rejects_161_word_draft(self):
        base=self.context()['outputs']['story']['script']
        window=revision_length_window(base,40824,45)
        self.assertTrue(86<=window['target_words']<=95)
        self.assertFalse(revision_length_fits(' '.join(['galaxy']*161),window))
        self.assertTrue(revision_length_fits(' '.join(['galaxy']*91),window))

    def test_exactly_one_distinct_repair_then_independent_review(self):
        result,gemini=self.run_revision([beats(161),beats(91)])
        self.assertEqual(gemini.keys,['next-measured-duration-revision',
                                      'next-measured-duration-revision-length-repair'])
        self.assertEqual(len(gemini.reviews),1)
        self.assertEqual(len(result['script'].split()),91)
        self.assertEqual(len(result['scenes']),3)

    def test_failed_length_repair_stops_before_review_or_tts(self):
        context=self.context()
        gemini=FakeGemini([beats(161),beats(150)])
        stage=PreparationStages('/empty',SimpleNamespace(gemini=gemini),lambda:None)
        with patch('factory_next.preparation.compact_materials',return_value=[]):
            with self.assertRaisesRegex(NaturalDurationRejected,'outside calibrated'):
                stage.revise_story({**context,'_voice_correction_round':3},40824)
        self.assertEqual(len(gemini.reviews),0)
        self.assertEqual(len(gemini.keys),2)


if __name__=="__main__":
    main()
