"""Isolated actual-media regression; no semantic or production acceptance claim.

Run with production media mounted READ ONLY at /fixtures-media and empty /data.
Existing voice and photograph are copied to a fresh UUID; no provider calls.
"""
import importlib.util
import json
from pathlib import Path
import shutil
import uuid
import sys

sys.path.insert(0, '/worker')
import server
spec = importlib.util.spec_from_file_location('audit', '/fixtures/audit_final_media.py')
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)
root = Path('/fixtures-media')
fixture = None
for path in sorted((root / 'renders').glob('*/manifest.json')):
    manifest = json.loads(path.read_text())
    audio = root / 'voiceovers' / path.parent.name / 'final.mp3'
    if audio.exists() and 14208 <= manifest.get('audio_duration_ms', 0) <= 15768:
        for segment in manifest.get('segments', []):
            if segment.get('media_type') == 'photo':
                files = list((root / 'visuals' / path.parent.name / segment['shot_uuid']).glob('selected.*'))
                if files:
                    fixture = (audio, files[0], manifest['audio_duration_ms'])
                    break
    if fixture:
        break
if fixture is None:
    raise RuntimeError('no immutable real-media fixture found')
job, shot, scene, visual = (str(uuid.uuid4()) for _ in range(4))
audio_dir = Path('/data/voiceovers') / job
asset_dir = Path('/data/visuals') / job / shot
final_dir = Path('/data/renders') / job
for folder in (audio_dir, asset_dir, final_dir):
    folder.mkdir(parents=True, exist_ok=False)
shutil.copyfile(fixture[0], audio_dir / 'final.mp3')
asset = asset_dir / ('selected' + fixture[1].suffix)
shutil.copyfile(fixture[1], asset)
probe = json.loads(server.subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(asset)],
                    check=True, capture_output=True, text=True).stdout)['streams'][0]
duration = fixture[2]
result = server.render_final_video(job, server.file_sha256(audio_dir / 'final.mp3'), duration,
    max(15000, duration), 15000, [{'scene_uuid': scene, 'shot_uuid': shot, 'visual_asset_id': visual,
        'media_type': 'photo', 'asset_sha256': server.file_sha256(asset), 'scene_order': 1,
        'segment_start_ms': 0, 'segment_end_ms': max(15000, duration),
        'speech_start_ms': 0, 'speech_end_ms': duration,
        'asset_width': probe['width'], 'asset_height': probe['height'], 'asset_path': str(asset)}], final_dir)
checked = audit_module.audit(job, 15, Path('/data'), expected_scenes=1)
if not checked['passed']:
    raise RuntimeError(json.dumps(checked))
print(json.dumps({'isolated': True, 'provider_calls': 0, 'human_pass': False,
                  'semantic_acceptance': False, 'audit': checked}))
