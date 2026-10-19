"""Real-incident regressions for source-preserving measured voice shortening.

No external network, no TTS and no live provider quota consumed.
Recreates the verified 2026-10-18 UK45 DNA story / 49.536 second MP3.
"""
import re
import unittest
from collections import Counter
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from factory_next.duration import revision_length_window, revision_length_fits, NaturalDurationRejected
from factory_next.voice_length_repair import (
    extractive_omission_candidates, apply_extractive_omission_plan)
from factory_next.preparation import PreparationStages


FACTS = [
    {'id':'f1','text':'ДНК — це макромолекула, яка виконує роль головного сховища генетичної інформації, необхідної для розвитку та функціонування живих організмів.'},
    {'id':'f2','text':"Структурно ДНК складається з двох полінуклеотидних ланцюгів, закручених у подвійну спіраль, де нуклеотиди з'єднані водневими зв'язками згідно з принципом комплементарності."},
    {'id':'f3','text':'Кожен нуклеотид у складі ДНК містить азотисту основу (аденін, гуанін, тимін або цитозин), цукор дезоксирибозу та фосфатну групу.'},
]
NARRATION = [
    "Дезоксирибонуклеїнова кислота, або ДНК, є фундаментальною макромолекулою, що функціонує як головне сховище генетичних інструкцій. Ця інформація є критично необхідною для розвитку та нормального функціонування будь-якого живого організму на Землі.",
    "Структурно ДНК організована як два полінуклеотидні ланцюги, що закручені у формі подвійної спіралі. Ці нитки утримуються разом за допомогою водневих зв'язків між азотистими основами, що підпорядковуються суворому принципу комплементарності.",
    "Кожен окремий нуклеотид у складі ДНК містить один із чотирьох типів азотистих основ — аденін, гуанін, тимін або цитозин. Крім основи, до складу кожного нуклеотиду обов'язково входять молекула цукру, відома як дезоксирибоза, та фосфатна група, які формують міцний остов спіралі.",
]
SELECTED = {
    'фундаментальною','критично','нормального','будь-якого',
    'разом','суворому','окремий','кожного',"обов'язково",'міцний'
}


class StrictLedger:
    def __init__(self):
        self.operations={}
    def run(self,key,kind,identity,invoke,**kwargs):
        if key in self.operations:
            raise AssertionError('a completed claim must not be resent')
        self.operations[key]=(kind,deepcopy(identity))
        return invoke()


class RecordedGemini:
    def __init__(self, ledger, plan=None, bad_then_good=False):
        self.calls=ledger
        self.plan=plan
        self.bad_then_good=bad_then_good
        self.requests=[]
        self.reviews=[]
    def generate(self,key,instruction,context,schema):
        self.requests.append((key,context,schema))
        result=deepcopy(self.plan)
        if self.bad_then_good and len(self.requests)==1:
            result={'remove_ids':['unknown:999']}
        return self.calls.run(key,'gemini',{'instruction':instruction,'context':context},
                              lambda: result),{'cached':True}
    def review_script(self, request):
        self.reviews.append(deepcopy(request))
        return self.calls.run('script-review','gemini',
            {'script':request['script']},
            lambda:{'native_language_quality':True})


class ExtractiveVoiceRevisionTests(unittest.TestCase):
    def setUp(self):
        self.scenes=[
            {'id':f'beat-{i}','material_id':f'photo-{i}',
             'evidence_ids':[f'f{i}'],'narration':narration}
            for i,narration in enumerate(NARRATION,1)]
        self.script=' '.join(NARRATION)
        self.evidence={'facts':deepcopy(FACTS)}
        self.window=revision_length_window(self.script,49536,45)
        self.public,self.candidates,self.schema=extractive_omission_candidates(
            self.scenes,self.evidence,self.window)
        self.plan={'remove_ids':[candidate['id'] for candidate in self.candidates
                                 if candidate['word'] in SELECTED]}

    def test_actual_49_536ms_dna_clip_shortens_with_no_new_words_or_fact_ids(self):
        self.assertEqual(len(self.script.split()),98)
        self.assertEqual(len(self.script),765)
        self.assertEqual((self.window['min_words'],self.window['max_words']),(83,93))
        self.assertEqual(len(self.plan['remove_ids']),10)
        result=apply_extractive_omission_plan(
            self.scenes,self.plan,self.candidates,self.schema,self.window)
        new_text=' '.join(beat['narration'] for beat in result['beats'])
        self.assertEqual(len(new_text.split()),88)
        self.assertEqual(len(new_text),667)
        self.assertTrue(revision_length_fits(new_text,self.window))
        self.assertEqual([b['material_id'] for b in result['beats']],
                         [scene['material_id'] for scene in self.scenes])
        self.assertEqual([b['fact_ids'] for b in result['beats']],
                         [scene['evidence_ids'] for scene in self.scenes])
        original_words=Counter(re.findall(r"[^\W\d_][\w’'-]*",self.script))
        edited_words=Counter(re.findall(r"[^\W\d_][\w’'-]*",new_text))
        self.assertFalse(edited_words-original_words,
                         'extractive rewrite must never invent or replace a word')
        self.assertEqual(original_words-edited_words,Counter(SELECTED))

    def test_only_proven_source_citation_terms_are_not_selectable(self):
        words={candidate['word'].casefold() for candidate in self.candidates}
        for required in ('дезоксирибоза','нуклеотид','комплементарності',
                         'полінуклеотидні','фосфатна'):
            self.assertNotIn(required,words)

    def test_invalid_ids_duplicate_ids_and_overlarge_deleted_text_fail(self):
        with self.assertRaises(ValueError):
            apply_extractive_omission_plan(self.scenes,
                {'remove_ids':['made-up:1']},self.candidates,self.schema,self.window)
        with self.assertRaises(NaturalDurationRejected):
            apply_extractive_omission_plan(self.scenes,
                {'remove_ids':[self.plan['remove_ids'][0]]*len(self.plan['remove_ids'])},
                self.candidates,self.schema,self.window)
        with self.assertRaises((ValueError,NaturalDurationRejected)):
            apply_extractive_omission_plan(self.scenes,
                {'remove_ids':self.plan['remove_ids'][:4]},
                self.candidates,self.schema,self.window)

    def test_model_can_only_choose_ids_and_approved_result_is_independently_reviewed(self):
        ledger=StrictLedger()
        model=RecordedGemini(ledger,plan=self.plan)
        stage=PreparationStages('/tmp',SimpleNamespace(gemini=model),lambda:None)
        context={'request':{'topic':'Молекула ДНК','language':'uk','seconds':45},
                 '_voice_correction_round':2,
                 'outputs':{'research':{'request':{'topic':'Молекула ДНК','language':'uk','seconds':45},
                                        'evidence':self.evidence},
                            'materials':{'photos':[{'id':f'photo-{i}'} for i in range(1,4)]},
                            'story':{'scenes':self.scenes,'script':self.script}}}
        def validate_story(request,evidence,photos,draft):
            return [{**scene,'narration':beat['narration']}
                    for scene,beat in zip(self.scenes,draft['beats'])]
        with patch('factory_next.preparation.validated_next_story',
                   side_effect=validate_story), \
             patch('factory_next.preparation.validate_native_surface'), \
             patch('factory_next.preparation.validate_script_review') as review:
            result=stage._revise_overlong_extractively(context,self.window)
        self.assertEqual(len(model.requests),1)
        self.assertEqual(len(model.reviews),1)
        self.assertEqual(model.reviews[0]['script'],result['script'])
        self.assertEqual(model.reviews[0]['scenes'],result['scenes'])
        self.assertEqual(len(result['script'].split()),88)
        self.assertIn('next-voice-correction:2:next-measured-extractive-deletions',
                      ledger.operations)
        self.assertIn('next-voice-correction:2:script-review',ledger.operations)
        self.assertNotIn('script-review',ledger.operations)
        review.assert_called_once()
        self.assertEqual(review.call_args.args[2],result['script'])

    def test_ambiguous_completed_plan_is_repaired_only_once_under_new_key(self):
        ledger=StrictLedger()
        model=RecordedGemini(ledger,plan=self.plan,bad_then_good=True)
        stage=PreparationStages('/tmp',SimpleNamespace(gemini=model),lambda:None)
        context={'request':{'topic':'Молекула ДНК','language':'uk','seconds':45},
                 'outputs':{'research':{'request':{'topic':'Молекула ДНК','language':'uk','seconds':45},
                                        'evidence':self.evidence},
                            'materials':{'photos':[{'id':f'photo-{i}'} for i in range(1,4)]},
                            'story':{'scenes':self.scenes,'script':self.script}}}
        with patch('factory_next.preparation.validated_next_story',
                   side_effect=lambda req,ev,photos,draft:[
                       {**s,'narration':b['narration']}
                       for s,b in zip(self.scenes,draft['beats'])]), \
             patch('factory_next.preparation.validate_native_surface'), \
             patch('factory_next.preparation.validate_script_review'):
            result=stage._revise_overlong_extractively(context,self.window)
        self.assertEqual(len(model.requests),2)
        self.assertEqual(len(model.reviews),1)
        self.assertIn('next-voice-correction:2:next-measured-extractive-deletion-repair',
                      ledger.operations)
        self.assertEqual(len(result['script'].split()),88)


if __name__ == '__main__':
    unittest.main()
