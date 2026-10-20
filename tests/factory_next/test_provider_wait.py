"""Retired provider timers must never dispatch a legacy or failed stage."""
import tempfile
import unittest
from uuid import uuid4
from factory_next.pipeline import Pipeline,ReconciliationRequired
from factory_v3.preparation import PreparationDeferred

class ProviderRetryRemovedTests(unittest.TestCase):
    def test_legacy_waiting_state_cannot_resume_even_when_due(self):
        class Adapter:
            sends=0
            def research(self,context):self.sends+=1;return {}
        with tempfile.TemporaryDirectory() as root:
            adapter=Adapter();p=Pipeline(root,adapter,'e'*40,clock=lambda:9999999)
            job=str(uuid4());p.create(job,'Grounded topic','ru',15)
            state=p.snapshot(job);state['status']='provider_wait'
            state['provider_wait_receipt']={'protocol':'budgeted-explicit-503','stage':'research',
                                          'retry_at':'1970-01-01T00:00:00+00:00'}
            p.save(p.directory(job),state)
            with self.assertRaises(ReconciliationRequired):p.step(job)
            self.assertEqual(adapter.sends,0)
            self.assertEqual(p.snapshot(job),state)

    def test_retired_deferral_exception_is_terminal_and_never_scheduled(self):
        class Adapter:
            sends=0
            def research(self,context):
                self.sends+=1;raise PreparationDeferred('2999-01-01T00:00:00+00:00')
        with tempfile.TemporaryDirectory() as root:
            adapter=Adapter();p=Pipeline(root,adapter,'e'*40)
            job=str(uuid4());p.create(job,'Grounded topic','ru',15)
            with self.assertRaises(PreparationDeferred):p.step(job)
            state=p.snapshot(job)
            self.assertEqual(state['status'],'needs_attention')
            self.assertNotIn('provider_wait_receipt',state)
            with self.assertRaises(ReconciliationRequired):p.step(job)
            self.assertEqual(adapter.sends,1)
