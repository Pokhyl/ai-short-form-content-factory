"""Regression: anonymous source failures must not stop unrelated research."""
import unittest

from factory_v3.http import HTTPFailure
from factory_v3.research import PublicPage


class FakePage(PublicPage):
    def __init__(self, status):
        self.status = status

    def _fetch(self, url):
        if self.status == 200:
            return {"usable": True, "status": 200, "text": "published evidence"}
        raise HTTPFailure(self.status, {})


class PublicPageAvailabilityTests(unittest.TestCase):
    def test_inaccessible_sources_are_not_accepted_as_evidence(self):
        for status in (401, 403, 404, 410, 429):
            with self.subTest(status=status):
                result = FakePage(status).fetch("https://example.com/article")
                self.assertFalse(result["usable"])
                self.assertEqual(result["status"], status)
                self.assertNotIn("text", result)

    def test_transient_server_errors_are_not_silently_reclassified(self):
        with self.assertRaises(HTTPFailure):
            FakePage(500).fetch("https://example.com/article")

    def test_successful_source_is_preserved(self):
        result = FakePage(200).fetch("https://example.com/article")
        self.assertTrue(result["usable"])
        self.assertEqual(result["text"], "published evidence")

    def test_research_continues_to_next_source_after_401(self):
        from factory_v3.research import Research

        class Calls:
            def run(self, key, kind, public_request, invoke, **kwargs):
                return invoke()

        class Search:
            def request_receipt(self, method, url, timeout):
                return {"body": {"results": [
                    {"url": "https://restricted.example.com/article", "title": "Blocked"},
                    {"url": "https://public.example.com/article", "title": "Public"},
                ]}}

        class Pages:
            def __init__(self):
                self.attempted = []

            def fetch(self, url):
                self.attempted.append(url)
                if "restricted" in url:
                    return FakePage(401).fetch(url)
                return {"usable": True, "status": 200,
                        "text": "Public article with corroborated evidence. " * 5,
                        "sha256": "known-source-hash"}

        pages = Pages()
        result = Research(Calls(), Search(), pages=pages).fetch(
            "Generic documentary subject", "uk")
        self.assertEqual(len(pages.attempted), 2)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["url"], "https://public.example.com/article")
        self.assertEqual(result[0]["sha256"], "known-source-hash")


if __name__ == "__main__":
    unittest.main()
