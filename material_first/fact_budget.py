"""Pre-freeze editorial scope for natural-duration Factory Next narration."""
import math

POLICY = 'duration-scoped-facts-v1'

def fact_budget(request):
    if request.get('fact_scope_policy') != POLICY:
        return None
    # Leave narration room for connective prose. This is an editorial bound,
    # never an assertion of measured speech duration.
    total = max(9, round(request['seconds'] * 1.8))
    return {'max_required_words': total,
            'max_single_fact_words': math.ceil(total / 3 * 1.4)}

def validate_fact_budget(request, draft):
    budget = fact_budget(request)
    if budget is None:
        return
    required = set(draft['required_fact_ids'])
    facts = [f for f in draft['facts'] if f['id'] in required]
    counts = {f['id']: len(f['text'].split()) for f in facts}
    if (sum(counts.values()) > budget['max_required_words'] or
            any(n > budget['max_single_fact_words'] for n in counts.values())):
        raise ValueError('required fact scope exceeds narration budget: '
                         + str({'observed_words': counts, **budget}))

def scope_instruction(request):
    budget = fact_budget(request)
    if budget is None:
        return ''
    return (f" Select exactly three distinct essential SINGLE claims in the requested narration language, "
            f"totaling at most {budget['max_required_words']} whitespace-separated words, "
            f"each at most {budget['max_single_fact_words']} words. "
            "Select a smaller coherent explanatory scope BEFORE facts freeze; do not compress "
            "whole source paragraphs into compound required facts. Keep necessary scientific "
            "qualifiers and causal meaning; omit optional background, examples and lists "
            "from the required inventory. The three claims together must answer the topic. "
            "Never remove essential qualifiers merely to satisfy length. ")
