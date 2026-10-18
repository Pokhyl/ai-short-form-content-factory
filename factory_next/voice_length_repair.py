"""Bound a Gemini duration rewrite by complete sentences, not artificial word slots.

A model has repeatedly ignored a prose-only total word target. A structural
schema with named sentence fields fixes the number of natural-language beats
and forces the model to make enough genuine assertions. This is an optional
single, budgeted repair of a completed model response, NOT a TTS retry.
"""
import math
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
