from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from prototype.v4.render_bundle import stage_render_bundle

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class RenderBundleTest(unittest.TestCase):
    def test_stages_verified_audio_and_exact_asset(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); audio=root/'a.mp3'; photo=root/'p.jpg'; audio.write_bytes(b'audio'); photo.write_bytes(b'photo')
            manifest={'manifest_version':'v4-render-manifest-1','audio':{'path':str(audio),'sha256':sha(audio)},'visual_track':[{'beat_id':'A','renderer':'exact_media','asset':{'path':str(photo),'sha256':sha(photo)}},{'beat_id':'B','renderer':'motion_graphic','graphic':{'elements':[{'id':'x'}]}}]}
            proof=stage_render_bundle(manifest,root/'bundle'); self.assertEqual(proof['exact_assets'],1); self.assertEqual(proof['motion_graphics'],1); self.assertTrue((root/'bundle/public/audio/voice.mp3').is_file()); self.assertTrue((root/'bundle/public/assets/A.jpg').is_file())
            props=(root/'bundle/props.json').read_text(); self.assertNotIn(str(audio),props); self.assertNotIn(str(photo),props)
    def test_stages_annotated_media_asset(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); audio=root/'a.mp3'; photo=root/'p.jpg'; audio.write_bytes(b'audio'); photo.write_bytes(b'photo')
            manifest={'manifest_version':'v4-render-manifest-1','audio':{'path':str(audio),'sha256':sha(audio)},'visual_track':[{'beat_id':'A','renderer':'annotated_media','asset':{'path':str(photo),'sha256':sha(photo)},'graphic':{'elements':[{'id':'arrow'}]}}]}
            proof=stage_render_bundle(manifest,root/'bundle'); self.assertEqual(proof['annotated_media'],1); self.assertTrue((root/'bundle/public/assets/A.jpg').is_file())
    def test_modified_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); audio=root/'a.mp3'; audio.write_bytes(b'audio'); manifest={'manifest_version':'v4-render-manifest-1','audio':{'path':str(audio),'sha256':'0'*64},'visual_track':[]}
            with self.assertRaisesRegex(ValueError,'source hash mismatch'): stage_render_bundle(manifest,root/'bundle')

if __name__=='__main__': unittest.main()
