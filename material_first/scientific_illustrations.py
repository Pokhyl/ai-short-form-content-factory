"""Opt-in provenance gate for explicitly labelled scientific illustrations.

A licensed published diagram is a still-image file, NOT a camera photograph.
Only Factory Next may opt into this path; the legacy photographic path stays
unchanged. A model must still inspect actual pixels and independently link
visible details to source-grounded facts.
"""
from urllib.parse import urlsplit

COMMONS_LICENSES = frozenset({'Public Domain', 'CC0', 'CC BY', 'CC BY-SA'})


def trusted_commons_illustration_source(asset):
    if not isinstance(asset, dict):
        return False
    try:
        page = urlsplit(asset.get('source_url', ''))
        license_url = urlsplit(asset.get('license_url', ''))
    except (TypeError, ValueError):
        return False
    return (asset.get('provider') == 'wikimedia'
            and str(asset.get('id', '')).startswith('wikimedia:')
            and asset.get('media_type') == 'photo'  # still-image container, not photographic assertion
            and page.scheme == 'https'
            and page.hostname == 'commons.wikimedia.org'
            and not page.username and not page.password and page.port in (None, 443)
            and license_url.scheme == 'https'
            and license_url.hostname in ('commons.wikimedia.org', 'creativecommons.org',
                                         'www.creativecommons.org')
            and not license_url.username and not license_url.password
            and license_url.port in (None, 443)
            and asset.get('license') in COMMONS_LICENSES
            and isinstance(asset.get('sha256'), str)
            and len(asset['sha256']) == 64)


def is_scientific_illustration(asset, receipt):
    return (trusted_commons_illustration_source(asset)
            and isinstance(receipt, dict)
            and receipt.get('inspection_protocol') == 'source-illustration-v1'
            and receipt.get('medium') == 'illustration'
            and receipt.get('illustration_type') in
                ('scientific_diagram', 'structural_illustration')
            and receipt.get('accepted') is True
            and receipt.get('is_real_material') is True
            and receipt.get('subject_fully_visible') is True
            and receipt.get('topic_relation', {}).get('kind') in
                ('direct_subject', 'direct_part_or_stage')
            and bool(receipt.get('visible_fact_details')))
