"""Safe machine-readable terminal diagnoses for arbitrary job topics."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from factory_next.pipeline import Pipeline, classify_stage_failure, fingerprint
from factory_next import studio_server


class BrokenResearch:
    def research(self, context):
        raise ValueError("research preflight failed after 2 revisions: secret source text")

class CredentialsInError:
    def research(self, context):
        raise ValueError("opaque third-party response bearer TOP_SECRET_DO_NOT_LEAK")


class SafeFailureDiagnostics(unittest.TestCase):
    def test_generic_semantic_rejection_has_persisted_category_not_source_quote(self):
        with tempfile.TemporaryDirectory() as directory:
            pipeline=Pipeline(directory, BrokenResearch(), "a"*40)
            job=str(uuid4())
            pipeline.create(job, "Any topic", "pl", 30)
            with self.assertRaises(ValueError):
                pipeline.step(job)
            state=pipeline.snapshot(job)
            self.assertEqual(state["status"], "needs_attention")
            self.assertEqual(state["error_type"], "ValueError")
            self.assertEqual(state["failure_code"], "RESEARCH_FACTS_REJECTED")
            self.assertNotIn("secret", Path(directory,job,"state.json").read_text())
            with self.assertRaises(Exception):
                pipeline.step(job)

    def test_untrusted_message_never_becomes_a_public_diagnostic(self):
        with tempfile.TemporaryDirectory() as directory:
            pipeline=Pipeline(directory, CredentialsInError(), "a"*40)
            job=str(uuid4())
            pipeline.create(job,"Unrelated topic","uk",60)
            with self.assertRaises(ValueError):
                pipeline.step(job)
            state=pipeline.snapshot(job)
            self.assertEqual(state["failure_code"], "STAGE_VALIDATION_FAILED")
            self.assertNotIn("TOP_SECRET",Path(directory,job,"state.json").read_text())

    def test_definite_http_rejection_differs_from_uncertain_transport(self):
        from factory_v3.http import HTTPFailure
        self.assertEqual(classify_stage_failure("research",HTTPFailure(403,{})),
                         "EXTERNAL_HTTP_FAILURE")
        self.assertEqual(classify_stage_failure("research",TimeoutError("unknown")),
                         "EXTERNAL_OPERATION_UNCERTAIN")

    def test_http_failure_receipt_persists_only_safe_diagnostics(self):
        from factory_v3.http import HTTPFailure
        class BrokenVoice:
            def voice(self,context):
                error=HTTPFailure(502,{"Authorization":"secret"})
                error.receipt.update(error_status="UNAVAILABLE",error_reason="UPSTREAM_TIMEOUT",
                    gateway_execution_id="12345",error_message="secret response")
                raise error
        with tempfile.TemporaryDirectory() as directory:
            pipeline=Pipeline(directory,BrokenVoice(),"a"*40)
            job=str(uuid4())
            pipeline.create(job,"Controlled voice failure","ru",30)
            state=pipeline.snapshot(job)
            state.update(next_stage="voice",outputs={"research":{},"materials":{},"story":{}},
                         receipts={"research":fingerprint({}),
                                   "materials":fingerprint({}),
                                   "story":fingerprint({})})
            pipeline.save(pipeline.directory(job),state)
            with self.assertRaises(Exception):
                pipeline.step(job)
            saved=pipeline.snapshot(job)
            self.assertEqual(saved["failure_details"],{
                "http_status":502,"error_status":"UNAVAILABLE",
                "error_reason":"UPSTREAM_TIMEOUT","gateway_execution_id":"12345"})
            self.assertNotIn("secret",Path(directory,job,"state.json").read_text())

    def test_failure_categories_do_not_depend_on_the_topic(self):
        for stage in ("research","materials","story","voice","render","audit"):
            with self.subTest(stage=stage):
                self.assertEqual(
                    classify_stage_failure(stage,ValueError("model response has invalid JSON type")),
                    "MODEL_RESPONSE_INVALID"
                )
                self.assertEqual(
                    classify_stage_failure(stage,RuntimeError("token ABC")),
                    None
                )

    def test_studio_returns_only_whitelisted_codes_from_durable_checkpoint(self):
        class FakeRuntime:
            def __init__(self,*args):
                pass
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(studio_server,"Runtime",FakeRuntime):
                app=studio_server.Studio(directory,{},"a"*40)
                app.enqueue=lambda job:None
                with patch.object(studio_server,"register_next",return_value={"created":True}):
                    job=app.create({"topic":"Any random topic","language":"en","seconds":15})["id"]
                pipeline=app.pipeline(job)
                state=pipeline.snapshot(job)
                state.update(status="needs_attention",error_type="ValueError",
                             failure_code="MODEL_RESPONSE_INVALID")
                pipeline.save(pipeline.directory(job),state)
                self.assertEqual(app.detail(job)["failure_reason"],"MODEL_RESPONSE_INVALID")
                state["failure_details"]={"http_status":502,"error_status":"UNAVAILABLE",
                    "gateway_execution_id":"12345","error_message":"SECRET"}
                pipeline.save(pipeline.directory(job),state)
                self.assertEqual(app.detail(job)["failure_details"],{
                    "http_status":502,"error_status":"UNAVAILABLE","gateway_execution_id":"12345"})
                state["failure_code"]="private token in raw error"
                pipeline.save(pipeline.directory(job),state)
                self.assertIsNone(app.detail(job)["failure_reason"])


if __name__=="__main__":
    unittest.main()
