from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _load_asset(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        payload = json.loads(Path(value).read_text(encoding='utf-8'))
        if isinstance(payload, dict):
            return payload
    raise ValueError('asset map values must be metadata objects or metadata JSON paths')


def resolve_timeline_assets(timeline: dict[str, Any], asset_map: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(timeline, dict):
        raise ValueError('timeline must be an object')
    if not isinstance(asset_map, dict):
        raise ValueError('asset_map must be an object')
    out = copy.deepcopy(timeline)
    beats = out.get('beats')
    if not isinstance(beats, list) or not beats:
        raise ValueError('timeline requires beats')

    used: set[str] = set()
    exact_count = 0
    annotated_exact_count = 0
    constructed_count = 0
    for beat in beats:
        beat_id = str(beat.get('beat_id') or '').strip()
        primary = beat.get('primary_visual') or {}
        source_class = str(primary.get('source_class') or '').strip()
        if source_class in {'exact', 'annotated_exact'}:
            if source_class == 'exact':
                exact_count += 1
            else:
                annotated_exact_count += 1
            if beat_id not in asset_map:
                raise ValueError(f'exact beat {beat_id} has no resolved asset')
            metadata = _load_asset(asset_map[beat_id])
            used.add(beat_id)
            local_path = Path(str(metadata.get('local_path') or ''))
            if not local_path.is_file():
                raise ValueError(f'exact beat {beat_id} asset file is missing: {local_path}')
            expected_sha = str(metadata.get('sha256') or '').strip()
            actual_sha = _sha256(local_path)
            if not expected_sha or actual_sha != expected_sha:
                raise ValueError(f'exact beat {beat_id} asset SHA mismatch')
            expected_title = str(primary.get('expected_file_title') or '').strip()
            actual_title = str(metadata.get('file_title') or '').strip()
            if expected_title:
                if not expected_title.lower().startswith('file:'):
                    expected_title = 'File:' + expected_title
                if actual_title != expected_title:
                    raise ValueError(f'exact beat {beat_id} Commons title mismatch: {actual_title} != {expected_title}')
            width = int(metadata.get('selected_width') or 0)
            height = int(metadata.get('selected_height') or 0)
            if width <= 0 or height <= 0:
                raise ValueError(f'exact beat {beat_id} asset dimensions are invalid')
            actual_orientation = 'portrait' if height > width else ('landscape' if width > height else 'square')
            layout = str(primary.get('layout') or '')
            declared_orientation = str(primary.get('source_orientation') or '')
            if layout == 'fullscreen' and actual_orientation != 'portrait' and declared_orientation != 'crop_safe':
                raise ValueError(f'exact beat {beat_id} cannot fullscreen actual {actual_orientation} media')
            beat['resolved_asset'] = {
                'provider': metadata.get('provider'),
                'file_title': actual_title,
                'page_url': metadata.get('page_url'),
                'local_path': str(local_path),
                'sha256': actual_sha,
                'bytes': int(metadata.get('bytes') or local_path.stat().st_size),
                'width': width,
                'height': height,
                'orientation': actual_orientation,
                'license': metadata.get('license'),
                'license_url': metadata.get('license_url'),
                'artist': metadata.get('artist'),
                'credit': metadata.get('credit'),
                'attribution_required': bool(metadata.get('attribution_required')),
            }
            if source_class == 'annotated_exact':
                beat['annotation_required'] = True
        elif source_class == 'constructed':
            constructed_count += 1
            beat['resolved_asset'] = None
            beat['construction_required'] = True
        elif source_class == 'contextual':
            raise ValueError(f'contextual beat {beat_id} requires a separate contextual-media resolver')
        else:
            raise ValueError(f'beat {beat_id} has unsupported source_class: {source_class}')

    unused = sorted(set(asset_map) - used)
    if unused:
        raise ValueError(f'asset_map contains unused beat ids: {unused}')
    out['asset_resolution'] = {
        'exact_resolved': exact_count,
        'annotated_exact_resolved': annotated_exact_count,
        'constructed_required': constructed_count,
        'all_exact_assets_hash_verified': True,
    }
    return out
