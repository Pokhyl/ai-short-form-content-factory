import base64
import copy
import hashlib
import tempfile
import unittest
import uuid
from pathlib import Path
from factory_v3.worker_adapters import GoogleVoice, WorkerAdapters, identity


class HTTPDouble:
    def __init__(self):
        self.calls = []
        self.duration = 15000
        self.replace_hash = False

    def request(self, method, url, body=None, headers=None, timeout=30):
        self.calls.append((method,url,body,headers))
        if url.startswith("https://texttospeech.googleapis.com"):
            return {"audioContent":base64.b64encode(b"controlled test audio; not real TTS").decode()}
        if "/voiceovers/" in url:
            raw=base64.b64decode(body["audio_base64"])
            return {"status":"ready","sha256":"bad" if self.replace_hash else hashlib.sha256(raw).hexdigest(),
                    "duration_ms":self.duration}
        if "/alignments/" in url:
            return {"status":"ready","audio_sha256":body["audio_sha256"],
                    "audio_duration_ms":body["audio_duration_ms"],"global_coverage":1,
                    "scene_timings":[{"scene_uuid":s["scene_uuid"],"scene_key":s["scene_key"],
                      "start_ms":i*3000+100,"end_ms":i*3000+2800,"coverage":1}
                      for i,s in enumerate(body["scenes"])]}
        if "/renders/" in url:
            return {"status":"ready","input_audio_sha256":body["input_audio_sha256"],
                    "qa_passed":True,"sha256":"controlled-render"}
        raise AssertionError(url)


class WorkerAdapterTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.root=Path(self.directory.name)
        self.job=str(uuid.uuid4())
        self.http=HTTPDouble()
        self.payload={"language":"pl","seconds":15,"script":"Controlled narration.",
                      "scenes":[],"assets":[],"selection":{}}
        for i in range(5):
            path=self.root/(str(i)+".jpg")
            path.write_bytes(("controlled image "+str(i)).encode())
            sha=hashlib.sha256(path.read_bytes()).hexdigest()
            asset={"id":str(i),"path":path.name,"sha256":sha,"author":"test",
                   "source_url":"https://example.invalid/test","license":"CC0",
                   "license_url":"https://example.invalid/license"}
            scene={"id":"s"+str(i),"narration":"Controlled scene."}
            self.payload["scenes"].append(scene)
            self.payload["assets"].append(asset)
            self.payload["selection"][scene["id"]]=asset["id"]
        self.accounts=0
        def account():
            self.accounts+=1
        self.account=account
        self.adapters=WorkerAdapters(self.root,GoogleVoice(lambda:"controlled token",self.http),
          "http://localhost:3001",
          lambda *args:{"passed":True,"sha256":"controlled-render"},
          http=self.http,probe=lambda path:{"width":1000,"height":800})

    def tearDown(self):
        self.directory.cleanup()

    def test_one_tts_correct_voice_exact_staged_bytes_and_native_render_contract(self):
        voice=self.adapters.voice(self.job,self.payload,{},self.account)
        calls=[c for c in self.http.calls if c[1].startswith("https://texttospeech")]
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][2]["voice"]["name"],"pl-PL-Chirp3-HD-Enceladus")
        self.assertEqual(self.accounts,1)
        for scene in self.payload["scenes"]:
            staged=voice["staged_photos"][scene["id"]]
            self.assertEqual(hashlib.sha256(Path(staged["path"]).read_bytes()).hexdigest(),staged["asset_sha256"])
        outputs={"voice":voice}
        outputs["align"]=self.adapters.align(self.job,self.payload,outputs)
        outputs["render"]=self.adapters.render(self.job,self.payload,outputs)
        render_body=self.http.calls[-1][2]
        scenes=render_body["scenes"]
        self.assertEqual(scenes[0]["segment_start_ms"],0)
        self.assertEqual(scenes[-1]["segment_end_ms"],15000)
        self.assertTrue(all(a["segment_end_ms"]==b["segment_start_ms"] for a,b in zip(scenes,scenes[1:])))
        self.assertTrue(all(s["segment_start_ms"]<=s["speech_start_ms"]<s["speech_end_ms"]<=s["segment_end_ms"] for s in scenes))
        self.assertFalse(self.adapters.qa(self.job,self.payload,outputs)["human_pass"])

    def test_wrong_duration_makes_one_call_and_never_resynthesizes(self):
        self.http.duration=12000
        with self.assertRaisesRegex(ValueError,"no re-synthesis"):
            self.adapters.voice(self.job,self.payload,{},self.account)
        self.assertEqual(len([c for c in self.http.calls if c[1].startswith("https://texttospeech")]),1)

    def test_storage_substitution_rejected(self):
        self.http.replace_hash=True
        with self.assertRaisesRegex(ValueError,"differs"):
            self.adapters.voice(self.job,self.payload,{},self.account)

    def test_local_density_failure_makes_no_http_or_accounting_call(self):
        self.payload["scenes"].pop()
        with self.assertRaisesRegex(ValueError,"density"):
            self.adapters.voice(self.job,self.payload,{},self.account)
        self.assertEqual(self.http.calls,[])
        self.assertEqual(self.accounts,0)

    def test_closing_filler_blocks_before_send(self):
        self.payload["script"]="Controlled narration. Koniec."
        with self.assertRaisesRegex(ValueError,"filler"):
            self.adapters.voice(self.job,self.payload,{},self.account)
        self.assertEqual(self.http.calls,[])
