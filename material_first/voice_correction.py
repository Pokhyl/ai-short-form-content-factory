"""Bounded measured-duration correction; completed samples are never retried."""
from copy import deepcopy
from factory_v3.preflight import digest
from factory_v3.gemini import obj, array, string, validate_json
from .paragraphs import validate_native_surface

POLICY = {'protocol': 'measured-text-correction-v1', 'max_attempts': 3}


def validate_revision(original, revised):
    allowed = {'script', 'scenes', 'script_review', 'speech_timing'}
    if {k:v for k,v in original.items() if k not in allowed} != {k:v for k,v in revised.items() if k not in allowed}:
        raise ValueError('voice correction changed immutable source or visual contract')
    if len(original['scenes']) != len(revised['scenes']):
        raise ValueError('voice correction changed paragraph count')
    for before, after in zip(original['scenes'], revised['scenes']):
        if {k:v for k,v in before.items() if k != 'narration'} != {k:v for k,v in after.items() if k != 'narration'}:
            raise ValueError('voice correction changed paragraph grounding')


def rewrite(payload, measured_ms, gemini):
    from .speech_timing import validate_timing
    from factory_v3.worker_adapters import VOICES
    if type(measured_ms) is not int or measured_ms <= 0:
        raise ValueError('completed voice measurement required')
    revised = deepcopy(payload)
    target = payload['seconds'] - .5
    ratio = target / (measured_ms / 1000)
    words = len(payload['script'].split())
    characters = len(payload['script'].strip())
    locale, voice = VOICES[payload['language']]
    timing = {'protocol':'natural-voice-timing-v1','locale':locale,'voice':voice,
              'words_per_second':words/(measured_ms/1000),
              'characters_per_second':characters/(measured_ms/1000),
              'minimum_estimated_seconds':payload['seconds']-1,
              'maximum_estimated_seconds':payload['seconds']}
    schema = obj({'narration':array({**string(),'maxLength':2400},len(payload['scenes']),len(payload['scenes']))})
    result, _ = gemini.generate('rewrite',
        'Rewrite the supplied consecutive narration paragraphs in natural native '+payload['language']+'. '
        'The previous synthesis was measured at its original speaking speed. Adjust TEXT LENGTH only. '
        'Preserve paragraph order, every cited claim, number, qualifier and source grounding. '
        'Keep the same paragraph subjects and visual relationships. Do not invent facts or add repetition/filler. '
        'Shorten redundant wording if too long; explain the SAME cited facts more fully if too short. '
        'Return fluent complete paragraphs, no instructions to the voice. '
        f'Aim for {round(words*ratio)} words and {round(characters*ratio)} characters TOTAL including spaces. '
        'The average of word-count/words_per_second and character-count/characters_per_second must fit the timing interval.',
        {'narration':[s['narration'] for s in payload['scenes']],
         'scenes':payload['scenes'],'evidence':payload['evidence'],
         'actual_duration_ms':measured_ms,'target_seconds':target,'speech_timing':timing},schema)
    validate_json(result,schema)
    for scene, text in zip(revised['scenes'], result['narration']):
        validate_native_surface(payload['language'],text)
        scene['narration']=text.strip()
    revised['script']=' '.join(s['narration'] for s in revised['scenes'])
    if revised['script'] == payload['script']:
        raise ValueError('duration correction returned unchanged text')
    revised['speech_timing']=timing
    validate_timing(revised['script'],timing,payload['language'],payload['seconds'])
    revised['script_review']=gemini.review_script({**{k:v for k,v in revised.items() if k != 'script_review'},'materials':revised['observations']})
    validate_revision(payload,revised)
    return {'payload':revised,'sha256':digest(revised)}


def fit(initial, synthesize, correct, verify, persist):
    """Callbacks account before every send and persist each successful measurement."""
    if initial.get('voice_correction') != POLICY:
        raise ValueError('bounded voice correction not enabled')
    current=deepcopy(initial)
    attempts=[]
    for number in range(1,POLICY['max_attempts']+1):
        frozen={'payload':current,'sha256':digest(current)}
        verify(frozen)
        result=synthesize(number,frozen)
        duration=result['duration_ms']
        if type(duration) is not int or duration <= 0:
            raise ValueError('invalid actual voice duration')
        persist(number,frozen,result)
        attempts.append({'attempt':number,'plan_sha256':frozen['sha256'],
                         'audio_sha256':result['sha256'],'duration_ms':duration})
        if initial['seconds']*1000-1000 <= duration <= initial['seconds']*1000:
            return result,frozen,attempts
        if number < POLICY['max_attempts']:
            next_frozen=correct(number+1,current,duration)
            verify(next_frozen)
            validate_revision(initial,next_frozen['payload'])
            current=deepcopy(next_frozen['payload'])
    from factory_v3.worker_adapters import VoiceDurationMismatch
    raise VoiceDurationMismatch('three measured narration attempts missed natural-duration window')
