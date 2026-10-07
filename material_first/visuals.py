"""Distinct visual pool, scheduled independently from narration paragraphs."""
import math
from .presentation import preferred_shots, visual_timeline, minimum_shots, phrase_frames, CALM_POLICY, WHOLE_POLICIES

POLICY = 'whole-photo-exact-v1'


def candidate_limit(seconds, policy=POLICY):
    return preferred_shots(seconds, policy) + 12


def make_visuals(seconds, materials, scenes, policy=POLICY):
    minimum = minimum_shots(seconds,policy)
    if len(materials) < minimum:
        raise ValueError('not enough inspected distinct photos for requested cadence')
    by_id = {m['id']: m for m in materials}
    selected = []
    # Preserve narration anchors, then rotate practical composition roles.
    for scene in scenes:
        if scene['material_id'] not in selected:
            selected.append(scene['material_id'])
    groups = {}
    for m in materials:
        role = next(iter(m.get('matched_visual_targets', {})), 'context')
        groups.setdefault(role, []).append(m['id'])
    count = min(len(materials), max(preferred_shots(seconds,policy), len(selected)), 32)
    while len(selected) < count:
        progressed = False
        for group in groups.values():
            candidate = next((identity for identity in group if identity not in selected), None)
            if candidate is not None and len(selected) < count:
                selected.append(candidate)
                progressed = True
        if not progressed:
            break
    visual_timeline(seconds, len(selected),policy)
    return [{'id': 'photo-' + str(i + 1), 'material_id': identity}
            for i, identity in enumerate(selected)]


def validate_visuals(payload, observations):
    visuals = payload.get('visuals')
    if not isinstance(visuals, list):
        raise ValueError('frozen visual pool missing')
    visual_timeline(payload['seconds'], len(visuals),payload['presentation_policy'])
    known = {m['id']: m for m in observations}
    ids, materials, hashes = set(), set(), set()
    for i, visual in enumerate(visuals, 1):
        if set(visual) != {'id', 'material_id'} or visual['id'] != 'photo-' + str(i):
            raise ValueError('visual identity or order changed')
        m = known.get(visual['material_id'])
        if m is None or m['media_type'] != 'photo':
            raise ValueError('visual has no inspected photograph')
        if visual['id'] in ids or m['id'] in materials or m['sha256'] in hashes:
            raise ValueError('duplicate visual photograph')
        ids.add(visual['id']); materials.add(m['id']); hashes.add(m['sha256'])
    if materials != {a['id'] for a in payload['assets']} or materials != set(known):
        raise ValueError('frozen visual pool differs from reviewed asset set')
    if not {s['material_id'] for s in payload['scenes']} <= materials:
        raise ValueError('narration anchor omitted from visual pool')
    if any(a.get('framing') != 'original-whole' for a in payload['assets']):
        raise ValueError('cropped asset cannot enter whole-photo presentation')
    return visuals


def ordered_visuals(payload, timings, source_duration_ms):
    """Prefer the current paragraph's role without repeating or holding photos."""
    policy = payload['presentation_policy']
    boundaries = phrase_frames(timings,source_duration_ms,payload['seconds']) if policy == CALM_POLICY else ()
    cuts = visual_timeline(payload['seconds'], len(payload['visuals']),policy,boundaries)
    observations = {m['id']: m for m in payload['observations']}
    unused = list(payload['visuals'])
    result = []
    for cut in cuts:
        midpoint_ms = ((cut['start_frame'] + cut['end_frame']) / 2
                       / (payload['seconds'] * 30) * source_duration_ms)
        index = min(range(len(timings)), key=lambda i:
                    max(timings[i]['start_ms'] - midpoint_ms,
                        midpoint_ms - timings[i]['end_ms'], 0))
        scene = payload['scenes'][index]
        def score(v):
            m = observations[v['material_id']]
            return (3 * (scene.get('visual_target_id') in m.get('matched_visual_targets', {}))
                    + len(set(scene['evidence_ids']) & set(m['supported_fact_ids'])))
        selected = max(unused, key=score)
        unused.remove(selected)
        result.append({**selected, **cut, 'narration_scene_id': scene['id']})
    return result
