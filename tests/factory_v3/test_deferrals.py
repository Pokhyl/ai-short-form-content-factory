"""Recovery uses saved receipts and physical budgets, without sleeping a worker."""
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace
from factory_v3.gemini import Gemini, obj, string
from factory_v3.preparation import BudgetedCalls, PreparationDeferred, ModelUnavailable
from test_model_unavailable import Ledger, rejection
from test_gemini import HTTP
from factory_v3.server import Application
from material_first.producer import DurableProducer


class DeferredLedger(Ledger):
    def __init__(self):
        super().__init__()
        self.limit = 3
        self.due = set()
        self.delays = []

    def defer(self, request_id, failed, next_key, delay):
        self.delays.append(delay)
        return {'deferred': next_key not in self.due, 'retry_at': 'controlled-future'}


class DeferralTests(unittest.TestCase):
    def test_producer_leaves_deferred_preparation_open_and_does_not_create_voice_job(self):
        ledger = SimpleNamespace(claim_run=lambda _: {'cached':False,'request':{
            'topic':'controlled','language':'pl','seconds':15}}, reject=Mock(), complete=Mock())
        component = SimpleNamespace(calls=SimpleNamespace(request_id='controlled'))
        ops = SimpleNamespace(source=component, gemini=component, search=component, downloader=component)
        with patch('material_first.producer.Producer.prepare', side_effect=PreparationDeferred('future')):
            with self.assertRaises(PreparationDeferred):
                DurableProducer('/unused',ledger,ops).prepare('controlled')
        ledger.reject.assert_not_called()
        ledger.complete.assert_not_called()

    def adapter(self, ledger, http):
        return Gemini(BudgetedCalls(ledger, 'controlled'), lambda: 'test-key', http,
                      model='gemini-3.1-flash-lite', free_tier_confirmed=True,
                      retry_unavailable=True, defer_unavailable=True)

    @patch('factory_v3.gemini.time.sleep')
    def test_restart_replays_rejection_and_success_without_duplicate_sends(self, sleep):
        ledger = DeferredLedger()
        http = HTTP({'answer': 'controlled'})
        send = http.request_receipt
        http.request_receipt = Mock(side_effect=[rejection(), send('POST', 'test', {}, {}, 1)])
        def run(adapter, context):
            return adapter.generate('edit', 'controlled', context, obj({'answer': string()}))
        with self.assertRaises(PreparationDeferred):
            run(self.adapter(ledger, http), {'z': {'b': 2, 'a': 1}, 'a': 0})
        self.assertEqual(http.request_receipt.call_count, 1)
        # Reconstructed JSONB ordering must retain exact request identity.
        with self.assertRaises(PreparationDeferred):
            run(self.adapter(ledger, http), {'a': 0, 'z': {'a': 1, 'b': 2}})
        self.assertEqual(http.request_receipt.call_count, 1)
        ledger.due.add('edit:availability:2')
        self.assertEqual(run(self.adapter(ledger, http), {'a': 0, 'z': {'a': 1, 'b': 2}})[0], {'answer':'controlled'})
        run(self.adapter(ledger, http), {'a': 0, 'z': {'a': 1, 'b': 2}})
        self.assertEqual(http.request_receipt.call_count, 2)
        self.assertFalse(ledger.terminal)
        sleep.assert_not_called()

    @patch('factory_v3.gemini.time.sleep')
    def test_three_total_rejections_stop_with_no_fourth_attempt(self, sleep):
        ledger = DeferredLedger()
        http = SimpleNamespace(request_receipt=Mock(side_effect=rejection()))
        def run(): return self.adapter(ledger, http).generate('edit','controlled',{},obj({'answer':string()}))
        with self.assertRaises(PreparationDeferred): run()
        ledger.due.add('edit:availability:2')
        with self.assertRaises(PreparationDeferred): run()
        self.assertEqual(ledger.delays[-1], 300)
        ledger.due.add('edit:availability:3')
        with self.assertRaises(ModelUnavailable): run()
        self.assertEqual(http.request_receipt.call_count, 3)
        sleep.assert_not_called()

    def test_unknown_or_rate_limit_never_enters_queue(self):
        for error in (TimeoutError(), rejection(502), rejection(429)):
            ledger = DeferredLedger()
            http = SimpleNamespace(request_receipt=Mock(side_effect=error))
            with self.assertRaises(type(error)):
                self.adapter(ledger,http).generate('edit','controlled',{},obj({'answer':string()}))
            self.assertEqual(ledger.delays, [])
            self.assertTrue(ledger.terminal)
            self.assertEqual(http.request_receipt.call_count,1)

    def test_queue_deduplicates_and_deferred_task_does_not_become_failed(self):
        prep = SimpleNamespace(ready=lambda:['same','same'], reject=Mock())
        runtime = SimpleNamespace(settings={'owner_token':'x'*32}, preparations=prep,
                                  run=Mock(side_effect=PreparationDeferred('future')))
        app = Application(runtime,'https://example.test',start_scheduler=False)
        app.pool.shutdown(wait=True)
        app.pool = Mock()
        app.enqueue_due(); app.enqueue_due()
        self.assertEqual(app.pool.submit.call_count,1)
        app._run('same')
        prep.reject.assert_not_called()
        self.assertEqual(app.inflight,set())
        self.assertTrue(app.slots.acquire(blocking=False))
        app.slots.release()
