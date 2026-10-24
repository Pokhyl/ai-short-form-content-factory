import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from factory_v3.gemini import obj,array,string
from material_first.fact_budget import POLICY,validate_fact_budget
from material_first.research_review import reviewed_brief
from material_first.source_spans import source_spans
from tests.factory_next.test_source_rebinding import Source,Model

class FactScopeTests(TestCase):
    def test_actual_compound_inventory_rejected_before_freeze(self):
        saved=json.loads((Path(__file__).parent/'fixtures/actual-story-4369.json').read_text())
        source=saved['context']['outputs']['research']
        draft={**source['evidence'],'required_fact_ids':source['request']['required_fact_ids']}
        before=deepcopy(draft)
        with self.assertRaisesRegex(ValueError,'scope exceeds'):
            validate_fact_budget({**source['request'],'fact_scope_policy':POLICY},draft)
        self.assertEqual(draft,before)
        validate_fact_budget(source['request'],draft) # legacy unchanged

    def run_review(self, *, reject_atomic=False, refuse_repair=False):
        sources=Source().sources;spans=source_spans(sources)
        draft=Model(sources).repaired
        short=deepcopy(draft)
        draft['facts'][0]['text']=' '.join(['overloaded']*40)
        schema=obj({'facts':array(obj({'id':string(),'text':string(),'support':array(obj({'span_id':string()}),1,3)}),3,8),
          'required_fact_ids':array(string(),3,3),'photo_contexts':obj({role:obj({'english_photo_object':string(),'source_mention':string(),'support_span_ids':array(string(),1,3),'fact_ids':array(string(),1,8)}) for role in draft['photo_contexts']})})
        calls=[]
        def generate(key,instruction,context,schema):
            calls.append(key)
            if 'repair' in key:return deepcopy(draft if refuse_repair else short),{}
            self.assertIn('editorial_scope',schema['required'])
            return {'facts':{f['id']:{'supported':True,'reason':'controlled source decision'} for f in short['facts']},
                'editorial_scope':{'atomic':{f['id']:not reject_atomic for f in short['facts']},'answers_topic':True,'reason':'controlled editorial decision'}},{}
        try:
            return reviewed_brief(SimpleNamespace(generate=generate),
                {'topic':'Andromeda Galaxy','seconds':15,'language':'en','fact_scope_policy':POLICY},
                sources,spans,schema,draft,check_photos=False),calls
        finally:self.calls=calls

    def test_budget_repair_requires_independent_review(self):
        result,calls=self.run_review()
        self.assertEqual(calls,['material-brief-repair:review:1','material-brief-review:2'])
        self.assertEqual(len(result['facts']),3)

    def test_short_compound_claim_still_rejected(self):
        with self.assertRaisesRegex(ValueError,'not an atomic claim'):
            self.run_review(reject_atomic=True)
        self.assertEqual(len(self.calls),4)

    def test_repeated_overflow_stops_without_semantic_call(self):
        with self.assertRaisesRegex(ValueError,'after 3 revisions'):
            self.run_review(refuse_repair=True)
        self.assertEqual(self.calls,['material-brief-repair:review:1','material-brief-repair:review:2','material-brief-repair:review:3'])
