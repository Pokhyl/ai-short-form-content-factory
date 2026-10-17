"""Reconcile completed model JSON with invalid beat count, once only."""
from unittest import TestCase,main
from unittest.mock import patch

from factory_next.preparation import PreparationStages
from factory_v3.gemini import ModelSchemaError


def beat(i):
    return {'material_id':f'p{i}','narration':f'Pszczoła przenosi pyłek między kwiatami {i}.',
            'fact_ids':[f'f{i}']}


class FakeGemini:
    def __init__(self,original,repaired=None,repair_error=None):
        self.original=original;self.repaired=repaired
        self.repair_error=repair_error
        self.calls=[]
        self.reviews=[]
    def generate(self,key,instruction,context,schema):
        self.calls.append((key,instruction,context))
        if key=='next-story':
            if isinstance(self.original,Exception):raise self.original
            return self.original,{'receipt_id':'original'}
        if key=='next-story-count-repair:1':
            if self.repair_error:raise self.repair_error
            return self.repaired,{'receipt_id':'repair'}
        raise AssertionError('unbudgeted request '+key)
    def review_script(self,review):
        self.reviews.append(review)
        return {'native_language_quality':True}


class Operations:
    def __init__(self,model):self.gemini=model
    def review_script(self,context):return self.gemini.review_script(context)


class StoryCountRepairTests(TestCase):
    def setUp(self):
        self.photos=[
            {'id':f'p{i}','sha256':f'{i:064x}','supported_fact_ids':[f'f{i}'],
             'source_interval':{'kind':'still'},'capacity_ms':5000,
             'visible_description':'Real photograph'} for i in range(3)]
        self.request={'topic':'Jak pszczoły zapylają kwiaty?',
                      'language':'pl','seconds':15,
                      'required_fact_ids':['f0','f1','f2']}
        self.context={'outputs':{
            'research':{'request':self.request,
                        'evidence':{'facts':[{'id':f'f{i}','text':f'Fact {i}',
                                              'support':[]} for i in range(3)]}},
            'materials':{'photos':self.photos}}}
        self.valid={'beats':[beat(i) for i in range(3)]}
    def run_story(self,g):
        stage=PreparationStages('/unused',Operations(g),lambda:None)
        with patch('factory_next.preparation.compact_materials',return_value=[]),             patch('factory_next.preparation.validate_native_surface') as lang,             patch('factory_next.preparation.validate_script_review') as review:
            result=stage.story(self.context)
            lang.assert_called_once()
            review.assert_called_once()
            return result

    def test_two_scene_response_gets_one_distinct_budgeted_repair(self):
        g=FakeGemini(ModelSchemaError({'beats':[beat(0),beat(1)]},
                                      'model response array exceeds bounds'),self.valid)
        result=self.run_story(g)
        self.assertEqual([x[0] for x in g.calls],
                         ['next-story','next-story-count-repair:1'])
        self.assertEqual(len(result['scenes']),3)
        self.assertEqual({f for s in result['scenes'] for f in s['evidence_ids']},
                         {'f0','f1','f2'})
        self.assertEqual(len({s['material_id'] for s in result['scenes']}),3)
        self.assertEqual(len(g.reviews),1)
        self.assertEqual(len(g.calls[1][2]['rejected_draft']['beats']),2)

    def test_nine_scene_response_gets_only_one_bounded_repair(self):
        huge={'beats':[beat(i%3) for i in range(9)]}
        g=FakeGemini(ModelSchemaError(huge,'model response array exceeds bounds'),self.valid)
        result=self.run_story(g)
        self.assertEqual(len(result['scenes']),3)
        self.assertEqual(len(g.calls),2)

    def test_valid_count_with_other_schema_error_is_not_repaired(self):
        g=FakeGemini(ModelSchemaError({'beats':[beat(i) for i in range(3)]},
                                      'invalid nested fact list'),self.valid)
        with self.assertRaises(ModelSchemaError):self.run_story(g)
        self.assertEqual([c[0] for c in g.calls],['next-story'])

    def test_ambiguous_transport_error_never_gets_repair_send(self):
        g=FakeGemini(TimeoutError('result requires reconciliation'),self.valid)
        with self.assertRaises(TimeoutError):self.run_story(g)
        self.assertEqual([c[0] for c in g.calls],['next-story'])

    def test_bad_second_draft_stops_without_third_attempt(self):
        g=FakeGemini(ModelSchemaError({'beats':[beat(0),beat(1)]},
                                      'model response array exceeds bounds'),
                     {'beats':[beat(0),beat(1)]})
        with self.assertRaisesRegex(ValueError,'bounds'):self.run_story(g)
        self.assertEqual([c[0] for c in g.calls],
                         ['next-story','next-story-count-repair:1'])

    def test_oversized_rejected_draft_cannot_expand_repair_prompt(self):
        invalid={'beats':[{'material_id':'p0','narration':'x'*20000,'fact_ids':['f0']}]}
        g=FakeGemini(ModelSchemaError(invalid,'model response array exceeds bounds'),self.valid)
        with self.assertRaises(ModelSchemaError):self.run_story(g)
        self.assertEqual(len(g.calls),1)


if __name__=='__main__':main()
