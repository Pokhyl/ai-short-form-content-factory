"""Offline byte-level integration gate, NOT semantic or natural-voice acceptance.

Synthesized test tone and test images exercise the actual FFmpeg renderer and
independent MP4 audit, without provider calls or production media writes.
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from factory_next.media import MediaStages
from factory_next.timeline import compile_edit
from material_first.rendering import probe, sha


def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', *map(str, args)],
                   check=True, stdout=subprocess.DEVNULL, timeout=30)


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),
                     'FFmpeg and ffprobe required for actual-byte integration test')
class ActualMediaBoundary(unittest.TestCase):
    def test_measured_edit_renders_and_independent_audit_passes(self):
        with tempfile.TemporaryDirectory(prefix='factory-next-media-') as temporary:
            root = Path(temporary)
            job_id = str(uuid4())
            audio_dir = root / 'voiceovers' / job_id
            audio_dir.mkdir(parents=True)
            audio = audio_dir / 'final.mp3'
            # A signal is deliberately used instead of pretending to have reviewed speech.
            ffmpeg('-f', 'lavfi', '-i', 'sine=frequency=523:duration=14.5',
                   '-ar', '48000', '-ac', '1', '-c:a', 'libmp3lame', '-q:a', '3', audio)
            duration_ms = round(float(probe(audio)['format']['duration']) * 1000)
            self.assertGreaterEqual(duration_ms, 14000)
            self.assertLessEqual(duration_ms, 15000)
            photo_dir = root / 'photos'
            photo_dir.mkdir()
            assets = []
            photos = []
            for i, color in enumerate(('red', 'green', 'blue', 'yellow', 'magenta', 'cyan')):
                relative = f'photos/test-{i}.png'
                path = root / relative
                ffmpeg('-f', 'lavfi', '-i', f'color=c={color}:s=144x256:d=0.1',
                       '-frames:v', '1', path)
                signature = sha(path)
                assets.append({'id': f'p{i}', 'path': relative, 'sha256': signature,
                               'source_url': f'https://example.invalid/photo/{i}',
                               'author': 'controlled integration fixture',
                               'license': 'CC0', 'license_url': 'https://creativecommons.org/publicdomain/zero/1.0/',
                               'media_type': 'photo'})
                photos.append({'id': f'p{i}', 'sha256': signature, 'media_type': 'photo',
                               'supported_fact_ids': [f'f{i // 2}']})
            scenes = [{'id': f's{i}', 'material_id': f'p{i * 2}',
                       'narration': f'Controlled source-bound paragraph {i}',
                       'evidence_ids': [f'f{i}']} for i in range(3)]
            timings = [{'start_ms': duration_ms * i / 3,
                        'end_ms': duration_ms * (i + 1) / 3} for i in range(3)]
            plan = compile_edit(scenes, photos, timings, duration_ms, 15)
            original_audio_hash = sha(audio)
            original_photo_hashes = {a['id']: a['sha256'] for a in assets}
            outputs = {'materials': {'photos': photos, 'assets': assets},
                       'story': {'scenes': scenes},
                       'voice': {'sha256': original_audio_hash, 'duration_ms': duration_ms},
                       'alignment': {'audio_sha256': original_audio_hash, 'timings': timings},
                       'edit': plan}
            context = {'id': job_id, 'request': {'seconds': 15, 'language': 'pl',
                                              'topic': 'Controlled fixture'}, 'outputs': outputs}
            adapter = MediaStages(root)
            rendered = adapter.render(context)
            outputs['render'] = rendered
            audited = adapter.audit(context)
            self.assertTrue(audited['passed'])
            self.assertTrue(all(audited['gates'].values()))
            self.assertEqual(audited['duration_ms'], 15000)
            self.assertEqual(sha(audio), original_audio_hash)
            self.assertEqual({a['id']: sha(root / a['path']) for a in assets},
                             original_photo_hashes)
            self.assertEqual(sha(Path(rendered['path'])), rendered['sha256'])
            self.assertEqual(len(plan['shots']), audited['scene_count'])
