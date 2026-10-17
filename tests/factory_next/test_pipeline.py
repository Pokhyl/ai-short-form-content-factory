import tempfile
import unittest
from uuid import uuid4
from factory_next.pipeline import Pipeline, ReconciliationRequired


class Adapters:
    def __init__(self):self.calls=[]
    def research(self,ctx):self.calls.append('research');return {'sources':['controlled fixture']}
    def materials(self,ctx):self.calls.append('materials');raise TimeoutError('ambiguous provider response')


class Checkpoints(unittest.TestCase):
    def test_restart_reuses_completed_stage_and_never_repeats_unknown_send(self):
        with tempfile.TemporaryDirectory() as root:
            adapter=Adapters();job=str(uuid4());revision='a'*40
            first=Pipeline(root,adapter,revision)
            first.create(job,'Topic','pl',15);first.step(job)
            second=Pipeline(root,adapter,revision)
            self.assertEqual(second.snapshot(job)['next_stage'],'materials')
            with self.assertRaises(TimeoutError):second.step(job)
            with self.assertRaises(ReconciliationRequired):Pipeline(root,adapter,revision).step(job)
            self.assertEqual(adapter.calls,['research','materials'])
            with self.assertRaises(FileExistsError):first.create(job,'Topic','pl',15)

    def test_revision_and_completed_output_tampering_stop_before_provider(self):
        with tempfile.TemporaryDirectory() as root:
            adapter=Adapters();job=str(uuid4());engine=Pipeline(root,adapter,'a'*40)
            engine.create(job,'Topic','en',30);engine.step(job)
            with self.assertRaises(ValueError):Pipeline(root,adapter,'b'*40).step(job)
            state=engine.snapshot(job);state['outputs']['research']['sources']=['changed']
            engine.save(engine.directory(job),state)
            with self.assertRaises(ValueError):engine.step(job)
            self.assertEqual(adapter.calls,['research'])

    def test_all_stages_resume_in_order_and_audit_is_required(self):
        from test_timeline import MeasuredEditTests
        scenes,photos,timings,duration=MeasuredEditTests().inputs(15)
        class Connected:
            def __init__(self):self.calls=[]
            def research(self,ctx):self.calls.append('research');return {'fixture':True}
            def materials(self,ctx):self.calls.append('materials');return {'photos':photos}
            def story(self,ctx):self.calls.append('story');return {'scenes':scenes}
            def voice(self,ctx):self.calls.append('voice');return {'duration_ms':duration,'sha256':'controlled-audio'}
            def alignment(self,ctx):
                self.calls.append('alignment');return {'timings':timings,'audio_sha256':'controlled-audio'}
            def render(self,ctx):
                self.calls.append('render')
                assert ctx['outputs']['edit']['audio_tempo_factor']==1
                return {'controlled_render':True}
            def audit(self,ctx):self.calls.append('audit');return {'passed':False}
        with tempfile.TemporaryDirectory() as root:
            adapters=Connected();job=str(uuid4());engine=Pipeline(root,adapters,'a'*40)
            engine.create(job,'Controlled test','pl',15)
            for _ in range(7):engine=Pipeline(root,adapters,'a'*40);engine.step(job)
            self.assertEqual(engine.snapshot(job)['next_stage'],'audit')
            with self.assertRaisesRegex(ValueError,'audit'):engine.step(job)
            self.assertEqual(engine.snapshot(job)['status'],'needs_attention')
            self.assertEqual(adapters.calls,['research','materials','story','voice','alignment','render','audit'])
