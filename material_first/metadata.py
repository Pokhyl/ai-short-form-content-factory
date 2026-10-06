"""Deterministic metadata selection; never a claim of pixel/AI inspection."""
import re
from copy import deepcopy
from factory_v3.preflight import digest

METHOD = 'provider-metadata-v1'
STOP = {'photo','photograph','photography','close','closeup','detail','details','view','image','images','the','and','with','from','of','on','in','a','an'}

def words(text):
    return {word for word in re.findall(r'[a-z]+', text.casefold()) if len(word) >= 3 and word not in STOP}

def receipt(asset, evidence):
    targets = {target['id']:target for target in asset.get('visual_targets', [])}
    target = targets.get(asset.get('discovery_target_id'))
    description = str(asset.get('description', '')).strip()
    query = asset.get('discovery_query', '')
    relevant = bool(words(description) & words(query))
    excluded = bool(re.search(r'\b(?:illustration|diagram|drawing|rendering|generated|cartoon)\b', description, re.I))
    accepted = bool(target and query == target['query'] and description and relevant and not excluded and asset.get('media_type') == 'photo')
    identity = {key:asset.get(key) for key in ('id','sha256','description','discovery_target_id','discovery_query','visual_targets')}
    result = {'validation_method':'metadata', 'method_version':METHOD, 'accepted':accepted,
              'asset_id':asset['id'], 'asset_sha256':asset['sha256'], 'metadata_sha256':digest(identity),
              'evidence_sha256':digest(evidence)}
    result['receipt_id'] = digest(result)
    return result

def material(asset, observed, evidence, facts):
    expected = receipt(asset, evidence)
    if observed != expected:
        raise ValueError('metadata selection receipt changed')
    if not observed['accepted']:
        return None
    target = next(t for t in asset['visual_targets'] if t['id'] == asset['discovery_target_id'])
    if not set(target['fact_ids']) <= set(facts):
        raise ValueError('metadata role introduced unknown source facts')
    description = 'Provider metadata (pixels not reviewed): ' + asset['description'].strip()
    return {'id':asset['id'], 'media_type':'photo', 'sha256':asset['sha256'],
            'visible_description':description, 'supported_fact_ids':deepcopy(target['fact_ids']),
            'source_interval':None, 'capacity_ms':60000, 'inspection':deepcopy(observed),
            'matched_visual_targets':{target['id']:description}}
