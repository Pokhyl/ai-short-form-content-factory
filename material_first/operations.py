"""Bounded real photo search and source-backed narration adapters."""
from pathlib import Path
from copy import deepcopy
import re
import hashlib
from factory_v3.gemini import obj, array, string, BOOL, ModelSchemaError, validate_json
from factory_v3.grounding import validate_evidence, compact_evidence
from factory_v3.preflight import asset_path, digest, validate_asset
from factory_v3.providers import PROVIDERS
from .engine import MaterialUnavailable
from .targets import validate_targets
from .visuals import POLICY, candidate_limit


def preparation_budgets(seconds):
    return {'research_search': 1, 'source_fetch': 6, 'gemini': 16,
            'download': candidate_limit(seconds), 'metadata': 1, **{'search:' + p: 3 for p in PROVIDERS}}


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
            # An explicit ellipsis denotes omitted original text, not invented
            # words. Restore only an exact ordered, bounded source span.
            fragments = [part.strip() for part in re.split(r'(?:\.{3}|…)', quote) if part.strip()]
            if len(fragments) > 1:
                start = text.find(fragments[0])
                end = start + len(fragments[0])
                if start >= 0:
                    for fragment in fragments[1:]:
                        found = text.find(fragment, end)
                        if found < 0 or found - end > 500:
                            break
                        end = found + len(fragment)
                    else:
                        support['quote'] = text[start:end]
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
    presentation_policy = POLICY

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
        desired_facts = max(3, min(8, (request['seconds'] + 7) // 8))
        result, _ = self.gemini.generate('material-brief',
            f'For {request["seconds"]} seconds, aim for {desired_facts} distinct source-backed facts, '
            'with enough useful explanation for natural speech. Cover the full requested process, '
            'including its final outcome; do not spend all facts on its starting ingredients. '
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
        for rank in range(40):
            for pool in pools:
                if rank < len(pool) and pool[rank]['id'] not in seen:
                    candidate = deepcopy(pool[rank])
                    if targets:
                        candidate['visual_targets'] = deepcopy(targets)
                    selected.append(candidate); seen.add(candidate['id'])
                    if len(selected) == candidate_limit(request['seconds']):
                        return selected
        return selected

    def download(self, candidate):
        return self.downloader.download(candidate)

    def _photo(self, asset):
        validate_asset(self.root, asset)
        data = asset_path(self.root, asset['path']).read_bytes()
        if hashlib.sha256(data).hexdigest() != asset['sha256']:
            raise ValueError('photo bytes changed before inspection')
        if data.startswith(b'\xff\xd8\xff'):
            mime = 'image/jpeg'
        elif data.startswith(b'\x89PNG\r\n\x1a\n'):
            mime = 'image/png'
        elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            mime = 'image/webp'
        else:
            raise ValueError('unsupported actual photo bytes')
        return {'bytes': data, 'mime': mime, 'asset_id': asset['id']}

    def _inspection_schema(self, evidence, targets):
        schema = obj({'accepted': BOOL, 'is_real_material': BOOL,
            'subject_fully_visible': BOOL, 'visible_description': string(),
            'visible_fact_details': array(obj({'fact_id': string(f['id'] for f in evidence['facts']),
                                               'detail': string()}), 0, 8)})
        if targets is not None:
            schema['properties']['target_matches'] = array(obj({
                'target_id': string(t['id'] for t in targets), 'matches': BOOL,
                'detail_prominent': BOOL, 'visible_detail': string()}), len(targets), len(targets))
            schema['required'].append('target_matches')
        return schema

    def _inspection_receipt(self, asset, evidence, result, provenance):
        result = deepcopy(result)
        details = result['visible_fact_details']
        if any(not item['detail'].strip() for item in details) or len({item['fact_id'] for item in details}) != len(details):
            raise ValueError('inspection must give unique visible evidence per fact')
        result['supported_fact_ids'] = [item['fact_id'] for item in details]
        result['accepted'] = result['accepted'] and result['subject_fully_visible'] and bool(details)
        if asset.get('visual_targets') is not None:
            result['visual_targets_sha256'] = digest(asset['visual_targets'])
        return {**result, 'asset_id': asset['id'], 'asset_sha256': asset['sha256'],
                'evidence_sha256': digest(evidence), 'receipt_id': provenance['receipt_id'],
                'model': self.gemini.model, 'provider_provenance': provenance}

    INSPECTION_INSTRUCTION = (
        'Inspect each attached whole original photograph, identified by its preceding asset_id. '
        'Describe what is actually visible. Accept real photographs with a relevant subject, detail '
        'or setting for the supplied topic/facts. Source text proves the narration; the picture need '
        'not show its exact action, historical date or microscopic mechanism. '
        'Reject unrelated subjects, drawings, synthetic imagery and photographs cutting off the main subject. '
        'visible_fact_details describe the concrete visible relationship without inventing hidden actions. '
        'Evaluate every visual_target as a practical composition role, not exact scientific proof. '
        'detail_prominent means that role is recognizable in the whole photo. '
        'Do not mark the same generic composition as every distinct role. '
        'Return one result for each supplied asset_id, preserving its identity; metadata is not proof.')

    def inspect(self, asset, evidence):
        targets = asset.get('visual_targets')
        result, provenance = self.gemini.generate('material-inspect:' + asset['id'],
            self.INSPECTION_INSTRUCTION,
            {'evidence': compact_evidence(evidence), 'visual_targets': targets,
             'metadata': {k: asset[k] for k in ('source_url', 'author', 'license')}},
            self._inspection_schema(evidence, targets), photo=self._photo(asset), max_tokens=2048)
        return self._inspection_receipt(asset, evidence, result, provenance)

    def inspect_many(self, assets, evidence):
        if not 1 <= len(assets) <= 4 or len({a['id'] for a in assets}) != len(assets):
            raise ValueError('bounded unique inspection batch required')
        targets = assets[0].get('visual_targets')
        if any(a.get('visual_targets') != targets for a in assets):
            raise ValueError('inspection batch roles differ')
        row_schema = self._inspection_schema(evidence, targets)
        row_schema['properties']['asset_id'] = string(a['id'] for a in assets)
        row_schema['required'].append('asset_id')
        schema = obj({'photos': array(row_schema, len(assets), len(assets))})
        context = {'evidence': compact_evidence(evidence), 'visual_targets': targets,
                   'assets': [{k: a[k] for k in ('id', 'source_url', 'author', 'license')} for a in assets]}
        try:
            result, provenance = self.gemini.generate('material-inspect-batch:' + digest([a['id'] for a in assets]),
                self.INSPECTION_INSTRUCTION, context, schema,
                photos=[self._photo(a) for a in assets], max_tokens=8192)
        except ModelSchemaError as error:
            # A completed bad individual row rejects that image, not its valid
            # neighbors. Provider failures/unknown calls are never retried.
            result, provenance = error.result, getattr(error, 'provenance', None)
            if not isinstance(result, dict) or set(result) != {'photos'} or not isinstance(result['photos'], list) or not provenance:
                raise
        identities = [r.get('asset_id') for r in result['photos'] if isinstance(r, dict)]
        if len(identities) != len(result['photos']) or len(set(identities)) != len(identities) or not set(identities) <= {a['id'] for a in assets}:
            raise ValueError('inspection batch invented or repeated asset identity')
        by_id = {r['asset_id']: r for r in result['photos']}
        receipts = []
        for asset in assets:
            row = by_id.get(asset['id'])
            try:
                validate_json(row, row_schema)
                row = {k: v for k, v in row.items() if k != 'asset_id'}
                receipts.append(self._inspection_receipt(asset, evidence, row, provenance))
            except ValueError:
                receipts.append({'asset_id': asset['id'], 'asset_sha256': asset['sha256'],
                    'evidence_sha256': digest(evidence), 'accepted': False,
                    'receipt_id': provenance['receipt_id'], 'model': self.gemini.model,
                    'rejection': 'completed malformed inspection row'})
        return receipts

    def compose(self, context):
        materials = context['materials']
        seconds = context['request']['seconds']
        minimum_words, maximum_words = round(seconds * 1.6), round(seconds * 2.4)
        minimum_available = 5
        if len(materials) < minimum_available:
            raise MaterialUnavailable("not enough distinct relevant photos for requested cadence")
        # Aim for frequent changes, but rejected candidates do not make a
        # longer short require a perfect 12/12 discovery/inspection batch.
        preferred_beats = min(len(materials), 8, max(5, (seconds + 7) // 8))
        minimum_beats = minimum_available
        schema = obj({'words': array(string(), minimum_words, maximum_words),
            'beats': array(obj({'material_id': string(m['id'] for m in materials),
                'word_start': {'type': 'number', 'minimum': 0, 'maximum': maximum_words},
                'word_end': {'type': 'number', 'minimum': 1, 'maximum': maximum_words},
                'fact_ids': array(string(f['id'] for f in context['evidence']['facts']), 1, 8)}),
                minimum_beats, min(len(materials), 8))})
        targets = context['request'].get('visual_targets')
        if targets is not None:
            beat_schema = schema['properties']['beats']['items']
            beat_schema['properties']['visual_target_id'] = string(t['id'] for t in targets)
            beat_schema['required'].append('visual_target_id')
        model_context = {**context, 'evidence': compact_evidence(context['evidence'])}
        instruction = (
            f'Write one natural factual script in the requested language. Return the script as a words array '
            f'of {minimum_words} to {maximum_words} individual words TOTAL, aiming for {round(seconds * 2.1)} '
            f'words for {seconds} seconds. Each words item is exactly one word, with punctuation attached. '
            'Do not return a shorter summary. Add useful source-supported explanation to fill the word budget, '
            'without repeating yourself or adding opening/closing filler. '
            f'Use {minimum_beats} to {preferred_beats} different supplied photographs, preferring {preferred_beats} '
            'for narration paragraphs. The renderer uses many more inspected photos independently of these paragraphs. Split on natural clause boundaries; '
            'do not demand two separate pictures for a role with only one available picture. '
            'Assign all words to consecutive beats using zero-based word_start and exclusive word_end. '
            'Use only supplied inspected anchor materials, each at most once. Source-backed facts may be explained over relevant contextual images; no literal proof of dates or invisible mechanisms is required. '
            'Cover required topic facts with practical, relevant visual variety. Do not assemble several '
            'variations of the same generic subject-and-setting photograph. Each beat must explain its concrete '
            'visible_fact_details without pretending invisible mechanisms are shown. '
            'When visual_targets are present, use at least two different available roles with materials whose matched_visual_targets '
            'includes it. Keep that target identity on its beat, explaining its visible detail. '
            'The continuous narration will be fitted once to the exact requested duration without changing pitch or re-synthesizing.')
        try:
            result, _ = self.gemini.generate('material-compose', instruction, model_context, schema)
        except ModelSchemaError as error:
            # Only a completed, structurally valid draft with a length mismatch
            # may get one distinct correction call. Never retry HTTP/unknowns.
            structural = deepcopy(schema)
            structural['properties']['words']['minItems'] = 1
            structural['properties']['words']['maxItems'] = 256
            validate_json(error.result, structural)
            if minimum_words <= len(error.result['words']) <= maximum_words:
                raise
            result, _ = self.gemini.generate('material-compose-length-repair',
                instruction + f' The completed draft contains {len(error.result["words"])} words; '
                f'rewrite it to {minimum_words}–{maximum_words} words, aiming for {round(seconds * 2.1)}. '
                'Expand or shorten source-supported explanations without repetition or invented claims. '
                'Reassign the complete revised words array to consecutive beats.',
                {**model_context, 'completed_draft': error.result}, schema)
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
            # Some valid provider drafts miss the last one or two words in
            # the final exclusive range. Keep the canonical script intact.
            if beats and 0 < len(words) - cursor <= 2:
                beats[-1]['narration'] += ' ' + ' '.join(words[cursor:])
            else:
                raise ValueError('narration words omitted from story')
        return {'beats': beats}

    def review_script(self, context):
        return self.gemini.review_script(context)
