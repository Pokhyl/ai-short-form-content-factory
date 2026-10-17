"""No automatic replay of a sent or ambiguous provider operation."""
import tempfile
import unittest
from uuid import uuid4

from factory_next.pipeline import (
    Pipeline, PreDispatchUnavailable, ReconciliationRequired,
)


class Clock:
    def __init__(self, initial=1000):self.now=initial
    def __call__(self):return self.now


class GateAdapter:
    def __init__(self, outcomes):
        self.outcomes=list(outcomes)
        self.preflights=[]
        self.sends=[]
    def preflight(self, stage, context):
        self.preflights.append(stage)
        item=self.outcomes.pop(0)
        if item is not None:raise item
    def research(self, context):
        self.sends.append(context['id'])
        return {'sources':['reviewed controlled evidence']}


class RecoveryTests(unittest.TestCase):
    def make(self, root, adapter, clock):
        engine=Pipeline(root,adapter,'b'*40,clock=clock)
        identity=str(uuid4())
        engine.create(identity,'Controlled topic','pl',15)
        return engine,identity

    def test_pre_dispatch_provider_deferrals_are_durable_and_bounded(self):
        with tempfile.TemporaryDirectory() as root:
            clock=Clock()
            adapter=GateAdapter([PreDispatchUnavailable('model',60),
                                 PreDispatchUnavailable('model',120),None])
            engine,identity=self.make(root,adapter,clock)
            first=engine.step(identity)
            self.assertEqual(first['status'],'deferred')
            self.assertEqual(first['preflight_deferrals']['research']['next_retry_at'],1060)
            self.assertEqual(adapter.sends,[])
            restarted=Pipeline(root,adapter,'b'*40,clock=clock)
            self.assertEqual(restarted.step(identity),first)
            self.assertEqual(adapter.preflights,['research'])
            clock.now=1060
            second=restarted.step(identity)
            self.assertEqual(second['status'],'deferred')
            self.assertEqual(second['preflight_deferrals']['research']['attempts'],2)
            self.assertEqual(second['preflight_deferrals']['research']['next_retry_at'],1180)
            clock.now=1180
            resumed=Pipeline(root,adapter,'b'*40,clock=clock).step(identity)
            self.assertEqual(resumed['status'],'ready')
            self.assertEqual(resumed['next_stage'],'materials')
            self.assertEqual(resumed['preflight_deferrals']['research']['status'],'resolved')
            self.assertEqual(resumed['outputs']['research'],{'sources':['reviewed controlled evidence']})
            self.assertEqual(len(adapter.sends),1)

    def test_gate_exhaustion_stops_without_provider_send(self):
        with tempfile.TemporaryDirectory() as root:
            clock=Clock()
            adapter=GateAdapter([PreDispatchUnavailable('model',60)]*3)
            engine,identity=self.make(root,adapter,clock)
            for step in range(3):
                clock.now=1000+60*step
                result=Pipeline(root,adapter,'b'*40,clock=clock).step(identity)
            self.assertEqual(result['status'],'needs_attention')
            self.assertEqual(result['error_type'],'PreDispatchAttemptsExhausted')
            self.assertEqual(result['preflight_deferrals']['research']['attempts'],3)
            with self.assertRaises(ReconciliationRequired):engine.step(identity)
            self.assertEqual(adapter.sends,[])

    def test_ambiguous_stage_failure_never_resends_even_typed(self):
        class Ambiguous:
            def __init__(self):self.calls=0
            def preflight(self, stage, context):return None
            def research(self,context):
                self.calls+=1
                raise PreDispatchUnavailable('provider',30)
        with tempfile.TemporaryDirectory() as root:
            adapter=Ambiguous();clock=Clock()
            engine,identity=self.make(root,adapter,clock)
            with self.assertRaises(PreDispatchUnavailable):engine.step(identity)
            self.assertEqual(engine.snapshot(identity)['status'],'needs_attention')
            clock.now+=1000
            with self.assertRaises(ReconciliationRequired):engine.step(identity)
            self.assertEqual(adapter.calls,1)

    def test_preflight_unexpected_exception_and_interrupted_claim_are_not_retried(self):
        with tempfile.TemporaryDirectory() as root:
            clock=Clock()
            adapter=GateAdapter([TimeoutError('ambiguous preflight response'),None])
            engine,identity=self.make(root,adapter,clock)
            with self.assertRaises(TimeoutError):engine.step(identity)
            with self.assertRaises(ReconciliationRequired):engine.step(identity)
            self.assertEqual(adapter.preflights,['research'])
            self.assertEqual(adapter.sends,[])
        with tempfile.TemporaryDirectory() as root:
            engine,identity=self.make(root,GateAdapter([None]),Clock())
            state=engine.snapshot(identity)
            state['status']='checking'
            engine.save(engine.directory(identity),state)
            with self.assertRaises(ReconciliationRequired):engine.step(identity)

    def test_tampered_prior_stage_stops_before_due_preflight(self):
        class TwoStages(GateAdapter):
            def materials(self, context):
                self.sends.append('materials')
                return {'photos':[]}
        with tempfile.TemporaryDirectory() as root:
            clock=Clock();adapter=TwoStages([None,PreDispatchUnavailable('model',60)])
            engine,identity=self.make(root,adapter,clock)
            engine.step(identity)
            state=engine.step(identity)
            self.assertEqual(state['status'],'deferred')
            state['outputs']['research']['sources']=['corrupted']
            engine.save(engine.directory(identity),state)
            with self.assertRaises(ValueError):engine.step(identity)
            self.assertEqual(adapter.preflights,['research','materials'])
            self.assertEqual(len(adapter.sends),1)

    def test_invalid_retry_contract_is_rejected(self):
        for provider,seconds in (('',60),('model',0),('model',3601),('model',1.5)):
            with self.assertRaises(ValueError):PreDispatchUnavailable(provider,seconds)


if __name__=='__main__':
    unittest.main()
