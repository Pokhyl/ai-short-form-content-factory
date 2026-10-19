"""Validate source mentions before spending the photo-search budget."""
import re
from .photo_queries import SYNTHETIC, INVISIBLE

DEPICTION = re.compile(r"\b(?:representations?|depictions?|radiation\s+beams?|particle\s+beams?|artwork|renderings?)\b", re.I)
GENERIC_SEARCH = re.compile(r"^(?:space|outer\s+space|astronomy|cosmos|universe|science|nature|technology|laboratory|observatory)(?:\s+(?:photo|photograph|images?))?$", re.I)
EQUIPMENT = re.compile(r"\b(?:telescopes?|microscopes?|cameras?|observatories|laboratories|detectors?|satellites?)\b", re.I)
EQUIPMENT_ALIASES = {
    'telescope': re.compile(r"\b(?:telescopes?|телескоп\w*|teleskop\w*)\b", re.I),
    'microscope': re.compile(r"\b(?:microscopes?|микроскоп\w*|mikroskop\w*)\b", re.I),
    'camera': re.compile(r"\b(?:cameras?|камер\w*|kamer\w*)\b", re.I),
    'observatory': re.compile(r"\b(?:observatories|observatory|обсерватор\w*|obserwator\w*)\b", re.I),
    'laboratory': re.compile(r"\b(?:laboratories|laboratory|лаборатор\w*|laborator\w*)\b", re.I),
    'detector': re.compile(r"\b(?:detectors?|детектор\w*|detektor\w*)\b", re.I),
    'satellite': re.compile(r"\b(?:satellites?|спутник\w*|супутник\w*|satelit\w*)\b", re.I),
}
STOP_WORDS = {'the','a','an','of','for','and','in','on','space','outer','astronomy','cosmos','universe','science','nature','technology','photo','photograph','image','images'}
EQUIPMENT_WORDS = {'telescope','telescopes','microscope','microscopes','camera','cameras','observatory','observatories','laboratory','laboratories','detector','detectors','satellite','satellites'}
OBSERVABLE_CATALOG_ID = re.compile(
    r"\b(?:RX|RBS|PSR|NGC|IC|SNR|SN|SGR|GRO|4U)\s*[A-Z]?\s*"
    r"\d{3,6}(?:\.\d+)?(?:[-–−+]\d{1,6}(?:\.\d+)?)?[A-Z]?\b", re.I)


def source_catalog_references(spans, maximum=24):
    """Literal source names to consider, not evidence of image availability."""
    references, known = [], set()
    for span in spans:
        for match in OBSERVABLE_CATALOG_ID.finditer(span['text']):
            literal = match.group(0)
            query = re.sub(r'\s+', ' ', literal).translate(str.maketrans({'–': '-', '−': '-'}))
            identity = re.sub(r'\s+', '', query).casefold()
            if identity in known:
                continue
            known.add(identity)
            references.append({'source_mention': literal, 'english_photo_object': query,
                               'support_span_ids': [span['id']]})
            if len(references) == maximum:
                return references
    return references



def validate_search_hints(contexts, topic, source_spans=None):
    """Reject broad hints and require source-named observed entities when available."""
    topic_words = set(re.findall(r"[a-z0-9]+", topic.casefold())) - STOP_WORDS
    errors = []
    span_catalog = {span['id']: span['text'] for span in (source_spans or [])}
    has_source_linked_catalog_id = False
    for role, row in contexts.items():
        query = row.get('query') or row.get('english_photo_object') or row.get('subject') or ''
        normalized = re.sub(r"\s+", " ", query.casefold()).strip(" .,:;-")
        if GENERIC_SEARCH.fullmatch(normalized):
            errors.append(role + ': search hint names only a broad category')
        elif EQUIPMENT.search(normalized):
            named_words = set(re.findall(r"[a-z0-9]+", normalized)) - STOP_WORDS - EQUIPMENT_WORDS
            query_equipment = {name for name, pattern in EQUIPMENT_ALIASES.items() if pattern.search(normalized)}
            topic_equipment = {name for name, pattern in EQUIPMENT_ALIASES.items() if pattern.search(topic)}
            if not named_words.intersection(topic_words) and not query_equipment.intersection(topic_equipment):
                errors.append(role + ': search hint names equipment without a topic-linked object')
        selected_spans = row.get('support_span_ids', [])
        source_ids = {match.group(0) for identity in selected_spans
                      for match in OBSERVABLE_CATALOG_ID.finditer(span_catalog.get(identity, ''))}
        if source_ids:
            normalized_query = re.sub(r'[^a-z0-9]', '', normalized)
            if any(re.sub(r'[^a-z0-9]', '', identity.casefold()) in normalized_query
                   for identity in source_ids):
                has_source_linked_catalog_id = True
    if span_catalog and not has_source_linked_catalog_id and any(
            OBSERVABLE_CATALOG_ID.search(span_catalog.get(identity, ''))
            for row in contexts.values() for identity in row.get('support_span_ids', [])):
        errors.append('photo contexts: use a source-named observable catalog object when one is present in the selected evidence')
    if errors:
        raise ValueError('; '.join(errors))

def validate_context_mentions(contexts, spans):
    catalog = {s['id']: s['text'] for s in spans}
    errors = []
    for role, row in contexts.items():
        mention = row.get('source_mention', '').strip()
        selected = row.get('support_span_ids', [])
        if not 3 <= len(mention) <= 160 or not selected or any(s not in catalog for s in selected):
            errors.append(role + ': source object mention is missing or invalid')
        if mention and selected and all(s in catalog for s in selected) and not any(mention in catalog[s] for s in selected):
            errors.append(role + ': selected source span does not contain the object mention')
        query = row['query'].strip()
        if any(pattern.search(query) for pattern in (SYNTHETIC, INVISIBLE, DEPICTION)):
            errors.append(role + ': search requests a depiction or invisible mechanism')
        if query.casefold() != row['subject'].strip().casefold():
            errors.append(role + ': search must use only the source-linked English object name')
        if not re.search(r'[A-Za-z]', query) or re.search(r'[\u0400-\u04ff\u3400-\u9fff]', query):
            errors.append(role + ': query and subject must be English; keep original source language only in source_mention')
    if errors:
        raise ValueError('; '.join(errors))


def bind_english_objects(contexts):
    """The server owns the query: one explicit English field, no duplicate labels."""
    return {role:{**{k:v for k,v in row.items() if k!='english_photo_object'},
                  'subject':row['english_photo_object'], 'query':row['english_photo_object']}
            for role,row in contexts.items()}



def restore_exact_source_case(contexts, spans):
    """Return the original lettercase of an already selected literal quote.

    A source quotation in a heading may be capitalized, while the model
    returns the identical words in lowercase. Never infer new words, change
    source IDs, translate, or accept a mention absent from its selected text.
    The unchanged strict literal validator must still pass afterward.
    """
    from copy import deepcopy
    by_id={span['id']:span['text'] for span in spans}
    result=deepcopy(contexts)
    for row in result.values():
        mention=row.get('source_mention')
        ids=row.get('support_span_ids')
        if not isinstance(mention,str) or not 3<=len(mention)<=160 or not isinstance(ids,list):
            continue
        texts=[by_id[sid] for sid in ids if sid in by_id]
        if any(mention in text for text in texts):
            continue
        matched=[]
        for text in texts:
            found=re.search(re.escape(mention),text,flags=re.IGNORECASE)
            if found is not None:
                matched.append(found.group(0))
        if matched and len(set(m.casefold() for m in matched))==1:
            row['source_mention']=matched[0]
    return result


def rebind_adjacent_literal_mentions(contexts, spans):
    """Use only a directly neighboring span of the SAME original source.

    A model may cite a sentence immediately after the object's literal name.
    Never invent a name, alter a fact, or rebind to a distant/context-free span.
    At most two immediate neighbours may be used when BOTH literally contain
    the same object mention: include both instead of guessing one. All other
    ambiguity remains for strict validation.
    """
    from copy import deepcopy
    by_id={span['id']:span for span in spans}
    repaired=deepcopy(contexts)
    for row in repaired.values():
        ids=row.get('support_span_ids',[])
        mention=row.get('source_mention','')
        if len(ids)!=1 or not isinstance(mention,str) or not 3<=len(mention)<=160:
            continue
        selected=by_id.get(ids[0])
        if selected is None or mention in selected['text']:
            continue
        adjacent=[span for span in spans
                  if span['source_id']==selected['source_id']
                  and (span['end']==selected['start'] or span['start']==selected['end'])
                  and mention in span['text']]
        # A literal name can occur on both sides of a selected source span.
        # All admitted citations remain from the SAME original source and
        # touch the selected span; never choose a distant or fuzzy match.
        if 1<=len(adjacent)<=2 and len({span['id'] for span in adjacent})==len(adjacent):
            row['support_span_ids']=[ids[0]]+[
                span['id'] for span in sorted(adjacent,key=lambda span:span['start'])]
    return repaired