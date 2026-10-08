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
    def test_actual_planetarium_and_artist_conception_are_ineligible_before_download(self):
        actual = json.loads((Path(__file__).parent/'fixtures/actual-availability-medium-contradiction.json').read_text())
        by_id = {c['id']: c for c in actual['candidates']}
        self.assertTrue(described_as_synthetic(by_id['wikimedia:165844980']))
        self.assertTrue(described_as_synthetic(by_id['wikimedia:155279395']))
        self.assertFalse(described_as_synthetic(by_id['wikimedia:104602817']))

    def test_actual_same_object_records_preserve_contrary_type_classification(self):
        from material_first.photo_planning import object_records
        actual = json.loads((Path(__file__).parent/'fixtures/actual-availability-medium-contradiction.json').read_text())
        records = object_records("Kepler's Supernova Remnant", actual['candidates'])
        self.assertEqual({r['asset_id'] for r in records}, {'wikimedia:104602817', 'wikimedia:180923603'})
        self.assertTrue(any('Type Ia' in r['description'] for r in records))
        asset = {'source_url':'https://example.invalid/image', 'author':'Author', 'license':'CC0',
                 'related_object_metadata':records}
        self.assertEqual(Operations._image_metadata(asset)['related_object_metadata'], records)

    def test_documented_objects_filter_other_named_objects_before_planner_call(self):
        from material_first.photo_planning import context_words
        self.assertIn('e0102', context_words('E0102-72.3'))
        contexts = [{'id':'v'+str(i), 'subject':name, 'query':name, 'support':[]}
                    for i,name in enumerate(['Crab Nebula', 'Eastern Veil Nebula', 'Jellyfish Nebula'])]
        brief = self.brief(); brief['evidence']['visual_contexts'] = contexts
        filename = 'File:Crab Nebula - Optical Telescope Data (catalog123).jpg'
        for pool in self.saved['pools']:
            for candidate in pool['candidates']:
                if candidate['id'] == self.contexts[0]['anchor_id']:
                    candidate['source_metadata']['title'] = filename
        self.contexts[0]['object_label'] = filename
        observed = []
        def generate(key, instruction, context, schema):
            observed.extend(context['candidates'])
            result = {'contexts':[{**row,'source_context_id':'v'+str(i)} for i,row in enumerate(self.contexts)]}
            validate_json(result,schema)
            return result, {'receipt_id':'controlled-documented-object-plan'}
        resolved, _ = plan_photos(SimpleNamespace(generate=generate), {'topic':'Neutron star','seconds':15},
                                 brief, [p['candidates'] for p in self.saved['pools']], 30)
        self.assertEqual(resolved['visual_targets'][0]['must_show'], 'Crab Nebula')
        self.assertEqual(resolved['visual_targets'][0]['query'], 'Crab Nebula')
        self.assertTrue(observed)
        for row in observed:
            text = context_words(' '.join(row['descriptions']))
            self.assertTrue(any(context_words(c['query']) <= text for c in contexts))
        self.assertFalse(any('Kepler' in ' '.join(row['descriptions']) for row in observed))

    def test_impossible_documented_availability_stops_before_new_model_or_download(self):
        brief = self.brief()
        brief['evidence']['visual_contexts'] = [{'id':'v0','query':'unretrieved catalog identifier'}]
        def forbidden(*args): raise AssertionError('model must not be called')
        with self.assertRaisesRegex(ValueError,'availability candidates'):
            plan_photos(SimpleNamespace(generate=forbidden), {'topic':'Neutron star','seconds':60},
                        brief, [p['candidates'] for p in self.saved['pools']], 30)

    def test_actual_forge_and_crescent_contexts_fail_source_class_gate(self):
        actual = json.loads((Path(__file__).parent/'fixtures/actual-source-foreign-contexts.json').read_text())
        def generate(key, instruction, context, schema):
            return actual['model_result'], {'receipt_id': 'actual-saved-context-response'}
        brief = {'queries': actual['targets'], 'evidence': {'facts': [{'id':'f'+str(i)} for i in range(1,9)]}}
        with self.assertRaisesRegex(ValueError, 'source-derived subject class'):
            plan_photos(SimpleNamespace(generate=generate), {'topic':'Neutron star'}, brief, [actual['anchors']], 30)

    def test_context_variety_requires_two_independently_approved_anchor_images(self):
        from material_first.engine import validated_context_anchors, MaterialUnavailable
        targets = [{'id':'v'+str(i)} for i in range(3)]
        assets = {id:{'photo_plan':{'anchor_ids':['a','b','c']},'visual_targets':targets} for id in ['a','b','c']}
        unrelated_anchor = [{'id':'b','matched_visual_targets':{'v1':'actual observed object'}},
                            {'id':'other','matched_visual_targets':{'v2':'same shape, different object'}}]
        with self.assertRaises(MaterialUnavailable): validated_context_anchors(assets, unrelated_anchor)
        proven = unrelated_anchor + [{'id':'a','matched_visual_targets':{'v0':'actual observed object'}}]
        self.assertEqual(validated_context_anchors(assets, proven), {'v0':'a','v1':'b'})

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
        self.assertTrue(all(c['topic_protocol'] == 'topic-specific-v1' for c in candidates))
        self.assertTrue(all(c['visual_qualification_protocol'] == 'qualified-target-v1' for c in candidates))

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

    def test_copied_article_is_preserved_in_object_requirement_and_normalized_only_for_ranking(self):
        # Actual availability response used labels beginning with "The".
        for pool in self.saved['pools']:
            for candidate in pool['candidates']:
                if candidate['id'] == self.contexts[0]['anchor_id']:
                    candidate['source_metadata']['title'] = 'File:Crab Nebula Supernova Remnant.jpg'
        self.contexts[0]['object_label'] = 'The Crab Nebula Supernova Remnant'
        brief, _ = self.operations().resolve_photos(
            {'topic': 'Neutron star', 'seconds': 60, 'presentation_policy': TOPIC_POLICY}, self.brief())
        self.assertEqual(brief['visual_targets'][0]['must_show'], 'The Crab Nebula Supernova Remnant')
        self.assertEqual(brief['visual_targets'][0]['query'], 'Crab Nebula Supernova Remnant')

    def test_actual_saved_plan_uses_same_anchor_metadata_without_regenerating_or_fuzzy_entity_matching(self):
        saved = json.loads((Path(__file__).parent / 'fixtures/availability-actual-article-failure.json').read_text())
        calls = []
        def generate(key, instruction, context, schema):
            calls.append(key)
            validate_json(saved['model_result'], schema)
            return saved['model_result'], {'receipt_id': 'saved-actual-plan'}
        brief = {'evidence': {'sources': [], 'facts': [{'id': 'f' + str(i)} for i in range(1, 9)]},
                 'required_fact_ids': ['f1', 'f2', 'f3']}
        resolved, _ = plan_photos(SimpleNamespace(generate=generate), {'topic': 'Neutron star'},
                                 brief, [saved['anchors']], 30)
        self.assertEqual(resolved['visual_targets'][0]['query'], 'Crab Nebula Supernova Remnant')
        self.assertEqual(calls, ['material-photo-plan'])
        saved['model_result']['contexts'][0]['object_label'] = 'The Crab Nebula Neutron Core'
        with self.assertRaisesRegex(ValueError, 'not copied'):
            plan_photos(SimpleNamespace(generate=generate), {'topic': 'Neutron star'},
                        brief, [saved['anchors']], 30)
