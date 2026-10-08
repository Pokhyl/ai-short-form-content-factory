"""Natural narration paragraphs; estimated length never needs model word indices."""
from copy import deepcopy
import re
from factory_v3.gemini import obj, array, string, validate_json
from factory_v3.grounding import compact_evidence


LANGUAGES = {'pl':'Polish (pl-PL)','en':'English (en-US)','ru':'Russian (ru-RU)','uk':'Ukrainian (uk-UA)'}


def validate_native_surface(language, narration):
    # Narrow regression gate for actual mixed-language output that received an
    # incorrect model approval. This is not a complete language-quality proof.
    if language == 'uk' and re.search(r'[ыъэё]|\b(?:сверхнов\w*|відброш\w*|остатка)\b', narration, re.I):
        raise ValueError('Ukrainian narration contains observed non-native forms')


def compact_materials(materials):
    """Keep semantic observations; HTTP receipts belong to server verification."""
    fields = ('id','media_type','visible_description','supported_fact_ids',
              'matched_visual_targets','source_interval')
    inspection_fields = ('validation_method','medium','topic_relation','visible_fact_details',
                         'target_matches','visual_qualification_protocol')
    result = []
    for material in materials:
        row = {key:deepcopy(material[key]) for key in fields if key in material}
        inspection = material.get('inspection', {})
        row['inspection'] = {key:deepcopy(inspection[key]) for key in inspection_fields if key in inspection}
        result.append(row)
    return result


def compose_paragraphs(gemini, context, budget_error):
    request = context['request'];seconds=request['seconds'];materials=context['materials']
    # Words are only a pre-voice estimate. Actual synthesis duration still has
    # to satisfy the existing bounded tempo fit and exact encoded-duration QA.
    minimum_words, maximum_words = round(seconds*1.4), round(seconds*2.4)+2
    maximum_beats=min(8,len(materials),seconds*2//5)
    if maximum_beats<3:raise ValueError('not enough inspected paragraph anchors')
    fields={'material_id':string(m['id'] for m in materials),'narration':{**string(),'maxLength':2400},
            'fact_ids':array(string(f['id'] for f in context['evidence']['facts']),1,8)}
    targets=request.get('visual_targets')
    if targets is not None:
        allowed = request.get('validated_visual_anchors', {t['id']: None for t in targets})
        fields['visual_target_id']=string(t['id'] for t in targets if t['id'] in allowed)
    schema=obj({'beats':array(obj(fields),3,maximum_beats)})
    instruction=(
        'Write a continuous factual explanation in natural native '+LANGUAGES[request['language']]+'. '
        f'Return 3 to {maximum_beats} complete narration paragraphs in order, not individual words or numerical word ranges. '
        f'Aim for {round(seconds*2.1)} words total for {seconds} seconds; {minimum_words}–{maximum_words} is a pre-voice estimate. '
        'Explain ALL required_fact_ids, including the essential mechanism and outcome; do not merely mention a related keyword. '
        'Summarize source facts in your own concise words. Do not copy every evidence fact or quote entire source paragraphs. '
        'Optional facts may be omitted; required facts and their essential mechanisms may not. '
        'Tag every source fact asserted by each paragraph in fact_ids. A paragraph often needs several IDs. '
        'Preserve qualifiers and numbers. Do not invent claims to meet length. '
        'Choose supplied inspected anchors and at least two available visual roles, using matched_visual_targets. '
        'The anchor must have a direct factual connection to the paragraph. Images illustrate source-supported facts; '
        'do not claim an invisible mechanism is visible. Natural clause boundaries matter; renderer schedules all photographs separately. '
        'Use each anchor once; avoid unrelated filler and repeated generic compositions.')
    if request.get('visual_validation_mode')=='metadata':
        instruction+=' Provider metadata is not pixel evidence; do not assert that a specific action or detail is visibly shown.'
    draft,_=gemini.generate('material-compose',instruction,
                            {**context,'materials':compact_materials(materials),
                             'evidence':compact_evidence(context['evidence'])},schema)
    validate_json(draft,schema)
    beats=deepcopy(draft['beats'])
    if any(len(set(b['fact_ids']))!=len(b['fact_ids']) for b in beats):
        raise ValueError('duplicate paragraph fact identity')
    narrated={f for b in beats for f in b['fact_ids']}
    if not set(request.get('required_fact_ids',[]))<=narrated:
        raise ValueError('paragraph draft omitted required source facts')
    edit_schema=obj({'narration':array({**string(),'maxLength':2400},len(beats),len(beats))})
    edited,_=gemini.generate('material-language-edit',
        'Proofread these consecutive paragraphs into natural standard native '+LANGUAGES[request['language']]+'. '
        'Correct foreign words, spelling, inflections and grammar; do not transliterate foreign words. '
        'Preserve every claim, qualifier and number, and the source facts asserted by each paragraph. '
        'Return complete paragraph strings in the same order. Do not add or delete explanations. '
        'Edit only the supplied narration; never replace paragraphs with quotations from source text. '
        'Spell scientific notation and units naturally for spoken narration while preserving exact values. '
        f'Tighten wording to {minimum_words}–{maximum_words} words TOTAL, preferably {round(seconds*2.1)}. '
        'Shorten redundant phrasing without dropping any asserted claim, qualifier or number.',
        {'language':request['language'],'narration':[b['narration'] for b in beats],
         'word_budget':{'minimum':minimum_words,'maximum':maximum_words,'preferred':round(seconds*2.1)}},edit_schema)
    validate_json(edited,edit_schema)
    for beat,text in zip(beats,edited['narration']):
        validate_native_surface(request['language'], text)
        beat['narration']=text.strip()
    words=sum(len(b['narration'].split()) for b in beats)
    if not minimum_words<=words<=maximum_words:
        raise budget_error('native paragraphs outside pre-voice length estimate')
    return {'beats':beats}
