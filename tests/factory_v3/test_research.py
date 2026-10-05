"""Controlled search/pages and DNS answers; no external network."""
import hashlib
import unittest
from factory_v3.http import HTTPFailure
from factory_v3.preparation import BudgetedCalls, ResourceUnavailable
from factory_v3.research import ArticleText, Research, public_address
from test_preparation import FakeLedger


class ResearchTests(unittest.TestCase):
    def test_html_retains_article_and_excludes_navigation_scripts(self):
        parser = ArticleText()
        parser.feed("<nav>noise</nav><article><h1>Title</h1><p>Exact &amp; supported fact.</p></article><script>bad()</script>")
        self.assertEqual(parser.text(), "Title Exact & supported fact.")

    def test_private_mixed_addresses_and_credential_urls_rejected(self):
        def resolver(ips):
            return lambda *args, **kwargs: [(None, None, None, None, (ip, 443)) for ip in ips]
        for ips in [["127.0.0.1"], ["::1"], ["8.8.8.8", "10.0.0.1"]]:
            with self.assertRaisesRegex(ValueError, "non-public"):
                public_address("https://example.invalid/page", resolver(ips))
        parsed, address, port = public_address("https://example.invalid/page", resolver(["8.8.8.8"]))
        self.assertEqual((address, port), ("8.8.8.8", 443))
        with self.assertRaises(ValueError):
            public_address("https://user:pass@example.invalid/page", resolver(["8.8.8.8"]))

    def test_bounded_fetched_sources_replay_and_skip_definitive403(self):
        class HTTP:
            def request_receipt(self, *args, **kwargs):
                return {"body": {"results": [{"url": "https://source" + str(i) + ".invalid/page"}
                                             for i in range(10)]}}
        class Pages:
            def __init__(self):
                self.calls = []
            def fetch(self, url):
                self.calls.append(url)
                if "source0." in url:
                    raise HTTPFailure(403, {})
                text = "Controlled actual fetched text. " * 5
                return {"usable": True, "status": 200, "text": text,
                        "sha256": hashlib.sha256(text.encode()).hexdigest()}
        ledger = FakeLedger()
        ledger.limit = 10
        pages = Pages()
        research = Research(BudgetedCalls(ledger, "test"), HTTP(), pages=pages)
        first = research.fetch("controlled topic", "pl")
        self.assertEqual(len(first), 3)
        self.assertEqual(len(pages.calls), 4)
        self.assertEqual(first, research.fetch("controlled topic", "pl"))
        self.assertEqual(len(pages.calls), 4)

    def test_429_is_terminal_even_when_resource_rejection_allowed(self):
        ledger = FakeLedger()
        calls = BudgetedCalls(ledger, "test")
        def rejected():
            raise HTTPFailure(429, {"Retry-After": "60"})
        with self.assertRaises(HTTPFailure):
            calls.run("page", "source_fetch", {}, rejected, allow_unavailable=True)
        self.assertTrue(ledger.terminal)
