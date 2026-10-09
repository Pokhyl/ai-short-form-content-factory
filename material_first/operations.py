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
from .visuals import POLICY, CALM_POLICY, CALM_POLICIES, TOPIC_POLICY, WHOLE_POLICIES, candidate_limit
from .source_spans import source_spans, bind_support
from .photo_queries import photograph_query, described_as_synthetic, relevance


def preparation_budgets(seconds):
    return {'research_search': 1, 'source_fetch': 6, 'gemini': 16,
            'download': candidate_limit(seconds,TOPIC_POLICY), 'metadata': 1, **{'search:' + p: 3 for p in PROVIDERS}}


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
    presentation_policy = TOPIC_POLICY

    def __init__(self, root, research, gemini, search, downloader, *, documented_contexts=False):
        self.root = Path(root)
        self.source, self.gemini, self.search, self.downloader = research, gemini, search, downloader
        self.documented_contexts = documented_contexts

    def speech_timing_budget(self, language, seconds):
        from .speech_timing import timing_budget
        return timing_budget(self.root, language, seconds)

    def research(self, request):
        self.topic = request['topic']
        sources = self.source.fetch(request['topic'], request['language'])
        spans = source_spans(sources)
        schema = obj({'facts': array(obj({'id': string(), 'text': string(),
            'support': array(obj({'span_id': string(s['id'] for s in spans)}), 1, 3)}), 3, 8),
            'required_fact_ids': array(string(), 3, 8),
            'photo_contexts': obj({role: obj({'subject': string(),
                'query': {**string(), 'maxLength': 100}, 'fact_ids': array(string(), 1, 8)})
                for role in ('setting', 'subject', 'detail')})})
        measured_feedback = getattr(self,'voice_correction_enabled',False)
        if measured_feedback:
            schema['properties']['required_fact_ids']=array(string(),3,3)
        desired_facts = max(3, min(6 if measured_feedback else 8, (request['seconds'] + 7) // 8))
        if self.documented_contexts:
            for context_schema in schema['properties']['photo_contexts']['properties'].values():
                context_schema['properties']['support_span_ids'] = array(string(s['id'] for s in spans), 1, 3)
                context_schema['required'].append('support_span_ids')
        result, _ = self.gemini.generate('material-brief',
            (('Select exactly THREE essential atomic facts that together answer the topic: starting condition, main mechanism, outcome. '
              'Keep each fact a concise single claim; split compound source explanations into optional facts. '
              'Do not make every discovered fact mandatory or require every source detail/number in the narration. ' if measured_feedback else '') +
            f'For {request["seconds"]} seconds, aim for {desired_facts} distinct source-backed facts, '
            'with enough useful explanation for natural speech. Cover the full requested process, '
            'including its final outcome; do not spend all facts on its starting ingredients. '
            'Extract at least three distinct atomic explanatory facts answering the topic. '
            'For each fact select support.span_id from the supplied source_spans; the server copies the exact original text. '
            'Select only spans that actually support that fact, including its qualifiers and numbers. '
            'Separate the starting condition, concrete mechanism/details, and consequence or purpose where supported. '
            'Do not merge multiple mechanisms into one broad topic statement, or paraphrase the same fact to fill slots. '
            'Mark at least three essential distinct facts for narration. Separately define photo_contexts: '
            'setting, subject, detail. Each has a concrete physical subject, a short English entity-focused search query, and fact_ids explaining its direct relationship to specific supplied facts. '
            'Every subject must be the actual requested object, its genuine physical component or stage, or a specifically identified associated object. Never substitute a generic parent category, decorative scenery, a laboratory prop or a visual analogy. For hidden, microscopic, '
            'historical or distant subjects seek documented observations and named associated objects. Do not use unrelated scientific equipment, atomic models or generic landscapes merely because they share a broad theme. '
            'Never request a diagram, cross-section, field lines, imagined particle beams, space art or a synthetic rendering. '
            'Prefer several documented related objects or genuine process stages over generic stock categories. Do not imply that an unrelated subject depicts an invisible mechanism. '
            'When support_span_ids are required, select source spans explicitly documenting each photo subject and its relationship. '
            'For distant or hidden subjects, search named observable associated objects mentioned in those spans, using their conventional English name or catalog identifier. '
            'For a named associated object, the query is just its searchable entity name or catalog identifier, not an entire mechanism or a demand for photographic proof. '
            'Do not waste a query on an invisible object when the sources name observable associated objects. '
            'Avoid generic search padding such as space, astronomy or telescope: retain the physical subject and defining qualifiers. '
            'The three contexts must differ in dominant subject, scale or setting. '
            'For example, a flowering meadow, a bee close-up, and a flower/pollen detail are different roles. '
            'Allow contextually relevant stock photographs; do not demand a rare precise action or anatomy angle. '
            'Facts are proved by source text, not photograph geometry.'),
            {**request, 'sources': [{k: s[k] for k in ('id', 'url', 'title', 'sha256') if k in s}
                                   for s in sources], 'source_spans': spans}, schema)
        evidence = bind_support(sources, spans, result['facts'])
        if self.documented_contexts:
            contexts = []
            for index, role in enumerate(('setting', 'subject', 'detail')):
                row = result['photo_contexts'][role]
                bound = bind_support(sources, spans, [{'id': role, 'text': row['subject'],
                    'support': [{'span_id': identity} for identity in row['support_span_ids']]}])
                contexts.append({'id': 'v' + str(index), 'subject': row['subject'],
                    'query': photograph_query(row['query']), 'support': bound['facts'][0]['support']})
            evidence['visual_contexts'] = contexts
        validate_evidence(evidence)
        if measured_feedback and len(set(result['required_fact_ids'])) != 3:
            raise ValueError('measured narration requires exactly three essential facts')
        if len(set(result['required_fact_ids'])) < 3:
            raise MaterialUnavailable('explanation needs three distinct source-backed aspects before material search')
        fact_ids = [f['id'] for f in evidence['facts']]
        if not set(result['required_fact_ids']) <= set(fact_ids):
            raise ValueError('required narration facts unknown')
        targets = [{'id': 'v' + str(i), 'fact_ids': result['photo_contexts'][role]['fact_ids'][:],
                    'must_show': (photograph_query(result['photo_contexts'][role]['query'])
                                  if request.get('presentation_policy') == TOPIC_POLICY else result['photo_contexts'][role]['subject']),
                    'must_not_show': 'Drawings, diagrams, synthetic images, unrelated subjects or identical composition in every role',
                    'query': (photograph_query(result['photo_contexts'][role]['query'])
                              if request.get('presentation_policy') == TOPIC_POLICY else result['photo_contexts'][role]['query'])}
                   for i, role in enumerate(('setting', 'subject', 'detail'))]
        validate_targets(targets, fact_ids)
        return {'evidence': evidence, 'required_fact_ids': result['required_fact_ids'],
                'queries': targets, 'visual_targets': targets}

    def discover(self, request, queries):
        if not isinstance(queries, list) or not 1 <= len(queries) <= 3:
            raise ValueError('bounded material queries required')
        pools, query_pools = [], []
        topical = request.get('presentation_policy') == TOPIC_POLICY
        targets = queries if queries and isinstance(queries[0], dict) else None
        for target in queries:
            query = target['query'] if targets else target
            query_pool = []
            for provider in (['wikimedia','pexels','pixabay'] if request.get('presentation_policy') == TOPIC_POLICY else sorted(PROVIDERS)):
                result = self.search.search(provider, query, 'all' if request.get('presentation_policy') in WHOLE_POLICIES else 'portrait')
                pool = deepcopy(result['candidates'])
                if request.get('presentation_policy') == TOPIC_POLICY:
                    pool = [candidate for candidate in pool if not described_as_synthetic(candidate)
                            and min(int(candidate.get('width',320)),int(candidate.get('height',320))) >= 320]
                    # Ranking, not a caption-only admission gate: sparse but
                    # relevant descriptions still reach independent inspection.
                    pool.sort(key=lambda candidate: -relevance(candidate, query))
                if targets:
                    for candidate in pool:
                        candidate['discovery_target_id'] = target['id']
                        candidate['discovery_query'] = query
                pools.append(pool)
                query_pool.extend(pool)
            if topical:
                query_pool.sort(key=lambda candidate: -relevance(candidate, query))
                query_pools.append(query_pool)
        if topical:
            self.discovery_pools = deepcopy(pools)
            # Give every provider/query an initial exposure (including sparse
            # captions), then rank jointly within each query. Equal quotas per
            # provider must not bury a relevant fourth result behind stock filler.
            selected, seen = [], set()
            limit = candidate_limit(request['seconds'], TOPIC_POLICY)
            def take(candidate):
                if candidate['id'] in seen:
                    return
                candidate = deepcopy(candidate)
                if targets:
                    candidate['visual_targets'] = deepcopy(targets)
                candidate['topic_protocol'] = 'topic-specific-v1'
                candidate['visual_qualification_protocol'] = 'qualified-target-v1'
                selected.append(candidate)
                seen.add(candidate['id'])
            for pool in pools:
                first = next((c for c in pool if c['id'] not in seen), None)
                if first is not None:
                    take(first)
                    if len(selected) == limit:
                        return selected
            while len(selected) < limit:
                before = len(selected)
                for pool in query_pools:
                    first = next((c for c in pool if c['id'] not in seen), None)
                    if first is not None:
                        take(first)
                        if len(selected) == limit:
                            return selected
                if len(selected) == before:
                    break
            return selected
        # Round-robin provider/query results rather than exhausting one provider.
        selected, seen = [], set()
        for rank in range(40):
            for pool in pools:
                if rank < len(pool) and pool[rank]['id'] not in seen:
                    candidate = deepcopy(pool[rank])
                    if targets:
                        candidate['visual_targets'] = deepcopy(targets)
                    if request.get('presentation_policy') == TOPIC_POLICY:
                        candidate['topic_protocol'] = 'topic-specific-v1'
                        candidate['visual_qualification_protocol'] = 'qualified-target-v1'
                    selected.append(candidate); seen.add(candidate['id'])
                    if len(selected) == candidate_limit(request['seconds'],request.get('presentation_policy',POLICY)):
                        return selected
        return selected

    def resolve_photos(self, request, brief):
        candidates = self.discover(request, brief['queries'])
        if (request.get('presentation_policy') != TOPIC_POLICY
                or request.get('visual_validation_mode', 'gemini') == 'metadata'):
            return brief, candidates
        from .photo_planning import plan_photos
        # Collect the complete bounded search pools first. Role contracts are
        # finalized once from available objects before any download/inspection.
        return plan_photos(self.gemini, request, brief, self.discovery_pools,
                           candidate_limit(request['seconds'], TOPIC_POLICY))

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

    @staticmethod
    def _image_metadata(asset):
        return {**{key:asset[key] for key in ('source_url','author','license')},
                'description':str(asset.get('description',''))[:4000],
                'file_title':str(asset.get('source_metadata',{}).get('title',''))[:500],
                **({'related_object_metadata': deepcopy(asset['related_object_metadata'])}
                   if asset.get('related_object_metadata') else {})}

    def _inspection_schema(self, evidence, targets, qualified=False):
        schema = obj({'accepted': BOOL, 'is_real_material': BOOL,
            'medium': string(['photograph','observational_image','illustration','synthetic','unknown']),
            'topic_relation': obj({'kind': string(['direct_subject','direct_part_or_stage','generic_analogy','unrelated','unknown']), 'visible_subject': string(), 'connection': string()}),
            'subject_fully_visible': BOOL, 'visible_description': string(),
            'visible_fact_details': array(obj({'fact_id': string(f['id'] for f in evidence['facts']),
                                               'detail': string()}), 0, 8)})
        if targets is not None:
            schema['properties']['target_matches'] = array(obj({
                'target_id': string(t['id'] for t in targets), 'matches': BOOL,
                'detail_prominent': BOOL, 'visible_detail': string()}), len(targets), len(targets))
            schema['required'].append('target_matches')
            if qualified:
                row = schema['properties']['target_matches']['items']
                row['properties']['subject_qualifications_match'] = BOOL
                row['required'].append('subject_qualifications_match')
        return schema

    def _inspection_receipt(self, asset, evidence, result, provenance):
        result = deepcopy(result)
        details = result['visible_fact_details']
        if any(not item['detail'].strip() for item in details) or len({item['fact_id'] for item in details}) != len(details):
            raise ValueError('inspection must give unique visible evidence per fact')
        result['supported_fact_ids'] = [item['fact_id'] for item in details]
        result['inspection_protocol'] = 'topic-specific-v1'
        relation = result['topic_relation']
        result['accepted'] = (result['accepted'] and result['subject_fully_visible'] and bool(details)
            and result['medium'] in {'photograph','observational_image'}
            and relation['kind'] in {'direct_subject','direct_part_or_stage'}
            and bool(relation['visible_subject'].strip()) and bool(relation['connection'].strip()))
        if asset.get('visual_targets') is not None:
            result['visual_targets_sha256'] = digest(asset['visual_targets'])
            if asset.get('visual_qualification_protocol') == 'qualified-target-v1':
                result['visual_qualification_protocol'] = 'qualified-target-v1'
        return {**result, 'asset_id': asset['id'], 'asset_sha256': asset['sha256'],
                'evidence_sha256': digest(evidence), 'receipt_id': provenance['receipt_id'],
                'model': self.gemini.model, 'provider_provenance': provenance}

    INSPECTION_INSTRUCTION = (
        'Inspect each attached whole original photograph, identified by its preceding asset_id. '
        'Describe what is actually visible. Accept real photographs with a relevant subject, detail '
        'or setting for the supplied topic/facts. Source text proves the narration; the picture need '
        'not show its exact action, historical date or microscopic mechanism. '
        'Classify medium and topic_relation independently of accepted. generic_analogy means a prop, generic scenery or a different object offered as a metaphor. Reject these even if visually attractive or loosely associated with a scientific field. Require the actual requested subject or a directly related documented physical part/stage. A molecular model cannot depict a neutron star; a generic star field cannot identify a pulsar. Reject illustrations, synthetic images and unknown origins. Observational astronomical composites may be accepted when their actual depicted object is directly relevant. '
        'visible_fact_details describe the concrete visible relationship without inventing hidden actions. '
        'Evaluate every visual_target as a practical composition role, not exact scientific proof. '
        'detail_prominent means that role is recognizable in the whole photo. '
        'subject_qualifications_match evaluates the requested object class and defining qualifiers separately: '
        'a generic member of a broader class is insufficient. A Sun image does not establish a massive '
        'supernova progenitor; a generic bright star does not identify a neutron star. Use the depicted '
        'object and reliable object-identifying metadata; if its defining qualifications are unknown, return false. '
        'A documented associated remnant or physical stage can still match its own requested contextual role. '
        'Check documented visual_contexts and related_object_metadata for the actual relationship and incompatible subtypes. '
        'A shared general category does not establish a shared mechanism or outcome; an image of a different subtype must not be described as the narrated process. '
        'Use corroborating records only when they identify the same object. Unknown or contradicted relationships are not direct_part_or_stage. '
        'Do not mark the same generic composition as every distinct role. '
        'Return one result for each supplied asset_id, preserving its identity; metadata is not proof.')

    def inspect(self, asset, evidence):
        targets = asset.get('visual_targets')
        result, provenance = self.gemini.generate('material-inspect:' + asset['id'],
            self.INSPECTION_INSTRUCTION,
            {'topic': getattr(self,'topic',None), 'evidence': compact_evidence(evidence), 'visual_targets': targets,
             'metadata': self._image_metadata(asset)},
            self._inspection_schema(evidence, targets, asset.get('visual_qualification_protocol') == 'qualified-target-v1'), photo=self._photo(asset), max_tokens=2048)
        return self._inspection_receipt(asset, evidence, result, provenance)

    def inspect_many(self, assets, evidence):
        if not 1 <= len(assets) <= 4 or len({a["id"] for a in assets}) != len(assets):
            raise ValueError("bounded unique inspection batch required")
        if getattr(self, "visual_validation_mode", "gemini") == "metadata":
            from .metadata import receipt
            for asset in assets:
                self._photo(asset)
            return [receipt(asset, evidence) for asset in assets]
        if not 1 <= len(assets) <= 4 or len({a['id'] for a in assets}) != len(assets):
            raise ValueError('bounded unique inspection batch required')
        targets = assets[0].get('visual_targets')
        if any(a.get('visual_targets') != targets for a in assets):
            raise ValueError('inspection batch roles differ')
        qualified = assets[0].get('visual_qualification_protocol') == 'qualified-target-v1'
        if any((a.get('visual_qualification_protocol') == 'qualified-target-v1') != qualified for a in assets):
            raise ValueError('inspection batch qualification contracts differ')
        photos = [self._photo(asset) for asset in assets]
        if any(not 0 < len(photo['bytes']) <= 8 * 1024 * 1024 for photo in photos):
            raise ValueError('photo input exceeds byte budget')
        if sum(len(photo['bytes']) for photo in photos) > 8 * 1024 * 1024:
            # Partition exact original bytes before any model claim. Each smaller
            # group still uses the same durable per-request Gemini budget.
            groups, group, size = [], [], 0
            for asset, photo in zip(assets, photos):
                length = len(photo['bytes'])
                if group and size + length > 8 * 1024 * 1024:
                    groups.append(group); group, size = [], 0
                group.append(asset); size += length
            groups.append(group)
            return [receipt for group in groups for receipt in self.inspect_many(group, evidence)]
        row_schema = self._inspection_schema(evidence, targets, qualified)
        row_schema['properties']['asset_id'] = string(a['id'] for a in assets)
        row_schema['required'].append('asset_id')
        schema = obj({'photos': array(row_schema, len(assets), len(assets))})
        context = {'topic': getattr(self,'topic',None), 'evidence': compact_evidence(evidence), 'visual_targets': targets,
                   'assets': [{'id':a['id'],**self._image_metadata(a)} for a in assets]}
        try:
            result, provenance = self.gemini.generate('material-inspect-batch:' + digest([a['id'] for a in assets]),
                self.INSPECTION_INSTRUCTION, context, schema,
                photos=photos, max_tokens=8192)
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
        if context['request'].get('presentation_policy') == TOPIC_POLICY:
            from .paragraphs import compose_paragraphs
            return compose_paragraphs(self.gemini, context, NarrationBudgetExceeded)
        materials = context['materials']
        seconds = context['request']['seconds']
        minimum_words, maximum_words = round(seconds * 1.6), round(seconds * 2.4)
        if context['request'].get('presentation_policy') in WHOLE_POLICIES:
            # Word count is an estimate. Actual voice duration and bounded
            # pitch-preserving fitting determine the exact delivery duration.
            minimum_words = max(1, minimum_words - 2)
            maximum_words += 2
        minimum_available = 3 if context['request'].get('presentation_policy') in WHOLE_POLICIES else 5
        if len(materials) < minimum_available:
            raise MaterialUnavailable("not enough distinct relevant photos for requested cadence")
        # Aim for frequent changes, but rejected candidates do not make a
        # longer short require a perfect 12/12 discovery/inspection batch.
        preferred_beats = min(len(materials), 8, max(5, (seconds + 7) // 8))
        minimum_beats = minimum_available
        maximum_beats = min(len(materials), 8)
        if context['request'].get('presentation_policy') in CALM_POLICIES:
            maximum_beats = min(maximum_beats, seconds * 2 // 5)
        schema = obj({'words': array(string(), minimum_words, maximum_words),
            'beats': array(obj({'material_id': string(m['id'] for m in materials),
                'word_start': {'type': 'number', 'minimum': 0, 'maximum': maximum_words},
                'word_end': {'type': 'number', 'minimum': 1, 'maximum': maximum_words},
                'fact_ids': array(string(f['id'] for f in context['evidence']['facts']), 1, 8)}),
                minimum_beats, maximum_beats)})
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
        if context['request'].get('visual_validation_mode') == 'metadata':
            instruction += (' Provider descriptions and discovery roles are metadata only, not pixel observations. '
                            'Explain source-supported facts over relevant contextual material; do not assert a specific '
                            'detail, person or action is visible based only on a caption.')
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
            # Preserve the canonical words array. A final range can omit a
            # trailing clause; attach it to the last paragraph and let the
            # independent factual/language reviewer inspect the full script.
            if beats and 0 < len(words) - cursor <= max(2, len(words) // 10):
                beats[-1]['narration'] += ' ' + ' '.join(words[cursor:])
            else:
                raise ValueError('narration words omitted from story')
        return {'beats': beats}

    def review_script(self, context):
        return self.gemini.review_script(context)
