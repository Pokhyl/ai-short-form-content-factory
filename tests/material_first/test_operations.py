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
                      'required_fact_ids': ['f0', 'f1', 'f2'], 'queries': ['real subject']}
        elif key.startswith('material-inspect:'):
            result = {'accepted': True, 'is_real_material': True, 'subject_fully_visible': True,
                      'visible_description': 'Real subject visible',
                      'visible_fact_details': [{'fact_id': f, 'detail': 'Concrete visible structure '+f}
                                               for f in ['f0', 'f1', 'f2']]}
        elif key == 'material-compose':
            words = ['Source-supported'] + ['narration'] * (schema['properties']['words']['minItems'] - 1)
            count = schema['properties']['beats']['minItems']
            result = {'words': words, 'beats': [
                {'material_id': context['materials'][i]['id'],
                 'word_start': len(words)*i//count, 'word_end': len(words)*(i+1)//count,
                 'fact_ids': ['f0','f1','f2']} for i in range(count)]}
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
            self.assertEqual(len(searches), 3)
            self.assertEqual(model.calls, ['material-brief'] + ['material-inspect:a'+str(i) for i in range(6)] + ['material-compose'])
            self.assertEqual(preparation_budgets(60)['gemini'], 15)

    def test_total_narration_budget_blocks_before_voice(self):
        from material_first.operations import NarrationBudgetExceeded
        model = SimpleNamespace(generate=lambda *args, **kwargs:
            ({"words": ["word"] * 40, "beats": []}, {}))
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
