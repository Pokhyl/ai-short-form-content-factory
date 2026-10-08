import copy
import unittest
from unittest.mock import Mock
from material_first.voice_correction import POLICY, fit, validate_revision
from factory_v3.preflight import digest
from factory_v3.worker_adapters import VoiceDurationMismatch

class CorrectionTests(unittest.TestCase):
    def setUp(self):
        self.plan={'voice_correction':dict(POLICY),'seconds':60,'language':'uk',
                   'script':'original text','scenes':[{'id':'s1','narration':'original text','evidence_ids':['f1']}],
                   'assets':['immutable'],'evidence':{'facts':['immutable']}}
        self.sent=[];self.saved=[];self.rewrites=[]
    def verify(self,frozen):
        self.assertEqual(frozen['sha256'],digest(frozen['payload']))
    def correct(self,number,payload,duration):
        self.rewrites.append((number,duration))
        p=copy.deepcopy(payload);p['script']='corrected '+str(number);p['scenes'][0]['narration']=p['script']
        return {'payload':p,'sha256':digest(p)}
    def run_fit(self,durations):
        def synthesize(number,frozen):
            self.sent.append((number,frozen['payload']['script']))
            d=durations[number-1]
            if isinstance(d,Exception):raise d
            return {'duration_ms':d,'sha256':str(number)}
        return fit(self.plan,synthesize,self.correct,self.verify,lambda *args:self.saved.append(args))
    def test_actual_short_voice_is_corrected_and_final_text_matches_second_audio(self):
        result,frozen,attempts=self.run_fit([50928,59640])
        self.assertEqual(result['duration_ms'],59640)
        self.assertEqual(frozen['payload']['script'],'corrected 2')
        self.assertEqual(self.rewrites,[(2,50928)])
        self.assertEqual(len(attempts),2)
        self.assertEqual(self.plan['script'],'original text')
    def test_long_voice_can_be_corrected_twice_and_stops_at_three(self):
        with self.assertRaises(VoiceDurationMismatch):self.run_fit([74000,62000,61000,59500])
        self.assertEqual(len(self.sent),3);self.assertEqual(len(self.saved),3)
    def test_valid_first_measurement_never_calls_rewriter(self):
        self.run_fit([59000]);self.assertEqual(self.rewrites,[])
    def test_lost_response_is_not_a_duration_failure_and_is_never_retried(self):
        with self.assertRaises(TimeoutError):self.run_fit([TimeoutError(),59500])
        self.assertEqual(len(self.sent),1);self.assertEqual(self.saved,[]);self.assertEqual(self.rewrites,[])
    def test_reviewer_failure_stops_before_second_synthesis(self):
        self.correct=Mock(side_effect=ValueError('unsupported fact'))
        with self.assertRaises(ValueError):self.run_fit([50928,59500])
        self.assertEqual(len(self.sent),1)
    def test_correction_cannot_change_sources_photos_duration_language_or_fact_ids(self):
        for key,value in [('assets',[]),('evidence',{}),('seconds',51),('language','pl')]:
            changed=copy.deepcopy(self.plan);changed[key]=value
            with self.assertRaises(ValueError):validate_revision(self.plan,changed)
        changed=copy.deepcopy(self.plan);changed['scenes'][0]['evidence_ids']=[]
        with self.assertRaises(ValueError):validate_revision(self.plan,changed)
    def test_persistence_failure_stops_before_correction(self):
        sent=Mock(return_value={'duration_ms':50928,'sha256':'a'})
        correct=Mock()
        with self.assertRaises(OSError):
            fit(self.plan,sent,correct,self.verify,Mock(side_effect=OSError()))
        correct.assert_not_called();self.assertEqual(sent.call_count,1)

class WorkerCorrectionTests(unittest.TestCase):
    def test_original_attempt_bytes_retained_and_final_links_only_accepted_audio(self):
        import tempfile,uuid,hashlib
        from pathlib import Path
        from unittest.mock import patch
        from material_first.worker import PhotoWorker
        p={'voice_correction':dict(POLICY),'seconds':60,'language':'uk','script':'old',
           'scenes':[{'id':'s','narration':'old','evidence_ids':['f']}], 'assets':[], 'evidence':{}}
        updated=copy.deepcopy(p);updated['script']='new';updated['scenes'][0]['narration']='new'
        frozen={'payload':updated,'sha256':digest(updated)}
        samples=[b'original-short',b'corrected-natural']
        provider=Mock();provider.synthesize.side_effect=[('encoded',hashlib.sha256(b).hexdigest()) for b in samples]
        with tempfile.TemporaryDirectory() as root:
            worker=PhotoWorker(root,provider,'http://localhost:3001',None)
            worker._validate_scene_count=Mock();worker._stage_photos=Mock(return_value={})
            worker._voice_measurement=Mock();worker.measure_voice_revision=Mock();worker.correction_gemini=Mock()
            def post(path,body):
                i=provider.synthesize.call_count-1
                folder=Path(root)/'voiceovers'/path.split('/')[-1];folder.mkdir(parents=True)
                (folder/'final.mp3').write_bytes(samples[i])
                return {'status':'ready','sha256':hashlib.sha256(samples[i]).hexdigest(),'duration_ms':[50928,59500][i]}
            worker._post=post;account=Mock();job=str(uuid.uuid4())
            with patch('material_first.worker.verify',side_effect=lambda root,f:f['payload']),patch('material_first.voice_correction.rewrite',return_value=frozen):
                output=worker.corrected_voice(job,p,account)
            self.assertEqual(account.call_count,2)
            self.assertEqual(worker.measure_voice_revision.call_count,2)
            self.assertEqual((Path(root)/'voiceovers'/job/'attempt-1'/'final.mp3').read_bytes(),samples[0])
            self.assertEqual((Path(root)/'voiceovers'/job/'final.mp3').read_bytes(),samples[1])
            self.assertEqual(output['effective_frozen']['payload']['script'],'new')
            self.assertEqual([call.args[1] for call in provider.synthesize.call_args_list],['old','new'])

class RewriteTests(unittest.TestCase):
    def test_measured_rate_drives_new_text_and_independent_review_gets_no_old_approval(self):
        from material_first.voice_correction import rewrite
        text=' '.join(['example']*100)
        original={'voice_correction':dict(POLICY),'seconds':60,'language':'en','script':text,
                  'scenes':[{'id':'s1','narration':text,'evidence_ids':['f1']}],
                  'evidence':{'facts':[],'sources':[]},'observations':[],'script_review':{'old_approval':True}}
        revised_text=' '.join(['example']*119)
        gemini=Mock();gemini.generate.return_value=({'paragraph_1':revised_text}, {})
        gemini.review_script.return_value={'independent_review':True}
        revised=rewrite(original,50000,gemini)
        self.assertEqual(revised['payload']['script'],revised_text)
        self.assertEqual(revised['payload']['speech_timing']['words_per_second'],2)
        self.assertNotIn('script_review',gemini.review_script.call_args.args[0])
        self.assertEqual(gemini.generate.call_args.args[2]['paragraphs']['paragraph_1']['target_words'],119)
        self.assertEqual(original['script'],text)
        gemini.generate.return_value=({'paragraph_1':text}, {})
        gemini.review_script.reset_mock()
        with self.assertRaisesRegex(ValueError,'unchanged'):rewrite(original,50000,gemini)
        gemini.review_script.assert_not_called()

class FirstMeasurementTests(unittest.TestCase):
    def test_measured_feedback_can_reach_first_measurement_but_legacy_estimate_stays_strict(self):
        from material_first.speech_timing import validate_plan_timing
        p={'language':'uk','seconds':60,'script':'short', 'voice_correction':dict(POLICY),
           'speech_timing':{'protocol':'natural-voice-timing-v1','locale':'uk-UA',
            'voice':'uk-UA-Chirp3-HD-Enceladus','words_per_second':2,'characters_per_second':15,
            'minimum_estimated_seconds':59,'maximum_estimated_seconds':60}}
        validate_plan_timing(p)
        del p['voice_correction']
        with self.assertRaises(ValueError):validate_plan_timing(p)
        p['voice_correction']={'max_attempts':99}
        with self.assertRaises(ValueError):validate_plan_timing(p)
