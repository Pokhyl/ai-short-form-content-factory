"""Controlled gateway responses; no native workflow or provider calls."""
import json
import unittest
from factory_v3.credential_http import CredentialHTTP, GATEWAY, MODEL
from factory_v3.http import HTTPFailure


class HTTP:
    def __init__(self):
        self.calls = []
        self.status = 200
    def request(self, method, url, body, headers, timeout):
        self.calls.append((method,url,body,headers,timeout))
        return {"status":self.status,"headers":{"x-ratelimit-remaining":"0"},
                "body":{"controlled":True},"gateway_execution_id":"controlled"}


class CredentialHTTPTests(unittest.TestCase):
    def setUp(self):
        self.http = HTTP()
        self.transport = CredentialHTTP("controlled-broker-token-" + "x"*32, self.http)

    def test_virtual_pixabay_key_never_forwarded_to_native_request_body(self):
        receipt = self.transport.request_receipt("GET",
            "https://pixabay.com/api/?q=controlled&per_page=8&key=virtual-not-real")
        request = self.http.calls[0]
        self.assertEqual(request[1], GATEWAY)
        self.assertEqual(request[2]["provider"], "pixabay")
        self.assertEqual(request[2]["request"]["query"]["per_page"], 8)
        self.assertNotIn("virtual-not-real", json.dumps(request[2]))
        self.assertEqual(receipt["gateway_execution_id"], "controlled")

    def test_only_selected_model_endpoint_is_forwarded(self):
        self.transport.request_receipt("POST",
            "https://generativelanguage.googleapis.com/v1beta/models/"+MODEL+":generateContent", {})
        with self.assertRaises(ValueError):
            self.transport.request_receipt("POST",
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-paid:generateContent", {})
        self.assertEqual(len(self.http.calls), 1)

    def test_provider429_preserves_receipt_and_is_never_retried(self):
        self.http.status = 429
        with self.assertRaises(HTTPFailure) as caught:
            self.transport.request_receipt("POST","https://texttospeech.googleapis.com/v1/text:synthesize", {})
        self.assertEqual(caught.exception.receipt["headers"]["x-ratelimit-remaining"], "0")
        self.assertEqual(len(self.http.calls), 1)

    def test_untrusted_endpoint_and_duplicate_query_never_use_gateway(self):
        for url in ["https://api.pexels.com.evil.invalid/v1/search",
                    "http://api.pexels.com/v1/search",
                    "https://api.pexels.com/v1/search?query=a&query=b"]:
            with self.assertRaises(ValueError):
                self.transport.request_receipt("GET",url)
        self.assertEqual(self.http.calls, [])
