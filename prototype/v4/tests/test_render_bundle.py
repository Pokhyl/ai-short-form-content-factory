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

    def test_multishot_assets_use_visual_ids_and_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); audio=root/'a.mp3'; a=root/'a.jpg'; b=root/'b.jpg'
            audio.write_bytes(b'audio'); a.write_bytes(b'one'); b.write_bytes(b'two')
            manifest={'manifest_version':'v4-render-manifest-2','audio':{'path':str(audio),'sha256':sha(audio)},'visual_track':[
                {'visual_id':'E1A','beat_id':'E1','renderer':'exact_media','asset':{'path':str(a),'sha256':sha(a)}},
                {'visual_id':'E1B','beat_id':'E1','renderer':'exact_media','asset':{'path':str(b),'sha256':sha(b)}},
            ]}
            proof=stage_render_bundle(manifest,root/'bundle')
            self.assertEqual(proof['visual_items'],2)
            self.assertTrue((root/'bundle/public/assets/E1A.jpg').is_file())
            self.assertTrue((root/'bundle/public/assets/E1B.jpg').is_file())
            self.assertNotEqual((root/'bundle/public/assets/E1A.jpg').read_bytes(),(root/'bundle/public/assets/E1B.jpg').read_bytes())

    def test_modified_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); audio=root/'a.mp3'; audio.write_bytes(b'audio'); manifest={'manifest_version':'v4-render-manifest-1','audio':{'path':str(audio),'sha256':'0'*64},'visual_track':[]}
            with self.assertRaisesRegex(ValueError,'source hash mismatch'): stage_render_bundle(manifest,root/'bundle')

if __name__=='__main__': unittest.main()
