"""Long generated story repairs only narration, preserving source/photo identities.

Factory Next production observation: 228 words for a 60s request and a
misplaced quote from beat 2 cited as beat 3. A revised story must still pass
the independent exact-scene reviewer before any voice synthesis.
"""
from copy import deepcopy
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from factory_next.preparation import PreparationStages


def first_story(words_per_beat):
    return {'beats':[
        {'material_id':f'p{i}','fact_ids':[f'f{i}'],
         'narration':' '.join([f'розповідь{i}']*words_per_beat)+'.'}
        for i in (1,2,3)]}


class Model:
    def __init__(self,initial,revision):
        self.initial=initial
        self.revision=revision
        self.calls=[]
        self.review_requests=[]
    def generate(self,key,instruction,context,schema):
        self.calls.append((key,instruction,deepcopy(schema)))
        if key=='next-story':
            return deepcopy(self.initial),{'cached':True}
        if key.startswith('next-story-length-repair:'):
            assert set(schema['properties'])=={'beat_1','beat_2','beat_3'}
            fields=[(beat,sentence) for beat,row in schema['properties'].items()
                    for sentence in row['required']]
            total=context['target_words']
            if key.endswith(':1') and self.revision.get('over_limit'):
                per_sentence=15
            else:
                per_sentence=total//len(fields)
            output={beat:{} for beat in schema['required']}
            words=['Дослідження','підтверджує','збережені','історичні',
                   'матеріали','свідчення','незалежних','архівів','важливому',
                   'контексті','документовані','обставини','подальші',
                   'події','розвитку','системи']
            for index,(beat,sentence) in enumerate(fields):
                count=per_sentence+(1 if not self.revision.get('over_limit')
                    and index<total%len(fields) else 0)
                output[beat][sentence]=' '.join(
                    (words[:count-1]+[f'джерело{index}.']))
            return output,{'cached':True}
        raise AssertionError('unbudgeted story call '+key)
    def review_script(self,request):
        self.review_requests.append(deepcopy(request))
        return {'native_language_quality':True}


def context(seconds,topic):
    return {'request':{'language':'uk','topic':topic,'seconds':seconds},
        'outputs':{
            'research':{'request':{'language':'uk','topic':topic,'seconds':seconds,
                                   'required_fact_ids':['f1','f2','f3']},
                'evidence':{'facts':[{'id':f'f{i}'} for i in (1,2,3)]}},
            'materials':{'photos':[{'id':f'p{i}'} for i in (1,2,3)]}}}


def validated(req,evidence,photos,draft):
    return [{'id':f'beat-{i}','material_id':beat['material_id'],
             'evidence_ids':list(beat['fact_ids']), 'narration':beat['narration']}
            for i,beat in enumerate(draft['beats'],1)]


class StoryDurationRegressions(TestCase):
    def test_oversized_story_rewrites_only_text_then_reviews_exact_result(self):
        for seconds,topic in [(15,'пчелы'),(30,'history of coral'),(45,'молекули'),(60,'видатні науковці')]:
            with self.subTest(seconds=seconds,topic=topic):
                first=first_story(round(seconds*1.27))
                words=round(seconds*2.1/3)
                repair={f'beat_{i}':' '.join(['цілісний']*words)+'.'
                        for i in (1,2,3)}
                self.assertGreater(
                    sum(len(b['narration'].split()) for b in first['beats']),
                    round(seconds*2.5))
                model=Model(first,repair)
                stage=PreparationStages('/tmp',SimpleNamespace(gemini=model,
                    review_script=model.review_script),lambda:None)
                with patch('factory_next.preparation.validated_next_story',side_effect=validated), \
                     patch('factory_next.preparation.validate_native_surface'), \
                     patch('factory_next.preparation.validate_script_review') as check, \
                     patch('factory_next.preparation.compact_materials',return_value=[]):
                    result=stage.story(context(seconds,topic))
                self.assertEqual([key for key,_,_ in model.calls],
                                 ['next-story','next-story-length-repair:1'])
                self.assertEqual([s['material_id'] for s in result['scenes']],['p1','p2','p3'])
                self.assertEqual([s['evidence_ids'] for s in result['scenes']],
                                 [['f1'],['f2'],['f3']])
                self.assertLessEqual(len(result['script'].split()),round(seconds*2.5))
                self.assertEqual(model.review_requests[0]['script'],result['script'])
                check.assert_called_once()

    def test_oversized_first_repair_gets_one_smaller_repair_then_review(self):
        first=first_story(76)
        model=Model(first,{'over_limit':True})
        stage=PreparationStages('/tmp',SimpleNamespace(gemini=model,
            review_script=model.review_script),lambda:None)
        with patch('factory_next.preparation.validated_next_story',side_effect=validated), \
             patch('factory_next.preparation.validate_native_surface'), \
             patch('factory_next.preparation.validate_script_review'), \
             patch('factory_next.preparation.compact_materials',return_value=[]):
            result=stage.story(context(60,'unrelated topic'))
        self.assertEqual([key for key,_,_ in model.calls],[
            'next-story','next-story-length-repair:1','next-story-length-repair:2'])
        self.assertEqual(sum(len(row['required']) for row in model.calls[1][2]['properties'].values()),12)
        self.assertEqual(sum(len(row['required']) for row in model.calls[2][2]['properties'].values()),9)
        self.assertLessEqual(len(result['script'].split()),150)
        self.assertEqual(model.review_requests[0]['script'],result['script'])

    def test_normal_story_does_not_consume_extra_model_call(self):
        normal=first_story(33)
        model=Model(normal,{})
        stage=PreparationStages('/tmp',SimpleNamespace(gemini=model,
            review_script=model.review_script),lambda:None)
        with patch('factory_next.preparation.validated_next_story',side_effect=validated), \
             patch('factory_next.preparation.validate_native_surface'), \
             patch('factory_next.preparation.validate_script_review'), \
             patch('factory_next.preparation.compact_materials',return_value=[]):
            result=stage.story(context(60,'ordinary topic'))
        self.assertEqual([key for key,_,_ in model.calls],['next-story'])
        self.assertEqual(len(result['scenes']),3)