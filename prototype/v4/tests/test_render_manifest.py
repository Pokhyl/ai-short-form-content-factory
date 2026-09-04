from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from prototype.v4.render_manifest import assemble_render_manifest

def sha(path: Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()

def base_payload(tmp:Path):
    audio=tmp/'voice.mp3'; audio.write_bytes(b'audio-bytes'); photo=tmp/'photo.jpg'; photo.write_bytes(b'photo-bytes')
    timeline={'duration_seconds':4.0,'provenance':{'script_sha256':'s'*64,'audio_sha256':sha(audio),'timing_source':'actual_audio_whisper_segments'},'asset_resolution':{'all_exact_assets_hash_verified':True},'graphic_compilation':{'all_constructed_beats_compiled':True,'compiler':'graphic_compiler_v1'},'beats':[{'beat_id':'A','start_seconds':0.0,'end_seconds':2.0,'primary_visual':{'source_class':'exact','layout':'fullscreen','visible_subject':'exact subject'},'overlays':[{'type':'caption'}],'resolved_asset':{'local_path':str(photo),'sha256':sha(photo),'width':720,'height':1280,'license':'Public domain','page_url':'https://example.test','attribution_required':False,'artist':'Test'}},{'beat_id':'B','start_seconds':2.0,'end_seconds':4.0,'primary_visual':{'source_class':'constructed','layout':'fullscreen','visible_subject':'mechanism'},'overlays':[{'type':'caption'}],'compiled_graphic':{'durationSeconds':2.0,'elements':[{'id':'x','type':'rect'}],'source':{'beat_id':'B','compiler':'graphic_compiler_v1','visual_basis':'pictorial_primitive'}}}]}
    whisper={'duration':4.0,'language':'en','probability':1.0,'words':[{'start':0.0,'end':0.5,'word':'hello'},{'start':2.0,'end':2.5,'word':'world'}]}; return audio,photo,timeline,whisper

class RenderManifestTest(unittest.TestCase):
    def test_assembles_exact_and_constructed_track(self):
        with tempfile.TemporaryDirectory() as td:
            audio,_,timeline,whisper=base_payload(Path(td)); out=assemble_render_manifest(timeline,whisper,audio_path=audio); self.assertEqual([x['renderer'] for x in out['visual_track']],['exact_media','motion_graphic']); self.assertEqual(out['captions']['source'],'actual_audio_whisper_words'); self.assertEqual(out['profile']['width'],1080); self.assertEqual(out['profile']['height'],1920)
    def test_annotated_exact_combines_verified_asset_and_overlay(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); audio=root/'voice.mp3'; photo=root/'photo.jpg'; audio.write_bytes(b'audio-bytes'); photo.write_bytes(b'photo-bytes')
            tl={'duration_seconds':2.0,'provenance':{'script_sha256':'s'*64,'audio_sha256':sha(audio),'timing_source':'actual_audio_whisper_segments'},'asset_resolution':{'all_exact_assets_hash_verified':True},'graphic_compilation':{'all_required_graphics_compiled':True,'compiler':'graphic_compiler_v1'},'beats':[{'beat_id':'A','start_seconds':0.0,'end_seconds':2.0,'primary_visual':{'source_class':'annotated_exact','layout':'fullscreen','visible_subject':'exact mechanism'},'resolved_asset':{'local_path':str(photo),'sha256':sha(photo),'width':720,'height':1280,'license':'Public domain','page_url':'https://example.test','attribution_required':False,'artist':'Test'},'compiled_graphic':{'durationSeconds':2.0,'elements':[{'id':'arrow','type':'line'}],'source':{'beat_id':'A','visual_basis':'exact_media_annotation'}}}]}
            whisper={'duration':2.0,'language':'en','probability':1.0,'words':[{'start':0.0,'end':0.5,'word':'hello'}]}; out=assemble_render_manifest(tl,whisper,audio_path=audio); self.assertEqual(out['visual_track'][0]['renderer'],'annotated_media'); self.assertIn('asset',out['visual_track'][0]); self.assertIn('graphic',out['visual_track'][0])

    def test_multishot_beat_flattens_to_distinct_render_items(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); audio=root/'voice.mp3'; a=root/'a.jpg'; b=root/'b.jpg'
            audio.write_bytes(b'audio'); a.write_bytes(b'a'); b.write_bytes(b'b')
            tl={
                'duration_seconds':4.0,
                'provenance':{'script_sha256':'s'*64,'audio_sha256':sha(audio),'timing_source':'actual_audio_whisper_word_alignment'},
                'asset_resolution':{'all_exact_assets_hash_verified':True},
                'beats':[{
                    'beat_id':'A','start_seconds':0.0,'end_seconds':4.0,'source_narration':'one two',
                    'primary_visual':{'source_class':'exact','layout':'fullscreen','visible_subject':'semantic scene'},
                    'shots':[
                        {'shot_id':'A1','start_seconds':0.0,'end_seconds':2.0,'primary_visual':{'source_class':'exact','layout':'fullscreen','visible_subject':'first'},'resolved_asset':{'local_path':str(a),'sha256':sha(a),'width':720,'height':1280,'license':'Public domain','page_url':'x','attribution_required':False}},
                        {'shot_id':'A2','start_seconds':2.0,'end_seconds':4.0,'primary_visual':{'source_class':'exact','layout':'fullscreen','visible_subject':'second'},'resolved_asset':{'local_path':str(b),'sha256':sha(b),'width':720,'height':1280,'license':'Public domain','page_url':'y','attribution_required':False}},
                    ],
                }],
            }
            whisper={'duration':4.0,'language':'en','probability':1.0,'words':[{'start':0.0,'end':0.5,'word':'one'},{'start':2.0,'end':2.5,'word':'two'}]}
            out=assemble_render_manifest(tl,whisper,audio_path=audio)
            self.assertEqual(out['manifest_version'],'v4-render-manifest-2')
            self.assertEqual([x['visual_id'] for x in out['visual_track']],['A1','A2'])
            self.assertEqual([x['beat_id'] for x in out['visual_track']],['A','A'])
            self.assertEqual(out['captions']['source'],'actual_audio_whisper_timing_script_text')

    def test_audio_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            audio,_,timeline,whisper=base_payload(Path(td)); audio.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'audio provenance mismatch'): assemble_render_manifest(timeline,whisper,audio_path=audio)
    def test_exact_asset_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            audio,photo,timeline,whisper=base_payload(Path(td)); photo.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'asset hash mismatch'): assemble_render_manifest(timeline,whisper,audio_path=audio)
    def test_missing_compiled_graphic_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            audio,_,timeline,whisper=base_payload(Path(td)); timeline['beats'][1].pop('compiled_graphic')
            with self.assertRaisesRegex(ValueError,'no compiled_graphic'): assemble_render_manifest(timeline,whisper,audio_path=audio)
    def test_out_of_range_word_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            audio,_,timeline,whisper=base_payload(Path(td)); whisper['words'][-1]['end']=5.0
            with self.assertRaisesRegex(ValueError,'invalid Whisper word timing'): assemble_render_manifest(timeline,whisper,audio_path=audio)

if __name__=='__main__': unittest.main()
