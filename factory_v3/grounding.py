"""Traceable research evidence: exact fetched text hashes and supporting quotations."""
import hashlib
from urllib.parse import urlparse


def validate_evidence(evidence):
    sources = evidence.get("sources", [])
    facts = evidence.get("facts", [])
    if not sources or not facts or len(sources)>20 or len(facts)>64:
        raise ValueError("evidence sources/facts missing or over budget")
    by_source = {}
    for source in sources:
        key = source["id"]
        if key in by_source or not source.get("text") or len(source["text"])>80000:
            raise ValueError("duplicate or invalid source text")
        url = urlparse(source["url"])
        if url.scheme not in {"http","https"} or not url.hostname:
            raise ValueError("invalid research source URL")
        actual=hashlib.sha256(source["text"].encode()).hexdigest()
        if source.get("sha256")!=actual:
            raise ValueError("research source text hash mismatch")
        by_source[key]=source
    by_fact = {}
    contexts = evidence.get('visual_contexts', [])
    if 'visual_contexts' in evidence and (len(contexts) != 3 or {c.get('id') for c in contexts} != {'v0', 'v1', 'v2'}):
        raise ValueError('documented visual context identities incomplete')
    for context in contexts:
        if not context.get('subject') or not context.get('query') or not context.get('support'):
            raise ValueError('documented visual context missing')
        for support in context['support']:
            source = by_source.get(support.get('source_id'))
            quote = support.get('quote')
            if source is None or not isinstance(quote, str) or not quote or quote not in source['text']:
                raise ValueError('visual context support is not an exact source quotation')
    for fact in facts:
        if fact["id"] in by_fact or not fact.get("text") or not fact.get("support"):
            raise ValueError("duplicate or unsupported fact")
        for support in fact["support"]:
            source=by_source.get(support.get("source_id"))
            quote=support.get("quote")
            if source is None or not isinstance(quote,str) or not quote or quote not in source["text"]:
                raise ValueError("fact support is not an exact source quotation")
        by_fact[fact["id"]]=fact
    return by_fact


def validate_script_review(evidence, language, script, scenes, review, topic=None):
    """A trusted semantic reviewer must approve the exact final text, not just citation IDs."""
    if not isinstance(review,dict) or not review.get("receipt_id") or not review.get("model"):
        raise ValueError("trusted script review missing")
    from .preflight import digest
    if review.get("script_sha256")!=hashlib.sha256(script.encode()).hexdigest() or review.get("evidence_sha256")!=digest(evidence):
        raise ValueError("script review applies to different narration or evidence")
    if review.get("language")!=language or any(review.get(k) is not True for k in
        ("language_match","visual_contracts_match","no_unsupported_claims")):
        raise ValueError("script semantic/language review failed")
    if 'native_language_quality' in review and review['native_language_quality'] is not True:
        raise ValueError('native-language quality review failed')
    if topic is not None and (review.get("topic_covered") is not True or review.get("topic_sha256") != hashlib.sha256(topic.encode()).hexdigest()):
        raise ValueError("script does not answer the requested topic")
    expected={(s["id"],f) for s in scenes for f in s["evidence_ids"]}
    by_scene={s["id"]:s for s in scenes}
    checks=review.get("factual_checks",[])
    observed=set()
    for check in checks:
        key=(check.get("scene_id"),check.get("fact_id"))
        quote=check.get("narration_quote")
        if key not in expected or key in observed or check.get("supported") is not True:
            raise ValueError("narrated fact not supported")
        if not isinstance(quote,str) or not quote or quote not in by_scene[key[0]]["narration"]:
            raise ValueError("semantic check does not quote actual narration")
        observed.add(key)
    if observed!=expected:
        raise ValueError("semantic review omitted narrated facts")


def compact_evidence(evidence):
    """Model view of already validated evidence; full source bytes stay in the plan.

    Preserve every fact and exact supporting quotation. Do not re-send entire
    articles for each image. The original hashes continue to bind local QA.
    """
    from copy import deepcopy
    return {**({'visual_contexts': deepcopy(evidence['visual_contexts'])} if 'visual_contexts' in evidence else {}),
        "facts": deepcopy(evidence["facts"]), "sources": [
        {key: source[key] for key in ("id", "url", "sha256")}
        for source in evidence.get("sources", [])]}
