"""Validate source mentions before spending the photo-search budget."""
import re
from .photo_queries import SYNTHETIC, INVISIBLE

DEPICTION = re.compile(r"\b(?:representations?|depictions?|radiation\s+beams?|particle\s+beams?|artwork|renderings?)\b", re.I)

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
