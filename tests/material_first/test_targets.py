import unittest
import json
from pathlib import Path
from factory_v3.preflight import digest
from material_first.targets import matched_targets
from material_first.engine import match_materials, MaterialUnavailable


class TargetTests(unittest.TestCase):
    def setUp(self):
        self.targets = [{'id': 'v'+str(i), 'fact_ids': ['f'+str(i)],
            'must_show': 'Readable structure '+str(i), 'must_not_show': 'Generic subject only',
            'query': 'structure '+str(i)} for i in range(3)]

    def test_relevant_fact_cannot_substitute_for_missing_visual_role(self):
        pictures = [{'id': 'a', 'supported_fact_ids': ['f0', 'f1', 'f2'],
                     'matched_visual_targets': {'v0': 'Visible food'}},
                    {'id': 'b', 'supported_fact_ids': ['f0', 'f1', 'f2'],
                     'matched_visual_targets': {'v0': 'Visible food'}}]
        draft = {'beats': [{'material_id': 'a', 'fact_ids': ['f1'],
                            'visual_target_id': 'v1', 'narration': 'Anatomy'}]}
        with self.assertRaises(MaterialUnavailable):
            match_materials(pictures, draft)

    def test_role_matching_swaps_only_within_exact_target(self):
        pictures = [{'id': 'a', 'supported_fact_ids': ['f0', 'f1'],
                     'matched_visual_targets': {'v0': 'Food'}},
                    {'id': 'b', 'supported_fact_ids': ['f0', 'f1'],
                     'matched_visual_targets': {'v1': 'Anatomy'}}]
        draft = {'beats': [{'material_id': 'a', 'fact_ids': ['f1'],
                            'visual_target_id': 'v1', 'narration': 'Anatomy'},
                           {'material_id': 'b', 'fact_ids': ['f0'],
                            'visual_target_id': 'v0', 'narration': 'Food'}]}
        result = match_materials(pictures, draft)
        self.assertEqual([b['material_id'] for b in result['beats']], ['b', 'a'])
        self.assertEqual([b['narration'] for b in result['beats']], ['Anatomy', 'Food'])

    def test_tiny_or_absent_detail_is_not_a_target_match(self):
        receipt = {'visual_targets_sha256': digest(self.targets), 'target_matches': [
            {'target_id': t['id'], 'matches': True, 'detail_prominent': False,
             'visible_detail': 'Tiny detail somewhere in frame'} for t in self.targets]}
        self.assertEqual(matched_targets({'visual_targets': self.targets}, receipt), {})
        receipt['target_matches'][0]['detail_prominent'] = True
        self.assertEqual(set(matched_targets({'visual_targets': self.targets}, receipt)), {'v0'})
        self.targets[0]['must_not_show'] = 'Changed contract after inspection'
        with self.assertRaises(ValueError):
            matched_targets({'visual_targets': self.targets}, receipt)

    def test_unreviewed_legacy_generic_photo_cannot_enter_new_target_plan(self):
        with self.assertRaises(ValueError):
            matched_targets({'visual_targets': self.targets}, {'supported_fact_ids': ['f0', 'f1', 'f2']})

    def test_saved_live_failure_has_no_proof_of_distinct_explanatory_targets(self):
        saved = json.loads((Path(__file__).parent / 'fixtures/bee-generic-visual-failure.json').read_text())
        self.assertEqual(len(saved['materials']), 5)
        self.assertFalse(saved['accepted'])
        for material in saved['materials']:
            self.assertTrue(material['supported_fact_ids'])
            with self.assertRaisesRegex(ValueError, 'exact visual targets'):
                matched_targets({'visual_targets': saved['visual_targets']}, material['inspection'])

    def test_saved_role_capacity_failure_consolidates_without_changing_the_script(self):
        from material_first.engine import fit_materials
        saved = json.loads((Path(__file__).parent / 'fixtures/coffee-role-capacity-failure.json').read_text())
        words = saved['draft']['words']
        draft = {'beats': [{k:b[k] for k in ('material_id', 'fact_ids', 'visual_target_id')} |
                 {'narration': ' '.join(words[b['word_start']:b['word_end']])}
                 for b in saved['draft']['beats']]}
        with self.assertRaises(MaterialUnavailable):
            match_materials(saved['materials'], draft)
        result = fit_materials(saved['materials'], draft)
        self.assertEqual(len(result['beats']), 6)
        self.assertEqual(len({b['material_id'] for b in result['beats']}), 6)
        self.assertEqual(' '.join(b['narration'] for b in result['beats']), ' '.join(words))
        self.assertEqual(result['merged_adjacent_beats'], 1)
        self.assertEqual({b['visual_target_id'] for b in result['beats']}, {'target-1','target-2','target-3'})

    def test_broad_class_match_cannot_substitute_for_qualified_subject(self):
        targets = [dict(t) for t in self.targets]
        targets[0]['must_show'] = 'Massive star that can end as a supernova'
        asset = {'visual_targets': targets, 'visual_qualification_protocol':'qualified-target-v1'}
        receipt = {'visual_targets_sha256':digest(targets),
            'visual_qualification_protocol':'qualified-target-v1', 'target_matches':[
                {'target_id':t['id'], 'matches':True, 'detail_prominent':True,
                 'visible_detail':'Sun' if i == 0 else 'Documented physical stage',
                 'subject_qualifications_match':i != 0} for i,t in enumerate(targets)]}
        self.assertEqual(set(matched_targets(asset,receipt)), {'v1','v2'})
        # The broad class was accepted by the model; server scheduling still
        # excludes it from the massive-progenitor role independently.
        receipt['target_matches'][0]['subject_qualifications_match'] = True
        self.assertEqual(set(matched_targets(asset,receipt)), {'v0','v1','v2'})
        del receipt['visual_qualification_protocol']
        with self.assertRaisesRegex(ValueError,'qualification inspection missing'):
            matched_targets(asset,receipt)
