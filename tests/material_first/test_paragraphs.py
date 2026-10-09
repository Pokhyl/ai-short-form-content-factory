import copy,json,unittest
from pathlib import Path
from types import SimpleNamespace
from material_first.operations import Operations,NarrationBudgetExceeded
from material_first.presentation import TOPIC_POLICY


class ParagraphTests(unittest.TestCase):
    @staticmethod
    def controlled_plan_reply(plan):
        # Structural coverage only; these tokens never claim provider prose approval.
        return {'paragraph_'+str(i+1):{
            'words':{'word_'+str(j+1):'контрольне' for j in range(p['word_budget']['preferred'])},
            'fact_ids':list(dict.fromkeys(p['required_fact_ids']+p['identifying_fact_ids']))}
            for i,p in enumerate(plan)}

    def test_actual_keyed_budget_failure_and_word_slot_controls(self):
        saved=json.loads((Path(__file__).parent/'fixtures/actual-uk60-keyed-budget-failure.json').read_text())
        from factory_v3.gemini import provider_schema
        for defect in ('saved','missing','multiword','valid'):
            calls=[]
            def generate(key,instruction,payload,schema):
                calls.append(key)
                if key=='material-compose':return copy.deepcopy(saved['draft']),{}
                if key=='material-language-edit':return {'narration':payload['narration']},{}
                plan=payload['paragraph_plan']
                compiled=provider_schema(schema)
                words=compiled['properties']['paragraph_1']['properties']['words']
                self.assertEqual(len(words['required']),plan[0]['word_budget']['preferred'])
                if defect=='saved':return copy.deepcopy(saved['failed_repair']),{}
                reply=self.controlled_plan_reply(plan)
                if defect=='missing':reply['paragraph_1']['words'].pop('word_1')
                if defect=='multiword':reply['paragraph_1']['words']['word_1']='два слова'
                return reply,{}
            ops=Operations('.',None,SimpleNamespace(generate=generate),None,None)
            with self.subTest(defect=defect):
                if defect=='valid':
                    result=ops.compose(copy.deepcopy(saved['composition_context']))
                    self.assertEqual(sum(len(b['narration'].split()) for b in result['beats']),125)
                    self.assertEqual(calls[-1],'material-language-edit')
                else:
                    with self.assertRaises(ValueError):ops.compose(copy.deepcopy(saved['composition_context']))
                    self.assertNotIn('material-language-edit',calls)

    def test_actual_rare_role_overlong_draft_uses_preverified_server_allocation(self):
        saved=json.loads((Path(__file__).parent/'fixtures/actual-uk60-rare-role-overlong.json').read_text())
        context=saved['composition_context'];calls=[]
        def generate(key,instruction,payload,schema):
            calls.append(key)
            if key=='material-compose':return saved['draft'],{}
            if key=='material-compose-length-repair':
                plan=payload['paragraph_plan']
                self.assertEqual([p['visual_target_id'] for p in plan],['v1','v2','v2'])
                self.assertEqual(set(schema['properties']),{'paragraph_1','paragraph_2','paragraph_3'})
                return self.controlled_plan_reply(plan),{}
            return {'narration':payload['narration']},{}
        result=Operations('.',None,SimpleNamespace(generate=generate),None,None).compose(context)
        self.assertEqual(calls,['material-compose','material-compose-length-repair','material-language-edit'])
        from material_first.engine import fit_contextual_paragraphs
        fit_contextual_paragraphs(context['materials'],result,seconds=60,
                                 anchor_ids=context['request']['validated_visual_anchors'].values())

    def test_actual_infeasible_anchors_can_be_regrouped_once_before_native(self):
        saved=json.loads((Path(__file__).parent/'fixtures/actual-uk60-infeasible-fixed-anchors.json').read_text())
        context=saved['composition_context']; calls=[]
        repaired={'beats':[
            {'material_id':'wikimedia:516106','visual_target_id':'v0','fact_ids':['f1','f4','f5','f6'],
             'narration':' '.join(['контрольне']*100)},
            {'material_id':'wikimedia:151097113','visual_target_id':'v1','fact_ids':['f2'],
             'narration':' '.join(['контрольне']*10)},
            {'material_id':'wikimedia:80137098','visual_target_id':'v2','fact_ids':['f8'],
             'narration':' '.join(['контрольне']*10)}]}
        # Controlled structure proves allocation only, not new native/factual provider approval.
        def generate(key,instruction,payload,schema):
            calls.append(key)
            if key=='material-compose':return copy.deepcopy(saved['draft']),{}
            if key=='material-compose-length-repair':
                self.assertIn('server-owned paragraph_plan',instruction)
                self.assertEqual(payload['cadence_guidance']['fact_photo_capacity']['f4'],0)
                return self.controlled_plan_reply(payload['paragraph_plan']),{}
            self.assertEqual(key,'material-language-edit')
            return {'narration':payload['narration']},{}
        result=Operations('.',None,SimpleNamespace(generate=generate),None,None).compose(context)
        self.assertEqual(calls,['material-compose','material-compose-length-repair','material-language-edit'])
        self.assertEqual(len(result['beats']),3)
        from material_first.engine import fit_contextual_paragraphs
        fit_contextual_paragraphs(context['materials'],result,seconds=60,
                                 anchor_ids=context['request']['validated_visual_anchors'].values())
        def failed(key,*args):
            if key=='material-compose':return copy.deepcopy(saved['draft']),{}
            if key=='material-compose-length-repair':return copy.deepcopy(saved['failed_repair']),{}
            raise AssertionError('native must not run for infeasible saved repair')
        with self.assertRaises(ValueError):
            Operations('.',None,SimpleNamespace(generate=failed),None,None).compose(context)

    def test_actual_short_draft_gets_one_bounded_source_aware_repair_before_native_edit(self):
        actual=json.loads((Path(__file__).parent/'fixtures/actual-uk60-short-paragraphs.json').read_text())
        beats=copy.deepcopy(actual['draft']['beats'])
        context=copy.deepcopy(actual['composition_context'])
        calls=[]
        def generate(key,instruction,payload,schema):
            calls.append(key)
            if key=='material-compose':return copy.deepcopy(actual['draft']),{}
            if key=='material-compose-length-repair':
                self.assertEqual(payload['completed_draft'],beats)
                self.assertEqual(payload['evidence']['facts'],context['evidence']['facts'])
                self.assertEqual(payload['cadence_guidance']['maximum_total_seconds_per_role']['v2'],5)
                self.assertIsNotNone(payload['cadence_error'])
                return self.controlled_plan_reply(payload['paragraph_plan']),{}
            self.assertEqual(key,'material-language-edit')
            self.assertEqual(set(payload),{'language','narration','word_budget'})
            return {'narration':payload['narration']},{}
        result=Operations('.',None,SimpleNamespace(generate=generate),None,None).compose(context)
        self.assertEqual(calls,['material-compose','material-compose-length-repair','material-language-edit'])
        self.assertGreaterEqual(sum(len(b['narration'].split()) for b in result['beats']),84)
        self.assertEqual(len(result['beats']),3)
        self.assertTrue({b['material_id'] for b in result['beats']} <= {m['id'] for m in context['materials']})
        self.assertTrue(set(context['request']['required_fact_ids']) <= {f for b in result['beats'] for f in b['fact_ids']})
        from material_first.engine import fit_contextual_paragraphs
        fit_contextual_paragraphs(context['materials'],result,seconds=60,
                                 anchor_ids=context['request']['validated_visual_anchors'].values())

    def test_completed_invalid_repair_is_terminal_before_native_or_voice(self):
        actual=json.loads((Path(__file__).parent/'fixtures/actual-uk60-short-paragraphs.json').read_text())
        context={'request':{'seconds':60,'language':'uk','presentation_policy':TOPIC_POLICY,
            'visual_targets':[{'id':'v'+str(i)} for i in range(3)]},
            'materials':[{'id':b['material_id']} for b in actual['draft']['beats']],
            'evidence':{'facts':actual['facts'],'sources':[]}}
        for defect in ('short','identity','provider'):
            calls=[]
            def generate(key,*args):
                calls.append(key)
                if key=='material-compose':return copy.deepcopy(actual['draft']),{}
                self.assertEqual(key,'material-compose-length-repair')
                if defect=='provider':raise RuntimeError('ambiguous provider transport')
                result=copy.deepcopy(actual['draft'])
                if defect=='identity':result['beats'][0]['material_id']=result['beats'][1]['material_id']
                return result,{}
            with self.subTest(defect=defect), self.assertRaises((ValueError,RuntimeError)):
                Operations('.',None,SimpleNamespace(generate=generate),None,None).compose(context)
            self.assertEqual(calls,['material-compose','material-compose-length-repair'])

    def test_cadence_or_required_fact_failure_after_one_repair_stops_before_native(self):
        actual=json.loads((Path(__file__).parent/'fixtures/actual-uk60-short-paragraphs.json').read_text())
        context=copy.deepcopy(actual['composition_context'])
        for defect in ('cadence','required'):
            calls=[]
            def generate(key,*args):
                calls.append(key)
                if key=='material-compose':return copy.deepcopy(actual['draft']),{}
                self.assertEqual(key,'material-compose-length-repair')
                result=copy.deepcopy(actual['draft'])
                for b,count in zip(result['beats'],(26,31,31,8)):
                    words=b['narration'].split()
                    b['narration']=' '.join((words+['контрольне']*count)[:count])
                if defect=='required':result['beats'][0]['fact_ids']=['f2']
                return result,{}
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                Operations('.',None,SimpleNamespace(generate=generate),None,None).compose(context)
            self.assertEqual(calls,['material-compose','material-compose-length-repair'])

    def setUp(self):
        saved=json.loads((Path(__file__).parent/'fixtures/neutron-uk60-92-word-failure.json').read_text())
        original=saved['drafts'][0];self.beats=[]
        for i,beat in enumerate(original['beats']):
            end=beat['word_end'] if i<len(original['beats'])-1 else len(original['words'])
            self.beats.append({k:v for k,v in beat.items() if k not in ('word_start','word_end')} |
                              {'narration':' '.join(original['words'][beat['word_start']:end])})
        self.context={'request':{'seconds':60,'language':'uk','presentation_policy':TOPIC_POLICY},
                      'materials':[{'id':b['material_id']} for b in self.beats],
                      'evidence':{'facts':saved['brief']['facts'],'sources':[]}}
        self.calls=[]

    def run_compose(self,beats=None,edited=None):
        def generate(key,instruction,context,schema):
            self.calls.append(key)
            if key=='material-compose':
                self.assertNotIn('words',schema['properties'])
                self.assertNotIn('word_start',schema['properties']['beats']['items']['properties'])
                return {'beats':copy.deepcopy(beats if beats is not None else self.beats)},{}
            if key=='material-language-edit':return {'narration':edited if edited is not None else context['narration']},{}
            raise AssertionError('no length retry or voice call')
        return Operations('.',None,SimpleNamespace(generate=generate),None,None).compose(self.context)

    def test_actual_92_word_text_preserved_without_word_array_or_length_retry(self):
        # Strip old target identities only because this narrow compiler fixture
        # does not supply targets. This is not factual/provider acceptance.
        for b in self.beats:b.pop('visual_target_id')
        result=self.run_compose()
        self.assertEqual(sum(len(b['narration'].split()) for b in result['beats']),92)
        self.assertEqual(self.calls,['material-compose','material-language-edit'])
        self.assertEqual(result['beats'],self.beats)

    def test_real_required_fact_omission_is_not_fixed_by_relaxing_length_estimate(self):
        for b in self.beats:b.pop('visual_target_id')
        self.context['request']['required_fact_ids']=['f2','f4','f5','f6']
        with self.assertRaisesRegex(ValueError,'omitted required'):self.run_compose()
        self.assertEqual(self.calls,['material-compose'])

    def test_unknown_source_fact_rejected_before_editing_or_voice(self):
        for b in self.beats:b.pop('visual_target_id')
        self.beats[0]['fact_ids']=['invented']
        with self.assertRaisesRegex(ValueError,'identity'):self.run_compose()
        self.assertEqual(self.calls,['material-compose'])

    def test_native_edit_cannot_silently_empty_or_explode_a_script(self):
        for b in self.beats:b.pop('visual_target_id')
        for edited in (["" for _ in self.beats],["word "*100 for _ in self.beats]):
            self.calls=[]
            with self.assertRaises((ValueError,NarrationBudgetExceeded)):self.run_compose(edited=edited)
            self.assertEqual(self.calls,['material-compose','material-language-edit'])

class MeasuredParagraphTests(unittest.TestCase):
    def test_feedback_plan_uses_natural_paragraphs_instead_of_individual_word_slots(self):
        from material_first.voice_correction import POLICY
        saved=json.loads((Path(__file__).parent/'fixtures/actual-uk60-keyed-budget-failure.json').read_text())
        context=copy.deepcopy(saved['composition_context']);context['request']['voice_correction']=dict(POLICY)
        calls=[]
        def generate(key,instruction,payload,schema):
            calls.append(key)
            if key=='material-compose':return copy.deepcopy(saved['draft']),{}
            if key=='material-language-edit':return {'narration':payload['narration']},{}
            self.assertIn('narration',schema['properties']['paragraph_1']['properties'])
            self.assertNotIn('words',schema['properties']['paragraph_1']['properties'])
            return {'paragraph_'+str(i+1):{'narration':' '.join(['контрольне']*(p['word_budget']['preferred']-1)),
                   'fact_ids':list(dict.fromkeys(p['required_fact_ids']+p['identifying_fact_ids']))}
                    for i,p in enumerate(payload['paragraph_plan'])},{}
        result=Operations('.',None,SimpleNamespace(generate=generate),None,None).compose(context)
        self.assertEqual(calls,['material-compose','material-compose-length-repair','material-language-edit'])
        self.assertTrue(set(context['request']['required_fact_ids'])<={f for b in result['beats'] for f in b['fact_ids']})
