"""One search, at most six page attempts, at most three fetched evidence texts."""
import hashlib
import http.client
import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urlencode, urlsplit, urlunsplit
from .http import HTTPFailure, response_headers
from .preflight import digest
from .preparation import ResourceUnavailable


class ArticleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = []
        self.parts = []

    def handle_starttag(self, tag, attributes):
        if tag in {"script", "style", "nav", "footer", "header", "aside", "noscript", "svg"}:
            self.hidden.append(tag)
        elif tag in {"p", "div", "br", "li", "h1", "h2", "h3", "section", "article"} and not self.hidden:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
        elif tag in {"p", "div", "li", "section", "article"}:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)

    def text(self):
        return re.sub(r"\s+", " ", "".join(self.parts)).strip()[:80000]


def public_address(url, resolver=socket.getaddrinfo):
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("invalid public source URL")
    port = 443 if parsed.scheme == "https" else 80
    if parsed.port not in (None, port) or len(url) > 2000:
        raise ValueError("unexpected public source port/length")
    addresses = resolver(parsed.hostname, port, type=socket.SOCK_STREAM)
    ips = [item[4][0] for item in addresses]
    if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
        raise ValueError("research source resolves to a non-public address")
    return parsed, ips[0], port


class PublicPage:
    def fetch(self, url):
        # This is a bounded, read-only public GET. An unavailable page can
        # be skipped without retrying it or accepting partial source text.
        # Paid/mutating calls retain their strict unknown-result semantics.
        try:
            return self._fetch(url)
        except HTTPFailure as error:
            if error.receipt['status'] != 429:
                raise
            return {'usable': False, **error.receipt, 'reason': 'source rate limited'}
        except (TimeoutError, OSError, http.client.HTTPException) as error:
            return {"usable": False, "reason": "source transport failure",
                    "error_type": type(error).__name__}

    def _fetch(self, url):
        parsed, ip, port = public_address(url)
        klass = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        connection = klass(parsed.hostname, port=port, timeout=20)
        # Pin the inspected address while HTTPS keeps the original hostname for TLS.
        connection._create_connection = lambda address, timeout, source: socket.create_connection((ip, port), timeout, source)
        try:
            path = urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
            connection.request("GET", path, headers={"User-Agent": "ContentFactoryV3/1.0",
                "Accept": "text/html,text/plain", "Accept-Encoding": "identity"})
            response = connection.getresponse()
            headers = response_headers(response.headers)
            if response.status >= 400:
                raise HTTPFailure(response.status, response.headers)
            if response.status != 200:
                return {"usable": False, "status": response.status, "headers": headers, "reason": "redirect or non-200"}
            content_type = headers.get("content-type", "").lower()
            if not content_type.startswith(("text/html", "text/plain", "application/xhtml+xml")):
                return {"usable": False, "status": response.status, "headers": headers, "reason": "unsupported source content"}
            raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                return {"usable": False, "status": response.status, "headers": headers, "reason": "source byte budget"}
            match = re.search(r"charset=['\"]?([a-zA-Z0-9_-]+)", content_type)
            try:
                decoded = raw.decode(match.group(1) if match else "utf-8", errors="replace")
            except LookupError:
                decoded = raw.decode("utf-8", errors="replace")
            if content_type.startswith("text/plain"):
                text = re.sub(r"\s+", " ", decoded).strip()[:80000]
            else:
                parser = ArticleText()
                parser.feed(decoded)
                text = parser.text()
            return {"usable": len(text) >= 100, "status": response.status, "headers": headers,
                    "body_sha256": hashlib.sha256(raw).hexdigest(), "text": text,
                    "sha256": hashlib.sha256(text.encode()).hexdigest()}
        finally:
            connection.close()


class Research:
    def __init__(self, calls, http, pages=None, endpoint="http://shorts-v2-searxng-1:8080/search"):
        if endpoint != "http://shorts-v2-searxng-1:8080/search":
            raise ValueError("only the project research service is allowed")
        self.calls, self.http = calls, http
        self.pages, self.endpoint = pages or PublicPage(), endpoint

    def fetch(self, topic, language):
        if language not in {"pl", "en", "ru", "uk"} or not isinstance(topic, str) or not 1 <= len(topic.strip()) <= 300:
            raise ValueError("invalid research input")
        params = {"q": topic.strip(), "language": language, "format": "json",
                  "categories": "general", "pageno": 1, "safesearch": 1}
        identity = {"endpoint": self.endpoint, "params": params}
        search = self.calls.run("research-search", "research_search", identity,
            lambda: self.http.request_receipt("GET", self.endpoint + "?" + urlencode(params), timeout=30))
        sources, attempted, hosts, limited_hosts = [], set(), {}, set()
        attempts = 0
        for entry in search["body"].get("results", [])[:20]:
            raw_url = entry.get("url")
            if not isinstance(raw_url, str):
                continue
            parsed = urlsplit(raw_url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
                continue
            url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))
            if url in attempted or parsed.hostname in limited_hosts or hosts.get(parsed.hostname, 0) >= 2:
                continue
            if attempts >= 6 or len(sources) >= 3:
                break
            attempted.add(url)
            hosts[parsed.hostname] = hosts.get(parsed.hostname, 0) + 1
            attempts += 1
            try:
                receipt = self.calls.run("source:" + digest(url), "source_fetch",
                    {"url": url, "byte_limit": 2 * 1024 * 1024, "text_limit": 80000},
                    lambda: self.pages.fetch(url), allow_unavailable=True)
            except ResourceUnavailable:
                continue
            if not receipt.get("usable"):
                if receipt.get("status") == 429:
                    limited_hosts.add(parsed.hostname)
                continue
            sources.append({"id": "source-" + str(len(sources) + 1), "url": url,
                "title": entry.get("title", ""), "text": receipt["text"], "sha256": receipt["sha256"],
                "fetch_provenance": {k: v for k, v in receipt.items() if k != "text"}})
        if not sources:
            raise ValueError("no usable fetched research sources within budget")
        return sources
