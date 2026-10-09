import copy
import hashlib
import unittest
from types import SimpleNamespace
from material_first.photo_contexts import validate_context_mentions
from material_first.operations import Operations
from factory_v3.gemini import validate_json

class ContextTests(unittest.TestCase):
    def setUp(self):
        self.text='Крабовидная туманность содержит пульсар. Остаток Кассиопея A содержит нейтронную звезду. Корма A также содержит нейтронную звезду.'
        self.spans=[{'id':'s1','text':self.text}]
        self.rows={role:{'subject':english,'query':english,'source_mention':name,'support_span_ids':['s1'],'fact_ids':['f'+str(i)]}
            for i,(role,name,english) in enumerate([('setting','Крабовидная туманность','Crab Nebula'),('subject','Кассиопея A','Cassiopeia A'),('detail','Корма A','Puppis A')])}

    def test_multilingual_named_objects_preserve_actual_mentions(self):
        validate_context_mentions(self.rows,self.spans)

    def test_unrelated_selected_span_cannot_ground_a_named_object(self):
        with self.assertRaisesRegex(ValueError,'does not contain'):
            validate_context_mentions(self.rows,[{'id':'s1','text':'General neutron star physics, without named objects.'}])

    def test_actual_bad_query_classes_are_rejected_before_search(self):
        for query in ['neutron star representation','pulsar radiation beam','neutron star diagram']:
            rows=copy.deepcopy(self.rows);rows['subject'].update(subject=query,query=query)
            with self.subTest(query=query),self.assertRaisesRegex(ValueError,'depiction or invisible'):
                validate_context_mentions(rows,self.spans)

    def test_query_cannot_add_unsupported_mechanism(self):
        rows=copy.deepcopy(self.rows);rows['setting']['query']='Crab Nebula supernova mechanism'
        with self.assertRaisesRegex(ValueError,'only the source-linked'):
            validate_context_mentions(rows,self.spans)

    def run_research(self, mode):
        source={'id':'source','url':'https://example.invalid/source','title':'Observed objects','text':self.text,'sha256':hashlib.sha256(self.text.encode()).hexdigest()}
        keys=[];facts=[]
        def generate(key,instruction,context,schema):
            keys.append(key)
            if key=='material-brief':
                span=context['source_spans'][0]['id']
                rows=copy.deepcopy(self.rows)
                for row in rows.values():row['support_span_ids']=[span]
                self.repaired=copy.deepcopy(rows)
                if mode!='valid':rows['subject']['query']=rows['subject']['subject']='neutron star representation'
                facts.extend([{'id':'f'+str(i),'text':claim,'support':[{'span_id':span}]} for i,claim in enumerate(self.text.split('. ')[:3])])
                result={'facts':facts,'required_fact_ids':['f0','f1','f2'],'photo_contexts':rows}
            else:
                self.assertEqual(key,'material-photo-context-repair')
                self.assertEqual(context['facts'],facts)
                result=copy.deepcopy(self.repaired)
                if mode=='invalid_twice':result['detail']['source_mention']='Invented object'
            validate_json(result,schema)
            return result,{'receipt_id':key}
        ops=Operations('.',SimpleNamespace(fetch=lambda *args:[source]),SimpleNamespace(generate=generate),None,None,documented_contexts=True)
        ops.voice_correction_enabled=True
        try:
            result=ops.research({'topic':'Neutron stars','language':'uk','seconds':60})
            self.assertEqual([f['text'] for f in result['evidence']['facts']],[f['text'] for f in facts])
        finally:self.keys=keys

    def test_valid_contexts_need_no_extra_call(self):
        self.run_research('valid');self.assertEqual(self.keys,['material-brief'])

    def test_completed_bad_context_gets_one_repair_without_changing_facts(self):
        self.run_research('repair');self.assertEqual(self.keys,['material-brief','material-photo-context-repair'])

    def test_second_invalid_context_stops_without_search_or_third_call(self):
        with self.assertRaisesRegex(ValueError,'does not contain'):self.run_research('invalid_twice')
        self.assertEqual(self.keys,['material-brief','material-photo-context-repair'])
