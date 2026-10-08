import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from material_first.speech_timing import record_sample, timing_budget, validate_timing
from material_first.worker import PhotoWorker

class SpeechTimingTests(unittest.TestCase):
    def setUp(self):
        self.actual=json.loads((Path(__file__).parent/'fixtures/natural-voice-regression.json').read_text())

    def sample(self, root, job='measured-case'):
        p=self.actual
        return record_sample(root,job,p['language'],p['script'],p['source_duration_ms'],p['source_audio_sha256'])

    def test_actual_51_second_narration_is_rejected_before_another_synthesis(self):
        with tempfile.TemporaryDirectory() as root:
            self.sample(root);budget=timing_budget(root,'uk',60)
            self.assertEqual(budget['preferred_words'],113)
            self.assertEqual(budget['preferred_characters'],904)
            with self.assertRaisesRegex(ValueError,'before synthesis'):
                validate_timing(self.actual['script'],budget)
            voice=Mock();worker=PhotoWorker(root,voice,'http://localhost:3001',None)
            before=Mock()
            with self.assertRaises(ValueError):
                worker.voice('fresh-case',{'language':'uk','seconds':60,'script':self.actual['script'],'speech_timing':budget}, {},before)
            voice.synthesize.assert_not_called();before.assert_not_called()

    def test_all_duration_targets_use_the_measured_voice_not_one_global_word_rate(self):
        with tempfile.TemporaryDirectory() as root:
            self.sample(root)
            for seconds in [15,30,45,60]:
                b=timing_budget(root,'uk',seconds)
                self.assertAlmostEqual(b['words_per_second'],97/50.928)
                self.assertEqual(b['preferred_words'],round((seconds-.5)*97/50.928))
            self.assertIsNone(timing_budget(root,'en',60))

    def test_measurement_is_immutable_and_not_shared_between_voices(self):
        with tempfile.TemporaryDirectory() as root:
            self.sample(root);self.sample(root)
            with self.assertRaisesRegex(ValueError,'changed'):
                p=self.actual
                record_sample(root,'measured-case','uk',p['script'],60000,p['source_audio_sha256'])
            self.assertEqual(timing_budget(root,'uk',60)['sample_count'],1)

    def test_a_completed_duration_failure_still_improves_the_next_request(self):
        with tempfile.TemporaryDirectory() as root:
            worker=PhotoWorker(root,None,'http://localhost:3001',None)
            p=self.actual
            worker._voice_measurement('failed-duration',{'language':'uk','script':p['script']},
                                      {'duration_ms':50928,'sha256':p['source_audio_sha256']})
            self.assertIsNotNone(timing_budget(root,'uk',60))

    def test_valid_word_count_cannot_hide_native_editor_shortening_the_spoken_text(self):
        from types import SimpleNamespace
        from material_first.operations import Operations,NarrationBudgetExceeded
        from factory_v3.worker_adapters import VOICES
        budget={'protocol':'natural-voice-timing-v1','locale':VOICES['uk'][0],'voice':VOICES['uk'][1],
                'sample_count':1,'words_per_second':1.9,'characters_per_second':19,
                'preferred_words':113,'preferred_characters':1130,'minimum_words':112,'maximum_words':114,
                'minimum_estimated_seconds':59,'maximum_estimated_seconds':60}
        materials=[{'id':'m'+str(i),'supported_fact_ids':['f'+str(i)]} for i in range(3)]
        beats=[{'material_id':'m'+str(i),'narration':' '.join(['пояснення']*n),'fact_ids':['f'+str(i)]}
               for i,n in enumerate([38,38,37])]
        calls=[]
        def generate(key,instruction,payload,schema):
            calls.append(key)
            if key=='material-compose':return {'beats':beats},{}
            return {'narration':[b['narration'].replace('пояснення','слово') for b in beats]},{}
        context={'request':{'language':'uk','seconds':60,'presentation_policy':'whole-photo-topic-v3',
                            'required_fact_ids':['f0','f1','f2'],'speech_timing':budget},
                 'materials':materials,'evidence':{'facts':[{'id':'f'+str(i)} for i in range(3)]}}
        with self.assertRaisesRegex(NarrationBudgetExceeded,'native edit misses'):
            Operations('.',None,SimpleNamespace(generate=generate),None,None).compose(context)
        self.assertEqual(calls,['material-compose','material-language-edit'])
