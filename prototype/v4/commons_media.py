from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, quote, urlparse
from urllib.request import Request, urlopen

API_URL = 'https://commons.wikimedia.org/w/api.php'
USER_AGENT = 'ai-short-form-content-factory-v4/1.0 (exact-media prototype)'


def _meta(extmetadata: dict[str, Any], key: str) -> str:
    value = extmetadata.get(key)
    if isinstance(value, dict):
        return str(value.get('value') or '').strip()
    return ''


def _strip_html(value: str) -> str:
    return re.sub(r'<[^>]+>', '', value or '').strip()


def _license_is_free(name: str) -> bool:
    normalized = name.lower().replace('_', ' ').strip()
    allowed = ('public domain', 'cc0', 'cc by', 'cc-by', 'creative commons attribution', 'gfdl')
    return any(token in normalized for token in allowed)


def parse_commons_response(payload: dict[str, Any], *, requested_title: str) -> dict[str, Any]:
    pages = ((payload.get('query') or {}).get('pages') or {})
    if not isinstance(pages, dict) or not pages:
        raise ValueError('Commons response has no pages')
    page = next(iter(pages.values()))
    if not isinstance(page, dict) or page.get('missing') is not None:
        raise ValueError(f'Commons file not found: {requested_title}')
    infos = page.get('imageinfo')
    if not isinstance(infos, list) or not infos:
        raise ValueError(f'Commons file has no imageinfo: {requested_title}')
    info = infos[0]
    ext = info.get('extmetadata') or {}
    license_name = _strip_html(_meta(ext, 'LicenseShortName'))
    if not license_name or not _license_is_free(license_name):
        raise ValueError(f'Commons license is not accepted as free: {license_name or "unknown"}')
    width = int(info.get('width') or 0)
    height = int(info.get('height') or 0)
    if width <= 0 or height <= 0:
        raise ValueError('Commons media dimensions are invalid')
    selected_url = str(info.get('thumburl') or info.get('url') or '').strip()
    if not selected_url:
        raise ValueError('Commons media has no downloadable URL')
    selected_width = int(info.get('thumbwidth') or width)
    selected_height = int(info.get('thumbheight') or height)
    orientation = 'portrait' if selected_height > selected_width else ('landscape' if selected_width > selected_height else 'square')
    canonical_title = str(page.get('title') or requested_title)
    return {
        'provider': 'wikimedia_commons',
        'file_title': canonical_title,
        'page_url': 'https://commons.wikimedia.org/wiki/' + quote(canonical_title.replace(' ', '_'), safe=':_(),-'),
        'download_url': selected_url,
        'original_url': str(info.get('url') or ''),
        'mime': str(info.get('mime') or ''),
        'original_width': width,
        'original_height': height,
        'selected_width': selected_width,
        'selected_height': selected_height,
        'orientation': orientation,
        'license': license_name,
        'license_url': _strip_html(_meta(ext, 'LicenseUrl')),
        'artist': _strip_html(_meta(ext, 'Artist')),
        'credit': _strip_html(_meta(ext, 'Credit')),
        'description': _strip_html(_meta(ext, 'ImageDescription')),
        'attribution_required': 'public domain' not in license_name.lower() and 'cc0' not in license_name.lower(),
    }


def fetch_commons_file(file_title: str, output_dir: str | Path, *, max_width: int = 1440) -> dict[str, Any]:
    title = file_title.strip()
    if not title:
        raise ValueError('file_title is required')
    if not title.lower().startswith('file:'):
        title = 'File:' + title
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'imageinfo',
        'iiprop': 'url|size|mime|extmetadata',
        'iiurlwidth': str(max_width),
        'titles': title,
    }
    req = Request(API_URL + '?' + urlencode(params), headers={'User-Agent': USER_AGENT})
    with urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode('utf-8'))
    metadata = parse_commons_response(payload, requested_title=title)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(urlparse(metadata['download_url']).path).suffix or Path(title.split(':', 1)[-1]).suffix or '.bin'
    safe_stem = re.sub(r'[^A-Za-z0-9._-]+', '-', title.split(':', 1)[-1]).strip('-._') or 'asset'
    asset_path = out_dir / f'{safe_stem}{suffix if not safe_stem.lower().endswith(suffix.lower()) else ""}'
    media_req = Request(metadata['download_url'], headers={'User-Agent': USER_AGENT})
    h = hashlib.sha256()
    total = 0
    with urlopen(media_req, timeout=60) as response, asset_path.open('wb') as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            h.update(chunk)
            total += len(chunk)
    if total <= 0:
        raise RuntimeError('Commons download produced an empty file')
    metadata['local_path'] = str(asset_path)
    metadata['bytes'] = total
    metadata['sha256'] = h.hexdigest()
    meta_path = asset_path.with_suffix(asset_path.suffix + '.json')
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    metadata['metadata_path'] = str(meta_path)
    return metadata
