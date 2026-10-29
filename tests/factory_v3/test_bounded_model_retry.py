"""Controlled provider failures: retries never change model/body or exceed job budget."""
import unittest
from unittest.mock import Mock, patch
from test_model_unavailable import Ledger, rejection
from test_gemini import HTTP
from factory_v3.gemini import Gemini, obj, string
from factory_v3.preparation import BudgetedCalls, ModelUnavailable


class RetryLedger(Ledger):
    def claim_model_retry(self, job, key, request_hash, prior):
        old=self.claims[prior]
        if key!=prior+':retry503' or old[:3]!=('gemini',request_hash,'failed'):
            raise ValueError('not identical rejected call')
        used=sum(':retry503' in k for k in self.claims)
        if key not in self.claims and used>=2:raise ValueError('job retry limit')
        return {**self.claim(job,key,'gemini',request_hash),
                'retry_delay_seconds':60 if used==0 else 180}


class BoundedRetryTests(unittest.TestCase):
    def setUp(self):
        self.ledger=RetryLedger();self.ledger.limit=20
        self.http=HTTP({'answer':'controlled'})
        self.send=self.http.request_receipt
        self.adapter=Gemini(BudgetedCalls(self.ledger,'job'),lambda:'controlled',self.http,
                            model='gemini-3.1-flash-lite',free_tier_confirmed=True)
        self.adapter.retry_model_unavailable=True
        self.sleep=patch('time.sleep').start();self.addCleanup(patch.stopall)

    def run_model(self,key='brief'):
        return self.adapter.generate(key,'controlled',{},obj({'answer':string()}))

    def failures_then_success(self, errors):
        errors=iter(errors)
        def invoke(*args,**kwargs):
            error=next(errors,None)
            if error:raise error
            return self.send(*args,**kwargs)
        self.http.request_receipt=Mock(side_effect=invoke)

    def test_two_explicit_rejections_then_success_exact_identity_and_cached_replay(self):
        self.failures_then_success([rejection(),rejection()])
        first=self.run_model()
        self.assertEqual(self.run_model(),first)
        self.assertEqual(self.http.request_receipt.call_count,3)
        requests=self.http.request_receipt.call_args_list
        self.assertEqual(requests[0],requests[1]);self.assertEqual(requests[1],requests[2])
        self.assertEqual([c.args[0] for c in self.sleep.call_args_list],[60,180])
        self.assertEqual(len({v[1] for v in self.ledger.claims.values()}),1)

    def test_third_rejection_is_terminal_for_this_operation(self):
        self.failures_then_success([rejection(),rejection(),rejection()])
        with self.assertRaises(ModelUnavailable):self.run_model()
        self.assertEqual(self.http.request_receipt.call_count,3)

    def test_global_limit_across_operations(self):
        for key in ('research','inspection'):
            self.failures_then_success([rejection()]);self.run_model(key)
        self.failures_then_success([rejection()])
        with self.assertRaisesRegex(ValueError,'job retry limit'):self.run_model('review')
        self.assertEqual(self.http.request_receipt.call_count,1)
        self.assertEqual([c.args[0] for c in self.sleep.call_args_list],[60,180])

    def test_timeout_other_status_or_unproven_503_never_retries(self):
        for error in (TimeoutError(),rejection(400),rejection(429),rejection(502),
                      rejection(execution=''),rejection(code='UNKNOWN_PROVIDER_RESULT')):
            with self.subTest(error=repr(error)):
                self.ledger.claims.clear();self.ledger.terminal=False
                self.failures_then_success([error])
                with self.assertRaises(type(error)):self.run_model()
                self.assertEqual(self.http.request_receipt.call_count,1)
        self.sleep.assert_not_called()

    def test_budget_exhaustion_blocks_retry_before_wait_or_send(self):
        self.ledger.limit=1;self.failures_then_success([rejection()])
        with self.assertRaisesRegex(ValueError,'exhausted'):self.run_model()
        self.assertEqual(self.http.request_receipt.call_count,1)
        self.sleep.assert_not_called()

    def test_crash_after_reservation_never_resends(self):
        self.sleep.side_effect=KeyboardInterrupt()
        self.failures_then_success([rejection()])
        with self.assertRaises(KeyboardInterrupt):self.run_model()
        self.sleep.side_effect=None
        with self.assertRaisesRegex(ValueError,'terminal|ambiguous'):self.run_model()
        self.assertEqual(self.http.request_receipt.call_count,1)

    def test_voice_prefix_applies_to_prior_identity(self):
        from factory_next.preparation import VoiceRevisionCalls
        underlying=Mock()
        VoiceRevisionCalls(underlying,attempt=2).run('review:retry503','gemini',{},lambda:None,
                                            retry_of='review',allow_model_unavailable=True)
        args,kwargs=underlying.run.call_args
        self.assertEqual(args[0],'next-voice-correction:2:review:retry503')
        self.assertEqual(kwargs['retry_of'],'next-voice-correction:2:review')
