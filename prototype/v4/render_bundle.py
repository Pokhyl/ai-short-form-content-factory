from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


def sha256_file(path: str | Path) -> str:
    h=hashlib.sha256()
    with Path(path).open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _copy_verified(src: Path, dst: Path, expected_sha: str) -> None:
    if not src.is_file():
        raise ValueError(f'source file missing: {src}')
    actual=sha256_file(src)
    if actual != expected_sha:
        raise ValueError(f'source hash mismatch for {src}: {actual} != {expected_sha}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src,dst)
    copied=sha256_file(dst)
    if copied != expected_sha:
        raise ValueError(f'copied hash mismatch for {dst}')


def stage_render_bundle(manifest: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    if manifest.get('manifest_version') not in {'v4-render-manifest-1','v4-render-manifest-2'}:
        raise ValueError('unsupported render manifest version')
    out=Path(output_dir)
    public=out/'public'
    public.mkdir(parents=True, exist_ok=True)
    staged=copy.deepcopy(manifest)

    audio=staged.get('audio') or {}
    audio_src=Path(str(audio.get('path') or ''))
    audio_sha=str(audio.get('sha256') or '')
    suffix=audio_src.suffix or '.mp3'
    audio_rel=f'audio/voice{suffix}'
    _copy_verified(audio_src, public/audio_rel, audio_sha)
    audio['src']=audio_rel
    audio.pop('path',None)

    exact=0
    annotated=0
    constructed=0
    seen_visual_ids:set[str]=set()
    for item in staged.get('visual_track',[]):
        renderer=item.get('renderer')
        visual_id=str(item.get('visual_id') or item.get('shot_id') or item.get('beat_id') or '').strip()
        if not visual_id or visual_id in seen_visual_ids:
            raise ValueError(f'invalid or duplicate render visual id: {visual_id!r}')
        seen_visual_ids.add(visual_id)
        if renderer in {'exact_media', 'annotated_media'}:
            asset=item.get('asset') or {}
            src=Path(str(asset.get('path') or ''))
            expected=str(asset.get('sha256') or '')
            suffix=src.suffix or '.bin'
            safe_id=''.join(ch if ch.isalnum() or ch in '-_' else '-' for ch in visual_id)
            rel=f"assets/{safe_id}{suffix}"
            _copy_verified(src, public/rel, expected)
            asset['src']=rel
            asset.pop('path',None)
            if renderer == 'annotated_media':
                graphic=item.get('graphic')
                if not isinstance(graphic,dict) or not graphic.get('elements'):
                    raise ValueError(f"annotated media graphic missing for {visual_id}")
                annotated += 1
            else:
                exact += 1
        elif renderer == 'motion_graphic':
            graphic=item.get('graphic')
            if not isinstance(graphic,dict) or not graphic.get('elements'):
                raise ValueError(f"motion graphic missing for {visual_id}")
            constructed += 1
        else:
            raise ValueError(f'unsupported renderer in manifest: {renderer}')

    props=out/'props.json'
    props.write_text(json.dumps(staged,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    proof={
        'bundle_version':'v4-render-bundle-2',
        'props_path':str(props),
        'public_dir':str(public),
        'visual_items':len(staged.get('visual_track',[])),
        'exact_assets':exact,
        'annotated_media':annotated,
        'motion_graphics':constructed,
        'audio_sha256':audio_sha,
    }
    (out/'bundle-proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return proof
