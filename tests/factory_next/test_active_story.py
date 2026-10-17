import copy
import tempfile
import unittest
from uuid import uuid4

from factory_next.pipeline import Pipeline
import test_timeline


class CorrectedNarrationRouting(unittest.TestCase):
    def test_edit_uses_source_reviewed_corrected_story_anchors(self):
        scenes,photos,timings,duration=test_timeline.MeasuredEditTests().inputs(15)
        original=copy.deepcopy(scenes)
        revised=copy.deepcopy(scenes)
        for index,beat in enumerate(revised):
            beat['material_id']=f'{index}-1'
            beat['narration']='A revised factual paragraph.'
        chosen={}
        class Adapter:
            def research(self,context):return {'fixture':True}
            def materials(self,context):return {'photos':photos}
            def story(self,context):return {'scenes':original}
            def voice(self,context):
                return {'sha256':'source-original-audio-hash',
                        'duration_ms':duration,
                        'reviewed_story':{'scenes':revised,'script':'A revised factual paragraph.',
                                          'review':{'native_language_quality':True}}}
            def alignment(self,context):
                chosen['story']=context['outputs']['voice']['reviewed_story']['scenes']
                return {'timings':timings,'audio_sha256':'source-original-audio-hash'}
        with tempfile.TemporaryDirectory() as root:
            job=str(uuid4())
            engine=Pipeline(root,Adapter(),'a'*40)
            engine.create(job,'Controlled topic','pl',15)
            for _ in range(6): engine.step(job)
            state=engine.snapshot(job)
            selected={s['material_id'] for s in state['outputs']['edit']['shots']}
            self.assertTrue({'0-1','1-1','2-1'}<=selected)
            self.assertEqual(chosen['story'],revised)
            self.assertEqual(state['next_stage'],'render')


if __name__=='__main__':unittest.main()
