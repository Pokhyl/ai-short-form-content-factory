import unittest
from factory_next.provider_recovery import inspect_exhausted_503

JOB = {"status": "needs_attention", "error_type": "ModelUnavailable",
       "next_stage": "research", "revision": "a" * 40}
PREP = {"status": "preparing", "source_revision": "a" * 40}
RECEIPT = {"status": 503, "error_status": "UNAVAILABLE", "gateway_execution_id": "13684"}
CALLS = [{"kind": "gemini", "state": "failed", "error_code": "ModelUnavailable",
          "response": RECEIPT} for _ in range(3)]

class RecoveryEligibilityTests(unittest.TestCase):
    def check(self, job=None, prep=None, calls=None, budget=27):
        return inspect_exhausted_503(checkpoint=JOB if job is None else job,
                                     preparation=PREP if prep is None else prep,
                                     calls=CALLS if calls is None else calls,
                                     gemini_budget=budget)
    def test_verified_explicit_503_is_eligible(self):
        self.assertEqual(self.check()["remaining_gemini_calls"], 24)
    def test_unknown_claim_blocks_replay(self):
        self.assertFalse(self.check(calls=CALLS + [{"kind": "gemini", "state": "started"}])["eligible"])
    def test_other_error_blocks_replay(self):
        self.assertFalse(self.check(job={**JOB, "error_type": "HTTPFailure"})["eligible"])
    def test_revision_mismatch_blocks_replay(self):
        self.assertFalse(self.check(prep={**PREP, "source_revision": "b" * 40})["eligible"])
    def test_budget_exhaustion_blocks_replay(self):
        self.assertFalse(self.check(budget=3)["eligible"])
    def test_unverified_failure_blocks_replay(self):
        self.assertFalse(self.check(calls=[*CALLS[:2], {**CALLS[2], "response": {"status": 500}}])["eligible"])
    def test_voice_stage_blocks_replay(self):
        self.assertFalse(self.check(job={**JOB, "next_stage": "voice"})["eligible"])

if __name__ == "__main__":
    unittest.main()
