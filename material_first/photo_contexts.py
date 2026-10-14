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
    r"\d{3,6}(?:[.-]\d{1,6}(?:\.\d+)?[A-Z]?)?(?:[A-Z])?(?:\+\d{1,4})?\b", re.I)


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
