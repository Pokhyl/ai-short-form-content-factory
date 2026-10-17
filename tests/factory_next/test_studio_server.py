import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from factory_next import studio_server as ss
from factory_next.pipeline import Pipeline

REV="da6472ecb52ca6add6b616015d06b1ace56c7740"


class FakeRuntime:
    def __init__(self,*args):self.calls=0


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        patcher=patch.object(ss,"Runtime",FakeRuntime)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.app=ss.Studio(self.root,{},REV)
        self.app.enqueue=lambda job:None

    def test_create_and_retrieve_custom_topic(self):
        topic="Jak powstają bursztyny nad morzem?"
        with patch.object(ss,"register_next",return_value={"created":True}) as registry:
            result=self.app.create({"topic":topic,"language":"pl","seconds":15})
        self.assertEqual(result["status"],"queued")
        registry.assert_called_once()
        rows=self.app.all_jobs()
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["request"]["topic"],topic)
        self.assertEqual(rows[0]["status"],"ready")
        detail=self.app.detail(result["id"])
        self.assertEqual(detail["next_stage"],"research")
        self.assertFalse(detail["machine_pass"])
        self.assertIsNone(detail["video_url"])
        self.assertEqual(len(list((self.root/"factory-next-states").glob("*/state.json"))),1)

    def test_rejects_invalid_submission_before_quota(self):
        for payload in [
            {"topic":"", "language":"pl","seconds":15},
            {"topic":"valid","language":"xxx","seconds":15},
            {"topic":"valid","language":"pl","seconds":"15"},
            {"topic":"valid","language":"pl","seconds":15,"force":True},
        ]:
            with self.assertRaises(ValueError):
                self.app.create(payload)
        self.assertEqual(list(self.app.entries()),[])

    def test_limits_studio_jobs_per_day(self):
        with patch.object(ss,"register_next",return_value={"created":True}):
            self.app.create({"topic":"one","language":"pl","seconds":15})
            self.app.create({"topic":"two","language":"en","seconds":30})
            with self.assertRaisesRegex(OverflowError,"already in progress"):
                self.app.create({"topic":"three","language":"uk","seconds":60})

    def test_render_video_cannot_be_served_without_pass(self):
        with patch.object(ss,"register_next",return_value={"created":True}):
            new=self.app.create({"topic":"Custom","language":"ru","seconds":45})
        with self.assertRaisesRegex(ValueError,"not passed"):
            self.app.video(new["id"])

    def test_provider_wait_does_not_resume_early(self):
        with patch.object(ss,"register_next",return_value={"created":True}):
            new=self.app.create({"topic":"Custom","language":"pl","seconds":15})
        p=Pipeline(self.root/"factory-next-states",None,REV)
        state=p.snapshot(new["id"])
        state["status"]="provider_wait"
        state["provider_wait_receipt"]={"stage":"research","protocol":"budgeted-explicit-503",
                                        "retry_at":"2999-01-01T00:00:00+00:00"}
        p.save(p.directory(new["id"]),state)
        class Dummy:
            called=False
            def snapshot(self,job):return p.snapshot(job)
            def step(self,job):
                self.called=True
                raise AssertionError("premature provider send")
        dummy=Dummy()
        with patch.object(self.app,"pipeline",return_value=dummy):
            self.app._advance(new["id"])
        self.assertFalse(dummy.called)


if __name__=="__main__":
    unittest.main()
