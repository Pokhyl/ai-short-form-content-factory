"""Controlled official-response shapes; no real search/download/API calls."""
import copy
import hashlib
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from factory_v3.download import PhotoDownload
from factory_v3.http import HTTPFailure, JSONHTTP
from factory_v3.preparation import BudgetedCalls
from factory_v3.providers import PhotoSearch, candidates, commons_license, media_url
from factory_v3.preflight import digest
from test_preparation import FakeLedger


PIX = {"id": 1, "type": "photo", "pageURL": "https://pixabay.com/photos/test-1/",
       "user": "Controlled Author", "user_id": 2, "largeImageURL": "https://cdn.pixabay.com/photo/test.jpg",
       "imageWidth": 1600, "imageHeight": 1200, "tags": "controlled"}
PEX = {"id": 3, "url": "https://www.pexels.com/photo/test-3/", "photographer": "Controlled",
       "photographer_url": "https://www.pexels.com/@controlled/", "src": {"large2x": "https://images.pexels.com/photos/3/test.jpg"},
       "width": 1600, "height": 1200, "alt": "controlled"}
WIKI = {"pageid": 4, "title": "File:Controlled.jpg", "imageinfo": [{"mime": "image/jpeg",
       "descriptionurl": "https://commons.wikimedia.org/wiki/File:Controlled.jpg",
       "url": "https://upload.wikimedia.org/wikipedia/commons/a/ab/Controlled.jpg",
       "width": 1600, "height": 1200, "extmetadata": {
       "LicenseShortName": {"value": "CC BY-SA 4.0"},
       "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0/"},
       "Artist": {"value": "<span>Controlled Author</span>"}}}]}


class Cache:
    def __init__(self):
        self.entries = {}

    def run(self, identity, provider, send):
        key = digest(identity)
        if key not in self.entries:
            self.entries[key] = send()
        return self.entries[key]


class HTTP:
    def __init__(self):
        self.searches = []
        self.downloads = []

    def request_receipt(self, method, url, headers, timeout):
        self.searches.append(url)
        return {"status": 200, "headers": {"x-ratelimit-remaining": "99"},
                "body": {"hits": [PIX]}}

    def binary_receipt(self, url):
        self.downloads.append(url)
        return {"status": 200, "headers": {"content-type": "image/jpeg"},
                "body": b"\xff\xd8\xffcontrolled-photo"}


class ProviderTests(unittest.TestCase):
    def test_saved_public_domain_records_keep_real_observations_without_a_license_url(self):
        saved = json.loads((Path(__file__).parent/'fixtures/commons-public-domain-retrieval.json').read_text())
        parsed = [asset for body in saved['search_responses'] for asset in candidates('wikimedia', body)]
        by_id = {asset['id']:asset for asset in parsed}
        for identity in ('wikimedia:516106','wikimedia:51481413','wikimedia:161778805'):
            asset = by_id[identity]
            self.assertEqual(asset['license'], 'Public Domain')
            self.assertEqual(asset['license_url'], 'https://commons.wikimedia.org/wiki/Help:Public_domain')
            self.assertTrue(asset['author'])
            self.assertEqual(asset['source_metadata']['imageinfo'][0]['extmetadata']['Copyrighted']['value'], 'False')
        self.assertNotIn('wikimedia:181623408', {asset['id'] for asset in parsed if asset['license']=='Public Domain'})

    def test_missing_license_link_is_not_an_unknown_or_copyrighted_license_fallback(self):
        for license_name, copyright, nonfree in [('CC BY 4.0','True','False'), ('Public domain','True','False'),
                                                ('Public domain',None,'False'),('Public domain','False','True')]:
            entry=copy.deepcopy(WIKI); metadata=entry['imageinfo'][0]['extmetadata']
            metadata.pop('LicenseUrl'); metadata['LicenseShortName']['value']=license_name
            metadata['Copyrighted']={'value':copyright};metadata['NonFree']={'value':nonfree}
            self.assertEqual(candidates('wikimedia',{'query':{'pages':{'4':entry}}}),[])
        entry=copy.deepcopy(WIKI);entry['imageinfo'][0]['extmetadata']['LicenseUrl']['value']='https://evil.invalid/license'
        self.assertEqual(candidates('wikimedia',{'query':{'pages':{'4':entry}}}),[])

    def test_commons_preserves_search_rank_not_page_dictionary_order(self):
        first=copy.deepcopy(WIKI);first.update(pageid=5,index=2)
        second=copy.deepcopy(WIKI);second.update(pageid=6,index=1)
        self.assertEqual([a['id'] for a in candidates('wikimedia',{'query':{'pages':{'5':first,'6':second}}})],['wikimedia:6','wikimedia:5'])

    def test_license_versions_preserved_and_unsupported_rejected(self):
        self.assertEqual(commons_license("CC BY-SA 4.0"), "CC BY-SA")
        self.assertEqual(commons_license("CC BY 3.0"), "CC BY")
        self.assertEqual(commons_license("CC0 1.0"), "CC0")
        for unsupported in ["CC BY-NC 4.0", "CC BY-ND", "unknown"]:
            with self.assertRaises(ValueError):
                commons_license(unsupported)
        parsed = candidates("wikimedia", {"query": {"pages": {"4": WIKI}}})
        self.assertEqual(parsed[0]["license_original"], "CC BY-SA 4.0")
        self.assertEqual(parsed[0]["author"], "Controlled Author")

    def test_three_providers_keep_attribution_and_reject_illustrations(self):
        self.assertEqual(candidates("pixabay", {"hits": [PIX]})[0]["author"], PIX["user"])
        self.assertEqual(candidates("pexels", {"photos": [PEX]})[0]["provider_link"], "https://www.pexels.com")
        illustration = dict(PIX, type="illustration")
        self.assertEqual(candidates("pixabay", {"hits": [illustration]}), [])
        incompatible = copy.deepcopy(WIKI)
        incompatible["imageinfo"][0]["extmetadata"]["LicenseShortName"]["value"] = "CC BY-NC 4.0"
        self.assertEqual(candidates("wikimedia", {"query": {"pages": {"4": incompatible}}}), [])

    def test_untrusted_provider_urls_rejected_before_network(self):
        for bad in ["http://cdn.pixabay.com/a.jpg", "https://cdn.pixabay.com.evil.invalid/a.jpg",
                    "https://user:pass@cdn.pixabay.com/a.jpg", "https://127.0.0.1/a.jpg"]:
            with self.assertRaises(ValueError):
                media_url("pixabay", bad)
        self.assertEqual(media_url('wikimedia','https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a.jpg'),
                         'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a.jpg')
        with self.assertRaises(ValueError):media_url('wikimedia','https://thumb.wikimedia.org.evil.invalid/a.jpg')

    def test_cross_request_cache_identity_contains_settings_without_credentials(self):
        cache, http = Cache(), HTTP()
        def search(request_id, orientation):
            ledger = FakeLedger()
            return PhotoSearch(BudgetedCalls(ledger, request_id), cache, http,
                lambda provider: "controlled-secret", "project-a").search("pixabay", "controlled", orientation)
        first = search("a", "portrait")
        self.assertEqual(first, search("b", "portrait"))
        self.assertEqual(len(http.searches), 1)
        self.assertNotIn("controlled-secret", json.dumps(first))
        search("c", "landscape")
        self.assertEqual(len(http.searches), 2)

    def test_selected_file_downloads_once_and_tampering_blocks_reuse(self):
        with tempfile.TemporaryDirectory() as temp:
            http = HTTP()
            candidate = candidates("pixabay", {"hits": [PIX]})[0]
            downloader = PhotoDownload(temp, "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                BudgetedCalls(FakeLedger(), "test"), http,
                probe=lambda file: {"width": 1080, "height": 1920})
            result = downloader.download(candidate)
            self.assertEqual(result, downloader.download(candidate))
            self.assertEqual(len(http.downloads), 1)
            file = Path(temp) / result["path"]
            self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(), result["sha256"])
            file.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "changed"):
                downloader.download(candidate)
            self.assertEqual(len(http.downloads), 1)

    def test_http429_preserves_rate_headers_without_credential_url_or_body(self):
        class Opener:
            def open(self, request, timeout):
                raise urllib.error.HTTPError(request.full_url, 429, "secret-body", {
                    "X-RateLimit-Remaining": "0", "Retry-After": "60", "Set-Cookie": "secret"}, io.BytesIO(b"secret-body"))
        http = JSONHTTP()
        http.opener = Opener()
        with self.assertRaises(HTTPFailure) as observed:
            http.request_receipt("GET", "https://pixabay.com/api/?key=controlled-secret")
        error = observed.exception
        self.assertEqual(error.receipt["headers"], {"x-ratelimit-remaining": "0", "retry-after": "60"})
        self.assertNotIn("secret", str(error))
        self.assertNotIn("secret", json.dumps(error.receipt))
