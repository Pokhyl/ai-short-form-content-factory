import unittest
from material_first.photo_contexts import rebind_adjacent_literal_mentions, validate_context_mentions, restore_exact_source_case


class AdjacentSourceMentionTests(unittest.TestCase):
    def spans(self):
        return [
            {'id':'s1-0-20','source_id':'source-1','start':0,'end':20,
             'text':'Галактика Андромеди '},
            {'id':'s1-20-42','source_id':'source-1','start':20,'end':42,
             'text':'має спіральні рукави.'},
            {'id':'s1-42-70','source_id':'source-1','start':42,'end':70,
             'text':'Інший об’єкт у небі.'},
            {'id':'s2-0-20','source_id':'source-2','start':0,'end':20,
             'text':'Галактика Андромеди '},
        ]

    def context(self, **overrides):
        base={'support_span_ids':['s1-20-42'],
              'source_mention':'Галактика Андромеди',
              'subject':'Andromeda Galaxy','query':'Andromeda Galaxy'}
        return {'subject':{**base,**overrides}}

    def test_verified_adjacent_span_of_same_source_can_rebind(self):
        result=rebind_adjacent_literal_mentions(self.context(),self.spans())
        self.assertEqual(result['subject']['support_span_ids'],['s1-20-42','s1-0-20'])
        validate_context_mentions(result,self.spans())

    def test_both_neighbouring_spans_with_same_literal_are_retained(self):
        for literal in ("Crist Drive in Los Altos","documented coral reef"):
            with self.subTest(literal=literal):
                rows=[
                    {'id':'source-0-100','source_id':'source','start':0,'end':100,
                     'text':'This source names '+literal+' explicitly.'},
                    {'id':'source-100-200','source_id':'source','start':100,'end':200,
                     'text':'A separate paragraph with no object mention.'},
                    {'id':'source-200-300','source_id':'source','start':200,'end':300,
                     'text':'The same source also describes '+literal+'.'},
                    {'id':'other-0-100','source_id':'other','start':0,'end':100,
                     'text':'Unrelated publisher quotes '+literal+'.'},
                ]
                ctx={'setting':{'support_span_ids':['source-100-200'],
                    'source_mention':literal,'subject':'Documented subject',
                    'query':'Documented subject'}}
                original=ctx['setting']['support_span_ids'][:]
                repaired=rebind_adjacent_literal_mentions(ctx,rows)
                self.assertEqual(repaired['setting']['support_span_ids'],
                    ['source-100-200','source-0-100','source-200-300'])
                self.assertEqual(ctx['setting']['support_span_ids'],original)
                validate_context_mentions(repaired,rows)

    def test_distant_span_does_not_rebind(self):
        draft=self.context(support_span_ids=['s1-42-70'])
        result=rebind_adjacent_literal_mentions(draft,self.spans())
        self.assertEqual(result,draft)
        with self.assertRaisesRegex(ValueError,'span does not contain'):
            validate_context_mentions(result,self.spans())

    def test_cross_source_does_not_rebind(self):
        rows=self.spans()[1:]
        draft=self.context()
        self.assertEqual(rebind_adjacent_literal_mentions(draft,rows),draft)

    def test_unverified_source_text_never_rebinds(self):
        draft=self.context(source_mention='Вигадане слово')
        self.assertEqual(rebind_adjacent_literal_mentions(draft,self.spans()),draft)

    def test_only_original_case_from_selected_source_is_restored(self):
        draft=self.context(support_span_ids=['s1-0-20'],
                           source_mention='галактика андромеди')
        fixed=restore_exact_source_case(draft,self.spans())
        self.assertEqual(fixed['subject']['source_mention'],'Галактика Андромеди')
        self.assertEqual(draft['subject']['source_mention'],'галактика андромеди')
        self.assertEqual(fixed['subject']['support_span_ids'],['s1-0-20'])
        validate_context_mentions(fixed,self.spans())

    def test_case_restoration_does_not_translate_or_rebind(self):
        draft=self.context(support_span_ids=['s1-42-70'],
                           source_mention='галактика андромеди')
        self.assertEqual(restore_exact_source_case(draft,self.spans()),draft)
        translation=self.context(support_span_ids=['s1-0-20'],
                                 source_mention='Andromeda Galaxy')
        self.assertEqual(restore_exact_source_case(translation,self.spans()),translation)
        with self.assertRaisesRegex(ValueError,'span does not contain'):
            validate_context_mentions(restore_exact_source_case(translation,self.spans()),self.spans())

    def test_does_not_modify_input_or_facts(self):
        draft=self.context(fact_ids=['f1'])
        result=rebind_adjacent_literal_mentions(draft,self.spans())
        self.assertEqual(draft['subject']['support_span_ids'],['s1-20-42'])
        self.assertEqual(result['subject']['fact_ids'],['f1'])


if __name__=='__main__':
    unittest.main()