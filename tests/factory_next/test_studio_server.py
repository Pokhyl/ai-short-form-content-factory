import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
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

    def test_failed_google_authorization_is_explained_without_exposing_receipts(self):
        from unittest.mock import Mock
        with patch.object(ss,"register_next",return_value={"created":True}):
            job=self.app.create({"topic":"Test","language":"uk","seconds":45})["id"]
        pipeline=self.app.pipeline(job)
        state=pipeline.snapshot(job)
        state.update(status="needs_attention",error_type="HTTPFailure")
        pipeline.save(pipeline.directory(job),state)
        ledger=Mock()
        ledger._call.return_value="GOOGLE_OAUTH_RECONNECT_REQUIRED"
        self.app.runtime.ledger=ledger
        detail=self.app.detail(job)
        self.assertEqual(detail["failure_reason"],"GOOGLE_OAUTH_RECONNECT_REQUIRED")
        self.assertNotIn("receipt",detail)
        self.assertEqual(ledger._call.call_args.args[1],(job,job))
        self.assertIn("RESOURCE_EXHAUSTED",ledger._call.call_args.args[0])
        ledger._call.side_effect=RuntimeError("database unavailable")
        self.assertIsNone(self.app.detail(job)["failure_reason"])

    def test_quota_exhaustion_is_reported_without_exposing_gateway_receipts(self):
        from unittest.mock import Mock
        with patch.object(ss,"register_next",return_value={"created":True}):
            job=self.app.create({"topic":"DNA molecule","language":"uk","seconds":45})["id"]
        pipeline=self.app.pipeline(job)
        state=pipeline.snapshot(job)
        state.update(status="needs_attention",error_type="HTTPFailure")
        pipeline.save(pipeline.directory(job),state)
        self.app.runtime.ledger=Mock()
        self.app.runtime.ledger._call.return_value="GEMINI_RATE_OR_QUOTA_EXHAUSTED"
        detail=self.app.detail(job)
        self.assertEqual(detail["failure_reason"],"GEMINI_RATE_OR_QUOTA_EXHAUSTED")
        self.assertNotIn("provider_receipt",detail)
        self.assertIsNone(detail["retry_at"])

    def test_scene_exposes_correct_scientific_visual_label_and_license(self):
        with patch.object(ss,"register_next",return_value={"created":True}):
            job=self.app.create({"topic":"DNA molecule","language":"uk","seconds":45})["id"]
        pipeline=self.app.pipeline(job)
        state=pipeline.snapshot(job)
        asset={"id":"wikimedia:120","source_url":"https://commons.wikimedia.org/wiki/File:DNA.png",
               "author":"Science author","license":"CC BY-SA",
               "license_url":"https://creativecommons.org/licenses/by-sa/4.0/"}
        state["outputs"]={
            "materials":{"assets":[asset],"photos":[{"id":asset["id"],
                "visual_kind":"scientific_illustration"}]},
            "story":{"scenes":[{"id":"beat-1","material_id":asset["id"],
                                "narration":"DNA contains complementary strands."}]},
        }
        pipeline.save(pipeline.directory(job),state)
        result=self.app.detail(job)
        self.assertEqual(result["scenes"][0]["visual_kind"],"scientific_illustration")
        self.assertEqual(result["scenes"][0]["license"],"CC BY-SA")
        self.assertEqual(result["scenes"][0]["author"],"Science author")
        self.assertEqual(result["scenes"][0]["license_url"],
                         "https://creativecommons.org/licenses/by-sa/4.0/")

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

    def test_busy_studio_queues_without_dispatch_and_bounds_waiting_count(self):
        admitted=[]
        self.app.enqueue=lambda job:admitted.append(job)
        with patch.object(ss,"register_next",return_value={"created":True}) as registry:
            first=self.app.create({"topic":"one","language":"pl","seconds":15})
            second=self.app.create({"topic":"two","language":"en","seconds":30})
            pending=[self.app.create({"topic":f"Queued {i}","language":"uk",
                                      "seconds":60}) for i in range(3)]
            with self.assertRaisesRegex(OverflowError,"waiting queue is full"):
                self.app.create({"topic":"Too many","language":"uk","seconds":60})
        self.assertEqual(registry.call_count,2)
        self.assertEqual(admitted,[first["id"],second["id"]])
        self.assertTrue(all(p["status"]=="queued_for_quota" for p in pending))
        self.assertTrue(all(self.app.detail(p["id"])["status"]=="queued_for_quota"
                            for p in pending))
        # Even a mistaken enqueue must not dispatch a delayed job.
        for p in pending:
            self.app.enqueue=ss.Studio.enqueue.__get__(self.app)
            self.app.enqueue(p["id"])
        self.assertTrue(all(p["id"] not in self.app.inflight for p in pending))

    def test_daily_quota_queues_and_automatically_admits_after_utc_reset(self):
        admitted=[]
        self.app.enqueue=lambda job:admitted.append(job)
        with patch.object(ss,"DAY_LIMIT",1), \
             patch.object(ss,"register_next",return_value={"created":True}) as registry:
            first=self.app.create({"topic":"DNA molecule","language":"uk","seconds":45})
            second=self.app.create({"topic":"Why leaves change colour",
                                    "language":"en","seconds":30})
            self.assertEqual(first["status"],"queued")
            self.assertEqual(second["status"],"queued_for_quota")
            self.assertEqual(admitted,[first["id"]])
            queued=self.app.detail(second["id"])
            self.assertEqual(queued["status"],"queued_for_quota")
            self.assertIsNone(queued["video_url"])
            due=datetime.fromisoformat(queued["eligible_after"])
            self.assertEqual((due.hour,due.minute),(0,0))
            self.assertGreater(due,datetime.now(timezone.utc))
            self.assertIsNone(self.app._admit_waiting(now=due-timedelta(seconds=1)))
            # Every database registration happens once, even for queued jobs.
            self.assertEqual(registry.call_count,1)
            admitted_id=self.app._admit_waiting(now=due)
            self.assertEqual(admitted_id,second["id"])
            self.assertEqual(self.app.detail(second["id"])["status"],"ready")
            self.assertIsNone(self.app._admit_waiting(now=due))
            self.assertEqual(registry.call_count,2)
            self.assertEqual(self.app.entries()[0]["admitted_at"],due.isoformat())

    def test_daily_queued_jobs_resume_oldest_first_without_resending_registration(self):
        with patch.object(ss,"DAY_LIMIT",1), \
             patch.object(ss,"register_next",return_value={"created":True}) as registry:
            first=self.app.create({"topic":"first","language":"pl","seconds":15})
            second=self.app.create({"topic":"second","language":"pl","seconds":15})
            third=self.app.create({"topic":"third","language":"pl","seconds":15})
            tomorrow=datetime.now(timezone.utc)+timedelta(days=1)
            tomorrow=tomorrow.replace(hour=0,minute=1,second=0,microsecond=0)
            next_day=tomorrow+timedelta(days=1)
            self.assertEqual(self.app._admit_waiting(now=tomorrow),second["id"])
            self.assertIsNone(self.app._admit_waiting(now=tomorrow))
            # An old still-ready job retains one active slot even after a
            # daily reset. Once it finishes, the FIFO queue may advance.
            prior=self.app.pipeline(first["id"])
            state=prior.snapshot(first["id"])
            state.update(status="needs_attention",error_type="FixtureStopped")
            prior.save(prior.directory(first["id"]),state)
            self.assertEqual(self.app._admit_waiting(now=next_day),third["id"])
            self.assertEqual(registry.call_count,3)
            self.assertEqual(self.app.detail(first["id"])["status"],"needs_attention")
            self.assertEqual(self.app.detail(second["id"])["status"],"ready")
            self.assertEqual(self.app.detail(third["id"])["status"],"ready")

    def test_busy_queue_advances_after_existing_job_finishes(self):
        admitted=[]
        self.app.enqueue=lambda job:admitted.append(job)
        with patch.object(ss,"register_next",return_value={"created":True}):
            first=self.app.create({"topic":"a","language":"pl","seconds":15})
            second=self.app.create({"topic":"b","language":"pl","seconds":15})
            queued=self.app.create({"topic":"c","language":"pl","seconds":15})
        self.assertEqual(queued["status"],"queued_for_quota")
        self.assertIsNone(self.app._admit_waiting())
        p=self.app.pipeline(first["id"])
        state=p.snapshot(first["id"])
        state["status"]="needs_attention"
        state["error_type"]="FixtureCompleted"
        p.save(p.directory(first["id"]),state)
        with patch.object(ss,"register_next",return_value={"created":True}): self.assertEqual(self.app._admit_waiting(),queued["id"])
        self.assertEqual(self.app.detail(queued["id"])["status"],"ready")

    def test_queued_job_registers_under_new_code_revision(self):
        with patch.object(ss,"DAY_LIMIT",1), \
             patch.object(ss,"register_next",return_value={"created":True}) as registry:
            self.app.create({"topic":"First","language":"pl","seconds":15})
            queued=self.app.create({"topic":"DNA molecule","language":"uk","seconds":45})
            self.assertEqual(registry.call_count,1)
            self.assertFalse(self.app.pipeline(queued["id"]).directory(queued["id"]).exists())
            self.app.revision="b"*40
            due=datetime.fromisoformat(self.app.detail(queued["id"])["eligible_after"])
            self.assertEqual(self.app._admit_waiting(now=due),queued["id"])
            self.assertEqual(registry.call_count,2)
            state=self.app.pipeline(queued["id"]).snapshot(queued["id"])
            self.assertEqual(state["revision"],"b"*40)

    def test_uncertain_queued_registration_is_not_automatically_retried(self):
        with patch.object(ss,"DAY_LIMIT",1), \
             patch.object(ss,"register_next",return_value={"created":True}):
            self.app.create({"topic":"First","language":"pl","seconds":15})
            queued=self.app.create({"topic":"DNA molecule","language":"uk","seconds":45})
        due=datetime.fromisoformat(self.app.detail(queued["id"])["eligible_after"])
        with patch.object(ss,"register_next",side_effect=RuntimeError("uncertain")) as registry:
            with self.assertRaisesRegex(RuntimeError,"uncertain"):
                self.app._admit_waiting(now=due)
            self.assertIsNone(self.app._admit_waiting(now=due))
            self.assertEqual(registry.call_count,1)
        self.assertEqual(self.app.detail(queued["id"])["status"],"registration_pending")

    def test_scheduler_admits_job_without_second_user_submission(self):
        received=[]
        self.app.enqueue=lambda job:received.append(job)
        with patch.object(ss,"register_next",return_value={"created":True}) as registry:
            first=self.app.create({"topic":"First","language":"pl","seconds":15})
            self.app.create({"topic":"Second","language":"pl","seconds":15})
            waiting=self.app.create({"topic":"DNA molecule","language":"uk","seconds":45})
            p=self.app.pipeline(first["id"])
            state=p.snapshot(first["id"])
            state.update(status="needs_attention",error_type="FixtureStopped")
            p.save(p.directory(first["id"]),state)
            class Once:
                calls=0
                def wait(self,seconds):
                    self.calls+=1
                    return self.calls>1
            self.app.stop=Once()
            self.app._schedule()
            self.assertIn(waiting["id"],received)
            self.assertEqual(registry.call_count,3)
            self.assertEqual(self.app.detail(waiting["id"])["status"],"ready")

    def test_pending_queued_job_is_visible_from_public_get_contract(self):
        import http.client
        import threading
        from http.server import ThreadingHTTPServer
        with patch.object(ss,"DAY_LIMIT",1), \
             patch.object(ss,"register_next",return_value={"created":True}):
            self.app.create({"topic":"First","language":"pl","seconds":15})
            queued=self.app.create({"topic":"DNA molecule","language":"uk","seconds":45})
        server=ThreadingHTTPServer(("127.0.0.1",0),ss.make_handler(self.app))
        self.addCleanup(server.server_close)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        conn=http.client.HTTPConnection("127.0.0.1",server.server_address[1],timeout=3)
        self.addCleanup(conn.close)
        conn.request("GET","/factory-next/api/jobs/"+queued["id"])
        result=conn.getresponse()
        self.assertEqual(result.status,200)
        body=json.loads(result.read())
        self.assertEqual(body["status"],"queued_for_quota")
        self.assertEqual(body["request"]["topic"],"DNA molecule")
        self.assertIsNotNone(body["eligible_after"])
        self.assertIsNone(body["video_url"])
        conn.request("GET","/factory-next/api/jobs")
        result=conn.getresponse()
        self.assertEqual(result.status,200)
        listing=json.loads(result.read())
        self.assertEqual(listing[0]["status"],"queued_for_quota")

    def test_rejected_post_closes_http_connection_safely(self):
        import http.client
        import threading
        from http.server import ThreadingHTTPServer
        server=ThreadingHTTPServer(("127.0.0.1",0),ss.make_handler(self.app))
        self.addCleanup(server.server_close)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        connection=http.client.HTTPConnection("127.0.0.1",server.server_address[1],timeout=3)
        self.addCleanup(connection.close)
        body=b'{"topic":"sample","language":"pl","seconds":15}'
        connection.request("POST","/factory-next/api/jobs",body=body,headers={
            "Content-Type":"application/json","Origin":"https://invalid.example"})
        response=connection.getresponse()
        self.assertEqual(response.status,403)
        self.assertEqual(response.getheader("Connection"),"close")
        response.read()
        # Reusing the client must establish a clean HTTP request: the rejected
        # JSON payload cannot become a prefix of the following GET.
        connection.request("GET","/factory-next/api/jobs")
        response=connection.getresponse()
        self.assertEqual(response.status,200)
        self.assertEqual(response.read(),b"[]")

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
