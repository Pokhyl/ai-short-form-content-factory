import hashlib
import unittest
from copy import deepcopy
from factory_next.source_context import SourceContextModel,select_source_context,MAX_SOURCE_CONTEXT_CHARS
from material_first.source_spans import source_spans,bind_support
from factory_v3.gemini import obj,string,array

class Model:
    def __init__(self):self.requests=[]
    def generate(self,*args,**kwargs):
        self.requests.append((args,kwargs));return {'result':'controlled'},{'receipt_id':'controlled'}

def corpus():
    result=[]
    for i in range(3):
        text=('An ordinary introductory statement. '*80)
        text+=('A longer unrelated passage. '*1200)
        text+=' RareMitochondrialAnchor is the specifically requested late subject. '
        text+=('Remaining source text. '*100)
        result.append({'id':'source-'+str(i),'url':'https://example.org/'+str(i),
            'title':'Original','text':text,'sha256':hashlib.sha256(text.encode()).hexdigest()})
    return result

class SourceContextTests(unittest.TestCase):
    def test_budget_source_coverage_late_relevance_and_determinism(self):
        sources=corpus();spans=source_spans(sources)
        chosen=select_source_context(spans,'RareMitochondrialAnchor')
        self.assertLessEqual(sum(len(s['text']) for s in chosen),MAX_SOURCE_CONTEXT_CHARS)
        self.assertEqual({s['source_id'] for s in chosen},{s['id'] for s in sources})
        self.assertTrue(any('RareMitochondrialAnchor' in s['text'] for s in chosen))
        self.assertEqual(chosen,select_source_context(spans,'RareMitochondrialAnchor'))
        by_id={s['id']:s for s in spans}
        self.assertTrue(all(s==by_id[s['id']] for s in chosen))

    def test_exact_citations_and_full_source_integrity_remain_authoritative(self):
        sources=corpus();saved=deepcopy(sources);spans=source_spans(sources)
        selected=select_source_context(spans,'RareMitochondrialAnchor')
        s=selected[-1]
        bound=bind_support(sources,spans,[{'id':'f1','text':'controlled',
            'support':[{'span_id':s['id']}]}])
        self.assertEqual(bound['facts'][0]['support'][0]['quote'],s['text'])
        self.assertEqual(bound['sources'],saved)
        sources[0]['text']+='tampered'
        with self.assertRaises(ValueError):bind_support(sources,spans,[])

    def test_draft_citations_survive_repair_selection(self):
        spans=source_spans(corpus());required={spans[20]['id'],spans[40]['id']}
        selected=select_source_context(spans,'unmatched query',required=required)
        self.assertTrue(required<={s['id'] for s in selected})

    def test_wire_enum_contains_only_supplied_exact_spans_without_input_mutation(self):
        spans=source_spans(corpus());context={'source_spans':spans,'topic':'RareMitochondrialAnchor'}
        schema=obj({'support':array(obj({'span_id':string(s['id'] for s in spans)}),1,3)})
        before=deepcopy((context,schema));model=Model()
        wrapped=SourceContextModel(model,'RareMitochondrialAnchor')
        result=wrapped.generate('research','instruction',context,schema,max_tokens=100)
        args,kwargs=model.requests[0];wire=args[2];selected={s['id'] for s in wire['source_spans']}
        self.assertEqual(args[3]['properties']['support']['items']['properties']['span_id']['enum'],
                         [s['id'] for s in spans if s['id'] in selected])
        self.assertEqual((context,schema),before)
        self.assertEqual(result[1]['receipt_id'],'controlled')
        self.assertEqual(kwargs,{'max_tokens':100})

    def test_independent_review_and_small_source_requests_are_unchanged(self):
        model=Model();wrapped=SourceContextModel(model,'topic')
        for context in [{'facts':[{'quote':'Exact source quote'}]},
                        {'source_spans':[{'id':'s','text':'short'}]}]:
            wrapped.generate('review','instruction',context,{})
            self.assertEqual(model.requests[-1][0][2],context)

    def test_over_budget_mandatory_citations_fail_before_send(self):
        spans=source_spans(corpus());model=Model()
        draft={'facts':[{'support':[{'span_id':s['id']} for s in spans]}]}
        with self.assertRaisesRegex(ValueError,'exceeds'):
            SourceContextModel(model,'topic').generate('repair','instruction',
                {'source_spans':spans,'rejected_draft':draft},{})
        self.assertEqual(model.requests,[])
