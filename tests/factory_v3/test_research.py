"""Controlled search/pages and DNS answers; no external network."""
import hashlib
import unittest
from factory_v3.http import HTTPFailure
from factory_v3.preparation import BudgetedCalls, ResourceUnavailable
from factory_v3.research import ArticleText, Research, PublicPage, public_address
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

    def test_timed_out_public_page_is_skipped_without_repeating_it(self):
        class HTTP:
            def request_receipt(self, *args, **kwargs):
                return {"body": {"results": [{"url": "https://source" + str(i) + ".invalid/page"}
                                             for i in range(10)]}}
        class Pages(PublicPage):
            def __init__(self): self.calls = []
            def _fetch(self, url):
                self.calls.append(url)
                if 'source0.' in url: raise TimeoutError('Saved Russian source timeout')
                text = 'Actual available source text. ' * 5
                return {'usable': True, 'status': 200, 'text': text,
                        'sha256': hashlib.sha256(text.encode()).hexdigest()}
        ledger = FakeLedger(); ledger.limit = 10
        pages = Pages()
        sources = Research(BudgetedCalls(ledger, 'test'), HTTP(), pages=pages).fetch('topic','ru')
        self.assertEqual(len(sources), 3)
        self.assertEqual(len(pages.calls), 4)
        self.assertEqual(len(set(pages.calls)), 4)
        self.assertFalse(ledger.terminal)

    def test_transport_fallback_does_not_bypass_security(self):
        from unittest.mock import patch
        page = PublicPage()
        for error in [ValueError('non-public address')]:
            with patch.object(page, '_fetch', side_effect=error):
                with self.assertRaises(type(error)):
                    page.fetch('https://example.invalid/page')

    def test_rate_limited_public_host_is_skipped_with_receipt_and_never_revisited(self):
        class HTTP:
            def request_receipt(self, *args, **kwargs):
                return {'body': {'results': [{'url': u} for u in [
                    'https://limited.invalid/a', 'https://limited.invalid/b',
                    'https://other.invalid/a', 'https://third.invalid/a',
                    'https://fourth.invalid/a']]}}
        class Pages(PublicPage):
            def __init__(self): self.urls = []
            def _fetch(self, url):
                self.urls.append(url)
                if 'limited.invalid' in url:
                    raise HTTPFailure(429, {'Retry-After': '60'})
                text = 'Available independent source. ' * 5
                return {'usable': True, 'text': text, 'sha256': hashlib.sha256(text.encode()).hexdigest()}
        ledger = FakeLedger(); ledger.limit = 10
        pages = Pages()
        research = Research(BudgetedCalls(ledger, 'test'), HTTP(), pages=pages)
        self.assertEqual(len(research.fetch('topic', 'en')), 3)
        self.assertEqual(pages.urls.count('https://limited.invalid/a'), 1)
        self.assertNotIn('https://limited.invalid/b', pages.urls)
        self.assertFalse(ledger.terminal)
        first = pages.fetch('https://limited.invalid/c')
        self.assertEqual(first['headers']['retry-after'], '60')
        self.assertFalse(first['usable'])
