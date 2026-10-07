import copy,json,unittest
from pathlib import Path
from material_first.engine import fit_contextual_paragraphs,match_materials,validate_story,MaterialUnavailable


class ContextualParagraphTests(unittest.TestCase):
    def setUp(self):
        self.saved=json.loads((Path(__file__).parent/'fixtures/paragraph-anchor-failure.json').read_text())
        self.draft=copy.deepcopy(self.saved['responses']['material-compose'])
        for beat,text in zip(self.draft['beats'],self.saved['responses']['material-language-edit']['narration']):
            beat['narration']=text

    def test_actual_hidden_mechanism_and_same_role_outcome_share_anchor(self):
        with self.assertRaises(MaterialUnavailable):
            match_materials(self.saved['materials'],self.draft,contextual=True,topical=True)
        result=fit_contextual_paragraphs(self.saved['materials'],self.draft)
        self.assertEqual(len(result['beats']),3)
        self.assertEqual(result['merged_adjacent_beats'],1)
        self.assertEqual(' '.join(b['narration'] for b in result['beats']),
                         ' '.join(b['narration'] for b in self.draft['beats']))
        self.assertEqual({f for b in result['beats'] for f in b['fact_ids']},
                         {f for b in self.draft['beats'] for f in b['fact_ids']})
        self.assertEqual(result['beats'][1]['fact_ids'],['f3','f4','f5'])
        scenes=validate_story(self.saved['request'],self.saved['evidence'],self.saved['materials'],result)
        self.assertEqual(len({s['material_id'] for s in scenes}),3)
        self.assertEqual({s['visual_target_id'] for s in scenes},{'v0','v1'})
        # This is saved assignment evidence only, not a new independent review
        # or approval of the old Sun/massive-star inspection.

    def test_unrelated_photos_still_cannot_fill_a_paragraph(self):
        materials=copy.deepcopy(self.saved['materials'])
        for material in materials:material['supported_fact_ids']=['unrelated']
        with self.assertRaises(MaterialUnavailable):fit_contextual_paragraphs(materials,self.draft)

    def test_different_visual_roles_cannot_be_merged(self):
        for i,beat in enumerate(self.draft['beats']):beat['visual_target_id']='different-'+str(i)
        with self.assertRaises(MaterialUnavailable):fit_contextual_paragraphs(self.saved['materials'],self.draft)

    def test_feasible_paragraphs_are_not_merged(self):
        materials=copy.deepcopy(self.saved['materials'])
        materials[1]['supported_fact_ids']+=['f3','f4']
        result=fit_contextual_paragraphs(materials,self.draft)
        self.assertEqual(result,match_materials(materials,self.draft,contextual=True,topical=True))
        self.assertNotIn('merged_adjacent_beats',result)

    def test_invalid_identity_is_not_hidden_by_consolidation(self):
        self.draft['beats'][1]['material_id']='invented'
        with self.assertRaisesRegex(ValueError,'invented'):fit_contextual_paragraphs(self.saved['materials'],self.draft)

    def test_partition_search_is_bounded(self):
        self.draft['beats']*=3
        with self.assertRaisesRegex(ValueError,'bounded'):fit_contextual_paragraphs(self.saved['materials'],self.draft)

    def test_model_context_keeps_semantics_without_http_receipt_noise(self):
        from material_first.paragraphs import compact_materials
        compact=compact_materials(self.saved['materials'])
        self.assertLess(len(json.dumps(compact)),len(json.dumps(self.saved['materials']))//2)
        for original,row in zip(self.saved['materials'],compact):
            for key in ('id','visible_description','supported_fact_ids','matched_visual_targets'):
                self.assertEqual(row[key],original[key])
            for key in ('medium','topic_relation','visible_fact_details','target_matches'):
                if key in original['inspection']:
                    self.assertEqual(row['inspection'][key],original['inspection'][key])
            self.assertNotIn('provider_provenance',row['inspection'])
