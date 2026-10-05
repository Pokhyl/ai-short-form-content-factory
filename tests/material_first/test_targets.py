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
