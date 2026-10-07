import copy,json,unittest
from pathlib import Path
from types import SimpleNamespace
from material_first.operations import Operations
from material_first.engine import inspected_material
from material_first.visuals import ordered_visuals
from material_first.presentation import TOPIC_POLICY,preferred_shots
from factory_v3.gemini import validate_json
from factory_v3.grounding import validate_script_review

FIXTURE=Path(__file__).parent/'fixtures/neutron-uk60-relevance-language-failure.json'
class TopicQualityTests(unittest.TestCase):
    def setUp(self):self.saved=json.loads(FIXTURE.read_text())
    def test_saved_generic_props_cannot_be_admitted_by_positive_accepted_boolean(self):
        assets={a['id']:a for a in self.saved['assets']}
        props=[m for m in self.saved['observations'] if any(w in m['visible_description'].casefold() for w in ('molecular','plasma','atomic','dna'))]
        self.assertGreaterEqual(len(props),4)
        ops=Operations('.',None,SimpleNamespace(model='controlled'),None,None)
        facts={f['id']:f for f in self.saved['evidence']['facts']}
        for observed in props:
            row=copy.deepcopy(observed['inspection'])
            row.update(medium='photograph',topic_relation={'kind':'generic_analogy','visible_subject':observed['visible_description'],'connection':'A laboratory prop, not the requested astronomical object'})
            receipt=ops._inspection_receipt(assets[observed['id']],self.saved['evidence'],row,{'receipt_id':'controlled-reclassification'})
            self.assertFalse(receipt['accepted'])
            receipt['accepted']=True
            self.assertIsNone(inspected_material(assets[observed['id']],receipt,self.saved['evidence'],facts))
    def test_actual_related_supernova_observation_remains_eligible(self):
        observed=next(m for m in self.saved['observations'] if m['id']=='pexels:17662495')
        asset=next(a for a in self.saved['assets'] if a['id']==observed['id'])
        row=copy.deepcopy(observed['inspection'])
        row.update(medium='observational_image',topic_relation={'kind':'direct_part_or_stage','visible_subject':'Crab Nebula','connection':'Documented supernova remnant containing the Crab pulsar'})
        ops=Operations('.',None,SimpleNamespace(model='controlled'),None,None)
        receipt=ops._inspection_receipt(asset,self.saved['evidence'],row,{'receipt_id':'controlled-reclassification'})
        self.assertIsNotNone(inspected_material(asset,receipt,self.saved['evidence'],{f['id']:f for f in self.saved['evidence']['facts']}))
    def test_native_language_rejection_blocks_saved_review_that_previously_passed(self):
        review=copy.deepcopy(self.saved['script_review']);self.assertTrue(review['language_match'])
        self.assertIn('звезда',self.saved['script'])
        review['native_language_quality']=False
        with self.assertRaisesRegex(ValueError,'native-language'):
            validate_script_review(self.saved['evidence'],'uk',self.saved['script'],self.saved['scenes'],review,topic=self.saved['topic'])
    def test_saved_draft_is_proofread_once_as_paragraphs_before_independent_review(self):
        words=[];beats=[]
        for scene in self.saved['scenes']:
            start=len(words);words.extend(scene['narration'].split())
            beats.append({'material_id':scene['material_id'],'word_start':start,'word_end':len(words),'fact_ids':scene['evidence_ids'],'visual_target_id':scene['visual_target_id']})
        changes={'звезда':'зоря','звізд':'зірок','сердцевини':'серцевини','Люба':'Будь-яка','звізда':'зоря','давлення':'тиск','нейтріно':'нейтрино','осевого':'осьового'}
        calls=[]
        def generate(key,instruction,context,schema):
            calls.append(key)
            if key=='material-compose':
                result={'beats':[{k:v for k,v in b.items() if k not in ('word_start','word_end')} |
                         {'narration':' '.join(words[b['word_start']:b['word_end']])} for b in beats]}
            elif key=='material-language-edit':
                self.assertIn('Ukrainian (uk-UA)',instruction)
                result={'narration':[' '.join(changes.get(w,w) for w in text.split()) for text in context['narration']]}
            else:raise AssertionError('no unrelated provider or voice call')
            validate_json(result,schema);return result,{'receipt_id':'controlled'}
        ops=Operations('.',None,SimpleNamespace(generate=generate),None,None)
        draft=ops.compose({'request':{'seconds':60,'language':'uk','presentation_policy':TOPIC_POLICY,'visual_targets':self.saved['visual_targets']},'materials':self.saved['observations'],'evidence':self.saved['evidence']})
        text=' '.join(b['narration'] for b in draft['beats'])
        self.assertNotIn('звезда',text);self.assertNotIn('осевого',text)
        self.assertEqual(calls,['material-compose','material-language-edit'])
        self.assertEqual([b['fact_ids'] for b in draft['beats']],[b['fact_ids'] for b in beats])
    def test_topical_scheduler_refuses_unrelated_filler_and_keeps_moderate_pace(self):
        self.assertEqual(preferred_shots(60,TOPIC_POLICY),18)
        payload={'presentation_policy':TOPIC_POLICY,'seconds':15,'visuals':[{'id':str(i),'material_id':str(i)} for i in range(5)],'scenes':[{'id':'one','evidence_ids':['f1']},{'id':'two','evidence_ids':['f2']}],
            'observations':[{'id':str(i),'supported_fact_ids':(['f1'] if i<2 else ['f2']),'matched_visual_targets':{}} for i in range(5)]}
        timings=[{'start_ms':0,'end_ms':6000},{'start_ms':6000,'end_ms':15000}]
        result=ordered_visuals(payload,timings,15000)
        self.assertEqual(len(result),5);self.assertEqual(result[-1]['end_frame'],450)
        payload['observations'][-1]['supported_fact_ids']=['unrelated']
        with self.assertRaisesRegex(ValueError,'subject-related'):
            ordered_visuals(payload,timings,15000)
