"""Bounded real photo search and source-backed narration adapters."""
from pathlib import Path
from factory_v3.gemini import obj, array, string, BOOL
from factory_v3.grounding import validate_evidence
from factory_v3.preflight import asset_path, digest, validate_asset
from factory_v3.providers import PROVIDERS


def preparation_budgets(seconds):
    return {'research_search': 1, 'source_fetch': 6, 'gemini': 15,
            'download': 12, 'metadata': 1, **{'search:' + p: 3 for p in PROVIDERS}}


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
            'Mark the essential facts. Give up to three English stock photograph searches for relevant '
            'subjects and settings. Do not create a storyboard or require a particular number of shots. '
            'Photographs may illustrate mechanisms explained by the sources without showing the motion itself.',
            {**request, 'sources': sources}, schema)
        evidence = {'sources': sources, 'facts': result['facts']}
        validate_evidence(evidence)
        return {'evidence': evidence, 'required_fact_ids': result['required_fact_ids'],
                'queries': result['queries']}

    def discover(self, request, queries):
        if not isinstance(queries, list) or not 1 <= len(queries) <= 3:
            raise ValueError('bounded material queries required')
        pools = []
        for query in queries:
            for provider in sorted(PROVIDERS):
                result = self.search.search(provider, query, 'all')
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
        schema = obj({'beats': array(obj({'material_id': string(m['id'] for m in materials),
            'narration': string(), 'fact_ids': array(string(f['id'] for f in context['evidence']['facts']), 1, 8)}),
            1, len(materials))})
        result, _ = self.gemini.generate('material-compose',
            'Write continuous natural narration answering the original topic in its requested language. '
            'Target about 2.1 words per second for requested duration; synthesis will retain natural speed. '
            'Select only supplied inspected materials, use each at most once, and use only facts it can '
            'illustrate. Cover required facts without inventing claims or describing motion as visible in '
            'a still. Choose a useful number of beats, no fixed shot count. No opening or closing filler.',
            context, schema)
        return result

    def review_script(self, context):
        return self.gemini.review_script(context)
