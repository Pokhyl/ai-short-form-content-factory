"""Bounded JSON HTTP with no retries or redirects; never expose credential bodies."""
import json
import urllib.error
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        raise ValueError("unexpected HTTP redirect")


class JSONHTTP:
    def __init__(self):
        self.opener = urllib.request.build_opener(NoRedirect())

    def request(self, method, url, body=None, headers=None, timeout=30):
        encoded = None if body is None else json.dumps(body, ensure_ascii=False).encode()
        request = urllib.request.Request(url, data=encoded, method=method,
            headers={"Content-Type": "application/json", "User-Agent": "ContentFactoryV3/1.0",
                     **(headers or {})})
        try:
            with self.opener.open(request, timeout=timeout) as response:
                raw = response.read(20 * 1024 * 1024 + 1)
                if len(raw) > 20 * 1024 * 1024:
                    raise ValueError("HTTP response exceeds budget")
                return json.loads(raw)
        except urllib.error.HTTPError as error:
            raise RuntimeError("HTTP request rejected: " + str(error.code)) from None
