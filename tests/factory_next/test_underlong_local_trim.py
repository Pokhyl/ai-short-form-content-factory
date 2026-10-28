"""Offline regression for real underlong 39.936s Ukrainian DNA recording.

The completed Gemini revision had correct source-grounded content but
95 words/735 chars, violating the strict 85..95/616..724 bounds.
Remove only generic modifiers and independently review the exact text.
No real provider call, no TTS, no persistent job replay.
"""
import re
import unittest
from collections import Counter
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from factory_next.duration import revision_length_window, revision_length_fits, NaturalDurationRejected
from factory_next.voice_length_repair import (
    sentence_contract, trim_complete_expansion_locally)
from factory_next.preparation import PreparationStages


SENTENCES={
  'beat_1':{
    'sentence_1':'Молекула ДНК є довгим полімером, що складається з багатьох повторюваних нуклеотидів.',
    'sentence_2':'Кожен такий блок включає азотисту основу, цукор дезоксирибозу та фосфатну групу.',
    'sentence_3':'Ці нуклеотиди формують хімічний склад цієї надзвичайно важливої для всього життя молекули.'},
  'beat_2':{
    'sentence_1':'Більшість організмів мають ДНК у формі подвійної спіралі з двох ланцюгів.',
    'sentence_2':"Вони надійно з'єднані водневими зв'язками між комплементарними основами у стабільну структуру.",
    'sentence_3':'При цьому аденін завжди розташований навпроти тиміну, а гуанін — навпроти комплементарного цитозину.'},
  'beat_3':{
    'sentence_1':'Головними функціями ДНК є тривале зберігання генетичних відомостей та їх передача наступним поколінням.',
    'sentence_2':'Також вона виступає матрицею для синтезу РНК, забезпечуючи важливі біологічні процеси біосинтезу білків.'}
}
FACTS=[
    {'id':'fact-1','text':'Молекула ДНК — це довгий полімер, що складається з повторюваних нуклеотидів, кожен з яких включає азотисту основу, цукор дезоксирибозу та фосфатну групу.'},
    {'id':'fact-2','text':"ДНК у більшості організмів має структуру подвійної спіралі, де два антипаралельні ланцюги з'єднані водневими зв'язками між комплементарними азотистими основами: аденін — з тиміном, а гуанін — з цитозином."},
    {'id':'fact-3','text':'Основними біологічними функціями ДНК є тривале зберігання генетичної інформації, її передача наступним поколінням під час реплікації та використання як матриці для синтезу РНК і білків.'}
]


class FakeGemini:
    def __init__(self,drafts):
        self.drafts=list(drafts);self.requests=[];self.reviews=[];self.calls=object()
    def generate(self,key,instruction,context,schema, **kwargs):
        if kwargs: assert kwargs == {'max_tokens':16384,'thinking_level':'medium'}
        self.requests.append((key,instruction,context,schema))
        if not self.drafts:raise AssertionError('unexpected provider request')
        return deepcopy(self.drafts.pop(0)),{'cached':True}
    def review_script(self,request):
        self.reviews.append(deepcopy(request))
        return {'native_language_quality':True}


class UnderlongLocalTrimTests(unittest.TestCase):
    def setUp(self):
        # Original recording: 81 words, 601 chars, 39.936 seconds.
        original=' '.join(['ДНК']*81).ljust(601,'.')
        self.scenes=[{'id':f'beat-{i}','material_id':f'p{i}',
                      'evidence_ids':[f'fact-{i}'],'narration':original}
                     for i in range(1,4)]
        self.source=original
        self.evidence={'facts':deepcopy(FACTS)}
        self.window=revision_length_window(original,39936,45)
        self.schema,_=sentence_contract(self.scenes,self.window)

    def test_archived_completed_repair_is_bounded_without_rewrite(self):
        result=trim_complete_expansion_locally(
            SENTENCES,self.schema,self.scenes,self.evidence,self.window)
        text=' '.join(beat['narration'] for beat in result['beats'])
        old=' '.join(v for row in SENTENCES.values() for v in row.values())
        self.assertEqual((len(old.split()),len(old)),(95,735))
        self.assertEqual((len(text.split()),len(text)),(90,692))
        self.assertTrue(revision_length_fits(text,self.window))
        old_words=Counter(re.findall(r"[^\W\d_][\w’'-]*",old))
        new_words=Counter(re.findall(r"[^\W\d_][\w’'-]*",text))
        self.assertFalse(new_words-old_words)
        self.assertEqual([beat['material_id'] for beat in result['beats']],['p1','p2','p3'])
        self.assertEqual([beat['fact_ids'] for beat in result['beats']],
                         [['fact-1'],['fact-2'],['fact-3']])
        for phrase in ('азотисту основу','дезоксирибозу','водневими зв’язками',
                       'комплементарними','генетичних відомостей'):
            self.assertIn(phrase.replace('’',"'"),text)

    def test_cannot_silently_pad_underlength_draft(self):
        too_short=deepcopy(SENTENCES)
        too_short['beat_3']['sentence_2']='ДНК зберігає генетичну інформацію у клітинах.'
        with self.assertRaises((ValueError,NaturalDurationRejected)):
            trim_complete_expansion_locally(
                too_short,self.schema,self.scenes,self.evidence,self.window)

    def test_completed_local_trim_passes_through_exact_independent_review(self):
        invalid=deepcopy(SENTENCES)
        invalid['beat_3']['sentence_1']+=' Дуже довге!'
        fake=FakeGemini([invalid,SENTENCES])
        stage=PreparationStages('/tmp',SimpleNamespace(gemini=fake),lambda:None)
        context={'request':{'topic':'Молекула ДНК','language':'uk','seconds':45},
                 '_voice_correction_round':2,
                 'outputs':{
                     'research':{'request':{'topic':'Молекула ДНК','language':'uk','seconds':45},
                                 'evidence':self.evidence},
                     'materials':{'photos':[{'id':f'p{i}'} for i in range(1,4)]},
                     'story':{'script':self.source,'scenes':self.scenes}}}
        def validated_story(request,evidence,photos,draft):
            return [{**s,'narration':row['narration']} for s,row in zip(self.scenes,draft['beats'])]
        with patch('factory_next.preparation.validated_next_story',
                   side_effect=validated_story), \
             patch('factory_next.preparation.validate_native_surface'), \
             patch('factory_next.preparation.validate_script_review') as review:
            output=stage.revise_story(context,39936)
        self.assertEqual(len(fake.requests),2)
        self.assertEqual([x[0] for x in fake.requests],
                         ['next-measured-duration-revision',
                          'next-measured-duration-structured-repair'])
        self.assertEqual(len(fake.reviews),1)
        self.assertEqual(fake.reviews[0]['script'],output['script'])
        self.assertEqual((len(output['script'].split()),len(output['script'])),(90,692))
        review.assert_called_once()


if __name__ == '__main__':
    unittest.main()
