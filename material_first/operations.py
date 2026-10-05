"""Bounded real photo search and source-backed narration adapters."""
from pathlib import Path
from copy import deepcopy
import re
from factory_v3.gemini import obj, array, string, BOOL
from factory_v3.grounding import validate_evidence
from factory_v3.preflight import asset_path, digest, validate_asset
from factory_v3.providers import PROVIDERS


def preparation_budgets(seconds):
    return {'research_search': 1, 'source_fetch': 6, 'gemini': 15,
            'download': 12, 'metadata': 1, **{'search:' + p: 3 for p in PROVIDERS}}


def contiguous_support(evidence):
    """Restore intervening source headings only when all sentences match literally."""
    result = deepcopy(evidence)
    sources = {s['id']: s['text'] for s in result['sources']}
    for fact in result['facts']:
        for support in fact['support']:
            text = sources.get(support['source_id'], '')
            quote = support['quote']
            if quote in text:
                continue
            parts = re.split(r'(?<=[.!?])\s+', quote)
            if len(parts) < 2 or any(not part for part in parts):
                continue
            start = text.find(parts[0])
            if start < 0:
                continue
            end = start + len(parts[0])
            valid = True
            for part in parts[1:]:
                found = text.find(part, end)
                if found < 0 or found - end > 500:
                    valid = False
                    break
                end = found + len(part)
            if valid:
                support['quote'] = text[start:end]
    return result


class NarrationBudgetExceeded(ValueError):
    pass


class Operations:
    def __init__(self, root, research, gemini, search, downloader):
        self.root = Path(root)
        self.source, self.gemini, self.search, self.downloader = research, gemini, search, downloader

    def research(self, request):
        sources = self.source.fetch(request['topic'], request['language'])
        schema = obj({'facts': array(obj({'id': string(), 'text': string(),
            'support': array(obj({'source_id': string(s['id'] for s in sources),
                                  'quote': string()}), 1, 3)}), 1, 8),
            'required_fact_ids': array(string(), 1, 8),
            'queries': array({**string(), 'maxLength': 100}, 1, 3)})
        result, _ = self.gemini.generate('material-brief',
            'Extract a small set of factual statements answering the topic, supported by exact source quotations. '
            'Each quote must be contiguous: retain intervening headings or use separate support entries. '
            'Mark the essential facts. Give up to three English stock photograph searches for relevant '
            'subjects and settings. Do not create a storyboard or require a particular number of shots. '
            'Photographs may illustrate mechanisms explained by the sources without showing the motion itself.',
            {**request, 'sources': sources}, schema)
        evidence = contiguous_support({'sources': sources, 'facts': result['facts']})
        validate_evidence(evidence)
        return {'evidence': evidence, 'required_fact_ids': result['required_fact_ids'],
                'queries': result['queries']}

    def discover(self, request, queries):
        if not isinstance(queries, list) or not 1 <= len(queries) <= 3:
            raise ValueError('bounded material queries required')
        pools = []
        for query in queries:
            for provider in sorted(PROVIDERS):
                result = self.search.search(provider, query, 'portrait')
                pools.append(result['candidates'])
        # Round-robin provider/query results rather than exhausting one provider.
        selected, seen = [], set()
        for rank in range(12):
            for pool in pools:
                if rank < len(pool) and pool[rank]['id'] not in seen:
                    selected.append(pool[rank]); seen.add(pool[rank]['id'])
                    if len(selected) == 12:
                        return selected
        return selected

    def download(self, candidate):
        return self.downloader.download(candidate)

    def inspect(self, asset, evidence):
        validate_asset(self.root, asset)
        data = asset_path(self.root, asset['path']).read_bytes()
        if data.startswith(b'\xff\xd8\xff'):
            mime = 'image/jpeg'
        elif data.startswith(b'\x89PNG\r\n\x1a\n'):
            mime = 'image/png'
        elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            mime = 'image/webp'
        else:
            raise ValueError('unsupported actual photo bytes')
        schema = obj({'accepted': BOOL, 'is_real_material': BOOL, 'visible_description': string(),
                      'supported_fact_ids': array(string(f['id'] for f in evidence['facts']), 0, 8)})
        result, provenance = self.gemini.generate('material-inspect:' + asset['id'],
            'Inspect the attached actual photograph. Describe visible subjects and setting. '
            'Accept a real photograph relevant to the supplied facts. supported_fact_ids are facts this '
            'photo can illustrate; factual proof comes from source quotations. A still may illustrate '
            'an action or hidden mechanism without depicting its motion or internal details. Reject '
            'unrelated subjects, contradictory imagery, drawings and synthetic imagery. Metadata is not proof.',
            {'evidence': evidence, 'metadata': {k: asset[k] for k in ('source_url', 'author', 'license')}},
            schema, photo={'bytes': data, 'mime': mime}, max_tokens=2048)
        return {**result, 'asset_id': asset['id'], 'asset_sha256': asset['sha256'],
                'evidence_sha256': digest(evidence), 'receipt_id': provenance['receipt_id'],
                'model': self.gemini.model, 'provider_provenance': provenance}

    def compose(self, context):
        materials = context['materials']
        seconds = context['request']['seconds']
        minimum_words, maximum_words = round(seconds * 1.8), round(seconds * 2.2)
        minimum_beats = min(len(materials), max(1, (seconds + 2) // 3))
        schema = obj({'words': array(string(), minimum_words, maximum_words),
            'beats': array(obj({'material_id': string(m['id'] for m in materials),
                'word_start': {'type': 'number', 'minimum': 0, 'maximum': maximum_words},
                'word_end': {'type': 'number', 'minimum': 1, 'maximum': maximum_words},
                'fact_ids': array(string(f['id'] for f in context['evidence']['facts']), 1, 8)}),
                minimum_beats, len(materials))})
        result, _ = self.gemini.generate('material-compose',
            f'Write one natural factual script in the requested language. Return the script as a words array '
            f'of {minimum_words} to {maximum_words} individual words TOTAL, aiming for {round(seconds * 2.1)} '
            f'words for {seconds} seconds. Each words item is exactly one word, with punctuation attached. '
            'Do not return a shorter summary. Add useful source-supported explanation to fill the word budget, '
            'without repeating yourself or adding opening/closing filler. '
            f'Use at least {minimum_beats} different supplied photographs, with roughly balanced beat lengths. '
            'Assign all words to consecutive beats using zero-based word_start and exclusive word_end. '
            'Use only supplied inspected materials, each at most once, and facts that it can illustrate. '
            'Cover required topic facts. A photograph can illustrate an action without showing its motion. '
            'Narration will be spoken at its natural speed.', context, schema)
        words = result['words']
        if not minimum_words <= len(words) <= maximum_words:
            raise NarrationBudgetExceeded('narration outside total word budget before TTS')
        if any(len(word.split()) != 1 or word != word.strip() for word in words):
            raise NarrationBudgetExceeded('words array must contain individual words')
        beats, cursor = [], 0
        for beat in result['beats']:
            start, end = beat['word_start'], beat['word_end']
            if type(start) is not int or type(end) is not int or start != cursor or not start < end <= len(words):
                raise ValueError('narration word ranges must cover the script consecutively')
            beats.append({'material_id': beat['material_id'], 'fact_ids': beat['fact_ids'],
                          'narration': ' '.join(words[start:end])})
            cursor = end
        if cursor != len(words):
            raise ValueError('narration words omitted from story')
        return {'beats': beats}

    def review_script(self, context):
        return self.gemini.review_script(context)
