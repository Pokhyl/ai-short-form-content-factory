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


def _resolve_visual_node(
    node: dict[str, Any],
    *,
    visual_id: str,
    asset_map: dict[str, Any],
    used: set[str],
    counters: dict[str, int],
) -> None:
    primary = node.get('primary_visual') or {}
    source_class = str(primary.get('source_class') or '').strip()
    if source_class in {'exact', 'annotated_exact', 'contextual'}:
        counters[source_class] += 1
        if visual_id not in asset_map:
            raise ValueError(f'exact visual {visual_id} has no resolved asset')
        metadata = _load_asset(asset_map[visual_id])
        used.add(visual_id)
        local_path = Path(str(metadata.get('local_path') or ''))
        if not local_path.is_file():
            raise ValueError(f'exact visual {visual_id} asset file is missing: {local_path}')
        expected_sha = str(metadata.get('sha256') or '').strip()
        actual_sha = _sha256(local_path)
        if not expected_sha or actual_sha != expected_sha:
            raise ValueError(f'exact visual {visual_id} asset SHA mismatch')
        expected_title = str(primary.get('expected_file_title') or '').strip()
        actual_title = str(metadata.get('file_title') or '').strip()
        if expected_title:
            if not expected_title.lower().startswith('file:'):
                expected_title = 'File:' + expected_title
            if actual_title != expected_title:
                raise ValueError(f'exact visual {visual_id} Commons title mismatch: {actual_title} != {expected_title}')
        width = int(metadata.get('selected_width') or 0)
        height = int(metadata.get('selected_height') or 0)
        if width <= 0 or height <= 0:
            raise ValueError(f'exact visual {visual_id} asset dimensions are invalid')
        actual_orientation = 'portrait' if height > width else ('landscape' if width > height else 'square')
        layout = str(primary.get('layout') or '')
        declared_orientation = str(primary.get('source_orientation') or '')
        if layout == 'fullscreen' and actual_orientation != 'portrait' and declared_orientation != 'crop_safe':
            raise ValueError(f'exact visual {visual_id} cannot fullscreen actual {actual_orientation} media')
        node['resolved_asset'] = {
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
            node['annotation_required'] = True
    elif source_class == 'constructed':
        counters[source_class] += 1
        node['resolved_asset'] = None
        node['construction_required'] = True
    else:
        raise ValueError(f'visual {visual_id} has unsupported source_class: {source_class}')


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
    counters = {'exact': 0, 'annotated_exact': 0, 'contextual': 0, 'constructed': 0}
    shot_count = 0
    for beat in beats:
        beat_id = str(beat.get('beat_id') or '').strip()
        shots = beat.get('shots')
        if isinstance(shots, list) and shots:
            for shot in shots:
                shot_id = str(shot.get('shot_id') or '').strip()
                if not shot_id:
                    raise ValueError(f'beat {beat_id} contains shot without shot_id')
                _resolve_visual_node(shot, visual_id=shot_id, asset_map=asset_map, used=used, counters=counters)
                shot_count += 1
        else:
            _resolve_visual_node(beat, visual_id=beat_id, asset_map=asset_map, used=used, counters=counters)

    unused = sorted(set(asset_map) - used)
    if unused:
        raise ValueError(f'asset_map contains unused visual ids: {unused}')
    out['asset_resolution'] = {
        'exact_resolved': counters['exact'],
        'annotated_exact_resolved': counters['annotated_exact'],
        'contextual_resolved': counters['contextual'],
        'constructed_required': counters['constructed'],
        'resolved_shots': shot_count,
        'all_exact_assets_hash_verified': True,
    }
    return out
