"""Source-owned beats with distinct inspected anchors; no generated fact IDs."""
from factory_v3.gemini import obj, string, validate_json


def distinct_fact_anchors(required, photos):
    """Maximum matching for facts actually observed in the inspected corpus.

    Unobserved mechanisms are deliberately not invented as pixel requirements.
    An observed fact may not silently fall back to unrelated topical context
    merely because another fact consumed its sole photograph.
    """
    owners={}
    eligible={fact:[i for i,p in enumerate(photos)
                    if fact in p['supported_fact_ids']] for fact in required}
    def match(fact, seen):
        for index in eligible[fact]:
            if index in seen:continue
            seen.add(index)
            if index not in owners or match(owners[index],seen):
                owners[index]=fact
                return True
        return False
    for fact in required:
        if eligible[fact]:match(fact,set())
    observed={fact for fact,indices in eligible.items() if indices}
    return {fact:photos[index] for index,fact in owners.items()},observed


def sufficient_fact_anchors(required, photos):
    matched,observed=distinct_fact_anchors(required,photos)
    return set(matched)==observed


def story_contract(request,evidence,photos):
    required=request['required_fact_ids']
    facts={f['id']:f for f in evidence['facts']}
    if len(required)!=3 or len(set(required))!=3 or not set(required)<=facts.keys():
        raise ValueError('three distinct required source facts needed')
    if len(photos)<3 or len({p['id'] for p in photos})!=len(photos) or len({p['sha256'] for p in photos})!=len(photos):
        raise ValueError('distinct inspected photo identities needed')
    matched,observed=distinct_fact_anchors(required,photos)
    if set(matched)!=observed:
        raise ValueError('insufficient distinct anchors for observed required facts')
    used={p['id'] for p in matched.values()}
    remaining=[p for p in photos if p['id'] not in used
               and set(p['supported_fact_ids']) & set(required)]
    for fact in required:
        if fact not in matched:
            if not remaining:raise ValueError('insufficient topical anchors for unobserved facts')
            matched[fact]=remaining.pop(0)
    beats={f'beat_{i}':{'material_id':matched[fact]['id'],
        'fact_ids':[fact],'required_claim':facts[fact]['text'],
        'visual_relation':'direct_fact_visual' if fact in observed else 'topic_context'}
        for i,fact in enumerate(required,1)}
    schema=obj({key:obj({'narration':{**string(),'maxLength':2400}}) for key in beats})
    return beats,schema


def assemble_story(reply,beats,schema):
    validate_json(reply,schema)
    return {'beats':[{'material_id':beat['material_id'],
                     'fact_ids':list(beat['fact_ids']),
                     'narration':reply[key]['narration']} for key,beat in beats.items()]}
