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
            result = {'accepted': True, 'is_real_material': True,
                      'visible_description': 'Real subject visible',
                      'supported_fact_ids': ['f0', 'f1', 'f2']}
        elif key == 'material-compose':
            words = ['Source-supported'] + ['narration'] * (schema['properties']['words']['minItems'] - 1)
            result = {'words': words, 'beats': [{'material_id': context['materials'][0]['id'],
                                'word_start': 0, 'word_end': len(words),
                                'fact_ids': ['f0', 'f1', 'f2']}]}
        else:
            raise AssertionError(key)
        validate_json(result, schema)
        return copy.deepcopy(result), {'receipt_id': key}
    def review_script(self, context):
        return self.fixtures.review_script(context)


class OperationTests(unittest.TestCase):
    def test_real_adapter_contracts_connect_research_search_inspection_and_composition(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures = Fixtures(root, ['photo'])
            file = root / '0.jpg'
            file.write_bytes(b'\xff\xd8\xffcontrolled-photo')
            import hashlib
            fixtures.assets[0]['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            model = Model(fixtures)
            searches = []
            def search(provider, query, orientation):
                searches.append((provider, query, orientation))
                return {'candidates': fixtures.assets}
            operations = Operations(root,
                SimpleNamespace(fetch=lambda *args: fixtures.evidence['sources']), model,
                SimpleNamespace(search=search), fixtures)
            frozen = Producer(root, operations, probe=fixtures.probe).prepare('topic', 'pl', 60)
            self.assertEqual(len(frozen['payload']['scenes']), 1)
            self.assertEqual(len(searches), 3)
            self.assertEqual(model.calls, ['material-brief', 'material-inspect:a0', 'material-compose'])
            self.assertEqual(preparation_budgets(60)['gemini'], 15)

    def test_total_narration_budget_blocks_before_voice(self):
        from material_first.operations import NarrationBudgetExceeded
        model = SimpleNamespace(generate=lambda *args, **kwargs:
            ({"words": ["word"] * 40, "beats": []}, {}))
        operations = Operations('.', None, model, None, None)
        context = {"request": {"seconds": 15}, "materials": [{"id": "a"}],
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
