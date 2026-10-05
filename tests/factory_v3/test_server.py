"""Owner HTTP boundaries, bounded admission and actual-byte review identity."""
import hashlib
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
from http.server import ThreadingHTTPServer
from factory_v3.server import Application, Sessions, byte_range, handler

OWNER = "controlled-owner-" + "x"*40
ORIGIN = "https://publisher.hodor.com.pl"
JOB = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


class Ledger:
    def __init__(self, state):
        self.state = state
        self.saved = None

    def snapshot(self, job_id):
        if job_id != JOB:
            raise KeyError()
        return self.state

    def _call(self, sql, parameters):
        if sql.startswith("INSERT"):
            if self.saved is None:
                self.saved = {"video_sha256": parameters[1], "decision": parameters[2], "comment": parameters[3], "created_at":"controlled"}
            return parameters[0]
        if "human_reviews" in sql:
            return self.saved
        return []


class Runtime:
    def __init__(self, root):
        self.settings = {"owner_token":OWNER}
        self.root = root
        self.revision = "a"*40
        self.created = set()
        self.ledger = Ledger({"status":"qa_pass","outputs":{"render":{},"qa":{}}})

    def create(self, request_id, topic, language, seconds):
        if language not in {"pl","en","ru","uk"} or seconds not in {15,30,45,60} or not topic:
            raise ValueError()
        created = request_id not in self.created
        self.created.add(request_id)
        return {"id":request_id,"created":created,"status":"preparing"}

    def status(self, request_id):
        return {"id":request_id,"request":{"topic":"Controlled","language":"pl","seconds":15},
                "status":self.ledger.state["status"],"source_revision":self.revision,
                "machine_pass":self.ledger.state["status"]=="qa_pass","human_pass":False}

    def run(self, request_id):
        raise AssertionError("controlled pool must not call provider runtime")


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.runtime = Runtime(self.root)
        self.app = Application(self.runtime, ORIGIN)
        self.app.pool.shutdown()
        self.app.pool = Mock()

    def tearDown(self):
        self.temp.cleanup()

    def request(self, **extra):
        return {"request_id":JOB,"topic":"Controlled","language":"pl","seconds":15,**extra}

    def video(self):
        folder = self.root/"renders"/JOB
        folder.mkdir(parents=True)
        file = folder/"final.mp4"
        file.write_bytes(b"controlled MP4 bytes, not media acceptance")
        sha = hashlib.sha256(file.read_bytes()).hexdigest()
        self.runtime.ledger.state["outputs"] = {"render":{"sha256":sha},"qa":{"sha256":sha}}
        return file, sha

    def test_session_signature_age_and_owner_key(self):
        sessions = Sessions(OWNER)
        with patch("factory_v3.server.time.time",return_value=100000):
            token = sessions.issue()
            self.assertTrue(sessions.valid(token))
            self.assertFalse(sessions.valid(token[:-1] + ("0" if token[-1] != "0" else "1")))
            self.assertFalse(Sessions("different-owner-"+"z"*40).valid(token))
        with patch("factory_v3.server.time.time",return_value=150000):
            self.assertFalse(sessions.valid(token))

    def test_video_byte_ranges_and_invalid_requests(self):
        self.assertEqual(byte_range(None,100),(0,99,False))
        self.assertEqual(byte_range("bytes=10-19",100),(10,19,True))
        self.assertEqual(byte_range("bytes=-20",100),(80,99,True))
        self.assertEqual(byte_range("bytes=90-",100),(90,99,True))
        for value in ["bytes=100-","bytes=0-1,3-4","bytes=-0","bytes=20-10","bytes=-"]:
            with self.assertRaises(ValueError):
                byte_range(value,100)

    def test_identical_request_does_not_enqueue_twice(self):
        self.assertTrue(self.app.submit(self.request())["created"])
        self.assertFalse(self.app.submit(self.request())["created"])
        self.assertEqual(self.app.pool.submit.call_count,1)

    def test_queue_bound_and_untrusted_fields(self):
        import uuid
        for _ in range(5):
            self.app.submit(self.request(request_id=str(uuid.uuid4())))
        with self.assertRaises(OverflowError):
            self.app.submit(self.request())
        with self.assertRaises(ValueError):
            self.app.submit(self.request(plan={"forged":True}))
        with self.assertRaises(ValueError):
            self.app.submit(self.request(seconds=True))

    def test_only_machine_passed_identical_mp4_is_served(self):
        file, sha = self.video()
        self.assertEqual(self.app.video(JOB),(file,"video/mp4"))
        self.runtime.ledger.state["status"] = "render_ready"
        with self.assertRaises(ValueError):
            self.app.video(JOB)
        self.runtime.ledger.state["status"] = "qa_pass"
        file.write_bytes(b"replacement bytes")
        with self.assertRaises(ValueError):
            self.app.video(JOB)

    def test_review_is_explicit_sha_bound_and_immutable(self):
        file, sha = self.video()
        data = {"decision":"accepted","video_sha256":sha,"comment":"Controlled explicit owner decision"}
        self.assertIsNone(self.app.review(JOB))
        with self.assertRaises(ValueError):
            self.app.record_review(JOB,{**data,"video_sha256":"b"*64})
        self.assertIsNone(self.app.review(JOB))
        self.assertEqual(self.app.record_review(JOB,data)["decision"],"accepted")
        self.assertEqual(self.app.record_review(JOB,data)["video_sha256"],sha)
        with self.assertRaises(ValueError):
            self.app.record_review(JOB,{**data,"decision":"rejected"})
        file.write_bytes(b"changed final bytes")
        with self.assertRaises(ValueError):
            self.app.record_review(JOB,data)

    def test_human_pass_display_requires_same_actual_video(self):
        _, sha = self.video()
        self.runtime.ledger.state["frozen"] = {"payload":{"script":"Controlled", "assets":[],
            "selection":{}, "scenes":[]}}
        self.app.record_review(JOB,{"decision":"accepted","video_sha256":sha,"comment":""})
        self.assertTrue(self.app.detail(JOB)["human_pass"])
        self.runtime.ledger.saved["video_sha256"] = "b"*64
        self.assertFalse(self.app.detail(JOB)["human_pass"])

    def test_http_authentication_origin_and_idempotent_intake(self):
        server = ThreadingHTTPServer(("127.0.0.1",0),handler(self.app))
        thread = threading.Thread(target=lambda:server.serve_forever(poll_interval=.05),daemon=True)
        thread.start()
        def send(method,path,data=None,headers=None):
            connection=http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=3)
            try:
                body=json.dumps(data) if data is not None else None
                connection.request(method,"/factory-v3"+path,body,headers or {})
                response=connection.getresponse()
                raw=response.read()
                return response.status,dict(response.getheaders()),json.loads(raw)
            finally:
                connection.close()
        try:
            code,_,_=send("GET","/api/requests")
            self.assertEqual(code,401)
            code,_,_=send("POST","/api/session",{"token":OWNER},{"Content-Type":"application/json","Origin":"https://other.invalid"})
            self.assertEqual(code,403)
            code,headers,_=send("POST","/api/session",{"token":OWNER},{"Content-Type":"application/json","Origin":ORIGIN})
            self.assertEqual(code,200)
            self.assertIn("HttpOnly",headers["Set-Cookie"])
            self.assertIn("Secure",headers["Set-Cookie"])
            auth={"Content-Type":"application/json","Origin":ORIGIN,"Cookie":headers["Set-Cookie"].split(";")[0]}
            self.assertEqual(send("POST","/api/requests",self.request(),auth)[0],202)
            self.assertEqual(send("POST","/api/requests",self.request(),auth)[0],200)
            self.assertEqual(self.app.pool.submit.call_count,1)
            self.assertEqual(send("GET","/api/requests",headers={"Cookie":auth["Cookie"]})[0],200)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_unsafe_public_origin_rejected(self):
        with self.assertRaises(ValueError):
            Application(self.runtime,"http://publisher.hodor.com.pl")
