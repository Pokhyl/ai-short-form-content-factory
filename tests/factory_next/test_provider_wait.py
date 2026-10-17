"""Durable explicit model 503 deferrals: never replay uncertain TTS."""
import tempfile
import unittest
from datetime import datetime,timezone
from uuid import uuid4

from factory_next.pipeline import Pipeline,ReconciliationRequired,fingerprint
from factory_next.wiring import ProviderResumeGate
from factory_v3.preparation import PreparationDeferred


def stamp(epoch):
    return datetime.fromtimestamp(epoch,timezone.utc).isoformat()


class Clock:
    def __init__(self):self.now=1000
    def __call__(self):return self.now


class ProviderAdapter:
    def __init__(self,clock):
        self.clock=clock
        self.sends=0
        self.resume_calls=0
        self.force_failure=False
    def research(self,context):
        self.sends+=1
        if self.sends==1:raise PreparationDeferred(stamp(1060))
        return {'reviewed_source':'budgeted-success'}
    def resume_provider_wait(self,stage,context,receipt):
        self.resume_calls+=1
        if self.force_failure:raise ValueError('ledger unknown')
        assert stage=='research'
        assert receipt['retry_at']==stamp(1060)
        return True


class PipelineProviderWaitTests(unittest.TestCase):
    def make(self,root,adapter,clock):
        p=Pipeline(root,adapter,'e'*40,clock=clock)
        job=str(uuid4())
        p.create(job,'Grounded source topic','pl',15)
        return p,job
    def test_verified_unavailable_waits_and_resumes_after_due(self):
        with tempfile.TemporaryDirectory() as root:
            clock=Clock();adapter=ProviderAdapter(clock)
            p,j=self.make(root,adapter,clock)
            first=p.step(j)
            self.assertEqual(first['status'],'provider_wait')
            self.assertEqual(first['provider_wait_receipt']['retry_at'],stamp(1060))
            self.assertEqual(first['outputs'],{})
            self.assertEqual(adapter.sends,1)
            other=Pipeline(root,adapter,'e'*40,clock=clock)
            self.assertEqual(other.step(j),first)
            clock.now=1059
            self.assertEqual(other.step(j),first)
            self.assertEqual(adapter.resume_calls,0)
            clock.now=1060
            result=other.step(j)
            self.assertEqual(result['status'],'ready')
            self.assertEqual(result['next_stage'],'materials')
            self.assertEqual(adapter.sends,2)
            self.assertEqual(adapter.resume_calls,1)
            self.assertEqual(result['outputs']['research'],
                             {'reviewed_source':'budgeted-success'})
            self.assertNotIn('provider_wait_receipt',result)

    def test_due_without_ledger_gate_is_still_blocked(self):
        class NoGate:
            def research(self,context):raise PreparationDeferred(stamp(1010))
        with tempfile.TemporaryDirectory() as root:
            clock=Clock();p,j=self.make(root,NoGate(),clock)
            p.step(j)
            clock.now=1010
            with self.assertRaises(ReconciliationRequired):p.step(j)
            self.assertEqual(p.snapshot(j)['status'],'provider_wait')

    def test_bad_ledger_gate_blocks_without_resending(self):
        with tempfile.TemporaryDirectory() as root:
            clock=Clock();adapter=ProviderAdapter(clock)
            p,j=self.make(root,adapter,clock)
            p.step(j);clock.now=1060;adapter.force_failure=True
            with self.assertRaisesRegex(ValueError,'ledger unknown'):p.step(j)
            self.assertEqual(p.snapshot(j)['status'],'needs_attention')
            self.assertEqual(adapter.sends,1)
            with self.assertRaises(ReconciliationRequired):p.step(j)

    def test_voice_stage_deferred_exception_never_replays(self):
        class Voice:
            def voice(self,context):
                raise PreparationDeferred(stamp(1060))
        with tempfile.TemporaryDirectory() as root:
            clock=Clock();p,j=self.make(root,Voice(),clock)
            s=p.snapshot(j)
            for stage in ('research','materials','story'):
                output={'dummy':stage}
                s['outputs'][stage]=output;s['receipts'][stage]=fingerprint(output)
            s['next_stage']='voice'
            p.save(p.directory(j),s)
            with self.assertRaises(PreparationDeferred):p.step(j)
            self.assertEqual(p.snapshot(j)['error_type'],'UnsafeProviderDeferral')
            clock.now=3000
            with self.assertRaises(ReconciliationRequired):p.step(j)

    def test_unknown_stage_failure_remains_manual(self):
        class Ambiguous:
            def research(self,context):raise TimeoutError('unknown HTTP outcome')
        with tempfile.TemporaryDirectory() as root:
            p,j=self.make(root,Ambiguous(),Clock())
            with self.assertRaises(TimeoutError):p.step(j)
            self.assertEqual(p.snapshot(j)['status'],'needs_attention')
            with self.assertRaises(ReconciliationRequired):p.step(j)

    def test_interrupted_resume_claim_remains_blocked(self):
        with tempfile.TemporaryDirectory() as root:
            clock=Clock();adapter=ProviderAdapter(clock)
            p,j=self.make(root,adapter,clock);p.step(j)
            s=p.snapshot(j);s['status']='checking_provider'
            p.save(p.directory(j),s)
            clock.now=2000
            with self.assertRaises(ReconciliationRequired):p.step(j)
            self.assertEqual(adapter.sends,1)


class FakeLedger:
    def __init__(self):self.unknown=0;self.reads=0
    def _call(self,sql,args):
        assert 'started' in sql and 'unknown' in sql
        self.reads+=1
        return self.unknown


class FakePreparation:
    def __init__(self):
        self.db=FakeLedger()
        self.live_retry_at=stamp(1060)
        self.state='preparing'
        self.revision='e'*40
        self.claims=0
        self.busy=False
    def snapshot(self,job):return {'status':self.state,'source_revision':self.revision}
    def waiting(self,job):return {'retry_at':self.live_retry_at}
    def claim_run(self,job):
        self.claims+=1
        return {'cached':False,'busy':self.busy}


class FakeRuntime:
    def __init__(self):
        self.preparations=FakePreparation()
        self.ledger=self.preparations.db
        self.revision='e'*40


class DatabaseGateTests(unittest.TestCase):
    def test_exact_due_database_receipt_required_for_resume(self):
        runtime=FakeRuntime()
        gate=ProviderResumeGate(runtime,clock=lambda:1060)
        receipt={'protocol':'budgeted-explicit-503','stage':'research','retry_at':stamp(1060)}
        self.assertIs(gate('research',{'id':str(uuid4())},receipt),True)
        self.assertEqual(runtime.preparations.claims,1)
        self.assertEqual(runtime.ledger.reads,1)

    def test_unknown_or_undue_or_tampered_receipt_never_claims(self):
        for failure in ('unknown','undue','wrong_db_time','wrong_revision','wrong_stage','busy'):
            runtime=FakeRuntime()
            now=1060
            if failure=='unknown':runtime.ledger.unknown=1
            if failure=='undue':now=1059
            if failure=='wrong_db_time':runtime.preparations.live_retry_at=stamp(1130)
            if failure=='wrong_revision':runtime.preparations.revision='f'*40
            if failure=='busy':runtime.preparations.busy=True
            gate=ProviderResumeGate(runtime,clock=lambda:now)
            record={'protocol':'budgeted-explicit-503','stage':'research',
                    'retry_at':stamp(1060)}
            if failure=='wrong_stage':record['stage']='materials'
            with self.subTest(failure=failure),self.assertRaises(ValueError):
                gate('research',{'id':str(uuid4())},record)
            if failure not in ('busy',):
                self.assertEqual(runtime.preparations.claims,0)


if __name__=='__main__':unittest.main()
