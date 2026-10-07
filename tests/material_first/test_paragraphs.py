import copy,json,unittest
from pathlib import Path
from types import SimpleNamespace
from material_first.operations import Operations,NarrationBudgetExceeded
from material_first.presentation import TOPIC_POLICY


class ParagraphTests(unittest.TestCase):
    def setUp(self):
        saved=json.loads((Path(__file__).parent/'fixtures/neutron-uk60-92-word-failure.json').read_text())
        original=saved['drafts'][0];self.beats=[]
        for i,beat in enumerate(original['beats']):
            end=beat['word_end'] if i<len(original['beats'])-1 else len(original['words'])
            self.beats.append({k:v for k,v in beat.items() if k not in ('word_start','word_end')} |
                              {'narration':' '.join(original['words'][beat['word_start']:end])})
        self.context={'request':{'seconds':60,'language':'uk','presentation_policy':TOPIC_POLICY},
                      'materials':[{'id':b['material_id']} for b in self.beats],
                      'evidence':{'facts':saved['brief']['facts'],'sources':[]}}
        self.calls=[]

    def run_compose(self,beats=None,edited=None):
        def generate(key,instruction,context,schema):
            self.calls.append(key)
            if key=='material-compose':
                self.assertNotIn('words',schema['properties'])
                self.assertNotIn('word_start',schema['properties']['beats']['items']['properties'])
                return {'beats':copy.deepcopy(beats if beats is not None else self.beats)},{}
            if key=='material-language-edit':return {'narration':edited if edited is not None else context['narration']},{}
            raise AssertionError('no length retry or voice call')
        return Operations('.',None,SimpleNamespace(generate=generate),None,None).compose(self.context)

    def test_actual_92_word_text_preserved_without_word_array_or_length_retry(self):
        # Strip old target identities only because this narrow compiler fixture
        # does not supply targets. This is not factual/provider acceptance.
        for b in self.beats:b.pop('visual_target_id')
        result=self.run_compose()
        self.assertEqual(sum(len(b['narration'].split()) for b in result['beats']),92)
        self.assertEqual(self.calls,['material-compose','material-language-edit'])
        self.assertEqual(result['beats'],self.beats)

    def test_real_required_fact_omission_is_not_fixed_by_relaxing_length_estimate(self):
        for b in self.beats:b.pop('visual_target_id')
        self.context['request']['required_fact_ids']=['f2','f4','f5','f6']
        with self.assertRaisesRegex(ValueError,'omitted required'):self.run_compose()
        self.assertEqual(self.calls,['material-compose'])

    def test_unknown_source_fact_rejected_before_editing_or_voice(self):
        for b in self.beats:b.pop('visual_target_id')
        self.beats[0]['fact_ids']=['invented']
        with self.assertRaisesRegex(ValueError,'identity'):self.run_compose()
        self.assertEqual(self.calls,['material-compose'])

    def test_native_edit_cannot_silently_empty_or_explode_a_script(self):
        for b in self.beats:b.pop('visual_target_id')
        for edited in (["" for _ in self.beats],["word "*100 for _ in self.beats]):
            self.calls=[]
            with self.assertRaises((ValueError,NarrationBudgetExceeded)):self.run_compose(edited=edited)
            self.assertEqual(self.calls,['material-compose','material-language-edit'])
