"""Runtime boundaries with controlled metadata/ledger; no real providers."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from factory_v3.runtime import Runtime, load_settings
from test_preparation import FakeLedger


REQUEST_ID="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
REVISION="a"*40
SETTINGS={"database_url":"postgresql://controlled.invalid/test",
          "broker_token":"controlled-"+"x"*40, "credential_scope":"controlled",
          "gemini_free_tier_confirmed":True,
          "free_tier_proof":{"billing_enabled":False,"model":"gemini-3.5-flash-lite",
                             "project_id":"controlled-project","credential_sha256":"controlled"}}


class HTTP:
    def __init__(self):
        self.calls=[]
    def request(self, method, url, body, headers, timeout):
        self.calls.append(body)
        return {"status":200,"headers":{},"body":{"projectId":"controlled-project","billingEnabled":True}}
    def request_receipt(self,*args,**kwargs):
        raise AssertionError("research/provider called after billing rejection")


class Ledger(FakeLedger):
    def claim_run(self, request_id):
        return {"cached":False,"request":{"topic":"controlled","language":"pl","seconds":15}}


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.http=HTTP()
        self.runtime=Runtime(SETTINGS,self.root,REVISION,ledger=object(),http=self.http)
    def tearDown(self):
        self.temp.cleanup()

    def test_paid_project_rejected_before_research_model_or_voice(self):
        ledger=Ledger()
        self.runtime.preparations=ledger
        with self.assertRaisesRegex(ValueError,"unbilled"):
            self.runtime.producer(REQUEST_ID).prepare(REQUEST_ID)
        self.assertEqual(len(self.http.calls),1)
        self.assertEqual(self.http.calls[0]["provider"],"google_metadata")
        self.assertTrue(ledger.terminal)

    def test_missing_free_tier_confirmation_never_calls_gateway(self):
        runtime=Runtime({**SETTINGS,"gemini_free_tier_confirmed":False},
                        self.root,REVISION,ledger=object(),http=self.http)
        with self.assertRaisesRegex(ValueError,"free-only"):
            runtime.producer(REQUEST_ID)
        self.assertEqual(self.http.calls,[])

    def test_existing_request_is_read_only_and_cannot_change(self):
        self.runtime.preparations=Mock()
        self.runtime.preparations.snapshot.return_value={
            "request":{"topic":"controlled","language":"pl","seconds":15},
            "source_revision":REVISION,"status":"unknown"}
        result=self.runtime.create(REQUEST_ID,"controlled","pl",15)
        self.assertFalse(result["created"])
        self.runtime.preparations.create.assert_not_called()
        with self.assertRaisesRegex(ValueError,"changed"):
            self.runtime.create(REQUEST_ID,"different","pl",15)
        self.assertEqual(self.http.calls,[])

    def test_visual_mode_is_persisted_and_cannot_change_existing_request(self):
        self.runtime.preparations=Mock()
        self.runtime.preparations.snapshot.side_effect=KeyError()
        self.runtime.create(REQUEST_ID, 'controlled', 'pl', 30, visual_validation_mode='metadata')
        saved=self.runtime.preparations.create.call_args.args[1]
        self.assertEqual(saved['visual_validation_mode'], 'metadata')
        self.runtime.preparations.snapshot.side_effect=None
        self.runtime.preparations.snapshot.return_value={'request':saved, 'source_revision':REVISION, 'status':'failed'}
        self.assertFalse(self.runtime.create(REQUEST_ID, 'controlled', 'pl', 30, visual_validation_mode='metadata')['created'])
        for mode in ('gemini', 'other'):
            with self.assertRaises(ValueError):
                self.runtime.create(REQUEST_ID, 'controlled', 'pl', 30, visual_validation_mode=mode)
        self.assertEqual(self.http.calls, [])

    def test_existing_media_job_id_is_not_reused(self):
        self.runtime.preparations=Mock()
        self.runtime.preparations.snapshot.side_effect=KeyError()
        (self.root/"voiceovers"/REQUEST_ID).mkdir(parents=True)
        with self.assertRaisesRegex(ValueError,"not be reused"):
            self.runtime.create(REQUEST_ID,"controlled","pl",15)
        self.runtime.preparations.create.assert_not_called()

    def test_private_settings_and_exact_source_revision_required(self):
        file=self.root/"settings.json"
        file.write_text(json.dumps(SETTINGS))
        file.chmod(0o644)
        with self.assertRaises(ValueError):
            load_settings(file)
        file.chmod(0o600)
        self.assertEqual(load_settings(file),SETTINGS)
        with self.assertRaisesRegex(ValueError,"revision"):
            Runtime(SETTINGS,self.root,"unknown",ledger=object())
