"""Preserve explanatory visual targets independently of broad factual relevance."""
from factory_v3.preflight import digest


def validate_targets(targets, facts):
    if not isinstance(targets, list) or len(targets) != 3:
        raise ValueError('three distinct explanatory visual targets required')
    seen = set()
    for target in targets:
        if set(target) != {'id', 'fact_ids', 'must_show', 'must_not_show', 'query'}:
            raise ValueError('invalid visual target contract')
        if not isinstance(target['id'], str) or not target['id'].strip() or target['id'] in seen:
            raise ValueError('unique visual target identity required')
        seen.add(target['id'])
        if not target['fact_ids'] or not set(target['fact_ids']) <= set(facts):
            raise ValueError('visual target must bind source facts')
        if any(not isinstance(target[k], str) or not target[k].strip()
               for k in ('must_show', 'must_not_show', 'query')):
            raise ValueError('visual target needs concrete inclusion, exclusion and search')
    if len({t['must_show'].strip().casefold() for t in targets}) != 3:
        raise ValueError('repeated visual target is not explanatory variety')
    return {t['id']: t for t in targets}


def matched_targets(asset, receipt):
    targets = asset.get('visual_targets')
    if targets is None:
        return None  # Historical immutable plans keep their original contract.
    known = validate_targets(targets, {f for t in targets for f in t['fact_ids']})
    if receipt.get('visual_targets_sha256') != digest(targets):
        raise ValueError('inspection was not bound to exact visual targets')
    matches = receipt.get('target_matches')
    if not isinstance(matches, list):
        raise ValueError('missing visual target inspection')
    result, seen = {}, set()
    for match in matches:
        identity = match.get('target_id')
        if identity not in known or identity in seen:
            raise ValueError('invented or repeated inspected visual target')
        seen.add(identity)
        if (match.get('matches') is not True or match.get('detail_prominent') is not True
                or not isinstance(match.get('visible_detail'), str) or not match['visible_detail'].strip()):
            continue
        result[identity] = match['visible_detail'].strip()
    if seen != set(known):
        raise ValueError('every visual target must be inspected')
    return result
