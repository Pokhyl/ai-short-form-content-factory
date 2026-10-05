"""Controlled callbacks only; no provider requests."""
import unittest
from unittest.mock import patch
from factory_v3.preparation import BudgetedCalls, PreparationLedger


class FakeLedger:
    def __init__(self):
        self.claims = {}
        self.limit = 1
        self.terminal = False
        self.rejected = None

    def claim(self, request_id, key, kind, request_hash):
        if self.terminal:
            raise ValueError("terminal")
        if key in self.claims:
            old = self.claims[key]
            if old[:2] != (kind, request_hash) or old[2] != "done":
                raise ValueError("changed or ambiguous")
            return {"cached": True, "response": old[3]}
        if len(self.claims) >= self.limit:
            raise ValueError("exhausted")
        self.claims[key] = (kind, request_hash, "started", None)
        return {"cached": False}

    def finish(self, request_id, key, result):
        old = self.claims[key]
        self.claims[key] = (*old[:2], "done", result)

    def fail(self, request_id, key, code):
        self.terminal = True

    def reject(self, request_id, code):
        self.rejected = code
        self.terminal = True


class PreparationTests(unittest.TestCase):
    def test_success_replays_without_second_callback(self):
        ledger = FakeLedger()
        calls = BudgetedCalls(ledger, "controlled")
        invoked = []
        callback = lambda: invoked.append(1) or {"photos": [1]}
        self.assertEqual(calls.run("q", "search", {"orientation": "portrait"}, callback),
                         calls.run("q", "search", {"orientation": "portrait"}, callback))
        self.assertEqual(len(invoked), 1)

    def test_changed_identity_and_exhausted_budget_never_invoke(self):
        calls = BudgetedCalls(FakeLedger(), "controlled")
        calls.run("q", "search", {"query": "first"}, lambda: {})
        def forbidden():
            self.fail("provider invoked")
        for key, request in [("q", {"query": "different"}), ("q2", {"query": "first"})]:
            with self.assertRaises(ValueError):
                calls.run(key, "search", request, forbidden)

    def test_ambiguous_result_never_retries(self):
        calls = BudgetedCalls(FakeLedger(), "controlled")
        invoked = []
        def timeout():
            invoked.append(1)
            raise TimeoutError("controlled")
        with self.assertRaises(TimeoutError):
            calls.run("q", "search", {}, timeout)
        with self.assertRaises(ValueError):
            calls.run("q", "search", {}, timeout)
        self.assertEqual(len(invoked), 1)

    def test_lost_ledger_response_preserves_started_claim(self):
        ledger = FakeLedger()
        ledger.finish = lambda *args: (_ for _ in ()).throw(ConnectionError())
        ledger.fail = lambda *args: (_ for _ in ()).throw(ConnectionError())
        calls = BudgetedCalls(ledger, "controlled")
        with self.assertRaises(ConnectionError):
            calls.run("q", "search", {}, lambda: {})
        with self.assertRaises(ValueError):
            calls.run("q", "search", {}, lambda: self.fail("repeat"))

    def test_invalid_local_preflight_marks_terminal(self):
        ledger = FakeLedger()
        calls = BudgetedCalls(ledger, "controlled")
        with patch("factory_v3.preparation.verify_before_voice", side_effect=ValueError("invalid")):
            with self.assertRaises(ValueError):
                calls.complete(None, {})
        self.assertEqual(ledger.rejected, "ValueError")

    def test_revision_is_bound_to_create_claim_and_complete(self):
        class Postgres:
            def _call(self, sql, args):
                self.args = args
        pg = Postgres()
        ledger = PreparationLedger(pg, "revision-a")
        ledger.create("id", {}, {})
        self.assertEqual(pg.args[-1], "revision-a")
        ledger.claim("id", "key", "search", "hash")
        self.assertEqual(pg.args[-1], "revision-a")
        ledger.complete("id", {})
        self.assertEqual(pg.args[-1], "revision-a")
        with self.assertRaises(ValueError):
            PreparationLedger(pg, "")
