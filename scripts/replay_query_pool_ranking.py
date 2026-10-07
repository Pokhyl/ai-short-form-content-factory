"""Compare bounded selection on saved provider results, with no network calls."""
import json
from pathlib import Path
from types import SimpleNamespace
from material_first.operations import Operations
from material_first.photo_queries import described_as_synthetic
from material_first.metadata import words
from material_first.presentation import TOPIC_POLICY

def replay():
    root=Path(__file__).resolve().parents[1]
    saved=json.loads((root/'tests/material_first/fixtures/saved-neutron-query-pools.json').read_text())
    calls=[]
    def search(provider,query,orientation):
        calls.append((provider,query,orientation))
        pool=next(p for p in saved['pools'] if p['provider']==provider and p['query']==query)
        return {'candidates':pool['candidates']}
    new=Operations('.',None,None,SimpleNamespace(search=search),None).discover(
        {'seconds':60,'presentation_policy':TOPIC_POLICY},saved['targets'])
    old_pools=[]
    for pool in saved['pools']:
        candidates=[c for c in pool['candidates'] if not described_as_synthetic(c)]
        candidates.sort(key=lambda c:-len(words(c.get('description',''))&words(pool['query'])))
        old_pools.append(candidates)
    old=[];seen=set()
    for rank in range(40):
        for pool in old_pools:
            if rank<len(pool) and pool[rank]['id'] not in seen:
                seen.add(pool[rank]['id']);old.append(pool[rank])
                if len(old)==30:break
        if len(old)==30:break
    old_ids={c['id'] for c in old};new_ids={c['id'] for c in new}
    return {'saved_request':saved['saved_request'],'new_provider_calls':0,'database_writes':0,
            'old_selected':len(old),'new_selected':len(new),'saved_searches_replayed':len(calls),
            'old_provider_counts':{p:sum(c['provider']==p for c in old) for p in ['wikimedia','pexels','pixabay']},
            'new_provider_counts':{p:sum(c['provider']==p for c in new) for p in ['wikimedia','pexels','pixabay']},
            'newly_exposed':[{'id':c['id'],'description':c['description'],'source_url':c['source_url']} for c in new if c['id'] not in old_ids],
            'new_selected_ids':[c['id'] for c in new],
            'pixel_relevance_certified':False}
if __name__=='__main__':print(json.dumps(replay(),ensure_ascii=False,indent=2))
