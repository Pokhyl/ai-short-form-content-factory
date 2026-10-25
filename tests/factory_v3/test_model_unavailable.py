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
    def test_provider_failure_is_sent_once_and_cannot_be_replayed(self):
        for error in [rejection(),rejection(retry_after='900'),rejection(429),
                      rejection(502),TimeoutError('unknown')]:
            with self.subTest(error=repr(error)):
                ledger=Ledger();ledger.limit=20
                http=HTTP({'answer':'controlled'})
                http.request_receipt=patch.object(http,'request_receipt',side_effect=error).start()
                self.addCleanup(patch.stopall)
                ledger.defer=unittest.mock.Mock()
                adapter=Gemini(BudgetedCalls(ledger,'controlled'),lambda:'test-only',http,
                               model='gemini-3.1-flash-lite',free_tier_confirmed=True)
                def run():return adapter.generate('brief','controlled',{},obj({'answer':string()}))
                expected = (ModelUnavailable if isinstance(error,HTTPFailure)
                            and error.receipt.get('status')==503
                            and error.receipt.get('error_status')=='UNAVAILABLE'
                            and error.receipt.get('gateway_execution_id','').isdigit()
                            else type(error))
                with self.assertRaises(expected):run()
                replay_error = ModelUnavailable if expected is ModelUnavailable else ValueError
                with self.assertRaises(replay_error):run()
                self.assertEqual(http.request_receipt.call_count,1)
                self.assertEqual(list(ledger.claims),['brief'])
                ledger.defer.assert_not_called()

    def test_removed_retry_switches_cannot_be_reenabled(self):
        for option in ('retry_unavailable','defer_unavailable'):
            with self.assertRaises(TypeError):
                Gemini(None,None,None,model='gemini-3.1-flash-lite',
                       free_tier_confirmed=True,**{option:True})
