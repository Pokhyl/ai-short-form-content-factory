import copy
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from factory_v3.gemini import obj,array,string
from material_first.research_review import reviewed_brief
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
    def test_actual_bad_plan_cannot_escape_two_negative_independent_reviews(self):
        def generate(key,instruction,context,schema):
            if key=='material-brief-repair':
                self.assertTrue(any('photo subject' in f for f in context['failures']))
                return copy.deepcopy(self.draft),{}
            self.assertIn('чрезвычайно малой массой',context['facts'][-1]['text'])
            self.assertEqual(context['photo_contexts']['subject']['english_photo_object'],'neutron core')
            return self.review(context,False),{}
        with self.assertRaisesRegex(ValueError,'after one revision'):self.run_case(generate)
        self.assertEqual(self.calls,['material-brief-review:1','material-brief-repair','material-brief-review:2'])
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
