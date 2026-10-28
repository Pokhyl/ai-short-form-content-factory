"""Adaptive correction from a completed, too-short response; no provider calls."""
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from factory_next.duration import revision_length_window
from factory_next.voice_length_repair import (
    sentence_contract, adaptive_underlength_sentence_contract,
    assemble_sentence_repair,
)
from factory_next.preparation import PreparationStages
from factory_v3.gemini import provider_schema


def measured_window():
    script=('слово '*99).strip().ljust(728,'.')
    return script,revision_length_window(script,53904,60)


def scenes():
    return [{'id':f'b{i}','material_id':f'p{i}',
             'evidence_ids':[f'f{i}'],'narration':f'Original reviewed scene {i}.'}
            for i in range(1,4)]


def first_short_reply(schema):
    sentences=[]
    for i in range(10):
        words="Цей опис пов'язує подію з перевіреним свідченням номер "+str(i)+"."
        if i==0:
            words="Цей достовірний опис пов'язує подію з перевіреним свідченням номер 0."
        sentences.append(words)
    answer={};index=0
    for beat,row in schema['properties'].items():
        answer[beat]={}
        for field in row['required']:
            answer[beat][field]=sentences[index];index+=1
    return answer


class DynamicUnderlengthSchemaTests(unittest.TestCase):
    def test_actual_60_second_shortfall_changes_second_claim_not_first(self):
        script,window=measured_window()
        self.assertEqual((len(script.split()),len(script)),(99,728))
        self.assertEqual((window['target_words'],window['min_words'],window['max_words']),
                         (109,102,116))
        first,first_counts=sentence_contract(scenes(),window)
        self.assertEqual(first_counts,[4,3,3])
        reply=first_short_reply(first)
        self.assertEqual(sum(len(v.split()) for row in reply.values() for v in row.values()),91)
        second,counts=adaptive_underlength_sentence_contract(
            reply,first,scenes(),window)
        self.assertEqual(counts,[4,4,4])
        self.assertEqual(sum(len(x['properties']) for x in second['properties'].values()),12)
        for beat in second['properties'].values():
            for spec in beat['properties'].values():
                self.assertIn('description',provider_schema(spec))
                self.assertNotIn('minLength',provider_schema(spec))
                self.assertIn('fact-grounded',spec['description'])
        with self.assertRaises(ValueError):
            assemble_sentence_repair(reply,first,scenes(),window)

    def test_real_reply_can_drive_all_topics_and_durations(self):
        for topic in ("coral reef","history of computing","bee pollination"):
            for target in (24,45,68,109,139):
                with self.subTest(topic=topic,target=target):
                    win={'target_words':target,'target_characters':round(target*7.4),
                         'min_words':round(target*.92),'max_words':round(target*1.07),
                         'min_characters':round(target*6.7),
                         'max_characters':round(target*8.1)}
                    first,_=sentence_contract(scenes(),win)
                    count=sum(len(row['required']) for row in first['properties'].values())
                    short={beat:{field:f'A real observable topic fact {i} in context.'
                        for i,field in enumerate(row['required'])}
                        for beat,row in first['properties'].items()}
                    second,new_counts=adaptive_underlength_sentence_contract(
                        short,first,scenes(),win)
                    if new_counts:
                        self.assertGreater(sum(new_counts),count)
                        self.assertLessEqual(sum(new_counts),min(32,count+max(2,(count+1)//2)))
                    else:
                        self.assertEqual(second,first)

    def test_invalid_or_duplicate_completed_reply_never_becomes_approved_text(self):
        _,window=measured_window()
        schema,_=sentence_contract(scenes(),window)
        original=first_short_reply(schema)
        for bad in ({}, {'beat_1':{}}, {key:{name:'Repeated identical sentence.'
                     for name in row} for key,row in original.items()}):
            with self.subTest(bad=repr(bad)[:15]):
                candidate,counts=adaptive_underlength_sentence_contract(
                    bad,schema,scenes(),window)
                self.assertIsNone(counts)
                self.assertEqual(candidate,schema)

    def test_second_correction_uses_new_schema_but_first_request_is_unchanged(self):
        script,window=measured_window()
        story={'script':script,'scenes':scenes(),'review':{'native_language_quality':True}}
        class Provider:
            def __init__(self):
                self.calls=object()
                self.keys=[]
                self.schemas=[]
                self.reviews=0
            def generate(self,key,instruction,inputs,schema, **kwargs):
                if kwargs: assert kwargs == {'max_tokens':16384,'thinking_level':'medium'}
                self.keys.append(key);self.schemas.append(deepcopy(schema))
                if len(self.keys)==1:
                    return first_short_reply(schema),{}
                if len(self.keys)==2:
                    # Deliberately repeat the old response: it must still fail.
                    old,_=sentence_contract(scenes(),window)
                    return first_short_reply(old),{}
                raise AssertionError('unbudgeted third provider call')
            def review_script(self,*args):
                self.reviews+=1
                raise AssertionError('invalid narration must not be reviewed')
        provider=Provider()
        stage=PreparationStages('/tmp',SimpleNamespace(gemini=provider),lambda:None)
        context={'request':{'topic':'Generic historical subject','language':'uk','seconds':60},
            '_voice_correction_round':2,
            'outputs':{
                'research':{'request':{'topic':'Generic historical subject',
                                       'language':'uk','seconds':60},
                            'evidence':{'facts':[{'id':f'f{i}'} for i in range(1,4)]}},
                'materials':{'photos':[{'id':f'p{i}'} for i in range(1,4)]},
                'story':story}}
        with patch('factory_next.preparation.compact_materials',return_value=[]):
            with self.assertRaises(ValueError):
                stage.revise_story(context,53904)
        self.assertEqual(provider.keys,[
            'next-measured-duration-revision',
            'next-measured-duration-structured-repair'])
        self.assertEqual(sum(len(r['properties']) for r in provider.schemas[0]['properties'].values()),10)
        self.assertEqual(sum(len(r['properties']) for r in provider.schemas[1]['properties'].values()),12)
        self.assertEqual(provider.reviews,0)


if __name__=="__main__":
    unittest.main()
