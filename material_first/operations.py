"""Bounded real photo search and source-backed narration adapters."""
from pathlib import Path
from copy import deepcopy
import re
from factory_v3.gemini import obj, array, string, BOOL
from factory_v3.grounding import validate_evidence
from factory_v3.preflight import asset_path, digest, validate_asset
from factory_v3.providers import PROVIDERS
from .engine import MaterialUnavailable
from .targets import validate_targets


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
                                  'quote': string()}), 1, 3)}), 3, 8),
            'required_fact_ids': array(string(), 3, 8),
            'visual_targets': array(obj({'id': string(), 'fact_ids': array(string(), 1, 8),
                'must_show': string(), 'must_not_show': string(),
                'query': {**string(), 'maxLength': 100}}), 3, 3)})
        result, _ = self.gemini.generate('material-brief',
            'Extract at least three distinct atomic explanatory facts answering the topic, supported by exact source quotations. '
            'Separate the starting condition, concrete mechanism/details, and consequence or purpose where supported. '
            'Do not merge multiple mechanisms into one broad topic statement, or paraphrase the same fact to fill slots. '
            'Each quote must be contiguous: retain intervening headings or use separate support entries. '
            'Mark at least three essential distinct facts. Define exactly three distinct visual_targets, each '
            'binding source fact_ids to concrete must_show and must_not_show conditions and an English photograph query. '
            'Targets are practical visual variety roles: overall setting, subject close-up, related object/detail '
            'or consequence. They are not exact scientific proof or three synonyms for the same composition. '
            'For example, a flowering meadow, a bee close-up, and a flower/pollen detail are different roles. '
            'Allow contextually relevant stock photographs; do not demand a rare precise action or anatomy angle. '
            'must_show names the broad dominant focus; must_not_show excludes substituting the same main-subject '
            'composition for every role. Facts are proved by source text, not photograph geometry.',
            {**request, 'sources': sources}, schema)
        evidence = contiguous_support({'sources': sources, 'facts': result['facts']})
        validate_evidence(evidence)
        if len(set(result['required_fact_ids'])) < 3:
            raise MaterialUnavailable('explanation needs three distinct source-backed aspects before material search')
        validate_targets(result['visual_targets'], {f['id'] for f in evidence['facts']})
        if not set(result['required_fact_ids']) <= {f for t in result['visual_targets'] for f in t['fact_ids']}:
            raise MaterialUnavailable('essential source facts omitted from explanatory targets')
        return {'evidence': evidence, 'required_fact_ids': result['required_fact_ids'],
                'queries': result['visual_targets'], 'visual_targets': result['visual_targets']}

    def discover(self, request, queries):
        if not isinstance(queries, list) or not 1 <= len(queries) <= 3:
            raise ValueError('bounded material queries required')
        pools = []
        targets = queries if queries and isinstance(queries[0], dict) else None
        for target in queries:
            query = target['query'] if targets else target
            for provider in sorted(PROVIDERS):
                result = self.search.search(provider, query, 'portrait')
                pools.append(result['candidates'])
        # Round-robin provider/query results rather than exhausting one provider.
        selected, seen = [], set()
        for rank in range(12):
            for pool in pools:
                if rank < len(pool) and pool[rank]['id'] not in seen:
                    candidate = deepcopy(pool[rank])
                    if targets:
                        candidate['visual_targets'] = deepcopy(targets)
                    selected.append(candidate); seen.add(candidate['id'])
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
        schema = obj({'accepted': BOOL, 'is_real_material': BOOL, 'subject_fully_visible': BOOL, 'visible_description': string(),
                      'visible_fact_details': array(obj({'fact_id': string(f['id'] for f in evidence['facts']),
                                                        'detail': string()}), 0, 8)})
        targets = asset.get('visual_targets')
        if targets is not None:
            schema['properties']['target_matches'] = array(obj({
                'target_id': string(t['id'] for t in targets), 'matches': BOOL,
                'detail_prominent': BOOL, 'visible_detail': string()}), len(targets), len(targets))
            schema['required'].append('target_matches')
        result, provenance = self.gemini.generate('material-inspect:' + asset['id'],
            'Inspect the attached final portrait crop. Describe visible subjects and setting. '
            'Reject crops cutting off the important subject at the frame edge; subject_fully_visible must be true. '
            'Accept photographs providing a relevant subject, detail or context for a supplied fact. '
            'visible_fact_details describe the visible relation; do not pretend an invisible action is pictured. '
            'Source quotations prove the claim. A contextual still can accompany a narrated mechanism without '
            'showing its exact action or microscopic anatomy. Reject '
            'unrelated subjects, contradictory imagery, drawings and synthetic imagery. Metadata is not proof. '
            'When visual_targets are supplied, evaluate EVERY target separately against its exact must_show '
            'AND must_not_show as broad composition roles. detail_prominent means the role\'s main visible '
            'focus is recognizable in the actual crop; do not require microscopic detail or exact action. '
            'A bee close-up is fine for the subject role, but cannot also count as a landscape or flower-only '
            'composition. Avoid excessive precision: prioritize different subjects, scales and contexts.',
            {'evidence': evidence, 'visual_targets': targets,
             'metadata': {k: asset[k] for k in ('source_url', 'author', 'license')}},
            schema, photo={'bytes': data, 'mime': mime}, max_tokens=2048)
        details = result['visible_fact_details']
        if any(not item['detail'].strip() for item in details) or len({item['fact_id'] for item in details}) != len(details):
            raise ValueError('inspection must give unique concrete visible evidence per fact')
        result['supported_fact_ids'] = [item['fact_id'] for item in details]
        result['accepted'] = result['accepted'] and result['subject_fully_visible'] and bool(details)
        if targets is not None:
            result['visual_targets_sha256'] = digest(targets)
        return {**result, 'asset_id': asset['id'], 'asset_sha256': asset['sha256'],
                'evidence_sha256': digest(evidence), 'receipt_id': provenance['receipt_id'],
                'model': self.gemini.model, 'provider_provenance': provenance}

    def compose(self, context):
        materials = context['materials']
        seconds = context['request']['seconds']
        minimum_words, maximum_words = round(seconds * 1.8), round(seconds * 2.2)
        minimum_available = 5 + (seconds - 15) // 15
        if len(materials) < minimum_available:
            raise MaterialUnavailable("not enough distinct relevant photos for requested cadence")
        # Aim for frequent changes, but rejected candidates do not make a
        # longer short require a perfect 12/12 discovery/inspection batch.
        minimum_beats = min(len(materials), 12, (seconds + 2) // 3)
        schema = obj({'words': array(string(), minimum_words, maximum_words),
            'beats': array(obj({'material_id': string(m['id'] for m in materials),
                'word_start': {'type': 'number', 'minimum': 0, 'maximum': maximum_words},
                'word_end': {'type': 'number', 'minimum': 1, 'maximum': maximum_words},
                'fact_ids': array(string(f['id'] for f in context['evidence']['facts']), 1, 8)}),
                minimum_beats, len(materials))})
        targets = context['request'].get('visual_targets')
        if targets is not None:
            beat_schema = schema['properties']['beats']['items']
            beat_schema['properties']['visual_target_id'] = string(t['id'] for t in targets)
            beat_schema['required'].append('visual_target_id')
        result, _ = self.gemini.generate('material-compose',
            f'Write one natural factual script in the requested language. Return the script as a words array '
            f'of {minimum_words} to {maximum_words} individual words TOTAL, aiming for {round(seconds * 2.1)} '
            f'words for {seconds} seconds. Each words item is exactly one word, with punctuation attached. '
            'Do not return a shorter summary. Add useful source-supported explanation to fill the word budget, '
            'without repeating yourself or adding opening/closing filler. '
            f'Use at least {minimum_beats} different supplied photographs, with roughly balanced beat lengths. '
            'Assign all words to consecutive beats using zero-based word_start and exclusive word_end. '
            'Use only supplied inspected materials, each at most once, and facts that it can illustrate. '
            'Cover required topic facts with practical, relevant visual variety. Do not assemble several '
            'variations of the same generic subject-and-setting photograph. Each beat must explain its concrete '
            'visible_fact_details without pretending invisible mechanisms are shown. '
            'When visual_targets are present, use at least two different available roles with materials whose matched_visual_targets '
            'includes it. Keep that target identity on its beat, explaining its visible detail. '
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
            if targets is not None:
                beats[-1]['visual_target_id'] = beat['visual_target_id']
            cursor = end
        if cursor != len(words):
            raise ValueError('narration words omitted from story')
        return {'beats': beats}

    def review_script(self, context):
        return self.gemini.review_script(context)
