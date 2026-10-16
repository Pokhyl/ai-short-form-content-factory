import copy
import json
import unittest
from pathlib import Path

from material_first.engine import paragraph_cadence_payload
from material_first.visuals import preflight_visual_capacity


class PoolAssignmentTests(unittest.TestCase):
    def setUp(self):
        self.saved=json.loads((Path(__file__).parent/'fixtures/actual-pl15-pool-selection-2a8d.json').read_text())

    def test_actual_pool_keeps_needed_photos_for_all_candidate_orders(self):
        materials=self.saved['materials'];draft=self.saved['draft']
        anchors={b['material_id'] for b in draft['beats']}
        for shift in range(len(materials)):
            with self.subTest(shift=shift):
                payload=paragraph_cadence_payload(materials[shift:]+materials[:shift],draft,15)
                selected={v['material_id'] for v in payload['visuals']}
                self.assertEqual(len(selected),5)
                self.assertTrue(anchors<=selected)
                self.assertIn('pexels:9910316',selected)
                preflight_visual_capacity(payload)

    def test_missing_related_photo_cannot_be_replaced_by_extra_fields(self):
        materials=[m for m in self.saved['materials'] if m['id']!='pexels:9910316']
        with self.assertRaisesRegex(ValueError,'subject-related'):
            paragraph_cadence_payload(materials,self.saved['draft'],15)

    def test_all_durations_select_from_whole_unbalanced_pool(self):
        for seconds in (15,30,45,60):
            materials=[]
            for fact in (1,2,3):
                for i in range(12):
                    materials.append({'id':f'f{fact}-photo{i}','media_type':'photo',
                        'sha256':f'hash-{fact}-{i}','supported_fact_ids':[f'f{fact}']})
            draft={'beats':[{'material_id':f'f{fact}-photo0','fact_ids':[f'f{fact}'],
                             'narration':'A controlled sentence with equal length.'} for fact in (1,2,3)]}
            with self.subTest(seconds=seconds):
                payload=paragraph_cadence_payload(materials,draft,seconds)
                preflight_visual_capacity(payload)
                ids=[v['material_id'] for v in payload['visuals']]
                self.assertEqual(len(ids),len(set(ids)))
                self.assertTrue({b['material_id'] for b in draft['beats']}<=set(ids))
