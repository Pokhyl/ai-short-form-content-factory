"""Compile an edit from measured speech and the complete reviewed photo pool."""
from copy import deepcopy
import math

from material_first.presentation import TOPIC_POLICY, minimum_shots, preferred_shots
from material_first.visuals import ordered_visuals


class EditUnavailable(ValueError):
    pass


def compile_edit(story, photos, timings, audio_duration_ms, seconds):
    """No estimated speech lengths, voice changes, or premature pool truncation.

    Narration/source review and original-byte validation belong to the input
    adapter. This compiler requires their selected scene/fact identities and
    measured alignment; the final renderer must verify those bytes again.
    """
    preferred = preferred_shots(seconds, TOPIC_POLICY)
    if not isinstance(audio_duration_ms, (int, float)) or not math.isfinite(audio_duration_ms):
        raise EditUnavailable('finite measured audio duration required')
    if not seconds*1000-1000 <= audio_duration_ms <= seconds*1000:
        raise EditUnavailable('natural speech does not fit the requested duration')
    if not story or len(timings) != len(story):
        raise EditUnavailable('measured alignment must cover every paragraph')
    previous = 0
    for scene, timing in zip(story, timings):
        if not scene.get('narration', '').strip() or not scene.get('evidence_ids'):
            raise EditUnavailable('source-bound narration required')
        start, end = timing['start_ms'], timing['end_ms']
        if not all(isinstance(v,(float,int)) and math.isfinite(v) for v in (start,end)):
            raise EditUnavailable('finite alignment required')
        if not previous <= start < end <= audio_duration_ms:
            raise EditUnavailable('alignment overlaps or exceeds original audio')
        previous = end
    identities = [p['id'] for p in photos]
    hashes = [p['sha256'] for p in photos]
    if len(set(identities)) != len(photos) or len(set(hashes)) != len(photos):
        raise EditUnavailable('duplicate photograph')
    if any(p.get('media_type') != 'photo' or not p.get('supported_fact_ids') for p in photos):
        raise EditUnavailable('reviewed source-related photographs required')
    anchors = {s['material_id'] for s in story}
    if not anchors <= set(identities):
        raise EditUnavailable('narration anchor absent')
    payload = {'seconds':seconds,'presentation_policy':TOPIC_POLICY,
               'scenes':deepcopy(story),'observations':deepcopy(photos),
               'visuals':[{'id':'candidate-'+str(i),'material_id':p['id']} for i,p in enumerate(photos)]}
    minimum=max(minimum_shots(seconds, TOPIC_POLICY),len(anchors))
    maximum=min(len(photos),seconds*2//5)
    # Prefer moderate cadence, but search every legal density before refusing.
    sizes=sorted(range(minimum,maximum+1),key=lambda n:(abs(n-preferred),n))
    for count in sizes:
        try:
            selected=ordered_visuals(payload,timings,audio_duration_ms,
                                     slot_count=count,required_material_ids=anchors)
        except ValueError:
            continue
        shots=[{**v,'id':'photo-'+str(i+1)} for i,v in enumerate(selected)]
        return {'version':'measured-edit-v1','seconds':seconds,'frame_count':seconds*30,
                'audio_duration_ms':audio_duration_ms,'audio_tempo_factor':1.0,
                'tail_silence_ms':seconds*1000-audio_duration_ms,'shots':shots}
    raise EditUnavailable('reviewed photographs cannot cover measured speech')
