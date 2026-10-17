import tempfile
import unittest
from uuid import uuid4

from factory_next.adapters import FactoryNextAdapters
from factory_next.pipeline import Pipeline, PreDispatchUnavailable

import test_timeline


class Stub:
    def __init__(self, fixture, calls):
        self.fixture=fixture
        self.calls=calls
    def __getattr__(self, name):
        def invoke(context):
            self.calls.append(name)
            if name=='research':return {'facts':['fixture']}
            if name=='materials':return {'photos':self.fixture[1]}
            if name=='story':return {'scenes':self.fixture[0]}
            if name=='voice':return {'sha256':'controlled-audio','duration_ms':self.fixture[3]}
            if name=='alignment':
                return {'audio_sha256':'controlled-audio','timings':self.fixture[2]}
            if name=='render':
                assert context['outputs']['edit']['frame_count']==450
                return {'sha256':'controlled-render'}
            if name=='audit':
                assert context['outputs']['render']['sha256']=='controlled-render'
                return {'passed':True}
            raise AssertionError(name)
        return invoke


class AdapterIntegrationTests(unittest.TestCase):
    def test_composed_adapters_support_full_checkpoint_chain(self):
        with tempfile.TemporaryDirectory() as root:
            calls=[]
            fixture=test_timeline.MeasuredEditTests().inputs(15)
            stub=Stub(fixture,calls)
            adapter=FactoryNextAdapters(stub,stub,stub)
            job=str(uuid4())
            pipeline=Pipeline(root,adapter,'c'*40)
            pipeline.create(job,'fixture','pl',15)
            for _ in range(8):
                pipeline.step(job)
            self.assertEqual(pipeline.snapshot(job)['status'],'complete')
            self.assertEqual(calls,['research','materials','story','voice',
                                    'alignment','render','audit'])
            self.assertEqual(len(pipeline.snapshot(job)['receipts']),8)

    def test_preflight_gate_propagates_safe_provider_block_without_send(self):
        with tempfile.TemporaryDirectory() as root:
            calls=[]
            stub=Stub(test_timeline.MeasuredEditTests().inputs(15),calls)
            def gate(stage, context):
                if stage=='research':
                    raise PreDispatchUnavailable('model',60)
            adapter=FactoryNextAdapters(stub,stub,stub,preflight_gate=gate)
            job=str(uuid4())
            pipeline=Pipeline(root,adapter,'c'*40,clock=lambda:1000)
            pipeline.create(job,'fixture','en',15)
            result=pipeline.step(job)
            self.assertEqual(result['status'],'deferred')
            self.assertEqual(calls,[])


if __name__=='__main__':unittest.main()
