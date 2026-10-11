import copy,json,unittest
from pathlib import Path
from types import SimpleNamespace
from material_first.retrieved_contexts import plan_retrieved_contexts,_bind_literal_source_mentions
from material_first.source_spans import source_spans,bind_support

ROOT=Path(__file__).parent/'fixtures'
class RetrievedContextTests(unittest.TestCase):
    def setUp(self):
        saved=json.loads((ROOT/'actual-semantic-brief.json').read_text())
        spans=source_spans(saved['sources']);self.span=next(s for s in spans if 'Крабовидная туманность' in s['text'])
        self.brief={'evidence':bind_support(saved['sources'],spans,saved['draft']['facts']),
            'required_fact_ids':saved['draft']['required_fact_ids'],
            'queries':[{'id':'v0','query':'neutron core'}]}
        self.pools=json.loads((ROOT/'actual-retrieved-photo-pools.json').read_text())['pools']
        ids=['wikimedia:516106','wikimedia:139881470','wikimedia:51481413']
        self.choice={f'v{i}':{'anchor_id':a,'english_photo_object':['Crab Nebula','neutron star','core of the Crab Nebula'][i],'source_mention':'Крабовидная туманность',
            'support_span_ids':[self.span['id']],'fact_ids':[self.brief['required_fact_ids'][i]]} for i,a in enumerate(ids)}
        self.calls=[];self.review_mode=None;self.review_count=0
    def run_plan(self, mutation=None, reject=False):
        def generate(key,instruction,context,schema):
            self.calls.append(key)
            if key in {'material-photo-plan','material-photo-plan-repair'}:
                if key=='material-photo-plan':
                    self.assertIn('verbatim contiguous substring',instruction)
                    self.assertIn('short 3–80 character verbatim contiguous substring',instruction)
                    self.assertIn('literally contains that exact substring',instruction)
                    self.assertIn('A relation only through a cause, aftermath',instruction)
                    self.assertIn('The three English photo-object labels must be distinct',instruction)
                    self.assertIn('explicitly named in the exact file title or URL',instruction)
                else:
                    self.assertIn('different actual candidate',instruction)
                result=copy.deepcopy(self.choice)
                if key=='material-photo-plan-repair' and reject:
                    for role,identity in zip(('v0','v1','v2'),('wikimedia:148830328','wikimedia:148830334','wikimedia:148830323')):
                        result[role]['anchor_id']=identity;result[role]['english_photo_object']='Crab Nebula'
                if key=='material-photo-plan-repair' and self.review_mode=='repair_once':
                    result['v2']['anchor_id']='wikimedia:148830323';result['v2']['english_photo_object']='pulsar'
                if mutation:mutation(result)
                return result,{'receipt_id':'controlled-selection'}
            self.assertIn(key,{'material-photo-plan-review','material-photo-plan-review:repair'})
            self.review_count+=1
            self.assertIn('multiwavelength',instruction)
            self.assertIn('surface detail',instruction)
            def topic_related(role):
                if reject:return False
                return not(self.review_mode=='repair_once' and self.review_count==1 and role=='v2')
            return {'contexts':{k:{'source_identity_supported':True,'topic_related':topic_related(k),'metadata_compatible':True,'reason':'Controlled review decision; not an actual model acceptance'} for k in context['contexts']},'distinct_contexts':True},{'receipt_id':'controlled-review'}
        return plan_retrieved_contexts(SimpleNamespace(generate=generate),{'topic':'Neutron star','seconds':60},self.brief,self.pools,30)
    def test_actual_pool_can_replace_unavailable_hint_without_changing_facts(self):
        original=copy.deepcopy(self.brief)
        result,candidates=self.run_plan()
        self.assertEqual(self.brief,original)
        self.assertEqual(result['evidence']['facts'],original['evidence']['facts'])
        self.assertEqual(result['evidence']['sources'],original['evidence']['sources'])
        self.assertEqual(result['required_fact_ids'],original['required_fact_ids'])
        self.assertEqual([t['query'] for t in result['visual_targets']],['Crab Nebula','neutron star','core of the Crab Nebula'])
        self.assertEqual(len(candidates),30)
        self.assertEqual(self.calls,['material-photo-plan','material-photo-plan-review'])
        self.assertTrue(all('accepted' not in c for c in candidates))
    def test_invented_photo_label_stops_before_review(self):
        def mutate(rows):rows['v1']['english_photo_object']='hidden neutron core'
        with self.assertRaisesRegex(ValueError,'absent from actual anchor'):self.run_plan(mutate)
        self.assertEqual(self.calls,['material-photo-plan'])
    def test_selected_object_without_source_mention_stops(self):
        def mutate(rows):rows['v0']['source_mention']='Invented associated object'
        with self.assertRaisesRegex(ValueError,'does not contain'):self.run_plan(mutate)
    def test_exact_source_mention_is_bound_to_its_literal_span(self):
        rows={'v0':{'source_mention':'пульсар','support_span_ids':['s1']}}
        spans=[{'id':'s1','source_id':'source-a','text':'Общий контекст нейтронных звёзд.'},
               {'id':'s2','source_id':'source-b','text':'В центре туманности находится пульсар.'}]
        _bind_literal_source_mentions(rows,spans)
        self.assertEqual(rows['v0']['support_span_ids'],['s2','s1'])
        self.assertIn(rows['v0']['source_mention'],next(s['text'] for s in spans if s['id']==rows['v0']['support_span_ids'][0]))
    def test_independent_rejection_is_terminal_without_extra_generation(self):
        with self.assertRaisesRegex(ValueError,'context review failed'):self.run_plan(reject=True)
        self.assertEqual(self.calls,['material-photo-plan','material-photo-plan-review','material-photo-plan-repair','material-photo-plan-review:repair'])
    def test_rejected_context_is_replaced_and_reviewed_again(self):
        self.review_mode='repair_once'
        result,_=self.run_plan()
        self.assertEqual(result['visual_targets'][2]['query'],'pulsar')
        self.assertEqual(self.calls,['material-photo-plan','material-photo-plan-review','material-photo-plan-repair','material-photo-plan-review:repair'])
    def test_repeated_anchor_cannot_fill_three_contexts(self):
        def mutate(rows):rows['v1']['anchor_id']=rows['v0']['anchor_id']
        with self.assertRaisesRegex(ValueError,'distinct anchors'):self.run_plan(mutate)
    def test_unknown_fact_cannot_replace_original_scope(self):
        def mutate(rows):rows['v0']['fact_ids']=['invented-fact']
        with self.assertRaisesRegex(ValueError,'unexpected identity'):self.run_plan(mutate)

    def test_repeated_object_labels_are_qualified_by_explicit_observation_bands(self):
        def mutate(rows):
            rows['v0']['anchor_id']='wikimedia:148830328'
            rows['v1']['anchor_id']='wikimedia:148830334'
            rows['v2']['anchor_id']='wikimedia:148830323'
            for row in rows.values():row['english_photo_object']='Crab Nebula'
        result,_=self.run_plan(mutate)
        self.assertEqual([target['must_show'] for target in result['visual_targets']],
            ['Crab Nebula (optical observation)','Crab Nebula (infrared observation)',
             'Crab Nebula (radio observation)'])
        self.assertEqual(self.calls,['material-photo-plan','material-photo-plan-review'])
