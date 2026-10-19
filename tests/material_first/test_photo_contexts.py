import copy
import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from material_first.photo_contexts import validate_context_mentions, validate_search_hints, source_catalog_references
from material_first.operations import Operations
from factory_v3.gemini import validate_json
from material_first.source_spans import source_spans

class ContextTests(unittest.TestCase):
    def setUp(self):
        self.text='Крабовидная туманность содержит пульсар. Остаток Кассиопея A содержит нейтронную звезду. Корма A также содержит нейтронную звезду.'
        self.spans=[{'id':'s1','text':self.text}]
        self.rows={role:{'subject':english,'query':english,'source_mention':name,'support_span_ids':['s1'],'fact_ids':['f'+str(i)]}
            for i,(role,name,english) in enumerate([('setting','Крабовидная туманность','Crab Nebula'),('subject','Кассиопея A','Cassiopeia A'),('detail','Корма A','Puppis A')])}

    def test_multilingual_named_objects_preserve_actual_mentions(self):
        validate_context_mentions(self.rows,self.spans)

    def test_search_hints_reject_generic_categories_and_unrelated_equipment(self):
        validate_search_hints(self.rows, 'Neutron stars')
        for bad in ('space', 'Hubble Space Telescope'):
            rows=copy.deepcopy(self.rows);rows['detail']['query']=bad
            with self.subTest(query=bad),self.assertRaises(ValueError):
                validate_search_hints(rows, 'Neutron stars')

    def test_equipment_is_valid_when_it_is_the_requested_subject(self):
        rows=copy.deepcopy(self.rows);rows['detail']['query']='Hubble Space Telescope'
        validate_search_hints(rows, 'Hubble Space Telescope observations')
        validate_search_hints(rows, 'Телескоп Хаббл')

    def test_catalogued_observable_in_selected_evidence_must_drive_a_search(self):
        rows=copy.deepcopy(self.rows)
        for row in rows.values():
            row['support_span_ids']=['catalogued-object']
            row['query']=row['subject']='neutron star'
        spans=[{'id':'catalogued-object','text':'RX J185635-3754 is a nearby neutron star.'}]
        with self.assertRaisesRegex(ValueError,'source-named observable catalog object'):
            validate_search_hints(rows,'Neutron stars',spans)
        rows['subject']['query']=rows['subject']['subject']='RX J185635-3754'
        validate_search_hints(rows,'Neutron stars',spans)

    def test_supported_catalog_families_keep_full_suffix_and_component(self):
        identifiers = [
            'RX J185635-3754', 'RBS 1223', 'PSR B0531+21', 'NGC 1952', 'IC 443',
            'SNR 0506-68.0', 'SN 1987A', 'SGR 1806-20', 'GRO J1008-57', '4U 0142+61',
            'RX J1856.5-3754', 'PSR J1614–2230', 'PSR J1614−2230',
        ]
        for identity in identifiers:
            with self.subTest(identity=identity):
                rows = copy.deepcopy(self.rows)
                for row in rows.values():
                    row['support_span_ids'] = ['catalogued-object']
                    row['query'] = row['subject'] = 'neutron star'
                spans = [{'id': 'catalogued-object', 'text': identity + ' is a catalogued neutron star.'}]
                with self.assertRaisesRegex(ValueError, 'source-named observable catalog object'):
                    validate_search_hints(rows, 'Neutron stars', spans)
                rows['subject']['query'] = rows['subject']['subject'] = identity
                validate_search_hints(rows, 'Neutron stars', spans)

    def test_catalogue_names_outside_selected_evidence_do_not_force_a_query(self):
        rows=copy.deepcopy(self.rows)
        for row in rows.values():row['support_span_ids']=['selected']
        validate_search_hints(rows,'Neutron stars',[
            {'id':'selected','text':'Neutron stars are compact stellar remnants.'},
            {'id':'other','text':'RX J185635-3754 is a nearby neutron star.'}])

    def test_saved_neutron_sources_require_one_of_their_named_observable_objects(self):
        saved=json.loads((Path(__file__).parent/'fixtures/neutron-uk60-brief-failure.json').read_text())
        spans=source_spans(saved['sources'])
        source_span=next(span for span in spans if 'RX J185635-3754' in span['text'])
        rows=copy.deepcopy(self.rows)
        for row in rows.values():
            row['support_span_ids']=[source_span['id']]
            row['query']=row['subject']='neutron star'
        with self.assertRaisesRegex(ValueError,'source-named observable catalog object'):
            validate_search_hints(rows,'Нейтронная звезда',spans)
        rows['detail']['query']=rows['detail']['subject']='RX J185635-3754'
        validate_search_hints(rows,'Нейтронная звезда',spans)

    def test_saved_source_and_old_bad_repair_stop_before_review_or_search(self):
        saved=json.loads((Path(__file__).parent/'fixtures/neutron-uk60-brief-failure.json').read_text())
        source=saved['sources'][1]
        spans=source_spans([source])
        source_span=next(span for span in spans if 'RX J185635-3754' in span['text'])
        source['sha256']=hashlib.sha256(source['text'].encode()).hexdigest()
        ids=['f1','f2','f3']
        facts=[{'id':identity,'text':'source claim '+identity,
                'support':[{'span_id':source_span['id']}]} for identity in ids]
        rows={role:{'english_photo_object':'neutron star',
                    'source_mention':'RX J185635-3754',
                    'support_span_ids':[source_span['id']],
                    'fact_ids':[identity]}
              for role,identity in zip(('setting','subject','detail'),ids)}
        keys=[];searches=[];reviews=[]
        def generate(key,instruction,context,schema):
            keys.append(key)
            result={'facts':copy.deepcopy(facts),'required_fact_ids':ids,
                    'photo_contexts':copy.deepcopy(rows)}
            if key=='material-brief-repair:initial':
                result['photo_contexts']['setting']['english_photo_object']='space'
                result['photo_contexts']['detail']['english_photo_object']='Hubble Space Telescope'
            else:
                self.assertEqual(key,'material-brief')
                self.assertTrue(any(row['english_photo_object'] == 'RX J185635-3754'
                                    for row in context['source_catalog_references']))
            validate_json(result,schema)
            return result,{'receipt_id':key}
        ops=Operations('.',SimpleNamespace(fetch=lambda *args:[source]),
            SimpleNamespace(generate=generate),
            SimpleNamespace(search=lambda *args:(searches.append(args) or {'candidates':[]})),
            None,documented_contexts=True)
        ops.voice_correction_enabled=True
        ops.review_script=lambda *args:(reviews.append(args) or {})
        with self.assertRaisesRegex(ValueError,'catalog object'):
            ops.research({'topic':'Нейтронная звезда','language':'uk','seconds':60})
        self.assertEqual(keys,['material-brief','material-brief-repair:initial'])
        self.assertEqual(searches,[])
        self.assertEqual(reviews,[])

    def test_unrelated_selected_span_cannot_ground_a_named_object(self):
        with self.assertRaisesRegex(ValueError,'does not contain'):
            validate_context_mentions(self.rows,[{'id':'s1','text':'General neutron star physics, without named objects.'}])

    def test_actual_bad_query_classes_are_rejected_before_search(self):
        for query in ['neutron star representation','pulsar radiation beam','neutron star diagram',
                      'neutron star core', 'stellar core', 'internal neutron star core']:
            rows=copy.deepcopy(self.rows);rows['subject'].update(subject=query,query=query)
            with self.subTest(query=query),self.assertRaisesRegex(ValueError,'depiction or invisible'):
                validate_context_mentions(rows,self.spans)

    def test_query_cannot_add_unsupported_mechanism(self):
        rows=copy.deepcopy(self.rows);rows['setting']['query']='Crab Nebula supernova mechanism'
        with self.assertRaisesRegex(ValueError,'only the source-linked'):
            validate_context_mentions(rows,self.spans)

    def test_correction_receives_all_actual_language_errors_together(self):
        rows=copy.deepcopy(self.rows)
        for row in rows.values():row['subject']=row['query']=row['source_mention']
        with self.assertRaises(ValueError) as failure:validate_context_mentions(rows,self.spans)
        for role in rows:self.assertIn(role+': query and subject must be English',str(failure.exception))

    def test_saved_initial_and_repaired_responses_report_every_wrong_language(self):
        import json
        from pathlib import Path
        saved=json.loads((Path(__file__).parent/'fixtures/actual-context-query-language.json').read_text())
        for key, rows in saved['responses'].items():
            with self.subTest(key=key), self.assertRaises(ValueError) as failure:
                validate_context_mentions(rows,saved['spans'])
            for role in rows:self.assertIn(role+': query and subject must be English',str(failure.exception))

    def run_research(self, mode, availability_first=False, duplicate=False, weak_hint=False, mutate_repair=False, reject_photos=False):
        source={'id':'source','url':'https://example.invalid/source','title':'Observed objects','text':self.text,'sha256':hashlib.sha256(self.text.encode()).hexdigest()}
        keys=[];facts=[]
        def generate(key,instruction,context,schema):
            keys.append(key)
            if key.startswith('material-brief-review:'):
                review={'facts':{f['id']:{'supported':True,'reason':'Supported by exact fixture source'} for f in context['facts']}}
                if 'photo_contexts' in context:
                    review['photo_contexts']={role:{'source_supported':True,'observable_object':not reject_photos,'reason':'Unobservable interior' if reject_photos else 'Observed fixture object'} for role in context['photo_contexts']}
                return review,{'receipt_id':key}
            if key=='material-brief':
                span=context['source_spans'][0]['id']
                rows=copy.deepcopy(self.rows)
                if duplicate:
                    for row in rows.values():row['subject']=row['query']='Crab Nebula'
                for row in rows.values():row['support_span_ids']=[span]
                self.repaired=copy.deepcopy(rows)
                if weak_hint:rows['setting']['subject']=rows['setting']['query']='space'
                if mode!='valid':
                    rows['subject']['query']=rows['subject']['subject']=(
                        'neutron star core' if mode=='hidden_core' else 'neutron star representation')
                facts.extend([{'id':'f'+str(i),'text':claim,'support':[{'span_id':span}]} for i,claim in enumerate(self.text.split('. ')[:3])])
                result={'facts':facts,'required_fact_ids':['f0','f1','f2'],'photo_contexts':rows}
            elif key.startswith('material-brief-repair:'):
                if key=='material-brief-repair:initial':
                    self.assertEqual(context['rejected_draft']['facts'],facts)
                rows=copy.deepcopy(self.repaired)
                if mode=='invalid_twice':rows['detail']['source_mention']='Invented object'
                result={'facts':facts,'required_fact_ids':['f0','f1','f2'],'photo_contexts':rows}
            wire_rows=result['photo_contexts']
            for row in wire_rows.values():
                row['english_photo_object']=row.pop('subject');row.pop('query')
                if mutate_repair and key=='material-brief-repair:initial':result['facts'][0]['text']+=' invented claim'
            if (key.startswith('material-brief-repair:review:')
                    and set(schema['properties'])=={'photo_contexts'}):
                result={'photo_contexts':{
                    role:{field:value for field,value in row.items()
                          if field!='fact_ids'}
                    for role,row in result['photo_contexts'].items()}}
            validate_json(result,schema)
            return result,{'receipt_id':key}
        ops=Operations('.',SimpleNamespace(fetch=lambda *args:[source]),SimpleNamespace(generate=generate),None,None,documented_contexts=True)
        ops.voice_correction_enabled=True
        ops.availability_first_contexts=availability_first
        try:
            result=ops.research({'topic':'Neutron stars','language':'uk','seconds':60})
            self.assertEqual([f['text'] for f in result['evidence']['facts']],[f['text'] for f in facts])
            if availability_first:
                self.assertNotIn('visual_contexts', result['evidence'])
            if duplicate:
                self.assertEqual([t['query'] for t in result['queries']],['Crab Nebula']*3)
            else:
                self.assertEqual([t['query'] for t in result['queries']],['Crab Nebula','Cassiopeia A','Puppis A'])
        finally:self.keys=keys

    def test_valid_contexts_need_no_extra_call(self):
        self.run_research('valid');self.assertEqual(self.keys,['material-brief','material-brief-review:1'])

    def test_broad_search_hint_gets_one_repair_before_semantic_review(self):
        self.run_research('valid',weak_hint=True)
        self.assertEqual(self.keys,['material-brief','material-brief-repair:initial','material-brief-review:1'])

    def test_photo_search_repair_cannot_change_claims(self):
        with self.assertRaisesRegex(ValueError,'changed source-backed facts'):
            self.run_research('valid',weak_hint=True,mutate_repair=True)
        self.assertEqual(self.keys,['material-brief','material-brief-repair:initial'])

    def test_completed_bad_context_gets_one_repair_without_changing_facts(self):
        self.run_research('repair');self.assertEqual(self.keys,['material-brief','material-brief-repair:review:1','material-brief-review:2'])

    def test_two_invalid_context_repairs_stop_without_search_or_extra_calls(self):
        with self.assertRaisesRegex(ValueError,'does not contain'):self.run_research('invalid_twice')
        self.assertEqual(self.keys,['material-brief','material-brief-repair:review:1',
            'material-brief-repair:review:2'])

    def test_availability_first_keeps_duplicate_labels_as_hints_for_retrieval(self):
        self.run_research('valid',availability_first=True,duplicate=True)
        self.assertEqual(self.keys,['material-brief','material-brief-review:1'])

    def test_availability_first_defers_photo_availability_to_actual_retrieval(self):
        # A text-only reviewer cannot rule out point-source observations by
        # inventing a resolved-surface requirement. Actual pixel gates decide.
        self.run_research('valid', availability_first=True, reject_photos=True)
        self.assertEqual(self.keys, ['material-brief', 'material-brief-review:1'])

    def test_invisible_core_hint_is_repaired_before_search_without_predicting_image_availability(self):
        self.run_research('hidden_core', availability_first=True)
        self.assertEqual(self.keys, ['material-brief', 'material-brief-repair:review:1',
                                    'material-brief-review:2'])

    def test_source_reference_inventory_preserves_full_names_and_literal_bindings(self):
        spans = [{'id': 'first', 'text': 'PSR J1614–2230 and RX J1856.5-3754 are named here.'},
                 {'id': 'second', 'text': 'PSR J1614-2230 repeats the same identifier; SN 1987A is another.'}]
        refs = source_catalog_references(spans)
        self.assertEqual([r['english_photo_object'] for r in refs],
                         ['PSR J1614-2230', 'RX J1856.5-3754', 'SN 1987A'])
        for row in refs:
            span = next(s for s in spans if s['id'] == row['support_span_ids'][0])
            self.assertIn(row['source_mention'], span['text'])
        self.assertEqual(source_catalog_references(spans, maximum=2), refs[:2])
        self.assertEqual(source_catalog_references([{'id': 'none', 'text': 'No catalogued object.'}]), [])
