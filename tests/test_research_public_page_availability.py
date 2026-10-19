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


if __name__ == "__main__":
    unittest.main()
