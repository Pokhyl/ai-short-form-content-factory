"""Distinct visual pool, scheduled independently from narration paragraphs."""
import math
from .presentation import preferred_shots, visual_timeline, minimum_shots, phrase_frames, CALM_POLICY, CALM_POLICIES, TOPIC_POLICY, WHOLE_POLICIES

POLICY = 'whole-photo-exact-v1'


class VisualCapacityError(ValueError):
    """No legal photo pool covers the estimated narration cadence."""



def candidate_limit(seconds, policy=POLICY):
    # Topic images pass strict pixel-level relevance checks; a broader bounded
    # candidate pool prevents a viable topic from dying on a thin search page.
    return preferred_shots(seconds, policy) + (27 if policy == TOPIC_POLICY else 12)


def make_visuals(seconds, materials, scenes, policy=POLICY, *, anchor_ids=()):
    minimum = minimum_shots(seconds,policy)
    if len(materials) < minimum:
        raise ValueError('not enough inspected distinct photos for requested cadence')
    by_id = {m['id']: m for m in materials}
    selected = []
    # Preserve narration anchors, then rotate practical composition roles.
    for scene in scenes:
        if scene['material_id'] not in by_id:
            raise ValueError('subject-related narration anchor absent from inspected pool')
        if scene['material_id'] not in selected:
            selected.append(scene['material_id'])
    for anchor in anchor_ids:
        if anchor not in by_id:
            raise ValueError('validated context anchor absent from inspected pool')
        if anchor not in selected:
            selected.append(anchor)
    groups = {}
    for m in materials:
        role = next(iter(m.get('matched_visual_targets', {})), 'context')
        groups.setdefault(role, []).append(m['id'])
    count = min(len(materials), max(preferred_shots(seconds,policy), len(selected)), 32)
    if policy == TOPIC_POLICY and all(s.get('narration','').strip() for s in scenes) and scenes:
        pool=[{'id':'candidate-'+str(i),'material_id':m['id']} for i,m in enumerate(materials)]
        payload={'seconds':seconds,'presentation_policy':policy,
                 'scenes':scenes,'observations':materials,'visuals':pool}
        # Preferred density is a target, not a requirement. Try smaller legal
        # pools before rejecting available, reviewed photographs. Every chosen
        # pool must satisfy both estimates, with all narration anchors retained.
        last_error = None
        for size in range(count, max(minimum, len(selected))-1, -1):
            for measure in ('words', 'characters'):
                try:
                    assigned=ordered_visuals(payload, estimated_timings(scenes, seconds, measure),
                        seconds*1000, slot_count=size, required_material_ids=selected)
                    visuals=[{'id':'photo-'+str(i+1),'material_id':v['material_id']}
                             for i,v in enumerate(assigned)]
                    preflight_visual_capacity({**payload, 'visuals':visuals})
                    return visuals
                except ValueError as error:
                    last_error = error
            visuals=common_visual_pool(payload,size,set(selected))
            if visuals is not None:
                preflight_visual_capacity({**payload,'visuals':visuals})
                return visuals
        raise VisualCapacityError('no subject-related photograph pool satisfies both cadence estimates: '
                         + str(last_error)) from last_error
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


def common_visual_pool(payload, size, required):
    """Common independent set of two photo/slot matchings, retaining anchors.

    Each estimate defines a transversal matroid. Contract the required photos
    and augment their common independent set; this avoids exponential subset
    enumeration and candidate-order-dependent false rejections.
    """
    from collections import deque
    photos=payload['visuals']; scenes=payload['scenes']; seconds=payload['seconds']
    observations={m['id']:m for m in payload['observations']}
    graphs=[]
    for measure in ('words','characters'):
        timings=estimated_timings(scenes, seconds, measure)
        cuts=visual_timeline(seconds,size,payload['presentation_policy'],
                            phrase_frames(timings,seconds*1000,seconds))
        graph={i:[] for i in range(len(photos))}
        for slot,cut in enumerate(cuts):
            midpoint=(cut['start_frame']+cut['end_frame'])/60*1000
            scene=scenes[min(range(len(timings)),key=lambda i:max(
                timings[i]['start_ms']-midpoint,midpoint-timings[i]['end_ms'],0))]
            for i,photo in enumerate(photos):
                if set(scene['evidence_ids']) & set(observations[photo['material_id']]['supported_fact_ids']):
                    graph[i].append(slot)
        graphs.append(graph)
    mandatory={i for i,p in enumerate(photos) if p['material_id'] in required}
    def independent(chosen,graph):
        owners={}
        def assign(photo,seen):
            for slot in graph[photo]:
                if slot in seen:continue
                seen.add(slot)
                if slot not in owners or assign(owners[slot],seen):
                    owners[slot]=photo;return True
            return False
        return all(assign(i,set()) for i in sorted(chosen))
    if any(not independent(mandatory,g) for g in graphs):return None
    chosen=set(mandatory); ground=set(range(len(photos)))
    while len(chosen)<size:
        outside=sorted(ground-chosen)
        sources=[x for x in outside if independent(chosen|{x},graphs[0])]
        parents={x:None for x in sources}; queue=deque(sources); end=None
        while queue:
            x=queue.popleft()
            if x not in chosen:
                if independent(chosen|{x},graphs[1]):end=x;break
                neighbors=[y for y in sorted(chosen-mandatory)
                           if independent((chosen-{y})|{x},graphs[1])]
            else:
                neighbors=[y for y in outside if independent((chosen-{x})|{y},graphs[0])]
            for y in neighbors:
                if y not in parents:parents[y]=x;queue.append(y)
        if end is None:return None
        while end is not None:
            chosen.symmetric_difference_update({end});end=parents[end]
    return [{'id':'photo-'+str(j+1),'material_id':photos[i]['material_id']}
            for j,i in enumerate(sorted(chosen))]


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


def ordered_visuals(payload, timings, source_duration_ms, *, slot_count=None, required_material_ids=()):
    """Align cuts to paragraphs; topical plans never fill a slot with zero relevance."""
    policy = payload['presentation_policy']
    boundaries = phrase_frames(timings,source_duration_ms,payload['seconds']) if policy in CALM_POLICIES else ()
    cuts = visual_timeline(payload['seconds'], slot_count or len(payload['visuals']),policy,boundaries)
    observations = {m['id']: m for m in payload['observations']}
    slots=[]
    for cut in cuts:
        midpoint_ms = (cut['start_frame']+cut['end_frame'])/2/(payload['seconds']*30)*source_duration_ms
        index=min(range(len(timings)),key=lambda i:max(timings[i]['start_ms']-midpoint_ms,midpoint_ms-timings[i]['end_ms'],0))
        slots.append((cut,payload['scenes'][index]))
    def score(v,scene):
        material=observations[v['material_id']]
        overlap=len(set(scene['evidence_ids']) & set(material['supported_fact_ids']))
        # A reviewed narration anchor is already bound to this exact photo by
        # the story stage. Keep that explicit relation usable when fact IDs
        # differ across independently generated stages.
        anchor_match = scene.get('material_id') == material.get('id')
        if policy==TOPIC_POLICY and not overlap and not anchor_match: return 0
        return 3*(scene.get('visual_target_id') in material.get('matched_visual_targets',{}))+overlap+int(anchor_match)
    if policy!=TOPIC_POLICY:
        unused=list(payload['visuals']);result=[]
        for cut,scene in slots:
            chosen=max(unused,key=lambda v:score(v,scene));unused.remove(chosen)
            result.append({**chosen,**cut,'narration_scene_id':scene['id']})
        return result
    options=[[i for i,v in sorted(enumerate(payload['visuals']),key=lambda row:-score(row[1],scene)) if score(v,scene)>0]
             for _,scene in slots]
    if required_material_ids:
        required=set(required_material_ids)
        order=sorted(range(len(payload['visuals'])),key=lambda i:payload['visuals'][i]['material_id'] not in required)
        owners={}
        def assign_photo(photo,visited):
            for slot in range(len(slots)):
                if photo not in options[slot] or slot in visited:continue
                visited.add(slot)
                if slot not in owners or assign_photo(owners[slot],visited):
                    owners[slot]=photo
                    return True
            return False
        for photo in order:
            if len(owners)==len(slots):break
            if not assign_photo(photo,set()) and payload['visuals'][photo]['material_id'] in required:
                raise ValueError('no subject-related photograph for a narration interval')
        if len(owners)!=len(slots):
            raise ValueError('no subject-related photograph for a narration interval')
        return [{**payload['visuals'][owners[i]],**cut,'narration_scene_id':scene['id']}
                for i,(cut,scene) in enumerate(slots)]
    owners={}
    def assign(slot,visited):
        for photo in options[slot]:
            if photo in visited: continue
            visited.add(photo)
            if photo not in owners or assign(owners[photo],visited):
                owners[photo]=slot
                return True
        return False
    for slot in sorted(range(len(slots)),key=lambda i:len(options[i])):
        if not assign(slot,set()): raise ValueError('no subject-related photograph for a narration interval')
    assignment={slot:photo for photo,slot in owners.items()}
    return [{**payload['visuals'][assignment[i]],**cut,'narration_scene_id':scene['id']} for i,(cut,scene) in enumerate(slots)]


def estimated_timings(scenes, seconds, measure):
    weights = [len(scene['narration'].split()) if measure == 'words'
               else len(scene['narration'].strip()) for scene in scenes]
    if any(weight <= 0 for weight in weights):
        raise ValueError('topical visual preflight requires nonempty narration scenes')
    total = sum(weights)
    cursor = 0
    timings = []
    for weight in weights:
        end = cursor + seconds * 1000 * weight / total
        timings.append({'start_ms': cursor, 'end_ms': end})
        cursor = end
    timings[-1]['end_ms'] = seconds * 1000
    return timings


def preflight_visual_capacity(payload):
    """Reject topical plans whose estimated scene cadence exceeds relevant photos.

    Actual TTS timings are not available before voice synthesis. Check both word-
    and character-weighted timing estimates so a scene that dominates either
    estimate cannot consume synthesis/alignment before its visual pool is known
    to be insufficient. This is a conservative early stop; render still checks
    the exact measured timings.
    """
    if payload.get('presentation_policy') != TOPIC_POLICY:
        return
    scenes = payload.get('scenes', [])
    if not scenes:
        raise ValueError('topical visual preflight requires narration scenes')
    seconds = payload['seconds']
    for measure in ('words', 'characters'):
        timings = estimated_timings(scenes, seconds, measure)
        try:
            ordered_visuals(payload, timings, seconds * 1000)
        except ValueError as error:
            raise ValueError('topical visual pool cannot cover ' + measure +
                             '-weighted scene cadence before voice: ' + str(error)) from error
