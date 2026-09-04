from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from prototype.v4.asset_resolver import resolve_timeline_assets


def timeline():
    return {'duration_seconds':4,'beats':[{'beat_id':'A','primary_visual':{'source_class':'exact','layout':'fullscreen','source_orientation':'portrait','expected_file_title':'Example.jpg'}},{'beat_id':'B','primary_visual':{'source_class':'constructed','layout':'fullscreen','source_orientation':'not_applicable'}}]}


class AssetResolverTest(unittest.TestCase):
    def make_asset(self,root:Path,*,title='File:Example.jpg',width=1000,height=1600):
        media=root/'asset.jpg'; media.write_bytes(b'exact-media'); sha=hashlib.sha256(media.read_bytes()).hexdigest()
        meta={'provider':'wikimedia_commons','file_title':title,'page_url':'https://commons.wikimedia.org/wiki/File:Example.jpg','local_path':str(media),'sha256':sha,'bytes':media.stat().st_size,'selected_width':width,'selected_height':height,'license':'Public domain','license_url':'','artist':'','credit':'','attribution_required':False}
        p=root/'asset.jpg.json'; p.write_text(json.dumps(meta)); return p,meta
    def test_resolves_and_hash_verifies_exact_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,_=self.make_asset(Path(tmp)); result=resolve_timeline_assets(timeline(),{'A':str(p)}); self.assertTrue(result['asset_resolution']['all_exact_assets_hash_verified']); self.assertEqual(result['asset_resolution']['exact_resolved'],1); self.assertTrue(result['beats'][1]['construction_required'])
    def test_resolves_annotated_exact_asset_and_marks_annotation_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,_=self.make_asset(Path(tmp)); tl={'duration_seconds':2,'beats':[{'beat_id':'A','primary_visual':{'source_class':'annotated_exact','layout':'fullscreen','source_orientation':'portrait','expected_file_title':'Example.jpg'}}]}; result=resolve_timeline_assets(tl,{'A':str(p)}); self.assertEqual(result['asset_resolution']['annotated_exact_resolved'],1); self.assertTrue(result['beats'][0]['annotation_required']); self.assertIsNotNone(result['beats'][0]['resolved_asset'])
    def test_wrong_title_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,_=self.make_asset(Path(tmp),title='File:Wrong.jpg')
            with self.assertRaisesRegex(ValueError,'title mismatch'): resolve_timeline_assets(timeline(),{'A':str(p)})
    def test_modified_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,meta=self.make_asset(Path(tmp)); Path(meta['local_path']).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'SHA mismatch'): resolve_timeline_assets(timeline(),{'A':str(p)})
    def test_missing_exact_asset_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'no resolved asset'): resolve_timeline_assets(timeline(),{})

if __name__=='__main__': unittest.main()
