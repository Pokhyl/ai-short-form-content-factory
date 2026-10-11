"""Bounded measured-duration correction; completed samples are never retried."""
from copy import deepcopy
from itertools import product
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



def select_paragraphs(payload, proposed, timing):
    """Choose whole reviewed-source paragraph variants, never splice words/audio."""
    from .speech_timing import estimated_seconds
    scenes=payload['scenes']
    if not 1 <= len(scenes) <= 8 or len(proposed) != len(scenes):
        raise ValueError('bounded paragraph alternatives required')
    originals=[s['narration'] for s in scenes]
    choices=[]
    for old,new in zip(originals,proposed):
        variants=[old,new] if isinstance(new,str) else new
        if not isinstance(variants,list) or not 1<=len(variants)<=3 or any(not isinstance(t,str) or not t.strip() for t in variants):
            raise ValueError('bounded complete paragraph variants required')
        choices.append(list(dict.fromkeys(variants)))
    target=timing.get('selection_target_seconds',payload['seconds']-.5)
    return list(min(product(*choices),key=lambda paragraphs:(
        abs(estimated_seconds(' '.join(paragraphs),timing)-target),
        sum(a!=b for a,b in zip(originals,paragraphs)))))


def proofread_selected(payload, selected, gemini):
    """Repair grammar after variant selection while preserving paragraph contracts."""
    schema=obj({'paragraph_'+str(i+1):{**string(),'maxLength':2400}
                for i in range(len(selected))})
    facts={f['id']:f['text'] for f in payload['evidence']['facts']}
    paragraphs={}
    for i,(scene,text) in enumerate(zip(payload['scenes'],selected),1):
        paragraphs['paragraph_'+str(i)]={
            'text':text,
            'assigned_facts':[{'id':fact_id,'claim':facts[fact_id]}
                              for fact_id in scene['evidence_ids']]}
    result,_=gemini.generate('proofread',
        'Proofread the selected narration in native '+payload['language']+'. '
        'This is a constrained language edit, not a rewrite: fix grammar, case, inflection, agreement, spelling, '
        'and unnatural phrasing with the smallest necessary changes. In Ukrainian, for example, use '
        '“електронне захоплення”, not “електронний захоплення”, and “завдяки закону”. '
        'Preserve every source-supported claim, number, qualifier, paragraph meaning, and paragraph order. '
        'Do not add, remove, generalize, or strengthen facts. Keep each paragraph close to its input length '
        'so measured speech duration does not drift. Return every paragraph exactly once as complete prose.',
        {'language':payload['language'],'paragraphs':paragraphs},schema,thinking_level='low')
    validate_json(result,schema)
    revised=deepcopy(payload)
    corrected=[]
    for i,scene in enumerate(revised['scenes'],1):
        text=result['paragraph_'+str(i)].strip()
        if not text:
            raise ValueError('proofread narration paragraph is empty')
        validate_native_surface(payload['language'],text)
        scene['narration']=text
        corrected.append(text)
    revised['script']=' '.join(corrected)
    validate_revision(payload,revised)
    return revised


def rewrite(payload, measured_ms, gemini):
    from .speech_timing import estimated_seconds
    from factory_v3.worker_adapters import VOICES
    if type(measured_ms) is not int or measured_ms <= 0:
        raise ValueError('completed voice measurement required')
    revised = deepcopy(payload)
    target = payload['seconds'] - .5
    selection_target = target
    previous_timing = payload.get('speech_timing')
    if isinstance(previous_timing,dict) and previous_timing.get('selection_target_seconds') is not None:
        previous_estimate = estimated_seconds(payload['script'],previous_timing)
        if previous_estimate > 0:
            observed_factor = (measured_ms / 1000) / previous_estimate
            # Correct only a measured overrun in the previous estimated text.
            # The final gate remains the actual 59–60s TTS measurement.
            if 1.02 < observed_factor < 1.2:
                selection_target = max(payload['seconds']-4,target/observed_factor)
    ratio = selection_target / (measured_ms / 1000)
    words = len(payload['script'].split())
    characters = len(payload['script'].strip())
    locale, voice = VOICES[payload['language']]
    timing = {'protocol':'natural-voice-timing-v1','locale':locale,'voice':voice,
              'words_per_second':words/(measured_ms/1000),
              'characters_per_second':characters/(measured_ms/1000),
              'selection_target_seconds':selection_target,
              'minimum_estimated_seconds':payload['seconds']-1,
              'maximum_estimated_seconds':payload['seconds']}
    facts={f['id']:f for f in payload['evidence']['facts']}
    paragraphs={
        'paragraph_'+str(i+1): {'previous_text':scene['narration'],
            'fact_ids':scene['evidence_ids'],
            'must_explain':[{'id':identity,'claim':facts[identity]['text']} for identity in scene['evidence_ids']],
            'target_words':max(1,round(len(scene['narration'].split())*ratio)),
            'target_characters':max(1,round(len(scene['narration'])*ratio))}
        for i,scene in enumerate(payload['scenes'])}
    for paragraph in paragraphs.values():
        paragraph['variants']={name:{'target_words':max(1,round(paragraph['target_words']*factor)),
                                    'target_characters':max(1,round(paragraph['target_characters']*factor))}
                               for name,factor in [('compact',.8),('balanced',1),('expanded',1.2)]}
    schema=obj({key:obj({name:{**string(),'maxLength':2400} for name in ('compact','balanced','expanded')})
                for key in paragraphs})
    action='EXPAND' if ratio>1 else 'SHORTEN'
    result, _ = gemini.generate('rewrite',
        f'{action} every supplied paragraph by approximately {abs(ratio-1)*100:.1f} percent. '
        'The current text FAILED measured speech timing and must change. This is rewriting, not proofreading. '
        'Write natural native '+payload['language']+'. For EVERY paragraph return three distinct complete alternatives: compact, balanced, expanded. '
        'Proofread every alternative for native grammar before returning it: check each preposition’s required case, noun/adjective/verb inflection, agreement, and natural word order. '
        'In Ukrainian, for example, write “завдяки закону”, never “завдяки закон”. Do not leave a known grammar defect in any length variant. '
        'Each alternative independently explains the same assigned facts. Vary wording length, not the claims. '
        'The server will select ONE alternative per paragraph; do not make variants continuations of one another. '
        'Follow each variant target_words and target_characters; compact must be shorter than balanced, and balanced shorter than expanded. '
        'Source quotations are evidence, not narration to copy. Summarize each core assigned claim with its essential qualifiers, without reciting the entire quoted article. '
        'Every paragraph must explicitly explain EVERY fact in its own must_explain list. A fact stated in another paragraph does not count. '
        'Replace vague importance/research/significance wording with the supplied physical explanation; do not preserve unsupported filler from previous_text. '
        'Preserve the source facts, numbers, qualifiers and paragraph subjects, using DIFFERENT wording. '
        'When a fact is assigned to more than one paragraph, explain it in each with a different useful emphasis instead of generic filler. '
        'For expansion, explain the same cited mechanisms more explicitly using their supplied facts. '
        'For shortening, replace wordy constructions with concise equivalents. '
        'Do not add generic importance claims, repetition, filler, new facts or voice instructions. '
        f'The previous text has {words} words and {characters} characters; the revised total should be '
        f'{round(words*ratio)} words and {round(characters*ratio)} characters including spaces. '
        'Return prose, never separate word slots. Do not copy the previous text unchanged.',
        {'paragraphs':paragraphs,'evidence':compact_evidence(payload['evidence']),
         'actual_duration_ms':measured_ms,'target_seconds':selection_target,
         'voice_acceptance_window_seconds':[payload['seconds']-1,payload['seconds']]},
        schema,thinking_level='low')
    validate_json(result,schema)
    alternatives=[]
    for i in range(1,len(revised['scenes'])+1):
        variants=[result['paragraph_'+str(i)][name].strip() for name in ('compact','balanced','expanded')]
        alternatives.append(variants)
    selected=select_paragraphs(payload,alternatives,timing)
    for scene,text in zip(revised['scenes'],selected):scene['narration']=text
    revised['script']=' '.join(selected)
    if revised['script'] == payload['script']:
        raise ValueError('duration correction returned unchanged text')
    revised['speech_timing']=timing
    # Estimates cannot certify a one-second window. Require meaningful progress;
    # only the next measured audio can pass the actual duration gate.
    previous_error=abs(measured_ms/1000-target)
    revised_error=abs(estimated_seconds(revised['script'],timing)-selection_target)
    if revised_error >= previous_error or revised_error > max(.25,previous_error*.65):
        raise ValueError('rewritten narration did not materially correct measured duration')
    revised=proofread_selected(revised,selected,gemini)
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
