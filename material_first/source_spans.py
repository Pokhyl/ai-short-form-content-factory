"""Server-owned citation spans: the model selects IDs, never writes quotations."""
from copy import deepcopy
import hashlib
import re


def source_spans(sources):
    if not isinstance(sources, list) or not 1 <= len(sources) <= 3:
        raise ValueError('source span budget invalid')
    spans, seen = [], set()
    for index, source in enumerate(sources):
        text = source.get('text')
        if source['id'] in seen or not isinstance(text, str) or not text.strip() or len(text) > 80000:
            raise ValueError('source span text/identity invalid')
        seen.add(source['id'])
        if hashlib.sha256(text.encode()).hexdigest() != source.get('sha256'):
            raise ValueError('source span hash mismatch')
        start = 0
        while start < len(text):
            end = min(start + 1200, len(text))
            if end < len(text):
                # Prefer sentence boundaries; preserve every character, including
                # source typos, Unicode punctuation and intervening headings.
                boundaries = list(re.finditer(r'[.!?。！？]\s+', text[start:end]))
                cut = boundaries[-1].end() if boundaries else text[start:end].rfind(' ') + 1
                if cut >= 600:
                    end = start + cut
            spans.append({'id': f's{index + 1}-{start}-{end}', 'source_id': source['id'],
                          'start': start, 'end': end, 'text': text[start:end]})
            start = end
    return spans


def bind_support(sources, spans, facts):
    # Recompute the catalog rather than trusting supplied offsets/text.
    if spans != source_spans(sources):
        raise ValueError('source span catalog changed')
    by_id = {span['id']: span for span in spans}
    result = deepcopy(facts)
    for fact in result:
        supports = []
        seen = set()
        for selection in fact['support']:
            if set(selection) != {'span_id'} or selection['span_id'] not in by_id:
                raise ValueError('unknown source span selection')
            span = by_id[selection['span_id']]
            if span['id'] in seen:
                raise ValueError('duplicate source span selection')
            seen.add(span['id'])
            supports.append({'source_id': span['source_id'], 'quote': span['text']})
        fact['support'] = supports
    return {'sources': deepcopy(sources), 'facts': result}
