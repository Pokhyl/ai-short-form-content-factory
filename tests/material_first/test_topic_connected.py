"""Current topical contracts end to end, with explicitly controlled providers."""
import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from factory_v3.gemini import validate_json
from material_first.engine import Producer, verify
from material_first.operations import Operations as RealOperations
from material_first.presentation import TOPIC_POLICY, preferred_shots
from material_first.visuals import ordered_visuals, candidate_limit
from test_engine import Operations as FixtureOperations


class TopicFixtures(FixtureOperations):
    presentation_policy = TOPIC_POLICY

    def __init__(self, root):
        super().__init__(root, ['photo'] * 24)
        self.targets = [{'id': 'v' + str(i), 'fact_ids': ['f0', 'f1', 'f2'],
                         'must_show': subject, 'must_not_show': 'Synthetic or unrelated objects',
                         'query': subject}
                        for i, subject in enumerate(('Field', 'Flower', 'Pollen'))]
        for asset in self.assets:
            asset.update(visual_targets=copy.deepcopy(self.targets),
                         visual_qualification_protocol='qualified-target-v1')
            asset['description'] = ('Field', 'Flower', 'Pollen')[int(asset['id'][1:]) % 3]
        self.model_calls = []
        self.native_quality = True
        self.omit_review_fact = False
        self.tiny = set()
        self.adapter = RealOperations(root, None,
            SimpleNamespace(model='controlled-fixture', generate=self.generate), None, None)

    def research(self, request):
        self.request = request
        return {**super().research(request), 'visual_targets': copy.deepcopy(self.targets)}

    def probe(self, path):
        return {'width': 300 if path.stem in self.tiny else 1080,
                'height': 200 if path.stem in self.tiny else 1920, 'duration_ms': None}

    def discover(self, request, queries):
        return super().discover(request, queries)[:candidate_limit(request['seconds'], TOPIC_POLICY)]

    def resolve_photos(self, request, brief):
        from material_first.photo_planning import plan_photos
        candidates = self.discover(request, brief['queries'])
        return plan_photos(self.adapter.gemini, request, brief, [candidates],
                           candidate_limit(request['seconds'], TOPIC_POLICY))

    def inspect_many(self, assets, evidence):
        self.events.append('inspect-batch')
        result = []
        for asset in assets:
            row = {'accepted': True, 'is_real_material': True, 'subject_fully_visible': True,
                   'medium': 'photograph', 'visible_description': 'Controlled flower observation',
                   'topic_relation': {'kind': 'direct_subject', 'visible_subject': 'Flower',
                                      'connection': 'Controlled direct relationship'},
                   'visible_fact_details': [{'fact_id': 'f' + str(i), 'detail': 'Controlled relationship'}
                                            for i in range(3)],
                   'target_matches': [{'target_id': t['id'], 'matches': True,
                                       'detail_prominent': True, 'subject_qualifications_match': True,
                                       'visible_detail': t['must_show']} for t in self.targets]}
            result.append(self.adapter._inspection_receipt(asset, evidence, row,
                                                          {'receipt_id': 'controlled-' + asset['id']}))
        return result

    def generate(self, key, instruction, context, schema):
        self.model_calls.append(key)
        if key == 'material-photo-plan':
            result = {'contexts': [{'anchor_id': 'a' + str(i), 'object_label': t['must_show'],
                                    'fact_ids': ['f0', 'f1', 'f2']} for i, t in enumerate(self.targets)]}
        elif key == 'material-compose':
            phrases = {'pl': 'Kwiat wytwarza pyłek.', 'en': 'The flower produces pollen.',
                       'ru': 'Цветок производит пыльцу.', 'uk': 'Квітка утворює пилок.'}
            phrase = phrases[self.request['language']]
            repetitions = max(1, round(self.request['seconds'] * 2 / (3 * len(phrase.split()))))
            result = {'beats': [{'material_id': context['materials'][i]['id'],
                                  'narration': ' '.join([phrase] * repetitions),
                                  'fact_ids': ['f' + str(i)], 'visual_target_id': schema['properties']['beats']['items']['properties']['visual_target_id']['enum'][i % len(schema['properties']['beats']['items']['properties']['visual_target_id']['enum'])]}
                                 for i in range(3)]}
        elif key == 'material-language-edit':
            result = {'narration': context['narration']}
        else:
            raise AssertionError('Unexpected provider call: ' + key)
        validate_json(result, schema)
        return result, {'receipt_id': 'controlled-' + key}

    def compose(self, context):
        return self.adapter.compose(context)

    def review_script(self, context):
        result = super().review_script(context)
        result['native_language_quality'] = self.native_quality
        if self.omit_review_fact:
            result['factual_checks'].pop()
        return result


class TopicConnectedTests(unittest.TestCase):
    def test_current_contract_all_sixteen_language_duration_pairs(self):
        for language in ('pl', 'en', 'ru', 'uk'):
            for seconds in (15, 30, 45, 60):
                with self.subTest(language=language, seconds=seconds), tempfile.TemporaryDirectory() as tmp:
                    ops = TopicFixtures(Path(tmp))
                    frozen = Producer(tmp, ops, probe=ops.probe).prepare('Controlled flower process', language, seconds)
                    payload = verify(tmp, frozen, ops.probe)
                    self.assertEqual(ops.model_calls, ['material-photo-plan', 'material-compose', 'material-language-edit'])
                    self.assertEqual(len(payload['visuals']), preferred_shots(seconds, TOPIC_POLICY))
                    timings = [{'start_ms': i * seconds * 1000 / 3,
                                'end_ms': (i + 1) * seconds * 1000 / 3} for i in range(3)]
                    cuts = ordered_visuals(payload, timings, seconds * 1000)
                    self.assertEqual(cuts[-1]['end_frame'], seconds * 30)
                    self.assertEqual(len({c['material_id'] for c in cuts}), len(cuts))
                    self.assertTrue(all(75 <= c['end_frame'] - c['start_frame'] <= 150 for c in cuts))

    def test_tiny_download_is_skipped_through_composition_and_freeze(self):
        with tempfile.TemporaryDirectory() as tmp:
            ops = TopicFixtures(Path(tmp)); ops.tiny = {'0'}
            payload = Producer(tmp, ops, probe=ops.probe).prepare('Controlled flower process', 'uk', 60)['payload']
            self.assertNotIn('a0', {a['id'] for a in payload['assets']})
            self.assertEqual(len(payload['visuals']), 18)

    def test_native_or_incomplete_factual_review_prevents_freezing(self):
        for field in ('native_quality', 'omit_review_fact'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                ops = TopicFixtures(Path(tmp))
                setattr(ops, field, field == 'omit_review_fact')
                with self.assertRaises(ValueError):
                    Producer(tmp, ops, probe=ops.probe).prepare('Controlled flower process', 'uk', 60)
