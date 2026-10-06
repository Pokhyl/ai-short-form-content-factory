import copy
import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from factory_v3.gemini import provider_schema, validate_json
from factory_v3.grounding import validate_evidence
from material_first.operations import Operations
from material_first.source_spans import source_spans, bind_support


def source(text, identity='source-1'):
    return {'id': identity, 'url': 'https://example.invalid/article', 'text': text,
            'sha256': hashlib.sha256(text.encode()).hexdigest()}


class SourceSpanTests(unittest.TestCase):
    def test_saved_neutron_fact_scope_is_independent_of_controlled_photo_contexts(self):
        saved = json.loads((Path(__file__).parent / 'fixtures/neutron-uk60-brief-failure.json').read_text())
        draft = saved['draft']
        mapped = {f for t in draft['visual_targets'] for f in t['fact_ids']}
        self.assertEqual(set(draft['required_fact_ids']) - mapped, {'fact-3'})
        # Actual saved source/fact response; newly selected photographic contexts
        # are controlled here, not represented as a fresh provider response.
        result = {k: copy.deepcopy(draft[k]) for k in ('facts', 'required_fact_ids')}
        result['photo_contexts'] = {
            'setting': {'subject': 'Photographic star fields in the night sky', 'query': 'night sky stars'},
            'subject': {'subject': 'Photographic nebulae from astronomical observations', 'query': 'nebula astrophotography'},
            'detail': {'subject': 'Telescopes used to observe distant stars', 'query': 'observatory telescope'}}
        def generate(key, instruction, context, schema):
            validate_json(result, schema)
            return result, {'receipt_id': 'controlled-photo-contexts'}
        ops = Operations('.', SimpleNamespace(fetch=lambda *args: saved['sources']),
                         SimpleNamespace(generate=generate), None, None)
        brief = ops.research({'topic': 'Нейтронная звезда', 'language': 'uk', 'seconds': 60})
        self.assertEqual(brief['required_fact_ids'], draft['required_fact_ids'])
        self.assertEqual(brief['evidence']['facts'][2]['text'], draft['facts'][2]['text'])
        validate_evidence(brief['evidence'])
        self.assertTrue(all(set(draft['required_fact_ids']) <= set(t['fact_ids']) for t in brief['visual_targets']))

    def test_contextual_photos_cannot_excuse_missing_or_invented_narration_facts(self):
        from material_first.engine import validate_story, MaterialUnavailable
        from material_first.visuals import POLICY
        evidence = {'facts': [{'id': f'f{i}'} for i in range(3)]}
        request = {'presentation_policy': POLICY, 'required_fact_ids': ['f0', 'f1', 'f2']}
        materials = [{'id': 'photo', 'sha256': 'unique', 'visible_description': 'Night sky',
                      'source_interval': None, 'capacity_ms': 60000}]
        beat = {'material_id': 'photo', 'narration': 'Controlled text', 'fact_ids': ['f0', 'f1']}
        with self.assertRaisesRegex(MaterialUnavailable, 'required topic coverage'):
            validate_story(request, evidence, materials, {'beats': [beat]})
        beat['fact_ids'] = ['invented']
        with self.assertRaisesRegex(ValueError, 'support'):
            validate_story(request, evidence, materials, {'beats': [beat]})

    def test_full_saved_source_corpus_reproduces_failure_and_binds_actual_original(self):
        path = Path(__file__).parent / 'fixtures/studio-ru30-quotation-failure.json'
        fixture = json.loads(path.read_text())
        from material_first.operations import contiguous_support
        legacy = contiguous_support({'sources': fixture['sources'], 'facts': fixture['draft']['facts']})
        with self.assertRaisesRegex(ValueError, 'exact source quotation'):
            validate_evidence(legacy)
        spans = source_spans(fixture['sources'])
        original = 'Перед употреблением остудить хлеб на решетке в течении часа.'
        span = next(s for s in spans if original in s['text'])
        fact = next(f for f in fixture['draft']['facts'] if any('остудить хлеб' in s['quote'] for s in f['support']))
        selected = {**fact, 'support': [{'span_id': span['id']}]}
        evidence = bind_support(fixture['sources'], spans, [selected])
        validate_evidence(evidence)
        self.assertIn(original, evidence['facts'][0]['support'][0]['quote'])
        self.assertEqual(evidence['facts'][0]['text'], fact['text'])

    def test_saved_real_typo_remains_exact_without_fuzzy_quote_acceptance(self):
        path = Path(__file__).resolve().parents[2] / 'acceptance/factory-v3/studio-quote-mismatch.jsonl'
        row = json.loads(path.read_text().splitlines()[0])
        sources = [source(row['nearby_actual'])]
        legacy = {'sources': sources, 'facts': [{'id': 'f1', 'text': row['fact'],
                  'support': [{'source_id': 'source-1', 'quote': row['quote']}]}]}
        with self.assertRaisesRegex(ValueError, 'exact source quotation'):
            validate_evidence(legacy)
        spans = source_spans(sources)
        evidence = bind_support(sources, spans, [{'id': 'f1', 'text': row['fact'],
                    'support': [{'span_id': spans[0]['id']}]}])
        validate_evidence(evidence)
        self.assertIn('в течении часа', evidence['facts'][0]['support'][0]['quote'])
        self.assertEqual(evidence['sources'], sources)

    def test_all_characters_preserved_across_multilingual_boundaries_and_long_text(self):
        for text in ['Żółć. Chleb stygnie. ', 'Cooling bread preserves texture. ',
                     'Хлеб охлаждают на решётке. ', 'Хліб охолоджують на решітці. ',
                     'abc'*1000, '水。食物！ ']:
            sources = [source((text * 4000)[:80000])]
            spans = source_spans(sources)
            self.assertEqual(''.join(s['text'] for s in spans), sources[0]['text'])
            self.assertLessEqual(len(spans), 134)
            for span in spans:
                self.assertLessEqual(len(span['text']), 1200)
                self.assertEqual(span['text'], sources[0]['text'][span['start']:span['end']])

    def test_duplicate_source_ids_hash_tampering_unknown_and_repeated_ids_rejected(self):
        sources = [source('Original sentence.')]
        spans = source_spans(sources)
        for supports in [[{'span_id': 'invented'}], [{'span_id': spans[0]['id'], 'quote': 'rewritten'}],
                         [{'span_id': spans[0]['id']}] * 2]:
            with self.assertRaises(ValueError):
                bind_support(sources, spans, [{'support': supports}])
        altered = copy.deepcopy(spans); altered[0]['text'] = 'Invented.'
        with self.assertRaisesRegex(ValueError, 'catalog changed'):
            bind_support(sources, altered, [])
        with self.assertRaisesRegex(ValueError, 'identity invalid'):
            source_spans(sources * 2)
        sources[0]['text'] += 'Changed.'
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            source_spans(sources)

    def test_connected_research_protocol_for_all_language_duration_pairs(self):
        for language in ('pl', 'en', 'ru', 'uk'):
            for seconds in (15, 30, 45, 60):
                sources = [source('First source sentence. Second source sentence.'),
                           source('Third source sentence.', 'source-2')]
                calls = []
                def generate(key, instruction, context, schema):
                    calls.append(key)
                    provider_schema(schema)
                    self.assertTrue(all('text' not in s for s in context['sources']))
                    spans = context['source_spans']
                    facts = [{'id': f'f{i}', 'text': f'Controlled fact {i}',
                              'support': [{'span_id': spans[i % 2]['id']}]} for i in range(3)]
                    result = {'facts': facts, 'required_fact_ids': ['f0', 'f1', 'f2'],
                        'photo_contexts': {role: {'subject': f'Different role {i}', 'query': f'context {i}'}
                            for i, role in enumerate(('setting', 'subject', 'detail'))}}
                    validate_json(result, schema)
                    return result, {'receipt_id': 'controlled'}
                ops = Operations('.', SimpleNamespace(fetch=lambda *args: sources),
                                 SimpleNamespace(generate=generate), None, None)
                brief = ops.research({'topic': 'Controlled', 'language': language, 'seconds': seconds})
                validate_evidence(brief['evidence'])
                self.assertEqual(calls, ['material-brief'])
                self.assertEqual(brief['evidence']['facts'][1]['support'][0]['source_id'], 'source-2')
