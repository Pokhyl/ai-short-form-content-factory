import json
from copy import deepcopy
from pathlib import Path
import unittest

from factory_next.contextual_edit import contextual_alternatives
from factory_next.timeline import compile_edit, EditUnavailable


class ContextualEditTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((Path(__file__).parent / 'fixtures/actual-edit-e3d35bf7.json').read_text())

    def test_saved_failure_compiles_without_changing_evidence(self):
        before = deepcopy(self.fixture)
        with self.assertRaises(EditUnavailable):
            compile_edit(**{k:v for k,v in before.items() if k not in ('assets','evidence')})
        result = compile_edit(**self.fixture)
        self.assertEqual(self.fixture, before)
        self.assertEqual(result['frame_count'], 1350)
        self.assertEqual(len({s['material_id'] for s in result['shots']}), len(result['shots']))
        self.assertTrue(all(75 <= s['end_frame']-s['start_frame'] <= 225 for s in result['shots']))
        contextual = [s for s in result['shots'] if s.get('context_anchor_material_id')]
        self.assertTrue(contextual)
        self.assertTrue(all(s['visual_relation']=='topic_context' for s in contextual))

    def alternatives(self):
        return contextual_alternatives(**{k:self.fixture[k] for k in ('story','photos','assets','evidence')})

    def test_direct_scene_cannot_inherit_context(self):
        self.fixture['story'][2]['visual_relation'] = 'direct_observation'
        self.assertNotIn('beat-3', self.alternatives())

    def test_missing_context_contract_rejects(self):
        self.fixture['story'][2]['contract']['contextual_not_direct_proof'] = False
        self.assertNotIn('beat-3', self.alternatives())

    def test_changed_qualification_rejects_asset(self):
        asset = self.fixture['assets'][0]
        asset['visual_targets'][0]['must_show'] = 'submarine under water'
        self.assertNotIn(asset['id'], self.alternatives()['beat-3'])

    def test_changed_receipt_rejects_asset(self):
        photo = self.fixture['photos'][0]
        photo['inspection']['visual_entailment']['verdict']['targets']['v0']['verdict'] = 'no_match'
        self.assertNotIn(photo['id'], self.alternatives()['beat-3'])

    def test_changed_evidence_rejects_context(self):
        self.fixture['evidence']['facts'][0]['claim'] = 'invented'
        self.assertEqual(self.alternatives()['beat-3'], [])

    def test_unverified_anchor_cannot_supply_context(self):
        anchor = self.fixture['story'][2]['material_id']
        next(p for p in self.fixture['photos'] if p['id']==anchor)['inspection'].pop('visual_entailment')
        self.assertEqual(self.alternatives()['beat-3'], [])
