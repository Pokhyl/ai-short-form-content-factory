"""Natural narration paragraphs; estimated length never needs model word indices."""
from copy import deepcopy
import math
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


def cadence_paragraph_plan(materials, targets, required, preferred_words):
    """Build three narration contracts from the two best-covered inspected roles."""
    groups = {t['id']:[m for m in materials if t['id'] in m.get('matched_visual_targets',{})
                      and m.get('supported_fact_ids')] for t in targets or []}
    roles = sorted((r for r in groups if groups[r]), key=lambda r:(-len(groups[r]),r))
    if len(roles)<2:return None
    dominant, secondary = roles[:2]
    if len(groups[dominant])<2:return None
    selected=[];used=set()
    for role in (secondary,dominant,dominant):
        material=next((m for m in groups[role] if m['id'] not in used),None)
        if material is None:return None
        used.add(material['id'])
        selected.append({'material_id':material['id'],'visual_target_id':role,
                         'identifying_fact_ids':list(material['supported_fact_ids']), 'required_fact_ids':[]})
    # Required facts with sparse imagery join an observed outcome rather than
    # dictating a long paragraph over that sole image. Every claim still needs
    # independent source/semantic review after prose generation.
    required=list(dict.fromkeys(list(required)+[f for m in materials for f in m['supported_fact_ids']]))
    for fact in required:
        options=[i for i,p in enumerate(selected) if fact in p['identifying_fact_ids']]
        index=options[0] if options else (0 if any(fact in m['supported_fact_ids'] for m in materials) else 1)
        selected[index]['required_fact_ids'].append(fact)
    coverage=[]
    for p in selected:
        facts=set(p['identifying_fact_ids']+p['required_fact_ids'])
        coverage.append(sum(bool(facts & set(m['supported_fact_ids'])) for m in materials))
    weights=[coverage[0],coverage[1]/2,coverage[2]/2];total=sum(weights)
    for p,weight in zip(selected,weights):
        target=round(preferred_words*weight/total)
        p['word_budget']={'minimum':max(1,target-2),'maximum':target+2,'preferred':target}
    return selected


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
    cadence_guidance = {'seconds':seconds,
        'minimum_unique_photos':math.ceil(seconds/5),
        'anchor_related_fact_ids':{m['id']:m.get('supported_fact_ids',[]) for m in materials},
        'fact_photo_capacity':{f['id']:5*sum(f['id'] in m.get('supported_fact_ids',[]) for m in materials)
                               for f in context['evidence']['facts']},
        'maximum_total_seconds_per_role':{t['id']:min(seconds,5*sum(
            t['id'] in m.get('matched_visual_targets',{}) for m in materials)) for t in targets or []}}
    model_context = {**context,'materials':compact_materials(materials),
                     'evidence':compact_evidence(context['evidence']), 'cadence_guidance':cadence_guidance}
    instruction=(
        'Write a continuous factual explanation in natural native '+LANGUAGES[request['language']]+'. '
        f'Return 3 to {maximum_beats} complete narration paragraphs in order, not individual words or numerical word ranges. '
        f'Write {minimum_words}–{maximum_words} words TOTAL, preferably {round(seconds*2.1)}, for {seconds} seconds. '
        'This total is required before voice synthesis; do not return a shorter abstract. '
        'Explain ALL required_fact_ids, including the essential mechanism and outcome; do not merely mention a related keyword. '
        'Summarize source facts in your own concise words. Do not copy every evidence fact or quote entire source paragraphs. '
        'Optional facts may be omitted; required facts and their essential mechanisms may not. '
        'Tag every source fact asserted by each paragraph in fact_ids. A paragraph often needs several IDs. '
        'Preserve qualifiers and numbers. Do not invent claims to meet length. '
        'Choose supplied inspected anchors and at least two available visual roles, using matched_visual_targets. '
        'The anchor must have a direct factual connection to the paragraph. Images illustrate source-supported facts; '
        'Respect cadence_guidance: a role with one eligible photo can occupy at most five seconds total, '
        'so use only a brief clause there and explain longer mechanisms over roles with more eligible photos. '
        'Estimate time by that role\'s share of ALL narration words, not by paragraph count. '
        'Each paragraph must explicitly explain at least one source fact in its anchor_related_fact_ids, '
        'tagging that asserted identifying fact as well as any source-supported hidden mechanism. '
        'do not claim an invisible mechanism is visible. Natural clause boundaries matter; renderer schedules all photographs separately. '
        'Use each anchor once; avoid unrelated filler and repeated generic compositions.')
    if request.get('visual_validation_mode')=='metadata':
        instruction+=' Provider metadata is not pixel evidence; do not assert that a specific action or detail is visibly shown.'
    draft,_=gemini.generate('material-compose',instruction,model_context,schema)
    validate_json(draft,schema)
    beats=deepcopy(draft['beats'])
    if any(len(set(b['fact_ids']))!=len(b['fact_ids']) for b in beats):
        raise ValueError('duplicate paragraph fact identity')
    narrated={f for b in beats for f in b['fact_ids']}
    if not set(request.get('required_fact_ids',[]))<=narrated:
        raise ValueError('paragraph draft omitted required source facts')
    words = sum(len(b['narration'].split()) for b in beats)
    def cadence_problem(paragraphs):
        if 'validated_visual_anchors' not in request or not all(
                {'matched_visual_targets','supported_fact_ids','sha256'} <= m.keys() for m in materials):
            return None
        from .engine import fit_contextual_paragraphs, MaterialUnavailable
        try:
            fit_contextual_paragraphs(materials, {'beats':paragraphs}, seconds=seconds,
                                     anchor_ids=request['validated_visual_anchors'].values())
        except MaterialUnavailable as error:
            return str(error)
        return None
    cadence_error = cadence_problem(beats)
    paragraph_diagnostics = [{'paragraph':i+1, 'fact_ids':b['fact_ids'],
        'eligible_photo_count':sum(bool(set(b['fact_ids']) & set(m.get('supported_fact_ids',[])))
            and (b.get('visual_target_id') is None or b['visual_target_id'] in m.get('matched_visual_targets',{}))
            for m in materials)} for i,b in enumerate(beats)]
    paragraph_plan = None
    if not minimum_words <= words <= maximum_words or cadence_error:
        # One separately keyed correction of a completed valid draft, inside
        # the existing durable Gemini ceiling. Provider failures are terminal.
        repair_schema = deepcopy(schema)
        if not cadence_error:
            repair_schema['properties']['beats']['minItems'] = len(beats)
            repair_schema['properties']['beats']['maxItems'] = len(beats)
        repair_identity_instruction = (
            'The completed visual assignment is infeasible. You may regroup paragraphs and choose different supplied inspected anchors and approved roles. '
            'Move hidden mechanisms into paragraphs that also explicitly explain a related observed outcome; do not leave a paragraph tagged only with facts absent from ALL its role photos. '
            'Every paragraph must assert at least one identifying anchor_related_fact_id. Include it in fact_ids only when the narration actually explains it. '
            if cadence_error else 'Preserve the same paragraphs, their order, anchor identities and visual roles. ')
        paragraph_plan = (cadence_paragraph_plan(materials, targets, request.get('required_fact_ids',[]), round(seconds*2.1))
                          if cadence_error else None)
        if paragraph_plan:
            from .engine import fit_contextual_paragraphs
            # Verify the server's own allocation against the actual global
            # unique-photo scheduler before asking for prose in these slots.
            planned_beats=[{'material_id':p['material_id'],'visual_target_id':p['visual_target_id'],
                'fact_ids':list(dict.fromkeys(p['identifying_fact_ids']+p['required_fact_ids'])),
                'narration':' '.join(['estimate']*p['word_budget']['preferred'])} for p in paragraph_plan]
            fit_contextual_paragraphs(materials,{'beats':planned_beats},seconds=seconds,
                                     anchor_ids=request['validated_visual_anchors'].values())
            repair_schema = obj({'paragraph_'+str(i+1):obj({
                'words':obj({'word_'+str(j+1):{**string(),'maxLength':80}
                             for j in range(paragraph_plan[i]['word_budget']['preferred'])}),
                'fact_ids':array(string(f['id'] for f in context['evidence']['facts']),1,8)})
                for i in range(len(paragraph_plan))})
            repair_identity_instruction = (
                'Follow the server-owned paragraph_plan exactly. Return paragraph_1, paragraph_2 and paragraph_3. '
                'Return each paragraph as its ordered words object: each word_N value is exactly one spoken word with punctuation attached, no spaces. '
                'Together the words form natural continuous prose. Fill every supplied word key in order. '
                'Each must explain ALL of its required_fact_ids, and explicitly assert at least one of its identifying_fact_ids. '
                'Explain mechanisms alongside their observed outcomes. The server supplies anchor and role identities; do not choose other assignments. '
                'Write a natural continuous explanation without repeating the same claim in every paragraph. ')
        repaired, _ = gemini.generate('material-compose-length-repair',
            instruction + f' The completed draft has {words} words. Rewrite to {minimum_words}–{maximum_words}, '
            f'preferably {round(seconds*2.1)}. ' + repair_identity_instruction +
            'Preserve ALL required_fact_ids across the continuous narration and every supported original claim, number and qualifier. '
            'Expand too-short paragraphs with explanatory details from the supplied source facts; '
            'shorten excessive wording without dropping those facts. No repetition, padding or invented facts. '
            'Redistribute paragraph lengths and source-backed explanations over the inspected anchors to respect cadence_guidance; '
            'a rare one-photo role must remain a short clause while better-covered roles carry more explanation. '
            'Correct fact_ids to the facts actually asserted in each revised paragraph. Never merely add a citation without explaining it; '
            'omit an optional fact_id that the paragraph does not assert. All required source facts must remain fully explained.',
            {**model_context, 'completed_draft':deepcopy(beats), 'cadence_error':cadence_error,
             'paragraph_diagnostics':paragraph_diagnostics, 'paragraph_plan':paragraph_plan}, repair_schema)
        validate_json(repaired, repair_schema)
        if paragraph_plan:
            structured=[]
            for i,contract in enumerate(paragraph_plan):
                paragraph=deepcopy(repaired['paragraph_'+str(i+1)])
                tokens=[paragraph['words']['word_'+str(j+1)] for j in range(contract['word_budget']['preferred'])]
                if any(len(token.split())!=1 or token!=token.strip() for token in tokens):
                    raise ValueError('paragraph word slot must contain exactly one word')
                paragraph={'narration':' '.join(tokens),'fact_ids':paragraph['fact_ids']}
                count=len(paragraph['narration'].split())
                if (not contract['word_budget']['minimum']<=count<=contract['word_budget']['maximum']
                        or not set(contract['required_fact_ids'])<=set(paragraph['fact_ids'])
                        or not set(contract['identifying_fact_ids']) & set(paragraph['fact_ids'])):
                    raise ValueError('paragraph violates server-owned cadence contract')
                structured.append({**paragraph,'material_id':contract['material_id'],
                                   'visual_target_id':contract['visual_target_id']})
            repaired={'beats':structured}
        for index, revised in enumerate(repaired['beats']):
            if ((not cadence_error and any(beats[index].get(k) != revised.get(k) for k in ('material_id', 'visual_target_id')))
                    or len(set(revised['fact_ids'])) != len(revised['fact_ids'])):
                raise ValueError('length repair changed paragraph source or visual identity')
        beats = deepcopy(repaired['beats'])
        if not set(request.get('required_fact_ids', [])) <= {f for b in beats for f in b['fact_ids']}:
            raise ValueError('length repair omitted required source facts')
        if not minimum_words <= sum(len(b['narration'].split()) for b in beats) <= maximum_words:
            raise budget_error('bounded paragraph length repair outside pre-voice estimate')
        if cadence_problem(beats):
            from .engine import MaterialUnavailable
            raise MaterialUnavailable('bounded paragraph repair still lacks related unique-photo cadence')
    edit_schema=obj({'narration':array({**string(),'maxLength':2400},len(beats),len(beats))})
    edited,_=gemini.generate('material-language-edit',
        'Proofread these consecutive paragraphs into natural standard native '+LANGUAGES[request['language']]+'. '
        'Correct foreign words, spelling, inflections and grammar; do not transliterate foreign words. '
        'Preserve every claim, qualifier and number, and the source facts asserted by each paragraph. '
        'Return complete paragraph strings in the same order. Do not add or delete explanations. '
        'Edit only the supplied narration; never replace paragraphs with quotations from source text. '
        'Spell scientific notation and units naturally for spoken narration while preserving exact values. '
        f'Tighten wording to {minimum_words}–{maximum_words} words TOTAL, preferably {round(seconds*2.1)}. '
        'Shorten redundant phrasing without dropping any asserted claim, qualifier or number. '
        'If word_budget contains paragraphs, preserve those individual word limits as well as the total.',
        {'language':request['language'],'narration':[b['narration'] for b in beats],
         'word_budget':{'minimum':minimum_words,'maximum':maximum_words,'preferred':round(seconds*2.1),
                        **({'paragraphs':[p['word_budget'] for p in paragraph_plan]} if paragraph_plan else {})}},edit_schema)
    validate_json(edited,edit_schema)
    for beat,text in zip(beats,edited['narration']):
        validate_native_surface(request['language'], text)
        beat['narration']=text.strip()
    words=sum(len(b['narration'].split()) for b in beats)
    if not minimum_words<=words<=maximum_words:
        raise budget_error('native paragraphs outside pre-voice length estimate')
    return {'beats':beats}
