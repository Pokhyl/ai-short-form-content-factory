"""A single undecodable source still image never stops all Factory Next materials.

Pure offline fixtures: no HTTP provider calls, no database writes, no model use.
"""
import subprocess
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from factory_v3.download import PhotoDownload
from factory_v3.preparation import ResourceUnavailable


CANDIDATE={
    "provider":"wikimedia",
    "id":"wikimedia:80800904",
    "media_url":"https://upload.wikimedia.org/wikipedia/commons/1/11/DNA_example.png",
}


class OnceHTTP:
    def __init__(self):
        self.sends=0

    def binary_receipt(self, url):
        self.sends+=1
        return {"headers":{"content-type":"image/png"},
                "body":b"\x89PNG\r\n\x1a\n"+b"known-invalid-decoder-input",
                "status":200}


class CachedCalls:
    def __init__(self):
        self.responses={}
        self.invokes=0

    def run(self,key,kind,identity,send,*,allow_unavailable=False):
        if key in self.responses:
            return self.responses[key]
        self.invokes+=1
        response=send()
        self.responses[key]=response
        return response


def broken_probe(_path):
    raise subprocess.CalledProcessError(1,["ffprobe","broken-original.png"])


class BadOriginalTests(unittest.TestCase):
    def test_next_only_local_media_rejection_is_cached_and_never_downloaded_twice(self):
        with tempfile.TemporaryDirectory() as folder:
            http=OnceHTTP()
            calls=CachedCalls()
            original=PhotoDownload(folder,str(uuid4()),calls,http,probe=broken_probe)
            original.skip_invalid_local_media=True
            with self.assertRaises(ResourceUnavailable) as error:
                original.download(CANDIDATE)
            self.assertEqual(error.exception.receipt["reason"],
                             "UNDECODABLE_DOWNLOADED_IMAGE")
            self.assertEqual(calls.invokes,1)
            self.assertEqual(http.sends,1)
            saved=calls.responses["download:wikimedia:80800904"]
            self.assertIs(saved["local_image_rejected"],True)
            self.assertEqual(saved["asset_id"],CANDIDATE["id"])
            # PostgreSQL has a durable successful result for the refused
            # original bytes; the same candidate cannot trigger a resend.
            with self.assertRaises(ResourceUnavailable):
                original.download(CANDIDATE)
            self.assertEqual(calls.invokes,1)
            self.assertEqual(http.sends,1)
            stored=list(Path(folder).rglob("selected.png"))
            self.assertEqual(len(stored),1)

    def test_legacy_download_error_behavior_is_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            http=OnceHTTP()
            calls=CachedCalls()
            legacy=PhotoDownload(folder,str(uuid4()),calls,http,probe=broken_probe)
            self.assertFalse(legacy.skip_invalid_local_media)
            with self.assertRaises(subprocess.CalledProcessError):
                legacy.download(CANDIDATE)
            self.assertEqual(http.sends,1)
            self.assertEqual(calls.responses,{})

    def test_factory_next_enables_skip_only_for_its_own_source_downloader(self):
        from hashlib import sha256
        from unittest.mock import Mock
        from factory_next.preparation import PreparationStages
        from material_first.portrait import PortraitDownload
        with tempfile.TemporaryDirectory() as folder:
            legacy=PhotoDownload(folder,str(uuid4()),CachedCalls(),OnceHTTP(),
                                 probe=broken_probe)
            ops=Mock()
            ops.downloader=PortraitDownload(folder,legacy)
            ops.discover.return_value=[]
            text="DNA has two strands with paired complementary bases."
            evidence={
                "sources":[{"id":"s1","url":"https://example.org/dna","text":text,
                            "sha256":sha256(text.encode()).hexdigest()}],
                "facts":[{"id":"f1","text":"DNA has two strands.",
                          "support":[{"source_id":"s1","quote":text}]}]}
            request={"topic":"DNA molecule","seconds":45,"language":"uk",
                     "visual_validation_mode":"gemini","required_fact_ids":["f1"]}
            self.assertFalse(legacy.skip_invalid_local_media)
            with self.assertRaisesRegex(ValueError,"insufficient distinct"):
                PreparationStages(folder,ops,lambda:None).materials({
                    "outputs":{"research":{"request":request,"queries":[{"query":"DNA"}],
                                           "evidence":evidence}}})
            self.assertTrue(legacy.skip_invalid_local_media)
            self.assertEqual(ops.topic,"DNA molecule")

    def test_metadata_validation_is_not_bypassed_by_malformed_content_type(self):
        with tempfile.TemporaryDirectory() as folder:
            http=OnceHTTP()
            http.binary_receipt=lambda url: {"headers":{"content-type":"text/html"},
                                             "body":b"not an image","status":200}
            calls=CachedCalls()
            adapted=PhotoDownload(folder,str(uuid4()),calls,http,probe=broken_probe)
            adapted.skip_invalid_local_media=True
            with self.assertRaisesRegex(ValueError,"unsupported/empty"):
                adapted.download(CANDIDATE)
            self.assertFalse(calls.responses)


if __name__=="__main__":
    unittest.main()
