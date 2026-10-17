import unittest
from material_first.photo_contexts import rebind_adjacent_literal_mentions, validate_context_mentions


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

    def test_does_not_modify_input_or_facts(self):
        draft=self.context(fact_ids=['f1'])
        result=rebind_adjacent_literal_mentions(draft,self.spans())
        self.assertEqual(draft['subject']['support_span_ids'],['s1-20-42'])
        self.assertEqual(result['subject']['fact_ids'],['f1'])


if __name__=='__main__':
    unittest.main()
