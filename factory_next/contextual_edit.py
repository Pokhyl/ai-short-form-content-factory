"""Bind contextual alternatives to the exact independently reviewed anchor target."""
from material_first.targets import matched_targets
from material_first.visual_entailment import verified
from factory_v3.preflight import digest


def contextual_alternatives(story, photos, assets, evidence):
    assets = {a['id']: a for a in assets}
    qualified = {}
    for photo in photos:
        asset = assets.get(photo['id'])
        receipt = photo.get('inspection', {})
        if (not asset or asset.get('sha256') != photo['sha256']
                or asset.get('visual_qualification_protocol') != 'qualified-target-v1'
                or receipt.get('accepted') is not True):
            continue
        try:
            if not verified(asset, evidence, receipt):
                continue
            matches = matched_targets(asset, receipt)
        except (ValueError, KeyError, TypeError):
            continue
        qualified[photo['id']] = {
            digest(target) for target in asset['visual_targets']
            if target['id'] in matches}
    result = {}
    for scene in story:
        if (scene.get('visual_relation') != 'topic_context'
                or scene.get('contract', {}).get('contextual_not_direct_proof') is not True):
            continue
        anchor = qualified.get(scene['material_id'], set())
        result[scene['id']] = [identity for identity, targets in qualified.items()
                               if anchor & targets]
    return result
