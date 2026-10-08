"""Bounded measured-duration correction; completed samples are never retried."""
from copy import deepcopy
from factory_v3.preflight import digest
from factory_v3.gemini import obj, string, validate_json
from factory_v3.grounding import compact_evidence
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
    from .speech_timing import estimated_seconds
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
    paragraphs={
        'paragraph_'+str(i+1): {'previous_text':scene['narration'],
            'fact_ids':scene['evidence_ids'],
            'target_words':max(1,round(len(scene['narration'].split())*ratio)),
            'target_characters':max(1,round(len(scene['narration'])*ratio))}
        for i,scene in enumerate(payload['scenes'])}
    schema=obj({key:{**string(),'maxLength':2400} for key in paragraphs})
    action='EXPAND' if ratio>1 else 'SHORTEN'
    result, _ = gemini.generate('rewrite',
        f'{action} every supplied paragraph by approximately {abs(ratio-1)*100:.1f} percent. '
        'The current text FAILED measured speech timing and must change. This is rewriting, not proofreading. '
        'Write natural native '+payload['language']+'. Return a complete paragraph string for every named key. '
        'Use paragraph target_words and target_characters to distribute the change across all paragraphs. '
        'Preserve every cited claim, number, qualifier, subject and source grounding, using DIFFERENT wording. '
        'For expansion, explain the same cited mechanisms more explicitly using their supplied facts. '
        'For shortening, replace wordy constructions with concise equivalents. '
        'Do not add generic importance claims, repetition, filler, new facts or voice instructions. '
        f'The previous text has {words} words and {characters} characters; the revised total should be '
        f'{round(words*ratio)} words and {round(characters*ratio)} characters including spaces. '
        'Return prose, never separate word slots. Do not copy the previous text unchanged.',
        {'paragraphs':paragraphs,'evidence':compact_evidence(payload['evidence']),
         'actual_duration_ms':measured_ms,'target_seconds':target},schema)
    validate_json(result,schema)
    for i,scene in enumerate(revised['scenes'],1):
        text=result['paragraph_'+str(i)]
        validate_native_surface(payload['language'],text)
        scene['narration']=text.strip()
    revised['script']=' '.join(s['narration'] for s in revised['scenes'])
    if revised['script'] == payload['script']:
        raise ValueError('duration correction returned unchanged text')
    revised['speech_timing']=timing
    # Estimates cannot certify a one-second window. Require meaningful progress;
    # only the next measured audio can pass the actual duration gate.
    previous_error=abs(measured_ms/1000-target)
    revised_error=abs(estimated_seconds(revised['script'],timing)-target)
    if revised_error >= previous_error or revised_error > max(.25,previous_error*.65):
        raise ValueError('rewritten narration did not materially correct measured duration')
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
