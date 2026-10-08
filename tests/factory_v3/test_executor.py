import copy
import unittest
import test_preflight
from factory_v3.executor import Executor, ReconciliationRequired


class LedgerDouble:
    """Controlled in-memory ledger double; production uses PostgreSQL."""
    def __init__(self):
        self.job = None
        self.claims = []
        self.accounted = 0

    def create(self, job_id, frozen):
        if self.job is not None:
            raise ValueError("duplicate")
        self.job = {"id": job_id, "status": "prepared", "frozen": copy.deepcopy(frozen), "outputs": {}}
        return job_id

    def snapshot(self, job_id):
        return copy.deepcopy(self.job)

    def claim(self, job_id, stage, plan_hash):
        expected = {"voice": "prepared", "align": "voice_ready", "render": "align_ready", "qa": "render_ready"}
        if self.job["status"] != expected[stage] or stage in self.claims:
            raise ValueError("already claimed")
        if plan_hash != self.job["frozen"]["sha256"]:
            raise ValueError("hash")
        self.claims.append(stage)
        self.job["status"] = stage + "_running"

    def account_voice_attempt(self, job_id):
        self.accounted += 1

    def finish(self, job_id, stage, output):
        self.job["outputs"][stage] = copy.deepcopy(output)
        self.job["status"] = "qa_pass" if stage == "qa" else stage + "_ready"

    def fail(self, job_id, stage, code, unknown):
        self.job["status"] = "unknown" if unknown else "failed"


class AdaptersDouble:
    def __init__(self):
        self.calls = []
        self.fail_voice = False

    def voice(self, job_id, payload, outputs, before_send):
        before_send()
        self.calls.append("voice")
        if self.fail_voice:
            raise TimeoutError("controlled lost response")
        return {"status": "ready", "sha256": "controlled"}

    def align(self, job_id, payload, outputs):
        assert "voice" in outputs
        self.calls.append("align")
        return {"status": "ready"}

    def render(self, job_id, payload, outputs):
        assert "align" in outputs
        self.calls.append("render")
        return {"status": "ready"}

    def qa(self, job_id, payload, outputs):
        assert "render" in outputs
        self.calls.append("qa")
        return {"status": "ready"}


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_preflight.FreezeTests()
        self.fixture.setUp()
        self.ledger = LedgerDouble()
        self.adapters = AdaptersDouble()
        self.executor = Executor(self.ledger, self.fixture.root, self.adapters)
        self.executor.create("controlled-job", self.fixture.make())

    def tearDown(self):
        self.fixture.tearDown()

    def test_verified_plan_executes_in_order_and_does_not_repeat_voice(self):
        for _ in range(4):
            self.executor.run_next("controlled-job")
        self.executor.run_next("controlled-job")
        self.assertEqual(self.adapters.calls, ["voice", "align", "render", "qa"])
        self.assertEqual(self.ledger.accounted, 1)

    def test_changed_bytes_block_before_claim_or_provider_call(self):
        self.fixture.path.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.executor.run_next("controlled-job")
        self.assertEqual(self.adapters.calls, [])
        self.assertEqual(self.ledger.claims, [])
        self.assertEqual(self.ledger.accounted, 0)

    def test_lost_voice_response_is_not_retried_by_new_executor(self):
        self.adapters.fail_voice = True
        with self.assertRaises(TimeoutError):
            self.executor.run_next("controlled-job")
        fresh = Executor(self.ledger, self.fixture.root, self.adapters)
        with self.assertRaises(ReconciliationRequired):
            fresh.run_next("controlled-job")
        self.assertEqual(self.adapters.calls, ["voice"])

    def test_process_crash_after_claim_is_not_blindly_repeated(self):
        self.ledger.claim("controlled-job", "voice", self.ledger.job["frozen"]["sha256"])
        with self.assertRaises(ReconciliationRequired):
            self.executor.run_next("controlled-job")
        self.assertEqual(self.adapters.calls, [])

    def test_failure_after_provider_return_does_not_repeat_call(self):
        def lost_database(*args):
            raise ConnectionError("controlled commit interruption")
        self.ledger.finish = lost_database
        with self.assertRaises(ConnectionError):
            self.executor.run_next("controlled-job")
        with self.assertRaises(ReconciliationRequired):
            self.executor.run_next("controlled-job")
        self.assertEqual(self.adapters.calls, ["voice"])

class CorrectedPlanTests(unittest.TestCase):
    def test_following_stages_receive_final_reviewed_text_and_original_remains_immutable(self):
        from material_first.voice_correction import POLICY
        from factory_v3.preflight import digest
        original={'voice_correction':dict(POLICY),'script':'before','scenes':[{'id':'s','narration':'before'}]}
        final=copy.deepcopy(original);final['script']='after';final['scenes'][0]['narration']='after'
        frozen={'payload':original,'sha256':digest(original)}
        effective={'payload':final,'sha256':digest(final)}
        ledger=LedgerDouble();ledger.create('job',frozen)
        ledger.job['status']='voice_ready';ledger.job['outputs']['voice']={'effective_frozen':effective}
        class Adapter:
            def align(self,job,payload,outputs):
                assert payload['script']=='after'
                return {'status':'ready'}
        Executor(ledger,'.',Adapter(),verifier=lambda root,f:f['payload']).run_next('job')
        self.assertEqual(ledger.job['frozen']['payload']['script'],'before')
        self.assertEqual(ledger.job['status'],'align_ready')
