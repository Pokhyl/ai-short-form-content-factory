from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from prototype.v4.render_manifest import assemble_render_manifest


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def base_payload(tmp: Path):
    audio=tmp/'voice.mp3'; audio.write_bytes(b'audio-bytes')
    photo=tmp/'photo.jpg'; photo.write_bytes(b'photo-bytes')
    timeline={
        'duration_seconds':4.0,
        'provenance':{'script_sha256':'s'*64,'audio_sha256':sha(audio),'timing_source':'actual_audio_whisper_segments'},
        'asset_resolution':{'all_exact_assets_hash_verified':True},
        'graphic_compilation':{'all_constructed_beats_compiled':True,'compiler':'graphic_compiler_v1'},
        'beats':[
            {'beat_id':'A','start_seconds':0.0,'end_seconds':2.0,'primary_visual':{'source_class':'exact','layout':'fullscreen','visible_subject':'exact subject'},'overlays':[{'type':'caption'}],
             'resolved_asset':{'local_path':str(photo),'sha256':sha(photo),'width':720,'height':1280,'license':'Public domain','page_url':'https://example.test','attribution_required':False,'artist':'Test'}},
            {'beat_id':'B','start_seconds':2.0,'end_seconds':4.0,'primary_visual':{'source_class':'constructed','layout':'fullscreen','visible_subject':'mechanism'},'overlays':[{'type':'caption'}],
             'compiled_graphic':{'durationSeconds':2.0,'elements':[{'id':'x','type':'rect'}],'source':{'beat_id':'B','compiler':'graphic_compiler_v1','visual_basis':'pictorial_primitive'}}},
        ],
    }
    whisper={'duration':4.0,'language':'en','probability':1.0,'words':[{'start':0.0,'end':0.5,'word':'hello'},{'start':2.0,'end':2.5,'word':'world'}]}
    return audio,photo,timeline,whisper


class RenderManifestTest(unittest.TestCase):
    def test_assembles_exact_and_constructed_track(self):
        with tempfile.TemporaryDirectory() as td:
            audio,_,timeline,whisper=base_payload(Path(td))
            out=assemble_render_manifest(timeline,whisper,audio_path=audio)
            self.assertEqual([x['renderer'] for x in out['visual_track']],['exact_media','motion_graphic'])
            self.assertEqual(out['captions']['source'],'actual_audio_whisper_words')
            self.assertEqual(out['profile']['width'],1080)
            self.assertEqual(out['profile']['height'],1920)

    def test_audio_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            audio,_,timeline,whisper=base_payload(Path(td)); audio.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'audio provenance mismatch'):
                assemble_render_manifest(timeline,whisper,audio_path=audio)

    def test_exact_asset_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            audio,photo,timeline,whisper=base_payload(Path(td)); photo.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'asset hash mismatch'):
                assemble_render_manifest(timeline,whisper,audio_path=audio)

    def test_missing_compiled_graphic_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            audio,_,timeline,whisper=base_payload(Path(td)); timeline['beats'][1].pop('compiled_graphic')
            with self.assertRaisesRegex(ValueError,'no compiled_graphic'):
                assemble_render_manifest(timeline,whisper,audio_path=audio)

    def test_out_of_range_word_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            audio,_,timeline,whisper=base_payload(Path(td)); whisper['words'][-1]['end']=5.0
            with self.assertRaisesRegex(ValueError,'invalid Whisper word timing'):
                assemble_render_manifest(timeline,whisper,audio_path=audio)


if __name__ == '__main__':
    unittest.main()
