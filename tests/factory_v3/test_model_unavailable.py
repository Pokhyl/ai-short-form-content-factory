"""Explicit Gemini rejection may advance; unknown sends remain immutable."""
import unittest
from unittest.mock import patch
from factory_v3.gemini import Gemini, obj, string
from factory_v3.http import HTTPFailure
from factory_v3.preparation import BudgetedCalls, ModelUnavailable
from test_preparation import FakeLedger
from test_gemini import HTTP


def rejection(status=503, code='UNAVAILABLE', execution='13142', retry_after=None):
    error = HTTPFailure(status, {} if retry_after is None else {'retry-after': retry_after})
    error.receipt.update(error_status=code, gateway_execution_id=execution)
    return error


class Ledger(FakeLedger):
    model_unavailable = FakeLedger.unavailable


class ModelAvailabilityTests(unittest.TestCase):
    def setup_adapter(self, errors, limit=20):
        self.ledger = Ledger(); self.ledger.limit = limit
        self.http = HTTP({'answer': 'controlled'})
        self.sends = 0
        success = self.http.request_receipt
        def send(*args, **kwargs):
            self.sends += 1
            if errors:
                error = errors.pop(0)
                if error is not None:
                    raise error
            return success(*args, **kwargs)
        self.http.request_receipt = send
        self.adapter = Gemini(BudgetedCalls(self.ledger, 'controlled'), lambda: 'test-only',
                              self.http, model='gemini-3.1-flash-lite',
                              free_tier_confirmed=True, retry_unavailable=True)

    def generate(self):
        return self.adapter.generate('brief', 'controlled', {}, obj({'answer': string()}))

    @patch('factory_v3.gemini.time.sleep')
    def test_each_explicit_rejection_consumes_a_distinct_claim_and_exact_replay_never_resends(self, sleep):
        self.setup_adapter([rejection(), rejection(), None])
        self.assertEqual(self.generate()[0], {'answer': 'controlled'})
        self.assertEqual(self.sends, 3)
        self.assertEqual(list(self.ledger.claims), ['brief', 'brief:availability:2', 'brief:availability:3'])
        self.assertEqual([r[2] for r in self.ledger.claims.values()], ['failed', 'failed', 'done'])
        self.assertEqual(len({r[1] for r in self.ledger.claims.values()}), 1)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [2, 4])
        self.generate()
        self.assertEqual(self.sends, 3)

    @patch('factory_v3.gemini.time.sleep')
    def test_inline_rejections_stop_before_backoff_exceeds_thirty_seconds(self, sleep):
        self.setup_adapter([rejection() for _ in range(6)])
        with self.assertRaises(ModelUnavailable): self.generate()
        self.assertEqual(self.sends, 5)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [2,4,8,16])

    @patch('factory_v3.gemini.time.sleep')
    def test_total_budget_still_caps_physical_attempts(self, sleep):
        self.setup_adapter([rejection(), rejection(), None], limit=2)
        with self.assertRaisesRegex(ValueError, 'exhausted'): self.generate()
        self.assertEqual(self.sends, 2)

    @patch('factory_v3.gemini.time.sleep')
    def test_other_errors_and_missing_gateway_provenance_never_retry(self, sleep):
        for error in [rejection(502), rejection(429), rejection(code='UNKNOWN_PROVIDER_RESULT'),
                      rejection(execution=None), rejection(execution='not-an-execution'), TimeoutError()]:
            with self.subTest(error=repr(error)):
                self.setup_adapter([error, None])
                with self.assertRaises(Exception): self.generate()
                self.assertEqual(self.sends, 1)
                self.assertTrue(self.ledger.terminal)
        sleep.assert_not_called()

    @patch('factory_v3.gemini.time.sleep')
    def test_retry_after_is_honored_but_long_delay_does_not_block_worker(self, sleep):
        self.setup_adapter([rejection(retry_after='7'), None]); self.generate()
        sleep.assert_called_once_with(7)
        sleep.reset_mock()
        self.setup_adapter([rejection(retry_after='31'), None])
        with self.assertRaises(ModelUnavailable): self.generate()
        self.assertEqual(self.sends, 1); sleep.assert_not_called()

    @patch('factory_v3.gemini.time.sleep')
    def test_lost_rejection_receipt_write_does_not_permit_another_send(self, sleep):
        self.setup_adapter([rejection(), None])
        def lost(*args): raise ConnectionError('controlled ledger response loss')
        self.ledger.model_unavailable = lost
        with self.assertRaises(ConnectionError): self.generate()
        with self.assertRaises(ValueError): self.generate()
        self.assertEqual(self.sends, 1)
        self.assertEqual(self.ledger.claims['brief'][2], 'started')
        sleep.assert_not_called()

    @patch('factory_v3.gemini.time.sleep')
    def test_completed_but_truncated_output_never_retries(self, sleep):
        self.setup_adapter([None]); self.http.finish = 'MAX_TOKENS'
        with self.assertRaisesRegex(ValueError, 'incomplete'): self.generate()
        self.assertEqual(self.sends, 1); sleep.assert_not_called()
