import copy
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from factory_v3.gemini import validate_json
from material_first.operations import Operations
from material_first.photo_planning import plan_photos
from material_first.presentation import TOPIC_POLICY
from material_first.photo_queries import described_as_synthetic


class AvailabilityPlanningTests(unittest.TestCase):
    def setUp(self):
        self.saved = json.loads((Path(__file__).parent / 'fixtures/availability-query-pools.json').read_text())
        self.contexts = [
            {'anchor_id': 'wikimedia:51481413', 'object_label': 'Crab Nebula', 'fact_ids': ['f4', 'f5']},
            {'anchor_id': 'wikimedia:182489427', 'object_label': 'Eastern Veil Nebula', 'fact_ids': ['f4', 'f5']},
            {'anchor_id': 'pexels:16880954', 'object_label': 'Jellyfish Nebula', 'fact_ids': ['f4', 'f5']},
        ]
        self.calls = []
        self.searches = []

    def operations(self):
        def search(provider, query, orientation):
            self.searches.append((provider, query, orientation))
            return {'candidates': next(p['candidates'] for p in self.saved['pools']
                                       if p['provider'] == provider and p['query'] == query)}
        def generate(key, instruction, context, schema):
            self.calls.append(key)
            self.assertEqual(key, 'material-photo-plan')
            self.assertNotIn('approval', context)
            result = {'contexts': copy.deepcopy(self.contexts)}
            validate_json(result, schema)
            return result, {'receipt_id': 'controlled-plan-over-actual-pools'}
        return Operations('.', None, SimpleNamespace(generate=generate), SimpleNamespace(search=search), None)

    def brief(self):
        return {'evidence': self.saved['evidence'], 'required_fact_ids': ['f1', 'f2', 'f3'],
                'queries': self.saved['targets'], 'visual_targets': self.saved['targets']}

    def test_actual_pool_replaces_imaginary_nucleus_contract_before_download_within_same_budget(self):
        request = {'topic': 'Нейтронная звезда', 'language': 'uk', 'seconds': 60,
                   'presentation_policy': TOPIC_POLICY, 'visual_validation_mode': 'gemini'}
        original = copy.deepcopy(self.brief())
        resolved, candidates = self.operations().resolve_photos(request, original)
        self.assertEqual(len(self.searches), 9)
        self.assertEqual(self.calls, ['material-photo-plan'])
        self.assertEqual(len(candidates), 30)
        self.assertEqual(resolved['evidence'], original['evidence'])
        self.assertEqual(resolved['required_fact_ids'], original['required_fact_ids'])
        self.assertEqual(resolved['visual_targets'][2]['must_show'], 'Jellyfish Nebula')
        self.assertIn('atomic nucleus', original['visual_targets'][2]['must_show'])
        self.assertTrue({c['anchor_id'] for c in self.contexts} <= {c['id'] for c in candidates})
        self.assertTrue(all(c['visual_targets'] == resolved['visual_targets'] for c in candidates))
        self.assertFalse(any(described_as_synthetic(c) for c in candidates))
        # Actual search provenance is retained; revised entity labels are not
        # falsely recorded as additional executed provider queries.
        self.assertTrue(all(c['discovery_query'] in {t['query'] for t in original['queries']} for c in candidates))
        self.assertFalse(any(c.get('accepted') for c in candidates))

    def test_invented_object_unknown_anchor_and_synthetic_label_are_terminal_without_retry(self):
        for replacement in ({'object_label': 'atomic nucleus'}, {'anchor_id': 'invented'},
                            {'object_label': 'Crab Nebula artistic impression'}):
            with self.subTest(replacement=replacement):
                self.setUp(); self.contexts[0].update(replacement)
                with self.assertRaises(ValueError):
                    self.operations().resolve_photos({'topic': 'Neutron star', 'seconds': 60,
                                                      'presentation_policy': TOPIC_POLICY}, self.brief())
                self.assertEqual(self.calls, ['material-photo-plan'])

    def test_standard_metadata_mode_keeps_original_contract_and_uses_no_planner_model(self):
        brief = self.brief()
        resolved, candidates = self.operations().resolve_photos(
            {'seconds': 60, 'presentation_policy': TOPIC_POLICY, 'visual_validation_mode': 'metadata'}, brief)
        self.assertEqual(resolved, brief)
        self.assertEqual(self.calls, [])
        self.assertEqual(len(self.searches), 9)
        self.assertTrue(all(c['visual_targets'] == brief['visual_targets'] for c in candidates))

