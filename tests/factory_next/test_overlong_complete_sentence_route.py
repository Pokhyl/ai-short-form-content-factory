"""Overlong voice revisions preserve grammatical units, then require review."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from factory_next.preparation import PreparationStages
from factory_next.duration import revision_length_window
from factory_next.voice_length_repair import sentence_contract


class RealDurationOverlongContract(unittest.TestCase):
    def test_measured_long_mp3_uses_complete_sentence_contract_not_word_deletions(self):
        script=('дані '*135).strip().ljust(959,'.')
        self.assertEqual((len(script.split()),len(script)),(135,959))
        scenes=[{'id':f'beat-{i}','material_id':f'photo-{i}',
                 'evidence_ids':[f'fact-{i}'],'narration':'Original reviewed description.'}
                for i in (1,2,3)]
        window=revision_length_window(script,69288,60)
        self.assertEqual((window['min_words'],window['max_words']),(109,123))
        self.assertEqual((window['min_characters'],window['max_characters']),(758,890))
        expected_schema,count=sentence_contract(scenes,window)
        self.assertEqual(sum(count),11)

        class Provider:
            def __init__(self):
                self.calls=object()
                self.keys=[]
                self.reviews=[]
            def generate(self,key,instruction,data,schema):
                self.keys.append(key)
                self.schema=schema
                # Unique whole sentences. The independent review is mocked
                # here only to test the orchestration, never claim QA success.
                i=0;result={}
                for beat,row in schema['properties'].items():
                    result[beat]={}
                    for field in row['required']:
                        i+=1
                        result[beat][field]=' '.join(['важливе']*9+[f'дані{i}.'])
                return result,{}
            def review_script(self,data):
                self.reviews.append(data)
                return {'native_language_quality':True}
        provider=Provider()
        stage=PreparationStages('/tmp',SimpleNamespace(gemini=provider),lambda:None)
        context={
            '_voice_correction_round':2,
            'request':{'topic':'General documented subject','language':'uk','seconds':60},
            'outputs':{
                'research':{'request':{'topic':'General documented subject',
                     'language':'uk','seconds':60},
                     'evidence':{'facts':[{'id':f'fact-{i}'} for i in (1,2,3)]}},
                'materials':{'photos':[{'id':f'photo-{i}'} for i in (1,2,3)]},
                'story':{'scenes':scenes,'script':script}}}
        def bind(req, evidence, photos, raw):
            return [{'id':f'beat-{i}','material_id':beat['material_id'],
                     'evidence_ids':beat['fact_ids'],'narration':beat['narration']}
                    for i,beat in enumerate(raw['beats'],1)]
        with patch('factory_next.preparation.validated_next_story',side_effect=bind),\
             patch('factory_next.preparation.validate_native_surface'),\
             patch('factory_next.preparation.validate_script_review') as checker,\
             patch.object(stage,'_revise_overlong_extractively',
                          side_effect=AssertionError('unsafe word deletions forbidden')):
            result=stage.revise_story(context,69288)
        self.assertEqual(provider.keys,['next-measured-duration-revision'])
        self.assertEqual(len(provider.reviews),1)
        self.assertEqual(result['script'],provider.reviews[0]['script'])
        self.assertEqual(len(result['scenes']),3)
        self.assertEqual([x['material_id'] for x in result['scenes']],
                         ['photo-1','photo-2','photo-3'])
        self.assertTrue(109<=len(result['script'].split())<=123)
        self.assertTrue(758<=len(result['script'])<=890)
        checker.assert_called_once()

    def test_old_extractively_repaired_script_was_not_accepted_without_review(self):
        # Direct test of route: a short fake response is not accepted just
        # because it has valid JSON; independent checked text remains required.
        script=('дані '*135).strip().ljust(959,'.')
        scenes=[{'id':f'beat-{i}','material_id':f'p{i}',
                 'evidence_ids':[f'f{i}'],'narration':'Source scene.'}
                for i in (1,2,3)]
        class Provider:
            def __init__(self):self.calls=object();self.keys=[];self.review_count=0
            def generate(self,key,instruction,data,schema):
                self.keys.append(key)
                # No valid full sentences: no reviewer nor TTS may see this.
                return {beat:{field:'Short.' for field in row['required']}
                        for beat,row in schema['properties'].items()},{}
            def review_script(self,*args):
                self.review_count+=1
                raise AssertionError('must not review garbage')
        provider=Provider()
        stage=PreparationStages('/tmp',SimpleNamespace(gemini=provider),lambda:None)
        context={
            '_voice_correction_round':2,
            'request':{'topic':'Any topic','language':'uk','seconds':60},
            'outputs':{'research':{'request':{'topic':'Any topic','language':'uk','seconds':60},
                       'evidence':{'facts':[{'id':f'f{i}'} for i in (1,2,3)]}},
                       'materials':{'photos':[{'id':f'p{i}'} for i in (1,2,3)]},
                       'story':{'script':script,'scenes':scenes}}}
        with patch('factory_next.preparation.compact_materials',return_value=[]):
            with self.assertRaises(ValueError):
                stage.revise_story(context,69288)
        self.assertEqual(len(provider.keys),2)
        self.assertEqual(provider.review_count,0)


if __name__=="__main__":
    unittest.main()