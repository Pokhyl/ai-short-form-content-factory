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
        return self.request_receipt(method, url, body, headers, timeout)["body"]

    def request_receipt(self, method, url, body=None, headers=None, timeout=30):
        encoded = None if body is None else json.dumps(body, ensure_ascii=False).encode()
        request = urllib.request.Request(url, data=encoded, method=method,
            headers={"Content-Type": "application/json", "User-Agent": "ContentFactoryV3/1.0",
                     **(headers or {})})
        try:
            with self.opener.open(request, timeout=timeout) as response:
                raw = response.read(20 * 1024 * 1024 + 1)
                if len(raw) > 20 * 1024 * 1024:
                    raise ValueError("HTTP response exceeds budget")
                allowed = {"date", "cache-control", "retry-after", "content-type",
                           "x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset"}
                metadata = {k.lower(): v for k,v in response.headers.items() if k.lower() in allowed}
                return {"body": json.loads(raw), "status": response.status, "headers": metadata}
        except urllib.error.HTTPError as error:
            raise RuntimeError("HTTP request rejected: " + str(error.code)) from None
