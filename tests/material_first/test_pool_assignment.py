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

    def test_fewer_photos_can_cover_both_estimates_without_extra_bread_photo(self):
        materials=[m for m in self.saved['materials'] if m['id']!='pexels:9910316']
        payload=paragraph_cadence_payload(materials,self.saved['draft'],15)
        self.assertLess(len(payload['visuals']),5)
        preflight_visual_capacity(payload)

    def test_missing_related_photo_cannot_be_replaced_by_extra_fields(self):
        materials=[m for m in self.saved['materials'] if m['id']!='pexels:9910316']
        materials=[m for m in materials if 'f3' not in m['supported_fact_ids']]
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

    def test_actual_native_review_uses_four_photos_for_both_estimates(self):
        saved=json.loads((Path(__file__).parent/'fixtures/actual-pl15-dual-timing-9fea.json').read_text())
        materials=saved['materials'];draft=saved['draft']
        for shift in range(len(materials)):
            with self.subTest(shift=shift):
                payload=paragraph_cadence_payload(materials[shift:]+materials[:shift],draft,15)
                selected={v['material_id'] for v in payload['visuals']}
                self.assertEqual(len(selected),4)
                self.assertTrue({b['material_id'] for b in draft['beats']}<=selected)
                preflight_visual_capacity(payload)

    def test_common_pool_matches_exhaustive_small_graphs(self):
        import itertools
        import random
        from material_first.visuals import common_visual_pool, ordered_visuals, estimated_timings
        from material_first.presentation import TOPIC_POLICY
        rng=random.Random(19)
        for case in range(80):
            materials=[{'id':str(i),'supported_fact_ids':rng.sample(['f1','f2','f3'],rng.randint(1,3))}
                       for i in range(7)]
            scenes=[{'id':str(i),'evidence_ids':['f'+str(i+1)],
                     'narration':' '.join(['x'*(i*4+1)]*rng.randint(2,8))} for i in range(3)]
            payload={'seconds':15,'presentation_policy':TOPIC_POLICY,'observations':materials,
                     'scenes':scenes,'visuals':[{'id':str(i),'material_id':str(i)} for i in range(7)]}
            size=rng.choice([3,4,5]);required={'0','1'}
            def valid(pool):
                try:
                    preflight_visual_capacity({**payload,'visuals':pool})
                    return True
                except ValueError:return False
            possible=any(valid([payload['visuals'][i] for i in subset])
                         for subset in itertools.combinations(range(7),size) if {0,1}<=set(subset))
            actual=common_visual_pool(payload,size,required)
            with self.subTest(case=case):
                self.assertEqual(actual is not None,possible)
                if actual is not None:
                    self.assertTrue(valid(actual))
                    self.assertTrue(required<={v['material_id'] for v in actual})
