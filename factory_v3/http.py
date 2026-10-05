"""Bounded HTTP without retries, redirects, or credential-bearing error output."""
import json
import urllib.error
import urllib.request


SAFE_RESPONSE_HEADERS = {"date", "cache-control", "retry-after", "content-type",
                         "x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset"}


def response_headers(headers):
    return {k.lower(): v for k, v in headers.items() if k.lower() in SAFE_RESPONSE_HEADERS}


class HTTPFailure(RuntimeError):
    def __init__(self, code, headers):
        self.receipt = {"status": code, "headers": response_headers(headers)}
        super().__init__("HTTP request rejected: " + str(code))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        raise ValueError("unexpected HTTP redirect")


class JSONHTTP:
    def __init__(self):
        self.opener = urllib.request.build_opener(NoRedirect())

    def _raw(self, method, url, body, headers, timeout, limit):
        encoded = None if body is None else json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
        request = urllib.request.Request(url, data=encoded, method=method,
            headers={"Content-Type": "application/json", "User-Agent": "ContentFactoryV3/1.0",
                     **(headers or {})})
        try:
            with self.opener.open(request, timeout=timeout) as response:
                raw = response.read(limit + 1)
                if len(raw) > limit:
                    raise ValueError("HTTP response exceeds byte budget")
                return {"body": raw, "status": response.status,
                        "headers": response_headers(response.headers)}
        except urllib.error.HTTPError as error:
            receipt = HTTPFailure(error.code, error.headers)
            error.close()
            raise receipt from None
        except urllib.error.URLError:
            raise RuntimeError("HTTP transport failed; result requires reconciliation") from None

    def request(self, method, url, body=None, headers=None, timeout=30):
        return self.request_receipt(method, url, body, headers, timeout)["body"]

    def request_receipt(self, method, url, body=None, headers=None, timeout=30):
        receipt = self._raw(method, url, body, headers, timeout, 20 * 1024 * 1024)
        receipt["body"] = json.loads(receipt["body"])
        return receipt

    def binary_receipt(self, url, *, timeout=60, limit=8 * 1024 * 1024):
        return self._raw("GET", url, None, {"Accept": "image/jpeg,image/png,image/webp"},
                         timeout, limit)
