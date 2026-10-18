"""Bound a Gemini duration rewrite by complete sentences, not artificial word slots.

A model has repeatedly ignored a prose-only total word target. A structural
schema with named sentence fields fixes the number of natural-language beats
and forces the model to make enough genuine assertions. This is an optional
single, budgeted repair of a completed model response, NOT a TTS retry.
"""
import math
import re
from itertools import combinations
from factory_v3.gemini import obj, string, validate_json
from .duration import revision_length_fits, NaturalDurationRejected


def sentence_contract(previous_scenes, window):
    if not isinstance(previous_scenes, list) or not 1 <= len(previous_scenes) <= 8:
        raise ValueError('bounded reviewed scene count required')
    if not isinstance(window, dict) or window['target_words'] < len(previous_scenes):
        raise ValueError('insufficient spoken words for reviewed beats')
    # An actual production correction measured 96 words where the calibrated
    # window allowed 74..84: the old nine-field contract asked for about
    # 9 words/sentence, but Gemini consistently wrote 10..12 natural words
    # in EACH field, even after one separately metered repair. Asking for
    # fewer complete sentences is a schema-level way to avoid generating
    # content just to fill nine fields. It does NOT alter speech speed or
    # remove any source/factual/native-review constraints.
    count=max(len(previous_scenes),round(window['target_words']/10.6))
    if count>32:
        raise ValueError('too many bounded sentences')
    per_beat,extra=divmod(count,len(previous_scenes))
    counts=[per_beat+(1 if i<extra else 0)
            for i in range(len(previous_scenes))]
    # The actual MP3, not this calibrated prose heuristic, decides whether
    # a voice fits the requested video duration.
    per_sentence_chars=window['target_characters']/count
    properties={}
    for i,n in enumerate(counts,1):
        fields={}
        for j in range(1,n+1):
            fields['sentence_'+str(j)]={
                **string(), 'minLength':max(12,math.floor(per_sentence_chars*.70)),
                'maxLength':max(32,math.ceil(per_sentence_chars*1.35))}
        properties['beat_'+str(i)]=obj(fields)
    return obj(properties),counts


def assemble_sentence_repair(result,schema,reviewed_scenes,window):
    validate_json(result,schema)
    beats=[];all_sentences=[]
    for i,previous in enumerate(reviewed_scenes,1):
        row=result['beat_'+str(i)]
        sentences=[row[key].strip() for key in schema['properties']['beat_'+str(i)]['required']]
        if any(text[-1] not in '.!?…' or len(text.split()) < 5 for text in sentences):
            raise NaturalDurationRejected('sentence repair must contain complete natural sentences')
        all_sentences.extend(sentences)
        beats.append({'material_id':previous['material_id'],
                      'fact_ids':list(previous['evidence_ids']),
                      'narration':' '.join(sentences)})
    if len(set(text.casefold() for text in all_sentences)) != len(all_sentences):
        raise NaturalDurationRejected('duration revision repeats a sentence to fill time')
    text=' '.join(beat['narration'] for beat in beats)
    if not revision_length_fits(text,window):
        raise NaturalDurationRejected('sentence repair outside calibrated voice length window')
    return {'beats':beats}


# Extractive shortening is used ONLY when a naturally spoken, independently
# reviewed original MP3 runs too long. There are no word-slot outputs:
# the final narration remains the original prose, minus bounded modifiers.
# Essential fact terms are excluded from selectable deletion candidates.
_NEGATION={'never','without','cannot','not','nothing','always','ніколи',
           'немає','нікому','нельзя','никогда','nigdy','nigdyż','brak'}


def extractive_omission_candidates(reviewed_scenes, evidence, window):
    if not isinstance(reviewed_scenes,list) or not 1<=len(reviewed_scenes)<=8:
        raise ValueError('bounded reviewed scenes required')
    if not isinstance(evidence,dict) or not evidence.get('facts'):
        raise ValueError('source evidence required for extractive editing')
    protected=set()
    for fact in evidence['facts']:
        for token in re.findall(r'[^\W\d_][\w’\'-]*',fact['text'].casefold()):
            if len(token)>=5:
                protected.add(token[:5])
    candidates=[]
    for scene in reviewed_scenes:
        text=scene['narration']
        for m in re.finditer(r'[^\W\d_][\w’\'-]*',text):
            word=m.group()
            if len(word)<5 or word.casefold()[:5] in protected or word.casefold() in _NEGATION:
                continue
            # Avoid editing word stems, mandatory terminal punctuation or
            # connective punctuation; only a standalone whole-word span.
            start,end=m.span()
            if end<len(text) and text[end] in ',.;:!?':
                continue
            if end<len(text) and text[end].isspace():
                cut_start,cut_end=start,end+1
            elif start>0 and text[start-1].isspace():
                cut_start,cut_end=start-1,end
            else:
                continue
            candidates.append({
                'id':f"{scene['id']}:{start}",
                'scene_id':scene['id'],
                'word':word,
                'left_context':text[max(0,start-20):start],
                'right_context':text[end:min(len(text),end+20)],
                'removed_characters':cut_end-cut_start,
                '_start':cut_start,'_end':cut_end})
    words=sum(len(scene['narration'].split()) for scene in reviewed_scenes)
    minimum=max(1,words-window['max_words'])
    maximum=min(24,len(candidates),max(0,words-window['min_words']))
    if not 1<=minimum<=maximum:
        raise NaturalDurationRejected('no bounded source-preserving omission plan available')
    public=[{k:v for k,v in candidate.items() if not k.startswith('_')}
            for candidate in candidates]
    schema=obj({'remove_ids':{
        'type':'array','items':string(c['id'] for c in candidates),
        'minItems':minimum,'maxItems':maximum}})
    return public,candidates,schema


def apply_extractive_omission_plan(reviewed_scenes,plan,candidates,schema,window):
    validate_json(plan,schema)
    ids=plan['remove_ids']
    if len(ids)!=len(set(ids)):
        raise NaturalDurationRejected('repeated omission identity is invalid')
    by_id={candidate['id']:candidate for candidate in candidates}
    if len(by_id)!=len(candidates):
        raise ValueError('candidate identities duplicated')
    grouped={}
    for identity in ids:
        candidate=by_id[identity]
        grouped.setdefault(candidate['scene_id'],[]).append(candidate)
    beats=[]
    for scene in reviewed_scenes:
        text=scene['narration']
        removals=sorted(grouped.get(scene['id'],[]),
                        key=lambda c:c['_start'],reverse=True)
        last_start=len(text)
        for candidate in removals:
            first,last=candidate['_start'],candidate['_end']
            if last>last_start:
                raise NaturalDurationRejected('overlapping omissions forbidden')
            original=text[first:last]
            if candidate['word'] not in original:
                raise NaturalDurationRejected('omission changed after approval')
            text=text[:first]+text[last:]
            last_start=first
        text=re.sub(r'\s+',' ',text).strip()
        if len(text.split())<5 or not text or text[-1] not in '.!?…':
            raise NaturalDurationRejected('extractive scene lost natural narration')
        beats.append({'material_id':scene['material_id'],
                      'fact_ids':list(scene['evidence_ids']),
                      'narration':text})
    narration=' '.join(beat['narration'] for beat in beats)
    if not revision_length_fits(narration,window):
        raise NaturalDurationRejected('extractive narration outside measured length window')
    return {'beats':beats}


# An optional LOCAL (zero additional provider calls) correction for a
# structurally valid but slightly TOO LONG completed expansion response.
# Only remove nonessential style modifiers from the completed JSON. Source
# fact vocabulary remains protected by extractive_omission_candidates.
# Never use this to pad an underlong response or replace any fact.
_STYLE_MODIFIERS = frozenset({
    # English
    'very','extremely','particularly','remarkably','highly','truly','really',
    'genuinely','significantly','quite','important','remarkable','numerous',
    # Polish
    'bardzo','niezwykle','szczególnie','naprawdę','wyraźnie','istotnie',
    'znacznie','ważne','ważnych','liczne','licznych','stabilną',
    # Ukrainian
    'надзвичайно','справді','значно','надійно','важливі',
    'такий','багатьох','повторюваних','особливо','істотно',
    # Russian
    'очень','особенно','крайне','значительно','надёжно','надежно',
    'важные','важный','различные','многочисленные','действительно',
})


def trim_complete_expansion_locally(result, schema, previous_scenes, evidence, window):
    """Deterministically remove low-risk modifiers from a completed reply.

    The reply MUST already satisfy its exact per-sentence schema. Strict
    source/fact/native-language review remains required after this helper.
    If there is not a safe bounded solution, stop rather than invent words.
    """
    validate_json(result,schema)
    beats=[];revised=[]
    for index,scene in enumerate(previous_scenes,1):
        row=result['beat_'+str(index)]
        sentences=[row[key].strip() for key in schema['properties']['beat_'+str(index)]['required']]
        if any(not line or line[-1] not in '.!?…' or len(line.split())<5 for line in sentences):
            raise NaturalDurationRejected('complete sentences required for local expansion trim')
        revised.append({**scene,'narration':' '.join(sentences)})
    text=' '.join(scene['narration'] for scene in revised)
    if len(text.split())<=window['max_words'] and len(text)<=window['max_characters']:
        raise NaturalDurationRejected('local trim cannot expand an underlength draft')
    _public,candidates,plan_schema=extractive_omission_candidates(revised,evidence,window)
    style=[candidate for candidate in candidates
           if candidate['word'].casefold() in _STYLE_MODIFIERS]
    # The plan is constrained to a small finite space and is completely
    # deterministic. No combinatorial search through unconstrained inputs.
    if not 1<=len(style)<=18:
        raise NaturalDurationRejected('no bounded optional modifiers for local repair')
    best=None
    minimum=plan_schema['properties']['remove_ids']['minItems']
    maximum=min(len(style),plan_schema['properties']['remove_ids']['maxItems'])
    for n in range(minimum,maximum+1):
        for subset in combinations(style,n):
            plan={'remove_ids':[candidate['id'] for candidate in subset]}
            try:
                edited=apply_extractive_omission_plan(
                    revised,plan,candidates,plan_schema,window)
            except (NaturalDurationRejected,ValueError):
                continue
            final=' '.join(beat['narration'] for beat in edited['beats'])
            # The original per-beat complete sentence boundaries and source
            # anchors are retained. Validate natural sentences after deletion.
            valid=True
            for original,beat in zip(revised,edited['beats']):
                before=re.split(r'(?<=[.!?…])\s+',original['narration'])
                after=re.split(r'(?<=[.!?…])\s+',beat['narration'])
                if len(before)!=len(after) or any(len(x.split())<5 for x in after):
                    valid=False;break
            if not valid:
                continue
            score=(abs(len(final.split())-window['target_words'])*4+
                   abs(len(final)-window['target_characters'])/8+n*.04)
            if best is None or score<best[0]:
                best=score,edited
    if best is None:
        raise NaturalDurationRejected('cannot locally correct completed voice expansion safely')
    return best[1]
