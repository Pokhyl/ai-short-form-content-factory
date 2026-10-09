"""Validate source mentions before spending the photo-search budget."""
import re
from .photo_queries import SYNTHETIC, INVISIBLE

DEPICTION = re.compile(r"\b(?:representations?|depictions?|radiation\s+beams?|particle\s+beams?|artwork|renderings?)\b", re.I)

def validate_context_mentions(contexts, spans):
    catalog = {s['id']: s['text'] for s in spans}
    for role, row in contexts.items():
        mention = row.get('source_mention', '').strip()
        selected = row.get('support_span_ids', [])
        if not 3 <= len(mention) <= 160 or not selected or any(s not in catalog for s in selected):
            raise ValueError(role + ': source object mention is missing or invalid')
        if not any(mention in catalog[s] for s in selected):
            raise ValueError(role + ': selected source span does not contain the object mention')
        query = row['query'].strip()
        if any(pattern.search(query) for pattern in (SYNTHETIC, INVISIBLE, DEPICTION)):
            raise ValueError(role + ': search requests a depiction or invisible mechanism')
        if query.casefold() != row['subject'].strip().casefold():
            raise ValueError(role + ': search must use only the source-linked English object name')
