"""Native n8n credential boundary, single upstream HTTP node, no caller credentials."""
from urllib.parse import urlsplit, parse_qsl
from .http import JSONHTTP, HTTPFailure


GATEWAY = "http://ai-short-form-n8n:5678/webhook/factory-v3-internal-provider"
MODEL = "gemini-3.5-flash-lite"


class CredentialHTTP:
    def __init__(self, token, http=None, gateway=GATEWAY):
        if gateway != GATEWAY or not isinstance(token, str) or len(token) < 32:
            raise ValueError("trusted project credential gateway required")
        self.token, self.http, self.gateway = token, http or JSONHTTP(), gateway

    def _send(self, provider, request, timeout):
        response = self.http.request("POST", self.gateway, {"provider": provider, "request": request},
                                     {"X-Factory-V3-Broker": self.token}, timeout=timeout)
        if not isinstance(response, dict) or not isinstance(response.get("status"), int):
            raise ValueError("invalid credential gateway receipt")
        if response["status"] >= 400:
            error = HTTPFailure(response["status"], response.get("headers", {}))
            for key in ("error_status", "error_reason", "error_message", "gateway_execution_id"):
                if isinstance(response.get(key), str):
                    error.receipt[key] = response[key][:750]
            raise error
        if response["status"] != 200:
            raise ValueError("unexpected credential gateway status")
        return response

    def metadata(self, operation, body=None):
        if operation == "model":
            return self._send("gemini_info", {}, 30)
        if operation not in {"key_owner", "project", "billing"}:
            raise ValueError("unsupported read-only metadata operation")
        return self._send("google_metadata", {"operation": operation, "body": body}, 30)

    def request(self, method, url, body=None, headers=None, timeout=30):
        return self.request_receipt(method, url, body, headers, timeout)["body"]

    def request_receipt(self, method, url, body=None, headers=None, timeout=30):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
            raise ValueError("invalid credential endpoint")
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        if len({k for k,v in pairs}) != len(pairs):
            raise ValueError("duplicate provider query fields")
        query = {k: v for k,v in pairs if k != "key"}
        if parsed.hostname == "pixabay.com" and parsed.path == "/api/" and method == "GET":
            if "per_page" in query:
                query["per_page"] = int(query["per_page"])
            provider = "pixabay"
        elif parsed.hostname == "api.pexels.com" and parsed.path == "/v1/search" and method == "GET":
            if "per_page" in query:
                query["per_page"] = int(query["per_page"])
            provider = "pexels"
        elif parsed.hostname == "generativelanguage.googleapis.com" and parsed.path == "/v1beta/models/" + MODEL + ":generateContent" and method == "POST" and not query:
            provider = "gemini"
        elif parsed.hostname == "texttospeech.googleapis.com" and parsed.path == "/v1/text:synthesize" and method == "POST" and not query:
            provider = "google_tts"
        elif parsed.hostname == "commons.wikimedia.org" and parsed.path == "/w/api.php" and method == "GET":
            return self.http.request_receipt(method, url, body, headers, timeout)
        else:
            raise ValueError("provider endpoint is not allowlisted")
        return self._send(provider, {"query": query, "body": body}, timeout)
