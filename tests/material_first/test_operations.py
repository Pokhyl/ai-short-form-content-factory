import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from factory_v3.gemini import validate_json, provider_schema
from material_first.operations import Operations, preparation_budgets
from material_first.engine import Producer
from test_engine import Operations as Fixtures


class Model:
    model = 'controlled-model'
    def __init__(self, fixtures):
        self.fixtures = fixtures
        self.calls = []
    def generate(self, key, instruction, context, schema, **kwargs):
        self.calls.append(key)
        provider_schema(schema)
        if key == 'material-brief':
            result = {'facts': self.fixtures.evidence['facts'],
                      'required_fact_ids': ['f0', 'f1', 'f2'], 'visual_targets': [
                          {'id': 'v'+str(i), 'fact_ids': ['f'+str(i)],
                           'must_show': 'Prominent explanatory detail '+str(i),
                           'must_not_show': 'Generic subject without detail', 'query': 'detail '+str(i)}
                          for i in range(3)]}
        elif key.startswith('material-inspect:'):
            result = {'accepted': True, 'is_real_material': True, 'subject_fully_visible': True,
                      'visible_description': 'Real subject visible',
                      'visible_fact_details': [{'fact_id': f, 'detail': 'Concrete visible structure '+f}
                                               for f in ['f0', 'f1', 'f2']]}
            if context.get('visual_targets') is not None:
                role = int(key.rsplit('a', 1)[1]) % 3
                result['target_matches'] = [{'target_id': t['id'], 'matches': t['id'] == 'v'+str(role),
                    'detail_prominent': t['id'] == 'v'+str(role), 'visible_detail': 'Observed concrete detail '+str(role)}
                    for t in context['visual_targets']]
        elif key == 'material-compose':
            words = ['Source-supported'] + ['narration'] * (schema['properties']['words']['minItems'] - 1)
            count = schema['properties']['beats']['minItems']
            result = {'words': words, 'beats': [
                {'material_id': context['materials'][i]['id'],
                 'word_start': len(words)*i//count, 'word_end': len(words)*(i+1)//count,
                 'fact_ids': ['f'+str(i%3)], 'visual_target_id': 'v'+str(i%3)} for i in range(count)]}
        else:
            raise AssertionError(key)
        validate_json(result, schema)
        return copy.deepcopy(result), {'receipt_id': key}
    def review_script(self, context):
        return self.fixtures.review_script(context)


class OperationTests(unittest.TestCase):
    def test_topic_related_photo_without_visible_fact_detail_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures = Fixtures(root, ['photo'])
            asset = fixtures.assets[0]
            import hashlib
            file = root / asset['path']
            file.write_bytes(b'\xff\xd8\xffcontrolled-photo')
            asset['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            model = SimpleNamespace(model='controlled-model', generate=lambda *args, **kwargs:
                ({'accepted': True, 'is_real_material': True, 'subject_fully_visible': True,
                  'visible_description': 'Bee sitting on a flower', 'visible_fact_details': []},
                 {'receipt_id': 'inspection'}))
            result = Operations(root, None, model, None, None).inspect(asset, fixtures.evidence)
            self.assertFalse(result['accepted'])
            self.assertEqual(result['supported_fact_ids'], [])

    def test_real_adapter_contracts_connect_research_search_inspection_and_composition(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures = Fixtures(root, ['photo'] * 6)
            import hashlib
            for i, asset in enumerate(fixtures.assets):
                file = root / asset['path']
                file.write_bytes(b'\xff\xd8\xffcontrolled-photo' + str(i).encode())
                asset['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            model = Model(fixtures)
            searches = []
            def search(provider, query, orientation):
                searches.append((provider, query, orientation))
                return {'candidates': fixtures.assets}
            operations = Operations(root,
                SimpleNamespace(fetch=lambda *args: fixtures.evidence['sources']), model,
                SimpleNamespace(search=search), fixtures)
            frozen = Producer(root, operations, probe=fixtures.probe).prepare('topic', 'pl', 15)
            self.assertEqual(len(frozen['payload']['scenes']), 5)
            self.assertEqual({s['visual_target_id'] for s in frozen['payload']['scenes']}, {'v0', 'v1', 'v2'})
            self.assertEqual(len(searches), 9)
            self.assertEqual(model.calls, ['material-brief'] + ['material-inspect:a'+str(i) for i in range(6)] + ['material-compose'])
            self.assertEqual(preparation_budgets(60)['gemini'], 15)
            from material_first.engine import verify
            from factory_v3.preflight import digest
            altered = copy.deepcopy(frozen)
            altered['payload']['visual_targets'][0]['must_show'] = 'Different explanatory detail'
            altered['sha256'] = digest(altered['payload'])
            with self.assertRaisesRegex(ValueError, 'asset targets differ'):
                verify(root, altered, fixtures.probe)

    def test_six_topic_related_photos_with_one_visual_role_stop_before_composition(self):
        from material_first.engine import MaterialUnavailable
        class SameRoleModel(Model):
            def generate(self, key, *args, **kwargs):
                result, provenance = super().generate(key, *args, **kwargs)
                if key.startswith('material-inspect:'):
                    for match in result['target_matches']:
                        match['matches'] = match['target_id'] == 'v0'
                        match['detail_prominent'] = match['target_id'] == 'v0'
                return result, provenance
        with tempfile.TemporaryDirectory() as directory:
            import hashlib
            root = Path(directory)
            fixtures = Fixtures(root, ['photo'] * 6)
            for i, asset in enumerate(fixtures.assets):
                file = root / asset['path']
                file.write_bytes(b'\xff\xd8\xffphoto' + str(i).encode())
                asset['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            model = SameRoleModel(fixtures)
            operations = Operations(root,
                SimpleNamespace(fetch=lambda *args: fixtures.evidence['sources']), model,
                SimpleNamespace(search=lambda *args: {'candidates': fixtures.assets}), fixtures)
            with self.assertRaisesRegex(MaterialUnavailable, 'different explanatory visuals unavailable'):
                Producer(root, operations, probe=fixtures.probe).prepare('topic', 'pl', 15)
            self.assertNotIn('material-compose', model.calls)

    def test_missing_exact_third_role_does_not_block_a_varied_contextual_short(self):
        class TwoRoleModel(Model):
            def generate(self, key, *args, **kwargs):
                result, provenance = super().generate(key, *args, **kwargs)
                if key.startswith('material-inspect:'):
                    role = int(key.rsplit('a', 1)[1]) % 2
                    for match in result['target_matches']:
                        match['matches'] = match['target_id'] == 'v'+str(role)
                        match['detail_prominent'] = match['matches']
                elif key == 'material-compose':
                    for i, beat in enumerate(result['beats']):
                        beat['visual_target_id'] = 'v'+str(i%2)
                return result, provenance
        with tempfile.TemporaryDirectory() as directory:
            import hashlib
            root = Path(directory)
            fixtures = Fixtures(root, ['photo'] * 6)
            for i, asset in enumerate(fixtures.assets):
                file = root / asset['path']
                file.write_bytes(b'\xff\xd8\xffphoto' + str(i).encode())
                asset['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            model = TwoRoleModel(fixtures)
            operations = Operations(root,
                SimpleNamespace(fetch=lambda *args: fixtures.evidence['sources']), model,
                SimpleNamespace(search=lambda *args: {'candidates': fixtures.assets}), fixtures)
            frozen = Producer(root, operations, probe=fixtures.probe).prepare('topic', 'pl', 15)
            self.assertEqual({s['visual_target_id'] for s in frozen['payload']['scenes']}, {'v0', 'v1'})
            self.assertEqual(len(frozen['payload']['scenes']), 5)

    def test_total_narration_budget_blocks_before_voice(self):
        from material_first.operations import NarrationBudgetExceeded
        model = SimpleNamespace(generate=lambda *args, **kwargs:
            ({"words": ["word"] * 50, "beats": []}, {}))
        operations = Operations('.', None, model, None, None)
        context = {"request": {"seconds": 15}, "materials": [{"id": "a"+str(i)} for i in range(5)],
                   "evidence": {"facts": [{"id": "f"}]}}
        with self.assertRaises(NarrationBudgetExceeded):
            operations.compose(context)

    def test_exact_source_span_preserves_intervening_heading(self):
        import hashlib
        from material_first.operations import contiguous_support
        from factory_v3.grounding import validate_evidence
        text = 'First statement. Section heading Second statement.'
        evidence = {'sources': [{'id': 's', 'url': 'https://example.invalid/source',
            'text': text, 'sha256': hashlib.sha256(text.encode()).hexdigest()}],
            'facts': [{'id': 'f', 'text': 'Source-backed claim', 'support': [
                {'source_id': 's', 'quote': 'First statement. Second statement.'}]}]}
        resolved = contiguous_support(evidence)
        validate_evidence(resolved)
        self.assertEqual(resolved['facts'][0]['support'][0]['quote'], text)
        evidence['facts'][0]['support'][0]['quote'] = 'First statement. Invented statement.'
        with self.assertRaises(ValueError):
            validate_evidence(contiguous_support(evidence))

    def test_two_photos_cannot_become_an_entire_short(self):
        from material_first.engine import MaterialUnavailable
        model = SimpleNamespace(generate=lambda *args, **kwargs: self.fail("model called with insufficient photos"))
        operations = Operations('.', None, model, None, None)
        with self.assertRaises(MaterialUnavailable):
            operations.compose({"request": {"seconds": 15}, "materials": [{"id": "a"}, {"id": "b"}]})

    def test_saved_english_case_uses_eight_accepted_photos_instead_of_demanding_ten(self):
        import json
        saved = json.loads((Path(__file__).parent / 'fixtures/coffee-en30-cadence-failure.json').read_text())
        self.assertEqual(len(saved['materials']), 8)
        class Composer:
            def generate(self, key, instruction, context, schema):
                count = len(context['materials'])
                assert schema['properties']['beats']['minItems'] <= count == 8
                words = ['word'] * schema['properties']['words']['minItems']
                return {'words': words, 'beats': [
                    {'material_id': m['id'], 'word_start': len(words)*i//count,
                     'word_end': len(words)*(i+1)//count,
                     'fact_ids': m['supported_fact_ids'],
                     'visual_target_id': next(iter(m['matched_visual_targets']))}
                    for i,m in enumerate(context['materials'])]}, {}
        context = {'request': {'seconds': 30, 'visual_targets': saved['visual_targets']},
                   'materials': saved['materials'], 'evidence': {'facts': saved['facts']}}
        draft = Operations('.', None, Composer(), None, None).compose(context)
        self.assertEqual(len(draft['beats']), 8)

    def test_longer_duration_keeps_variety_without_requiring_twelve_perfect_candidates(self):
        class Composer:
            def generate(self, key, instruction, context, schema):
                count = len(context['materials'])
                words = ['word'] * schema['properties']['words']['minItems']
                return {'words': words, 'beats': [
                    {'material_id': m['id'], 'word_start': len(words)*i//count,
                     'word_end': len(words)*(i+1)//count, 'fact_ids': ['f']}
                    for i,m in enumerate(context['materials'])]}, {}
        for seconds,count in [(45, 6), (60, 6), (45, 9), (60, 10)]:
            context = {'request': {'seconds': seconds},
                       'materials': [{'id': 'a'+str(i)} for i in range(count)],
                       'evidence': {'facts': [{'id': 'f'}]}}
            self.assertEqual(len(Operations('.', None, Composer(), None, None).compose(context)['beats']), count)

    def test_saved_ukrainian_source_ellipsis_restores_only_actual_original_text(self):
        import json
        from material_first.operations import contiguous_support
        from factory_v3.grounding import validate_evidence
        saved = json.loads((Path(__file__).parent / 'fixtures/uk60-ellipsis-source-failure.json').read_text())
        with self.assertRaises(ValueError):
            validate_evidence(saved)
        restored = contiguous_support(saved)
        validate_evidence(restored)
        self.assertEqual(restored['facts'][0]['support'][0]['quote'], saved['sources'][0]['text'])
        saved['facts'][0]['support'][0]['quote'] += ' Invented words.'
        with self.assertRaises(ValueError):
            validate_evidence(contiguous_support(saved))

    def test_saved_russian_eighty_word_script_is_not_rejected_for_missing_one_estimated_word(self):
        import json
        saved = json.loads((Path(__file__).parent / 'fixtures/bread-ru45-pacing-failure.json').read_text())
        self.assertEqual(len(saved['draft']['words']), 80)
        class Composer:
            def generate(self, key, instruction, context, schema):
                validate_json(saved['draft'], schema)
                return saved['draft'], {}
        context = {'request': {'seconds':45,'visual_targets':saved['brief']['visual_targets']},
                   'materials':saved['materials'],'evidence':{'facts':saved['brief']['facts']}}
        result = Operations('.',None,Composer(),None,None).compose(context)
        self.assertEqual(' '.join(b['narration'] for b in result['beats']), ' '.join(saved['draft']['words']))
