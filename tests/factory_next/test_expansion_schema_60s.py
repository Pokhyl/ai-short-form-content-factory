"""Measured long-form underlength calibration without unreviewed TTS."""
from copy import deepcopy
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from factory_next.duration import revision_length_window
from factory_next.voice_length_repair import sentence_contract,assemble_sentence_repair
from factory_next.preparation import PreparationStages
from factory_v3.gemini import provider_schema


def window_from_archived_measurement():
    # Matches observed 99-word / 728-character UK60 script and 53,904ms
    # measured MP3. No actual provider output, secrets or external calls.
    script=('слово '*99).strip().ljust(728,'.')
    return revision_length_window(script,53904,60)


class ExpansionContractTests(TestCase):
    def test_long_underlength_uses_observed_natural_words_per_sentence(self):
        window=window_from_archived_measurement()
        self.assertEqual((window['target_words'],window['min_words'],window['max_words']),
                         (109,102,116))
        scenes=[{'id':f'beat-{i}','material_id':f'photo-{i}',
                 'evidence_ids':[f'fact-{i}'],'narration':'fact'} for i in range(1,4)]
        default, old_counts=sentence_contract(scenes,window)
        actual, counts=sentence_contract(scenes,window,measured_expansion=True)
        self.assertEqual(old_counts,[4,3,3])
        self.assertEqual(counts,[4,4,4])
        self.assertEqual(len(actual['properties']),3)
        for beat,row in actual['properties'].items():
            for column in row['properties'].values():
                self.assertIn('description',column)
                self.assertIn('fact-grounded',column['description'])
                self.assertGreater(column['minLength'],0)
                sent=provider_schema(column)
                self.assertIn('description',sent)
                self.assertNotIn('minLength',sent)
                self.assertNotIn('maxLength',sent)
        self.assertEqual([scene['material_id'] for scene in scenes],
                         ['photo-1','photo-2','photo-3'])

    def test_shorter_windows_preserve_existing_calibration(self):
        scenes=[{'material_id':f'p{i}','evidence_ids':[f'f{i}'],
                 'narration':'original'} for i in range(3)]
        for target in (24,47,89,99):
            window={'target_words':target,'target_characters':target*8}
            self.assertEqual(sentence_contract(scenes,window)[1],
                             sentence_contract(scenes,window,measured_expansion=True)[1])

    def test_unreviewed_archived_short_reply_remains_rejected(self):
        window=window_from_archived_measurement()
        scenes=[{'id':f'b{i}','material_id':f'p{i}',
                 'evidence_ids':[f'f{i}'],'narration':'original'} for i in range(3)]
        schema,_=sentence_contract(scenes,window,measured_expansion=True)
        old_reply={'beat_1':{f'sentence_{j}':'Short documented statement.'
                             for j in range(1,5)},
                   'beat_2':{f'sentence_{j}':'Another short statement.'
                             for j in range(1,4)},
                   'beat_3':{f'sentence_{j}':'Yet another short statement.'
                             for j in range(1,4)}}
        with self.assertRaises(ValueError):
            assemble_sentence_repair(old_reply,schema,scenes,window)

    def test_underlong_stage_requests_twelve_fields_before_source_review(self):
        window=window_from_archived_measurement()
        script=('слово '*99).strip().ljust(728,'.')
        scenes=[{'id':f'b{i}','material_id':f'p{i}',
                 'evidence_ids':[f'f{i}'],'narration':script[i*50:(i+1)*50]}
                for i in range(3)]
        story={'script':script,'scenes':scenes,'review':{'native_language_quality':True}}
        class Provider:
            def __init__(self):
                self.calls=[]
                self.reviews=0
                self.calls_obj=object()
            @property
            def calls(self):return self._calls
            @calls.setter
            def calls(self,value):
                if isinstance(value,list):self._calls=value
                else:self.calls_obj=value
            def generate(self,key,prompt,inputs,schema):
                self._calls.append((key,deepcopy(schema)))
                # Returned body is an old ten-field form, deliberately
                # not accepted as a twelve-field source-grounded correction.
                old_schema,_=sentence_contract(scenes,window)
                old={beat:{name:'A short but complete sentence on the subject.'
                           for name in row['required']}
                     for beat,row in old_schema['properties'].items()}
                return old,{}
            def review_script(self,*args):
                self.reviews+=1
                raise AssertionError('invalid correction must not be reviewed')
        model=Provider()
        # This stage requires .calls to be swappable; use a minimal object
        # with its own call recorder, not provider/network objects.
        class CallsRecorder:
            def __init__(self):self.requests=[]
            def run(self,*args):raise AssertionError('no network ledger calls')
        model.calls=CallsRecorder()
        stage=PreparationStages('/tmp',SimpleNamespace(gemini=model),lambda:None)
        context={'request':{'topic':'Unrelated documented subject','language':'uk','seconds':60},
            '_voice_correction_round':2,
            'outputs':{
                'research':{'request':{'topic':'Unrelated documented subject',
                                       'language':'uk','seconds':60},
                            'evidence':{'facts':[{'id':f'f{i}'} for i in range(3)]}},
                'materials':{'photos':[{'id':f'p{i}'} for i in range(3)]},
                'story':story}}
        with patch('factory_next.preparation.compact_materials',return_value=[]):
            with self.assertRaises(ValueError):
                stage.revise_story(context,53904)
        self.assertEqual([x[0] for x in model._calls],
            ['next-measured-duration-revision','next-measured-duration-structured-repair'])
        self.assertEqual(model.reviews,0)
        self.assertEqual(sum(len(row['properties']) for row in
            model._calls[0][1]['properties'].values()),12)