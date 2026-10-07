"""Controlled availability planner over real saved pools; never calls a provider."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from factory_v3.gemini import validate_json
from material_first.operations import Operations
from material_first.presentation import TOPIC_POLICY


def replay():
    root = Path(__file__).resolve().parents[1]
    path = root / 'tests/material_first/fixtures/availability-query-pools.json'
    saved = json.loads(path.read_text())
    searches, models = [], []
    def search(provider, query, orientation):
        searches.append((provider, query, orientation))
        return {'candidates': next(p['candidates'] for p in saved['pools']
                                   if p['provider'] == provider and p['query'] == query)}
    def generate(key, instruction, context, schema):
        if key != 'material-photo-plan':
            raise ValueError('unexpected model boundary')
        models.append(key)
        validate_json(saved['controlled_plan'], schema)
        return saved['controlled_plan'], {'receipt_id': 'controlled-saved-pool-planner'}
    ops = Operations('.', None, SimpleNamespace(generate=generate), SimpleNamespace(search=search), None)
    brief = {'evidence': saved['evidence'], 'required_fact_ids': ['f1', 'f2', 'f3'],
             'queries': saved['targets'], 'visual_targets': saved['targets']}
    resolved, selected = ops.resolve_photos(
        {'topic': 'Нейтронная звезда', 'seconds': 60, 'presentation_policy': TOPIC_POLICY}, brief)
    original = set(saved['selected_ids'])
    return {'saved_request': saved['saved_request'],
            'fixture_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'scope': saved['controlled_plan_note'], 'new_provider_calls': 0,
            'new_model_calls': 0, 'database_writes': 0, 'new_tts_calls': 0,
            'saved_searches': len(searches), 'controlled_model_steps': models,
            'selected_count': len(selected), 'original_required_facts_unchanged': resolved['required_fact_ids'] == brief['required_fact_ids'],
            'original_evidence_unchanged': resolved['evidence'] == brief['evidence'],
            'new_targets': resolved['visual_targets'],
            'selected_query_origins': dict(Counter(c['discovery_target_id'] for c in selected)),
            'newly_exposed': [{'id': c['id'], 'description': c.get('description', '')}
                              for c in selected if c['id'] not in original],
            'pixel_approval': False, 'current_provider_plan_verified': False,
            'video_created': False, 'human_pass': False}


if __name__ == '__main__':
    print(json.dumps(replay(), ensure_ascii=False, indent=2))
