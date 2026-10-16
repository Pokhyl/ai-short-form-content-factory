"""Controlled full preparation contracts; not real provider/product acceptance."""
import copy
from pathlib import Path
import tempfile
import unittest

from factory_v3.gemini import validate_json
from material_first.engine import Producer, MaterialUnavailable, verify
from material_first.operations import Operations as RealOperations
from material_first.presentation import TOPIC_POLICY, preferred_shots
from material_first.visuals import ordered_visuals
from test_engine import Operations as FixtureOperations
from test_topic_connected import TopicFixtures


class PixelFirstFixtures(TopicFixtures):
    availability_first_contexts = True
    resolve_photos = RealOperations.resolve_photos

    def __init__(self, root):
        super().__init__(root)
        self.reject_medium = None
        self.reject_relation = None

    def research(self, request):
        self.request = request
        return {**FixtureOperations.research(self, request),
                'visual_targets': copy.deepcopy(self.targets)}

    def inspect_many(self, assets, evidence):
        for asset in assets:
            assert 'visual_targets' not in asset, 'search hints leaked into pixel contracts'
        rows = super().inspect_many(assets, evidence)
        for row in rows:
            if self.reject_medium:
                row['medium'] = self.reject_medium
            if self.reject_relation:
                row['topic_relation']['kind'] = self.reject_relation
        return rows

    def generate(self, key, instruction, context, schema):
        if key != 'material-compose':
            return super().generate(key, instruction, context, schema)
        self.model_calls.append(key)
        phrases = {'pl': 'Kwiat wytwarza pyłek.', 'en': 'The flower produces pollen.',
                   'ru': 'Цветок производит пыльцу.', 'uk': 'Квітка утворює пилок.'}
        phrase = phrases[self.request['language']]
        repetitions = max(1, round(self.request['seconds'] * 2 / (3 * len(phrase.split()))))
        result = {'beats': [{'material_id': context['materials'][i]['id'],
            'narration': ' '.join([phrase] * repetitions), 'fact_ids': ['f' + str(i)]} for i in range(3)]}
        validate_json(result, schema)
        return result, {'receipt_id': 'controlled-compose'}

class PixelFirstConnectedTests(unittest.TestCase):
    def test_overlong_pixel_first_draft_reaches_bounded_length_repair(self):
        class Overlong(PixelFirstFixtures):
            def generate(self, key, instruction, context, schema):
                if key == 'material-compose-length-repair':
                    self.model_calls.append(key)
                    assert context['paragraph_plan'] is None
                    return {'paragraph_'+str(i+1): {
                        'words':['control']*count,
                        'fact_ids':self.normal_draft['beats'][i]['fact_ids']}
                        for i,count in enumerate(context['word_allocations'])}, {'receipt_id': 'controlled-repair'}
                result, receipt = super().generate(key, instruction, context, schema)
                if key == 'material-compose':
                    self.normal_draft = copy.deepcopy(result)
                    for beat in result['beats']:
                        beat['narration'] = ' '.join([beat['narration']] * 5)
                return result, receipt

        for language in ('pl', 'en', 'ru', 'uk'):
            for seconds in (15, 30, 45, 60):
                with self.subTest(language=language, seconds=seconds), tempfile.TemporaryDirectory() as tmp:
                    ops = Overlong(Path(tmp))
                    frozen = Producer(tmp, ops, probe=ops.probe).prepare('Controlled flower process', language, seconds)
                    payload = verify(tmp, frozen, ops.probe)
                    self.assertNotIn('visual_targets', payload)
                    self.assertEqual(ops.model_calls, ['material-compose', 'material-compose-length-repair',
                                                     'material-language-edit'])

    def test_all_language_duration_pairs_reach_frozen_plan_without_caption_calls(self):
        for language in ('pl', 'en', 'ru', 'uk'):
            for seconds in (15, 30, 45, 60):
                with self.subTest(language=language, seconds=seconds), tempfile.TemporaryDirectory() as tmp:
                    ops = PixelFirstFixtures(Path(tmp))
                    evidence = copy.deepcopy(ops.evidence)
                    frozen = Producer(tmp, ops, probe=ops.probe).prepare('Controlled flower process', language, seconds)
                    payload = verify(tmp, frozen, ops.probe)
                    self.assertEqual(payload['evidence'], evidence)
                    self.assertNotIn('visual_targets', payload)
                    self.assertEqual(ops.model_calls, ['material-compose', 'material-language-edit'])
                    self.assertIn('inspect-batch', ops.events)
                    self.assertEqual(len(payload['visuals']), preferred_shots(seconds, TOPIC_POLICY))
                    timing = [{'start_ms': i * seconds * 1000 / 3,
                               'end_ms': (i + 1) * seconds * 1000 / 3} for i in range(3)]
                    cuts = ordered_visuals(payload, timing, seconds * 1000)
                    self.assertEqual(cuts[-1]['end_frame'], seconds * 30)
                    self.assertEqual(len({cut['material_id'] for cut in cuts}), len(cuts))

    def test_invalid_pixels_still_stop_before_composition(self):
        for field, value in (('reject_medium', 'synthetic'), ('reject_relation', 'generic_analogy'),
                             ('reject_relation', 'unknown')):
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as tmp:
                ops = PixelFirstFixtures(Path(tmp))
                setattr(ops, field, value)
                with self.assertRaises(MaterialUnavailable):
                    Producer(tmp, ops, probe=ops.probe).prepare('Controlled flower process', 'en', 30)
                self.assertEqual(ops.model_calls, [])
