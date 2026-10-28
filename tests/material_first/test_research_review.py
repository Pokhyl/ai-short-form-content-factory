import copy
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from factory_v3.gemini import obj,array,string
from material_first.research_review import reviewed_brief, _focused_literal_source_quotes
from material_first.photo_contexts import validate_search_hints
from material_first.source_spans import source_spans

class ResearchReviewTests(unittest.TestCase):
    def setUp(self):
        saved=json.loads((Path(__file__).parent/'fixtures/actual-semantic-brief.json').read_text())
        self.draft,self.sources=saved['draft'],saved['sources'];self.spans=source_spans(self.sources)
        self.schema=obj({'facts':array(obj({'id':string(),'text':string(),'support':array(obj({'span_id':string()}),1,3)}),3,8),
            'required_fact_ids':array(string(),3,3),'photo_contexts':obj({role:obj({'english_photo_object':string(),'source_mention':string(),'support_span_ids':array(string(),1,3),'fact_ids':array(string(),1,8)}) for role in self.draft['photo_contexts']})})
        self.calls=[]
    def run_case(self, generate):
        def record(key,*args):self.calls.append(key);return generate(key,*args)
        return reviewed_brief(SimpleNamespace(generate=record),{'topic':'Нейтронная звезда','seconds':60,'language':'uk'},self.sources,self.spans,self.schema,copy.deepcopy(self.draft))
    def review(self, context, supported=True):
        return {'facts':{f['id']:{'supported':supported,'reason':'Check mass qualifier against quoted source'} for f in context['facts']},
            'photo_contexts':{role:{'source_supported':True,'observable_object':supported,'reason':'A hidden interior cannot be shown by a real photo'} for role in context['photo_contexts']}}
    def test_repair_gets_actual_quote_ids_without_inventing_absent_name(self):
        malformed=copy.deepcopy(self.draft)
        malformed['photo_contexts']['setting']['source_mention']='вигадана точна цитата'
        # The prior citations and actual fetched sources remain the authority.
        real_quotes=_focused_literal_source_quotes(malformed,self.spans)
        self.assertTrue(real_quotes)
        ids={span['id']:span for span in self.spans}
        for entry in real_quotes:
            self.assertIn(entry['span_id'],ids)
            self.assertEqual(entry['literal_source_excerpt'],ids[entry['span_id']]['text'][:1200])
        seen=[]
        def fake_generate(key,instruction,context,schema):
            seen.append((key,context))
            self.assertIn(key,('material-brief-repair:review:1','material-brief-repair:review:2'))
            self.assertTrue(context['focused_literal_source_quotes'])
            self.assertIn('selected source span does not contain',context['failures'][0])
            self.assertEqual(set(schema['required']),{'photo_contexts'})
            contexts=copy.deepcopy(malformed['photo_contexts'])
            for row in contexts.values():
                row.pop('fact_ids',None)
            return {'photo_contexts':contexts},{}
        with self.assertRaisesRegex(ValueError,'after 2 revisions'):
            reviewed_brief(SimpleNamespace(generate=fake_generate),
                           {'topic':'Нейтронная звезда'},self.sources,self.spans,
                           self.schema,malformed,check_photos=False)
        self.assertEqual(len(seen),2)

    def test_source_excerpt_keeps_literal_mention_at_end_of_bounded_span(self):
        # A real DNA45 failure cited "ядро клітини" absent from the source.
        # The Russian source actually says "в ядре клетки" near the END
        # of a 1055-character span. The old 950-character excerpt dropped it.
        span={'id':'s1-0-1055','source_id':'source-1','start':0,'end':1055,
              'text':('ДНК: источник. '+('Проверенные сведения. '*44)+
                      ' В клетках эукариотов ДНК находится в ядре клетки')}
        draft={'photo_contexts':{'setting':{'support_span_ids':['s1-0-1055'],
                     'source_mention':'ядро клітини'}}}
        quotes=_focused_literal_source_quotes(draft,[span])
        self.assertEqual(len(quotes),1)
        self.assertIn('в ядре клетки',quotes[0]['literal_source_excerpt'])
        self.assertEqual(quotes[0]['span_id'],'s1-0-1055')
        self.assertLessEqual(len(quotes[0]['literal_source_excerpt']),1200)

    def test_original_source_quotes_are_not_sent_for_unrelated_schema_failure(self):
        malformed=copy.deepcopy(self.draft)
        malformed['required_fact_ids']=['wrong']
        calls=[]
        def fake_generate(key,instruction,context,schema):
            calls.append(context)
            return copy.deepcopy(malformed),{}
        with self.assertRaisesRegex(ValueError,'after 2 revisions'):
            reviewed_brief(SimpleNamespace(generate=fake_generate),
                           {'topic':'Нейтронная звезда'},self.sources,self.spans,
                           self.schema,malformed)
        self.assertEqual(len(calls),2)
        self.assertEqual([x['focused_literal_source_quotes'] for x in calls],[[],[]])

    def test_actual_bad_plan_stops_after_two_revisions(self):
        def generate(key,instruction,context,schema):
            if key.startswith('material-brief-repair:review:'):
                self.assertTrue(any('photo subject' in f for f in context['failures']))
                return copy.deepcopy(self.draft),{}
            self.assertIn('чрезвычайно малой массой',context['facts'][-1]['text'])
            self.assertEqual(context['photo_contexts']['subject']['english_photo_object'],'neutron core')
            return self.review(context,False),{}
        with self.assertRaisesRegex(ValueError,'after 2 revisions'):self.run_case(generate)
        self.assertEqual(self.calls,['material-brief-review:1','material-brief-repair:review:1','material-brief-review:2','material-brief-repair:review:2','material-brief-review:3'])

    def test_reviewer_rejection_gets_one_targeted_correction(self):
        def generate(key,instruction,context,schema):
            if key=='material-brief-review:1':
                return self.review(context,False),{}
            if key.startswith('material-brief-repair:review:'):
                self.assertIn('preserve its exact source qualifiers',instruction)
                return copy.deepcopy(self.draft),{}
            return self.review(context,True),{}
        reviewed_brief(SimpleNamespace(generate=lambda key,*args: (self.calls.append(key) or generate(key,*args))),
            {'topic':'Нейтронная звезда','seconds':60,'language':'uk'},self.sources,self.spans,self.schema,copy.deepcopy(self.draft))
        self.assertEqual(self.calls,['material-brief-review:1','material-brief-repair:review:1','material-brief-review:2'])

    def test_search_hints_are_rechecked_after_brief_repair_before_review(self):
        bad=copy.deepcopy(self.draft)
        bad['photo_contexts']['setting']['english_photo_object']='space'
        bad['photo_contexts']['detail']['english_photo_object']='Hubble Space Telescope'
        def generate(key,instruction,context,schema):
            if key.startswith('material-brief-repair:review:'):
                self.assertTrue(any('broad category' in failure for failure in context['failures']))
                self.assertTrue(any('equipment' in failure for failure in context['failures']))
                fixed=copy.deepcopy(bad)
                fixed['photo_contexts']['setting']['english_photo_object']='massive star'
                fixed['photo_contexts']['detail']['english_photo_object']='neutron star'
                return fixed,{}
            self.assertEqual(key,'material-brief-review:2')
            return self.review(context),{}
        result=reviewed_brief(SimpleNamespace(generate=lambda key,*args:(self.calls.append(key) or generate(key,*args))),
            {'topic':'Нейтронная звезда','seconds':60,'language':'uk'},self.sources,self.spans,self.schema,bad)
        self.assertEqual(self.calls,['material-brief-repair:review:1','material-brief-review:2'])
        self.assertEqual(result['photo_contexts']['setting']['subject'],'massive star')

    def test_fact_repair_then_hint_repair_use_distinct_durable_call_keys(self):
        bad=copy.deepcopy(self.draft)
        bad['photo_contexts']['setting']['english_photo_object']='space'
        bad['photo_contexts']['detail']['english_photo_object']='Hubble Space Telescope'
        def generate(key,instruction,context,schema):
            if key=='material-brief-review:1':
                return self.review(context,False),{}
            if key=='material-brief-repair:review:1':
                return copy.deepcopy(bad),{}
            if key=='material-brief-repair:review:2':
                fixed=copy.deepcopy(context['rejected_draft'])
                fixed['photo_contexts']['setting']['english_photo_object']='massive star'
                fixed['photo_contexts']['detail']['english_photo_object']='neutron star'
                return fixed,{}
            self.assertEqual(key,'material-brief-review:3')
            return self.review(context),{}
        result=self.run_case(generate)
        self.assertEqual(result['photo_contexts']['setting']['subject'],'massive star')
        self.assertEqual(self.calls,['material-brief-review:1','material-brief-repair:review:1',
            'material-brief-repair:review:2','material-brief-review:3'])

    def test_search_hint_only_repair_cannot_change_facts_or_source_bindings(self):
        bad=copy.deepcopy(self.draft)
        bad['photo_contexts']['setting']['english_photo_object']='space'
        def generate(key,instruction,context,schema):
            self.assertIn(key,('material-brief-repair:review:1','material-brief-repair:review:2'))
            changed=copy.deepcopy(bad);changed['facts'][0]['text']+=' unsupported'
            return changed,{}
        with self.assertRaisesRegex(ValueError,'changed source-backed facts'):
            reviewed_brief(SimpleNamespace(generate=lambda key,*args:(self.calls.append(key) or generate(key,*args))),
                {'topic':'Нейтронная звезда','seconds':60,'language':'uk'},self.sources,self.spans,self.schema,bad)
        self.assertEqual(self.calls,['material-brief-repair:review:1'])

    def test_saved_actual_repair_that_caused_broad_provider_search_is_rejected(self):
        saved=json.loads((Path(__file__).parent/'fixtures/actual-photo-hint-repair.json').read_text())
        topic=saved['provenance']['topic']
        validate_search_hints(saved['initial_photo_contexts'],topic)
        with self.assertRaisesRegex(ValueError,'search hint') as failure:
            validate_search_hints(saved['repaired_photo_contexts'],topic)
        self.assertIn('setting:',str(failure.exception))
        self.assertIn('detail:',str(failure.exception))
    def test_review_network_ambiguity_never_causes_a_revision_or_retry(self):
        def generate(*args):raise OSError('controlled connection reset')
        with self.assertRaises(OSError):self.run_case(generate)
        self.assertEqual(self.calls,['material-brief-review:1'])
    def test_missing_fact_decision_is_rejected_not_implicitly_approved(self):
        def generate(key,instruction,context,schema):
            result=self.review(context);result['facts'].pop(next(iter(result['facts'])))
            return result,{}
        with self.assertRaisesRegex(ValueError,'fields differ'):self.run_case(generate)
        self.assertEqual(self.calls,['material-brief-review:1'])

    def test_facts_only_review_omits_speculative_photo_decisions(self):
        def generate(key,instruction,context,schema):
            self.calls.append(key)
            self.assertNotIn('photo_contexts',context)
            self.assertNotIn('photo_contexts',schema['properties'])
            self.assertNotIn('photo_contexts',schema['required'])
            return {'facts':{f['id']:{'supported':True,'reason':'Controlled decision only'} for f in context['facts']}},{}
        result=reviewed_brief(SimpleNamespace(generate=generate),{'topic':'Neutron star'},self.sources,self.spans,self.schema,copy.deepcopy(self.draft),check_photos=False)
        self.assertEqual(result['facts'],self.draft['facts'])
        self.assertEqual(self.calls,['material-brief-review:1'])