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
    def test_r14_variants_reduce_only_approved_photos_to_restore_cadence(self):
        import json
        from pathlib import Path
        from material_first.voice_correction import select_paragraphs_and_visuals, validate_revision
        from material_first.visuals import preflight_visual_capacity
        saved=json.loads((Path(__file__).parent/'fixtures/r14-topical-preflight-replay.json').read_text())
        def text(words,characters):
            lengths=[1]*words;extra=characters-(2*words-1)
            for i in range(words):
                addition=min(extra,40);lengths[i]+=addition;extra-=addition
            return ' '.join('x'*length for length in lengths)
        scenes=[{**scene,'narration':text(scene['words'],scene['characters'])}
                for scene in saved['scenes']]
        observations=[{'id':photo['material_id'],'supported_fact_ids':photo['supported_fact_ids'],
                       'matched_visual_targets':{identity:True for identity in photo['target_ids']}}
                      for photo in saved['photos_in_visual_order']]
        payload={'presentation_policy':saved['presentation_policy'],'seconds':60,'scenes':scenes,
                 'script':' '.join(scene['narration'] for scene in scenes),'observations':observations,
                 'assets':[{'id':photo['material_id']} for photo in saved['photos_in_visual_order']],
                 'visuals':[{'id':'photo-'+str(i),'material_id':photo['material_id']}
                            for i,photo in enumerate(saved['photos_in_visual_order'],1)]}
        sizes=[[(27,194),(63,480),(76,610)],[(30,241),(52,418),(71,538)],
               [(24,191),(48,405),(59,508)]]
        variants=[[text(words,characters) for words,characters in paragraph] for paragraph in sizes]
        timing={'words_per_second':2.297,'characters_per_second':17.97,'selection_target_seconds':59.5}
        selected,visuals=select_paragraphs_and_visuals(payload,variants,timing)
        candidate={**payload,'visuals':visuals,
                   'scenes':[{**scene,'narration':narration}
                             for scene,narration in zip(scenes,selected)]}
        selected_ids={item['material_id'] for item in visuals}
        candidate['assets']=[item for item in payload['assets'] if item['id'] in selected_ids]
        candidate['observations']=[item for item in observations if item['id'] in selected_ids]
        self.assertEqual([(len(value.split()),len(value)) for value in selected],[(63,480),(30,241),(48,405)])
        self.assertEqual(len(visuals),12)
        self.assertEqual({item['material_id'] for item in visuals},
                         {item['material_id'] for item in payload['visuals'][:12]})
        preflight_visual_capacity(candidate)
        validate_revision(payload,candidate)
        changed={**candidate,'assets':[{'id':'invented-photo'}]+candidate['assets']}
        with self.assertRaises(ValueError):validate_revision(payload,changed)

    def test_variant_selection_prefers_best_duration_fit_that_preserves_photo_cadence(self):
        import json
        from pathlib import Path
        from material_first.voice_correction import select_paragraphs
        from material_first.visuals import preflight_visual_capacity
        saved=json.loads((Path(__file__).parent/'fixtures/r14-topical-preflight-replay.json').read_text())
        def text(words):return ' '.join(['foobar']*words)
        scenes=[{**scene,'narration':text(31)} for scene in saved['scenes']]
        observations=[{'id':photo['material_id'],'supported_fact_ids':photo['supported_fact_ids'],
                       'matched_visual_targets':{identity:True for identity in photo['target_ids']}}
                      for photo in saved['photos_in_visual_order']]
        payload={'presentation_policy':saved['presentation_policy'],'seconds':60,
                 'scenes':scenes,'script':' '.join(s['narration'] for s in scenes),
                 'observations':observations,
                 'visuals':[{'id':'photo-'+str(i),'material_id':photo['material_id']}
                            for i,photo in enumerate(saved['photos_in_visual_order'],1)]}
        variants=[[text(n) for n in values] for values in ((35,40,63),(30,54,60),(24,36,48))]
        timing={'words_per_second':2,'characters_per_second':14,'selection_target_seconds':58.5}
        selected=select_paragraphs(payload,variants,timing)
        candidate={**payload,'scenes':[{**scene,'narration':paragraph}
                                      for scene,paragraph in zip(scenes,selected)]}
        preflight_visual_capacity(candidate)
        self.assertNotEqual(len(selected[0].split()),63)

    def test_native_surface_gate_checks_selected_proofread_variant_only(self):
        from material_first.voice_correction import rewrite
        text=' '.join(['example']*100)
        original={'voice_correction':dict(POLICY),'seconds':60,'language':'uk','script':text,
                  'scenes':[{'id':'s1','narration':text,'evidence_ids':['f1']}],
                  'evidence':{'facts':[{'id':'f1','text':'The source mechanism.','support':[]}],'sources':[]},
                  'observations':[]}
        variants=[' '.join(['example']*110),
                  ' '.join(['example']*119),
                  ' '.join(['example']*140)+' густины']
        gemini=Mock();gemini.generate.side_effect=[
            ({'paragraph_1':dict(zip(('compact','balanced','expanded'),variants))},{}),
            ({'paragraph_1':variants[1]}, {})]
        gemini.review_script.return_value={'independent_review':True}
        revised=rewrite(original,50000,gemini)
        self.assertEqual(revised['payload']['scenes'][0]['narration'],variants[1])
        self.assertNotIn('густины',revised['payload']['script'])

    def test_selected_ukrainian_text_is_edited_before_independent_review(self):
        from material_first.voice_correction import proofread_selected
        bad='Електронний захоплення зупиняє стискання радіуса.'
        good='Електронне захоплення зупиняє стискання ядра.'
        payload={'language':'uk','script':bad,'scenes':[{'id':'s1','narration':bad,
            'evidence_ids':['f1']}], 'evidence':{'facts':[{'id':'f1',
            'text':'Electron capture and core collapse.'}]}}
        gemini=Mock();gemini.generate.return_value=({'paragraph_1':good},{})
        revised=proofread_selected(payload,[bad],gemini)
        self.assertEqual(revised['script'],good)
        self.assertEqual(revised['scenes'][0]['evidence_ids'],['f1'])
        self.assertIn({'id':'f1','claim':'Electron capture and core collapse.'},
                      gemini.generate.call_args.args[2]['paragraphs']['paragraph_1']['assigned_facts'])

    def test_measured_rate_drives_new_text_and_independent_review_gets_no_old_approval(self):
        from material_first.voice_correction import rewrite
        text=' '.join(['example']*100)
        original={'voice_correction':dict(POLICY),'seconds':60,'language':'en','script':text,
                  'scenes':[{'id':'s1','narration':text,'evidence_ids':['f1']}],
                  'evidence':{'facts':[{'id':'f1','text':'The source mechanism.','support':[]}],'sources':[]},'observations':[],'script_review':{'old_approval':True}}
        revised_text=' '.join(['example']*119)
        gemini=Mock();gemini.generate.side_effect=[
            ({'paragraph_1':{'compact':' '.join(['example']*105),'balanced':revised_text,'expanded':' '.join(['example']*135)}}, {}),
            ({'paragraph_1':revised_text}, {})]
        gemini.review_script.return_value={'independent_review':True}
        revised=rewrite(original,50000,gemini)
        prompt=gemini.generate.call_args_list[0].args[1]
        self.assertIn('Proofread every alternative for native grammar',prompt)
        self.assertIn('завдяки закону',prompt)
        self.assertIn('required case',prompt)
        proofread_prompt=gemini.generate.call_args_list[1].args[1]
        self.assertIn('smallest necessary changes',proofread_prompt)
        self.assertEqual(gemini.generate.call_args_list[1].args[0],'proofread')
        self.assertEqual(revised['payload']['script'],revised_text)
        self.assertEqual(revised['payload']['speech_timing']['words_per_second'],2)
        self.assertNotIn('script_review',gemini.review_script.call_args.args[0])
        self.assertEqual(gemini.generate.call_args_list[0].args[2]['paragraphs']['paragraph_1']['target_words'],119)
        self.assertEqual(gemini.generate.call_args_list[0].args[2]['paragraphs']['paragraph_1']['must_explain'],[{'id':'f1','claim':'The source mechanism.'}])
        self.assertEqual(original['script'],text)
        gemini.generate.side_effect=[({'paragraph_1':dict.fromkeys(['compact','balanced','expanded'],text)}, {})]
        gemini.review_script.reset_mock()
        with self.assertRaisesRegex(ValueError,'unchanged'):rewrite(original,50000,gemini)
        gemini.review_script.assert_not_called()

    def test_measured_overrun_calibrates_next_selection_without_weakening_actual_window(self):
        from material_first.voice_correction import rewrite
        from material_first.speech_timing import estimated_seconds
        text=' '.join(['example']*100)
        original={'voice_correction':dict(POLICY),'seconds':60,'language':'uk','script':text,
            'scenes':[{'id':'s1','narration':text,'evidence_ids':['f1']}],
            'evidence':{'facts':[{'id':'f1','text':'The source mechanism.','support':[]}],'sources':[]},
            'observations':[],
            'speech_timing':{'protocol':'natural-voice-timing-v1','locale':'uk-UA',
                'voice':'uk-UA-Chirp3-HD-Enceladus','words_per_second':100/59.5,
                'characters_per_second':len(text)/59.5,'selection_target_seconds':59.5,
                'minimum_estimated_seconds':59,'maximum_estimated_seconds':60}}
        variants=[' '.join(['example']*n) for n in (80,88,110)]
        selected=variants[1]
        gemini=Mock();gemini.generate.side_effect=[({'paragraph_1':dict(zip(
            ('compact','balanced','expanded'),variants))},{}),({'paragraph_1':selected},{})]
        gemini.review_script.return_value={'independent_review':True}
        revised=rewrite(original,63504,gemini)
        context=gemini.generate.call_args_list[0].args[2]
        self.assertEqual(context['target_seconds'],56)
        self.assertEqual(context['voice_acceptance_window_seconds'],[59,60])
        self.assertEqual(context['paragraphs']['paragraph_1']['target_words'],88)
        self.assertEqual(revised['payload']['speech_timing']['selection_target_seconds'],56)
        self.assertLess(abs(estimated_seconds(revised['payload']['script'],
            revised['payload']['speech_timing'])-56),.2)

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

class ParagraphSelectionTests(unittest.TestCase):
    def test_saved_model_overshoot_can_use_complete_paragraph_variants_without_extra_model_call(self):
        import json
        from pathlib import Path
        from material_first.voice_correction import select_paragraphs
        from material_first.speech_timing import estimated_seconds
        sample=json.loads((Path(__file__).parent/'fixtures/voice-rewrite-overshoot.json').read_text())
        original=' '.join(sample['original']);duration=sample['actual_duration_ms']/1000
        timing={'words_per_second':len(original.split())/duration,'characters_per_second':len(original)/duration}
        p={'seconds':60,'scenes':[{'narration':t} for t in sample['original']]}
        selected=select_paragraphs(p,sample['proposed'],timing)
        self.assertGreater(estimated_seconds(' '.join(sample['proposed']),timing),72)
        self.assertAlmostEqual(estimated_seconds(' '.join(selected),timing),59.814,places=3)
        self.assertEqual(selected,[sample['original'][0],sample['proposed'][1],sample['proposed'][2]])
        for i,text in enumerate(selected):self.assertIn(text,[sample['original'][i],sample['proposed'][i]])

class VariantSelectionTests(unittest.TestCase):
    def test_complete_new_variants_are_selected_without_reusing_old_generic_paragraph(self):
        from material_first.voice_correction import select_paragraphs
        p={'seconds':15,'scenes':[{'narration':'old unsupported filler'}]}
        variants=[' '.join(['mechanism']*n) for n in (20,29,40)]
        selected=select_paragraphs(p,[variants],{'words_per_second':2,'characters_per_second':20})
        self.assertEqual(selected,[variants[1]])
        with self.assertRaises(ValueError):
            select_paragraphs(p,[variants+['extra']],{'words_per_second':2,'characters_per_second':20})
